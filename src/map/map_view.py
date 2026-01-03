"""
Map view module for rendering subway systems on a PyDeck map.

Handles map rendering with click selection to set selected_system_id.
"""

import pandas as pd
import streamlit as st
import pydeck as pdk
from typing import Optional, Tuple, List

# Date bucket definitions (from master-plan.md)
DATE_BUCKETS = [
    (None, 1949, "pre-1950"),
    (1950, 1979, "1950-1979"),
    (1980, 1999, "1980-1999"),
    (2000, 2014, "2000-2014"),
    (2015, None, "2015+")
]

# Color palette for date buckets (RGB values, 0-255)
DATE_BUCKET_COLORS = {
    "pre-1950": [255, 100, 100, 200],      # Red
    "1950-1979": [255, 200, 100, 200],     # Orange
    "1980-1999": [255, 255, 100, 200],     # Yellow
    "2000-2014": [100, 255, 100, 200],     # Green
    "2015+": [100, 200, 255, 200],         # Blue
    "unknown": [128, 128, 128, 150]        # Gray for missing data
}

# Color for visited status
VISITED_COLORS = {
    True: [100, 255, 100, 255],   # Bright green
    False: [255, 255, 255, 200],  # White
    None: [128, 128, 128, 150]    # Gray for unknown
}


def assign_date_bucket(year: Optional[float]) -> str:
    """
    Assign a date bucket to a year based on the bucketing logic.
    
    Args:
        year: Year value (can be NaN/None)
        
    Returns:
        Bucket label string
    """
    if pd.isna(year) or year is None:
        return "unknown"
    
    year_int = int(year)
    
    for min_year, max_year, label in DATE_BUCKETS:
        if min_year is None and year_int <= max_year:
            return label
        elif max_year is None and year_int >= min_year:
            return label
        elif min_year <= year_int <= max_year:
            return label
    
    return "unknown"


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
        
        # Normalize to a reasonable range (e.g., 30000 to 150000 meters)
        values = df["NUMBER_OF_LINES"].fillna(1)
        min_size, max_size = 30000, 150000
        
        if values.max() == values.min():
            return [base_size] * len(df)
        
        normalized = min_size + (values - values.min()) / (values.max() - values.min()) * (max_size - min_size)
        return normalized.fillna(base_size).tolist()
    
    elif size_by == "Miles":
        if "TOTAL_MILES" not in df.columns:
            return [base_size] * len(df)
        
        # Normalize to a reasonable range
        values = df["TOTAL_MILES"].fillna(1)
        min_size, max_size = 30000, 150000
        
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
        color_by: One of "None", "Visited", "Opening Date", "Last Update"
        
    Returns:
        List of [R, G, B, A] color tuples
    """
    if color_by == "None":
        return [[255, 255, 255, 200]] * len(df)
    
    elif color_by == "Visited":
        if "VISITED" not in df.columns:
            return [[255, 255, 255, 200]] * len(df)
        
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
            return [[255, 255, 255, 200]] * len(df)
        
        colors = []
        for year in df["OPENED_YEAR"]:
            bucket = assign_date_bucket(year)
            colors.append(DATE_BUCKET_COLORS.get(bucket, DATE_BUCKET_COLORS["unknown"]))
        
        return colors
    
    elif color_by == "Last Update":
        if "LAST_MAJOR_UPDATE" not in df.columns:
            return [[255, 255, 255, 200]] * len(df)
        
        colors = []
        for year in df["LAST_MAJOR_UPDATE"]:
            bucket = assign_date_bucket(year)
            colors.append(DATE_BUCKET_COLORS.get(bucket, DATE_BUCKET_COLORS["unknown"]))
        
        return colors
    
    return [[255, 255, 255, 200]] * len(df)


def parse_view_mode(view_mode: str) -> Tuple[str, str]:
    """
    Parse the view mode string into size and color encodings.
    
    Args:
        view_mode: The selected view mode string
        
    Returns:
        Tuple of (size_by, color_by) where each is one of:
        - size_by: "None", "Lines", "Miles"
        - color_by: "None", "Visited", "Opening Date", "Last Update"
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
    elif view_mode == "Color by Last Major Update":
        return ("None", "Last Update")
    else:
        return ("None", "None")


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
            st.markdown("⚪ Not Visited")
    
    elif color_by in ["Opening Date", "Last Update"]:
        for min_year, max_year, label in DATE_BUCKETS:
            color = DATE_BUCKET_COLORS[label]
            # Create a small colored square using HTML
            color_hex = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
            st.markdown(f'<span style="color: {color_hex}">⬤</span> {label}', unsafe_allow_html=True)


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
    
    # Prepare data for PyDeck - add size and color to each record
    map_data = []
    for i in range(len(df_with_coords)):
        row = df_with_coords.iloc[i]
        record = {
            "SYSTEM_ID": row["SYSTEM_ID"],
            "LATITUDE": row["LATITUDE"],
            "LONGITUDE": row["LONGITUDE"],
            "CITY": row["CITY"],
            "COUNTRY": row["COUNTRY"],
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
    
    # Create deck
    deck = pdk.Deck(
        map_style="dark",  # Dark theme to match app
        initial_view_state=view_state,
        layers=[layer],
        tooltip={
            "text": "{CITY}, {COUNTRY}\nSystem ID: {SYSTEM_ID}"
        }
    )
    
    # Render map
    st.pydeck_chart(deck, use_container_width=True)
    
    # Show legend based on view mode
    if color_by != "None":
        _render_color_legend(color_by)
    
    # Handle selection via clickable dataframe
    # PyDeck click events are complex in Streamlit, so we use a clickable dataframe
    st.subheader("Click a system below to select it")
    
    # Create a simplified dataframe for selection
    selection_df = df_with_coords[[
        "SYSTEM_ID", "CITY", "COUNTRY"
    ]].copy()
    selection_df.index = range(len(selection_df))
    
    # Use st.dataframe with selection_mode to allow clicking
    selected_rows = st.dataframe(
        selection_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row"
    )
    
    # Get selected system ID from selection
    if selected_rows.selection.rows:
        selected_idx = selected_rows.selection.rows[0]
        selected_system_id = selection_df.iloc[selected_idx]["SYSTEM_ID"]
        return selected_system_id
    
    return None

