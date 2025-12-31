"""
Map view module for rendering subway systems on a PyDeck map.

Handles map rendering with click selection to set selected_system_id.
"""

import pandas as pd
import streamlit as st
import pydeck as pdk
from typing import Optional


def render_map_view(df: pd.DataFrame) -> Optional[str]:
    """
    Render a PyDeck map with subway system points and handle click selection.
    
    Args:
        df: DataFrame with subway system data including LATITUDE and LONGITUDE
        
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
    
    # Prepare data for PyDeck
    # PyDeck expects a list of dictionaries with lat/lon
    map_data = df_with_coords[[
        "SYSTEM_ID", "LATITUDE", "LONGITUDE", "CITY", "COUNTRY"
    ]].to_dict(orient="records")
    
    # Calculate initial view state (center on data)
    avg_lat = df_with_coords["LATITUDE"].mean()
    avg_lon = df_with_coords["LONGITUDE"].mean()
    
    # Create PyDeck layer
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_data,
        get_position=["LONGITUDE", "LATITUDE"],
        get_color=[255, 255, 255, 200],  # White color with transparency
        get_radius=50000,  # Radius in meters
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

