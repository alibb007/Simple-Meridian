# /app_pages/step4_insights.py
import streamlit as st
import pandas as pd
import numpy as np
import os
import tempfile
import pickle
import base64
from io import BytesIO
from datetime import datetime

# Import Meridian libraries (will only work if properly installed)
try:
    import meridian
    from meridian import constants
    from meridian.data import load
    from meridian.model import model
    from meridian.model import spec
    from meridian.model import prior_distribution
    from meridian.analysis import analyzer
    from meridian.analysis import visualizer
    from meridian.analysis import summarizer
    import tensorflow as tf
    import tensorflow_probability as tfp
    import arviz as az
    MERIDIAN_AVAILABLE = True
except ImportError:
    MERIDIAN_AVAILABLE = False

# Import visualization utilities
from utils.visualization import (
    create_roi_visualization, 
    create_media_contribution_visualization,
    create_response_curves_visualization,
    create_model_diagnostics_visualization,
    create_export_report,
    get_model_date_range
)
# Add this to the top of step4_insights.py after imports
@st.cache_resource(ttl=3600)
def get_analyzer(mmm):
    """Cache analyzer object to avoid recreating it for each tab"""
    return analyzer.Analyzer(mmm)

@st.cache_resource(ttl=3600)
def get_media_summary(mmm):
    """Cache media summary object to avoid recreating it for each tab"""
    return visualizer.MediaSummary(mmm)

# Cache decorator to improve performance
@st.cache_data(ttl=3600)
def load_model_file(file_content):
    """Load model from file with caching to improve performance"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pkl') as tmp_file:
        tmp_file.write(file_content)
        tmp_path = tmp_file.name
    
    # Load the model from the temporary file
    with open(tmp_path, 'rb') as f:
        model = pickle.load(f)
    
    # Clean up temporary file
    os.unlink(tmp_path)
    return model

def show_insights():
    """Display the insights page with visualizations and analysis"""
    
    st.title("Step 4: Insights & Visualization")
    
    # Check if Meridian is installed
    if not MERIDIAN_AVAILABLE:
        st.error("⚠️ Meridian libraries are not installed. Some visualizations may not be available.")
        
    # Provide option to upload model pickle file
    st.header("4.1 Load Meridian Model")
    
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
    <h4 style="margin-top: 0;">Insights from Your Meridian Model</h4>
    <p>You can either use the model from the previous step or upload a saved Meridian model file (.pkl) to visualize insights.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if model from previous step is available in session state
    has_session_model = hasattr(st.session_state, 'mmm_object') and st.session_state.mmm_object is not None
    has_model_results = hasattr(st.session_state, 'model_results') and st.session_state.model_results is not None
    
    model_source = st.radio(
        "Select model source:",
        options=["Upload model file", "Use model from previous step"],
        index=1 if has_session_model else 0
    )
    
    mmm = None
    model_loaded = False
    
    if model_source == "Upload model file":
        uploaded_file = st.file_uploader("Upload Meridian Model File (.pkl)", type=["pkl"])
        
        if uploaded_file is not None:
            try:
                # Use cached function to load model
                mmm = load_model_file(uploaded_file.getvalue())
                
                # Store in session state for future use
                st.session_state.mmm_object = mmm
                model_loaded = True
                st.success("✅ Model loaded successfully!")
                
            except Exception as e:
                st.error(f"Error loading model file: {str(e)}")
    
    elif model_source == "Use model from previous step":
        if has_session_model:
            mmm = st.session_state.mmm_object
            model_loaded = True
            st.success("✅ Using model from previous step")
        else:
            st.warning("⚠️ No model available from previous step. Please run a model in Step 3 or upload a model file.")
    
    # If no model is loaded, but we have model results, we can still show some insights
    if not model_loaded and has_model_results:
        st.info("No Meridian model object is available, but basic model results are present. Limited visualizations will be available.")
    

    
    if model_loaded or has_model_results:
        selected_tab = st.radio(
            "Select visualization:",
            ["Model Diagnostics","ROI Analysis", "Media Contribution", "Response Curves", "Export Insights"],
            horizontal=True
        )
        
        if selected_tab == "ROI Analysis":
            st.subheader("Return on Investment (ROI) Analysis")
            
            if model_loaded and MERIDIAN_AVAILABLE:
                with st.spinner("Generating ROI visualization..."):
                    create_roi_visualization(mmm)
            
            elif has_model_results:
                # Use plotly for basic ROI visualization from model_results
                model_results = st.session_state.model_results
                
                if 'meridian_data' in model_results and model_results['meridian_data'].get('roi') is not None:
                    roi_df = pd.DataFrame(model_results['meridian_data']['roi'])
                    import plotly.express as px
                    fig = px.bar(
                        roi_df.reset_index(),
                        x='index',
                        y='roi_mean',
                        error_y='roi_std',
                        title="Return on Investment (ROI) by Channel",
                        labels={'index': 'Channel', 'roi_mean': 'ROI'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    st.dataframe(roi_df, use_container_width=True)
                else:
                    st.info("ROI data not available in the model results")
        
        elif selected_tab == "Media Contribution":
            st.subheader("Media Contribution Analysis")
            
            if model_loaded and MERIDIAN_AVAILABLE:
                with st.spinner("Generating media contribution visualization..."):
                    create_media_contribution_visualization(mmm)
            
            elif has_model_results:
                # Use plotly for basic contribution visualization from model_results
                model_results = st.session_state.model_results
                
                if 'meridian_data' in model_results and model_results['meridian_data'].get('attribution') is not None:
                    attribution_df = pd.DataFrame(model_results['meridian_data']['attribution'])
                    
                    # Pie chart for attribution
                    import plotly.express as px
                    fig = px.pie(
                        attribution_df.reset_index(),
                        names='index',
                        values='mean',
                        title="KPI Attribution by Channel"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Bar chart for attribution
                    fig2 = px.bar(
                        attribution_df.reset_index(),
                        x='index',
                        y='mean',
                        error_y='std',
                        title="Channel Attribution",
                        labels={'index': 'Channel', 'mean': 'Attribution'}
                    )
                    st.plotly_chart(fig2, use_container_width=True)
                    
                    # Display attribution table
                    st.dataframe(attribution_df, use_container_width=True)
                else:
                    st.info("Attribution data not available in the model results")
        
            
        elif selected_tab ==  "Response Curves":
            st.subheader("Response Curves Analysis")
            
            if model_loaded and MERIDIAN_AVAILABLE:
                # Plot settings
                col1, col2 = st.columns(2)
                with col1:
                    plot_separately = st.checkbox("Plot channels separately", value=False)
                with col2:
                    include_ci = st.checkbox("Include confidence intervals", value=False)
                
                if not plot_separately:
                    num_channels = st.slider("Number of channels to display", 1, 10, 5)
                else:
                    num_channels = None
                
                with st.spinner("Generating response curves visualization..."):
                    create_response_curves_visualization(mmm, plot_separately, include_ci, num_channels)
            
            else:
                st.info("Response curves analysis requires a Meridian model object. Please upload a model file.")
        
        elif selected_tab == "Model Diagnostics":
            st.subheader("Model Diagnostics")
            
            if model_loaded and MERIDIAN_AVAILABLE:
                with st.spinner("Generating model diagnostics visualization..."):
                    create_model_diagnostics_visualization(mmm)
            
            else:
                st.info("Model diagnostics requires a Meridian model object. Please upload a model file.")
       
        
        
        # Export Insights Tab - Updated with quick time selection buttons
        elif selected_tab == "Export Insights":
            st.subheader("Export Insights")
            
            if model_loaded:
                # Get model date range for reporting
                start_date, end_date = get_model_date_range(mmm)
                
                # Fallback defaults if not available
                if not start_date:
                    start_date = "2020-01-01"
                if not end_date:
                    end_date = pd.to_datetime("today").strftime('%Y-%m-%d')

                # Initialize session state if not already set
                if 'report_start_date' not in st.session_state:
                    st.session_state.report_start_date = start_date
                if 'report_end_date' not in st.session_state:
                    st.session_state.report_end_date = end_date

                # Convert string dates to datetime objects for calculations
                model_start_dt = pd.to_datetime(start_date)
                model_end_dt = pd.to_datetime(end_date)

                # Inject CSS for custom button styling:
                st.markdown(
                    """
                    <style>
                    /* Remove margin and padding from the button container */
                    div.row-widget.stButton > div {
                        margin: 0 !important;
                        padding: 0 !important;
                    }
                    /* Style the buttons with a red border and no extra margin */
                    div.stButton > button {
                        border: 2px solid red;
                        border-radius: 5px;
                        padding: 0.4rem 0.8rem;
                        margin: 0 !important;
                    }
                    </style>
                    """,
                    unsafe_allow_html=True
                )
                
                st.markdown("#### Quick Date Selection")
                # Create 5 columns for buttons (all on one line)
                quick_cols = st.columns(5)

                with quick_cols[0]:
                    if st.button("Full Data", key="export_full_data"):
                        st.session_state.report_start_date = start_date
                        st.session_state.report_end_date = end_date

                with quick_cols[1]:
                    if st.button("Last Month", key="export_last_month"):
                        new_start = model_end_dt - pd.DateOffset(days=30)
                        new_start = max(new_start, model_start_dt)
                        st.session_state.report_start_date = new_start.strftime('%Y-%m-%d')
                        st.session_state.report_end_date = model_end_dt.strftime('%Y-%m-%d')

                with quick_cols[2]:
                    if st.button("Last 3 Months", key="export_last_3m"):
                        new_start = model_end_dt - pd.DateOffset(months=3)
                        new_start = max(new_start, model_start_dt)
                        st.session_state.report_start_date = new_start.strftime('%Y-%m-%d')
                        st.session_state.report_end_date = model_end_dt.strftime('%Y-%m-%d')

                with quick_cols[3]:
                    if st.button("Last 6 Months", key="export_last_6m"):
                        new_start = model_end_dt - pd.DateOffset(months=6)
                        new_start = max(new_start, model_start_dt)
                        st.session_state.report_start_date = new_start.strftime('%Y-%m-%d')
                        st.session_state.report_end_date = model_end_dt.strftime('%Y-%m-%d')

                with quick_cols[4]:
                    if st.button("Last Year", key="export_last_year"):
                        new_start = model_end_dt - pd.DateOffset(years=1)
                        new_start = max(new_start, model_start_dt)
                        st.session_state.report_start_date = new_start.strftime('%Y-%m-%d')
                        st.session_state.report_end_date = model_end_dt.strftime('%Y-%m-%d')
                # Removed the "Or select Full Model Date Range:" section.
                
                st.markdown("---")
                st.markdown("### Manual Date Selection")
                col_start, col_end = st.columns(2)
                with col_start:
                    new_start_date = st.text_input(
                        "Start Date (YYYY-MM-DD)", 
                        value=st.session_state.report_start_date,
                        key="export_start_date",
                        help="Update the start date. The system normally sets the end date to the model's end date."
                    )
                    st.session_state.report_start_date = new_start_date
                with col_end:
                    new_end_date = st.text_input(
                        "End Date (YYYY-MM-DD)", 
                        value=st.session_state.report_end_date,
                        key="export_end_date",
                        help="End date defaults to the model's end date. You can override it here if desired."
                    )
                    st.session_state.report_end_date = new_end_date

                if st.button("Generate Report", key="generate_report_btn", use_container_width=True):
                    with st.spinner("Generating Meridian HTML report..."):
                        create_export_report(
                            mmm, 
                            start_date=st.session_state.report_start_date, 
                            end_date=st.session_state.report_end_date
                        )
            
            else:
                st.warning("Export features require a loaded Meridian model. Please upload a model file.")

        

    # Navigation buttons update (at the bottom of your insights page)
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back to Model Runner", key="back_to_model_btn"):
            st.session_state.page = 'step1'
            st.experimental_rerun()
    with col2:
        if st.button("Continue to Optimization ➡️", key="goto_report_btn"):
            st.session_state.page = 'step3'
            st.experimental_rerun()
