"""
Plots module for subway system visualizations using Plotly.

Creates scatter plots with click selection to set selected_system_id.
"""

import pandas as pd
import streamlit as st
import plotly.express as px
from typing import Optional

from src.colors import (
    PLOTLY_BACKGROUND_COLOR,
    PLOTLY_PAPER_COLOR,
    PLOTLY_FONT_COLOR,
    PLOTLY_GRID_COLOR,
    PLOTLY_LINE_COLOR,
    PLOTLY_MARKER_COLOR,
    PLOTLY_MARKER_COLOR_SEQUENCE
)


def _format_visited_status(visited_val) -> str:
    """Format visited status for display."""
    if pd.isna(visited_val):
        return "Unknown"
    elif isinstance(visited_val, bool):
        return "Yes" if visited_val else "No"
    elif isinstance(visited_val, str):
        visited_lower = visited_val.lower().strip()
        if visited_lower in ["yes", "true", "y", "1"]:
            return "Yes"
        elif visited_lower in ["no", "false", "n", "0"]:
            return "No"
    return "Unknown"


def _format_accessible_status(accessible_val) -> str:
    """Format currently accessible status for display."""
    if pd.isna(accessible_val):
        return "Unknown"
    elif isinstance(accessible_val, bool):
        return "Yes" if accessible_val else "No"
    elif isinstance(accessible_val, str):
        acc_lower = accessible_val.lower().strip()
        if acc_lower in ["yes", "true", "y", "1"]:
            return "Yes"
        elif acc_lower in ["no", "false", "n", "0"]:
            return "No"
    return "Unknown"


def _format_number(value, default="N/A") -> str:
    """Format a numeric value for display."""
    if pd.isna(value):
        return default
    try:
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value)
    except:
        return default


def _create_tooltip_hovertemplate() -> str:
    """
    Create a unified Plotly hovertemplate that matches the map tooltip content.
    Uses Plotly's default styling (white background, clean formatting).
    """
    return (
        "<b>%{customdata[0]}, %{customdata[1]}</b><br>" +
        "Visited: %{customdata[2]}<br>" +
        "Year Opened: %{customdata[3]}<br>" +
        "Last Major Update: %{customdata[4]}<br>" +
        "Number of Lines: %{customdata[5]}<br>" +
        "Total Length (mi): %{customdata[6]}<br>" +
        "Currently Accessible: %{customdata[7]}<extra></extra>"
    )


def _prepare_tooltip_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare DataFrame with formatted tooltip data columns.
    
    Args:
        df: DataFrame with subway system data
        
    Returns:
        DataFrame with additional formatted tooltip columns
    """
    plot_df = df.copy()
    
    # Format visited status
    plot_df["VISITED_DISPLAY"] = plot_df.get("VISITED", pd.Series()).apply(_format_visited_status)
    
    # Format opened year
    if "OPENED_YEAR" in plot_df.columns:
        plot_df["OPENED_YEAR_DISPLAY"] = plot_df["OPENED_YEAR"].apply(_format_number)
    elif "YEAR_OPENED_GENERAL_FORMAT" in plot_df.columns:
        plot_df["OPENED_YEAR_DISPLAY"] = plot_df["YEAR_OPENED_GENERAL_FORMAT"].apply(_format_number)
    else:
        plot_df["OPENED_YEAR_DISPLAY"] = "N/A"
    
    # Format last update
    plot_df["LAST_UPDATE_DISPLAY"] = plot_df.get("LAST_MAJOR_UPDATE", pd.Series()).apply(_format_number)
    
    # Format number of lines
    plot_df["NUM_LINES_DISPLAY"] = plot_df.get("NUMBER_OF_LINES", pd.Series()).apply(_format_number)
    
    # Format total miles
    plot_df["TOTAL_MILES_DISPLAY"] = plot_df.get("TOTAL_MILES", pd.Series()).apply(_format_number)
    
    # Format currently accessible
    if "CURRENTLY_ACCESSIBLE" in plot_df.columns:
        plot_df["ACCESSIBLE_DISPLAY"] = plot_df["CURRENTLY_ACCESSIBLE"].apply(_format_accessible_status)
    elif "Currently accessible?" in plot_df.columns:
        plot_df["ACCESSIBLE_DISPLAY"] = plot_df["Currently accessible?"].apply(_format_accessible_status)
    else:
        plot_df["ACCESSIBLE_DISPLAY"] = "Unknown"
    
    return plot_df


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
    
    # Prepare tooltip data
    plot_df = _prepare_tooltip_data(plot_df)
    
    # Prepare customdata for hovertemplate (order matches _create_tooltip_hovertemplate)
    # Plotly expects custom_data as a list of arrays, where each array is one custom data field
    # So we transpose: each column becomes an array, all arrays have same length (number of rows)
    custom_data_cols = [
        plot_df["CITY"].tolist(),
        plot_df["COUNTRY"].tolist(),
        plot_df["VISITED_DISPLAY"].tolist(),
        plot_df["OPENED_YEAR_DISPLAY"].tolist(),
        plot_df["LAST_UPDATE_DISPLAY"].tolist(),
        plot_df["NUM_LINES_DISPLAY"].tolist(),
        plot_df["TOTAL_MILES_DISPLAY"].tolist(),
        plot_df["ACCESSIBLE_DISPLAY"].tolist(),
    ]
    
    # Create scatter plot
    fig = px.scatter(
        plot_df,
        x="TOTAL_MILES",
        y="NUMBER_OF_LINES",
        custom_data=custom_data_cols,
        labels={
            "TOTAL_MILES": "Total Miles",
            "NUMBER_OF_LINES": "Number of Lines"
        },
        title="Lines vs Miles",
        color_discrete_sequence=PLOTLY_MARKER_COLOR_SEQUENCE
    )
    
    # Update layout for dark theme
    fig.update_layout(
        plot_bgcolor=PLOTLY_BACKGROUND_COLOR,
        paper_bgcolor=PLOTLY_PAPER_COLOR,
        font_color=PLOTLY_FONT_COLOR,
        xaxis=dict(gridcolor=PLOTLY_GRID_COLOR, linecolor=PLOTLY_LINE_COLOR),
        yaxis=dict(gridcolor=PLOTLY_GRID_COLOR, linecolor=PLOTLY_LINE_COLOR)
    )
    
    # Update marker color and tooltip
    fig.update_traces(
        marker=dict(color=PLOTLY_MARKER_COLOR, size=8),
        hovertemplate=_create_tooltip_hovertemplate()
    )
    
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
    
    # Prepare tooltip data
    plot_df = _prepare_tooltip_data(plot_df)
    
    # Prepare customdata for hovertemplate (order matches _create_tooltip_hovertemplate)
    # Plotly expects custom_data as a list of arrays, where each array is one custom data field
    # So we transpose: each column becomes an array, all arrays have same length (number of rows)
    custom_data_cols = [
        plot_df["CITY"].tolist(),
        plot_df["COUNTRY"].tolist(),
        plot_df["VISITED_DISPLAY"].tolist(),
        plot_df["OPENED_YEAR_DISPLAY"].tolist(),
        plot_df["LAST_UPDATE_DISPLAY"].tolist(),
        plot_df["NUM_LINES_DISPLAY"].tolist(),
        plot_df["TOTAL_MILES_DISPLAY"].tolist(),
        plot_df["ACCESSIBLE_DISPLAY"].tolist(),
    ]
    
    # Create scatter plot
    fig = px.scatter(
        plot_df,
        x="CITY_POPULATION",
        y="ANNUAL_RIDERSHIP",
        custom_data=custom_data_cols,
        labels={
            "CITY_POPULATION": "City Population",
            "ANNUAL_RIDERSHIP": "Annual Ridership"
        },
        title="Annual Ridership vs City Population",
        color_discrete_sequence=PLOTLY_MARKER_COLOR_SEQUENCE
    )
    
    # Update layout for dark theme
    fig.update_layout(
        plot_bgcolor=PLOTLY_BACKGROUND_COLOR,
        paper_bgcolor=PLOTLY_PAPER_COLOR,
        font_color=PLOTLY_FONT_COLOR,
        xaxis=dict(gridcolor=PLOTLY_GRID_COLOR, linecolor=PLOTLY_LINE_COLOR),
        yaxis=dict(gridcolor=PLOTLY_GRID_COLOR, linecolor=PLOTLY_LINE_COLOR)
    )
    
    # Update marker color and tooltip
    fig.update_traces(
        marker=dict(color=PLOTLY_MARKER_COLOR, size=8),
        hovertemplate=_create_tooltip_hovertemplate()
    )
    
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
