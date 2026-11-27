
/* ==========================================
   MINDBRIDGE AI
   Main Frontend JavaScript
   ========================================== */

const API = "/api";

let token = localStorage.getItem("mb_token");

const $ = (selector) => document.querySelector(selector);

// ==========================================
// 1. UTILITY FUNCTIONS
// ==========================================

function message(element, text, good = false) {
    if (!element) return;

    element.textContent = text;
    element.style.color = good ? "#16805d" : "#b43d48";
}

async function request(path, options = {}) {
    const headers = {
        "Content-Type": "application/json",
        ...(options.headers || {})
    };

    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }

    const response = await fetch(API + path, {
        ...options,
        headers
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(data.detail || "Request failed");
    }

    return data;
}

// ==========================================
// 2. LOGIN / REGISTER TABS
// ==========================================

function setTab(tab) {
    document.querySelectorAll(".tab").forEach(button => {
        button.classList.toggle(
            "active",
            button.dataset.tab === tab
        );
    });

    $("#loginForm")?.classList.toggle("hidden", tab !== "login");
    $("#registerForm")?.classList.toggle("hidden", tab !== "register");
}

document.querySelectorAll(".tab").forEach(button => {
    button.addEventListener("click", () => {
        setTab(button.dataset.tab);
    });
});

// ==========================================
// 3. PAGE NAVIGATION
// ==========================================

const pageMap = {
    "#dashboard": "view-dashboard",
    "#profiles": "view-profiles",
    "#goals": "view-goals",
    "#progress": "view-progress",
    "#assistant": "view-assistant"
};

function showPage(hash, updateUrl = true) {
    const pageId = pageMap[hash];

    if (!pageId) {
        hash = "#dashboard";
    }

    const selectedId = pageMap[hash];
    const selectedPage = document.getElementById(selectedId);

    if (!selectedPage) {
        console.error("MindBridge AI page not found:", selectedId);
        return;
    }

    // Hide every page
    document.querySelectorAll(".page-view").forEach(page => {
        page.classList.add("hidden");
    });

    // Display selected page
    selectedPage.classList.remove("hidden");

    // Update sidebar active state
    document.querySelectorAll("nav a").forEach(link => {
        link.classList.toggle(
            "active",
            link.getAttribute("href") === hash
        );
    });

    // Update browser URL
    if (updateUrl && window.location.hash !== hash) {
        history.pushState(null, "", hash);
    }

    // Refresh profiles when opening profiles page
    if (hash === "#profiles" && token) {
        loadProfiles();
    }
}

// Sidebar click events
document.querySelectorAll("nav a").forEach(link => {
    link.addEventListener("click", event => {
        event.preventDefault();

        const hash = link.getAttribute("href");

        if (pageMap[hash]) {
            showPage(hash);
        }
    });
});

// Browser back and forward support
window.addEventListener("popstate", () => {
    showPage(
        pageMap[window.location.hash]
            ? window.location.hash
            : "#dashboard",
        false
    );
});

// ==========================================
// 4. AUTHENTICATION VIEW
// ==========================================

function showAuth() {
    $("#authView")?.classList.remove("hidden");
    $("#appView")?.classList.add("hidden");
    $("#logoutBtn")?.classList.add("hidden");

    const welcome = $("#welcome");

    if (welcome) {
        welcome.textContent = "Good day";
    }

    setTab("login");
}

// ==========================================
// 5. APPLICATION VIEW
// ==========================================

function showApp(user) {
    $("#authView")?.classList.add("hidden");
    $("#appView")?.classList.remove("hidden");
    $("#logoutBtn")?.classList.remove("hidden");

    const welcome = $("#welcome");

    if (welcome) {
        welcome.textContent = `Welcome, ${user.full_name}`;
    }

    const roleLabel = $("#roleLabel");

    if (roleLabel) {
        roleLabel.textContent =
            (user.role || "user").replaceAll("_", " ");
    }

    // Open dashboard after successful login
    showPage("#dashboard");

    // Load existing profiles
    loadProfiles();
}

// ==========================================
// 6. LOAD PROFILES
// ==========================================

async function loadProfiles() {
    try {
        const profiles = await request("/profiles");

        const count = $("#profileCount");
        const profileList = $("#profileList");

        if (count) {
            count.textContent = profiles.length;
        }

        if (!profileList) return;

        profileList.innerHTML = "";

        if (!profiles.length) {
            const empty = document.createElement("p");

            empty.className = "muted";
            empty.textContent =
                "No profiles yet. Add a fictional test profile to begin.";

            profileList.appendChild(empty);
            return;
        }

        profiles.forEach(profile => {
            const card = document.createElement("div");

            card.className = "profile-card";

            const left = document.createElement("div");

            const name = document.createElement("b");
            name.textContent = profile.display_name;

            const meta = document.createElement("small");

            const context = (profile.support_context || "general")
                .replaceAll("_", " ");

            const date = profile.created_at
                ? new Date(profile.created_at).toLocaleDateString()
                : "Date unavailable";

            meta.textContent = `${context} · Created ${date}`;

            left.append(name, meta);
            card.appendChild(left);

            profileList.appendChild(card);
        });

    } catch (error) {
        console.error("Profile loading error:", error);
    }
}

// ==========================================
// 7. LOGIN
// ==========================================

async function authenticate(path, form) {
    const data = Object.fromEntries(
        new FormData(form).entries()
    );

    try {
        message($("#authMessage"), "Please wait...", true);

        const result = await request(path, {
            method: "POST",
            body: JSON.stringify(data)
        });

        token = result.access_token;

        localStorage.setItem("mb_token", token);

        form.reset();

        message($("#authMessage"), "", true);

        showApp(result.user);

    } catch (error) {
        message($("#authMessage"), error.message);
    }
}

$("#loginForm")?.addEventListener("submit", event => {
    event.preventDefault();

    authenticate("/auth/login", event.currentTarget);
});

// ==========================================
// 8. REGISTRATION
// ==========================================

$("#registerForm")?.addEventListener("submit", event => {
    event.preventDefault();

    authenticate("/auth/register", event.currentTarget);
});

// ==========================================
// 9. LOGOUT
// ==========================================

$("#logoutBtn")?.addEventListener("click", () => {
    token = null;

    localStorage.removeItem("mb_token");

    showAuth();
});

// ==========================================
// 10. CREATE PROFILE DIALOG
// ==========================================

const profileDialog = $("#profileDialog");

$("#newProfileBtn")?.addEventListener("click", () => {
    profileDialog?.showModal();
});

$("#closeDialog")?.addEventListener("click", () => {
    profileDialog?.close();
});

// ==========================================
// 11. SAVE PROFILE
// ==========================================

$("#profileForm")?.addEventListener("submit", async event => {
    event.preventDefault();

    const form = event.currentTarget;

    const data = Object.fromEntries(
        new FormData(form).entries()
    );

    try {
        message($("#profileMessage"), "Saving...", true);

        await request("/profiles", {
            method: "POST",
            body: JSON.stringify(data)
        });

        form.reset();

        profileDialog?.close();

        message($("#profileMessage"), "", true);

        await loadProfiles();

    } catch (error) {
        message($("#profileMessage"), error.message);
    }
});

// ==========================================
// 12. APPLICATION INITIALIZATION
// ==========================================

async function initializeApp() {

    // No saved token: show login
    if (!token) {
        showAuth();
        return;
    }

    try {
        // Verify existing login
        const user = await request("/users/me");

        showApp(user);

    } catch (error) {
        console.error("Authentication error:", error);

        token = null;

        localStorage.removeItem("mb_token");

        showAuth();
    }
}

// Start application
initializeApp();
