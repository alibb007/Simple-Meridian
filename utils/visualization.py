#/utils/visualization.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import tempfile
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import base64
from io import BytesIO
from datetime import datetime
import altair as alt

# Check if Meridian is available
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
    

def display_chart_safely(chart, use_container_width=True):
    """Helper function to display charts of various types safely with increased height"""
    
    # For Altair charts
    if hasattr(chart, 'to_dict') or 'altair' in str(type(chart)).lower():
        # Check if it's a FacetChart (which doesn't support height property)
        if 'facet' in str(type(chart)).lower():
            # Don't try to set height on FacetChart
            st.altair_chart(chart, use_container_width=use_container_width)
        elif hasattr(chart, 'properties'):
            # For regular Altair charts, set height if not already set
            if not chart.height:
                chart = chart.properties(height=900)  # Increased default height
            st.altair_chart(chart, use_container_width=use_container_width)
        else:
            # For any other Altair chart
            st.altair_chart(chart, use_container_width=use_container_width)
    else:
        # For matplotlib figures
        if hasattr(chart, 'get_figheight') and hasattr(chart, 'set_figheight'):
            # Increase figure height for better visibility
            current_width = chart.get_figwidth()
            chart.set_figheight(8)  # Substantially increased height
            # Make sure tick labels are fully visible
            chart.tight_layout()
            
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
            tmp_path = tmp_file.name
            chart.savefig(tmp_path, format='png', dpi=100, bbox_inches='tight')
            st.image(tmp_path, use_column_width=use_container_width)
            os.unlink(tmp_path)

def create_media_contribution_visualization(mmm):
    """Create media contribution visualizations with increased height"""
    
    if not MERIDIAN_AVAILABLE:
        st.warning("Meridian libraries are not available. Cannot create media contribution visualization.")
        return
    
    # explanatory card
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
    <h3 style="margin-top: 0;">Understanding Contribution Analysis</h3>
    <p>Contribution shows how much each channel contributes to your total revenue or KPI.</p>
    <ul>
      <li><strong>Larger segments:</strong> Bigger impact on overall business results</li>
      <li><strong>Channels with small contribution but high ROI:</strong> May be underutilized</li>
      <li><strong>Baseline:</strong> Shows results you'd get without any media</li>
    </ul>
    <p><strong>Business action:</strong> Focus optimization efforts on channels with large contribution to maximize impact.</p>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        # Create media contribution visualizations
        media_summary = visualizer.MediaSummary(mmm)
        
        # Contribution Waterfall Chart
        try:
            st.markdown("### Channel Contribution Waterfall")
            st.markdown("""
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
            <p>The contribution waterfall shows how each marketing channel adds to your total outcome. 
            It starts with the baseline (what you'd get without any marketing) and shows the incremental 
            contribution of each channel.</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.spinner("Generating channel contribution visualization..."):
                contribution_chart = media_summary.plot_contribution_waterfall_chart()
                display_chart_safely(contribution_chart)
        except Exception as e:
            st.warning(f"Could not generate contribution waterfall chart: {str(e)}")
        
        # Pie Chart
        try:
            st.markdown("### Overall Contribution Breakdown")
            st.markdown("""
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
            <p>This pie chart shows the percentage breakdown of all your outcomes, including both baseline and 
            marketing-driven results. It helps you understand the relative importance of each channel.</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.spinner("Generating contribution pie chart..."):
                pie_chart = media_summary.plot_contribution_pie_chart()
                display_chart_safely(pie_chart)
        except Exception as e:
            st.warning(f"Could not generate contribution pie chart: {str(e)}")
        
        # Spend vs Contribution
        try:
            st.markdown("### Spend vs Contribution Comparison")
            st.markdown("""
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
            <p>This chart compares the percentage of spend allocated to each channel versus the percentage 
            of contribution it generates. Channels that contribute more than their share of spend are 
            more efficient.</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.spinner("Generating spend vs contribution visualization..."):
                # Remove height parameter completely
                spend_contrib_chart = media_summary.plot_spend_vs_contribution()
                st.altair_chart(spend_contrib_chart, use_container_width=True)
        except Exception as e:
            # If that fails, create a custom plotly chart as fallback
            try:
                summary_table = media_summary.summary_table()
                if 'spend' in summary_table.columns and 'contribution_mean' in summary_table.columns:
                    fig = px.scatter(
                        summary_table.reset_index(),
                        x='spend',
                        y='contribution_mean',
                        text='index',
                        size='spend',
                        color='contribution_mean',
                        title="Spend vs Contribution",
                        labels={'index': 'Channel', 'spend': 'Spend', 'contribution_mean': 'Contribution'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Could not generate spend vs contribution chart: required columns not available")
            except Exception as inner_e:
                st.warning(f"Could not generate spend vs contribution chart: {str(e)}, Fallback error: {str(inner_e)}")
        
        # CPIK Chart (Cost Per Incremental KPI)
        try:
            st.markdown("### Cost Per Incremental KPI (CPIK) by Channel")
            st.markdown("""
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
            <p>CPIK (Cost Per Incremental KPI) shows how much you spend to generate one unit of your KPI. 
            Lower values are better, indicating more cost-efficient channels.</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.spinner("Generating CPIK visualization..."):
                cpik_chart = media_summary.plot_cpik(include_ci=True)
                display_chart_safely(cpik_chart)
        except Exception as e:
            st.warning(f"Could not generate CPIK chart: {str(e)}")


    except Exception as e:
        st.error(f"Error generating contribution visualizations: {str(e)}")
        
def get_explanation_text(chart_type):
    """Return predefined explanation text for different chart types"""
    
    explanations = {
        "roi_analysis": """
        ### Understanding ROI Analysis
        
        Return on Investment (ROI) shows how much revenue or KPI lift you get for each dollar spent on a channel.
        
        **How to use this chart:**
        - ROI > 1: Channel generates positive returns (profitable)
        - ROI < 1: Channel costs more than it returns
        - Higher bars = better performance per dollar
        
        **Business action:** Consider shifting budget from low ROI channels to high ROI channels for better overall performance.
        """,
        
        "contribution": """
        ### Understanding Contribution Analysis
        
        Contribution shows how much each channel contributes to your total revenue or KPI.
        
        **How to use these charts:**
        - Larger segments = bigger impact on overall business results
        - Channels with small contribution but high ROI may be underutilized
        - Baseline shows results you'd get without any media
        
        **Business action:** Focus optimization efforts on channels with large contribution to maximize impact.
        """,
        
        "response_curves": """
        ### Understanding Response Curves
        
        Response curves show how spending at different levels affects your results. They reveal the relationship between investment and returns.
        
        **How to use these charts:**
        - Steep slope = high responsiveness to spending changes
        - Flat sections = diminishing returns (saturation)
        - Current spend point shows your actual spending level
        
        **Business action:** Look for channels where the curve is still steep to find opportunities for additional investment.
        """,
        
        "model_diagnostics": """
        ### Understanding Model Diagnostics
        
        These diagnostics show how well the model is performing and whether it can be trusted for decision-making.
        
        **How to use these charts:**
        - R-hat values close to 1.0 indicate good model convergence
        - Expected vs Actual shows how well the model predicts outcomes
        - Prior vs Posterior shows how the model updated its understanding based on data
        
        **Business action:** Check these metrics before making decisions to ensure your model is reliable.
        """,
    
        
        "feature_importance": """
        ### Understanding Feature Importance
        
        Feature importance shows which channels have the biggest impact on your business outcomes.
        
        **How to use these charts:**
        - Longer bars = more important channels
        - Consider both ROI and importance when making budget decisions
        - A channel can have high importance but low ROI if it's expensive
        
        **Business action:** Focus optimization and testing on your most important channels for maximum impact.
        """,
    }
    
    return explanations.get(chart_type, "")

def create_roi_visualization(mmm):
    """Create comprehensive ROI visualizations with model coefficients"""
    
    if not MERIDIAN_AVAILABLE:
        st.warning("Meridian libraries are not available. Cannot create ROI visualization.")
        return
    
    # Add explanatory card for ROI Analysis
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
    <h3 style="margin-top: 0;">ROI Analysis</h3>
    <p>Return on Investment (ROI) shows how much revenue you get for each dollar spent on a channel. 
    Higher ROI indicates more efficient marketing spend.</p>
    <ul>
      <li><strong>ROI > 1:</strong> Channel generates profit (returns exceed cost)</li>
      <li><strong>ROI < 1:</strong> Channel costs more than it returns</li>
    </ul>
    <p><strong>Action:</strong> Consider shifting budget from low to high ROI channels for better overall performance.</p>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        # Create ROI visualizations using Meridian
        analyzer_obj = analyzer.Analyzer(mmm)
        media_summary = visualizer.MediaSummary(mmm)
        
        st.markdown("### Channel ROI Comparison")
        
        try:
            # Try to create ROI bar chart
            with st.spinner("Generating ROI visualization..."):
                roi_chart = media_summary.plot_roi_bar_chart(include_ci=True)
                display_chart_safely(roi_chart)
                
                # Add explanatory text - shorter and clearer
                st.markdown("""
                **Note:** Higher ROI indicates more revenue generated per dollar spent.
                """)
        except Exception as e:
            st.warning(f"Could not generate ROI bar chart: {str(e)}")
            
            # Try different method names that might exist in your Meridian version
            roi_df = None
            try:
                # Try method name 1: get_roi
                roi_df = analyzer_obj.get_roi()
            except Exception:
                try:
                    # Try method name 2: get_roi_decomposition
                    roi_df = analyzer_obj.get_roi_decomposition()
                except Exception:
                    try:
                        # Try method name 3: get_channel_roi
                        roi_df = analyzer_obj.get_channel_roi()
                    except Exception as roi_err:
                        st.error(f"Could not generate ROI analysis: {str(roi_err)}")
            
            if roi_df is not None:
                fig = px.bar(
                    roi_df.reset_index(),
                    x='index',
                    y='roi_mean',
                    error_y='roi_std',
                    title="Return on Investment (ROI) by Channel",
                    labels={'index': 'Channel', 'roi_mean': 'ROI'},
                    height=600  # Increased height
                )
                fig.update_layout(
                    margin=dict(l=50, r=50, t=50, b=100),  # Increase bottom margin for labels
                    xaxis=dict(tickangle=-45)  # Angle the labels to fit better
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # ROI vs Effectiveness bubble chart
        try:
            st.markdown("### ROI vs Effectiveness")
            # Add simplified explanation
            st.markdown("""
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
            <p><strong>ROI vs Effectiveness:</strong> Compares efficiency (ROI) with impact per impression (effectiveness)</p>
            <ul>
              <li><strong>Top-right quadrant:</strong> Ideal channels (high ROI & high effectiveness)</li>
              <li><strong>Top-left:</strong> Effective but expensive channels</li>
              <li><strong>Bottom-right:</strong> Efficient but low-impact channels</li>
            </ul>
            <p>Bubble size represents media spend.</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.spinner("Generating ROI vs Effectiveness visualization..."):
                roi_eff_chart = media_summary.plot_roi_vs_effectiveness()
                
                # If it's an Altair chart, increase its height substantially
                if hasattr(roi_eff_chart, 'properties'):
                    # Make the chart much taller with proper axis labels
                    roi_eff_chart = roi_eff_chart.properties(
                        height=700  # Increased height
                    ).configure_axis(
                        labelFontSize=14,  # Larger axis labels
                        titleFontSize=16   # Larger axis titles
                    ).configure_axisY(
                        titlePadding=20  # Add more padding for Y-axis title
                    )
                
                # Add CSS to ensure chart takes up more vertical space
                st.markdown("""
                <style>
                .stChart {
                    min-height: 700px !important;
                }
                </style>
                """, unsafe_allow_html=True)
                
                display_chart_safely(roi_eff_chart)
        except Exception as e:
            st.warning(f"Could not generate ROI vs Effectiveness chart: {str(e)}")
        
        # ROI vs mROI bubble chart
        try:
            st.markdown("### ROI vs Marginal ROI")
            # Add simplified explanation
            st.markdown("""
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
            <p><strong>ROI vs Marginal ROI:</strong> Compares overall efficiency with returns on additional spending</p>
            <ul>
              <li><strong>High ROI, High mROI:</strong> Increase budget (performs well & has room to grow)</li>
              <li><strong>High ROI, Low mROI:</strong> Maintain budget (good performance but reaching saturation)</li>
              <li><strong>Low ROI, Low mROI:</strong> Consider reducing budget</li>
            </ul>
            <p>Bubble size represents media spend.</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.spinner("Generating ROI vs Marginal ROI visualization..."):
                roi_mroi_chart = media_summary.plot_roi_vs_mroi()
                
                # If it's an Altair chart, increase its height substantially
                if hasattr(roi_mroi_chart, 'properties'):
                    # Make the chart much taller with proper axis labels
                    roi_mroi_chart = roi_mroi_chart.properties(
                        height=700  # Increased height
                    ).configure_axis(
                        labelFontSize=14,  # Larger axis labels
                        titleFontSize=16   # Larger axis titles
                    ).configure_axisY(
                        titlePadding=20  # Add more padding for Y-axis title
                    )
                
                display_chart_safely(roi_mroi_chart)
        except Exception as e:
            st.warning(f"Could not generate ROI vs Marginal ROI chart: {str(e)}")
            
        # -------------------- MODEL COEFFICIENTS SECTION (Added from Feature Importance) -------------------- #
        st.markdown("### Key Insights - Model Coefficients")
        st.markdown("""
        - **Model coefficients** represent the direct impact of each channel on your KPI
        - **Channels with larger coefficients** have stronger influence on business outcomes
        - **Budget implications:** Consider these values alongside ROI for comprehensive budget decisions
        """)
        
        # Try to get model coefficients
        try:
            if hasattr(mmm, 'inference_data') and hasattr(mmm.inference_data, 'posterior'):
                posterior = mmm.inference_data.posterior
                
                # Add explanation
                st.markdown("""
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <p>These model coefficients represent the direct impact of each channel on your KPI.
                Larger coefficients indicate channels with stronger influence on your business outcomes.
                Consider these values alongside ROI for comprehensive budget allocation decisions.</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Get actual channel names directly from model
                try:
                    # Get channel names from model's media channels
                    if hasattr(mmm.input_data, 'get_media_channels'):
                        channel_names = mmm.input_data.get_media_channels()
                    elif hasattr(mmm.input_data, 'media_channels'):
                        channel_names = mmm.input_data.media_channels
                    elif hasattr(mmm.input_data, 'get_all_paid_channels'):
                        channel_names = mmm.input_data.get_all_paid_channels()
                    else:
                        # Fallback: try to get channels from data
                        channel_names = []
                        try:
                            # Channels should be consistent in Meridian, so we use this method
                            media_effects = visualizer.MediaEffects(mmm)
                            channel_names = media_effects.get_media_names()
                        except:
                            # Last resort: get from media summary
                            try:
                                summary_table = media_summary.summary_table()
                                channel_names = summary_table.index.tolist()
                            except:
                                # If all else fails, provide generic names
                                channel_names = [f"Channel {i+1}" for i in range(5)]
                except:
                    channel_names = [f"Channel {i+1}" for i in range(5)]
                
                # Find coefficient variables
                coef_var = None
                for pattern in ['media', 'channel', 'coef', 'beta']:
                    for var in posterior.data_vars:
                        if pattern in str(var).lower():
                            coef_var = var
                            break
                    if coef_var:
                        break
                
                if coef_var:
                    st.success("Found coefficient data in model posterior")
                    
                    # Get data
                    media_data = posterior[coef_var]
                    means = media_data.mean(dim=['chain', 'draw']).values.flatten()
                    stds = media_data.std(dim=['chain', 'draw']).values.flatten()
                    
                    # Map channel names
                    coef_data = []
                    for i in range(len(means)):
                        if i < len(channel_names):
                            # Use actual channel name from our list
                            channel = channel_names[i]
                        else:
                            # Fallback if we have more coefficients than channel names
                            channel = f"Channel {i+1}"
                        
                        coef_data.append({
                            'Channel': channel,
                            'Coefficient': means[i],
                            'Std': stds[i]
                        })
                    
                    # Create DataFrame
                    coef_df = pd.DataFrame(coef_data).sort_values('Coefficient')
                    
                    # Color scheme
                    custom_coef_colors = [
                        [0.0, "#6C3483"], [0.25, "#8E44AD"], 
                        [0.5, "#9B59B6"], [0.75, "#C0392B"], [1.0, "#922B21"]
                    ]
                    
                    # Create visualization
                    fig = px.bar(
                        coef_df,
                        y='Channel',
                        x='Coefficient',
                        text='Coefficient',
                        color='Coefficient',
                        color_continuous_scale=custom_coef_colors,
                        orientation='h'
                    )
                    
                    # Styling
                    fig.update_layout(
                        title={
                            'text': "Model Coefficients by Channel",
                            'font': {'size': 22, 'color': '#2C3E50'},
                            'y': 0.95,
                            'x': 0.5,
                            'xanchor': 'center',
                            'yanchor': 'top'
                        },
                        height=max(500, len(coef_df) * 60),
                        margin=dict(l=150, r=50, t=80, b=50),
                        yaxis=dict(
                            title="",
                            tickfont={'size': 14},
                            tickangle=0
                        ),
                        xaxis=dict(
                            title=dict(
                                text="Coefficient Value",
                                font={'size': 16, 'color': '#2C3E50'}
                            ),
                            tickfont={'size': 12},
                            gridcolor='#EEEEEE'
                        ),
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        coloraxis_showscale=False
                    )
                    
                    # Update traces with error bars
                    fig.update_traces(
                        texttemplate='%{text:.3f}',
                        textposition='outside',
                        marker_line_color='#FFFFFF',
                        marker_line_width=1,
                        opacity=0.9,
                        error_x=dict(
                            type='data',
                            array=coef_df['Std'].tolist(),
                            visible=True,
                            thickness=2,
                            width=6,
                            color='rgba(55, 55, 55, 0.6)'
                        )
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Add interpretation guidance section
                    st.markdown("""
                    ### Comparing ROI and Model Coefficients
                    
                    When analyzing your marketing channels, it's important to look at both ROI and model coefficients together:
                    
                    - **High ROI + High Coefficient:** These are your star performers. Prioritize these channels in your marketing mix.
                    
                    - **High ROI + Low Coefficient:** These channels are efficient but may have limited overall impact. Good for targeted campaigns with limited budget.
                    
                    - **Low ROI + High Coefficient:** These channels have strong impact but at high cost. Consider optimizing spend or improving efficiency.
                    
                    - **Low ROI + Low Coefficient:** These channels provide minimal returns and impact. Consider reducing investment or testing new approaches.
                    """)
                else:
                    st.warning("Could not find coefficient data in model")
        except Exception as e:
            st.warning(f"Could not get coefficient data: {str(e)}")
    
    except Exception as e:
        st.error(f"Error generating ROI visualization: {str(e)}")

def create_response_curves_visualization(mmm, plot_separately=True, include_ci=True, num_channels=None):
    """Create response curves visualizations"""
    
    if not MERIDIAN_AVAILABLE:
        st.warning("Meridian libraries are not available. Cannot create response curves visualization.")
        return
    
    # Add explanatory card
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
    <h3 style="margin-top: 0;">Understanding Response Curves</h3>
    <p>Response curves show how spending at different levels affects your results. They reveal the relationship between investment and returns.</p>
    <ul>
      <li><strong>Steep slope:</strong> High responsiveness to spending changes</li>
      <li><strong>Flat sections:</strong> Diminishing returns (saturation)</li>
      <li><strong>Current spend point:</strong> Shows your actual spending level</li>
    </ul>
    <p><strong>Business action:</strong> Look for channels where the curve is still steep to find opportunities for additional investment.</p>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        # Create response curves visualizations
        media_effects = visualizer.MediaEffects(mmm)
        
        # Response Curves
        try:
            st.markdown("### Channel Response Curves")
            st.markdown("""
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
            <p>The response curves are constructed based on the historical flighting pattern and present the cumulative
            incremental outcome from the total media spend over the selected time period. They help you understand the 
            efficiency of each channel at different spend levels.</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.spinner("Generating response curves..."):
                response_chart = media_effects.plot_response_curves(
                    plot_separately=plot_separately,
                    include_ci=include_ci,
                    num_channels_displayed=num_channels
                )
                display_chart_safely(response_chart)
        except Exception as e:
            st.warning(f"Could not generate response curves: {str(e)}")
        
       
    
    except Exception as e:
        st.error(f"Error generating response curves visualizations: {str(e)}")

def create_model_diagnostics_visualization(mmm):
    """Create model diagnostics visualizations"""
    
    if not MERIDIAN_AVAILABLE:
        st.warning("Meridian libraries are not available. Cannot create model diagnostics visualization.")
        return
    
    # Add explanatory card
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
    <h3 style="margin-top: 0;">Understanding Model Diagnostics</h3>
    <p>These diagnostics show how well the model is performing and whether it can be trusted for decision-making.</p>
    <ul>
      <li><strong>R-hat values close to 1.0:</strong> Indicate good model convergence</li>
      <li><strong>Expected vs Actual:</strong> Shows how well the model predicts outcomes</li>
      <li><strong>Prior vs Posterior:</strong> Shows how the model updated its understanding based on data</li>
    </ul>
    <p><strong>Business action:</strong> Check these metrics before making decisions to ensure your model is reliable.</p>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        # Create model diagnostics visualizations
        model_diagnostics = visualizer.ModelDiagnostics(mmm)
        model_fit = visualizer.ModelFit(mmm)
        
        
        
        # Model Fit plot
        try:
            st.markdown("### Model Fit - Expected vs Actual")
            st.markdown("""
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
            <p>This chart compares the model's prediction (Expected) with the actual observed values.
            The closer these lines match, the better the model is at predicting outcomes. The baseline shows 
            what would be expected without any media effects.</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.spinner("Generating expected vs actual plot..."):
                fit_chart = model_fit.plot_model_fit(include_baseline=True)
                display_chart_safely(fit_chart)
        except Exception as e:
            st.warning(f"Could not generate model fit plot: {str(e)}")
            
            # Try alternative approach to get expected vs actual
            try:
                expected = model_fit.get_expected()
                actual = model_fit.get_actual()
                baseline = model_fit.get_baseline()
                
                # Create DataFrame
                fit_df = pd.DataFrame({
                    'Actual': actual,
                    'Expected': expected,
                    'Baseline': baseline
                })
                
                # Create plotly chart
                fig = go.Figure()
                fig.add_trace(go.Scatter(y=fit_df['Actual'], mode='lines', name='Actual'))
                fig.add_trace(go.Scatter(y=fit_df['Expected'], mode='lines', name='Expected'))
                fig.add_trace(go.Scatter(y=fit_df['Baseline'], mode='lines', name='Baseline',
                                        line=dict(color='gray', dash='dash')))
                
                fig.update_layout(
                    title='Expected vs Actual Values',
                    xaxis_title='Time Period',
                    yaxis_title='Value'
                )
                
                st.plotly_chart(fig, use_container_width=True)
            except Exception as alt_err:
                st.error(f"Alternative approach also failed: {str(alt_err)}")
        
        # Model Accuracy Metrics
        try:
            st.markdown("### Model Fit Metrics")
            st.markdown("""
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
            <p>These metrics quantify the model's accuracy:</p>
            <ul>
              <li><strong>R-squared:</strong> Measures the amount of variation explained by the model (higher is better)</li>
              <li><strong>MAPE:</strong> Mean Absolute Percentage Error (lower is better)</li>
              <li><strong>wMAPE:</strong> Weighted MAPE, gives more weight to high-value observations</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
            
            with st.spinner("Generating model accuracy metrics..."):
                metrics_df = model_diagnostics.predictive_accuracy_table()
                st.dataframe(metrics_df, use_container_width=True)
        except Exception as e:
            st.warning(f"Could not generate model accuracy metrics: {str(e)}")
    
    except Exception as e:
        st.error(f"Error generating model diagnostics: {str(e)}")
        

def create_explanation_card(title, content):
    """Utility function to create consistent explanation cards"""
    
    html = f"""
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
    <h3 style="margin-top: 0;">{title}</h3>
    {content}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def get_explanation_text(chart_type):
    """Return concise explanation text for different chart types"""
    
    explanations = {
        "roi_analysis": """
        <p>ROI shows return on each dollar spent. Higher values = more efficient channels.</p>
        <ul>
          <li><strong>ROI > 1:</strong> Profitable channel (returns exceed cost)</li>
          <li><strong>ROI < 1:</strong> Unprofitable channel (costs exceed returns)</li>
        </ul>
        <p><strong>Action:</strong> Shift budget from low ROI to high ROI channels.</p>
        """,
        
        "contribution": """
        <p>Shows how much each channel contributes to total results.</p>
        <ul>
          <li><strong>Larger segments:</strong> Bigger business impact</li>
          <li><strong>Baseline:</strong> Results without any media</li>
        </ul>
        <p><strong>Action:</strong> Focus improvement on channels with large contribution.</p>
        """,
        
        "response_curves": """
        <p>Shows how spend affects results at different investment levels.</p>
        <ul>
          <li><strong>Steep curve:</strong> High responsiveness to spend changes</li>
          <li><strong>Flat section:</strong> Diminishing returns (saturation)</li>
        </ul>
        <p><strong>Action:</strong> Invest more in channels with steep curves.</p>
        """,
        
        "model_diagnostics": """
        <p>Shows how well the model performs and reliability for decisions.</p>
        <ul>
          <li><strong>R-hat ≈ 1.0:</strong> Good model convergence</li>
          <li><strong>Expected vs Actual:</strong> Prediction accuracy</li>
        </ul>
        <p><strong>Action:</strong> Verify these metrics before making decisions.</p>
        """,
       
        
        "feature_importance": """
        <p>Shows which channels have the biggest impact on outcomes.</p>
        <ul>
          <li><strong>Longer bars:</strong> More important channels</li>
          <li><strong>Consider both ROI and importance</strong> for budget decisions</li>
        </ul>
        <p><strong>Action:</strong> Focus optimization on your most important channels.</p>
        """,
        
        "roi_effectiveness": """
        <p>Compares ROI with outcome per impression.</p>
        <ul>
          <li><strong>Top-right:</strong> Best performance (high ROI, high effectiveness)</li>
          <li><strong>Top-left:</strong> Effective but expensive</li>
          <li><strong>Bottom-right:</strong> Efficient but small impact</li>
        </ul>
        <p><strong>Action:</strong> Prioritize top-right quadrant channels.</p>
        """,
        
        "roi_mroi": """
        <p>Compares overall ROI with returns on additional spend.</p>
        <ul>
          <li><strong>High ROI, High mROI:</strong> Increase investment</li>
          <li><strong>High ROI, Low mROI:</strong> Maintain (approaching saturation)</li>
          <li><strong>Low ROI, Low mROI:</strong> Reduce investment</li>
        </ul>
        <p><strong>Action:</strong> Invest more in high marginal ROI channels.</p>
        """,
    }
    
    return explanations.get(chart_type, "")

def get_valid_date_range(mmm):
    """
    Retrieve a list of valid dates from the model.
    Looks for mmm.input_data.time or, as a fallback, the index of mmm.df_data.
    Returns a Pandas DatetimeIndex or None if not found.
    """
    valid_dates = None
    try:
        if hasattr(mmm, 'input_data') and hasattr(mmm.input_data, 'time'):
            valid_dates = pd.to_datetime(mmm.input_data.time.values)
        elif hasattr(mmm, 'df_data') and isinstance(mmm.df_data.index, pd.DatetimeIndex):
            valid_dates = mmm.df_data.index
    except Exception:
        pass
    return valid_dates


def create_export_report(mmm, start_date=None, end_date=None):
    """
    Create and export Meridian's built-in HTML report with minimal UI.
    This function clamps the supplied start and end dates to the model's valid time
    coordinates (if necessary) so that the dates used are actually in the model.
    Only a download link is displayed upon completion.
    """
    if not MERIDIAN_AVAILABLE:
        st.warning("Meridian libraries are not available. Cannot create export.")
        return

    try:
        # Create the summarizer
        mmm_summarizer = summarizer.Summarizer(mmm)

        # Retrieve the model's valid date range (as strings)
        model_start_date, model_end_date = get_model_date_range(mmm)
        if model_start_date is None or model_end_date is None:
            st.error("Model date range is not available.")
            return

        # Retrieve valid time coordinates from the model (if available)
        valid_dates = get_valid_date_range(mmm)

        # If no start_date is provided, use the model's start date
        if start_date is None:
            start_date = model_start_date
        # Otherwise, convert to datetime and adjust if not in valid_dates
        else:
            start_date_dt = pd.to_datetime(start_date)
            if valid_dates is not None and start_date_dt not in valid_dates:
                # Use the smallest valid date that is >= start_date_dt, or fallback to model_start_date
                valid_start = valid_dates[valid_dates >= start_date_dt]
                start_date = valid_start.min().strftime('%Y-%m-%d') if not valid_start.empty else model_start_date

        # If no end_date is provided, use the model's end date
        if end_date is None:
            end_date = model_end_date
        else:
            end_date_dt = pd.to_datetime(end_date)
            if valid_dates is not None and end_date_dt not in valid_dates:
                # Use the largest valid date that is <= end_date_dt, or fallback to model_end_date
                valid_end = valid_dates[valid_dates <= end_date_dt]
                end_date = valid_end.max().strftime('%Y-%m-%d') if not valid_end.empty else model_end_date

        # Also ensure that the start_date is not later than the end_date
        if pd.to_datetime(start_date) > pd.to_datetime(end_date):
            st.error("Start date must be earlier than or equal to the end date.")
            return

        # Generate the report in a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            report_filename = f"meridian_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            report_path = os.path.join(temp_dir, report_filename)

            with st.spinner():
                mmm_summarizer.output_model_results_summary(
                    report_filename,
                    filepath=temp_dir,
                    start_date=start_date,
                    end_date=end_date
                )

                # Read the generated HTML file
                with open(report_path, 'rb') as f:
                    report_content = f.read()

                # Create and display a download link (no extra text)
                b64 = base64.b64encode(report_content).decode()
                href = f'<a href="data:text/html;base64,{b64}" download="{report_filename}">Download Meridian HTML Report</a>'
                st.markdown(href, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error generating Meridian report: {str(e)}")


def get_model_date_range(mmm):
    """Get the date range available in the model"""
    
    start_date = None
    end_date = None
    
    if not MERIDIAN_AVAILABLE:
        return start_date, end_date
    
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
                     
        # Method 3: Try to get from model_fit
        if (start_date is None or end_date is None) and MERIDIAN_AVAILABLE:
            try:
                model_fit = visualizer.ModelFit(mmm)
                actual = model_fit.get_actual()
                
                # Check if actual is a Series with DatetimeIndex
                if isinstance(actual, pd.Series) and isinstance(actual.index, pd.DatetimeIndex):
                    start_date = actual.index[0].strftime('%Y-%m-%d')
                    end_date = actual.index[-1].strftime('%Y-%m-%d')
            except Exception:
                pass
                
        # Method 4: Try to get from the df_data attribute
        if (start_date is None or end_date is None) and hasattr(mmm, 'df_data'):
            if isinstance(mmm.df_data.index, pd.DatetimeIndex):
                start_date = mmm.df_data.index[0].strftime('%Y-%m-%d')
                end_date = mmm.df_data.index[-1].strftime('%Y-%m-%d')
        
        # Method 5: Try to get from time periods if all else fails
        if (start_date is None or end_date is None) and hasattr(mmm, 'num_time_periods'):
            # Create default dates based on number of time periods
            import datetime as dt
            today = dt.datetime.now()
            end_date = today.strftime('%Y-%m-%d')
            start_date = (today - dt.timedelta(days=mmm.num_time_periods * 7)).strftime('%Y-%m-%d')
    except Exception as e:
        pass
    
    return start_date, end_date

# Additional custom helper functions

def create_roi_comparison_chart(mmm, channels=None, baseline=None):
    """Create a custom ROI comparison chart for selected channels"""
    if not MERIDIAN_AVAILABLE:
        st.warning("Meridian libraries are not available.")
        return
    
    try:
        # Get ROI data
        analyzer_obj = analyzer.Analyzer(mmm)
        roi_df = analyzer_obj.get_roi()
        
        # Filter channels if provided
        if channels:
            roi_df = roi_df.loc[channels]
        
        # Plot the custom visualization
        fig = px.bar(
            roi_df.reset_index().sort_values('roi_mean', ascending=False),
            x='index',
            y='roi_mean',
            error_y='roi_std',
            title="ROI Comparison for Selected Channels",
            labels={'index': 'Channel', 'roi_mean': 'ROI'},
            color='roi_mean',
            color_continuous_scale='Blues'
        )
        
        # Add baseline line if provided
        if baseline:
            fig.add_shape(
                type="line",
                x0=-0.5,
                y0=baseline,
                x1=len(roi_df) - 0.5,
                y1=baseline,
                line=dict(color="red", width=2, dash="dash"),
            )
            fig.add_annotation(
                x=len(roi_df) / 2,
                y=baseline,
                text=f"Baseline ROI: {baseline}",
                showarrow=False,
                yshift=10
            )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error creating ROI comparison chart: {str(e)}")

def create_spend_vs_roi_optimization(mmm):
    """Create a visualization to help with spend vs ROI optimization"""
    if not MERIDIAN_AVAILABLE:
        st.warning("Meridian libraries are not available.")
        return
    
    try:
        # Get ROI data
        analyzer_obj = analyzer.Analyzer(mmm)
        roi_df = analyzer_obj.get_roi()
        
        # Try to get spend data
        try:
            media_summary = visualizer.MediaSummary(mmm)
            summary_table = media_summary.summary_table()
            
            # Check if spend exists in summary table
            if 'spend' in summary_table.columns:
                # Merge spend with ROI
                merged_df = pd.DataFrame({
                    'ROI': roi_df['roi_mean'],
                    'Spend': summary_table['spend']
                })
                
                # Create scatter plot
                fig = px.scatter(
                    merged_df.reset_index(),
                    x='Spend',
                    y='ROI',
                    text='index',
                    size='Spend',
                    color='ROI',
                    hover_data=['Spend', 'ROI'],
                    title="Spend vs ROI Optimization",
                    labels={'index': 'Channel'},
                    color_continuous_scale='Viridis'
                )
                
                fig.update_traces(textposition='top center')
                fig.add_shape(
                    type="line",
                    x0=0,
                    y0=1,
                    x1=merged_df['Spend'].max() * 1.1,
                    y1=1,
                    line=dict(color="red", width=2, dash="dash"),
                )
                fig.add_annotation(
                    x=merged_df['Spend'].max() * 0.5,
                    y=1,
                    text="ROI = 1 (Breakeven)",
                    showarrow=False,
                    yshift=10
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Create optimization recommendation
                st.markdown("### Optimization Recommendations")
                
                # Identify channels with high, medium, and low ROI
                high_roi = merged_df[merged_df['ROI'] > 1.5].index.tolist()
                medium_roi = merged_df[(merged_df['ROI'] <= 1.5) & (merged_df['ROI'] > 1)].index.tolist()
                low_roi = merged_df[merged_df['ROI'] <= 1].index.tolist()
                
                if high_roi:
                    st.markdown(f"""
                    **Increase Budget for:** {', '.join(high_roi)}  
                    These channels have high ROI (>1.5) and would benefit from increased investment.
                    """)
                
                if medium_roi:
                    st.markdown(f"""
                    **Maintain Budget for:** {', '.join(medium_roi)}  
                    These channels have positive ROI but could be optimized further.
                    """)
                
                if low_roi:
                    st.markdown(f"""
                    **Decrease Budget for:** {', '.join(low_roi)}  
                    These channels have ROI ≤ 1 and may need optimization or reduced investment.
                    """)
                
            else:
                st.warning("Spend data not available in model summary table.")
                
        except Exception as e:
            st.warning(f"Could not create spend vs ROI optimization: {str(e)}")
            
    except Exception as e:
        st.error(f"Error creating spend vs ROI optimization: {str(e)}")


