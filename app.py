# simple-meridian/app.py
import streamlit as st
import os
import sys

# Set page configuration
st.set_page_config(
    page_title="Simple Meridian",
    page_icon="Ⓜ️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables if they don't exist
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'data' not in st.session_state:
    st.session_state.data = None
if 'meridian_installed' not in st.session_state:
    st.session_state.meridian_installed = False
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = {}
if 'model_results' not in st.session_state:
    st.session_state.model_results = None
if 'optimization_results' not in st.session_state:
    st.session_state.optimization_results = None

# Navigation function
def navigate_to(page):
    st.session_state.page = page
    
def show_footer():
    footer_html = """
    <hr style="border-top: 1px solid #eee;">
    <div style="text-align: center; font-size: 12px; color: #666; padding: 10px 0;">
        <p>
            © 2025 Ali Barfi Bafghi. This independent app uses the open source 
            <a href="https://github.com/google/meridian/tree/main" target="_blank"><strong>Google Meridian</strong></a> 
            library (Google trademark). All rights remain with Google.
        </p>
        <p>
            <a href="https://www.linkedin.com/in/alibarfibafghi/" target="_blank" style="text-decoration: none; margin: 0 10px;">
                <img src="https://img.icons8.com/fluency/24/000000/linkedin.png" alt="LinkedIn" style="vertical-align:middle;"/>
            </a>
            <a href="mailto:ali.barfib@gmail.com" target="_blank" style="text-decoration: none; margin: 0 10px;">
                <img src="https://img.icons8.com/fluency/24/000000/email.png" alt="Email" style="vertical-align:middle;"/>
            </a>
            <a href="https://github.com/alibb007" target="_blank" style="text-decoration: none; margin: 0 10px;">
                <img src="https://img.icons8.com/fluency/24/000000/github.png" alt="GitHub" style="vertical-align:middle;"/>
            </a>
        </p>
    </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)


# Load sample dataset function
def load_sample_dataset(dataset_name):
    import pandas as pd
    
    with st.spinner(f"Loading {dataset_name} dataset..."):
        # Construct the path to the CSV in the 'data' folder
        dataset_map = {
            "simple": "simple_dataset.csv",
            
        }
        
        csv_path = os.path.join(os.path.dirname(__file__), 'data', dataset_map.get(dataset_name, "national_media.csv"))
        
        try:
            # Read the CSV
            st.session_state.data = pd.read_csv(csv_path)
            st.success(f"{dataset_name.title()} dataset loaded successfully!")
            
            # Navigate to Step 1
            st.session_state.page = 'step1'
            st.rerun()
        except Exception as e:
            st.error(f"Error loading dataset: {str(e)}")

# Import page modules
sys.path.append(os.path.dirname(__file__))
from app_pages.home import show_home
from app_pages.step1_upload_and_run import show_upload_and_run  # Renamed from step1_initialization
from app_pages.step2_insights import show_insights            # Renamed from step4_insights
from app_pages.step3_optimization import show_optimization    # Renamed from step5_optimization

# Main function
def main():
    # Sidebar navigation
    with st.sidebar:
        # Logo and title
        col1, col2 = st.columns([1, 4])
        with col1:
            st.image("./pic/Logo.png", width=30)
        with col2:
            st.markdown("<div style='color: #1E3D59; font-weight: 500;'>Simple Meridian</div>", unsafe_allow_html=True)
        
        # Home button
        if st.button("Home", key="nav_home", use_container_width=True, 
                   type="primary", help="Return to home page"):
            navigate_to('home')
        
        # Analysis Steps header
        st.markdown("<div style='font-size: 12px; color: #666; margin: 15px 0 5px 0;'>STEPS</div>", unsafe_allow_html=True)
        
        # Simplified step buttons
        step_buttons = [
            ("1. Upload & Run Model", "step1"),
            ("2. Insights", "step2"),
            ("3. Optimization", "step3"),
        ]
        
        # Create step buttons
        for label, page in step_buttons:
            if st.button(label, key=f"nav_{page}", use_container_width=True):
                navigate_to(page)
        
        # Status indicators at the bottom
        st.markdown("<div style='position: absolute; bottom: 20px; left: 0; right: 0; padding: 0 15px;'>", unsafe_allow_html=True)
        
        # Data status
        status_color = "#4CAF50" if st.session_state.data is not None else "#FFC107"
        status_icon = "✓" if st.session_state.data is not None else "⚠"
        status_text = "Data loaded" if st.session_state.data is not None else "No data loaded"
        
        st.markdown(
            f"""<div class="status-indicator" style="color: {status_color};">
                <span class="status-icon">{status_icon}</span>
                {status_text}
            </div>""", 
            unsafe_allow_html=True
        )
        
        # Meridian API status
        try:
            import meridian
            st.session_state.meridian_installed = True
            status_color = "#4CAF50"
            status_icon = "✓"
            status_text = "Meridian Ready"
        except ImportError:
            st.session_state.meridian_installed = False
            status_color = "#FFC107"
            status_icon = "⚠"
            status_text = "No Meridian"
        
        st.markdown(
            f"""<div class="status-indicator" style="color: {status_color};">
                <span class="status-icon">{status_icon}</span>
                {status_text}
            </div>""", 
            unsafe_allow_html=True
        )
        
        st.markdown("</div>", unsafe_allow_html=True)
            
    # Main content area - show the appropriate page based on navigation state
    if st.session_state.page == 'home':
        show_home()
    elif st.session_state.page == 'step1':
        show_upload_and_run()
    elif st.session_state.page == 'step2':
        show_insights()
    elif st.session_state.page == 'step3':
        show_optimization()

    show_footer()

# Run the app
if __name__ == "__main__":
    main()