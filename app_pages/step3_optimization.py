#step3_optimization.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import tempfile
import pickle
import base64
import io
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
    from meridian.analysis import optimizer
    import tensorflow as tf
    import tensorflow_probability as tfp
    import arviz as az
    MERIDIAN_AVAILABLE = True
except ImportError:
    MERIDIAN_AVAILABLE = False

def load_model_file(file_content):
    """Load model from file"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pkl') as tmp_file:
        tmp_file.write(file_content)
        tmp_path = tmp_file.name
    
    # Load the model from the temporary file
    with open(tmp_path, 'rb') as f:
        model = pickle.load(f)
    
    # Clean up temporary file
    os.unlink(tmp_path)
    return model

def get_model_date_range(mmm):
    """Get the date range available in the model"""
    
    start_date = None
    end_date = None
    
    try:
        # Method 1: Get all time periods from the model
        if hasattr(mmm, 'input_data') and hasattr(mmm.input_data, 'time'):
            all_times = mmm.input_data.time.values.tolist()
            
            # Convert to datetime for better display if possible
            try:
                if isinstance(all_times[0], (str, int, float)):
                    # Try to convert to datetime
                    start_date = pd.to_datetime(all_times[0]).strftime('%Y-%m-%d')
                    end_date = pd.to_datetime(all_times[-1]).strftime('%Y-%m-%d')
                elif hasattr(all_times[0], 'strftime'):
                    # Already datetime-like
                    start_date = all_times[0].strftime('%Y-%m-%d')
                    end_date = all_times[-1].strftime('%Y-%m-%d')
            except:
                pass
        
        # Method 2: Check if data has a date index
        if (start_date is None or end_date is None) and hasattr(mmm, 'input_data') and hasattr(mmm.input_data, 'data'):
            if hasattr(mmm.input_data.data, 'index'):
                if isinstance(mmm.input_data.data.index, pd.DatetimeIndex):
                    start_date = mmm.input_data.data.index[0].strftime('%Y-%m-%d')
                    end_date = mmm.input_data.data.index[-1].strftime('%Y-%m-%d')
        
        # Method 3: Fallback to default dates
        if start_date is None or end_date is None:
            import datetime as dt
            today = dt.datetime.now()
            end_date = today.strftime('%Y-%m-%d')
            start_date = (today - dt.timedelta(days=365)).strftime('%Y-%m-%d')  # One year ago
            
    except Exception as e:
        # Fallback to default dates if anything goes wrong
        import datetime as dt
        today = dt.datetime.now()
        end_date = today.strftime('%Y-%m-%d')
        start_date = (today - dt.timedelta(days=365)).strftime('%Y-%m-%d')  # One year ago
    
    return start_date, end_date

def run_budget_optimization():
    """Function to run the budget optimization with error handling and proper state management"""
    with st.spinner("Running budget optimization... This may take some time."):
        try:
            # Create the BudgetOptimizer object using the loaded model from session state
            budget_optimizer = optimizer.BudgetOptimizer(st.session_state.mmm_object)

            # Format dates properly for optimization
            try:
                start_date = pd.to_datetime(st.session_state.report_start_date).strftime('%Y-%m-%d')
                end_date = pd.to_datetime(st.session_state.report_end_date).strftime('%Y-%m-%d')
            except:
                # If dates cannot be parsed, use the raw string values
                start_date = st.session_state.report_start_date
                end_date = st.session_state.report_end_date

            # Run the optimization using the selected date range
            optimization_results = budget_optimizer.optimize(
                selected_times=(start_date, end_date),
                fixed_budget=True,  # Using fixed budget for simplicity
                use_kpi=False,      # Using revenue as the optimization target
                use_posterior=True,
                use_optimal_frequency=False
            )

            # Store optimization results in session state
            st.session_state.optimization_results = optimization_results
            
            st.success("✅ Budget optimization completed successfully!")
            
            # Display the optimization results immediately
            display_optimization_results(optimization_results)
        except Exception as e:
            st.error(f"Error running optimization: {str(e)}")
            st.info("Try selecting a different date range or check your model configuration.")

def configure_time_selection():
    """Configure time period selection with quick buttons"""
    st.header("Time Period Selection")
    
    # Get model date range from the loaded model
    mmm = st.session_state.mmm_object
    
    # Get all time coordinates from the model
    try:
        time_coords = mmm.input_data.time.values.tolist()
        # Convert to strings if needed
        time_coords = [str(t) for t in time_coords]
        model_start_date = time_coords[0]
        model_end_date = time_coords[-1]
    except Exception as e:
        # Fallback defaults
        model_start_date = "2020-01-01"
        model_end_date = pd.to_datetime("today").strftime('%Y-%m-%d')
        time_coords = None
    
    # Initialize session state if not already set
    if 'report_start_date' not in st.session_state:
        st.session_state.report_start_date = model_start_date
    if 'report_end_date' not in st.session_state:
        st.session_state.report_end_date = model_end_date
    
    # Store the valid time coordinates in session state
    st.session_state.valid_time_coords = time_coords
    
    # Inject CSS for custom button styling (matching insights.py)
    st.markdown("""
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
    """, unsafe_allow_html=True)
    
    # Create a row of quick selection buttons
    st.markdown("#### Quick Date Selection")
    quick_cols = st.columns(5)
    
    with quick_cols[0]:
        if st.button("Full Data", key="opt_full_data"):
            st.session_state.report_start_date = model_start_date
            st.session_state.report_end_date = model_end_date
    
    with quick_cols[1]:
        if st.button("Last Month", key="opt_last_month"):
            end_dt = pd.to_datetime(model_end_date)
            start_dt = end_dt - pd.DateOffset(months=1)
            if time_coords:
                available_dates = [d for d in time_coords if pd.to_datetime(d) >= start_dt]
                st.session_state.report_start_date = available_dates[0] if available_dates else model_start_date
            else:
                st.session_state.report_start_date = start_dt.strftime('%Y-%m-%d')
            st.session_state.report_end_date = model_end_date

    with quick_cols[2]:
        if st.button("Last 3 Months", key="opt_last_3m"):
            end_dt = pd.to_datetime(model_end_date)
            start_dt = end_dt - pd.DateOffset(months=3)
            if time_coords:
                available_dates = [d for d in time_coords if pd.to_datetime(d) >= start_dt]
                st.session_state.report_start_date = available_dates[0] if available_dates else model_start_date
            else:
                st.session_state.report_start_date = start_dt.strftime('%Y-%m-%d')
            st.session_state.report_end_date = model_end_date

    
    with quick_cols[3]:
        if st.button("Last 6 Months", key="opt_last_6m"):
            if time_coords and len(time_coords) > 180:
                st.session_state.report_start_date = time_coords[-180]
            else:
                end_dt = pd.to_datetime(model_end_date)
                start_dt = end_dt - pd.DateOffset(months=6)
                start_str = start_dt.strftime('%Y-%m-%d')
                if time_coords:
                    available_dates = [d for d in time_coords if d >= start_str]
                    if available_dates:
                        st.session_state.report_start_date = available_dates[0]
                    else:
                        st.session_state.report_start_date = model_start_date
                else:
                    st.session_state.report_start_date = start_str
            st.session_state.report_end_date = model_end_date
    
    with quick_cols[4]:
        if st.button("Last Year", key="opt_last_year"):
            if time_coords and len(time_coords) > 365:
                st.session_state.report_start_date = time_coords[-365]
            else:
                end_dt = pd.to_datetime(model_end_date)
                start_dt = end_dt - pd.DateOffset(years=1)
                start_str = start_dt.strftime('%Y-%m-%d')
                if time_coords:
                    available_dates = [d for d in time_coords if d >= start_str]
                    if available_dates:
                        st.session_state.report_start_date = available_dates[0]
                    else:
                        st.session_state.report_start_date = model_start_date
                else:
                    st.session_state.report_start_date = start_str
            st.session_state.report_end_date = model_end_date
    
    # Display selected date range in an info box
    st.info(f"Selected date range: {st.session_state.report_start_date} to {st.session_state.report_end_date}")
    
    # Manual date selection using selectboxes if time_coords is available
    st.markdown("### Manual Date Selection")
    if time_coords:
        col_start, col_end = st.columns(2)
        with col_start:
            start_idx = time_coords.index(st.session_state.report_start_date) if st.session_state.report_start_date in time_coords else 0
            start_date = st.selectbox("Start Date:", options=time_coords, index=start_idx)
            st.session_state.report_start_date = start_date
        with col_end:
            end_idx = time_coords.index(st.session_state.report_end_date) if st.session_state.report_end_date in time_coords else len(time_coords)-1
            end_date = st.selectbox("End Date:", options=time_coords, index=end_idx)
            st.session_state.report_end_date = end_date
    else:
        col_start, col_end = st.columns(2)
        with col_start:
            start_date = st.text_input("Start Date (YYYY-MM-DD):", value=st.session_state.report_start_date)
            st.session_state.report_start_date = start_date
        with col_end:
            end_date = st.text_input("End Date (YYYY-MM-DD):", value=st.session_state.report_end_date)
            st.session_state.report_end_date = end_date

    # Run Budget Optimization button
    st.markdown("---")
    if st.button("Run Budget Optimization", use_container_width=True, type="primary"):
        run_budget_optimization()

def display_export_results_tab(optimization_results, non_optimized_data, optimized_data, is_revenue):
    """Display the export results tab with inline report generation to prevent page jumping"""
    
    st.subheader("Export Optimization Results")
    
    # Add explanation text
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin-bottom: 15px;">
    <h4 style="margin-top: 0;">Export Report</h4>
        <p>Below you'll find a direct download link for your optimization report in HTML format.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get date range
    start_date = st.session_state.report_start_date
    end_date = st.session_state.report_end_date
    st.info(f"Reports include optimization results from {start_date} to {end_date}")
    
    # DIRECTLY GENERATE BOTH REPORTS WITHOUT BUTTONS
    # We generate both reports immediately without waiting for button clicks
    
    # Create a layout for the download links
    st.markdown("### Download Your Reports")
    link_cols = st.columns(2)
    
    # 1. Generate full report with dates
    with link_cols[0]:
        st.markdown("#### Full Report (with date range)")
        try:
            # Generate in memory directly
            with tempfile.TemporaryDirectory() as temp_dir:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                full_report_filename = f"meridian_optimization_{timestamp}.html"
                full_report_path = os.path.join(temp_dir, full_report_filename)
                
                try:
                    optimization_results.output_optimization_summary(
                        full_report_filename,
                        filepath=temp_dir,
                        start_date=start_date,
                        end_date=end_date
                    )
                    
                    # Check if file exists and read content
                    if os.path.exists(full_report_path):
                        with open(full_report_path, 'r', encoding='utf-8') as f:
                            full_report_content = f.read()
                            
                        # Create download link directly
                        b64 = base64.b64encode(full_report_content.encode()).decode()
                        download_link = f"""
                            <a href="data:text/html;base64,{b64}" 
                            download="{full_report_filename}" 
                            style="background-color: #4CAF50; color: white; 
                                   padding: 15px 30px; text-decoration: none; 
                                   font-size: 16px; border-radius: 4px;
                                   font-weight: bold; display: inline-block;
                                   width: 100%; text-align: center;
                                   box-sizing: border-box; margin: 10px 0;">
                                DOWNLOAD FULL REPORT
                            </a>
                        """
                        st.markdown(download_link, unsafe_allow_html=True)
                    else:
                        st.error("Could not generate full report file.")
                except Exception as e:
                    st.error(f"Error generating full report: {str(e)}")
        except Exception as outer_e:
            st.error(f"Unexpected error: {str(outer_e)}")
    
    # 2. Generate simple report without dates
    with link_cols[1]:
        st.markdown("#### Simple Report (no date range)")
        try:
            # Generate in memory directly
            with tempfile.TemporaryDirectory() as temp_dir:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                simple_report_filename = f"meridian_simple_{timestamp}.html"
                simple_report_path = os.path.join(temp_dir, simple_report_filename)
                
                try:
                    # Basic report without date parameters
                    optimization_results.output_optimization_summary(
                        simple_report_filename,
                        filepath=temp_dir
                    )
                    
                    # Check if file exists and read content
                    if os.path.exists(simple_report_path):
                        with open(simple_report_path, 'r', encoding='utf-8') as f:
                            simple_report_content = f.read()
                            
                        # Create download link directly
                        b64 = base64.b64encode(simple_report_content.encode()).decode()
                        download_link = f"""
                            <a href="data:text/html;base64,{b64}" 
                            download="{simple_report_filename}" 
                            style="background-color: #FFA500; color: white; 
                                   padding: 15px 30px; text-decoration: none; 
                                   font-size: 16px; border-radius: 4px;
                                   font-weight: bold; display: inline-block;
                                   width: 100%; text-align: center;
                                   box-sizing: border-box; margin: 10px 0;">
                                DOWNLOAD SIMPLE REPORT
                            </a>
                        """
                        st.markdown(download_link, unsafe_allow_html=True)
                    else:
                        st.error("Could not generate simple report file.")
                except Exception as e:
                    st.error(f"Error generating simple report: {str(e)}")
        except Exception as outer_e:
            st.error(f"Unexpected error: {str(outer_e)}")
    
    # Add some helpful notes
    st.markdown("""
    <div style="background-color: #e6f7ff; padding: 15px; border-radius: 5px; margin-top: 20px;">
    <h4 style="margin-top: 0;">💡 About These Reports</h4>
    <ul>
        <li><strong>Full Report:</strong> Contains optimization results specific to your selected date range.</li>
        <li><strong>Simple Report:</strong> A fallback option that may work better if the full report has any issues.</li>
    </ul>
    <p>Both reports contain visualizations and data tables that can be shared with your team.</p>
    </div>
    """, unsafe_allow_html=True)



def show_optimization():
    """Display the optimization page with budget allocation recommendations"""
    
    st.title("Step 3: Optimization")
    
    # Check if Meridian is installed
    if not MERIDIAN_AVAILABLE:
        st.error("⚠️ Meridian libraries are not installed. Budget optimization is not available.")
        return
    
    # Model loading section
    st.header("Load Your Marketing Model")
    
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
    <p>You can either use the model from the previous steps or upload a saved model file (.pkl).</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if model from previous step is available in session state
    has_session_model = hasattr(st.session_state, 'mmm_object') and st.session_state.mmm_object is not None
    
    model_source = st.radio(
        "Select model source:",
        options=["Use model from previous step", "Upload model file"],
        index=0 if has_session_model else 1
    )
    
    mmm = None
    model_loaded = False
    
    if model_source == "Upload model file":
        uploaded_file = st.file_uploader("Upload Marketing Model File (.pkl)", type=["pkl"])
        
        if uploaded_file is not None:
            try:
                # Load the model
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
            st.warning("⚠️ No model available from previous step. Please upload a model file or go back to step 2.")
    
    # Store optimization results in session state if not already there
    if 'optimization_results' not in st.session_state:
        st.session_state.optimization_results = None
    
    # If model is loaded, show optimization tools
    if model_loaded:
       configure_time_selection()

    
    # If no model is loaded, show guidance
    elif not model_loaded:
        st.info("Please upload a model file or go back to the previous steps to create a model.")
        
        if st.button("Go to Step 1: Upload & Run Model", use_container_width=True):
            st.session_state.page = 'step1'
            st.rerun()

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Back to Insights", use_container_width=True):
            st.session_state.page = 'step2'
            st.experimental_rerun()
    with col2:
        if st.button("Return Home", use_container_width=True):
            st.session_state.page = 'home'
            st.experimental_rerun()
        

def display_optimization_results(optimization_results):
    """Display the optimization results in a user-friendly format with insights"""
    
    st.header("Budget Optimization Results")
    
    try:
        # Extract key metrics from optimization results
        non_optimized_data = optimization_results.nonoptimized_data
        optimized_data = optimization_results.optimized_data
        
        # Determine if using revenue or KPI
        is_revenue = non_optimized_data.attrs.get('is_revenue_kpi', True)
        outcome_label = "Revenue" if is_revenue else "KPI"
        
        # Create tabs for different types of results
        optimization_tabs = st.tabs([
            "Budget Summary",
            "Channel Allocation",
            "Recommendations",
            "Export Results"
        ])
        
        with optimization_tabs[0]:
            st.subheader("Budget Optimization Summary")
            
            # ========== INSIGHT BOX ========== #
            improvement_pct = (
                (optimized_data.attrs['total_incremental_outcome'] - non_optimized_data.attrs['total_incremental_outcome'])
                / non_optimized_data.attrs['total_incremental_outcome']
                * 100
            )
            st.markdown(f"""
            <div style="background-color: #e6f7ff; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 5px solid #1890ff;">
              <h4 style="margin-top: 0;">💡 Insight</h4>
              <ul style="margin: 0; padding-left: 20px;">
                <li>Potential <strong>{improvement_pct:.1f}%</strong> increase in incremental {outcome_label.lower()}</li>
                <li>Same total budget - only reallocation needed</li>
                <li>Move spending from low to high-performing channels</li>
              </ul>
            </div>
            """, unsafe_allow_html=True)
            
            # ========== DATE RANGE (IF AVAILABLE) ========== #
            date_range = ""
            if hasattr(st.session_state, 'report_start_date') and hasattr(st.session_state, 'report_end_date'):
                date_range = f"{st.session_state.report_start_date} to {st.session_state.report_end_date}"
            
            # ========== SCENARIO METRICS (PART 2) ========== #
            # Grab integer/more readable forms for top-line display
            budget_value = int(round(non_optimized_data.attrs['budget'] / 1_000_000))
            roi_value = float(non_optimized_data.attrs['total_roi'])
            opt_roi_value = float(optimized_data.attrs['total_roi'])
            roi_diff = opt_roi_value - roi_value
            inc_rev_value = int(round(non_optimized_data.attrs['total_incremental_outcome'] / 1_000_000))
            opt_inc_rev_value = int(round(optimized_data.attrs['total_incremental_outcome'] / 1_000_000))
            inc_rev_diff = (optimized_data.attrs['total_incremental_outcome'] 
                            - non_optimized_data.attrs['total_incremental_outcome']) / 1_000_000
        
            
            st.markdown(f"""
            <div style="margin-top: 15px; padding: 15px; background-color: #f0f0f0; border-radius: 5px;">
                <p>These estimates are from a fixed budget scenario with ±30% constraints relative to historical spend.
                The non-optimized spend is the historical spend during the period: <strong>{date_range}</strong>.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Create a more visually attractive optimization scenario section
           

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #ffffff, #e6f7ff);
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    border-radius: 10px;
                    padding: 20px;
                    text-align: center;">
                    <p style="font-size: 1.5rem; color: #333; margin-bottom: 10px;">Budget</p>
                    <div style="display: flex; justify-content: space-around; align-items: center;">
                        <div style="width: 40%;">
                            <p style="font-size: 1rem; color: #666; margin: 0;">Non-optimized</p>
                            <p style="font-size: 2rem; font-weight: bold; margin: 5px 0 0;">${budget_value}M</p>
                        </div>
                        <div style="width: 20%; text-align: center;">
                            <p style="font-size: 2rem; color: #888; margin: 0;">→</p>
                        </div>
                        <div style="width: 40%;">
                            <p style="font-size: 1rem; color: #666; margin: 0;">Optimized</p>
                            <p style="font-size: 2rem; font-weight: bold; margin: 5px 0 0;">${budget_value}M</p>
                        </div>
                    </div>
                    <p style="font-size: 3rem;; font-weight: bold; color: #722ed1; margin-top: 10px;">$0 change</p>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #ffffff, #e6f7ff);
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    border-radius: 10px;
                    padding: 20px;
                    text-align: center;">
                    <p style="font-size: 1.5rem; color: #333; margin-bottom: 10px;">Incremental {outcome_label}</p>
                    <div style="display: flex; justify-content: space-around; align-items: center;">
                        <div style="width: 40%;">
                            <p style="font-size: 1rem; color: #666; margin: 0;">Non-optimized</p>
                            <p style="font-size: 2rem; font-weight: bold; margin: 5px 0 0;">${inc_rev_value}M</p>
                        </div>
                        <div style="width: 20%; text-align: center;">
                            <p style="font-size: 2rem; color: #888; margin: 0;">→</p>
                        </div>
                        <div style="width: 40%;">
                            <p style="font-size: 1rem; color: #666; margin: 0;">Optimized</p>
                            <p style="font-size: 2rem; font-weight: bold; margin: 5px 0 0;">${opt_inc_rev_value}M</p>
                        </div>
                    </div>
                    <p style="font-size: 3rem;; font-weight: bold; color: #52c41a; margin-top: 10px;">+${inc_rev_diff:.1f}M</p>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #ffffff, #e6f7ff);
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    border-radius: 10px;
                    padding: 20px;
                    text-align: center;">
                    <p style="font-size: 1.5rem; color: #333; margin-bottom: 10px;">ROI</p>
                    <div style="display: flex; justify-content: space-around; align-items: center;">
                        <div style="width: 40%;">
                            <p style="font-size: 1rem; color: #666; margin: 0;">Non-optimized</p>
                            <p style="font-size: 2rem; font-weight: bold; margin: 5px 0 0;">{roi_value:.2f}</p>
                        </div>
                        <div style="width: 20%; text-align: center;">
                            <p style="font-size: 2rem; color: #888; margin: 0;">→</p>
                        </div>
                        <div style="width: 40%;">
                            <p style="font-size: 1rem; color: #666; margin: 0;">Optimized</p>
                            <p style="font-size: 2rem; font-weight: bold; margin: 5px 0 0;">{opt_roi_value:.2f}</p>
                        </div>
                    </div>
                    <p style="font-size: 3rem;; font-weight: bold; color: #1890ff; margin-top: 10px;">+{roi_diff:.2f}</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # ========== EXPLANATORY BOX ========== #
            st.markdown("""
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <p>This summary shows how the optimized budget allocation compares to your current spending.
               The optimization aims to maximize your results while respecting realistic constraints.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # ========== WATERFALL CHART ========== #
            try:
                # Insight
                waterfall_insight = """
                <div style="background-color: #f0f9eb; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 5px solid #52c41a;">
                  <h4 style="margin-top: 0;">💡 Insight</h4>
                  <ul style="margin: 0; padding-left: 20px;">
                    <li>Blue bars: Channels that benefit from increased investment</li>
                    <li>Red bars: Channels with minimal impact when budget is reduced</li>
                    <li>Focus on largest Blue bars for highest impact</li>
                  </ul>
                </div>
                """
                st.markdown(waterfall_insight, unsafe_allow_html=True)
                # Attempt to use Meridian's built-in waterfall
                waterfall_chart = optimization_results.plot_incremental_outcome_delta()
                
                if hasattr(waterfall_chart, 'to_dict'):
                    st.altair_chart(waterfall_chart, use_container_width=True)
                else:
                    # Plotly fallback
                    channels = optimization_results.optimized_data.channel.values
                    current_outcome = non_optimized_data.sel(metric='mean').incremental_outcome.values
                    opt_outcome = optimized_data.sel(metric='mean').incremental_outcome.values
                    outcome_deltas = opt_outcome - current_outcome
                    
                    waterfall_df = pd.DataFrame({
                        'Channel': list(channels) + ['Total'],
                        'Delta': list(outcome_deltas) + [outcome_deltas.sum()]
                    })
                    
                    fig = go.Figure(go.Waterfall(
                        name="Incremental Outcome Change",
                        orientation="v",
                        measure=["relative"] * len(channels) + ["total"],
                        x=waterfall_df['Channel'],
                        y=waterfall_df['Delta'],
                        textposition="outside",
                        text=[f"${x:,.2f}" for x in waterfall_df['Delta']],
                        connector={"line": {"color": "rgb(63, 63, 63)"}},
                        increasing={"marker": {"color": "#00CC96"}},
                        decreasing={"marker": {"color": "#EF553B"}},
                        totals={"marker": {"color": "#636EFA"}}
                    ))
                    
                    fig.update_layout(
                        title=f"Incremental {outcome_label} Change by Channel",
                        showlegend=False
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
            except Exception as e:
                st.warning(f"Could not generate waterfall chart: {str(e)}")
                # Show basic results in a table
                delta_df = pd.DataFrame({
                    'Channel': optimization_results.optimized_data.channel.values,
                    'Current Outcome': non_optimized_data.sel(metric='mean').incremental_outcome.values,
                    'Optimized Outcome': optimized_data.sel(metric='mean').incremental_outcome.values,
                    'Difference': optimized_data.sel(metric='mean').incremental_outcome.values - 
                                non_optimized_data.sel(metric='mean').incremental_outcome.values
                })
                
                # Add a total row
                total_row = pd.DataFrame({
                    'Channel': ['Total'],
                    'Current Outcome': [delta_df['Current Outcome'].sum()],
                    'Optimized Outcome': [delta_df['Optimized Outcome'].sum()],
                    'Difference': [delta_df['Difference'].sum()]
                })
                
                delta_df = pd.concat([delta_df, total_row], ignore_index=True)
                
                # Format currency columns
                for col in ['Current Outcome', 'Optimized Outcome', 'Difference']:
                    delta_df[col] = delta_df[col].apply(lambda x: f"${x:,.2f}")
                
                st.dataframe(delta_df, use_container_width=True)
        
        with optimization_tabs[1]:
            st.subheader("Channel Budget Allocation")
            
            # INSIGHT: Add insight for budget allocation
            allocation_insight = """
            <div style="background-color: #f0f9eb; padding: 15px; border-radius: 5px; margin-bottom: 20px; border-left: 5px solid #52c41a;">
            <h4 style="margin-top: 0;">💡 Insight</h4>
            <ul style="margin: 0; padding-left: 20px;">
              <li>Focus on channels with large % changes</li>
              <li>These represent biggest efficiency opportunities</li>
              <li>Consider gradual implementation for major shifts</li>
            </ul>
            </div>
            """
            st.markdown(allocation_insight, unsafe_allow_html=True)
            
            # Add explanation
            st.markdown("""
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
            <p>This section shows how the budget is allocated across channels in the optimized scenario compared to your current spending.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Create a DataFrame comparing historical vs optimized allocation
            # Force conversion to list if needed to handle potential edge cases
            try:
                channels = list(optimization_results.optimized_data.channel.values)
                historical_spend = list(optimization_results.nonoptimized_data.sel(metric='mean').spend.values)
                optimized_spend = list(optimization_results.optimized_data.sel(metric='mean').spend.values)
                
                # Calculate differences and percentages
                spend_diff = [opt - hist for opt, hist in zip(optimized_spend, historical_spend)]
                spend_diff_pct = [((opt - hist) / hist * 100) if hist > 0 else 0 
                                for opt, hist in zip(optimized_spend, historical_spend)]
                
                # Create a comparison table
                allocation_df = pd.DataFrame({
                    'Channel': channels,
                    'Current Spend': historical_spend,
                    'Optimized Spend': optimized_spend,
                    'Change': spend_diff,
                    'Change %': spend_diff_pct
                })
                
                # UPDATED: Sort the allocation table by absolute percentage change (highest to lowest)
                allocation_df['Abs Change %'] = allocation_df['Change %'].abs()
                allocation_df = allocation_df.sort_values(by='Abs Change %', ascending=False).drop(columns=['Abs Change %'])
                
                # Format for display
                display_df = allocation_df.copy()
                display_df['Current Spend'] = display_df['Current Spend'].apply(lambda x: f"${x:,.2f}")
                display_df['Optimized Spend'] = display_df['Optimized Spend'].apply(lambda x: f"${x:,.2f}")
                display_df['Change'] = display_df['Change'].apply(lambda x: f"${x:,.2f}")
                display_df['Change %'] = display_df['Change %'].apply(lambda x: f"{x:.1f}%")
                
                # Display table
                st.dataframe(display_df, use_container_width=True)
                
                # Create comparison bar chart
                # INSIGHT: Add bar chart insight
                bar_chart_insight = """
                <div style="background-color: #f0f9eb; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 5px solid #52c41a;">
                <h4 style="margin-top: 0;">💡 Insight</h4>
                <ul style="margin: 0; padding-left: 20px;">
                  <li>Taller bars indicate priority channels</li>
                  <li>Implement changes gradually for channels with large differences</li>
                  <li>Monitor performance closely after budget shifts</li>
                </ul>
                </div>
                """
                st.markdown(bar_chart_insight, unsafe_allow_html=True)
                
                # Prepare data for bar chart - use the sorted order
                sorted_channels = allocation_df['Channel'].tolist()
                sorted_indices = [channels.index(ch) for ch in sorted_channels]
                
                sorted_historical_spend = [historical_spend[i] for i in sorted_indices]
                sorted_optimized_spend = [optimized_spend[i] for i in sorted_indices]
                
                bar_data = pd.DataFrame({
                    'Channel': sorted_channels * 2,
                    'Budget Type': ['Current'] * len(sorted_channels) + ['Optimized'] * len(sorted_channels),
                    'Spend': sorted_historical_spend + sorted_optimized_spend
                })
                
                fig = px.bar(
                    bar_data,
                    x='Channel',
                    y='Spend',
                    color='Budget Type',
                    barmode='group',
                    title='Current vs. Optimized Spend by Channel',
                    color_discrete_map={
                        'Current': '#636EFA',
                        'Optimized': '#00CC96'
                    }
                )
                
                # Format y-axis to include commas and dollar signs
                fig.update_layout(
                    yaxis=dict(
                        tickprefix="$",
                        tickformat=",."
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Show pie charts for allocation comparison
                # INSIGHT: Add pie chart insight
                pie_chart_insight = """
                <div style="background-color: #f0f9eb; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 5px solid #52c41a;">
                <h4 style="margin-top: 0;">💡 Insight</h4>
                <ul style="margin: 0; padding-left: 20px;">
                  <li>Note which channels gain/lose budget share</li>
                  <li>Digital channels often gain share due to better targeting</li>
                  <li>Portfolio balance shifts toward higher-ROI channels</li>
                </ul>
                </div>
                """
                st.markdown(pie_chart_insight, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    fig1 = px.pie(
                        values=historical_spend,
                        names=channels,
                        title='Current Budget Allocation'
                    )
                    st.plotly_chart(fig1, use_container_width=True)
                
                with col2:
                    fig2 = px.pie(
                        values=optimized_spend,
                        names=channels,
                        title='Optimized Budget Allocation'
                    )
                    st.plotly_chart(fig2, use_container_width=True)
            
            except Exception as e:
                st.error(f"Error displaying channel allocation: {str(e)}")
                st.info("There might be an issue with the channel data in your model. Please check your model configuration.")
        
        with optimization_tabs[2]:
            st.subheader("Optimization Recommendations")
            
            try:
                # Calculate overall impact metrics first
                channels = list(optimization_results.optimized_data.channel.values)
                historical_spend = list(optimization_results.nonoptimized_data.sel(metric='mean').spend.values)
                optimized_spend = list(optimization_results.optimized_data.sel(metric='mean').spend.values)
                
                total_current = sum(historical_spend)
                total_optimized = sum(optimized_spend)
                total_diff = total_optimized - total_current
                
                current_roi = non_optimized_data.attrs.get('total_roi', 0)
                optimized_roi = optimized_data.attrs.get('total_roi', 0)
                roi_improvement = optimized_roi - current_roi
                
                current_outcome = non_optimized_data.attrs.get('total_incremental_outcome', 0)
                optimized_outcome = optimized_data.attrs.get('total_incremental_outcome', 0)
                outcome_improvement = optimized_outcome - current_outcome
                outcome_improvement_pct = (outcome_improvement / current_outcome) * 100 if current_outcome > 0 else 0
                
                # OVERALL IMPACT (Moved to top as requested)
                st.markdown("""
                <div style="background-color: #e6f3ff; padding: 20px; border-radius: 8px; margin-bottom: 25px; border-left: 5px solid #1890ff;">
                    <h4 style="margin-top: 0;">Overall Impact of Optimization</h4>
                """, unsafe_allow_html=True)
                
                # UPDATED: Reordered to show budget change first, then revenue, then ROI
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown(f"""
                    <div style="text-align: center;">
                        <p style="font-size: 0.9rem; color: #666;">Budget Change</p>
                        <p style="font-size: 2rem; font-weight: bold; color: #722ed1; margin: 0;">${total_diff:,.0f}</p>
                        <p style="font-size: 1rem; color: #666;">Same total budget</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div style="text-align: center;">
                        <p style="font-size: 0.9rem; color: #666;">Additional {outcome_label}</p>
                        <p style="font-size: 2rem; font-weight: bold; color: #52c41a; margin: 0;">+${outcome_improvement:,.0f}</p>
                        <p style="font-size: 1rem; color: #666;">{outcome_improvement_pct:.1f}% increase</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"""
                    <div style="text-align: center;">
                        <p style="font-size: 0.9rem; color: #666;">ROI Improvement</p>
                        <p style="font-size: 2rem; font-weight: bold; color: #1890ff; margin: 0;">+{roi_improvement:.2f}</p>
                        <p style="font-size: 1rem; color: #666;">{current_roi:.2f} → {optimized_roi:.2f}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                # INSIGHT: Add recommendations insight
                recommendations_insight = """
                <div style="background-color: #f0f9eb; padding: 15px; border-radius: 5px; margin-bottom: 20px; border-left: 5px solid #52c41a;">
                <h4 style="margin-top: 0;">💡 Insight</h4>
                <ul style="margin: 0; padding-left: 20px;">
                  <li>Focus on 2-3 channels with largest recommended changes</li>
                  <li>Test changes on small scale before full implementation</li>
                  <li>Monitor performance closely after shifts</li>
                </ul>
                </div>
                """
                st.markdown(recommendations_insight, unsafe_allow_html=True)
                
                # Create specific recommendations for each channel
                # First, get the top 3 channels with biggest absolute % changes
                channel_changes = []
                for i, channel in enumerate(channels):
                    current = historical_spend[i]
                    optimized = optimized_spend[i]
                    diff = optimized - current
                    diff_pct = (diff / current) * 100 if current > 0 else 0
                    
                    channel_changes.append({
                        'channel': channel,
                        'current': current,
                        'optimized': optimized,
                        'diff': diff,
                        'diff_pct': diff_pct,
                        'abs_diff_pct': abs(diff_pct)
                    })
                
                # Sort by absolute percentage change
                channel_changes.sort(key=lambda x: x['abs_diff_pct'], reverse=True)
                
                # Display recommendations in a visually appealing way
                st.subheader("Channel Recommendations")
                
                # Use columns for a cleaner layout
                col1, col2 = st.columns(2)
                
                # Counter for column balancing
                count = 0
                
                for change in channel_changes:
                    # Determine recommendation type and styling
                    if change['diff_pct'] > 10:
                        recommendation = "Increase budget"
                        color = "#00CC96"  # Green
                        arrow = "↑"
                    elif change['diff_pct'] < -10:
                        recommendation = "Decrease budget"
                        color = "#EF553B"  # Red
                        arrow = "↓"
                    else:
                        recommendation = "Maintain budget"
                        color = "#FFA15A"  # Orange
                        arrow = "→"
                    
                    # Create recommendation card
                    rec_card = f"""
                    <div style="border-left: 5px solid {color}; padding: 15px; margin-bottom: 15px; background-color: #f8f9fa; border-radius: 4px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <h4 style="margin: 0;">{change['channel']}</h4>
                            <span style="font-weight: bold; color: {color}; font-size: 1.2rem;">{arrow} {abs(change['diff_pct']):.1f}%</span>
                        </div>
                        <p style="margin: 10px 0 5px 0;"><strong>{recommendation}</strong></p>
                        <div style="display: flex; justify-content: space-between; font-size: 0.9rem;">
                            <span>Current: ${change['current']:,.0f}</span>
                            <span>→</span>
                            <span>Optimized: ${change['optimized']:,.0f}</span>
                        </div>
                    </div>
                    """
                    
                    # Alternate between columns
                    if count % 2 == 0:
                        with col1:
                            st.markdown(rec_card, unsafe_allow_html=True)
                    else:
                        with col2:
                            st.markdown(rec_card, unsafe_allow_html=True)
                    
                    count += 1
                
            except Exception as e:
                st.error(f"Error displaying recommendations: {str(e)}")
                st.info("There might be an issue with the optimization data. Please try running the optimization again.")
        
        with optimization_tabs[3]:
            # Call the updated export function instead of implementing it here
            display_export_results_tab(optimization_results, non_optimized_data, optimized_data, is_revenue)
    
    except Exception as e:
        st.error(f"Error displaying optimization results: {str(e)}")
        st.info("Please try running the optimization again or reload your model.")

def display_export_results_tab(optimization_results, non_optimized_data, optimized_data, is_revenue):
    """Display the export tab with simplified download options"""
    st.subheader("Export Results")
    
    try:
        # Create exportable dataframes
        channels = list(optimization_results.optimized_data.channel.values)
        historical_spend = list(non_optimized_data.sel(metric='mean').spend.values)
        optimized_spend = list(optimized_data.sel(metric='mean').spend.values)
        
        outcome_label = "Revenue" if non_optimized_data.attrs.get('is_revenue_kpi', True) else "KPI"
        
        current_outcome = list(non_optimized_data.sel(metric='mean').incremental_outcome.values)
        optimized_outcome = list(optimized_data.sel(metric='mean').incremental_outcome.values)
        
        # Calculate differences
        spend_diff = [opt - hist for opt, hist in zip(optimized_spend, historical_spend)]
        spend_diff_pct = [((opt - hist) / hist * 100) if hist > 0 else 0 
                        for opt, hist in zip(optimized_spend, historical_spend)]
        
        outcome_diff = [opt - curr for opt, curr in zip(optimized_outcome, current_outcome)]
        outcome_diff_pct = [((opt - curr) / curr * 100) if curr > 0 else 0 
                          for opt, curr in zip(optimized_outcome, current_outcome)]
        
        # Create a complete summary dataframe
        export_df = pd.DataFrame({
            'Channel': channels,
            'Current Spend': historical_spend,
            'Optimized Spend': optimized_spend,
            'Spend Difference': spend_diff,
            'Spend Difference %': spend_diff_pct,
            f'Current Incremental {outcome_label}': current_outcome,
            f'Optimized Incremental {outcome_label}': optimized_outcome,
            f'{outcome_label} Difference': outcome_diff,
            f'{outcome_label} Difference %': outcome_diff_pct
        })
        
        # Add a total row
        totals = pd.DataFrame({
            'Channel': ['Total'],
            'Current Spend': [sum(historical_spend)],
            'Optimized Spend': [sum(optimized_spend)],
            'Spend Difference': [sum(spend_diff)],
            'Spend Difference %': [sum(spend_diff) / sum(historical_spend) * 100 if sum(historical_spend) > 0 else 0],
            f'Current Incremental {outcome_label}': [sum(current_outcome)],
            f'Optimized Incremental {outcome_label}': [sum(optimized_outcome)],
            f'{outcome_label} Difference': [sum(outcome_diff)],
            f'{outcome_label} Difference %': [sum(outcome_diff) / sum(current_outcome) * 100 if sum(current_outcome) > 0 else 0]
        })
        
        export_df = pd.concat([export_df, totals], ignore_index=True)
        
        # Show preview of data
        st.dataframe(export_df.style.format({
            'Current Spend': '${:,.2f}',
            'Optimized Spend': '${:,.2f}',
            'Spend Difference': '${:,.2f}',
            'Spend Difference %': '{:.2f}%',
            f'Current Incremental {outcome_label}': '${:,.2f}',
            f'Optimized Incremental {outcome_label}': '${:,.2f}',
            f'{outcome_label} Difference': '${:,.2f}',
            f'{outcome_label} Difference %': '{:.2f}%'
        }), use_container_width=True)
        
        # Two simple download buttons
        col1, col2 = st.columns(2)
        
        # Excel download button
        with col1:
            excel_buffer = io.BytesIO()
            export_df.to_excel(excel_buffer, index=False, engine='xlsxwriter')
            excel_b64 = base64.b64encode(excel_buffer.getvalue()).decode()
            excel_href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{excel_b64}" download="budget_optimization_results.xlsx" class="btn" style="background-color: #1890ff; color: white; padding: 15px 30px; text-decoration: none; font-size: 16px; border-radius: 4px; font-weight: bold; display: inline-block; width: 100%; text-align: center; box-sizing: border-box; margin: 10px 0;">DOWNLOAD EXCEL</a>'
            st.markdown(excel_href, unsafe_allow_html=True)
        
        # HTML Report button
        with col2:
            try:
                # Get date range if available
                start_date = ""
                end_date = ""
                if hasattr(st.session_state, 'report_start_date') and hasattr(st.session_state, 'report_end_date'):
                    start_date = st.session_state.report_start_date
                    end_date = st.session_state.report_end_date
                
                # Generate HTML report directly
                with tempfile.TemporaryDirectory() as temp_dir:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    report_filename = f"meridian_report_{timestamp}.html"
                    report_path = os.path.join(temp_dir, report_filename)
                    
                    try:
                        # Basic report without date parameters
                        optimization_results.output_optimization_summary(
                            report_filename,
                            filepath=temp_dir
                        )
                        
                        # Check if file exists and read content
                        if os.path.exists(report_path):
                            with open(report_path, 'r', encoding='utf-8') as f:
                                report_content = f.read()
                                
                            # Create download link directly
                            b64 = base64.b64encode(report_content.encode()).decode()
                            download_link = f"""
                                <a href="data:text/html;base64,{b64}" 
                                download="{report_filename}" 
                                style="background-color:  #b71c1c; color: white; 
                                       padding: 15px 30px; text-decoration: none; 
                                       font-size: 16px; border-radius: 4px;
                                       font-weight: bold; display: inline-block;
                                       width: 100%; text-align: center;
                                       box-sizing: border-box; margin: 10px 0;">
                                    DOWNLOAD MERIDIAN HTML REPORT
                                </a>
                            """
                            st.markdown(download_link, unsafe_allow_html=True)
                        else:
                            st.error("Could not generate HTML report file.")
                    except Exception as e:
                        st.error(f"Error generating HTML report: {str(e)}")
            except Exception as outer_e:
                st.error(f"Unexpected error: {str(outer_e)}")
    
    except Exception as e:
        st.error(f"Error preparing export data: {str(e)}")
        st.info("Please try running the optimization again before exporting results.")
    
    except Exception as e:
        st.error(f"Error preparing export data: {str(e)}")
        st.info("Please try running the optimization again before exporting results.")