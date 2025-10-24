import streamlit as st
from simple_salesforce import Salesforce, SalesforceAuthenticationFailed
import account
import contact
import opportunity
import lead

# ------------------ PAGE CONFIG ------------------
st.set_page_config(
    page_title="Salesforce Enterprise",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------ SESSION INIT ------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "userid" not in st.session_state:
    st.session_state.userid = ""
if "sf_connection" not in st.session_state:
    st.session_state.sf_connection = None

# =====================================================
# ============== LOGIN SCREEN =========================
# =====================================================
if not st.session_state.logged_in:

    # --- Login page CSS ---
    st.markdown(
        """
        <style>
        .block-container {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 100vh;                 /* vertically center */
            max-width: 600px;
            margin: auto;
            text-align: center;
            padding-top: 40px;             /* fix logo clipping */
        }
        h1 {
            text-align: center;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # --- Salesforce logo and title ---
    st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/f/f9/Salesforce.com_logo.svg",
        width=100,
    )

    st.title("Salesforce Enterprise Login")
    st.write("Enter your Salesforce credentials to continue:")

    # --- Login form ---
    userid = st.text_input("User ID:")
    password = st.text_input("Password:", type="password")
    securitytoken = st.text_input("Security Token:", type="password")
    loginbutton = st.button("Login", use_container_width=True)

    if loginbutton:
        if not userid or not password or not securitytoken:
            st.error("⚠️ All fields are mandatory")
        else:
            with st.spinner("Verifying credentials..."):
                try:
                    sf = Salesforce(
                        username=userid, password=password, security_token=securitytoken
                    )
                    st.session_state.sf_connection = sf
                    st.session_state.logged_in = True
                    st.session_state.userid = userid
                    st.success("✅ Login successful!")
                    st.rerun()
                except SalesforceAuthenticationFailed:
                    st.error("❌ Invalid Login Credentials")

# =====================================================
# ============== MAIN APP SCREEN ======================
# =====================================================
else:
    # --- Sidebar configuration ---
    st.sidebar.image(
        "https://upload.wikimedia.org/wikipedia/commons/f/f9/Salesforce.com_logo.svg",
        width=250,
    )
    st.sidebar.markdown("### 🌐 Salesforce Data Manager")
    st.sidebar.info(
        "Manage your Salesforce objects seamlessly: "
        "Accounts, Contacts, Opportunities, and Leads — all from one unified interface."
    )
    st.sidebar.markdown("---")
    st.sidebar.write(f"👤 **Logged in as:** {st.session_state.userid}")

    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.sf_connection = None
        st.session_state.userid = ""
        st.success("You have been logged out successfully.")
        st.rerun()

    # --- Main UI layout ---
    st.markdown(
        """
        <style>
        .block-container {
            max-width: 100% !important;
            padding-left: 2rem;
            padding-right: 2rem;
            padding-top: 3rem;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.write(
        f"### Welcome, {st.session_state.userid}! Select the Salesforce object you want to manage:"
    )

    choice = st.selectbox(
        "Select your option to work:",
        ["--Select Option--", "Account", "Contact", "Opportunity", "Lead"],
        key="object_select",
        index=0,
    )

    st.write("---")

    # --- Route to selected object ---
    try:
        if choice == "Account":
            account.run()
        elif choice == "Contact":
            contact.run()
        elif choice == "Opportunity":
            opportunity.run()
        elif choice == "Lead":
            lead.run()
        elif choice == "--Select Option--":
            st.info("Please select an object from the dropdown above.")
    except Exception as e:
        st.error(f"❌ Error loading {choice} module: {e}")
