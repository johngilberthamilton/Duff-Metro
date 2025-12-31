"""
Data ingestion module for Excel file uploads.

Handles Excel file upload, sheet selection, data cleaning, validation,
and storage in session state.
"""

import pandas as pd
import streamlit as st
from typing import Optional, Tuple

from src.validate import validate_dataframe, ValidationError
from src.state import compute_data_version, initialize_session_state


def create_dummy_dataframe() -> pd.DataFrame:
    """
    Create a dummy dataframe for fallback when no Excel file is uploaded.
    
    Returns:
        A sample dataframe with the expected structure
    """
    dummy_data = {
        "SYSTEM_ID": ["NYC_1", "LONDON_1", "TOKYO_1"],
        "CITY": ["New York", "London", "Tokyo"],
        "COUNTRY": ["United States", "United Kingdom", "Japan"],
        "SYSTEM_NAME": ["New York City Subway", "London Underground", "Tokyo Metro"],
        "OPENED_YEAR": [1904, 1863, 1927],
        "NUMBER_OF_LINES": [28, 11, 13],
        "TOTAL_MILES": [245.0, 249.0, 121.0],
        "ANNUAL_RIDERSHIP": [1700000000, 1350000000, 3200000000],
        "CITY_POPULATION": [8800000, 9000000, 14000000],
        "VISITED": ["yes", "yes", "no"],
    }
    return pd.DataFrame(dummy_data)


def load_excel_sheet(file_bytes: bytes, sheet_name: str) -> pd.DataFrame:
    """
    Load a specific sheet from an Excel file.
    
    Args:
        file_bytes: Bytes of the Excel file
        sheet_name: Name of the sheet to load
        
    Returns:
        DataFrame from the specified sheet
    """
    return pd.read_excel(file_bytes, sheet_name=sheet_name, engine='openpyxl')


def get_excel_sheet_names(file_bytes: bytes) -> list:
    """
    Get list of sheet names from an Excel file.
    
    Args:
        file_bytes: Bytes of the Excel file
        
    Returns:
        List of sheet names
    """
    xl_file = pd.ExcelFile(file_bytes, engine='openpyxl')
    return xl_file.sheet_names


def process_excel_upload(
    file_bytes: bytes, 
    selected_sheet: Optional[str] = None
) -> Tuple[Optional[pd.DataFrame], Optional[str], list]:
    """
    Process an uploaded Excel file through validation and cleaning.
    
    Args:
        file_bytes: Bytes of the uploaded Excel file
        selected_sheet: Name of the sheet to load (if None, loads first sheet)
        
    Returns:
        Tuple of (cleaned DataFrame, data_version hash, list of validation issues)
        Returns (None, None, [errors]) if validation fails
    """
    if file_bytes is None or len(file_bytes) == 0:
        return None, None, []
    
    try:
        # Get sheet names
        sheet_names = get_excel_sheet_names(file_bytes)
        
        if not sheet_names:
            return None, None, ["Excel file has no sheets."]
        
        # Use selected sheet or first sheet
        sheet_to_load = selected_sheet if selected_sheet else sheet_names[0]
        
        # Load the sheet
        df_raw = load_excel_sheet(file_bytes, sheet_to_load)
        
        if df_raw.empty:
            return None, None, ["Selected sheet is empty."]
        
        # Validate and clean
        df_cleaned, validation_issues = validate_dataframe(df_raw)
        
        # Compute data version
        data_version = compute_data_version(file_bytes)
        
        return df_cleaned, data_version, validation_issues
        
    except ValidationError as e:
        return None, None, [str(e)]
    except Exception as e:
        return None, None, [f"Error processing Excel file: {str(e)}"]


def render_ingest_tab():
    """
    Render the Ingest tab UI for Excel file upload and preview.
    
    This function handles:
    - File upload widget
    - Sheet selection
    - Data validation
    - Preview display
    - Error display
    - Session state updates
    """
    initialize_session_state()
    
    st.header("Data Ingestion")
    st.markdown("Upload an Excel file containing subway system data.")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose an Excel file",
        type=['xlsx', 'xls'],
        help="Upload an Excel file with subway system data"
    )
    
    # Handle file upload
    if uploaded_file is not None:
        # Store file bytes in session state to avoid re-reading
        file_key = f"file_bytes_{uploaded_file.name}"
        if file_key not in st.session_state or st.session_state.get("current_file_name") != uploaded_file.name:
            st.session_state[file_key] = uploaded_file.read()
            st.session_state.current_file_name = uploaded_file.name
        
        file_bytes = st.session_state[file_key]
        
        # Get sheet names
        try:
            sheet_names = get_excel_sheet_names(file_bytes)
            
            if len(sheet_names) > 1:
                selected_sheet = st.selectbox(
                    "Select the sheet with subway data:",
                    options=sheet_names,
                    help="Choose which sheet contains the subway system data"
                )
            else:
                selected_sheet = sheet_names[0] if sheet_names else None
                st.info(f"Using sheet: {selected_sheet}")
            
            # Process button
            if st.button("Process File", type="primary"):
                with st.spinner("Processing Excel file..."):
                    df_cleaned, data_version, validation_issues = process_excel_upload(
                        file_bytes, 
                        selected_sheet
                    )
                    
                    if df_cleaned is not None:
                        # Store in session state
                        st.session_state.df_core = df_cleaned
                        st.session_state.data_version = data_version
                        
                        st.success(f"✅ File processed successfully! Loaded {len(df_cleaned)} rows.")
                        
                        # Show validation issues if any
                        if validation_issues:
                            st.warning("⚠️ Validation warnings:")
                            for issue in validation_issues:
                                st.text(f"  • {issue}")
                    else:
                        st.error("❌ Failed to process file:")
                        for error in validation_issues:
                            st.error(f"  • {error}")
        except Exception as e:
            st.error(f"Error reading Excel file: {str(e)}")
    
    # Show current dataframe if available
    if st.session_state.df_core is not None:
        st.divider()
        st.subheader("📊 Data Preview")
        st.dataframe(st.session_state.df_core, use_container_width=True)
        
        st.subheader("📈 Data Summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Systems", len(st.session_state.df_core))
        with col2:
            st.metric("Columns", len(st.session_state.df_core.columns))
        with col3:
            if st.session_state.data_version:
                st.metric("Data Version", st.session_state.data_version[:8] + "...")
        
        # Show column info
        with st.expander("Column Information"):
            st.json(list(st.session_state.df_core.columns))
    else:
        # Show dummy data option
        st.divider()
        st.info("💡 No data uploaded yet. Use the file uploader above, or load dummy data to explore the app.")
        
        if st.button("Load Dummy Data", type="secondary"):
            dummy_df = create_dummy_dataframe()
            st.session_state.df_core = dummy_df
            st.session_state.data_version = "dummy_data_v1"
            st.success("✅ Dummy data loaded!")
            st.rerun()

