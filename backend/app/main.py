
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from .database import Base, engine, get_db
from .models import User, Organization, Profile, Goal, Activity
from .schemas import (
    RegisterIn,
    LoginIn,
    TokenOut,
    UserOut,
    ProfileCreate,
    ProfileOut,
    GoalCreate,
    GoalUpdate,
    GoalOut,
    ActivityCreate,
    ActivityUpdate,
    ActivityOut,
)
from .security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)


# ==========================================
# CONFIGURATION
# ==========================================

GOAL_STATUSES = {"active", "paused", "completed", "archived"}
ACTIVITY_STATUSES = {"planned", "in_progress", "completed", "skipped"}

ALLOWED_PROFILE_ROLES = {
    "platform_admin",
    "institution_admin",
    "professional",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="MindBridge AI API",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def require_professional(user: User):
    if user.role not in ALLOWED_PROFILE_ROLES:
        raise HTTPException(
            status_code=403,
            detail="Your role does not have permission to perform this action",
        )


def get_organization_profile(
    profile_id: int,
    user: User,
    db: Session,
) -> Profile:
    profile = db.scalar(
        select(Profile).where(
            Profile.id == profile_id,
            Profile.organization_id == user.organization_id,
        )
    )

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Profile not found",
        )

    return profile


def get_organization_goal(
    goal_id: int,
    user: User,
    db: Session,
) -> Goal:
    goal = db.scalar(
        select(Goal).where(
            Goal.id == goal_id,
            Goal.organization_id == user.organization_id,
        )
    )

    if not goal:
        raise HTTPException(
            status_code=404,
            detail="Goal not found",
        )

    return goal


def get_organization_activity(
    activity_id: int,
    user: User,
    db: Session,
) -> Activity:
    activity = db.scalar(
        select(Activity).where(
            Activity.id == activity_id,
            Activity.organization_id == user.organization_id,
        )
    )

    if not activity:
        raise HTTPException(
            status_code=404,
            detail="Activity not found",
        )

    return activity


def validate_date_range(start_date, target_date):
    if start_date and target_date:
        start = start_date
        target = target_date

        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)

        if target.tzinfo is None:
            target = target.replace(tzinfo=timezone.utc)

        if target < start:
            raise HTTPException(
                status_code=422,
                detail="Target date cannot be earlier than start date",
            )


def validate_assigned_user(
    assigned_to: int | None,
    user: User,
    db: Session,
):
    if assigned_to is None:
        return

    assigned_user = db.scalar(
        select(User).where(
            User.id == assigned_to,
            User.organization_id == user.organization_id,
        )
    )

    if not assigned_user:
        raise HTTPException(
            status_code=404,
            detail="Assigned user not found in your organization",
        )


# ==========================================
# HEALTH CHECK
# ==========================================

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "MindBridge AI",
        "version": "0.2.0",
    }


# ==========================================
# AUTHENTICATION
# ==========================================

@app.post(
    "/api/auth/register",
    response_model=TokenOut,
    status_code=status.HTTP_201_CREATED,
)
def register(
    data: RegisterIn,
    db: Session = Depends(get_db),
):
    email = data.email.lower()

    existing_user = db.scalar(
        select(User).where(User.email == email)
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already registered",
        )

    organization = db.scalar(
        select(Organization).where(
            Organization.name == data.organization_name
        )
    )

    if not organization:
        organization = Organization(name=data.organization_name)
        db.add(organization)
        db.flush()

    user_count = db.scalar(
        select(func.count(User.id))
    ) or 0

    # Development-only bootstrap.
    # Replace this role assignment with an invitation/admin approval
    # process before any real-world deployment.
    role = "platform_admin" if user_count == 0 else "professional"

    user = User(
        email=email,
        full_name=data.full_name,
        password_hash=hash_password(data.password),
        role=role,
        organization_id=organization.id,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "access_token": create_access_token(user.id),
        "user": user,
    }


@app.post("/api/auth/login", response_model=TokenOut)
def login(
    data: LoginIn,
    db: Session = Depends(get_db),
):
    user = db.scalar(
        select(User).where(User.email == data.email.lower())
    )

    if not user or not verify_password(
        data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
        )

    return {
        "access_token": create_access_token(user.id),
        "user": user,
    }


@app.get("/api/users/me", response_model=UserOut)
def me(
    user: User = Depends(get_current_user),
):
    return user


# ==========================================
# PROFILES
# ==========================================

@app.post(
    "/api/profiles",
    response_model=ProfileOut,
    status_code=status.HTTP_201_CREATED,
)
def create_profile(
    data: ProfileCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_professional(user)

    profile = Profile(
        **data.model_dump(),
        created_by=user.id,
        organization_id=user.organization_id,
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return ProfileOut(
        id=profile.id,
        display_name=profile.display_name,
        support_context=profile.support_context,
        strengths=profile.strengths,
        preferences=profile.preferences,
        created_at=profile.created_at.isoformat(),
    )


@app.get("/api/profiles", response_model=list[ProfileOut])
def list_profiles(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rows = db.scalars(
        select(Profile)
        .where(Profile.organization_id == user.organization_id)
        .order_by(Profile.created_at.desc())
    ).all()

    return [
        ProfileOut(
            id=p.id,
            display_name=p.display_name,
            support_context=p.support_context,
            strengths=p.strengths,
            preferences=p.preferences,
            created_at=p.created_at.isoformat(),
        )
        for p in rows
    ]


# ==========================================
# GOALS
# ==========================================

@app.post(
    "/api/goals",
    response_model=GoalOut,
    status_code=status.HTTP_201_CREATED,
)
def create_goal(
    data: GoalCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_professional(user)

    get_organization_profile(data.profile_id, user, db)

    if data.status not in GOAL_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid goal status. Allowed values: {sorted(GOAL_STATUSES)}",
        )

    validate_date_range(data.start_date, data.target_date)

    goal = Goal(
        **data.model_dump(),
        created_by=user.id,
        organization_id=user.organization_id,
    )

    db.add(goal)
    db.commit()
    db.refresh(goal)

    return goal


@app.get("/api/goals", response_model=list[GoalOut])
def list_goals(
    profile_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(Goal).where(
        Goal.organization_id == user.organization_id
    )

    if profile_id is not None:
        get_organization_profile(profile_id, user, db)
        query = query.where(Goal.profile_id == profile_id)

    return db.scalars(
        query.order_by(Goal.created_at.desc())
    ).all()


@app.patch("/api/goals/{goal_id}", response_model=GoalOut)
def update_goal(
    goal_id: int,
    data: GoalUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_professional(user)

    goal = get_organization_goal(goal_id, user, db)

    updates = data.model_dump(exclude_unset=True)

    for field, value in updates.items():
        if field in {
            "title",
            "description",
            "domain",
            "target_measure",
            "status",
        } and value is None:
            raise HTTPException(
                status_code=422,
                detail=f"{field} cannot be null",
            )

    new_status = updates.get("status", goal.status)

    if new_status not in GOAL_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid goal status. Allowed values: {sorted(GOAL_STATUSES)}",
        )

    new_start = updates.get("start_date", goal.start_date)
    new_target = updates.get("target_date", goal.target_date)

    validate_date_range(new_start, new_target)

    for field, value in updates.items():
        setattr(goal, field, value)

    db.commit()
    db.refresh(goal)

    return goal


# ==========================================
# ACTIVITIES
# ==========================================

@app.post(
    "/api/activities",
    response_model=ActivityOut,
    status_code=status.HTTP_201_CREATED,
)
def create_activity(
    data: ActivityCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_professional(user)

    goal = get_organization_goal(data.goal_id, user, db)

    if goal.profile_id != data.profile_id:
        raise HTTPException(
            status_code=422,
            detail="The selected goal does not belong to the selected profile",
        )

    get_organization_profile(data.profile_id, user, db)

    if data.status not in ACTIVITY_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid activity status. Allowed values: {sorted(ACTIVITY_STATUSES)}",
        )

    validate_assigned_user(data.assigned_to, user, db)

    activity = Activity(
        **data.model_dump(),
        completion_notes="",
        created_by=user.id,
        organization_id=user.organization_id,
    )

    db.add(activity)
    db.commit()
    db.refresh(activity)

    return activity


@app.get("/api/activities", response_model=list[ActivityOut])
def list_activities(
    profile_id: int | None = None,
    goal_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(Activity).where(
        Activity.organization_id == user.organization_id
    )

    if profile_id is not None:
        get_organization_profile(profile_id, user, db)
        query = query.where(Activity.profile_id == profile_id)

    if goal_id is not None:
        get_organization_goal(goal_id, user, db)
        query = query.where(Activity.goal_id == goal_id)

    return db.scalars(
        query.order_by(Activity.created_at.desc())
    ).all()


@app.patch(
    "/api/activities/{activity_id}",
    response_model=ActivityOut,
)
def update_activity(
    activity_id: int,
    data: ActivityUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_professional(user)

    activity = get_organization_activity(
        activity_id,
        user,
        db,
    )

    updates = data.model_dump(exclude_unset=True)

    for field, value in updates.items():
        if field in {
            "title",
            "description",
            "activity_type",
            "status",
            "completion_notes",
        } and value is None:
            raise HTTPException(
                status_code=422,
                detail=f"{field} cannot be null",
            )

    new_status = updates.get("status", activity.status)

    if new_status not in ACTIVITY_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid activity status. Allowed values: {sorted(ACTIVITY_STATUSES)}",
        )

    if "assigned_to" in updates:
        validate_assigned_user(
            updates["assigned_to"],
            user,
            db,
        )

    for field, value in updates.items():
        setattr(activity, field, value)

    db.commit()
    db.refresh(activity)

    return activity


# ==========================================
# FRONTEND STATIC FILES
# ==========================================

current_file = Path(__file__).resolve()

frontend = next(
    (
        parent / "frontend"
        for parent in current_file.parents
        if (parent / "frontend").is_dir()
    ),
    None,
)

if frontend is None:
    raise RuntimeError("Frontend directory not found")

app.mount(
    "/",
    StaticFiles(directory=str(frontend), html=True),
    name="frontend"

)
