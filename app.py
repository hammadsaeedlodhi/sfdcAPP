import streamlit as st
from simple_salesforce import Salesforce, SalesforceAuthenticationFailed
import account
import contact
import opportunity
import lead

# -------- Page Config --------
st.set_page_config(
    page_title="Salesforce Enterprise App",
    layout="wide",
    initial_sidebar_state="expanded"   # 👈 Sidebar always visible
)

# -------- Initialize session states --------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if 'userid' not in st.session_state:
    st.session_state.userid = ""

if 'sf_connection' not in st.session_state:
    st.session_state.sf_connection = None

# ---------- LOGIN SCREEN ----------
if not st.session_state.logged_in:
    st.markdown(
        """
        <style>
        .block-container {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            max-width: 600px;
            margin: auto;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Inline Salesforce logo in title
    st.markdown(
        "### <img src='https://upload.wikimedia.org/wikipedia/commons/f/f9/Salesforce.com_logo.svg' "
        "width='25' style='vertical-align:middle;'> Salesforce Enterprise Login",
        unsafe_allow_html=True
    )
    st.write("Enter your Salesforce credentials to continue:")

    userid = st.text_input("User ID:")
    password = st.text_input("Password:", type="password")
    securitytoken = st.text_input("Security Token:", type="password")

    # Smaller, centered login button
    st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
    loginbutton = st.button("Login")
    st.markdown("</div>", unsafe_allow_html=True)

    if loginbutton:
        if not userid or not password or not securitytoken:
            st.error("⚠️ All fields are required.")
        else:
            st.success("🔄 Verifying your credentials, please wait...")  # green success message
            try:
                sf = Salesforce(username=userid, password=password, security_token=securitytoken)
                st.session_state.sf_connection = sf
                st.session_state.logged_in = True
                st.session_state.userid = userid
                st.success("✅ Login successful!")
                st.rerun()
            except SalesforceAuthenticationFailed:
                st.error("❌ Invalid Salesforce credentials. Please try again.")

# ---------- MAIN APP ----------
else:
    # ---------------- SIDEBAR ----------------
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #01437a, #0a3b6a);
            }
        [data-testid="stSidebar"] * {
            color: white !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    with st.sidebar:
        st.image(
            "https://upload.wikimedia.org/wikipedia/commons/f/f9/Salesforce.com_logo.svg",
            width=180
        )
        st.markdown("### 👋 Welcome!")
        st.markdown(f"**{st.session_state.userid}**")
        st.caption("Connected to your Salesforce Org")

        st.markdown("---")
        st.markdown("#### 📊 Manage Records")
        st.markdown(
            """
            - 🏢 **Accounts**  
            - 👥 **Contacts**  
            - 💼 **Opportunities**  
            - 👤 **Leads**
            """
        )
        st.caption("💡 Tip: Use the main panel to search, add, or update Salesforce records.")

        if st.sidebar.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.sf_connection = None
            st.session_state.userid = ""
            st.success("You have been logged out successfully.")
            st.rerun()

 # ---------------- REMOVE TOP PADDING ----------------
    st.markdown(
        """
        <style>
        /* Remove top padding/margin of main container */
        .block-container {
            padding-top: 0rem;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    # ---------------- MAIN CONTENT ----------------
    st.title("Salesforce Enterprise Data Manager")
    st.write(f"Logged in as: **{st.session_state.userid}**")

   # st.divider()

    # ---------- COMPACT SELECTBOX STYLING ----------
    st.markdown(
        """
        <style>
        /* Reduce selectbox option spacing */
        div[data-baseweb="select"] > div > div {
            padding-top: 2px !important;
            padding-bottom: 2px !important;
        }

        /* Reduce overall selectbox height */
        div[data-baseweb="select"] > div {
            height: 35px;  /* adjust as needed */
        }

        /* Optional: smaller font for options */
        div[data-baseweb="select"] span {
            font-size: 14px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Limit selectbox width to ~25 characters
    st.markdown(
        """
        <style>
        div[data-baseweb="select"] > div {
            max-width: 400px;  /* adjust width as needed */
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    choice = st.selectbox(
        "Select Salesforce Object:",
        ["--Select Option--", "Account", "Contact", "Opportunity", "Lead"],
        index=0,
        key="object_choice"
    )

    #st.divider()

    # ---------- OBJECT MODULES ----------
    if choice == "Account":
        try:
            account.run()
        except Exception as e:
            st.error(f"❌ Failed to open Account module: {e}")
    elif choice == "Contact":
        try:
            contact.run()
        except Exception as e:
            st.error(f"❌ Failed to open Contact module: {e}")
    elif choice == "Opportunity":
        try:
            opportunity.run()
        except Exception as e:
            st.error(f"❌ Failed to open Opportunity module: {e}")
    elif choice == "Lead":
        try:
            lead.run()
        except Exception as e:
            st.error(f"❌ Failed to open Lead module: {e}")
