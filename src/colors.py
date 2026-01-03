"""
Central color definitions for the Duff Metro application.

All website colors are defined here and initialized via initialize_colors().
This module provides a single source of truth for all color values used
throughout the application.
"""

# UI/Theme Colors (Hex format for CSS)
BACKGROUND_COLOR = "#FFFFFF"
TEXT_COLOR = "#000000"
DATAFRAME_BACKGROUND_COLOR = "#F5F5F5"

# UI/Theme Colors (RGB format for Python/PyDeck)
# RGB values as [R, G, B, A] where each component is 0-255
BACKGROUND_RGB = [255, 255, 255, 255]
TEXT_RGB = [0, 0, 0, 255]
DATAFRAME_BACKGROUND_RGB = [245, 245, 245, 255]

# Default Map Point Color (RGB format) - Royal Blue
DEFAULT_POINT_COLOR = [100, 149, 237, 200]  # Royal blue (CornflowerBlue-ish, soft but darker)

# Visited Status Colors (RGB format) - Soft Green and Soft Red
VISITED_COLORS = {
    True: [152, 223, 138, 255],   # Soft green
    False: [255, 182, 193, 255],   # Soft red (LightPink-ish)
    None: [128, 128, 128, 150]    # Gray for unknown
}

# Opening Date Colors (RGB format) - Pre-1985 (soft orange) and 1985+ (royal blue)
OPENING_DATE_COLORS = {
    "pre-1985": [255, 218, 185, 255],   # Soft orange (PeachPuff-ish)
    "1985+": [100, 149, 237, 255],       # Royal blue (CornflowerBlue-ish, soft but darker)
    "unknown": [128, 128, 128, 150]     # Gray for missing data
}

# Date Bucket Colors (RGB format) - Kept for backwards compatibility but not used for opening date
DATE_BUCKET_COLORS = {
    "pre-1950": [255, 100, 100, 200],      # Red
    "1950-1979": [255, 200, 100, 200],     # Orange
    "1980-1999": [255, 255, 100, 200],     # Yellow
    "2000-2014": [100, 255, 100, 200],     # Green
    "2015+": [100, 200, 255, 200],         # Blue
    "unknown": [128, 128, 128, 150]        # Gray for missing data
}

# Tooltip Colors (for PyDeck map tooltips)
TOOLTIP_BACKGROUND_COLOR = "#FFFFFF"  # White background
TOOLTIP_TEXT_COLOR = "#000000"        # Black text
TOOLTIP_BORDER_COLOR = "#000000"      # Black border

# Plotly Colors (String format for Plotly API)
PLOTLY_BACKGROUND_COLOR = "white"
PLOTLY_PAPER_COLOR = "white"
PLOTLY_FONT_COLOR = "black"
PLOTLY_GRID_COLOR = "lightgray"
PLOTLY_LINE_COLOR = "black"
PLOTLY_MARKER_COLOR = "black"
PLOTLY_MARKER_COLOR_SEQUENCE = ["black"]


def initialize_colors():
    """
    Initialize all color variables.
    
    This function is called during app startup to set up color values.
    Currently, colors are set as module-level constants, but this function
    allows for future expansion (e.g., theme switching, dynamic color loading).
    
    Should be called early in the app initialization process, typically
    from initialize_session_state() in src/state.py.
    """
    # Currently, all colors are defined as module-level constants above.
    # This function exists to:
    # 1. Ensure colors are initialized as part of the app startup process
    # 2. Provide a hook for future color customization or theme switching
    # 3. Maintain consistency with other initialization patterns in the app
    
    # Future: Could load colors from config, environment variables, or theme files here
    pass

