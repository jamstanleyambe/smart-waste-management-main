import streamlit as st
import streamlit.components.v1 as components
import folium
from streamlit_folium import folium_static
import requests
import numpy as np
from folium.plugins import MarkerCluster
import json
import altair as alt
import pandas as pd
import datetime as dt
from dateutil import parser as date_parser

try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:  # pragma: no cover - fallback for environments missing extra dependency
    def st_autorefresh(interval=1000, limit=None, key=None):
        """Minimal JS-based fallback to keep the dashboard refreshing."""
        if interval is None or interval <= 0:
            return 0
        refresh_key = key or f"auto_refresh_{interval}"
        limit_js = "null" if limit is None else str(limit)
        script = f"""
        <script>
        (function() {{
            const storageKey = "st-autorefresh-count-" + {json.dumps(refresh_key)};
            const limitValue = {limit_js};
            const count = Number(window.sessionStorage.getItem(storageKey) || 0);
            if (!limitValue || count < limitValue) {{
                window.sessionStorage.setItem(storageKey, count + 1);
                setTimeout(() => window.parent.location.reload(), {int(interval)});
            }}
        }})();
        </script>
        """
        components.html(script, height=0, width=0)
        state_key = "_autorefresh_missing_dependency_notice"
        if not st.session_state.get(state_key):
            st.caption("⚠️ Install `streamlit-autorefresh` for smoother live updates.")
            st.session_state[state_key] = True
        return 0

# Configure Streamlit page
st.set_page_config(
    page_title="Smart Waste Management Dashboard",
    page_icon="🗑️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
DOUALA5_CENTER = [4.0511, 9.7679]
API_BASE_URL = "http://localhost:8000/api"
LIVE_REFRESH_INTERVAL_MS = 500

# Inject custom CSS
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Inject custom JavaScript (example: a simple alert)
def local_js(script_content):
    st.markdown(f'<script>{script_content}</script>', unsafe_allow_html=True)

# Call the function to inject CSS
local_css("style.css")

# Call the function to inject JS (example)
local_js("console.log('Hello from Streamlit JS!');")

# Inject custom CSS for full-width layout and map styling
st.markdown("""
<style>
    /* Global fix for all Streamlit elements to fit screen */
    html, body {
        width: 100% !important;
        max-width: 100% !important;
        overflow-x: hidden !important;
    }
    
    /* Target the specific problematic element you mentioned */
    .st-emotion-cache-6px8kg.e4man1110,
    [class*="st-emotion-cache-6px8kg"] {
        width: 100% !important;
        max-width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
        box-sizing: border-box !important;
        overflow: hidden !important;
    }
    
    /* Additional selectors for the specific element */
    .e4man1110,
    [class*="e4man1110"] {
        width: 100% !important;
        max-width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
        box-sizing: border-box !important;
        overflow: hidden !important;
    }
    
    /* Force any element with 6px8kg in class to fit */
    [class*="6px8kg"] {
        width: 100% !important;
        max-width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
        box-sizing: border-box !important;
        overflow: hidden !important;
    }
    
    /* Universal fix for all emotion cache elements */
    [class*="st-emotion-cache"] {
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
    }
    
    /* Full-Width Layout - Remove All White Space */
    .main .block-container {
        padding: 1rem 0.5rem !important;
        max-width: 100% !important;
        margin: 0 !important;
        width: 100% !important;
    }
    
    /* Expand all content to full screen width */
    .main .block-container > div {
        max-width: 100% !important;
        width: 100% !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    
    /* Force full width for all Streamlit elements */
    .stMarkdown, .stHeader, .stSubheader, .stText, .stMap, .stDataFrame {
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* Remove default Streamlit margins and padding */
    .stMarkdown > div {
        max-width: 100% !important;
        width: 100% !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    
    /* Full-width map container */
    .stMap {
        width: 100% !important;
        max-width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Force map to span full width */
    .stMap > div {
        width: 100% !important;
        max-width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Map iframe full width */
    .stMap iframe {
        width: 100% !important;
        max-width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
        border: none !important;
    }
    
    /* Map container wrapper */
    .stMap > div > div {
        width: 100% !important;
        max-width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Force all map elements to full width */
    .stMap * {
        max-width: 100% !important;
        box-sizing: border-box !important;
    }
    
    /* Ensure main content area content spans end-to-end */
    .main .block-container > div:not(.stSidebar):not(.sidebar) {
        display: flex !important;
        flex-direction: column !important;
        width: 100% !important;
        max-width: 100% !important;
        flex-grow: 1 !important;
        flex-shrink: 0 !important;
        position: relative !important;
        left: 0 !important;
        margin-left: 0 !important;
        padding-left: 0 !important;
    }
    
    /* Force sidebar and main content to touch */
    .stSidebar, .sidebar .sidebar-content {
        margin-right: 0 !important;
        padding-right: 0 !important;
        border-right: none !important;
        outline: none !important;
        box-shadow: none !important;
    }
    
    .main .block-container > div:not(.stSidebar):not(.sidebar) {
        margin-left: 0 !important;
        padding-left: 0 !important;
        border-left: none !important;
        outline: none !important;
        box-shadow: none !important;
    }
    
    /* Eliminate ALL possible white space */
    .main .block-container {
        gap: 0 !important;
        column-gap: 0 !important;
        row-gap: 0 !important;
    }
    
    /* Force containers to be absolutely adjacent */
    .stSidebar, .sidebar .sidebar-content {
        position: relative !important;
        right: 0 !important;
        z-index: 1 !important;
    }
    
    .main .block-container > div:not(.stSidebar):not(.sidebar) {
        position: relative !important;
        left: 0 !important;
        z-index: 1 !important;
    }
    
    /* Remove any default browser spacing */
    * {
        box-sizing: border-box !important;
    }
    
    /* Ensure no gaps in flexbox */
    .main .block-container > * {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Force absolute adjacency with no white space */
    .stSidebar, .sidebar .sidebar-content {
        margin: 0 !important;
        padding: 0.5rem 0.5rem 0.5rem 0.5rem !important;
        padding-right: 0 !important;
        margin-right: 0 !important;
    }
    
    .main .block-container > div:not(.stSidebar):not(.sidebar) {
        margin: 0 !important;
        padding: 0 !important;
        margin-left: 0 !important;
        padding-left: 0 !important;
    }
    
    /* Remove any remaining visual separators */
    .stSidebar::after,
    .sidebar .sidebar-content::after {
        display: none !important;
        content: none !important;
    }
    
    .main .block-container > div:not(.stSidebar):not(.sidebar)::before {
        display: none !important;
        content: none !important;
    }
    
    /* Force all direct children in main area to full width */
    .main .block-container > div:not(.stSidebar):not(.sidebar) > * {
        width: 100% !important;
        max-width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Ensure search section spans full width */
    .main .block-container > div:not(.stSidebar):not(.sidebar) .stHorizontalBlock {
        width: 100% !important;
        max-width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Layout: Sidebar 25%, Main Content 75% */
    .main .block-container {
        display: flex !important;
        flex-direction: row !important;
        gap: 0 !important;
        padding: 0 !important;
        max-width: 100vw !important;
        width: 100vw !important;
        margin: 0 !important;
        align-items: stretch !important;
        justify-content: flex-start !important;
        overflow: hidden !important;
    }
    
    /* Sidebar for "Route through selected bins" - 20% width */
    .stSidebar, .sidebar .sidebar-content {
        width: 25% !important;
        min-width: 25% !important;
        max-width: 25% !important;
        flex: 0 0 25% !important;
        padding: 0.5rem !important;
        margin-right: 0 !important;
        padding-right: 0 !important;
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%) !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1) !important;
    }
    
    /* Main content area - 75% width */
    .main .block-container > div:not(.stSidebar):not(.sidebar) {
        width: 75% !important;
        flex: 1 !important;
        max-width: 75% !important;
        margin-left: 0 !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
        margin-right: 0 !important;
        border-left: none !important;
    }
    
    /* Ensure the map takes full width of its container */
    .stMap, .folium-map, .leaflet-container {
        width: 100% !important;
        max-width: 100% !important;
    }
    
    /* Force main content to span end-to-end within its container */
    .main .block-container > div:not(.stSidebar):not(.sidebar) > div {
        width: 100% !important;
        max-width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Ensure all content inside main area spans full width */
    .main .block-container > div:not(.stSidebar):not(.sidebar) .stMarkdown,
    .main .block-container > div:not(.stSidebar):not(.sidebar) .stHeader,
    .main .block-container > div:not(.stSidebar):not(.sidebar) .stSubheader,
    .main .block-container > div:not(.stSidebar):not(.sidebar) .stText,
    .main .block-container > div:not(.stSidebar):not(.sidebar) .stMap,
    .main .block-container > div:not(.stSidebar):not(.sidebar) .stDataFrame {
        width: 100% !important;
        max-width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Force all Streamlit widgets in main area to full width */
    .main .block-container > div:not(.stSidebar):not(.sidebar) .stButton,
    .main .block-container > div:not(.stSidebar):not(.sidebar) .stSelectbox,
    .main .block-container > div:not(.stSidebar):not(.sidebar) .stTextInput,
    .main .block-container > div:not(.stSidebar):not(.sidebar) .stNumberInput {
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
    }
    
    /* Responsive design for different screen sizes */
    @media (max-width: 1200px) {
        .main .block-container {
            padding: 0.5rem !important;
            flex-direction: row !important;
            gap: 0 !important;
        }
        
        .stSidebar, .sidebar .sidebar-content {
            width: 25% !important;
            min-width: 25% !important;
        }
        
        .main .block-container > div:not(.stSidebar):not(.sidebar) {
            width: 75% !important;
        }
        
        [class*="st-emotion-cache"] {
            width: 100% !important;
            max-width: 100% !important;
        }
    }
    
    @media (max-width: 768px) {
        .main .block-container {
            padding: 0.25rem !important;
            flex-direction: column !important;
            gap: 0.5rem !important;
        }
        
        .stSidebar, .sidebar .sidebar-content {
            width: 100% !important;
            min-width: 100% !important;
            max-width: 100% !important;
            flex: none !important;
        }
        
        .main .block-container > div:not(.stSidebar):not(.sidebar) {
            width: 100% !important;
            max-width: 100% !important;
        }
        
        .st-emotion-cache-6px8kg.e4man1110 {
            width: 100% !important;
            max-width: 100% !important;
        }
        
        /* Ensure mobile-friendly layout */
        .stMarkdown, .stHeader, .stSubheader {
            padding: 0.5rem !important;
        }
    }
    
    @media (max-width: 480px) {
        .main .block-container {
            padding: 0.1rem !important;
            flex-direction: column !important;
            gap: 0.25rem !important;
        }
        
        .stSidebar, .sidebar .sidebar-content {
            width: 100% !important;
            min-width: 100% !important;
            max-width: 100% !important;
            flex: none !important;
        }
        
        .main .block-container > div:not(.stSidebar):not(.sidebar) {
            width: 100% !important;
            max-width: 100% !important;
        }
        
        /* Extra small screen optimizations */
        [class*="st-emotion-cache"] {
            width: 100% !important;
            max-width: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
        }
    }
    
    /* Target Folium map container for end-to-end span */
    .folium-map.leaflet-container.leaflet-touch.leaflet-retina.leaflet-fade-anim.leaflet-grab.leaflet-touch-drag.leaflet-touch-zoom {
        width: 100% !important;
        max-width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
        left: 0 !important;
        right: 0 !important;
    }
    
    /* Alternative Folium selectors for broader coverage */
    .folium-map {
        width: 100% !important;
        max-width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    .leaflet-container {
        width: 100% !important;
        max-width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Force all Folium elements to full width */
    .folium-map *, .leaflet-container * {
        max-width: 100% !important;
        box-sizing: border-box !important;
    }
    
    /* Enhanced Folium map end-to-end span */
    .folium-map.leaflet-container.leaflet-touch.leaflet-retina.leaflet-fade-anim.leaflet-grab.leaflet-touch-drag.leaflet-touch-zoom {
        width: 100vw !important;
        max-width: 100vw !important;
        margin: 0 !important;
        padding: 0 !important;
        left: 0 !important;
        right: 0 !important;
        position: relative !important;
    }
    
    /* Force Folium map to use full viewport width */
    .folium-map {
        width: 100vw !important;
        max-width: 100vw !important;
        margin: 0 !important;
        padding: 0 !important;
        left: 0 !important;
        right: 0 !important;
    }
    
    /* Leaflet container full width */
    .leaflet-container {
        width: 100vw !important;
        max-width: 100vw !important;
        margin: 0 !important;
        padding: 0 !important;
        left: 0 !important;
        right: 0 !important;
    }
    
    /* Force all map elements to use full width */
    .folium-map > div, .leaflet-container > div {
        width: 100% !important;
        max-width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Map tiles full width */
    .leaflet-tile-pane, .leaflet-overlay-pane, .leaflet-marker-pane {
        width: 100% !important;
        max-width: 100% !important;
    }
    
    /* Target Streamlit element container for end-to-end span */
    .stElementContainer.element-container.st-emotion-cache-1clwqzo.eertqu00 {
        width: 100vw !important;
        max-width: 100vw !important;
        margin: 0 !important;
        padding: 0 !important;
        left: 0 !important;
        right: 0 !important;
        position: relative !important;
    }
    
    /* Alternative selectors for broader coverage */
    .stElementContainer {
        width: 100vw !important;
        max-width: 100vw !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    .element-container {
        width: 100vw !important;
        max-width: 100vw !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    .st-emotion-cache-1clwqzo.eertqu00 {
        width: 100vw !important;
        max-width: 100vw !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Force all content inside to use full width */
    .stElementContainer > div, .element-container > div {
        width: 100% !important;
        max-width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Target specific container for end-to-end spread */
    .st-emotion-cache-lxqt60.e1cbzgzq10 {
        width: 100% !important;
        max-width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
        left: 0 !important;
        right: 0 !important;
    }
    
    /* Force all content inside to spread end-to-end */
    .st-emotion-cache-lxqt60.e1cbzgzq10 > div {
        width: 100% !important;
        max-width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Alternative selector in case class changes */
    .st-emotion-cache-lxqt60 {
        width: 100% !important;
        max-width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Target stMain container for smaller size with nice padding */
    .stMain.st-emotion-cache-z4kicb.e1cbzgzq1 {
        width: 90% !important;
        max-width: 1200px !important;
        margin: 0 auto !important;
        padding: 2rem !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1) !important;
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%) !important;
    }
    
    /* Force all content inside stMain to fit properly */
    .stMain.st-emotion-cache-z4kicb.e1cbzgzq1 > div {
        width: 100% !important;
        max-width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Universal fix for all Streamlit emotion cache elements to fit screen */
    [class*="st-emotion-cache"] {
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
    }
    
    /* Specific fix for the problematic element you mentioned */
    .st-emotion-cache-6px8kg.e4man1110 {
        width: 100% !important;
        max-width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
        box-sizing: border-box !important;
        overflow: hidden !important;
    }
    
    /* Force all Streamlit containers to use full width */
    .stElementContainer, .element-container, .stBlock, .stHorizontalBlock {
        width: 100% !important;
        max-width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
        box-sizing: border-box !important;
    }
    
    /* Reduce margin and padding for specific Streamlit main container */
    .stMain.st-emotion-cache-4rsbii.e4man111,
    .st-emotion-cache-4rsbii.e4man111 {
        margin: 30px !important;
        padding: 20px !important;
        margin-top: 30px !important;
        margin-bottom: 30px !important;
        margin-left: 30px !important;
        margin-right: 30px !important;
        padding-top: 20px !important;
        padding-bottom: 20px !important;
        padding-left: 20px !important;
        padding-right: 20px !important;
    }
    
    /* Target any element with the specific class combination */
    [class*="4rsbii"][class*="e4man111"] {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Alternative selector for broader coverage */
    .e4man111 {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Ensure all content inside Streamlit elements fits */
    [class*="st-emotion-cache"] > div,
    .stElementContainer > div,
    .element-container > div {
        width: 100% !important;
        max-width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
        box-sizing: border-box !important;
    }
    
    /* Fix for any horizontally scrolling elements */
    .stHorizontalBlock > div {
        width: 100% !important;
        max-width: 100% !important;
        overflow-x: hidden !important;
    }
    
        /* Ensure the main app container fits the screen */
    .main .block-container {
        width: 100% !important;
        max-width: 100% !important;
        padding: 1rem !important;
        margin: 0 !important;
    }
    
    /* Prevent horizontal scrolling and ensure all content fits */
    .main {
        overflow-x: hidden !important;
        width: 100% !important;
        max-width: 100% !important;
    }
    
    /* Force all Streamlit widgets to fit within screen bounds */
    .stButton, .stSelectbox, .stTextInput, .stNumberInput {
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
    }
    
    /* Ensure search and control elements don't overflow */
    .stHorizontalBlock {
        width: 100% !important;
        max-width: 100% !important;
        overflow-x: hidden !important;
    }
    
    /* Responsive design for mobile and tablet */
    @media (max-width: 768px) {
        .stMain.st-emotion-cache-z4kicb.e1cbzgzq1 {
            width: 95% !important;
            padding: 1rem !important;
        }
        
        [class*="st-emotion-cache"] {
            width: 100% !important;
            max-width: 100% !important;
        }
        
        .st-emotion-cache-6px8kg.e4man1110 {
            width: 100% !important;
            max-width: 100% !important;
        }
    }
    
    /* Extra small screens */
    @media (max-width: 480px) {
        .stMain.st-emotion-cache-z4kicb.e1cbzgzq1 {
            width: 98% !important;
            padding: 0.5rem !important;
        }
    }
    
    /* Alternative stMain selectors */
    .stMain {
        width: 90% !important;
        max-width: 1200px !important;
        margin: 0 auto !important;
        padding: 2rem !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1) !important;
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%) !important;
    }
    
    .st-emotion-cache-z4kicb.e1cbzgz1 {
        width: 90% !important;
        max-width: 1200px !important;
        margin: 0 auto !important;
        padding: 2rem !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1) !important;
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%) !important;
    }
    
    /* Professional Form Styling */
    .stSelectbox, .stTextInput, .stButton {
        margin: 0.5rem 0 !important;
        width: 100% !important;
    }
    
    /* Additional overflow prevention */
    .stMain, .stMain > div, .main .block-container, .main .block-container > div {
        overflow-x: hidden !important;
        box-sizing: border-box !important;
    }
    
    .stMain * {
        max-width: 100% !important;
        box-sizing: border-box !important;
    }
</style>
""", unsafe_allow_html=True)

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate Euclidean distance between two points in kilometers"""
    R = 6371  # Earth's radius in kilometers
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

def get_bins():
    """Fetch all bins from the API"""
    response = requests.get(f"{API_BASE_URL}/bin-data/")
    if response.status_code == 200:
        data = response.json()
        # Handle paginated response
        if isinstance(data, dict) and 'results' in data:
            return data['results']
        return data
    return []

def get_dumping_spots():
    """Fetch all dumping spots from the API"""
    response = requests.get(f"{API_BASE_URL}/dumping-spots/")
    if response.status_code == 200:
        data = response.json()
        # Handle paginated response
        if isinstance(data, dict) and 'results' in data:
            return data['results']
        return data
    return []

def get_trucks():
    """Fetch all trucks from the API"""
    response = requests.get(f"{API_BASE_URL}/trucks/")
    if response.status_code == 200:
        data = response.json()
        # Handle paginated response
        if isinstance(data, dict) and 'results' in data:
            return data['results']
        return data
    return []

def add_bin(bin_data):
    """Add a new bin via the API"""
    response = requests.post(f"{API_BASE_URL}/bin-data/", json=bin_data)
    return response.status_code == 201



def create_map(bins, dumping_spots, trucks, selected_bin=None, path=None, highlight_item=None, highlight_type=None):
    m = folium.Map(
        location=[4.0511, 9.7679], 
        zoom_start=7,
        tiles='OpenStreetMap',
        control_scale=True,
        prefer_canvas=True,
        width='100%',
        height='800px'
    )
    
    # Add truck markers
    for truck in trucks:
        # Create enhanced truck popup content
        status_color = "#e74c3c" if truck['status'] == 'MAINTENANCE' else "#27ae60" if truck['status'] == 'ACTIVE' else "#f39c12"
        status_icon = "🔧" if truck['status'] == 'MAINTENANCE' else "✅" if truck['status'] == 'ACTIVE' else "⏸️"
        
        truck_popup_content = f"""
        <div style="
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
            color: white;
            padding: 15px;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            min-width: 280px;
            border: 2px solid rgba(255,255,255,0.2);
        ">
            <div style="
                text-align: center;
                margin-bottom: 12px;
                padding-bottom: 8px;
                border-bottom: 2px solid rgba(255,255,255,0.3);
            ">
                <h3 style="
                    margin: 0;
                    font-size: 18px;
                    font-weight: bold;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
                    color: #fff;
                ">🚛 Waste Truck</h3>
            </div>
            
            <div style="margin-bottom: 8px;">
                <span style="
                    display: inline-block;
                    background: rgba(255,255,255,0.2);
                    padding: 4px 8px;
                    border-radius: 20px;
                    font-weight: bold;
                    font-size: 11px;
                    margin-right: 8px;
                    min-width: 60px;
                    text-align: center;
                ">ID</span>
                <span style="font-weight: bold; font-size: 14px;">{truck['truck_id']}</span>
            </div>
            
            <div style="margin-bottom: 8px;">
                <span style="
                    display: inline-block;
                    background: rgba(255,255,255,0.2);
                    padding: 4px 8px;
                    border-radius: 20px;
                    font-weight: bold;
                    font-size: 11px;
                    margin-right: 8px;
                    min-width: 60px;
                    text-align: center;
                ">STATUS</span>
                <span style="
                    background: {status_color};
                    color: white;
                    padding: 3px 8px;
                    border-radius: 15px;
                    font-weight: bold;
                    font-size: 13px;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
                ">{status_icon} {truck['status']}</span>
            </div>
            
            <div style="
                background: rgba(255,255,255,0.1);
                padding: 10px;
                border-radius: 8px;
                margin: 8px 0;
            ">
                <div style="font-weight: bold; margin-bottom: 6px; color: #f1c40f;">👨‍💼 Driver & Details</div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span>👤 Driver:</span>
                    <span style="font-weight: bold; color: #ecf0f1;">{truck['driver_name']}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span>⛽ Fuel Level:</span>
                    <span style="font-weight: bold; color: #e67e22;">{truck['fuel_level']:.1f}%</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span>📍 Location:</span>
                    <span style="font-weight: bold; color: #95a5a6; font-size: 10px;">
                        {truck['current_latitude']:.4f}, {truck['current_longitude']:.4f}
                    </span>
                </div>
            </div>
            
            <div style="
                font-size: 10px;
                color: rgba(255,255,255,0.7);
                text-align: center;
                margin-top: 10px;
                padding-top: 8px;
                border-top: 1px solid rgba(255,255,255,0.2);
            ">
                📅 Updated: {truck['last_updated'][:16].replace('T', ' ')}
            </div>
        </div>
        """
        
        folium.Marker(
            [truck['current_latitude'], truck['current_longitude']],
            popup=folium.Popup(truck_popup_content, max_width=320),
            icon=folium.Icon(color='blue', icon='truck', prefix='fa')
        ).add_to(m)
    
        # Add enhanced truck ID label above the marker
        folium.Marker(
            [truck['current_latitude'], truck['current_longitude']],
            icon=folium.DivIcon(
                html=f'<div style="font-size:8px;font-weight:bold;color:white;background:rgba(30,144,255,0.95);border:2px solid white;border-radius:4px;padding:1px 3px;text-align:center;display:flex;align-items:center;justify-content:center;white-space:nowrap;box-shadow:0 3px 6px rgba(0,0,0,0.4);transform:translate(-50%,-95%);letter-spacing:0.2px;">{truck["truck_id"]}</div>',
                icon_size=(38, 10),
                icon_anchor=(19, 20)
            )
        ).add_to(m)
    
    # Add bin markers with different colors based on fill level
    for bin in bins:
        # Technical support bins: fill_level < 0 or > 100
        if bin['fill_level'] < 0 or bin['fill_level'] > 100:
            color = 'gray'
            icon = folium.Icon(color=color, icon='exclamation-triangle', prefix='fa')
        elif bin['fill_level'] == 100:
            color = 'red'
            # Enhanced 100% full bins with warning symbols and animations
            icon_html = f'''
                <div style="
                    width: 32px; 
                    height: 32px; 
                    background: linear-gradient(45deg, #dc143c, #ff4444); 
                    border: 3px solid white;
                    border-radius: 50%; 
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    animation: alertBlink 1s infinite;
                    box-shadow: 0 0 15px rgba(220, 20, 60, 0.8);
                    position: relative;
                ">
                    <span style="color: white; font-size: 16px; text-shadow: 1px 1px 2px rgba(0,0,0,0.8);">🚨</span>
                    <div style="
                        position: absolute;
                        top: -6px;
                        right: -6px;
                        background-color: #ffff00;
                        color: #dc143c;
                        border-radius: 50%;
                        width: 14px;
                        height: 14px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 8px;
                        font-weight: bold;
                        border: 2px solid white;
                        animation: pulse 0.6s infinite;
                    ">⚠</div>
                </div>
                <style>
                    @keyframes alertBlink {{
                        0% {{ opacity: 1; transform: scale(1); }}
                        50% {{ opacity: 0.7; transform: scale(1.05); }}
                        100% {{ opacity: 1; transform: scale(1); }}
                    }}
                    @keyframes pulse {{
                        0% {{ transform: scale(1); }}
                        50% {{ transform: scale(1.3); }}
                        100% {{ transform: scale(1); }}
                    }}
                </style>
            '''
            icon = folium.DivIcon(html=icon_html, icon_size=(32, 32), icon_anchor=(16, 16))
        elif bin['fill_level'] >= 80:
            color = 'orange'
            icon = folium.Icon(color=color)
        elif bin['fill_level'] >= 50:
            color = 'yellow'
            icon = folium.Icon(color=color)
        elif bin['fill_level'] < 50:
            color = 'green'
            icon = folium.Icon(color=color)
        else:
            color = 'gray'
            icon = folium.Icon(color=color)
        
        # Create enhanced popup content with professional styling
        fill_color = "#e74c3c" if bin['fill_level'] >= 80 else "#f39c12" if bin['fill_level'] >= 50 else "#27ae60"
        popup_content = f"""
        <div style="
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            min-width: 280px;
            border: 2px solid rgba(255,255,255,0.2);
        ">
            <div style="
                text-align: center;
                margin-bottom: 12px;
                padding-bottom: 8px;
                border-bottom: 2px solid rgba(255,255,255,0.3);
            ">
                <h3 style="
                    margin: 0;
                    font-size: 18px;
                    font-weight: bold;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
                    color: #fff;
                ">🗑️ Waste Bin</h3>
            </div>
            
            <div style="margin-bottom: 8px;">
                <span style="
                    display: inline-block;
                    background: rgba(255,255,255,0.2);
                    padding: 4px 8px;
                    border-radius: 20px;
                    font-weight: bold;
                    font-size: 11px;
                    margin-right: 8px;
                    min-width: 60px;
                    text-align: center;
                ">ID</span>
                <span style="font-weight: bold; font-size: 14px;">{bin['bin_id']}</span>
            </div>
            
            <div style="margin-bottom: 8px;">
                <span style="
                    display: inline-block;
                    background: rgba(255,255,255,0.2);
                    padding: 4px 8px;
                    border-radius: 20px;
                    font-weight: bold;
                    font-size: 11px;
                    margin-right: 8px;
                    min-width: 60px;
                    text-align: center;
                ">FILL</span>
                <span style="
                    background: {fill_color};
                    color: white;
                    padding: 3px 8px;
                    border-radius: 15px;
                    font-weight: bold;
                    font-size: 13px;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
                ">{bin['fill_level']:.1f}%</span>
            </div>
            
            <div style="
                background: rgba(255,255,255,0.1);
                padding: 10px;
                border-radius: 8px;
                margin: 8px 0;
            ">
                <div style="font-weight: bold; margin-bottom: 6px; color: #f1c40f;">📊 Composition</div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span>🥬 Organic:</span>
                    <span style="font-weight: bold; color: #2ecc71;">{bin['organic_percentage']:.1f}%</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span>♻️ Plastic:</span>
                    <span style="font-weight: bold; color: #3498db;">{bin['plastic_percentage']:.1f}%</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span>🔩 Metal:</span>
                    <span style="font-weight: bold; color: #95a5a6;">{bin['metal_percentage']:.1f}%</span>
                </div>
            </div>
            
            <div style="
                font-size: 10px;
                color: rgba(255,255,255,0.7);
                text-align: center;
                margin-top: 10px;
                padding-top: 8px;
                border-top: 1px solid rgba(255,255,255,0.2);
            ">
                📅 Updated: {bin['last_updated'][:16].replace('T', ' ')}
            </div>
        </div>
        """
        
        # Add marker to map
        folium.Marker(
            [bin['latitude'], bin['longitude']],
            popup=folium.Popup(popup_content, max_width=320),
            icon=icon
        ).add_to(m)

        # Add enhanced bin ID label above the marker
        folium.Marker(
            [bin['latitude'], bin['longitude']],
            icon=folium.DivIcon(
                html=f'<div style="font-size:8px;font-weight:bold;color:white;background:rgba(0,0,0,0.9);border:2px solid white;border-radius:4px;padding:1px 3px;text-align:center;display:flex;align-items:center;justify-content:center;white-space:nowrap;box-shadow:0 3px 6px rgba(0,0,0,0.4);transform:translate(-50%,-100%);letter-spacing:0.2px;">{bin["bin_id"]}</div>',
                icon_size=(28, 10),
                icon_anchor=(14, 20)
            )
        ).add_to(m)

    # Add dumping spot markers
    for spot in dumping_spots:
        # Calculate fill level and percentages
        total_content = spot['organic_content'] + spot['plastic_content'] + spot['metal_content']
        fill_level = (total_content / spot['total_capacity']) * 100 if spot['total_capacity'] > 0 else 0
        
        organic_percentage = (spot['organic_content'] / total_content) * 100 if total_content > 0 else 0
        plastic_percentage = (spot['plastic_content'] / total_content) * 100 if total_content > 0 else 0
        metal_percentage = (spot['metal_content'] / total_content) * 100 if total_content > 0 else 0
        
        # Create enhanced dumping spot popup content
        capacity_color = "#e74c3c" if fill_level >= 80 else "#f39c12" if fill_level >= 50 else "#27ae60"
        
        popup_content = f"""
        <div style="
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%);
            color: white;
            padding: 15px;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            min-width: 280px;
            border: 2px solid rgba(255,255,255,0.2);
        ">
            <div style="
                text-align: center;
                margin-bottom: 12px;
                padding-bottom: 8px;
                border-bottom: 2px solid rgba(255,255,255,0.3);
            ">
                <h3 style="
                    margin: 0;
                    font-size: 18px;
                    font-weight: bold;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
                    color: #fff;
                ">🗑️ Dumping Spot</h3>
            </div>
            
            <div style="margin-bottom: 8px;">
                <span style="
                    display: inline-block;
                    background: rgba(255,255,255,0.2);
                    padding: 4px 8px;
                    border-radius: 20px;
                    font-weight: bold;
                    font-size: 11px;
                    margin-right: 8px;
                    min-width: 60px;
                    text-align: center;
                ">ID</span>
                <span style="font-weight: bold; font-size: 14px;">{spot['spot_id']}</span>
            </div>
            
            <div style="margin-bottom: 8px;">
                <span style="
                    display: inline-block;
                    background: rgba(255,255,255,0.2);
                    padding: 4px 8px;
                    border-radius: 20px;
                    font-weight: bold;
                    font-size: 11px;
                    margin-right: 8px;
                    min-width: 60px;
                    text-align: center;
                ">FILL</span>
                <span style="
                    background: {capacity_color};
                    color: white;
                    padding: 3px 8px;
                    border-radius: 15px;
                    font-weight: bold;
                    font-size: 13px;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
                ">{fill_level:.1f}%</span>
            </div>
            
            <div style="margin-bottom: 8px;">
                <span style="
                    display: inline-block;
                    background: rgba(255,255,255,0.2);
                    padding: 4px 8px;
                    border-radius: 20px;
                    font-weight: bold;
                    font-size: 11px;
                    margin-right: 8px;
                    min-width: 60px;
                    text-align: center;
                ">CAPACITY</span>
                <span style="
                    background: #8e44ad;
                    color: white;
                    padding: 3px 8px;
                    border-radius: 15px;
                    font-weight: bold;
                    font-size: 13px;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
                ">{spot['total_capacity']:.1f} tons</span>
            </div>
            
            <div style="
                background: rgba(255,255,255,0.1);
                padding: 10px;
                border-radius: 8px;
                margin: 8px 0;
            ">
                <div style="font-weight: bold; margin-bottom: 6px; color: #f1c40f;">📊 Waste Composition</div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span>🥬 Organic:</span>
                    <span style="font-weight: bold; color: #2ecc71;">{organic_percentage:.1f}%</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span>♻️ Plastic:</span>
                    <span style="font-weight: bold; color: #3498db;">{plastic_percentage:.1f}%</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span>🔩 Metal:</span>
                    <span style="font-weight: bold; color: #95a5a6;">{metal_percentage:.1f}%</span>
                </div>
            </div>
            
            <div style="
                background: rgba(255,255,255,0.1);
                padding: 8px;
                border-radius: 8px;
                margin: 8px 0;
                text-align: center;
            ">
                <div style="font-weight: bold; color: #e67e22; font-size: 12px;">
                    📍 Location: {spot['latitude']:.4f}, {spot['longitude']:.4f}
                </div>
            </div>
        </div>
        """
        folium.Marker(
            [spot['latitude'], spot['longitude']],
            popup=folium.Popup(popup_content, max_width=320),
            icon=folium.Icon(color='black', icon='trash', prefix='fa') # Black color, trash icon
        ).add_to(m)
        
        # Add enhanced dumping spot ID label above the marker
        folium.Marker(
            [spot['latitude'], spot['longitude']],
            icon=folium.DivIcon(
                html=f'<div style="font-size:8px;font-weight:bold;color:white;background:rgba(44,62,80,0.95);border:2px solid white;border-radius:4px;padding:1px 3px;text-align:center;display:flex;align-items:center;justify-content:center;white-space:nowrap;box-shadow:0 3px 6px rgba(0,0,0,0.4);transform:translate(-50%,-100%);letter-spacing:0.2px;">{spot["spot_id"]}</div>',
                icon_size=(28, 10),
                icon_anchor=(14, 20)
            )
        ).add_to(m)

    
    # Add path if provided
    if path:
        folium.PolyLine(
            path,
            color='blue',
            weight=2,
            opacity=0.8
        ).add_to(m)
    
    # Add special star marker for highlighted/searched item
    if highlight_item and highlight_type:
        if highlight_type == "Bin":
            highlight_coords = [highlight_item['latitude'], highlight_item['longitude']]
            highlight_id = highlight_item['bin_id']
        elif highlight_type == "Truck":
            highlight_coords = [highlight_item['current_latitude'], highlight_item['current_longitude']]
            highlight_id = highlight_item['truck_id']
        else:  # Dumping Spot
            highlight_coords = [highlight_item['latitude'], highlight_item['longitude']]
            highlight_id = highlight_item['spot_id']
        
                # Use existing bin data for popup but with star marker
        if highlight_type == "Bin":
            # Get the existing bin data for popup
            bin_data = next((b for b in bins if b['bin_id'] == highlight_id), None)
            if bin_data:
                # Use the existing bin popup content but mark it as searched
                star_popup_content = f"""
                <div style="
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
                    color: white;
                    padding: 15px;
                    border-radius: 12px;
                    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                    min-width: 280px;
                    border: 3px solid #f1c40f;
                ">
                    <div style="
                        text-align: center;
                        margin-bottom: 12px;
                        padding-bottom: 8px;
                        border-bottom: 2px solid rgba(255,255,255,0.3);
                    ">
                        <h3 style="
                            margin: 0;
                            font-size: 18px;
                            font-weight: bold;
                            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
                            color: #fff;
                        ">🗑️ Waste Bin - {bin_data['bin_id']}</h3>
                        <div style="
                            background: #f1c40f;
                            color: #2c3e50;
                            padding: 4px 8px;
                            border-radius: 15px;
                            font-weight: bold;
                            font-size: 12px;
                            margin-top: 8px;
                        ">⭐ SEARCHED ITEM</div>
                    </div>
                    
                    <div style="margin-bottom: 8px;">
                        <span style="
                            display: inline-block;
                            background: rgba(255,255,255,0.2);
                            padding: 4px 8px;
                            border-radius: 20px;
                            font-weight: bold;
                            font-size: 11px;
                            margin-right: 8px;
                            min-width: 60px;
                            text-align: center;
                        ">FILL LEVEL</span>
                        <span style="font-weight: bold; font-size: 14px;">{bin_data['fill_level']:.1f}%</span>
                    </div>
                    
                    <div style="
                        background: rgba(255,255,255,0.1);
                        padding: 10px;
                        border-radius: 8px;
                        margin: 8px 0;
                    ">
                        <div style="font-weight: bold; margin-bottom: 6px; color: #f1c40f;">📍 Location & Details</div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                            <span>🌍 Coordinates:</span>
                            <span style="font-weight: bold; color: #ecf0f1; font-size: 10px;">
                                {bin_data['latitude']:.4f}, {bin_data['longitude']:.4f}
                            </span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                            <span>♻️ Organic:</span>
                            <span style="font-weight: bold; color: #e67e22;">{bin_data['organic_percentage']:.1f}%</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                            <span>🥤 Plastic:</span>
                            <span style="font-weight: bold; color: #3498db;">{bin_data['plastic_percentage']:.1f}%</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>🔩 Metal:</span>
                            <span style="font-weight: bold; color: #95a5a6;">{bin_data['metal_percentage']:.1f}%</span>
                        </div>
                    </div>
                    
                    <div style="
                        font-size: 10px;
                        color: rgba(255,255,255,0.7);
                        text-align: center;
                        margin-top: 8px;
                        padding-top: 8px;
                        border-top: 1px solid rgba(255,255,255,0.2);
                    ">
                        Last updated: {bin_data.get('last_updated', 'Unknown')}
                    </div>
                </div>
                """
            else:
                # Fallback if bin data not found
                star_popup_content = f"⭐ {highlight_type}: {highlight_id} (SEARCHED)"
        else:
            # For trucks and dumping spots, use simple popup
            star_popup_content = f"⭐ {highlight_type}: {highlight_id} (SEARCHED)"
        
        # Add the star marker with custom icon
        folium.Marker(
            highlight_coords,
            popup=folium.Popup(star_popup_content, max_width=320),
            icon=folium.Icon(color='red', icon='star', prefix='fa'),
            tooltip=f"⭐ {highlight_type}: {highlight_id} (SEARCHED)"
        ).add_to(m)
        
        # Add a pulsing circle around the star marker for extra visibility
        folium.Circle(
            highlight_coords,
            radius=100,  # 100 meters radius for better visibility
            color='#f39c12',
            fill=True,
            fill_color='#f39c12',
            fill_opacity=0.2,
            weight=4,
            opacity=0.9
        ).add_to(m)
    
    # Auto-fit map to show all markers
    if bins or dumping_spots or trucks:
        # Collect all coordinates
        all_coords = []
        for bin in bins:
            all_coords.append([bin['latitude'], bin['longitude']])
        for spot in dumping_spots:
            all_coords.append([spot['latitude'], spot['longitude']])
        for truck in trucks:
            all_coords.append([truck['current_latitude'], truck['current_longitude']])
        
        if all_coords:
            # Fit map to show all markers with some padding
            m.fit_bounds(all_coords, padding=[0.1, 0.1])
    
    return m

def camera_gallery_section():
    """Camera Gallery Section"""
    st.header("📸 Camera Gallery")
    st.markdown("View all captured images from ESP32-CAM and other cameras")
    
    # Add custom CSS for the 4x4 gallery grid
    st.markdown("""
    <style>
    /* Enhanced 4x4 Gallery Grid Styling */
    .gallery-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
        padding: 16px 0;
    }
    
    .gallery-card {
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 12px;
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        overflow: hidden;
    }
    
    .gallery-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0,0,0,0.15);
        border-color: #3498db;
    }
    
    .gallery-image {
        width: 100%;
        height: 150px;
        object-fit: cover;
        border-radius: 8px;
        margin-bottom: 8px;
    }
    
    .gallery-info {
        font-size: 12px;
        line-height: 1.4;
        color: #2c3e50;
    }
    
    .gallery-buttons {
        display: flex;
        gap: 8px;
        margin-top: 8px;
    }
    
    .gallery-button {
        flex: 1;
        padding: 4px 8px;
        border: none;
        border-radius: 6px;
        background: #3498db;
        color: white;
        font-size: 12px;
        cursor: pointer;
        transition: background 0.2s ease;
    }
    
    .gallery-button:hover {
        background: #2980b9;
    }
    
    /* Responsive design for smaller screens */
    @media (max-width: 1200px) {
        .gallery-grid {
            grid-template-columns: repeat(3, 1fr);
        }
    }
    
    @media (max-width: 768px) {
        .gallery-grid {
            grid-template-columns: repeat(2, 1fr);
        }
    }
    
    @media (max-width: 480px) {
        .gallery-grid {
            grid-template-columns: 1fr;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Fetch camera images from API
    try:
        response = requests.get(f"{API_BASE_URL}/camera-images/")
        if response.status_code == 200:
            images_data = response.json()
            images = images_data.get('results', [])
            
            if not images:
                st.info("📷 No images captured yet. ESP32-CAM will start sending images automatically.")
                return
            
            # Gallery controls
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                # Filter by camera
                camera_response = requests.get(f"{API_BASE_URL}/cameras/")
                cameras = []
                if camera_response.status_code == 200:
                    cameras_data = camera_response.json()
                    cameras = cameras_data.get('results', [])
                
                camera_filter = st.selectbox(
                    "📷 Filter by Camera:",
                    ["All Cameras"] + [cam['name'] for cam in cameras]
                )
            
            with col2:
                # Filter by analysis type
                analysis_types = ["All Types", "WASTE_CLASSIFICATION", "SECURITY", "COLLECTION", "GENERAL"]
                analysis_filter = st.selectbox("🔍 Filter by Type:", analysis_types)
            
            with col3:
                # Sort options
                sort_by = st.selectbox("📊 Sort by:", ["Newest", "Oldest", "File Size", "Camera"])
            
            # Apply filters
            filtered_images = images
            if camera_filter != "All Cameras":
                filtered_images = [img for img in images if img.get('camera_name') == camera_filter]
            
            if analysis_filter != "All Types":
                filtered_images = [img for img in filtered_images if img.get('analysis_type') == analysis_filter]
            
            # Apply sorting
            if sort_by == "Oldest":
                filtered_images.sort(key=lambda x: x.get('created_at', ''))
            elif sort_by == "File Size":
                filtered_images.sort(key=lambda x: x.get('file_size_mb', 0), reverse=True)
            elif sort_by == "Camera":
                filtered_images.sort(key=lambda x: x.get('camera_name', ''))
            else:  # Newest (default)
                filtered_images.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            # Display image count
            st.success(f"📊 Found {len(filtered_images)} images")
            
            # Gallery grid - 4x4 layout
            st.markdown("### 📸 Image Gallery (4x4 Grid)")
            
            # Create 4 columns for the grid
            cols = st.columns(4)
            
            for idx, image in enumerate(filtered_images):
                col_idx = idx % 4
                
                with cols[col_idx]:
                    # Image card with enhanced styling
                    with st.container():
                        # Create a card-like container
                        st.markdown("""
                        <div style="
                            border: 1px solid #e0e0e0;
                            border-radius: 12px;
                            padding: 12px;
                            margin-bottom: 16px;
                            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
                            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                            transition: transform 0.2s ease;
                        ">
                        """, unsafe_allow_html=True)
                        
                        # Image thumbnail with hover effect
                        try:
                            if image.get('thumbnail_url'):
                                # Convert relative URL to full URL
                                thumbnail_url = f"{API_BASE_URL.replace('/api', '')}{image['thumbnail_url']}"
                                st.image(
                                    thumbnail_url, 
                                    use_container_width=True,
                                    caption=f"📷 {image.get('camera_name', 'Unknown Camera')}"
                                )
                            elif image.get('image_url'):
                                # Convert relative URL to full URL
                                image_url = f"{API_BASE_URL.replace('/api', '')}{image['image_url']}"
                                st.image(
                                    image_url, 
                                    use_container_width=True,
                                    caption=f"📷 {image.get('camera_name', 'Unknown Camera')}"
                                )
                            else:
                                st.error("❌ Image not available")
                        except Exception as e:
                            # Fallback to main image if thumbnail fails
                            if image.get('image_url'):
                                image_url = f"{API_BASE_URL.replace('/api', '')}{image['image_url']}"
                                st.image(
                                    image_url, 
                                    use_container_width=True,
                                    caption=f"📷 {image.get('camera_name', 'Unknown Camera')} (Full Image)"
                                )
                            else:
                                st.error("❌ Image not available")
                        
                        # Compact image info
                        st.markdown(f"**📅 {image.get('created_at', 'Unknown Date')[:10]}**")
                        st.markdown(f"**🔍 {image.get('analysis_type', 'Unknown Type')}**")
                        
                        # File details in compact format
                        if image.get('file_size_mb') and image.get('dimensions'):
                            st.markdown(f"**💾 {image.get('file_size_mb')} MB | 📐 {image.get('dimensions')}**")
                        
                        # Analysis results
                        if image.get('is_analyzed') and image.get('confidence_score'):
                            confidence = image.get('confidence_score', 0)
                            confidence_color = "🟢" if confidence > 0.8 else "🟡" if confidence > 0.5 else "🔴"
                            st.markdown(f"**🎯 {confidence_color} {confidence:.2f}**")
                        
                        # Action buttons in compact layout
                        button_col1, button_col2 = st.columns(2)
                        
                        with button_col1:
                            # View full image button
                            if image.get('image_url'):
                                if st.button("🔍", key=f"view_{image['id']}", help="View full image"):
                                    full_image_url = f"{API_BASE_URL.replace('/api', '')}{image['image_url']}"
                                    st.image(full_image_url, use_container_width=True)
                                    st.success("✅ Full image displayed above")
                        
                        with button_col2:
                            # Download button
                            if image.get('image_url'):
                                full_image_url = f"{API_BASE_URL.replace('/api', '')}{image['image_url']}"
                                st.download_button(
                                    "⬇️",
                                    data=requests.get(full_image_url).content,
                                    file_name=f"camera_image_{image['id']}.jpg",
                                    mime="image/jpeg",
                                    key=f"download_{image['id']}",
                                    help="Download image"
                                )
                        
                        st.markdown("</div>", unsafe_allow_html=True)
            
            # Pagination info
            if len(images) > len(filtered_images):
                st.info(f"📄 Showing {len(filtered_images)} of {len(images)} total images")
                
        else:
            st.error(f"❌ Failed to fetch images: {response.status_code}")
            
    except Exception as e:
        st.error(f"❌ Error loading camera gallery: {str(e)}")
        st.info("💡 Make sure the Django backend is running and accessible")

def main():
    # Navigation system with enhanced styling and descriptions
    st.sidebar.markdown("""
        <div class="nav-panel nav-panel--simple">
            <div class="nav-panel__header">
                <span class="nav-panel__icon">🧭</span>
                <div>
                    <h3>Navigation</h3>
                    <p>Pick a workspace to view.</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    nav_options = {
        "🗺️ Interactive Map": "Live situational awareness for bins, trucks, and dumping spots.",
        "📊 Analytics Dashboard": "Key performance indicators and strategic trends.",
        "🚛 Truck Management": "Fleet health, assignments, and live telemetry.",
        "🗑️ Bin Management": "Capacity, classifications, and service priorities.",
        "📈 Real-time Data": "Streaming metrics and on-the-minute updates.",
        "📸 Camera Gallery": "ESP32-CAM intelligence and visual inspections."
    }

    selected = st.sidebar.radio(
        "Choose a section:",
        options=list(nav_options.keys()),
        key="navigation_selection"
    )

    if not selected:
        selected = list(nav_options.keys())[0]

    st.sidebar.markdown(
        f"""
        <div class="nav-helper-inline">
            <span>{nav_options[selected]}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    if "live_refresh_enabled" not in st.session_state:
        st.session_state["live_refresh_enabled"] = True

    st.sidebar.markdown('<div class="live-refresh-card">', unsafe_allow_html=True)
    live_refresh_enabled = st.sidebar.checkbox(
        "⚡ Live map refresh (0.5s)",
        value=st.session_state["live_refresh_enabled"],
        key="live_refresh_enabled",
        help="Toggle off if you need to pause automatic reruns while interacting."
    )

    if live_refresh_enabled:
        st.sidebar.caption("Live updates every 0.5s. Toggle off to freeze the screen temporarily.")
        st_autorefresh(interval=LIVE_REFRESH_INTERVAL_MS, key="live_bin_data_refresh")
    else:
        st.sidebar.caption("Live refresh paused. Reactivate when you're done interacting.")
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

    # Add custom CSS for container margins and map enhancements
    st.markdown("""
    <style>
    /* Main title styling - big and clear */
    h1 {
        font-size: 2.8em !important;
        font-weight: bold !important;
        margin-top: 0 !important;
        margin-bottom: 0 !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        color: #1f77b4 !important;
    }
    
    /* Target the specific Streamlit container */
    .st-emotion-cache-lxqt60.e1cbzgzq10,
    .st-emotion-cache-lxqt60 {
        margin-left: 0 !important;
        margin-right: 0 !important;
    }
    
    /* General container margin adjustment */
    .main .block-container {
        margin-left: 0 !important;
        margin-right: 0 !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Map container enhancements */
    .folium-container {
        border-radius: 12px !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1) !important;
        overflow: hidden !important;
    }
    
    /* Smooth transitions for map elements */
    .leaflet-marker-icon,
    .leaflet-popup-content {
        transition: all 0.3s ease-in-out !important;
    }
    
    /* Enhanced map controls */
    .leaflet-control-zoom a {
        background: rgba(255,255,255,0.9) !important;
        border: 2px solid #3498db !important;
        color: #2c3e50 !important;
        font-weight: bold !important;
        transition: all 0.2s ease !important;
    }
    
    .leaflet-control-zoom a:hover {
        background: #3498db !important;
        color: white !important;
        transform: scale(1.1) !important;
    }
    
    /* Star marker animations */
    .fa-star {
        animation: starPulse 2s ease-in-out infinite !important;
    }
    
    @keyframes starPulse {
        0% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.2); opacity: 0.8; }
        100% { transform: scale(1); opacity: 1; }
    }
    
    /* Highlighted item popup styling */
    .leaflet-popup-content-wrapper {
        border-radius: 12px !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4) !important;
    }
    
    /* Reduce spacing in columns and input fields */
    div[data-testid="column"] {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Make buttons and inputs more compact */
    .stButton > button {
        height: 38px !important;
        padding: 0.25rem 0.5rem !important;
        font-size: 0.9em !important;
    }
    
    /* Reduce input field spacing */
    .stSelectbox, .stTextInput {
        margin-top: 0 !important;
        margin-bottom: 0 !important;
        padding: 0 !important;
    }
    
    /* Compact selectbox and text input */
    div[data-baseweb="select"] > div, 
    div[data-baseweb="input"] > div {
        padding: 0.25rem !important;
    }
    
    /* Remove spacing between search buttons and map */
    .element-container:has(.stButton) {
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
    }
    
    /* Make map container appear right after buttons */
    .stContainer + .element-container,
    .stContainer + .element-container .map-container {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* Remove gaps in vertical blocks */
    div[data-testid="stVerticalBlock"] {
        gap: 0 !important;
    }
    
    /* Compact spacing for all containers before map */
    .main .block-container > div > div:has(.stButton) {
        margin-bottom: 0 !important;
    }
    </style>
    
    <script>
    // Enhanced map functionality with smooth zoom transitions
    document.addEventListener('DOMContentLoaded', function() {
        // Wait for map to load
        setTimeout(function() {
            const mapContainer = document.querySelector('.folium-container');
            if (mapContainer) {
                // Add smooth zoom transition class
                mapContainer.style.transition = 'all 0.5s ease-in-out';
                
                // Ensure map is properly centered and zoomed
                const map = mapContainer.querySelector('.leaflet-container');
                if (map) {
                    map.style.opacity = '0';
                    map.style.transform = 'scale(0.95)';
                    
                    // Smooth entrance animation
                    setTimeout(function() {
                        map.style.opacity = '1';
                        map.style.transform = 'scale(1)';
                    }, 100);
                }
            }
        }, 500);
    });
    </script>
    """, unsafe_allow_html=True)
    
    # Remove single truck location input
    # Get bins data
    bins = get_bins()
    # Get dumping spot data
    dumping_spots = get_dumping_spots()
    # Get trucks data
    trucks = get_trucks()
    
    # Display last update timestamp and data freshness indicator
    current_time = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Check if we have recent data (within last 5 minutes)
    if bins and len(bins) > 0:
        latest_bin_time = max(bins, key=lambda x: x.get('last_updated', '1970-01-01')).get('last_updated', '1970-01-01')
        if latest_bin_time != '1970-01-01':
            try:
                from datetime import datetime as dt_local
                latest_time = dt_local.fromisoformat(latest_bin_time.replace('Z', '+00:00'))
                time_diff = (dt_local.now().astimezone() - latest_time.astimezone()).total_seconds() / 60
                
                if time_diff < 5:
                    freshness_icon = "🟢"
                    freshness_text = "Fresh"
                elif time_diff < 15:
                    freshness_icon = "🟡"
                    freshness_text = "Recent"
                else:
                    freshness_icon = "🔴"
                    freshness_text = "Stale"
                
                st.markdown(f'<div style="font-size: 0.75em; color: #666; margin: 2px 0; padding: 2px 0;">{freshness_icon} Data freshness: {freshness_text} | 📅 Last updated: {current_time} | 🕒 API data: {time_diff:.1f} min ago</div>', unsafe_allow_html=True)
            except:
                st.markdown(f'<div style="font-size: 0.75em; color: #666; margin: 2px 0; padding: 2px 0;">📅 Last updated: {current_time}</div>', unsafe_allow_html=True)
        else:
            st.caption(f"📅 Last updated: {current_time}")
    else:
        st.caption(f"📅 Last updated: {current_time}")
    
    # Navigation routing
    if selected == "📸 Camera Gallery":
        camera_gallery_section()
        return
    elif selected == "📊 Analytics Dashboard":
        st.header("📊 Analytics Dashboard")
        st.info("Analytics dashboard coming soon...")
        return
    elif selected == "🚛 Truck Management":
        st.header("🚛 Truck Management")
        st.info("Truck management coming soon...")
        return
    elif selected == "🗑️ Bin Management":
        st.header("🗑️ Bin Management")
        st.info("Bin management coming soon...")
        return
    elif selected == "📈 Real-time Data":
        st.header("📈 Real-time Data")
        st.info("Real-time data monitoring coming soon...")
        return
    
    # Default: Interactive Map
    st.header("🗺️ Interactive Map")
    
    # Search and highlight item on the map
    st.subheader("🔍 Search Item by ID on Map")
    st.caption("Enter an ID below to highlight it with a ⭐ marker. Data refreshes with every lookup.")
    
    # Show search history if available
    if 'search_history' not in st.session_state:
        st.session_state['search_history'] = []
    
    if st.session_state['search_history']:
        st.info(f"💡 **Recent searches**: {', '.join(st.session_state['search_history'][-3:])}")
    
    # Placeholder for search results
    search_results_placeholder = st.empty()
    
    # Create columns for search input and button - all in one line
    with st.container():
        st.markdown('<div class="search-control-row">', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns([1.5, 2, 1, 1], gap="small")
    
        with col1:
            map_search_type = st.selectbox("Select item type", ["Bin", "Truck", "Dumping Spot"], key="map_search_type")
        with col2:
            map_search_id = st.text_input("Enter ID", "", key="map_search_id", placeholder="BIN001, TRUCK01")
        with col3:
            search_button = st.button("🔍 Search", type="primary", use_container_width=True)
        with col4:
            refresh_button = st.button("🔄 Refresh", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    highlight_item = None
    
    # Handle refresh all button
    if refresh_button:
        st.info("🔄 Refreshing all data from API...")
        bins = get_bins()
        trucks = get_trucks()
        dumping_spots = get_dumping_spots()
        st.success("✅ All data refreshed!")
        # Clear search state when refreshing all
        if 'last_search_id' in st.session_state:
            del st.session_state['last_search_id']
    
    if map_search_id and (search_button or st.session_state.get('last_search_id') != map_search_id):
        if map_search_type == "Bin":
            # Fetch fresh bin data specifically for this search
            fresh_bins = get_bins()
            highlight_item = next((b for b in fresh_bins if b['bin_id'] == map_search_id), None)
            # Update the main bins data with fresh data
            bins = fresh_bins
        elif map_search_type == "Truck":
            # Fetch fresh truck data specifically for this search
            fresh_trucks = get_trucks()
            highlight_item = next((t for t in fresh_trucks if t['truck_id'] == map_search_id), None)
            # Update the main trucks data with fresh data
            trucks = fresh_trucks
        else:
            # Fetch fresh dumping spot data specifically for this search
            fresh_dumping_spots = get_dumping_spots()
            highlight_item = next((d for d in fresh_dumping_spots if d['spot_id'] == map_search_id), None)
            # Update the main dumping spots data with fresh data
            dumping_spots = fresh_dumping_spots
        
        # Store the last searched ID to track changes
        st.session_state['last_search_id'] = map_search_id
        
        # Add to search history
        search_entry = f"{map_search_type}:{map_search_id}"
        if search_entry not in st.session_state['search_history']:
            st.session_state['search_history'].append(search_entry)
            # Keep only last 10 searches
            if len(st.session_state['search_history']) > 10:
                st.session_state['search_history'] = st.session_state['search_history'][-10:]
        
        if not highlight_item:
            search_results_placeholder.warning(f"No {map_search_type.lower()} found with ID '{map_search_id}'")
        else:
            item_id = highlight_item.get('bin_id') or highlight_item.get('truck_id') or highlight_item.get('spot_id') or 'Unknown'
            if map_search_type == "Bin":
                last_updated = highlight_item.get('last_updated', 'Unknown')
                fill_level = highlight_item.get('fill_level', 0)
                st.session_state['floating_card_data'] = {
                    "title": f"✅ Bin Found: {map_search_id}",
                    "lines": [
                        {"label": "📊 Fill Level", "value": f"{fill_level:.1f}%"},
                        {"label": "🕒 Last Updated", "value": last_updated},
                        {"label": "🎯 Map Highlight", "value": "Pinned with a ⭐ marker"}
                    ],
                    "key": f"{map_search_type}_{map_search_id}"
                }
            elif map_search_type == "Truck":
                last_updated = highlight_item.get('last_updated', 'Unknown')
                status = highlight_item.get('status', 'Unknown')
                fuel_level = highlight_item.get('fuel_level', 0)
                st.session_state['floating_card_data'] = {
                    "title": f"✅ Truck Found: {map_search_id}",
                    "lines": [
                        {"label": "🚛 Status", "value": status},
                        {"label": "⛽ Fuel", "value": f"{fuel_level:.1f}%"},
                        {"label": "🕒 Last Updated", "value": last_updated},
                        {"label": "🎯 Map Highlight", "value": "Pinned with a ⭐ marker"}
                    ],
                    "key": f"{map_search_type}_{map_search_id}"
                }
            else:
                last_updated = highlight_item.get('last_updated', 'Unknown')
                st.session_state['floating_card_data'] = {
                    "title": f"✅ {map_search_type} Found: {map_search_id}",
                    "lines": [
                        {"label": "🕒 Last Updated", "value": last_updated},
                        {"label": "🎯 Map Highlight", "value": "Pinned with a ⭐ marker"}
                    ],
                    "key": f"{map_search_type}_{map_search_id}"
                }
    # Floating detail card
    floating_card = st.session_state.get('floating_card_data')
    if floating_card:
        st.markdown("""
            <style>
            .floating-card {
                position: fixed;
                bottom: 32px;
                right: 32px;
                width: min(420px, 90vw);
                background: linear-gradient(160deg, #0f172a 0%, #1e3a8a 100%);
                border-radius: 20px;
                padding: 22px 24px 16px;
                box-shadow: 0 25px 60px rgba(8, 25, 78, 0.45);
                border: 1px solid rgba(59, 130, 246, 0.4);
                z-index: 9999;
            }
            .floating-card h5 {
                margin: 0 0 16px;
                font-size: 1.1rem;
                color: #f8fafc;
                display: flex;
                align-items: center;
                gap: 0.6rem;
            }
            .floating-card .card-line {
                display: flex;
                justify-content: space-between;
                font-size: 0.92rem;
                margin-bottom: 10px;
                background: rgba(15, 23, 42, 0.6);
                padding: 12px 14px;
                border-radius: 14px;
                border: 1px solid rgba(99, 102, 241, 0.35);
                color: #e2e8f0;
            }
            .floating-card .card-line span:first-child {
                font-weight: 600;
                color: #93c5fd;
            }
            .floating-card .stButton button {
                width: 100%;
                border-radius: 999px;
                font-weight: 600;
                background: #38bdf8;
                color: #0f172a;
                border: none;
                margin-top: 6px;
            }
            </style>
        """, unsafe_allow_html=True)

        toast_container = st.empty()
        with toast_container.form(key=f"floating_card_{floating_card['key']}"):
            st.markdown("<div class='floating-card'>", unsafe_allow_html=True)
            st.markdown(f"<h5>{floating_card['title']}</h5>", unsafe_allow_html=True)
            for line in floating_card["lines"]:
                st.markdown(f"<div class='card-line'><span>{line['label']}</span><span>{line['value']}</span></div>", unsafe_allow_html=True)
            submitted = st.form_submit_button("OK")
            st.markdown("</div>", unsafe_allow_html=True)
            if submitted:
                st.session_state['floating_card_data'] = None
                st.session_state['clear_highlight'] = True
                st.rerun()

    # Create main map, centering/highlighting if search is active
    if highlight_item:
        if map_search_type == "Bin":
            center = [highlight_item['latitude'], highlight_item['longitude']]
            main_map = create_map(bins, dumping_spots, trucks, selected_bin=highlight_item, highlight_item=highlight_item, highlight_type=map_search_type)
        elif map_search_type == "Truck":
            center = [highlight_item['current_latitude'], highlight_item['current_longitude']]
            main_map = create_map(bins, dumping_spots, trucks, selected_bin=None, path=None, highlight_item=highlight_item, highlight_type=map_search_type)
        else:
            center = [highlight_item['latitude'], highlight_item['longitude']]
            main_map = create_map(bins, dumping_spots, trucks, selected_bin=None, path=None, highlight_item=highlight_item, highlight_type=map_search_type)
        
        # Enhanced zoom and centering for searched item
        # Force the map to center and zoom to the highlighted item
        main_map.location = center
        main_map.zoom_start = 11  # More zoomed out for better visibility and context
        
        # Force map to center on the searched item with proper bounds
        if highlight_item:
            # Create a small bounds around the searched item to ensure it's centered
            lat, lon = center
            bounds = [[lat - 0.01, lon - 0.01], [lat + 0.01, lon + 0.01]]
            main_map.fit_bounds(bounds, padding=[0.1, 0.1])
        
        # Ensure the map properly centers on the searched item
        if hasattr(main_map, '_name'):
            item_id = highlight_item.get('bin_id') or highlight_item.get('truck_id') or highlight_item.get('spot_id') or 'item'
            main_map._name = f"map_centered_on_{item_id}"
        
    else:
        main_map = create_map(bins, dumping_spots, trucks)
    
    # Display map in a full-width container
    with st.container():
        st.markdown('<div class="map-container">', unsafe_allow_html=True)
        folium_static(main_map, width=1200, height=800)
        st.markdown('</div>', unsafe_allow_html=True)



    # Calculate and display statistics
    st.header("Bin Statistics")
    if bins:
        # Separate technical support bins (abnormal fill levels)
        tech_support_bins = [b for b in bins if b.get('fill_level', 50) < 0 or b.get('fill_level', 50) > 100]
        tech_support_statistic_count = len(tech_support_bins)
        tech_support_bin_ids = {b['bin_id'] for b in tech_support_bins}
        # All other bins
        other_bins = [b for b in bins if b['bin_id'] not in tech_support_bin_ids]
        # Categorize the remaining bins by fill level
        full_bins = sum(1 for b in other_bins if 0 <= b.get('fill_level', 50) <= 100 and b['fill_level'] == 100)
        almost_full_bins = sum(1 for b in other_bins if 0 <= b.get('fill_level', 50) <= 100 and b['fill_level'] >= 80 and b['fill_level'] < 100)
        half_full_bins = sum(1 for b in other_bins if 0 <= b.get('fill_level', 50) <= 100 and b['fill_level'] >= 50 and b['fill_level'] < 80)
        low_fill_bins = sum(1 for b in other_bins if 0 <= b.get('fill_level', 50) <= 100 and b['fill_level'] < 50)
        # Create a DataFrame for statistics with redefined categories
        stats_data = {
            'Category': [
                'Total Bins',
                'Technical Support Needed',
                '100% Full Bins',
                '80-99% Full Bins',
                '50-79% Full Bins',
                'Below 50% Full Bins'
            ],
            'Count': [
                len(bins),
                tech_support_statistic_count,
                full_bins,
                almost_full_bins,
                half_full_bins,
                low_fill_bins
            ]
        }
        stats_df = pd.DataFrame(stats_data)

        # Define colors for categories (matching map markers/pie chart)
        category_colors = {
            'Technical Support Needed': 'rgba(128, 128, 128, 0.5)', # Gray
            '100% Full Bins': 'rgba(255, 0, 0, 0.5)',       # Red
            '80-99% Full Bins': 'rgba(255, 165, 0, 0.5)',    # Orange
            '50-79% Full Bins': 'rgba(255, 255, 0, 0.5)',    # Yellow
            'Below 50% Full Bins': 'rgba(0, 128, 0, 0.5)'     # Green
            # No specific color for Total Bins in this scheme
        }

        # Function to apply colors
        def color_cells(row):
            styles = [''] * len(row)
            if row['Category'] in category_colors:
                bg_color = category_colors[row['Category']]
                styles[0] = f'background-color: {bg_color}'
                styles[1] = f'background-color: {bg_color}'
            return styles

        # Apply styling to the DataFrame
        styled_stats_df = stats_df.style.apply(color_cells, axis=1)

        # Display the styled DataFrame
        st.dataframe(styled_stats_df, hide_index=True, use_container_width=True)

    else:
        st.write("No bin data available.")

    # Create charts if data exists
    if bins:
        df = pd.DataFrame(bins)

        # Pie Chart for Fill Level Distribution
        st.header("Fill Level Distribution")
        # Use the same logic as the statistics table
        tech_support_bins = [b for b in bins if b.get('fill_level', 50) < 0 or b.get('fill_level', 50) > 100]
        tech_support_count = len(tech_support_bins)
        other_bins = [b for b in bins if b['bin_id'] not in {b['bin_id'] for b in tech_support_bins}]
        full_bins = sum(1 for b in other_bins if 0 <= b.get('fill_level', 50) <= 100 and b['fill_level'] == 100)
        almost_full_bins = sum(1 for b in other_bins if 0 <= b.get('fill_level', 50) <= 100 and b['fill_level'] >= 80 and b['fill_level'] < 100)
        half_full_bins = sum(1 for b in other_bins if 0 <= b.get('fill_level', 50) <= 100 and b['fill_level'] >= 50 and b['fill_level'] < 80)
        low_fill_bins = sum(1 for b in other_bins if 0 <= b.get('fill_level', 50) <= 100 and b['fill_level'] < 50)
        chart_data = [
            {"category": "Technical Support Needed", "count": tech_support_count},
            {"category": "100% Full Bins", "count": full_bins},
            {"category": "80-99% Full Bins", "count": almost_full_bins},
            {"category": "50-79% Full Bins", "count": half_full_bins},
            {"category": "Below 50% Full Bins", "count": low_fill_bins},
        ]
        chart_df = pd.DataFrame(chart_data)
        # Remove categories with zero count
        chart_df = chart_df[chart_df['count'] > 0]
        category_order = ['Technical Support Needed', '100% Full Bins', '80-99% Full Bins', '50-79% Full Bins', 'Below 50% Full Bins']
        category_colors = ['gray', 'red', 'orange', 'yellow', 'green']
        pie_chart = alt.Chart(chart_df).mark_arc(outerRadius=120).encode(
            theta=alt.Theta(field="count", type="quantitative"),
            color=alt.Color(field="category", type="nominal", sort=category_order, scale=alt.Scale(domain=category_order, range=category_colors)),
            order=alt.Order(field="category", sort="descending"),
            tooltip=['category', 'count', alt.Tooltip('count', title='Number of Bins')],
            text=alt.Text(field="count", type="quantitative")
        ).properties(
            title='Distribution of Bin Categories (Real Data)'
        )
        st.altair_chart(pie_chart, use_container_width=True)
        
        st.info("Note: The 'Technical Support Needed' count in this chart represents the bins with fill_level < 0 or > 100.")

        # Waste Composition Distribution
        st.header("Waste Composition Distribution")
        # Only use bins with valid fill levels (not technical support bins)
        valid_bins = [b for b in bins if 0 <= b.get('fill_level', 50) <= 100]
        if valid_bins:
            df_valid = pd.DataFrame(valid_bins)
            # Organic Waste Histogram
            st.info("This chart is based on the current, real bin data in the system.")
            # Summary statistics for organic percentage
            organic_mean = df_valid['organic_percentage'].mean()
            organic_median = df_valid['organic_percentage'].median()
            organic_min = df_valid['organic_percentage'].min()
            organic_max = df_valid['organic_percentage'].max()
            st.write(f"**Organic Percentage Stats:** Mean: {organic_mean:.2f}%, Median: {organic_median:.2f}%, Min: {organic_min:.2f}%, Max: {organic_max:.2f}%")
            organic_binned = df_valid.groupby(pd.cut(df_valid['organic_percentage'], bins=20, right=False)).size().reset_index(name='count')
            organic_binned['organic_percentage'] = organic_binned['organic_percentage'].apply(lambda x: x.mid).round(1)
            organic_binned = organic_binned[organic_binned['count'] > 0]
            organic_hist = alt.Chart(organic_binned).mark_bar().encode(
                alt.X('organic_percentage', title='Organic Waste Percentage', axis=alt.Axis(format='.1f')),
                alt.Y('count', title='Number of Bins'),
                tooltip=[alt.Tooltip('organic_percentage', format='.1f'), 'count']
            ).properties(
                title='Distribution of Organic Waste Percentage'
            )
            st.altair_chart(organic_hist, use_container_width=True)
            # Plastic Waste Histogram
            plastic_binned = df_valid.groupby(pd.cut(df_valid['plastic_percentage'], bins=20, right=False)).size().reset_index(name='count')
            plastic_binned['plastic_percentage'] = plastic_binned['plastic_percentage'].apply(lambda x: x.mid).round(1)
            plastic_binned = plastic_binned[plastic_binned['count'] > 0]
            plastic_hist = alt.Chart(plastic_binned).mark_bar().encode(
                alt.X('plastic_percentage', title='Plastic Waste Percentage', axis=alt.Axis(format='.1f')),
                alt.Y('count', title='Number of Bins'),
                tooltip=[alt.Tooltip('plastic_percentage', format='.1f'), 'count']
            ).properties(
                title='Distribution of Plastic Waste Percentage'
            )
            st.altair_chart(plastic_hist, use_container_width=True)
            # Metal Waste Histogram
            metal_binned = df_valid.groupby(pd.cut(df_valid['metal_percentage'], bins=20, right=False)).size().reset_index(name='count')
            metal_binned['metal_percentage'] = metal_binned['metal_percentage'].apply(lambda x: x.mid).round(1)
            metal_binned = metal_binned[metal_binned['count'] > 0]
            metal_hist = alt.Chart(metal_binned).mark_bar().encode(
                alt.X('metal_percentage', title='Metal Waste Percentage', axis=alt.Axis(format='.1f')),
                alt.Y('count', title='Number of Bins'),
                tooltip=[alt.Tooltip('metal_percentage', format='.1f'), 'count']
            ).properties(
                title='Distribution of Metal Waste Percentage'
            )
            st.altair_chart(metal_hist, use_container_width=True)
        else:
            st.info("No valid bins available for waste composition distribution.")

    # Display Dumping Spot Records
    st.header("Dumping Spot Records")
    if dumping_spots:
        # Calculate percentages and fill level for each dumping spot
        processed_spots = []
        for spot in dumping_spots:
            total_content = spot['organic_content'] + spot['plastic_content'] + spot['metal_content']
            fill_level = (total_content / spot['total_capacity']) * 100 if spot['total_capacity'] > 0 else 0
            
            organic_percentage = (spot['organic_content'] / total_content) * 100 if total_content > 0 else 0
            plastic_percentage = (spot['plastic_content'] / total_content) * 100 if total_content > 0 else 0
            metal_percentage = (spot['metal_content'] / total_content) * 100 if total_content > 0 else 0
            
            processed_spot = {
                'spot_id': spot['spot_id'],
                'latitude': spot['latitude'],
                'longitude': spot['longitude'],
                'total_capacity': spot['total_capacity'],
                'organic_percentage': organic_percentage,
                'plastic_percentage': plastic_percentage,
                'metal_percentage': metal_percentage,
                'current_fill_level': fill_level
            }
            processed_spots.append(processed_spot)
        
        df_dumping_spots = pd.DataFrame(processed_spots)
        # Select and reorder columns for display
        df_display = df_dumping_spots[[
            'spot_id', 
            'latitude', 
            'longitude', 
            'total_capacity', 
            'organic_percentage', 
            'plastic_percentage', 
            'metal_percentage',
            'current_fill_level'
        ]]
        # Rename columns for better display in the table
        df_display = df_display.rename(columns={
            'spot_id': 'ID',
            'latitude': 'Latitude',
            'longitude': 'Longitude',
            'total_capacity': 'Total Capacity',
            'organic_percentage': 'Organic %',
            'plastic_percentage': 'Plastic %',
            'metal_percentage': 'Metal %',
            'current_fill_level': 'Fill Level %'
        })

        st.dataframe(df_display.style.format({
            'Total Capacity': '{:.1f} tons',
            'Organic %': '{:.1f}%',
            'Plastic %': '{:.1f}%',
            'Metal %': '{:.1f}%',
            'Fill Level %': '{:.1f}%',
            'Latitude': '{:.4f}', 
            'Longitude': '{:.4f}' 
        }), hide_index=True, use_container_width=True)
    else:
        st.write("No dumping spot data available.")

    # Technical Support Bins Section
    st.header("Technical Support Needed (Real Data)")
    # Find real bins needing technical support
    now = dt.datetime.utcnow()
    tech_support_bins = []
    for b in bins:
        reason = None
        severity = None
        # Only flag the 5 seeded technical bins
        if b.get('fill_level') == -20:
            reason = "Negative fill"
            severity = "Critical"
        elif b.get('fill_level') == 150:
            reason = "Overfilled"
            severity = "Warning"
        elif b.get('fill_level') == -999:
            reason = "Sensor Error / Poor Data Format"
            severity = "Critical"
        elif b.get('fill_level') == 9999:
            reason = "Unreachable / 404"
            severity = "Critical"
        else:
            # Or, if the bin is the one with the old timestamp (simulate 'No Signal')
            try:
                last_updated = date_parser.parse(b.get('last_updated'))
                if (now - last_updated).total_seconds() > 3600 * 24:  # 1 day old
                    reason = "No Signal"
                    severity = "Warning"
            except Exception:
                pass
        if reason:
            b = b.copy()
            b['Reason'] = reason
            b['Severity'] = severity
            tech_support_bins.append(b)
    if tech_support_bins:
        st.warning(f"{len(tech_support_bins)} bins require technical support:")
        df_tech = pd.DataFrame(tech_support_bins)
        display_columns = ['bin_id', 'fill_level', 'last_updated', 'Reason', 'Severity']
        df_tech_display = df_tech[display_columns].rename(columns={
            'bin_id': 'Bin ID',
            'fill_level': 'Fill Level (%)',
            'last_updated': 'Last Updated'
        })
        def style_severity(val):
            if val == 'Critical':
                return 'background-color: #ff0000; color: white'
            elif val == 'Warning':
                return 'background-color: #ffd93d; color: black'
            return ''
        styled_df = df_tech_display.style.applymap(style_severity, subset=['Severity']).format({
            'Fill Level (%)': '{:.1f}'
        })
        st.dataframe(styled_df, hide_index=True, use_container_width=True)
        st.info("Please investigate these bins as soon as possible. Severity is color-coded for quick triage.")
    else:
        st.success("All bins are operating within normal parameters. No technical support needed!")

    # Sidebar: Select a truck and bins to show shortest path
    st.sidebar.markdown('<div class="route-card">', unsafe_allow_html=True)
    st.sidebar.subheader("Route through selected bins")
    truck_options = {f"{t['truck_id']} (Driver: {t['driver_name']})": t for t in trucks}
    truck_options_list = list(truck_options.keys())
    selected_truck_label = st.sidebar.selectbox(
        "Select truck to route with",
        truck_options_list,
        key="route_truck_select"
    )
    selected_truck = truck_options[selected_truck_label] if selected_truck_label else None

    bin_options = {f"{b['bin_id']} (Fill: {b['fill_level']:.1f}%)": b for b in bins}
    bin_options_list = list(bin_options.keys())
    selected_bin_labels = st.sidebar.multiselect(
        "Select bins to route through",
        bin_options_list
    )
    selected_bins = [bin_options[label] for label in selected_bin_labels]

    # Button to trigger routing
    calculate_route_button = st.sidebar.button("Calculate Route")
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

    # Create main map
    main_map = create_map(bins, dumping_spots, trucks, selected_bins)
    
    # Display map in a full-width container
    with st.container():
        st.markdown('<div class="map-container">', unsafe_allow_html=True)
        folium_static(main_map, width=1200, height=800)
        st.markdown('</div>', unsafe_allow_html=True)

    # Add Legend Table
    st.subheader("Map Legend")
    st.write("Bin and item colors/styles indicate status and fill level:")

    # Enhanced HTML legend with icons, color swatches, and creative descriptions
    legend_html = """
    <style>
    .legend-table { width: 100%; border-collapse: collapse; font-size: 1.05em; }
    .legend-table th, .legend-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    .legend-icon { font-size: 20px; vertical-align: middle; margin-right: 6px; }
    .legend-swatch { display: inline-block; width: 18px; height: 18px; border-radius: 50%; margin-right: 6px; border: 1px solid #888; vertical-align: middle; }
    </style>
    <table class='legend-table'>
      <tr><th>Item</th><th>Visual</th><th>Description</th></tr>
      <tr style='background-color: rgba(0,0,255,0.07);'>
        <td>Trash Truck</td>
        <td><span class='legend-icon' style='color: #0074D9;'>&#128666;</span></td>
        <td>Truck location (blue truck icon)</td>
      </tr>
      <tr style='background-color: rgba(255,0,0,0.07);'>
        <td>100% Full Bin</td>
        <td><span class='legend-swatch' style='background: red; animation: blink 1s infinite;'></span></td>
        <td>Completely full bin (blinking red)</td>
      </tr>
      <tr style='background-color: rgba(255,165,0,0.07);'>
        <td>80-99% Full Bin</td>
        <td><span class='legend-swatch' style='background: orange;'></span></td>
        <td>Almost full bin (orange)</td>
      </tr>
      <tr style='background-color: rgba(255,255,0,0.07);'>
        <td>50-79% Full Bin</td>
        <td><span class='legend-swatch' style='background: yellow;'></span></td>
        <td>Half to three-quarters full (yellow)</td>
      </tr>
      <tr style='background-color: rgba(0,128,0,0.07);'>
        <td>Below 50% Full Bin</td>
        <td><span class='legend-swatch' style='background: green;'></span></td>
        <td>Less than half full (green)</td>
      </tr>
      <tr style='background-color: rgba(240,240,240,0.5);'>
        <td style='font-weight:bold;'>Technical Support Bin</td>
        <td></td>
        <td>Needs attention: see below for reasons</td>
      </tr>
      <tr style='background-color: rgba(230,210,255,0.7);'>
        <td style='padding-left: 2em;'>Negative fill</td>
        <td><span class='legend-swatch' style='background: purple;'></span></td>
        <td>Sensor reported negative value (critical)</td>
      </tr>
      <tr style='background-color: rgba(255,200,200,0.7);'>
        <td style='padding-left: 2em;'>Overfilled</td>
        <td><span class='legend-swatch' style='background: darkred;'></span></td>
        <td>Fill level > 100% (warning/critical)</td>
      </tr>
      <tr style='background-color: rgba(255,210,240,0.7);'>
        <td style='padding-left: 2em;'>Sensor Error / Poor Data Format</td>
        <td><span class='legend-swatch' style='background: pink;'></span></td>
        <td>Impossible or corrupted data (critical)</td>
      </tr>
      <tr style='background-color: rgba(80,80,80,0.15);'>
        <td style='padding-left: 2em;'>Unreachable / 404</td>
        <td><span class='legend-swatch' style='background: black;'></span></td>
        <td>Bin not responding or not found (critical)</td>
      </tr>
      <tr style='background-color: rgba(210,140,70,0.2);'>
        <td style='padding-left: 2em;'>No Signal</td>
        <td><span class='legend-swatch' style='background: saddlebrown;'></span></td>
        <td>No update for 24+ hours (warning)</td>
      </tr>
      <tr style='background-color: rgba(0,0,0,0.07);'>
        <td>Dumping Spot</td>
        <td><span class='legend-icon' style='color: black;'>&#128465;</span></td>
        <td>Waste dumping location (black trash icon)</td>
      </tr>
    </table>
    <style>
    @keyframes blink {
      0% { opacity: 1; }
      50% { opacity: 0.3; }
      100% { opacity: 1; }
    }
    </style>
    """
    st.markdown(legend_html, unsafe_allow_html=True)

    # Routing logic triggered by button click
    if calculate_route_button and selected_truck and selected_bins:
        st.subheader("Calculated Route")
        # Start from the selected truck's location
        current_location = [selected_truck['current_latitude'], selected_truck['current_longitude']]
        bins_to_visit = selected_bins[:]
        path = [current_location]
        total_distance = 0
        # Calculate the route visiting all selected bins using Nearest Neighbor heuristic
        while bins_to_visit:
            nearest_bin = None
            min_distance = float('inf')
            for bin in bins_to_visit:
                dist = calculate_distance(current_location[0], current_location[1], bin['latitude'], bin['longitude'])
                if dist < min_distance:
                    min_distance = dist
                    nearest_bin = bin
            if nearest_bin:
                path.append([nearest_bin['latitude'], nearest_bin['longitude']])
                total_distance += min_distance
                current_location = [nearest_bin['latitude'], nearest_bin['longitude']]
                bins_to_visit.remove(nearest_bin)
        # After visiting all selected bins, find the nearest dumping spot
        nearest_dumping_spot = None
        min_distance_to_dumping_spot = float('inf')
        if dumping_spots:
            for spot in dumping_spots:
                dist = calculate_distance(current_location[0], current_location[1], spot['latitude'], spot['longitude'])
                if dist < min_distance_to_dumping_spot:
                    min_distance_to_dumping_spot = dist
                    nearest_dumping_spot = spot
            if nearest_dumping_spot:
                path.append([nearest_dumping_spot['latitude'], nearest_dumping_spot['longitude']])
                total_distance += min_distance_to_dumping_spot
                st.write(f"Ending at Dumping Spot: {nearest_dumping_spot['spot_id']}")
        st.write(f"Total Route Distance (including dumping spot): {total_distance:.2f} km")
        # Display map with the calculated path
        path_map = create_map(
            bins,
            dumping_spots,
            trucks,
            selected_bins,
            path,
            highlight_item=None,  # No highlight for route calculation
            highlight_type=None
        )
        
        # Display route map in a full-width container
        with st.container():
            st.markdown('<div class="map-container">', unsafe_allow_html=True)
            folium_static(path_map, width=1200, height=800)
            st.markdown('</div>', unsafe_allow_html=True)
    elif calculate_route_button and not selected_truck:
        st.warning("Please select a truck to calculate a route.")
    elif calculate_route_button and not selected_bins:
        st.warning("Please select at least one bin to calculate a route.")





if __name__ == "__main__":
    main() 