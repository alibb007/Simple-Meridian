import streamlit as st
import os
import pandas as pd


def show_home():
    """Display the home page of the application"""
    
    # Main header with logo and title
    col1, col2 = st.columns([1, 5])
    with col1:
        logo_path = "./pic/Logo.png"
        st.image(logo_path, width=200)
    with col2:
        st.title("Simple Meridian")
     
    
    st.markdown("---")
    
    # App description with hyperlink for Meridian
    st.markdown("""
    ## Measure Your Marketing Impact Without Any Coding
    
    Simple Meridian helps you understand **which marketing channels are working** and **how to optimize your budget**
    without needing any technical expertise.
    
    ### 👉 What This Tool Does:
    
    * **Analyzes** your marketing data automatically
    * **Measures** the impact of each marketing channel 
    * **Shows** which channels give the best return on investment
    * **Recommends** the optimal budget allocation
    
    ###  In Just Three Simple Steps:
    """, unsafe_allow_html=True)
    
    # Workflow steps - simplified to 3 steps
    workflow_cols = st.columns(3)
    
    workflow_steps = [
        ("1. Upload & Run", "Upload your marketing data and let the system analyze it", "📊"),
        ("2. Insights", "See which channels are working and why", "💡"),
        ("3. Optimization", "Get recommendations on how to improve your budget allocation", "💰"),
    ]
    
    for i, (col, (title, desc, icon)) in enumerate(zip(workflow_cols, workflow_steps)):
        with col:
            st.markdown(f"""
            <div style="text-align: center; padding: 20px; border-radius: 10px; background-color: #f8f9fa; height: 180px;">
                <div style="font-size: 36px; margin-bottom: 10px;">{icon}</div>
                <div style="font-weight: bold; font-size: 18px; margin-bottom: 10px;">{title}</div>
                <div style="font-size: 14px; color: #666;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Add connecting arrows between steps (except for the last one)
            if i < len(workflow_steps) :
                # Use the arrow icon by default, but for the last connection use 💸
                arrow_icon = "💸" if i == len(workflow_steps) - 1 else "➡️"
                st.markdown(f"""
                <div style="text-align: center; margin-top: 80px; font-size: 24px;">{arrow_icon}</div>
                """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Start button to navigate to first step
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("START NOW", key="start_button", use_container_width=True):
            st.session_state.page = 'step1'
            st.rerun()
    
    # About Marketing Mix Modeling section - simple explanation for beginners
    st.markdown("""
    ## What is Marketing Mix Modeling?
    
    Marketing Mix Modeling (MMM) is a powerful analysis technique that helps you understand how your marketing activities affect your business results. 
    
    Without getting technical, it answers questions like:
    
    * **Which marketing channels drive the most sales?**
    * **What's the ROI for each marketing activity?**
    * **How should I divide my marketing budget for maximum results?**
    * **What would happen if I shifted budget between channels?**
    
    Simple Meridian uses Google's advanced MMM technology but with an interface that anyone can use - no statistics or coding knowledge required!
    """)
    
    # Available Datasets section header
    st.markdown('<h2>Try with Sample Data</h2>', unsafe_allow_html=True)

    
    # Dataset options - only keep simple dataset
    datasets = [
        {
            "key": "simple",
            "title": "Simple Synthetic Dataset",
            "desc": "Basic example for quick testing",
            "icon": "📋",
            "filename": "simple_dataset.csv"
        }
    ]
    
    # Create centered column for dataset
    col1, col2, col3 = st.columns([1, 2, 1])
    
    # Display dataset in center column
    with col2:
        with st.container():
            st.markdown(f"""
            <div style="display: flex; background-color: white; padding: 15px; border-radius: 8px; 
                    border: 1px solid #eee; margin-bottom: 15px; align-items: center; height: 120px;">
                <div style="font-size: 32px; margin-right: 15px; color: #1E3D59;">{datasets[0]['icon']}</div>
                <div style="flex: 1;">
                    <div style="font-weight: 500; margin: 0; font-size: 18px;">{datasets[0]['title']}</div>
                    <div style="color: #666; font-size: 14px; margin: 5px 0;">{datasets[0]['desc']}</div>
                </div>
            </div>
""", unsafe_allow_html=True)
            
            # Load button
            if st.button(f"Try {datasets[0]['title']}", key=f"load_{datasets[0]['key']}", use_container_width=True):
                load_sample_dataset(datasets[0]['key'], datasets[0]['filename'])
  

def load_sample_dataset(dataset_key, filename):
    """Load a sample dataset from the data folder"""
    
    with st.spinner(f"Loading {dataset_key} dataset..."):
        try:
            # Construct the path to the CSV in the 'data' folder
            csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', filename)
            
            # Read the CSV
            st.session_state.data = pd.read_csv(csv_path)
            
            # Navigate to Step 1
            st.session_state.page = 'step1'
            st.success(f"{dataset_key.title()} dataset loaded successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Error loading dataset: {str(e)}")