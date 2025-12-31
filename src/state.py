"""
State management for session state keys and data version tracking.

This module handles the session_state keys used throughout the app,
including df_core, data_version, and selected_system_id.
"""

import hashlib
import streamlit as st


def initialize_session_state():
    """
    Initialize required session state keys if they don't exist.
    
    Sets up:
    - df_core: The cleaned and validated dataframe
    - data_version: Hash of the uploaded Excel file bytes
    - selected_system_id: Currently selected subway system ID
    """
    if "df_core" not in st.session_state:
        st.session_state.df_core = None
    
    if "data_version" not in st.session_state:
        st.session_state.data_version = None
    
    if "selected_system_id" not in st.session_state:
        st.session_state.selected_system_id = None


def compute_data_version(file_bytes: bytes) -> str:
    """
    Compute a deterministic hash of the uploaded Excel file bytes.
    
    This is used as part of the cache key for AI profiles.
    
    Args:
        file_bytes: The raw bytes of the uploaded Excel file
        
    Returns:
        A hexadecimal hash string
    """
    return hashlib.sha256(file_bytes).hexdigest()

