import streamlit as st
import os
import json
import pandas as pd
import plotly.express as px
from datetime import datetime
from dotenv import load_dotenv
import logging
from pathlib import Path
import time # Added for spinner demo

# --- App Configuration (MUST BE THE FIRST STREAMLIT COMMAND) ---
st.set_page_config(
    page_title="HealthGuard - AI Healthcare Assistant",
    page_icon="🏥", # Using a standard emoji icon
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- UI Enhancements ---
# Custom CSS for a more modern look (Placed AFTER set_page_config)
st.markdown("""
    <style>
        /* General App Styling */
        .stApp {
            background-color: #f0f2f6; /* Light grey background */
        }

        /* Sidebar Styling */
        .stSidebar > div:first-child { /* Target the inner div for background */
            background-color: #ffffff; /* White sidebar */
            border-right: 1px solid #e6e6e6;
            padding: 1rem; /* Add some padding */
        }
        .stSidebar .stImage > img {
             display: block;
             margin-left: auto;
             margin-right: auto;
             border-radius: 50%;
             border: 2px solid #4A90E2; /* Accent color border */
             margin-bottom: 1rem;
        }
         .stSidebar .stButton>button {
            width: 100%; /* Make sidebar buttons full width */
            border-radius: 10px;
            border: 1px solid #4A90E2;
            transition: background-color 0.3s ease, color 0.3s ease;
            margin-bottom: 0.5rem; /* Add space between buttons */
         }
        .stSidebar .stButton>button[kind="primary"] {
            background-color: #4A90E2; /* Primary button blue */
            color: white;
        }
        .stSidebar .stButton>button[kind="secondary"] {
            background-color: white;
            color: #4A90E2; /* Primary blue text */
        }
        .stSidebar .stButton>button:hover {
            opacity: 0.85; /* Slightly more subtle hover */
        }
        .stSidebar .stTextInput>div>div>input {
             border-radius: 10px;
             border: 1px solid #ced4da;
        }
        .stSidebar h1 {
            text-align: center;
            color: #333; /* Darker title */
            font-weight: 600;
            margin-top: 0; /* Adjust top margin */
        }
        .stSidebar h3 {
            color: #4A90E2; /* Accent color for subheaders */
            font-weight: 500;
            margin-top: 20px;
            margin-bottom: 10px;
            font-size: 1.1rem;
        }
        .stSidebar .stMarkdown p, .stSidebar .stExpander div[data-baseweb="expander"] div p {
             color: #555; /* Slightly lighter text color */
             font-size: 0.95rem;
             line-height: 1.4;
        }
        .stSidebar .stCaption {
            text-align: center;
            font-style: italic;
            color: #777;
            margin-top: -0.5rem; /* Adjust caption spacing */
            margin-bottom: 1rem;
        }
        .stSidebar hr {
             margin-top: 15px;
             margin-bottom: 15px;
             border-top: 1px solid #e6e6e6;
        }

        /* Main Content Styling */
        .main .block-container { /* Add padding to main content */
            padding-top: 2rem;
            padding-bottom: 5rem; /* Ensure space above footer */
            padding-left: 2rem;
            padding-right: 2rem;
        }
        .stChatInput > div > div > textarea {
            border-radius: 10px;
            border: 1px solid #ced4da;
            background-color: #ffffff;
        }
        .stChatMessage {
            border-radius: 15px;
            padding: 12px 18px;
            margin-bottom: 12px; /* Increased spacing */
            box-shadow: 0 2px 5px rgba(0,0,0,0.08); /* Slightly stronger shadow */
            max-width: 85%; /* Limit message width */
            border: 1px solid transparent; /* Base border */
        }
        /* Assistant message alignment */
        div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) {
             margin-right: auto; /* Align left */
        }
        /* User message alignment */
        div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) {
            margin-left: auto; /* Align right */
        }

        .stChatMessage[data-testid="stChatMessageContent"] { /* Target the content div */
             color: #333;
        }

        /* Assistant message background */
        div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) .stChatMessage {
            background-color: #ffffff;
            border: 1px solid #e6e6e6;
        }
        /* User message background */
         div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) .stChatMessage {
            background-color: #d1e7ff; /* Light blue */
            border: 1px solid #b8d6f9;
         }
         .main .stTabs [data-baseweb="tab-list"] {
             gap: 24px; /* Spacing between tabs */
             border-bottom: 2px solid #e6e6e6; /* Underline for tab list */
             padding-bottom: 0;
         }
         .main .stTabs [data-baseweb="tab"] {
             height: 44px;
             background-color: transparent; /* Make inactive tabs transparent */
             border-radius: 8px 8px 0 0;
             padding: 0px 24px;
             margin-bottom: -2px; /* Overlap border */
             color: #555;
             border: 2px solid transparent; /* Placeholder border */
             border-bottom: none; /* Remove bottom border for inactive */
         }
         .main .stTabs [aria-selected="true"] {
             background-color: #ffffff; /* White background for selected tab content area */
             color: #4A90E2; /* Accent color for selected tab text */
             font-weight: 600;
             border: 2px solid #e6e6e6; /* Border around selected tab */
             border-bottom: 2px solid #ffffff; /* Connect with content area */
         }
         /* Style the content area below tabs */
         .stTabs [data-baseweb="tab-panel"] {
             background-color: #ffffff;
             border: 2px solid #e6e6e6;
             border-top: none; /* Remove top border as it's handled by the tab */
             border-radius: 0 0 8px 8px; /* Round bottom corners */
             padding: 1.5rem;
             margin-top: 0;
         }

         .main .stMetric {
             background-color: #ffffff;
             border: 1px solid #e6e6e6;
             border-radius: 10px;
             padding: 15px 20px;
             box-shadow: 0 2px 4px rgba(0,0,0,0.05);
         }
         .main .stMetric > label {
             font-weight: 500;
             color: #555;
         }
          .main .stMetric > div > span { /* The metric value */
             font-size: 1.8rem;
             font-weight: 600;
             color: #333;
          }
          .main .stMetric > div > div { /* Delta indicator */
             font-size: 0.9rem;
             font-weight: 500;
          }

         /* Footer */
         .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: #e6eaf1; /* Slightly different background */
            color: #555; /* Darker text */
            text-align: center;
            padding: 8px; /* Reduced padding */
            border-top: 1px solid #d1d5db; /* Softer border */
            font-size: 0.8rem; /* Smaller font */
            z-index: 100;
         }
         /* Ensure footer doesn't overlap content when scrolling might be limited */
         .stApp > footer {
             visibility: hidden;
         }

    </style>
""", unsafe_allow_html=True)


# --- Set up logging ---
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Load environment variables ---
load_dotenv()

# --- Environment Variable Check ---
# Check after set_page_config and CSS, but before agent logic
if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("GOOGLE_API_KEY"):
    st.error("⚠️ **Configuration Error:** Neither OPENAI_API_KEY nor GOOGLE_API_KEY is set. Please add at least one API key to your `.env` file to use the application.", icon="🚨")
    st.stop()

# --- Import HealthGuard Components ---
# Import after the initial config checks
try:
    # Assuming healthcareagent is in the same directory or installed
    from healthcareagent import HealthGuardAgent
    from healthcareagent.tools import MedicationTool, SymptomTool, MedicalInfoTool, HealthAnalysisTool
    HEALTHGUARD_AVAILABLE = True
except ImportError:
    st.error("❌ **Import Error:** Failed to import HealthGuard components. Ensure the `healthcareagent` library is installed and accessible (e.g., in the same folder or Python path).", icon="🚨")
    HEALTHGUARD_AVAILABLE = False
    # We might want to stop here if the core agent is unavailable
    # st.stop()
    # Or allow running with limited functionality (e.g., only UI demo)
    # For now, let's assume it should stop if components are missing
    st.stop()


# --- Core Functions ---
def initialize_agent():
    """Initialize the HealthGuard agent with all tools."""
    if not HEALTHGUARD_AVAILABLE:
        st.error("Agent cannot be initialized because components are missing.", icon="❌")
        return None

    try:
        # Determine Database Path
        db_path_env = os.environ.get("DB_PATH")
        if db_path_env and Path(db_path_env).is_absolute():
            db_path = db_path_env
        else:
             # Default to a 'data' subdirectory in the script's location
             script_dir = Path(__file__).parent if "__file__" in locals() else Path.cwd()
             data_dir = script_dir / "data"
             data_dir.mkdir(parents=True, exist_ok=True) # Ensure directory exists
             db_filename = "healthguard_data.db"
             if db_path_env: # If DB_PATH was set but not absolute, use it as filename
                 db_filename = db_path_env
             db_path = str(data_dir / db_filename)

        logger.info(f"Using database path: {db_path}")

        # Initialize all tools
        medication_tool = MedicationTool(db_path=db_path)
        symptom_tool = SymptomTool(db_path=db_path)
        medical_info_tool = MedicalInfoTool() # Assumes keys are in env if needed
        health_analysis_tool = HealthAnalysisTool()

        # Get patient ID from session state
        patient_id = st.session_state.get("patient_id", "default_patient")

        # Initialize agent with all tools
        agent = HealthGuardAgent(
            tools=[medication_tool, symptom_tool, medical_info_tool, health_analysis_tool],
            patient_id=patient_id
        )
        logger.info(f"HealthGuard Agent initialized successfully for patient_id: {patient_id}")
        return agent
    except Exception as e:
        logger.error(f"Error initializing agent: {str(e)}", exc_info=True)
        st.error(f"❌ **Initialization Failed:** Could not initialize the HealthGuard agent. Please check database access and API key configurations. Details: {str(e)}", icon="🚨")
        return None

def display_chat_history():
    """Display the chat history in the Streamlit UI."""
    for message in st.session_state.chat_history:
        role = message["role"]
        content = message["content"]

        avatar_icon = "👤" if role == "user" else "🏥"
        with st.chat_message(role, avatar=avatar_icon):
             st.markdown(content, unsafe_allow_html=True) # Allow potential HTML in response

def process_user_message(user_message):
    """Process a user message through the agent and update the chat history."""
    # Add user message to UI and history immediately
    st.chat_message("user", avatar="👤").markdown(user_message)
    st.session_state.chat_history.append({"role": "user", "content": user_message})

    # Show spinner while processing
    with st.chat_message("assistant", avatar="🏥"):
        with st.spinner("👩‍⚕️ Thinking..."):
            try:
                # Ensure agent is initialized
                if not st.session_state.agent:
                     st.error("Agent is not currently available. Please ensure it initialized correctly.", icon="⚠️")
                     st.session_state.chat_history.append({"role": "assistant", "content": "Error: Agent not available."})
                     return

                # Get agent response
                start_time = time.time()
                response = st.session_state.agent(user_message)
                end_time = time.time()
                logger.info(f"Agent response received in {end_time - start_time:.2f} seconds.")

                # Display response
                st.markdown(response, unsafe_allow_html=True)

                # Add agent response to history
                st.session_state.chat_history.append({"role": "assistant", "content": response})

                # Save chat history (Consider making this async or less frequent if slow)
                save_chat_history()

            except Exception as e:
                logger.error(f"Error processing message: {str(e)}", exc_info=True)
                error_msg = "😥 I encountered an unexpected issue while processing your request. Please check the logs or try rephrasing. If the problem persists, contact support."
                st.error(error_msg, icon="⚠️")
                st.session_state.chat_history.append({"role": "assistant", "content": error_msg})

def get_data_dir():
    """Gets the data directory, creating it if necessary."""
    script_dir = Path(__file__).parent if "__file__" in locals() else Path.cwd()
    data_dir = script_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

def save_chat_history():
    """Save chat history to a JSON file in the data directory."""
    if 'chat_history' not in st.session_state or not st.session_state.chat_history:
        return # Nothing to save

    try:
        data_dir = get_data_dir()
        patient_id = st.session_state.get("patient_id", "default_patient")
        # Sanitize patient_id for filename (basic example)
        safe_patient_id = "".join(c for c in patient_id if c.isalnum() or c in ('_', '-')).rstrip()
        if not safe_patient_id: safe_patient_id = "default_patient" # Fallback

        history_file = data_dir / f"chat_history_{safe_patient_id}.json"

        with open(history_file, "w", encoding='utf-8') as f:
            json.dump(st.session_state.chat_history, f, indent=2)
        # logger.debug(f"Chat history saved to {history_file}") # Use debug level
    except Exception as e:
        logger.warning(f"Could not save chat history for patient {patient_id}: {str(e)}", exc_info=False) # Warning instead of error

def load_chat_history():
    """Load chat history from a JSON file."""
    try:
        data_dir = get_data_dir()
        patient_id = st.session_state.get("patient_id", "default_patient")
        safe_patient_id = "".join(c for c in patient_id if c.isalnum() or c in ('_', '-')).rstrip()
        if not safe_patient_id: safe_patient_id = "default_patient"

        history_file = data_dir / f"chat_history_{safe_patient_id}.json"

        if history_file.exists():
            with open(history_file, "r", encoding='utf-8') as f:
                loaded_history = json.load(f)
                # Basic validation
                if isinstance(loaded_history, list) and all(isinstance(item, dict) and 'role' in item and 'content' in item for item in loaded_history):
                     st.session_state.chat_history = loaded_history
                     logger.info(f"Chat history loaded successfully for patient {patient_id}")
                else:
                    logger.warning(f"Chat history file {history_file} has invalid format. Starting fresh.")
                    st.session_state.chat_history = get_initial_welcome_message()
        else:
            st.session_state.chat_history = get_initial_welcome_message()
            logger.info(f"No chat history file found for patient {patient_id}. Started new chat.")
    except Exception as e:
        logger.error(f"Error loading chat history for patient {patient_id}: {str(e)}", exc_info=True)
        st.error(f"⚠️ Could not load previous chat history due to an error. Starting a fresh chat session.", icon=" W ")
        st.session_state.chat_history = get_initial_welcome_message()

def get_initial_welcome_message():
    """Returns the standard welcome message list."""
    return [{"role": "assistant", "content": "Welcome to HealthGuard! How can I assist you with your health management today?"}]


def get_llm_provider():
    """Return the LLM provider being used based on set API keys."""
    if os.environ.get("GOOGLE_API_KEY"):
        return "Google Gemini"
    elif os.environ.get("OPENAI_API_KEY"):
        return "OpenAI GPT"
    else:
        # This case should ideally be caught by the initial check
        return "Unknown Provider (No API Key Detected)"

# --- Initialize Session State ---
if "agent" not in st.session_state:
    st.session_state.agent = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [] # Will be populated by load_chat_history
if "patient_id" not in st.session_state:
    st.session_state.patient_id = "default_patient"
if "view" not in st.session_state:
    st.session_state.view = "chat"
if "agent_initialized" not in st.session_state:
    st.session_state.agent_initialized = False


# --- Sidebar ---
with st.sidebar:
    # Logo and Title
    # Using a styled placeholder - replace with your actual logo URL if available
    st.image("https://img.icons8.com/external-flatart-icons-flat-flatarticons/128/external-heart-health-care-and-medical-flatart-icons-flat-flatarticons.png", width=100)
    st.title("HealthGuard")
    st.caption(f"Powered by {get_llm_provider()}")

    st.markdown("---")

    # Patient ID Input
    st.subheader("👤 Patient Profile")
    current_patient_id = st.session_state.patient_id
    patient_id_input = st.text_input(
        "Current Patient ID",
        value=current_patient_id,
        key="patient_id_input", # Assign a key for stability
        help="Enter a unique ID to manage personal health data and chat history. Changing this will reload the agent and history."
    )

    # Detect Patient ID change using the input key's value
    if patient_id_input != current_patient_id:
        st.session_state.patient_id = patient_id_input
        logger.info(f"Patient ID changed to: {patient_id_input}. Re-initializing...")
        st.session_state.agent = None # Reset agent
        st.session_state.agent_initialized = False # Mark as needing init
        st.session_state.chat_history = [] # Reset history
        st.rerun() # Rerun to reload history and re-init agent

    st.markdown("---")

    # Navigation
    st.subheader("🧭 Navigation")
    view_changed = False
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💬 Chat", key="nav_chat", use_container_width=True,
                     type="primary" if st.session_state.view == "chat" else "secondary"):
            if st.session_state.view != "chat":
                st.session_state.view = "chat"
                view_changed = True
    with col2:
        if st.button("📊 Dashboard", key="nav_dashboard", use_container_width=True,
                     type="primary" if st.session_state.view == "dashboard" else "secondary"):
             if st.session_state.view != "dashboard":
                st.session_state.view = "dashboard"
                view_changed = True

    if view_changed:
        st.rerun()

    st.markdown("---")

    # About Section
    with st.expander("ℹ️ About HealthGuard", expanded=False):
        st.markdown("""
        HealthGuard is your AI-powered assistant for managing health records and getting insights.
        - **Track Medications:** Record doses and check adherence.
        - **Monitor Symptoms:** Log how you feel and identify patterns.
        - **Access Info:** Get reliable answers to health questions.
        - **Visualize Trends:** See your health data in charts.

        *Remember: This is an AI tool and does not replace professional medical advice.*
        """)

    # Services Status
    with st.expander("🛠️ Connected Services", expanded=True): # Expand by default
        if os.environ.get("GOOGLE_API_KEY") or os.environ.get("OPENAI_API_KEY"):
            st.markdown(f"<span style='color:green; font-weight:bold;'>✓</span> **LLM:** {get_llm_provider()} Connected", unsafe_allow_html=True)
        else:
            st.markdown("<span style='color:orange; font-weight:bold;'>⚠</span> **LLM:** No API Key Found", unsafe_allow_html=True)

        # Check for Traversaal API Key
        traversaal_key = os.environ.get("TRAVERSAAL_ARES_API_KEY")
        if traversaal_key:
            st.markdown("<span style='color:green; font-weight:bold;'>✓</span> **Medical Search:** Enhanced (Traversaal Ares API)", unsafe_allow_html=True)
        else:
             st.markdown("<span style='color:grey; font-weight:bold;'>ℹ</span> **Medical Search:** Basic Mode", unsafe_allow_html=True)

    # Clear Chat Button
    st.markdown("---")
    if st.button("🗑️ Clear Current Chat History", use_container_width=True, key="clear_chat"):
        st.session_state.chat_history = get_initial_welcome_message()
        save_chat_history() # Save the cleared state
        st.toast("Chat history cleared!", icon="🗑️") # Use toast for feedback
        # Rerun only if already in chat view to show the effect immediately
        if st.session_state.view == "chat":
             time.sleep(0.5) # Short delay for toast visibility
             st.rerun()


# --- Initialize Agent and Load History (Run Once Per Session or Patient Change) ---
# This block now runs *after* the sidebar, allowing patient_id changes to take effect first
if not st.session_state.agent_initialized and HEALTHGUARD_AVAILABLE:
    # Show a spinner in the main area while initializing
    with st.spinner("🛠️ Initializing HealthGuard Agent... Please wait."):
        st.session_state.agent = initialize_agent()
        if st.session_state.agent:
            load_chat_history() # Load history *after* successful agent init
            st.session_state.agent_initialized = True
            # Optionally trigger a rerun if the first view needs the loaded history immediately
            # st.rerun()
        else:
             # Error message is already shown by initialize_agent
             # Stop execution if agent failed to initialize, as most functions depend on it
             st.stop()


# --- Main Content Area ---
if st.session_state.view == "chat":
    # Chat View
    st.title("💬 HealthGuard Chat")
    st.markdown(f"Chatting as patient: **{st.session_state.patient_id}**. Use the sidebar to switch profiles or clear history.")
    st.markdown("---") # Visual separator

    # Display chat history
    if 'chat_history' in st.session_state:
        display_chat_history()
    else:
        st.info("Starting a new chat session.") # Should not happen if load_chat_history works

    # Chat input area
    user_message = st.chat_input("Ask HealthGuard (e.g., 'Log my headache: severity 7', 'Did I take Lisinopril today?')")
    if user_message:
        # Make sure agent is ready before processing
        if st.session_state.agent_initialized and st.session_state.agent:
             process_user_message(user_message)
        else:
             st.error("The AI agent is not ready. Please wait for initialization or check for errors.", icon="⚠️")
             # Append an error message to history as well
             st.session_state.chat_history.append({
                 "role": "assistant",
                 "content": "I cannot process your request right now as the agent is not initialized."
             })
             time.sleep(1) # Give time for user to see error
             st.rerun() # Rerun might help if it was a temporary glitch

else: # Dashboard View
    st.title("📊 Health Dashboard")
    st.markdown(f"Displaying dashboard for patient: **{st.session_state.patient_id}**. Use the sidebar to switch profiles.")
    st.info("ℹ️ This dashboard displays **simulated data** for demonstration. In a real application, it would visualize data logged via the chat or other connected devices.", icon="💡")
    st.markdown("---") # Visual separator

    # --- Dashboard Tabs ---
    tab1, tab2, tab3 = st.tabs(["**💊 Medications**", "**🩺 Symptoms**", "**📈 Health Trends**"])

    with tab1:
        st.subheader("Medication Adherence Overview")
        # Placeholder Adherence Data (Simulated - In real app, fetch from DB via agent/tool)
        try:
            # Simulate fetching or use placeholder
            adherence_data = {
                'Medication': ['Lisinopril 10mg', 'Metformin 500mg', 'Atorvastatin 20mg', 'Vitamin D 1000IU', 'Aspirin 81mg'],
                'Adherence (%)': [92, 78, 100, 85, 95],
                'Doses This Week': ['7/7', '5/7', '7/7', '6/7', '7/7'],
                'Last Missed': ['3 days ago', 'Yesterday', 'Never', '5 days ago', 'Never']
            }
            df_meds = pd.DataFrame(adherence_data)
            df_meds_display = df_meds.sort_values(by='Adherence (%)', ascending=True) # Show lowest first

            # Adherence Bar Chart
            fig_meds = px.bar(df_meds_display,
                              x='Adherence (%)', y='Medication',
                              orientation='h', title="Recent Medication Adherence Rate",
                              labels={'Adherence (%)': 'Adherence', 'Medication': ''},
                              range_x=[0, 105],
                              color='Adherence (%)',
                              color_continuous_scale=px.colors.sequential.Blues,
                              text='Adherence (%)', height=400 + len(df_meds_display)*10) # Adjust height
            fig_meds.update_traces(textposition='outside', texttemplate='%{text}%')
            fig_meds.update_layout(
                                   yaxis={'categoryorder':'total ascending'},
                                   margin=dict(l=10, r=20, t=50, b=10),
                                   coloraxis_showscale=False,
                                   plot_bgcolor='rgba(0,0,0,0)', # Transparent plot bg
                                   paper_bgcolor='rgba(0,0,0,0)') # Transparent paper bg
            st.plotly_chart(fig_meds, use_container_width=True)

            st.markdown("##### Adherence Details")
            st.dataframe(df_meds[['Medication', 'Doses This Week', 'Last Missed']], use_container_width=True)

        except Exception as e:
             st.error(f"Could not display medication data: {e}", icon="💊")

        with st.expander("💡 Tips for Improving Adherence"):
            st.markdown("""
            *   **Reminders:** Use phone alarms, calendar events, or smart pill dispensers.
            *   **Pill Organizers:** Prepare doses weekly to simplify daily tasks.
            *   **Routine:** Link taking medication with consistent daily habits (e.g., meals, brushing teeth).
            *   **Visibility:** Keep medications where you'll see them (but safely stored).
            *   **Communicate:** Discuss challenges (side effects, cost, complexity) with your doctor or pharmacist.
            """)

    with tab2:
        st.subheader("Symptom Tracking")
        # Placeholder Symptom Data (Simulated)
        try:
            num_days = 14
            dates = pd.date_range(start=datetime.now() - pd.Timedelta(days=num_days-1), periods=num_days, freq='D')
            symptom_data = {
                'Date': dates,
                'Headache Severity (0-10)': [3, 2, 4, 5, 2, 1, 0, 0, 1, 3, 4, 2, 1, 0],
                'Fatigue Level (0-5)': [2, 3, 3, 4, 4, 3, 2, 1, 2, 2, 3, 4, 3, 2],
                'Joint Pain (0-10)': [1, 1, 0, 2, 3, 1, 1, 0, 0, 1, 2, 2, 3, 1]
            }
            df_symp = pd.DataFrame(symptom_data)
            # df_symp['DateStr'] = df_symp['Date'].dt.strftime('%b %d') # Format date for display

            # Symptom Line Chart
            df_melt = df_symp.melt(id_vars=['Date'], var_name='Symptom', value_name='Severity')
            fig_symp = px.line(df_melt, x='Date', y='Severity', color='Symptom',
                               title=f"Symptom Severity Over Last {num_days} Days",
                               labels={'Severity': 'Reported Severity', 'Date': 'Date', 'Symptom': 'Symptom Tracked'},
                               markers=True, height=450)
            fig_symp.update_layout(legend_title_text='Symptom',
                                  xaxis_title=None, # Cleaner look
                                  margin=dict(l=10, r=10, t=50, b=10),
                                  plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_symp, use_container_width=True)

        except Exception as e:
            st.error(f"Could not display symptom data: {e}", icon="🩺")


        with st.expander("🔍 Potential Insights (Example based on simulated data)"):
            st.markdown("""
            *   **Headaches:** Show some peaks; consider logging potential triggers like sleep, stress, or diet around those dates via chat.
            *   **Fatigue:** Appears correlated with increased Joint Pain in the latter half of the period.
            *   **Tracking:** Consistent logging helps identify trends. Use the chat feature to log symptoms daily!
            """)

    with tab3:
        st.subheader("Overall Health Metrics")
        # Placeholder Metrics (Simulated)
        try:
            col1, col2, col3 = st.columns(3)
            with col1:
                # Example: Fetch avg steps if available, else show placeholder
                st.metric(label="Avg. Daily Steps", value="7,842", delta="↑ 523 vs last week", delta_color="normal")
            with col2:
                 # Example: Calculate overall adherence
                 overall_adherence = df_meds['Adherence (%)'].mean() if 'df_meds' in locals() else 89
                 st.metric(label="Medication Adherence", value=f"{overall_adherence:.0f}%", delta="↑ 4% vs last month", delta_color="normal")
            with col3:
                # Example: Fetch sleep data if available
                st.metric(label="Avg. Sleep / Night", value="7.2 hrs", delta="↓ 0.3 hrs vs last week", delta_color="inverse")

            st.markdown("---",) # Divider before next chart

            # Placeholder for another chart - e.g., Weight Trend
            st.markdown("##### Weight Trend (Example)")
            weight_dates = pd.date_range(start=datetime.now() - pd.Timedelta(days=89), periods=10, freq='9D')
            weight_data = {'Date': weight_dates,'Weight (kg)': [85.2, 84.8, 85.0, 84.5, 84.6, 84.2, 83.9, 84.0, 83.5, 83.6]}
            df_weight = pd.DataFrame(weight_data)
            fig_weight = px.line(df_weight, x='Date', y='Weight (kg)', markers=True, height=300, title="Weight Over Last 3 Months")
            fig_weight.update_layout(margin=dict(l=10, r=10, t=50, b=10), yaxis_title="Weight (kg)", xaxis_title=None,
                                     plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_weight, use_container_width=True)

        except Exception as e:
            st.error(f"Could not display health trends: {e}", icon="📈")

        st.markdown("---")
        st.markdown("##### Key Observations (Example)")
        st.markdown("""
        *   **Activity:** Positive trend in step count recently.
        *   **Adherence:** Overall adherence is good; check the Medications tab for details.
        *   **Sleep:** Slight decrease in average sleep; monitor impact on fatigue or other symptoms.
        *   **Weight:** Shows a gradual downward trend over the last 3 months.
        """)


# --- Footer ---
st.markdown(f"""
<div class="footer">
    <p>HealthGuard AI Assistant © {datetime.now().year} | Informational purposes only. Consult a healthcare professional for medical advice.</p>
</div>
""", unsafe_allow_html=True)
