"""
Streamlit app entrypoint for Subway Systems Visualization.

Main app with three tabs: Ingest, Map, and Plots.
"""

import streamlit as st

from src.ingest import render_ingest_tab

# Configure page
st.set_page_config(
    page_title="Main Page",
    page_icon="🚈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for black background and white lines
st.markdown("""
    <style>
    .stApp {
        background-color: #000000;
        color: #FFFFFF;
    }
    .stMarkdown, .stText {
        color: #FFFFFF;
    }
    /* Keep data visualizations readable */
    [data-testid="stDataFrame"] {
        background-color: #1E1E1E;
    }
    </style>
    """, unsafe_allow_html=True)


def main():
    """Main app function."""
    st.title("🚈 Duff Metro:  Subway Systems Explorer")
    st.markdown("Visualize data about the world's subway systems and explore AI-generated profiles.")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📥 Ingest", "🗺️ Map", "📊 Plots"])
    
    with tab1:
        render_ingest_tab()
    
    with tab2:
        st.header("🗺️ Map View")
        st.info("Map functionality will be implemented in Phase 2.")
        if st.session_state.get("df_core") is not None:
            st.write(f"Ready to visualize {len(st.session_state.df_core)} systems on the map.")
        else:
            st.write("Please upload data in the Ingest tab first.")
    
    with tab3:
        st.header("📊 Plots View")
        st.info("Plots functionality will be implemented in Phase 2.")
        if st.session_state.get("df_core") is not None:
            st.write(f"Ready to create plots for {len(st.session_state.df_core)} systems.")
        else:
            st.write("Please upload data in the Ingest tab first.")


if __name__ == "__main__":
    main()

