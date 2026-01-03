"""
Streamlit app entrypoint for Subway Systems Visualization.

Main app with three tabs: Ingest, Map, and Plots.
"""

import streamlit as st

from src.ingest import render_ingest_tab
from src.map.map_view import render_map_view
from src.plots import render_plots_tab
from src.profile.panel import render_profile_panel
from src.state import initialize_session_state
from src.colors import (
    BACKGROUND_COLOR,
    TEXT_COLOR,
    DATAFRAME_BACKGROUND_COLOR
)

# Configure page
st.set_page_config(
    page_title="Main Page",
    page_icon="🚈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for black background and white lines
st.markdown(f"""
    <style>
    .stApp {{
        background-color: {BACKGROUND_COLOR};
        color: {TEXT_COLOR};
    }}
    .stMarkdown, .stText {{
        color: {TEXT_COLOR};
    }}
    /* Keep data visualizations readable */
    [data-testid="stDataFrame"] {{
        background-color: {DATAFRAME_BACKGROUND_COLOR};
    }}
    </style>
    """, unsafe_allow_html=True)


def main():
    """Main app function."""
    initialize_session_state()
    
    # Check for existing S3 table on first run
    if not st.session_state.s3_table_checked:
        st.session_state.s3_table_checked = True
        try:
            from src.s3_storage import check_s3_table_exists, load_table_from_s3
            
            if check_s3_table_exists():
                st.session_state.s3_table_exists = True
                
                # Show preview and choice
                st.title("Duff Metro:  Subway Systems Explorer")
                st.markdown("")
                
                st.info("📦 Found existing preprocessed table in S3.")
                
                # Load and show preview
                df_preview = load_table_from_s3()
                if df_preview is not None:
                    st.subheader("📊 Preview of Existing Table")
                    st.dataframe(df_preview.head(10), use_container_width=True)
                    st.caption(f"Total rows: {len(df_preview)}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Use Existing Table", type="primary", use_container_width=True):
                            st.session_state.df_core = df_preview
                            st.session_state.s3_table_loaded = True
                            st.rerun()
                    
                    with col2:
                        if st.button("📤 Upload New Table", type="secondary", use_container_width=True):
                            st.session_state.s3_table_loaded = False
                            st.rerun()
                else:
                    # If preview failed to load, continue to normal flow
                    st.session_state.s3_table_exists = False
                    st.warning("⚠️ Could not load preview from S3. Proceeding to normal upload flow.")
            else:
                st.session_state.s3_table_exists = False
        except Exception as e:
            # If S3 is not configured or there's an error, continue normally
            st.session_state.s3_table_exists = False
            # Don't show error to user if it's just missing config - app should work without S3
    
    st.title("Duff Metro:  Subway Systems Explorer")
    st.markdown("")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["Ingest", "Map", "Plots"])
    
    with tab1:
        render_ingest_tab()
    
    with tab2:
        st.header("Map View")
        df = st.session_state.get("df_core")
        
        if df is None or df.empty:
            st.info("Please upload data in the Ingest tab first.")
        else:
            # Add selectbox for view mode
            view_mode = st.selectbox(
                "Map View Mode",
                options=[
                    "Default",
                    "Size by Number of Lines",
                    "Size by Total Miles",
                    "Color by Visited Status",
                    "Color by Opening Date"
                ],
                index=0,  # Default to "Default"
                help="Choose how to visualize subway systems on the map"
            )
            
            # Create two columns: map on left, profile on right
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Render map and get selected system
                selected_system_id = render_map_view(df, view_mode=view_mode)
                
                # Update session state if selection changed
                if selected_system_id:
                    st.session_state.selected_system_id = selected_system_id
            
            with col2:
                # Show profile panel
                render_profile_panel(df, st.session_state.get("selected_system_id"))
    
    with tab3:
        st.header("Plots View")
        df = st.session_state.get("df_core")
        
        if df is None or df.empty:
            st.info("Please upload data in the Ingest tab first.")
        else:
            # Create two columns: plots on left, profile on right
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Render plots and get selected system
                selected_system_id = render_plots_tab(df)
                
                # Update session state if selection changed
                if selected_system_id:
                    st.session_state.selected_system_id = selected_system_id
            
            with col2:
                # Show profile panel
                render_profile_panel(df, st.session_state.get("selected_system_id"))


if __name__ == "__main__":
    main()

