"""
Plots module for subway system visualizations using Plotly.

Creates scatter plots with click selection to set selected_system_id.
"""

import pandas as pd
import streamlit as st
import plotly.express as px
from typing import Optional


def create_lines_vs_miles_plot(df: pd.DataFrame) -> Optional[str]:
    """
    Create a scatter plot of lines vs miles with click selection.
    
    Args:
        df: DataFrame with subway system data
        
    Returns:
        Selected system ID if a point was clicked, None otherwise
    """
    # Filter to rows with both columns
    plot_df = df[
        df["NUMBER_OF_LINES"].notna() & df["TOTAL_MILES"].notna()
    ].copy()
    
    if plot_df.empty:
        st.warning("No data available for lines vs miles plot.")
        return None
    
    # Create scatter plot
    fig = px.scatter(
        plot_df,
        x="TOTAL_MILES",
        y="NUMBER_OF_LINES",
        hover_data=["SYSTEM_ID", "CITY", "COUNTRY"],
        labels={
            "TOTAL_MILES": "Total Miles",
            "NUMBER_OF_LINES": "Number of Lines"
        },
        title="Lines vs Miles",
        color_discrete_sequence=["white"]  # White points to match theme
    )
    
    # Update layout for dark theme
    fig.update_layout(
        plot_bgcolor="black",
        paper_bgcolor="black",
        font_color="white",
        xaxis=dict(gridcolor="gray", linecolor="white"),
        yaxis=dict(gridcolor="gray", linecolor="white")
    )
    
    # Update marker color
    fig.update_traces(marker=dict(color="white", size=8))
    
    # Render plot
    event = st.plotly_chart(
        fig,
        use_container_width=True,
        on_select="rerun",
        key="lines_miles_plot"
    )
    
    # Handle selection - Streamlit returns selection data in event
    if event and "selection" in event:
        selection = event["selection"]
        if selection and "points" in selection and len(selection["points"]) > 0:
            # Get the first selected point index
            point_idx = selection["points"][0].get("point_index", None)
            if point_idx is not None and point_idx < len(plot_df):
                selected_system_id = plot_df.iloc[point_idx]["SYSTEM_ID"]
                return selected_system_id
    
    # Fallback: show clickable dataframe for selection
    st.markdown("**Or select a system from the list below:**")
    selection_df = plot_df[["SYSTEM_ID", "CITY", "COUNTRY", "NUMBER_OF_LINES", "TOTAL_MILES"]].copy()
    selection_df.index = range(len(selection_df))
    
    selected_rows = st.dataframe(
        selection_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="lines_miles_selection"
    )
    
    if selected_rows.selection.rows:
        selected_idx = selected_rows.selection.rows[0]
        selected_system_id = selection_df.iloc[selected_idx]["SYSTEM_ID"]
        return selected_system_id
    
    return None


def create_ridership_vs_population_plot(df: pd.DataFrame) -> Optional[str]:
    """
    Create a scatter plot of annual ridership vs city population with click selection.
    
    Args:
        df: DataFrame with subway system data
        
    Returns:
        Selected system ID if a point was clicked, None otherwise
    """
    # Filter to rows with both columns
    plot_df = df[
        df["ANNUAL_RIDERSHIP"].notna() & df["CITY_POPULATION"].notna()
    ].copy()
    
    if plot_df.empty:
        st.warning("No data available for ridership vs population plot.")
        return None
    
    # Create scatter plot
    fig = px.scatter(
        plot_df,
        x="CITY_POPULATION",
        y="ANNUAL_RIDERSHIP",
        hover_data=["SYSTEM_ID", "CITY", "COUNTRY"],
        labels={
            "CITY_POPULATION": "City Population",
            "ANNUAL_RIDERSHIP": "Annual Ridership"
        },
        title="Annual Ridership vs City Population",
        color_discrete_sequence=["white"]  # White points to match theme
    )
    
    # Update layout for dark theme
    fig.update_layout(
        plot_bgcolor="black",
        paper_bgcolor="black",
        font_color="white",
        xaxis=dict(gridcolor="gray", linecolor="white"),
        yaxis=dict(gridcolor="gray", linecolor="white")
    )
    
    # Update marker color
    fig.update_traces(marker=dict(color="white", size=8))
    
    # Render plot
    event = st.plotly_chart(
        fig,
        use_container_width=True,
        on_select="rerun",
        key="ridership_population_plot"
    )
    
    # Handle selection - Streamlit returns selection data in event
    if event and "selection" in event:
        selection = event["selection"]
        if selection and "points" in selection and len(selection["points"]) > 0:
            # Get the first selected point index
            point_idx = selection["points"][0].get("point_index", None)
            if point_idx is not None and point_idx < len(plot_df):
                selected_system_id = plot_df.iloc[point_idx]["SYSTEM_ID"]
                return selected_system_id
    
    # Fallback: show clickable dataframe for selection
    st.markdown("**Or select a system from the list below:**")
    selection_df = plot_df[["SYSTEM_ID", "CITY", "COUNTRY", "ANNUAL_RIDERSHIP", "CITY_POPULATION"]].copy()
    selection_df.index = range(len(selection_df))
    
    selected_rows = st.dataframe(
        selection_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="ridership_population_selection"
    )
    
    if selected_rows.selection.rows:
        selected_idx = selected_rows.selection.rows[0]
        selected_system_id = selection_df.iloc[selected_idx]["SYSTEM_ID"]
        return selected_system_id
    
    return None


def render_plots_tab(df: pd.DataFrame) -> Optional[str]:
    """
    Render the plots tab with multiple scatter plot options.
    
    Args:
        df: DataFrame with subway system data
        
    Returns:
        Selected system ID if a point was clicked, None otherwise
    """
    if df is None or df.empty:
        st.warning("No data available. Please upload data in the Ingest tab.")
        return None
    
    # Create sub-tabs for different plots
    tab1, tab2 = st.tabs(["Lines vs Miles", "Ridership vs Population"])
    
    selected_system_id = None
    
    with tab1:
        selected_system_id = create_lines_vs_miles_plot(df)
    
    with tab2:
        if not selected_system_id:  # Only check second tab if first didn't select
            selected_system_id = create_ridership_vs_population_plot(df)
    
    return selected_system_id
