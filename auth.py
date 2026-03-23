"""
auth.py — Authentication UI
Renders a full-screen login / register screen.
Returns True when the user is authenticated (user_id in session_state).
"""

import streamlit as st
from db_store import create_user, verify_login


# ── Inline CSS for the auth screen ────────────────────────────────────────
AUTH_CSS = """
<style>
.auth-shell {
    display: flex;
    justify-content: center;
    align-items: flex-start;
    padding: 60px 16px 40px;
    min-height: 80vh;
}

.auth-card {
    width: 100%;
    max-width: 440px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 38px 40px 32px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.25);
    position: relative;
    overflow: hidden;
}

.auth-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, var(--gold), var(--gold-light), var(--blue-ice));
    border-radius: 20px 20px 0 0;
}

.auth-logo {
    text-align: center;
    margin-bottom: 28px;
}

.auth-logo-icon {
    font-size: 42px;
    line-height: 1;
    margin-bottom: 8px;
}

.auth-logo-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 22px;
    font-weight: 700;
    color: var(--gold);
    letter-spacing: 1.5px;
}

.auth-logo-sub {
    font-size: 10.5px;
    color: var(--text-dim);
    letter-spacing: 1.3px;
    text-transform: uppercase;
    margin-top: 3px;
}

.auth-divider {
    width: 40px;
    height: 2px;
    background: linear-gradient(90deg, var(--gold), var(--gold-light));
    border-radius: 2px;
    margin: 18px auto;
}

.auth-tab-row {
    display: flex;
    gap: 6px;
    background: var(--bg-base);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 4px;
    margin-bottom: 24px;
}

.auth-tab {
    flex: 1;
    text-align: center;
    padding: 8px 0;
    border-radius: 7px;
    font-size: 12.5px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.18s;
    color: var(--text-secondary);
    letter-spacing: 0.3px;
}

.auth-tab.active {
    background: var(--gold-dim);
    color: var(--gold);
    border: 1px solid rgba(201,168,76,0.25);
}

.auth-field-label {
    font-size: 9.5px !important;
    font-weight: 700 !important;
    letter-spacing: 1.3px !important;
    text-transform: uppercase !important;
    color: var(--text-dim) !important;
    margin-bottom: 5px !important;
    display: block !important;
}

.auth-footer {
    text-align: center;
    font-size: 10.5px;
    color: var(--text-dim);
    margin-top: 22px;
    line-height: 1.6;
}

.auth-security-row {
    display: flex;
    gap: 10px;
    justify-content: center;
    flex-wrap: wrap;
    margin-top: 10px;
}

.auth-security-badge {
    font-size: 9.5px;
    padding: 3px 10px;
    border-radius: 12px;
    background: rgba(34,197,94,0.08);
    color: var(--compliant);
    border: 1px solid rgba(34,197,94,0.2);
    font-weight: 600;
}
</style>
"""


def _render_logo():
    st.markdown("""
    <div class="auth-logo">
        <div class="auth-logo-icon">🏦</div>
        <div class="auth-logo-title">RBI CSF Tool</div>
        <div class="auth-logo-sub">Cybersecurity Compliance Assessment</div>
        <div class="auth-divider"></div>
    </div>
    """, unsafe_allow_html=True)


def show_auth() -> bool:
    """
    Render login/register UI. Returns True if user is authenticated.
    On success, sets st.session_state:
        user_id   : int
        username  : str
        user_role : str
        _session_loaded : bool (False — triggers data load in App.py)
    """
    # Already logged in
    if st.session_state.get("user_id"):
        return True

    st.markdown(AUTH_CSS, unsafe_allow_html=True)

    # Centered layout
    _, center, _ = st.columns([1, 2.2, 1])

    with center:
        _render_logo()

        # Tab state
        if "auth_tab" not in st.session_state:
            st.session_state["auth_tab"] = "login"

        tab = st.session_state["auth_tab"]

        # Tab switcher
        col_l, col_r = st.columns(2)
        with col_l:
            if st.button(
                "🔑  Sign In",
                key="tab_login_btn",
                width='stretch',
                type="primary" if tab == "login" else "secondary",
            ):
                st.session_state["auth_tab"] = "login"
                st.rerun()
        with col_r:
            if st.button(
                "✨  Register",
                key="tab_reg_btn",
                width='stretch',
                type="primary" if tab == "register" else "secondary",
            ):
                st.session_state["auth_tab"] = "register"
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # ── LOGIN FORM ─────────────────────────────────────────
        if tab == "login":
            st.markdown('<span class="auth-field-label">Username</span>', unsafe_allow_html=True)
            login_user = st.text_input(
                "username_login",
                placeholder="Enter your username",
                label_visibility="collapsed",
                key="login_username_field",
            )

            st.markdown('<span class="auth-field-label">Password</span>', unsafe_allow_html=True)
            login_pass = st.text_input(
                "password_login",
                placeholder="Enter your password",
                type="password",
                label_visibility="collapsed",
                key="login_password_field",
            )

            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Sign In →", key="login_submit", width='stretch', type="primary"):
                if not login_user or not login_pass:
                    st.error("Please enter both username and password.")
                else:
                    user = verify_login(login_user, login_pass)
                    if user:
                        st.session_state["user_id"]        = user["id"]
                        st.session_state["username"]       = user["username"]
                        st.session_state["user_role"]      = user["role"]
                        st.session_state["_session_loaded"] = False  # trigger load
                        st.success(f"Welcome back, **{user['username']}**! Loading your data…")
                        st.rerun()
                    else:
                        st.error("Invalid username or password. Please try again.")

            # Hint for first-time users
            st.markdown("""
            <div style="text-align:center; margin-top:14px; font-size:11.5px; color:var(--text-dim);">
                No account yet? Switch to <strong style="color:var(--gold);">Register</strong> above.
            </div>
            """, unsafe_allow_html=True)

        # ── REGISTER FORM ──────────────────────────────────────
        elif tab == "register":
            st.markdown('<span class="auth-field-label">Bank / Organisation Name</span>', unsafe_allow_html=True)
            reg_org = st.text_input(
                "org_register",
                placeholder="e.g. Saraswat Co-operative Bank",
                label_visibility="collapsed",
                key="reg_org_field",
            )

            st.markdown('<span class="auth-field-label">Username</span>', unsafe_allow_html=True)
            reg_user = st.text_input(
                "username_register",
                placeholder="Choose a username (min 3 chars)",
                label_visibility="collapsed",
                key="reg_user_field",
            )

            col_p1, col_p2 = st.columns(2)
            with col_p1:
                st.markdown('<span class="auth-field-label">Password</span>', unsafe_allow_html=True)
                reg_pass = st.text_input(
                    "password_register",
                    placeholder="Min 6 characters",
                    type="password",
                    label_visibility="collapsed",
                    key="reg_pass_field",
                )
            with col_p2:
                st.markdown('<span class="auth-field-label">Confirm Password</span>', unsafe_allow_html=True)
                reg_pass2 = st.text_input(
                    "password_register2",
                    placeholder="Repeat password",
                    type="password",
                    label_visibility="collapsed",
                    key="reg_pass2_field",
                )

            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Create Account →", key="register_submit", width='stretch', type="primary"):
                if not reg_user or not reg_pass:
                    st.error("Username and password are required.")
                elif reg_pass != reg_pass2:
                    st.error("Passwords do not match.")
                else:
                    result = create_user(reg_user, reg_pass)
                    if result["ok"]:
                        # Auto-login after registration
                        user = verify_login(reg_user, reg_pass)
                        if user:
                            st.session_state["user_id"]        = user["id"]
                            st.session_state["username"]       = user["username"]
                            st.session_state["user_role"]      = user["role"]
                            st.session_state["_session_loaded"] = False
                            # Pre-fill bank name if provided
                            if reg_org.strip():
                                st.session_state["_prefill_bank_name"] = reg_org.strip()
                            st.success("Account created! Setting up your workspace…")
                            st.rerun()
                    else:
                        st.error(result["error"])

        # Security footer
        st.markdown("""
        <div class="auth-footer">
            <div>Data is stored securely and isolated per organisation.</div>
            <div class="auth-security-row">
                <span class="auth-security-badge">🔒 PBKDF2-SHA256</span>
                <span class="auth-security-badge">🗄️ Isolated DB rows</span>
                <span class="auth-security-badge">✓ Session persistent</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    return False  # not yet authenticated


# ══════════════════════════════════════════════════════════════
#  CHANGE PASSWORD  (rendered inside App as a sidebar expander)
# ══════════════════════════════════════════════════════════════

def render_change_password_widget():
    """Small inline widget for the sidebar."""
    from db_store import change_password

    with st.expander("🔑  Change Password"):
        old_p = st.text_input("Current password", type="password", key="chpw_old")
        new_p = st.text_input("New password",     type="password", key="chpw_new")
        new_p2= st.text_input("Confirm new",      type="password", key="chpw_new2")

        if st.button("Update Password", key="chpw_submit", width='stretch'):
            user_id = st.session_state.get("user_id")
            # Verify old password
            username = st.session_state.get("username", "")
            user = verify_login(username, old_p)
            if not user:
                st.error("Current password is incorrect.")
            elif new_p != new_p2:
                st.error("New passwords do not match.")
            else:
                result = change_password(user_id, new_p)
                if result["ok"]:
                    st.success("Password updated successfully.")
                else:
                    st.error(result["error"])
