"""
Map view module for rendering subway systems on a PyDeck map.

Handles map rendering with click selection to set selected_system_id.
"""

import pandas as pd
import streamlit as st
import pydeck as pdk
from typing import Optional, Tuple, List

from src.colors import (
    OPENING_DATE_COLORS,
    VISITED_COLORS,
    DEFAULT_POINT_COLOR,
    TOOLTIP_BACKGROUND_COLOR,
    TOOLTIP_TEXT_COLOR,
    TOOLTIP_BORDER_COLOR
)

def assign_opening_date_category(year: Optional[float]) -> str:
    """
    Assign an opening date category (pre-1985 or 1985+).
    
    Args:
        year: Year value (can be NaN/None)
        
    Returns:
        Category label string: "pre-1985", "1985+", or "unknown"
    """
    if pd.isna(year) or year is None:
        return "unknown"
    
    year_int = int(year)
    return "pre-1985" if year_int < 1985 else "1985+"


def calculate_point_sizes(df: pd.DataFrame, size_by: str, base_size: int = 50000) -> List[float]:
    """
    Calculate point sizes for PyDeck based on the size encoding.
    
    Args:
        df: DataFrame with subway system data
        size_by: One of "None", "Lines", "Miles"
        base_size: Base radius in meters (used when size_by is "None")
        
    Returns:
        List of radius values in meters
    """
    if size_by == "None":
        return [base_size] * len(df)
    
    elif size_by == "Lines":
        if "NUMBER_OF_LINES" not in df.columns:
            return [base_size] * len(df)
        
        # Normalize to a reasonable range (30000 to 225000 meters - max increased by 1.5x)
        values = df["NUMBER_OF_LINES"].fillna(1)
        min_size, max_size = 30000, 225000
        
        if values.max() == values.min():
            return [base_size] * len(df)
        
        normalized = min_size + (values - values.min()) / (values.max() - values.min()) * (max_size - min_size)
        return normalized.fillna(base_size).tolist()
    
    elif size_by == "Miles":
        if "TOTAL_MILES" not in df.columns:
            return [base_size] * len(df)
        
        # Normalize to a reasonable range (30000 to 225000 meters - max increased by 1.5x)
        values = df["TOTAL_MILES"].fillna(1)
        min_size, max_size = 30000, 225000
        
        if values.max() == values.min():
            return [base_size] * len(df)
        
        normalized = min_size + (values - values.min()) / (values.max() - values.min()) * (max_size - min_size)
        return normalized.fillna(base_size).tolist()
    
    return [base_size] * len(df)


def calculate_point_colors(df: pd.DataFrame, color_by: str) -> List[List[int]]:
    """
    Calculate point colors for PyDeck based on the color encoding.
    
    Args:
        df: DataFrame with subway system data
        color_by: One of "None", "Visited", "Opening Date"
        
    Returns:
        List of [R, G, B, A] color tuples
    """
    if color_by == "None":
        return [DEFAULT_POINT_COLOR] * len(df)
    
    elif color_by == "Visited":
        if "VISITED" not in df.columns:
            return [DEFAULT_POINT_COLOR] * len(df)
        
        colors = []
        for visited_val in df["VISITED"]:
            # Handle various formats: boolean, "yes"/"no", "true"/"false"
            is_visited = None
            if pd.isna(visited_val):
                is_visited = None
            elif isinstance(visited_val, bool):
                is_visited = visited_val
            elif isinstance(visited_val, str):
                visited_lower = visited_val.lower().strip()
                is_visited = visited_lower in ["yes", "true", "y", "1"]
            
            colors.append(VISITED_COLORS.get(is_visited, VISITED_COLORS[None]))
        
        return colors
    
    elif color_by == "Opening Date":
        if "OPENED_YEAR" not in df.columns:
            return [DEFAULT_POINT_COLOR] * len(df)
        
        colors = []
        for year in df["OPENED_YEAR"]:
            category = assign_opening_date_category(year)
            colors.append(OPENING_DATE_COLORS.get(category, OPENING_DATE_COLORS["unknown"]))
        
        return colors
    
    return [DEFAULT_POINT_COLOR] * len(df)


def parse_view_mode(view_mode: str) -> Tuple[str, str]:
    """
    Parse the view mode string into size and color encodings.
    
    Args:
        view_mode: The selected view mode string
        
    Returns:
        Tuple of (size_by, color_by) where each is one of:
        - size_by: "None", "Lines", "Miles"
        - color_by: "None", "Visited", "Opening Date"
    """
    if view_mode == "Default":
        return ("None", "None")
    elif view_mode == "Size by Number of Lines":
        return ("Lines", "None")
    elif view_mode == "Size by Total Miles":
        return ("Miles", "None")
    elif view_mode == "Color by Visited Status":
        return ("None", "Visited")
    elif view_mode == "Color by Opening Date":
        return ("None", "Opening Date")
    else:
        return ("None", "None")


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


def _render_color_legend(color_by: str):
    """
    Render a color legend for the current color encoding.
    
    Args:
        color_by: The color encoding type
    """
    if color_by == "None":
        return
    
    st.caption("**Legend:**")
    
    if color_by == "Visited":
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("🟢 Visited")
        with col2:
            st.markdown("🔴 Not Visited")
    
    elif color_by == "Opening Date":
        # Pre-1985 (soft orange) and 1985+ (soft blue)
        pre_color = OPENING_DATE_COLORS["pre-1985"]
        post_color = OPENING_DATE_COLORS["1985+"]
        pre_hex = f"#{pre_color[0]:02x}{pre_color[1]:02x}{pre_color[2]:02x}"
        post_hex = f"#{post_color[0]:02x}{post_color[1]:02x}{post_color[2]:02x}"
        st.markdown(f'<span style="color: {pre_hex}">⬤</span> Pre-1985', unsafe_allow_html=True)
        st.markdown(f'<span style="color: {post_hex}">⬤</span> 1985+', unsafe_allow_html=True)


def render_map_view(df: pd.DataFrame, view_mode: str = "Default") -> Optional[str]:
    """
    Render a PyDeck map with subway system points and handle click selection.
    
    Args:
        df: DataFrame with subway system data including LATITUDE and LONGITUDE
        view_mode: Selected view mode for map encoding
        
    Returns:
        Selected system ID if a point was clicked, None otherwise
    """
    # Filter out rows without coordinates
    df_with_coords = df[
        df["LATITUDE"].notna() & df["LONGITUDE"].notna()
    ].copy()
    
    if df_with_coords.empty:
        st.warning("No systems with valid coordinates to display on map.")
        return None
    
    # Parse view mode to get size and color encodings
    size_by, color_by = parse_view_mode(view_mode)
    
    # Calculate dynamic sizes and colors
    point_sizes = calculate_point_sizes(df_with_coords, size_by)
    point_colors = calculate_point_colors(df_with_coords, color_by)
    
    # Prepare data for PyDeck - add size, color, and tooltip data to each record
    map_data = []
    for i in range(len(df_with_coords)):
        row = df_with_coords.iloc[i]
        
        # Format values for tooltip
        city = str(row.get("CITY", "N/A"))
        country = str(row.get("COUNTRY", "N/A"))
        visited = _format_visited_status(row.get("VISITED"))
        # Use OPENED_YEAR (which should be mapped from "Year opened (General Format)")
        # or fallback to YEAR_OPENED_GENERAL_FORMAT if the column wasn't mapped
        if "OPENED_YEAR" in df_with_coords.columns:
            opened_year = _format_number(row.get("OPENED_YEAR"))
        elif "YEAR_OPENED_GENERAL_FORMAT" in df_with_coords.columns:
            opened_year = _format_number(row.get("YEAR_OPENED_GENERAL_FORMAT"))
        else:
            opened_year = "N/A"
        last_update = _format_number(row.get("LAST_MAJOR_UPDATE"))
        num_lines = _format_number(row.get("NUMBER_OF_LINES"))
        total_miles = _format_number(row.get("TOTAL_MILES"))
        
        # Handle currently accessible column (may not exist)
        currently_accessible = "Unknown"
        if "CURRENTLY_ACCESSIBLE" in df_with_coords.columns:
            currently_accessible = _format_accessible_status(row.get("CURRENTLY_ACCESSIBLE"))
        elif "Currently accessible?" in df_with_coords.columns:
            currently_accessible = _format_accessible_status(row.get("Currently accessible?"))
        
        record = {
            "SYSTEM_ID": row["SYSTEM_ID"],
            "LATITUDE": row["LATITUDE"],
            "LONGITUDE": row["LONGITUDE"],
            "CITY": city,
            "COUNTRY": country,
            "VISITED_DISPLAY": visited,
            "OPENED_YEAR_DISPLAY": opened_year,
            "LAST_UPDATE_DISPLAY": last_update,
            "NUM_LINES_DISPLAY": num_lines,
            "TOTAL_MILES_DISPLAY": total_miles,
            "ACCESSIBLE_DISPLAY": currently_accessible,
            "RADIUS": point_sizes[i],
            "COLOR_R": point_colors[i][0],
            "COLOR_G": point_colors[i][1],
            "COLOR_B": point_colors[i][2],
            "COLOR_A": point_colors[i][3],
        }
        map_data.append(record)
    
    # Calculate initial view state (center on data)
    avg_lat = df_with_coords["LATITUDE"].mean()
    avg_lon = df_with_coords["LONGITUDE"].mean()
    
    # Create PyDeck layer with dynamic properties
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_data,
        get_position=["LONGITUDE", "LATITUDE"],
        get_color="[COLOR_R, COLOR_G, COLOR_B, COLOR_A]",
        get_radius="RADIUS",
        pickable=True,  # Enable click selection
    )
    
    # Create view state
    view_state = pdk.ViewState(
        latitude=avg_lat,
        longitude=avg_lon,
        zoom=2,
        pitch=0,
        bearing=0
    )
    
    # Create tooltip matching Plotly's default style (clean, minimal, white background)
    # Content matches the unified tooltip format
    # PyDeck uses {variable} syntax (single braces) for template variables
    # In f-strings, {{ becomes {, so {{CITY}} in code becomes {CITY} in output
    # Styling matches Plotly's default tooltip exactly: subtle border, minimal padding, no shadow
    tooltip_html = f"""
    <div style="padding: 10px; background-color: {TOOLTIP_BACKGROUND_COLOR}; color: {TOOLTIP_TEXT_COLOR}; border: 1px solid {TOOLTIP_BORDER_COLOR}; border-radius: 3px; font-family: "Open Sans", verdana, arial, sans-serif; font-size: 12px;">
        <div style="font-weight: bold; margin-bottom: 2px;">{{CITY}}, {{COUNTRY}}</div>
        <div>Visited: {{VISITED_DISPLAY}}</div>
        <div>Year Opened: {{OPENED_YEAR_DISPLAY}}</div>
        <div>Last Major Update: {{LAST_UPDATE_DISPLAY}}</div>
        <div>Number of Lines: {{NUM_LINES_DISPLAY}}</div>
        <div>Total Length (mi): {{TOTAL_MILES_DISPLAY}}</div>
        <div>Currently Accessible: {{ACCESSIBLE_DISPLAY}}</div>
    </div>
    """
    
    # Create deck
    deck = pdk.Deck(
        map_style="light",  # Light theme to match app
        initial_view_state=view_state,
        layers=[layer],
        tooltip={"html": tooltip_html}
    )
    
    # Render map
    st.pydeck_chart(deck, use_container_width=True)
    
    # Show legend based on view mode
    if color_by != "None":
        _render_color_legend(color_by)
    
    # Note: Click selection removed as table was removed
    return None

