
import os
import requests
import streamlit as st

from dotenv import load_dotenv


# =========================================================
# CONFIGURATION
# =========================================================

load_dotenv()

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000"
).rstrip("/")

# Change these paths only if your FastAPI routes use different names.
LOGIN_URL = f"{API_BASE_URL}/user/login"
REGISTER_URL = f"{API_BASE_URL}/user/register"

DOCUMENTS_URL = f"{API_BASE_URL}/documents/"
UPLOAD_URL = f"{API_BASE_URL}/upload/document"

CHAT_SESSIONS_URL = f"{API_BASE_URL}/chat/sessions"


st.set_page_config(
    page_title="RAG Assistant",
    page_icon="📚",
    layout="wide"
)


# =========================================================
# SESSION STATE
# =========================================================

def initialize_session_state():

    defaults = {
        "token": None,
        "logged_in": False,
        "display_name": None,
        "show_register": False,
        "selected_document_id": None,
        "selected_document_name": None,
        "active_chat_id": None,
        "messages": [],
        "delete_chat_id": None,
        "documents": [],
        "sessions": []
    }

    for key, value in defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value


initialize_session_state()


# =========================================================
# API HELPERS
# =========================================================

def get_headers():

    return {
        "Authorization": f"Bearer {st.session_state.token}"
    }


def api_get(url, params=None):

    try:

        response = requests.get(
            url,
            headers=get_headers(),
            params=params,
            timeout=60
        )

        return response

    except requests.RequestException as e:

        st.error(f"Unable to connect to backend: {e}")
        return None


def api_post(url, json_data=None, files=None, data=None):

    try:

        response = requests.post(
            url,
            headers=get_headers(),
            json=json_data,
            files=files,
            data=data,
            timeout=180
        )

        return response

    except requests.RequestException as e:

        st.error(f"Unable to connect to backend: {e}")
        return None


def api_delete(url):

    try:

        response = requests.delete(
            url,
            headers=get_headers(),
            timeout=60
        )

        return response

    except requests.RequestException as e:

        st.error(f"Unable to connect to backend: {e}")
        return None


def get_list_from_response(response, key):

    """
    Supports both:
        [...]
    and:
        {"documents": [...]}
        {"sessions": [...]}
        {"messages": [...]}
    """

    if response is None:
        return []

    try:

        data = response.json()

        if isinstance(data, list):
            return data

        if isinstance(data, dict):

            value = data.get(key, [])

            if isinstance(value, list):
                return value

        return []

    except Exception:

        return []


# =========================================================
# AUTHENTICATION
# =========================================================

def login_user(email, password):

    try:

        # OAuth2PasswordRequestForm expects form data.
        response = requests.post(
            LOGIN_URL,
            data={
                "username": email,
                "password": password
            },
            timeout=60
        )

        if response.status_code == 200:

            result = response.json()

            token = result.get("access_token")

            if not token:
                st.error("Login response did not contain an access token.")
                return

            st.session_state.token = token
            st.session_state.logged_in = True

            # Use the name returned by the API when available.
            # If the API only returns a token, use the login email as a fallback.
            st.session_state.display_name = (
                result.get("username")
                or result.get("name")
                or result.get("full_name")
                or result.get("email")
                or email.split("@")[0]
            )

            st.session_state.selected_document_id = None
            st.session_state.selected_document_name = None
            st.session_state.active_chat_id = None
            st.session_state.messages = []

            st.rerun()

        else:

            try:
                error = response.json().get("detail", "Login failed.")
            except Exception:
                error = "Login failed."

            st.error(error)

    except requests.RequestException as e:

        st.error(f"Backend connection failed: {e}")


def register_user(name, email, password):

    try:

        response = requests.post(
            REGISTER_URL,
            json={
                "username": name,
                "email": email,
                "password": password
            },
            timeout=60
        )

        if response.status_code in [200, 201]:

            st.success("Registration successful! Please log in.")

            st.session_state.show_register = False
            st.rerun()

        else:

            try:
                error = response.json().get(
                    "detail",
                    "Registration failed."
                )
            except Exception:
                error = "Registration failed."

            st.error(error)

    except requests.RequestException as e:

        st.error(f"Backend connection failed: {e}")


def logout():

    st.session_state.token = None
    st.session_state.logged_in = False
    st.session_state.display_name = None

    st.session_state.selected_document_id = None
    st.session_state.selected_document_name = None
    st.session_state.active_chat_id = None

    st.session_state.messages = []
    st.session_state.documents = []
    st.session_state.sessions = []

    st.rerun()


# =========================================================
# LOGIN PAGE
# =========================================================

def show_login_page():

    st.title("📚 RAG Assistant")
    st.caption("Your personal document workspace")

    st.divider()

    if st.session_state.show_register:

        st.subheader("Create an Account")

        with st.form("register_form"):

            name = st.text_input("Full Name")

            email = st.text_input("Email")

            password = st.text_input(
                "Password",
                type="password"
            )

            confirm_password = st.text_input(
                "Confirm Password",
                type="password"
            )

            register_button = st.form_submit_button(
                "Register",
                use_container_width=True
            )

            if register_button:

                if not name or not email or not password:

                    st.warning("Please fill in all fields.")

                elif password != confirm_password:

                    st.error("Passwords do not match.")

                else:

                    register_user(
                        name,
                        email,
                        password
                    )

        if st.button("Already have an account? Login"):

            st.session_state.show_register = False
            st.rerun()

    else:

        st.subheader("Login")

        with st.form("login_form"):

            email = st.text_input("Email")

            password = st.text_input(
                "Password",
                type="password"
            )

            login_button = st.form_submit_button(
                "Login",
                use_container_width=True
            )

            if login_button:

                if not email or not password:

                    st.warning("Enter your email and password.")

                else:

                    login_user(
                        email,
                        password
                    )

        if st.button("Create a new account"):

            st.session_state.show_register = True
            st.rerun()


# =========================================================
# DOCUMENT FUNCTIONS
# =========================================================

def load_documents():

    response = api_get(DOCUMENTS_URL)

    if response is not None:

        if response.status_code == 200:

            st.session_state.documents = get_list_from_response(
                response,
                "documents"
            )

        else:

            st.error("Unable to load documents.")


def upload_document(uploaded_file):

    try:

        files = {
            "file": (
                uploaded_file.name,
                uploaded_file.getvalue(),
                uploaded_file.type
            )
        }

        response = api_post(
            UPLOAD_URL,
            files=files
        )

        if response is not None:

            if response.status_code in [200, 201]:

                st.success("Document uploaded successfully!")

                load_documents()
                st.rerun()

            else:

                try:
                    error = response.json().get(
                        "detail",
                        "Document upload failed."
                    )
                except Exception:
                    error = "Document upload failed."

                st.error(error)

    except Exception as e:

        st.error(f"Upload error: {e}")


def get_document_id(document):

    return (
        document.get("document_id")
        or document.get("id")
    )


def get_document_name(document):

    return (
        document.get("filename")
        or document.get("file_name")
        or document.get("original_filename")
        or document.get("name")
        or "Untitled document"
    )


# =========================================================
# CHAT SESSION FUNCTIONS
# =========================================================

def load_chat_sessions():

    response = api_get(CHAT_SESSIONS_URL)

    if response is not None:

        if response.status_code == 200:

            sessions = get_list_from_response(
                response,
                "sessions"
            )

            # Hide sessions without messages.
            # The backend endpoint should also use an INNER JOIN
            # with chat_messages for this filtering.
            st.session_state.sessions = sessions

        else:

            st.warning("Unable to load chat history.")


def get_chat_id(session):

    return session.get("chat_id")


def get_chat_title(session):

    return (
        session.get("title")
        or "New Chat"
    )


def get_chat_document_id(session):

    return (
        session.get("document_id")
        or session.get("doc_id")
    )


def get_session_document_name(session):

    """
    First use a document name returned by the chat-history API.
    If it is missing, match document_id against the documents
    already loaded from GET /documents/.
    """

    name = (
        session.get("file_name")
        or session.get("filename")
        or session.get("document_name")
        or session.get("original_filename")
    )

    if name:
        return name

    session_document_id = get_chat_document_id(session)

    for document in st.session_state.documents:
        if str(get_document_id(document)) == str(session_document_id):
            return get_document_name(document)

    return "Document name unavailable"


def load_chat_messages(chat_id):

    url = f"{CHAT_SESSIONS_URL}/{chat_id}/messages"

    response = api_get(url)

    if response is not None:

        if response.status_code == 200:

            st.session_state.messages = get_list_from_response(
                response,
                "messages"
            )

        else:

            st.error("Unable to load conversation messages.")

            st.session_state.messages = []


def start_new_chat():

    """
    Do not create a database session here.

    A new session will be created by the backend
    when the user sends the first question.
    """

    if not st.session_state.selected_document_id:

        st.warning("Please select a document first.")
        return

    st.session_state.active_chat_id = None
    st.session_state.messages = []

    st.rerun()


def select_existing_chat(session):

    chat_id = get_chat_id(session)

    document_id = get_chat_document_id(session)

    st.session_state.active_chat_id = chat_id

    st.session_state.selected_document_id = document_id

    st.session_state.selected_document_name = get_session_document_name(session)

    load_chat_messages(chat_id)

    st.rerun()


def delete_chat(chat_id):

    url = f"{CHAT_SESSIONS_URL}/{chat_id}"

    response = api_delete(url)

    if response is not None:

        if response.status_code in [200, 204]:

            if st.session_state.active_chat_id == chat_id:

                st.session_state.active_chat_id = None
                st.session_state.messages = []

            st.session_state.delete_chat_id = None

            st.success("Conversation deleted.")

            load_chat_sessions()
            st.rerun()

        else:

            try:
                error = response.json().get(
                    "detail",
                    "Unable to delete conversation."
                )
            except Exception:
                error = "Unable to delete conversation."

            st.error(error)


# =========================================================
# CHAT FUNCTIONS
# =========================================================

def send_message(question):

    document_id = st.session_state.selected_document_id

    if not document_id:
        st.warning("Please select a document.")
        return

    chat_url = f"{API_BASE_URL}/chat/{document_id}"

    payload = {
        "question": question
    }

    # Existing conversation: send its chat ID.
    # New conversation: omit chat_id so the backend
    # creates a session on the first question.
    if st.session_state.active_chat_id is not None:

        payload["chat_id"] = st.session_state.active_chat_id

    with st.spinner("Thinking..."):

        response = api_post(
            chat_url,
            json_data=payload
        )

    if response is None:
        return

    if response.status_code == 200:

        result = response.json()

        answer = result.get("answer", "No answer received.")

        returned_chat_id = result.get("chat_id")

        if returned_chat_id:

            st.session_state.active_chat_id = returned_chat_id

        # If your backend does not return chat_id,
        # try to identify the newly created session.
        if st.session_state.active_chat_id is None:

            load_chat_sessions()

            matching_sessions = [
                session
                for session in st.session_state.sessions
                if str(get_chat_document_id(session)) == str(document_id)
                and get_chat_title(session).strip().lower()
                == question.strip()[:50].lower()
            ]

            if matching_sessions:

                st.session_state.active_chat_id = get_chat_id(
                    matching_sessions[0]
                )

        # Refresh messages from the database.
        if st.session_state.active_chat_id is not None:

            load_chat_messages(
                st.session_state.active_chat_id
            )

        else:

            # Fallback if the backend does not return a chat ID.
            st.session_state.messages.extend([
                {
                    "role": "user",
                    "content": question
                },
                {
                    "role": "assistant",
                    "content": answer
                }
            ])

        load_chat_sessions()

        st.rerun()

    else:

        try:
            error = response.json().get(
                "detail",
                "Something went wrong."
            )
        except Exception:
            error = "Something went wrong."

        st.error(error)


# =========================================================
# SIDEBAR
# =========================================================

def show_sidebar():

    with st.sidebar:

        st.title("📚 RAG Assistant")

        st.caption("YOUR DOCUMENT WORKSPACE")

        st.divider()

        # NEW CHAT
        if st.button(
            "➕  New Chat",
            use_container_width=True,
            type="primary"
        ):

            start_new_chat()

        st.divider()

        # CHAT HISTORY
        st.subheader("💬 Chat History")

        if st.session_state.sessions:

            for session in st.session_state.sessions:

                chat_id = get_chat_id(session)

                title = get_chat_title(session)

                document_name = get_session_document_name(session)

                col1, col2 = st.columns([5, 1])

                with col1:

                    if st.button(
                        f"💬 {title}",
                        key=f"history_{chat_id}",
                        use_container_width=True
                    ):

                        select_existing_chat(session)

                with col2:

                    if st.button(
                        "🗑️",
                        key=f"delete_{chat_id}",
                        help="Delete conversation"
                    ):

                        st.session_state.delete_chat_id = chat_id
                        st.rerun()

                st.caption(f"📄 {document_name}")

                # Delete confirmation
                if st.session_state.delete_chat_id == chat_id:

                    st.warning("Delete this conversation?")

                    yes_col, no_col = st.columns(2)

                    with yes_col:

                        if st.button(
                            "Delete",
                            key=f"confirm_{chat_id}",
                            type="primary"
                        ):

                            delete_chat(chat_id)

                    with no_col:

                        if st.button(
                            "Cancel",
                            key=f"cancel_{chat_id}"
                        ):

                            st.session_state.delete_chat_id = None
                            st.rerun()

        else:

            st.caption(
                "No conversations yet. Start a new chat!"
            )

        st.divider()

        # INSTRUCTIONS
        with st.expander("📖 Instructions"):

            st.markdown(
                """
                **How to use RAG Assistant**

                1. Upload a PDF document.
                2. Select the document.
                3. Click New Chat.
                4. Ask questions about your PDF.
                5. View previous conversations in Chat History.
                6. Delete conversations you no longer need.

                **Tips**

                - Ask clear questions.
                - Ask follow-up questions in the same chat.
                - Start a new chat for a separate conversation.
                - Answers are generated using your uploaded document.
                """
            )

        st.divider()

        if st.button(
            "🚪 Logout",
            use_container_width=True
        ):

            logout()


# =========================================================
# MAIN APPLICATION
# =========================================================

def show_main_application():

    # Load application data.
    load_documents()
    load_chat_sessions()

    # Display sidebar.
    show_sidebar()

    # MAIN HEADER
    display_name = st.session_state.get("display_name") or "there"

    st.title(f"👋 Welcome, {display_name}!")

    st.caption(
        "Your document workspace is ready. Upload a PDF, select it, "
        "and ask questions about its content."
    )

    st.divider()

    # =====================================================
    # DOCUMENT UPLOAD
    # =====================================================

    with st.expander("📤 Upload a PDF Document"):

        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=["pdf"],
            key="pdf_uploader"
        )

        if uploaded_file:

            if st.button(
                "Upload Document",
                use_container_width=True
            ):

                upload_document(uploaded_file)

    # =====================================================
    # DOCUMENT CARDS
    # =====================================================

    st.subheader("📁 Your Documents")

    documents = st.session_state.documents

    if not documents:

        st.info(
            "No documents uploaded yet. Upload a PDF to get started."
        )

    else:

        columns = st.columns(3)

        for index, document in enumerate(documents):

            document_id = get_document_id(document)

            document_name = get_document_name(document)

            with columns[index % 3]:

                with st.container(border=True):

                    st.markdown("### 📄")

                    st.markdown(f"**{document_name}**")

                    if st.button(
                        "Open Document",
                        key=f"document_{document_id}",
                        use_container_width=True
                    ):

                        st.session_state.selected_document_id = document_id

                        st.session_state.selected_document_name = document_name

                        st.session_state.active_chat_id = None

                        st.session_state.messages = []

                        st.rerun()

    st.divider()

    # =====================================================
    # CHAT AREA
    # =====================================================

    selected_document_id = st.session_state.selected_document_id

    if not selected_document_id:

        st.info(
            "👆 Select a document above to start chatting."
        )

        return

    document_name = (
        st.session_state.selected_document_name
        or "Selected Document"
    )

    st.subheader("💬 Chat with your document")

    st.caption(f"📄 {document_name}")

    # Load messages when opening an existing chat.
    if st.session_state.active_chat_id is not None:

        if not st.session_state.messages:

            load_chat_messages(
                st.session_state.active_chat_id
            )

    # DISPLAY CONVERSATION
    for message in st.session_state.messages:

        role = message.get("role", "assistant")

        content = message.get("content", "")

        if role not in ["user", "assistant"]:
            continue

        with st.chat_message(role):

            st.markdown(content)

    # EMPTY CHAT MESSAGE
    if not st.session_state.messages:

        st.markdown(
            """
            <div style="
                text-align:center;
                padding:35px 10px;
                color:gray;
            ">
                <h3>👋 Hello!</h3>
                <p>Ask me anything about your selected PDF.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    # CHAT INPUT
    question = st.chat_input(
        "Ask a question about your document..."
    )

    if question:

        send_message(question)


# =========================================================
# APPLICATION ENTRY POINT
# =========================================================

if not st.session_state.logged_in:

    show_login_page()

else:

    show_main_application()
