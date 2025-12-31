"""
Profile panel component for displaying selected subway system information.

Shows "Selected: <SYSTEM_ID>" and row fields from the dataframe.
"""

import pandas as pd
import streamlit as st
from typing import Optional


def render_profile_panel(df: pd.DataFrame, system_id: Optional[str]) -> None:
    """
    Render the profile panel showing selected system information.
    
    Args:
        df: DataFrame with subway system data
        system_id: Selected system ID to display, or None if nothing selected
    """
    if system_id is None:
        st.info("No system selected. Click on a point in the map or plot to view details.")
        return
    
    # Find the row for this system
    system_row = df[df["SYSTEM_ID"] == system_id]
    
    if system_row.empty:
        st.warning(f"System ID '{system_id}' not found in data.")
        return
    
    # Get the first (and should be only) row
    row = system_row.iloc[0]
    
    # Display header
    st.header(f"Selected: {system_id}")
    
    # Display all row fields
    st.subheader("System Details")
    
    # Create a dictionary of all fields (excluding index)
    system_data = {}
    for col in df.columns:
        value = row[col]
        # Format the value nicely
        if pd.isna(value):
            system_data[col] = "N/A"
        elif isinstance(value, (int, float)):
            system_data[col] = value
        else:
            system_data[col] = str(value)
    
    # Display as a dataframe for clean formatting
    display_df = pd.DataFrame({
        "Field": system_data.keys(),
        "Value": system_data.values()
    })
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

