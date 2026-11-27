
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ==========================================
# 1. AUTHENTICATION SCHEMAS
# ==========================================

class RegisterIn(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=12, max_length=128)
    organization_name: str = Field(min_length=2, max_length=180)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: str
    organization_id: int | None

    model_config = ConfigDict(from_attributes=True)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ==========================================
# 2. PROFILE SCHEMAS
# ==========================================

class ProfileCreate(BaseModel):
    display_name: str = Field(min_length=2, max_length=120)
    support_context: str = Field(default="general", max_length=80)
    strengths: str = Field(default="", max_length=2000)
    preferences: str = Field(default="", max_length=2000)


class ProfileOut(BaseModel):
    id: int
    display_name: str
    support_context: str
    strengths: str
    preferences: str
    created_at: str


# ==========================================
# 3. GOAL SCHEMAS
# ==========================================

class GoalCreate(BaseModel):
    profile_id: int
    title: str = Field(min_length=2, max_length=200)
    description: str = Field(default="", max_length=5000)
    domain: str = Field(default="general", max_length=100)
    target_measure: str = Field(default="", max_length=200)
    status: str = Field(default="active", max_length=40)
    start_date: datetime | None = None
    target_date: datetime | None = None


class GoalUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    domain: str | None = Field(default=None, max_length=100)
    target_measure: str | None = Field(default=None, max_length=200)
    status: str | None = Field(default=None, max_length=40)
    start_date: datetime | None = None
    target_date: datetime | None = None


class GoalOut(BaseModel):
    id: int
    profile_id: int
    title: str
    description: str
    domain: str
    target_measure: str
    status: str
    start_date: datetime | None
    target_date: datetime | None
    created_by: int
    organization_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 4. ACTIVITY SCHEMAS
# ==========================================

class ActivityCreate(BaseModel):
    goal_id: int
    profile_id: int
    title: str = Field(min_length=2, max_length=200)
    description: str = Field(default="", max_length=5000)
    activity_type: str = Field(default="general", max_length=100)
    status: str = Field(default="planned", max_length=40)
    assigned_to: int | None = None


class ActivityUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    activity_type: str | None = Field(default=None, max_length=100)
    status: str | None = Field(default=None, max_length=40)
    assigned_to: int | None = None
    completion_notes: str | None = Field(default=None, max_length=5000)


class ActivityOut(BaseModel):
    id: int
    goal_id: int
    profile_id: int
    title: str
    description: str
    activity_type: str
    status: str
    assigned_to: int | None
    completion_notes: str
    created_by: int
    organization_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
