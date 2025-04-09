import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
import base64
import pickle
from io import BytesIO
from datetime import datetime

# Import Meridian libraries (will be available after installation via requirements.txt)
try:
    import meridian
    from meridian import constants
    from meridian.data import load
    from meridian.model import model
    from meridian.model import spec
    from meridian.model import prior_distribution
    from meridian.analysis import analyzer
    from meridian.analysis import visualizer
    MERIDIAN_AVAILABLE = True
except ImportError:
    MERIDIAN_AVAILABLE = False  # Will proceed without Meridian functionality if not installed

def show_upload_and_run():
    """Display the upload data and run model page"""
    
    st.title("Step 1: Upload Data & Run Model")
    
    # Check if data is loaded
    if 'data' not in st.session_state or st.session_state.data is None:
        # Data upload section
        st.subheader("Upload Your Marketing Data")
        
        st.markdown("""
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
        <h4 style="margin-top: 0;">What data do I need?</h4>
        <p>For best results, your data should include:</p>
        <ul>
            <li><strong>Date column:</strong> Weekly Data ( It's better to have 3 years of Data)</li>
            <li><strong>Revenue/Sales column:</strong> What you're trying to measure</li>
            <li><strong>Marketing channels:</strong> Spend and metrics (like Impression) for each channel</li>
            <li><strong>Control variables:</strong> Factors like seasonality, pricing, etc. (optional but it's better to have)</li>
        </ul>
        <p>Excel or CSV files are accepted.</p>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Upload your data file",
            type=["csv", "xlsx", "xls"],
            help="Upload your marketing data file in CSV or Excel format"
        )
        
        if uploaded_file is not None:
            # Read the file
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                
                # Display file details in a nicer format
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Rows", f"{df.shape[0]:,}")
                with col2:
                    st.metric("Columns", f"{df.shape[1]}")
                with col3:
                    st.metric("File Size", f"{uploaded_file.size / 1024:.2f} KB")
                
                st.session_state.data = df
                
                # Success message
                st.success(f"✅ Successfully loaded data with {df.shape[0]} rows and {df.shape[1]} columns!")
                
            except Exception as e:
                st.error(f"❌ Error reading file: {str(e)}")
                return
    
    # If data is loaded, show data preview and model configuration
    if 'data' in st.session_state and st.session_state.data is not None:
        df = st.session_state.data
        
        # Data Preview
        st.subheader("Data Preview")
        st.dataframe(df.head(5), use_container_width=True)
        
        # Model configuration
        st.subheader("Model Configuration")
        
        st.markdown("""
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
        <p>Configure your model by selecting the key columns below. The system will analyze the relationship
        between your marketing activities and your revenue.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 1. Date column selection
        st.markdown("### 1. Date Column (required)")
        date_cols = []
        for col in df.columns:
            # Check if column is datetime
            if pd.api.types.is_datetime64_dtype(df[col]):
                date_cols.append(col)
            # Check if column could be converted to datetime
            elif df[col].dtype == 'object' or df[col].dtype == 'string':
                try:
                    pd.to_datetime(df[col].iloc[0] if not df[col].empty else '', errors='raise')
                    date_cols.append(col)
                except:
                    pass

        # Auto-detect date columns that contain 'date' or 'time'
        suggested_date_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['date', 'time', 'week', 'month', 'year', 'day'])]
        for col in suggested_date_cols:
            if col not in date_cols:
                date_cols.append(col)

        # Date column selection
        if date_cols:
            date_col = st.selectbox(
                "Select Date Column:",
                options=date_cols,
                index=0,
                help="This column contains the time periods for your data"
            )
        else:
            date_col = st.selectbox(
                "Select Date Column:",
                options=df.columns.tolist(),
                help="This column contains the time periods for your data"
            )
            st.warning("⚠️ No date columns detected. Please select a column that contains dates.")
        
        # 2. Target KPI selection (revenue only for simplicity)
        st.markdown("### 2. Revenue/Target Column (required)")
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        
        # Auto-detect revenue columns with improved keywords
        revenue_keywords = ['revenue', 'sales', 'conversion', 'kpi', 'target', 'outcome', 'roi', 'profit', 'income', 'return']
        suggested_revenue_cols = [col for col in numeric_cols if any(keyword in col.lower() for keyword in revenue_keywords)]
        
        if suggested_revenue_cols:
            target_col = st.selectbox(
                "Select Revenue/Target Column:",
                options=numeric_cols,
                index=numeric_cols.index(suggested_revenue_cols[0]) if suggested_revenue_cols[0] in numeric_cols else 0,
                help="This is the metric you want to analyze (e.g., revenue, sales, conversions)"
            )
        else:
            target_col = st.selectbox(
                "Select Revenue/Target Column:",
                options=numeric_cols,
                help="This is the metric you want to analyze (e.g., revenue, sales, conversions)"
            )
        
        # 3. Media Variables with improved detection
        st.markdown("### 3. Media Metrics Columns")
        # Auto-detect media exposure columns with better pattern matching
        media_keywords = ['impression', 'view', 'click', 'ad', 'campaign', 'media', 'channel', 'exposure', 'reach', 'traffic']
        # Fix: ensure we don't include spend columns in media metrics
        suggested_media_cols = [col for col in numeric_cols if 
                               any(keyword in col.lower() for keyword in media_keywords) and 
                               not any(spend_keyword in col.lower() for spend_keyword in ['spend', 'cost', 'budget'])]
        
        media_channels = st.multiselect(
            "Select Media Metrics Columns:",
            options=numeric_cols,
            default=suggested_media_cols,
            help="These columns contain metrics like impressions, clicks, views"
        )
        
        # 4. Media Spend with improved detection
        st.markdown("### 4. Media Spend Columns")
        # Auto-detect spend columns - ensure they don't overlap with media metrics
        spend_keywords = ['spend', 'cost', 'budget', 'investment', 'expense']
        suggested_spend_cols = [col for col in numeric_cols if 
                               any(keyword in col.lower() for keyword in spend_keywords) and
                               col not in media_channels]
        
        media_spend_channels = st.multiselect(
            "Select Media Spend Columns:",
            options=numeric_cols,
            default=suggested_spend_cols,
            help="These columns contain your media spending data"
        )
        
        # 5. Control Variables (Optional but recommended)
        st.markdown("### 5. Control Variables (Recommended)")
        st.info("Control variables help account for external factors that affect your results but aren't marketing channels.")
        
        # Auto-detect control variables with expanded keywords
        control_keywords = ['control', 'season', 'holiday', 'price', 'competitor', 'weather', 'promotion', 
                           'trend', 'gdp', 'unemployment', 'cpi', 'inflation', 'discount', 'industry', 
                           'sentiment', 'stock', 'supply', 'demand', 'covid', 'event']
        
        # Ensure control variables don't overlap with already selected columns
        already_selected = [target_col] + media_channels + media_spend_channels
        suggested_control_cols = [col for col in numeric_cols if 
                                 any(keyword in col.lower() for keyword in control_keywords) and 
                                 col not in already_selected]
        
        control_vars = st.multiselect(
            "Select Control Variables:",
            options=[col for col in numeric_cols if col not in already_selected],
            default=suggested_control_cols,
            help="These columns contain variables that may affect your revenue but aren't media channels"
        )
        
        # 6. Channel Mapping (Display names)
        st.markdown("### 6. Channel Mapping")
        
        st.markdown("""
        <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin-bottom: 15px;">
        <p>Assign readable display names to your media channels for clearer reporting.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Media channel mapping
        channel_mappings = {}
        
        if media_channels:
            st.markdown("#### Media Metrics Channel Names")
            media_to_channel = {}
            
            for i, channel in enumerate(media_channels):
                col1, col2 = st.columns([3, 3])
                
                with col1:
                    st.markdown(f"**Column: {channel}**")
                
                with col2:
                    # Create clean display name by default - improved pattern matching
                    display_name = channel
                    for suffix in ['_impression', '_impressions', '_click', '_clicks', '_view', '_views', '_media', '_channel', '_traffic']:
                        display_name = display_name.replace(suffix, '')
                    
                    # Let user edit the display name
                    display_name = st.text_input(
                        "Display Name:",
                        value=display_name,
                        key=f"media_name_{i}"
                    )
                
                # Update mapping
                media_to_channel[channel] = display_name
            
            channel_mappings['media_to_channel'] = media_to_channel
        
        # Media spend mapping
        if media_spend_channels:
            st.markdown("#### Media Spend Channel Names")
            media_spend_to_channel = {}
            
            for i, channel in enumerate(media_spend_channels):
                col1, col2 = st.columns([3, 3])
                
                with col1:
                    st.markdown(f"**Column: {channel}**")
                
                with col2:
                    # Create clean display name by default - improved pattern matching
                    display_name = channel
                    for suffix in ['_spend', '_cost', '_budget', '_investment', '_expense']:
                        display_name = display_name.replace(suffix, '')
                    
                    # Let user edit the display name
                    display_name = st.text_input(
                        "Display Name:",
                        value=display_name,
                        key=f"spend_name_{i}"
                    )
                
                # Update mapping
                media_spend_to_channel[channel] = display_name
            
            channel_mappings['media_spend_to_channel'] = media_spend_to_channel
        
        # Run Model button
        st.markdown("### Run Model")
        if st.button("Run Marketing Mix Model", use_container_width=True, type="primary"):
            # Validate inputs
            if not date_col:
                st.error("Please select a date column.")
                return
            
            if not target_col:
                st.error("Please select a revenue/target column.")
                return
            
            # Check if at least one media type is provided
            has_media_data = (media_channels and len(media_channels) > 0) or (media_spend_channels and len(media_spend_channels) > 0)
            
            if not has_media_data:
                st.error("You must provide at least one type of media data: media metrics or media spend columns.")
                return
            
            # Run model with progress indicators
            with st.spinner("Running marketing mix model..."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Step 1: Data Preparation
                status_text.text("Preparing data...")
                progress_bar.progress(10)
                
                # Ensure date column is datetime
                try:
                    if not pd.api.types.is_datetime64_dtype(df[date_col]):
                        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                        
                    # Sort by date
                    df = df.sort_values(by=date_col)
                except Exception as e:
                    st.error(f"Error converting date column: {str(e)}")
                    return
                
                # Step 2: Create Meridian configuration
                status_text.text("Creating model configuration...")
                progress_bar.progress(20)
                
                # Create CoordToColumns configuration
                coord_to_columns_args = {
                    'time': date_col,
                    'kpi': target_col,
                    'controls': control_vars if control_vars else []
                }
                
                if media_channels:
                    coord_to_columns_args['media'] = media_channels
                
                if media_spend_channels:
                    coord_to_columns_args['media_spend'] = media_spend_channels
                
                # Display config for debugging
                if not MERIDIAN_AVAILABLE:
                    st.error("Google Meridian library is not installed. Cannot run model.")
                    return
                
                # Step 3: Run model
                try:
                    status_text.text("Setting up model...")
                    progress_bar.progress(30)
                    
                    # Save temporary CSV for Meridian
                    temp_csv_path = "meridian_data_temp.csv"
                    df.to_csv(temp_csv_path, index=False)
                    
                    # Create data loader
                    status_text.text("Loading data into model...")
                    progress_bar.progress(40)
                    
                    # Create CoordToColumns with all parameters
                    coord_to_columns = load.CoordToColumns(**coord_to_columns_args)
                    
                    # Create loader args
                    loader_args = {
                        'csv_path': temp_csv_path,
                        'kpi_type': 'revenue',  # Simplified - always treat as revenue
                        'coord_to_columns': coord_to_columns
                    }
                    
                    # Add channel mappings
                    if channel_mappings.get('media_to_channel'):
                        loader_args['media_to_channel'] = channel_mappings['media_to_channel']
                    
                    if channel_mappings.get('media_spend_to_channel'):
                        loader_args['media_spend_to_channel'] = channel_mappings['media_spend_to_channel']
                    
                    # Create data loader
                    loader = load.CsvDataLoader(**loader_args)
                    
                    # Load data
                    status_text.text("Processing data...")
                    progress_bar.progress(50)
                    mmm_data = loader.load()
                    
                    # Configure and create model
                    status_text.text("Building model...")
                    progress_bar.progress(60)
                    
                    # Create prior distribution
                    prior = prior_distribution.PriorDistribution()
                    
                    # Create model spec and Meridian model
                    model_spec = spec.ModelSpec(prior=prior)
                    mmm = model.Meridian(input_data=mmm_data, model_spec=model_spec)
                    
                    # Sample from prior
                    status_text.text("Initializing model...")
                    progress_bar.progress(70)
                    mmm.sample_prior(500)
                    
                    # Sample from posterior
                    status_text.text("Training model (this may take some time)...")
                    progress_bar.progress(80)
                    
                    # Run the model with fixed parameters
                    start_time = datetime.now()
                    mmm.sample_posterior(
                        n_chains=4,  # Using 4 chains as requested
                        n_adapt=500,
                        n_burnin=500,
                        n_keep=500
                    )
                    end_time = datetime.now()
                    execution_time = end_time - start_time
                    execution_time_minutes = execution_time.total_seconds() / 60.0
                    
                    # Model completed
                    status_text.text("Model training completed! Creating results...")
                    progress_bar.progress(90)
                    
                    # Save the model to session state
                    st.session_state.mmm_object = mmm
                    
                    # Create model results dictionary
                    model_results = {
                        'model_type': "Meridian Marketing Mix Model",
                        'target': target_col,
                        'features': media_channels + media_spend_channels + (control_vars if control_vars else []),
                        'metrics': {
                            'Execution Time (minutes)': execution_time_minutes
                        },
                        'meridian_data': {
                            'mmm_object': mmm
                        },
                        'channel_mappings': channel_mappings  # Store channel mappings for persistence
                    }
                    
                    # Store results in session state for persistence across tabs
                    st.session_state.model_results = model_results
                    
                    # Complete progress
                    status_text.text("Model execution completed!")
                    progress_bar.progress(100)
                    
                    # Save the model to a pickle file
                    model_bytes = BytesIO()
                    pickle.dump(mmm, model_bytes)
                    model_bytes.seek(0)
                    
                    # Success message with download button
                    st.success("✅ Model successfully trained! Your marketing mix model is ready.")
                    
                    # Create download button for the model
                    st.markdown("### Download Your Model")
                    st.markdown("""
                    <div style="background-color: #f0f7ff; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                    <p><strong>⚠️ Important:</strong> Download your model file to save your results. You'll need this file if you want to:
                    <ul>
                        <li>Avoid having to retrain the model</li>
                    </ul>
                    </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    b64 = base64.b64encode(model_bytes.read()).decode()
                    download_filename = f"marketing_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
                    href = f'<a href="data:file/pickle;base64,{b64}" download="{download_filename}" style="background-color: #4CAF50; color: white; padding: 10px 24px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; border-radius: 4px; cursor: pointer;">Download Model File</a>'
                    st.markdown(href, unsafe_allow_html=True)
                    
                    # Next steps guidance
                    st.markdown("### Next Steps")
                    st.markdown("""
                    Now that your model is ready, proceed to the Insights page to:
                    - See which marketing channels are most effective
                    - Understand your return on investment by channel
                    - Visualize your model results
                    """)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("⬅️ Back to Home", use_container_width=True):
                            st.session_state.page = 'home'
                            st.experimental_rerun()
                    with col2:
                        if st.button("Continue to Insights ➡️", use_container_width=True):
                            st.session_state.page = 'step2'
                            st.rerun()
                
                except Exception as e:
                    st.error(f"An error occurred during model execution: {str(e)}")
                    
                    # Provide helpful guidance based on common errors
                    if "should include media data" in str(e):
                        st.warning("Model configuration error: You must provide media data. Please check your media channel selections.")
                    elif "CoordToColumns" in str(e):
                        st.warning("Selection error: Please check your column selections and try again.")
                    else:
                        st.warning("Try selecting different columns or check your data format.")
                    
                    with st.expander("Error Details"):
                        st.text(str(e))
                    
                    progress_bar.empty()
                    status_text.empty()
        
        # Show model results if they exist
        elif 'model_results' in st.session_state and st.session_state.model_results is not None:
            st.success("✅ Model already trained! Your marketing mix model is ready.")
            
            # Display model information
            results = st.session_state.model_results
            st.write(f"**Model Type:** {results['model_type']}")
            st.write(f"**Target Variable:** {results['target']}")
            
            # Create download button for existing model
            st.markdown("### Download Your Model")
            if 'mmm_object' in st.session_state:
                model_bytes = BytesIO()
                pickle.dump(st.session_state.mmm_object, model_bytes)
                model_bytes.seek(0)
                
                b64 = base64.b64encode(model_bytes.read()).decode()
                download_filename = f"marketing_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
                href = f'<a href="data:file/pickle;base64,{b64}" download="{download_filename}" style="background-color: #4CAF50; color: white; padding: 10px 24px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; border-radius: 4px; cursor: pointer;">Download Model File</a>'
                st.markdown(href, unsafe_allow_html=True)
            
            # Next steps guidance for existing model
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("⬅️ Back to Home", use_container_width=True):
                    st.session_state.page = 'home'
                    st.experimental_rerun()
            with col2:
                if st.button("Continue to Insights ➡️", use_container_width=True):
                    st.session_state.page = 'step2'
                    st.rerun()
