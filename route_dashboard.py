import streamlit as st
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
import os
import polyline
from streamlit_autorefresh import st_autorefresh

def get_google_maps_route(origin, destination, waypoints):
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return None, 0, 0, "Google Maps API Key not found in .env file."
    
    origin_str = f"{origin[0]},{origin[1]}"
    destination_str = f"{destination[0]},{destination[1]}"
    
    waypoints_str = ""
    if waypoints:
        waypoints_str = "optimize:true|" + "|".join([f"{wp[0]},{wp[1]}" for wp in waypoints])
        
    url = f"https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": origin_str,
        "destination": destination_str,
        "waypoints": waypoints_str,
        "key": api_key
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if data.get("status") != "OK":
        error_message = data.get("error_message", data.get("status"))
        return None, 0, 0, f"Google Maps API Error: {error_message}"
        
    route = data["routes"][0]
    
    total_distance_meters = sum([leg["distance"]["value"] for leg in route["legs"]])
    total_duration_seconds = sum([leg["duration"]["value"] for leg in route["legs"]])
        
    total_distance_km = total_distance_meters / 1000.0
    total_duration_mins = total_duration_seconds / 60.0
    
    encoded_polyline = route["overview_polyline"]["points"]
    decoded_path = polyline.decode(encoded_polyline)
    
    return decoded_path, total_distance_km, total_duration_mins, None

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
            
            <!-- Latest Image Display -->
            <div style="text-align: center; margin: 10px 0;">
                <img id="latest-image" src="{bin.get('latest_image_url', '')}" 
                     style="max-width: 100%; border-radius: 8px; border: 2px solid rgba(255,255,255,0.3); display: {'block' if bin.get('latest_image_url') else 'none'};" 
                     alt="Latest Bin Status" />
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
                " id="fill-level">{bin['fill_level']:.1f}%</span>
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
                📅 Updated: <span id="last-updated">{bin['last_updated'][:16].replace('T', ' ')}</span>
            </div>
            
            <button onclick="updateData()" style="
                width: 100%;
                margin-top: 12px;
                padding: 8px;
                background-color: #f1c40f;
                color: #2c3e50;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                cursor: pointer;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            ">🔄 Pull Latest Data</button>
            
            <script>
                function updateData() {{
                    const btn = document.querySelector('button');
                    btn.innerText = '🔄 Pulling...';
                    fetch('http://localhost:8000/api/bin-data/?bin_id=' + '{bin["bin_id"]}')
                    .then(r => r.json())
                    .then(data => {{
                        let b = (data.results && data.results.length > 0) ? data.results[0] : (data.length > 0 ? data[0] : data);
                        if (b && b.fill_level !== undefined) {{
                            document.getElementById('fill-level').innerText = parseFloat(b.fill_level).toFixed(1) + '%';
                            if (b.last_updated) {{
                                document.getElementById('last-updated').innerText = b.last_updated.substring(0,16).replace('T', ' ');
                            }}
                            if (b.latest_image_url) {{
                                let imgEl = document.getElementById('latest-image');
                                if (imgEl) {{
                                    imgEl.src = b.latest_image_url;
                                    imgEl.style.display = 'block';
                                }}
                            }}
                        }}
                        btn.innerText = '✅ Updated!';
                        setTimeout(() => btn.innerText = '🔄 Pull Latest Data', 2000);
                    }}).catch(e => {{
                        btn.innerText = '❌ Failed';
                        setTimeout(() => btn.innerText = '🔄 Pull Latest Data', 2000);
                    }});
                }}
            </script>
        </div>
        """
        
        iframe = folium.IFrame(html=popup_content, width=320, height=580)
        
        # Add marker to map
        folium.Marker(
            [bin['latitude'], bin['longitude']],
            popup=folium.Popup(iframe, max_width=320),
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
                    
                    <!-- Latest Camera Image -->
                    <div style="text-align: center; margin: 10px 0;">
                        <img id="star-image" src="{bin_data.get('latest_image_url', '')}" 
                             style="max-width: 100%; border-radius: 8px; border: 2px solid rgba(255,255,255,0.3); display: {'block' if bin_data.get('latest_image_url') else 'none'};" 
                             alt="Latest Bin Photo" />
                        {'<div style="font-size:10px; color:rgba(255,255,255,0.5); margin-top:4px;">📷 Latest capture</div>' if bin_data.get('latest_image_url') else ''}
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
                        <span id="star-fill" style="font-weight: bold; font-size: 14px;">{bin_data['fill_level']:.1f}%</span>
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
                        Last updated: <span id="star-updated">{bin_data.get('last_updated', 'Unknown')[:16].replace('T', ' ')}</span>
                    </div>
                    
                    <button onclick="updateStarData()" style="
                        width: 100%;
                        margin-top: 12px;
                        padding: 8px;
                        background-color: #f1c40f;
                        color: #2c3e50;
                        border: none;
                        border-radius: 6px;
                        font-weight: bold;
                        cursor: pointer;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                    ">🔄 Pull Latest Data</button>
                    
                    <script>
                        function updateStarData() {{
                            const btn = document.querySelector('button');
                            btn.innerText = '🔄 Pulling...';
                            fetch('http://localhost:8000/api/bin-data/?bin_id=' + '{bin_data["bin_id"]}')
                            .then(r => r.json())
                            .then(data => {{
                                let b = (data.results && data.results.length > 0) ? data.results[0] : (data.length > 0 ? data[0] : data);
                                if (b && b.fill_level !== undefined) {{
                                    document.getElementById('star-fill').innerText = parseFloat(b.fill_level).toFixed(1) + '%';
                                    if (b.last_updated) {{
                                        document.getElementById('star-updated').innerText = b.last_updated.substring(0,16).replace('T', ' ');
                                    }}
                                    if (b.latest_image_url) {{
                                        let imgEl = document.getElementById('star-image');
                                        if (imgEl) {{
                                            imgEl.src = b.latest_image_url;
                                            imgEl.style.display = 'block';
                                        }}
                                    }}
                                }}
                                btn.innerText = '✅ Updated!';
                                setTimeout(() => btn.innerText = '🔄 Pull Latest Data', 2000);
                            }}).catch(e => {{
                                btn.innerText = '❌ Failed';
                                setTimeout(() => btn.innerText = '🔄 Pull Latest Data', 2000);
                            }});
                        }}
                    </script>
                </div>
                """
            else:
                # Fallback if bin data not found
                star_popup_content = f"⭐ {highlight_type}: {highlight_id} (SEARCHED)"
        else:
            # For trucks and dumping spots, use simple popup
            star_popup_content = f"⭐ {highlight_type}: {highlight_id} (SEARCHED)"
        
        # Add the star marker with custom icon
        if highlight_type == "Bin" and 'bin_data' in locals() and bin_data:
            iframe_star = folium.IFrame(html=star_popup_content, width=320, height=600)
            folium.Marker(
                highlight_coords,
                popup=folium.Popup(iframe_star, max_width=320),
                icon=folium.Icon(color='red', icon='star', prefix='fa'),
                tooltip=f"⭐ {highlight_type}: {highlight_id} (SEARCHED)"
            ).add_to(m)
        else:
            folium.Marker(
                highlight_coords,
                popup=folium.Popup(star_popup_content, max_width=320),
                icon=folium.Icon(color='red', icon='star', prefix='fa'),
                tooltip=f"⭐ {highlight_type}: {highlight_id} (SEARCHED)"
            ).add_to(m)
        
        # Add a permanent data label next to the highlighted item
        if highlight_type == "Bin" and bin_data:
            highlight_label_html = f'''
            <div style="
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
                background: rgba(255, 255, 255, 0.95);
                border: 3px solid #f1c40f;
                border-radius: 8px;
                padding: 6px 10px;
                text-align: center;
                white-space: nowrap;
                box-shadow: 0 4px 12px rgba(0,0,0,0.4);
                transform: translate(20px, -20px);
                font-family: Arial, sans-serif;
            ">
                <div style="color: #e74c3c; margin-bottom: 2px;">⭐ {bin_data["bin_id"]}</div>
                <div style="font-size: 16px; color: #27ae60;">Fill: {bin_data["fill_level"]:.1f}%</div>
            </div>
            '''
            folium.Marker(
                highlight_coords,
                icon=folium.DivIcon(
                    html=highlight_label_html,
                    icon_size=(120, 50),
                    icon_anchor=(0, 0)
                )
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

@st.fragment
def display_live_search_result(map_search_type, map_search_id):
    """Displays a real-time updating card for the searched item without reloading the whole page."""
    if map_search_type == "Bin":
        response = requests.get(f"{API_BASE_URL}/bin-data/?bin_id={map_search_id}")
        if response.status_code == 200:
            data = response.json()
            items = data.get('results', data) if isinstance(data, dict) else data
            item = items[0] if items else None
            if item:
                fill_level = item.get('fill_level', 0)
                last_updated = item.get('last_updated', 'Unknown')
                st.markdown(f'''
                    <div style="background-color: #f8fafc; border-left: 4px solid #10b981; padding: 12px 16px; border-radius: 6px; margin-top: 16px; box-shadow: 0 2px 5px rgba(0,0,0,0.03); border-right: 1px solid #e2e8f0; border-top: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0;">
                        <div style="color: #0f172a; font-weight: 600; font-size: 0.95em; margin-bottom: 6px;">
                            ✅ {map_search_type} Found: {map_search_id} 
                        </div>
                        <div style="color: #475569; font-size: 0.85em; margin-bottom: 4px;">
                            📊 Fill Level: <span style="font-size:1.4em; font-weight:bold; color:#10b981;">{fill_level:.1f}%</span>
                        </div>
                        <div style="color: #475569; font-size: 0.85em;">🕒 Last Updated: {str(last_updated)[:19].replace('T', ' ')}</div>
                        <div style="color: #10b981; font-size: 0.8em; margin-top: 8px; font-weight: 500;">🎯 Highlighted on map with permanent label</div>
                    </div>
                ''', unsafe_allow_html=True)
                
                # Manual refresh button inside the fragment
                if st.button(f"🔄 Pull Live Data from {map_search_id}", use_container_width=True):
                    st.rerun() # This safely re-runs ONLY this fragment, not the whole map!
                return
    st.info(f"Loading {map_search_type} data...")

def main():
    # Navigation system
    st.sidebar.header("🧭 Navigation")
    selected = st.sidebar.selectbox(
        "Choose a section:",
        ["🗺️ Interactive Map", "📊 Analytics Dashboard", "🚛 Truck Management", "🗑️ Bin Management", "📈 Real-time Data", "📸 Camera Gallery"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.info("💡 Map popups now auto-update in real-time (every 0.5s) when you click on a bin.")
    
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
    .st-emotion-cache-lxqt60.e1cbzgzq10 {
        margin-left: 50px !important;
        margin-right: 50px !important;
    }
    
    /* Alternative selector in case the exact class changes */
    .st-emotion-cache-lxqt60 {
        margin-left: 50px !important;
        margin-right: 50px !important;
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
                
                pill_style = f"""
                <div style="display: flex; justify-content: flex-end; margin-bottom: 0;">
                    <div style="display: inline-flex; align-items: center; background-color: #ffffff; border: 1px solid rgba(0,0,0,0.08); border-radius: 20px; padding: 6px 14px; font-size: 0.8rem; font-weight: 500; color: #475569; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
                        <span style="margin-right: 6px;">{freshness_icon}</span>
                        <span style="margin-right: 10px;"><b>Status:</b> {freshness_text}</span>
                        <span style="margin-right: 10px; color: #cbd5e1;">|</span>
                        <span style="margin-right: 10px;">📅 {current_time}</span>
                        <span style="margin-right: 10px; color: #cbd5e1;">|</span>
                        <span>🕒 API: {time_diff:.1f} min ago</span>
                    </div>
                </div>
                """
                st.markdown(pill_style, unsafe_allow_html=True)
            except:
                st.markdown(f"""
                <div style="display: flex; justify-content: flex-end; margin-bottom: 0;">
                    <div style="display: inline-block; background-color: #ffffff; border: 1px solid rgba(0,0,0,0.08); border-radius: 20px; padding: 6px 14px; font-size: 0.8rem; font-weight: 500; color: #475569;">
                        📅 Last updated: {current_time}
                    </div>
                </div>
                """, unsafe_allow_html=True)
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
    with st.container(border=True):
        st.markdown("##### 🔍 Search & Highlight Map Items")
        
        # Show search history if available
        if 'search_history' not in st.session_state:
            st.session_state['search_history'] = []
        
        if st.session_state['search_history']:
            st.caption(f"💡 **Recent searches**: {', '.join(st.session_state['search_history'][-3:])}")
        
        # Create columns for search input and button - all in one line
        col1, col2, col3, col4 = st.columns([1.5, 2, 1, 1], vertical_alignment="bottom")
        
        with col1:
            map_search_type = st.selectbox("Select Item Type", ["Bin", "Truck", "Dumping Spot"], key="map_search_type")
        
        with col2:
            map_search_id = st.text_input("Enter ID", "", key="map_search_id", placeholder="e.g., BIN001, TRUCK01")
        
        with col3:
            search_button = st.button("🔍 Search", type="primary", use_container_width=True)
        
        with col4:
            refresh_button = st.button("🔄 Refresh", use_container_width=True)
            
        # Placeholder for search results
        search_results_placeholder = st.empty()
    
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
            search_results_placeholder.error(f"❌ No {map_search_type.lower()} found with ID '{map_search_id}'")
        else:
            # Show professional detailed info about the found item in the placeholder
            item_id = highlight_item.get('bin_id') or highlight_item.get('truck_id') or highlight_item.get('spot_id') or 'Unknown'
            
            if map_search_type == "Bin":
                # Call the live fragment instead of static markdown
                with search_results_placeholder:
                    display_live_search_result(map_search_type, map_search_id)
            elif map_search_type == "Truck":
                last_updated = highlight_item.get('last_updated', 'Unknown')
                status = highlight_item.get('status', 'Unknown')
                fuel_level = highlight_item.get('fuel_level', 0)
                search_results_placeholder.markdown(f'''
                    <div style="background-color: #f8fafc; border-left: 4px solid #10b981; padding: 12px 16px; border-radius: 6px; margin-top: 16px; box-shadow: 0 2px 5px rgba(0,0,0,0.03); border-right: 1px solid #e2e8f0; border-top: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0;">
                        <div style="color: #0f172a; font-weight: 600; font-size: 0.95em; margin-bottom: 6px;">✅ {map_search_type} Found: {map_search_id}</div>
                        <div style="color: #475569; font-size: 0.85em; margin-bottom: 4px;">🚛 Status: {status} | ⛽ Fuel: {fuel_level:.1f}%</div>
                        <div style="color: #475569; font-size: 0.85em; margin-bottom: 4px;">🕒 Last Updated: {last_updated}</div>
                        <div style="color: #10b981; font-size: 0.8em; margin-top: 8px; font-weight: 500;">🎯 Highlighted on map with ⭐ marker</div>
                    </div>
                ''', unsafe_allow_html=True)
            else:
                last_updated = highlight_item.get('last_updated', 'Unknown')
                search_results_placeholder.markdown(f'''
                    <div style="background-color: #f8fafc; border-left: 4px solid #10b981; padding: 12px 16px; border-radius: 6px; margin-top: 16px; box-shadow: 0 2px 5px rgba(0,0,0,0.03); border-right: 1px solid #e2e8f0; border-top: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0;">
                        <div style="color: #0f172a; font-weight: 600; font-size: 0.95em; margin-bottom: 6px;">✅ {map_search_type} Found: {map_search_id}</div>
                        <div style="color: #475569; font-size: 0.85em;">🕒 Last Updated: {last_updated}</div>
                        <div style="color: #10b981; font-size: 0.8em; margin-top: 8px; font-weight: 500;">🎯 Highlighted on map with ⭐ marker</div>
                    </div>
                ''', unsafe_allow_html=True)
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
    st.sidebar.header("Route through selected bins")
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
    smart_dispatch_button = st.sidebar.button("🤖 Smart Dispatch (Auto-Route)", type="primary", use_container_width=True)
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    st.sidebar.markdown("**Or manual routing:**")
    calculate_route_button = st.sidebar.button("Calculate Route", use_container_width=True)

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
    if smart_dispatch_button:
        st.subheader("🤖 Smart Dispatch: Automated Route")
        
        # 1. Identify critical bins (>= 80% full)
        critical_bins = [b for b in bins if b.get('fill_level', 0) >= 80]
        
        if not critical_bins:
            st.success("✅ All bins are in good condition. No dispatch required at this time.")
        elif not trucks:
            st.error("❌ No trucks available for dispatch.")
        else:
            st.info(f"🚨 Identified **{len(critical_bins)} critical bin(s)** requiring immediate collection.")
            
            # 2. Find centroid of critical bins
            avg_lat = sum(b['latitude'] for b in critical_bins) / len(critical_bins)
            avg_lng = sum(b['longitude'] for b in critical_bins) / len(critical_bins)
            
            # 3. Find optimal truck (nearest to centroid)
            best_truck = None
            min_truck_dist = float('inf')
            for t in trucks:
                if t['status'] == 'ACTIVE':  # Prioritize active trucks
                    dist = calculate_distance(avg_lat, avg_lng, t['current_latitude'], t['current_longitude'])
                    if dist < min_truck_dist:
                        min_truck_dist = dist
                        best_truck = t
            
            # Fallback to any truck if no active ones
            if not best_truck:
                for t in trucks:
                    dist = calculate_distance(avg_lat, avg_lng, t['current_latitude'], t['current_longitude'])
                    if dist < min_truck_dist:
                        min_truck_dist = dist
                        best_truck = t
                        
            st.write(f"🚛 **Assigned Optimal Truck:** {best_truck['truck_id']} (Driver: {best_truck['driver_name']})")
            
            # 3.5. Limit to 25 waypoints due to Google Maps API restrictions
            if len(critical_bins) > 25:
                # Sort critical bins by distance to the assigned truck and keep the closest 25
                critical_bins.sort(key=lambda b: calculate_distance(best_truck['current_latitude'], best_truck['current_longitude'], b['latitude'], b['longitude']))
                critical_bins = critical_bins[:25]
                st.warning("⚠️ **API Limit Reached:** Google Maps allows a maximum of 25 bins per route. The route has been optimized for the 25 closest critical bins.")
            
            # 4. Find nearest dumping spot to centroid
            nearest_dumping_spot = None
            if dumping_spots:
                min_spot_dist = float('inf')
                for spot in dumping_spots:
                    dist = calculate_distance(avg_lat, avg_lng, spot['latitude'], spot['longitude'])
                    if dist < min_spot_dist:
                        min_spot_dist = dist
                        nearest_dumping_spot = spot
            
            current_location = [best_truck['current_latitude'], best_truck['current_longitude']]
            destination_coords = current_location
            if nearest_dumping_spot:
                destination_coords = [nearest_dumping_spot['latitude'], nearest_dumping_spot['longitude']]
                
            waypoint_coords = [[b['latitude'], b['longitude']] for b in critical_bins]
            
            with st.spinner("Calculating optimal automated route on Google Maps..."):
                path, dist_km, duration_mins, error = get_google_maps_route(
                    origin=current_location,
                    destination=destination_coords,
                    waypoints=waypoint_coords
                )
                
            if error:
                st.error(error)
            else:
                if nearest_dumping_spot:
                    st.write(f"🏭 **Final Destination:** Dumping Spot {nearest_dumping_spot['spot_id']}")
                    
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("🚗 Driving Distance", f"{dist_km:.2f} km")
                with col2:
                    st.metric("⏳ Estimated Time", f"{duration_mins:.1f} mins")
                    
                # Display map
                path_map = create_map(
                    bins,
                    dumping_spots,
                    trucks,
                    critical_bins,
                    path,
                    highlight_item=None,
                    highlight_type=None
                )
                
                with st.container():
                    st.markdown('<div class="map-container">', unsafe_allow_html=True)
                    folium_static(path_map, width=1200, height=800)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
    elif calculate_route_button and selected_truck and selected_bins:
        st.subheader("📍 Calculated Real-World Route")
        # Start from the selected truck's location
        current_location = [selected_truck['current_latitude'], selected_truck['current_longitude']]
        
        # We need a destination. Let's find the nearest dumping spot to the LAST bin 
        # using our fast Euclidean heuristic so we know where to send the truck finally.
        nearest_dumping_spot = None
        if dumping_spots and selected_bins:
            last_bin = selected_bins[-1]
            min_dist = float('inf')
            for spot in dumping_spots:
                dist = calculate_distance(last_bin['latitude'], last_bin['longitude'], spot['latitude'], spot['longitude'])
                if dist < min_dist:
                    min_dist = dist
                    nearest_dumping_spot = spot
        
        destination_coords = current_location
        if nearest_dumping_spot:
            destination_coords = [nearest_dumping_spot['latitude'], nearest_dumping_spot['longitude']]
            
        # Limit to 25 waypoints due to Google Maps API restrictions
        if len(selected_bins) > 25:
            st.warning("⚠️ **API Limit Reached:** Google Maps allows a maximum of 25 bins per route. Only the first 25 bins selected will be routed.")
            selected_bins = selected_bins[:25]
            
        waypoint_coords = [[b['latitude'], b['longitude']] for b in selected_bins]
        
        with st.spinner("Calculating optimal route on Google Maps..."):
            path, dist_km, duration_mins, error = get_google_maps_route(
                origin=current_location,
                destination=destination_coords,
                waypoints=waypoint_coords
            )
            
        if error:
            st.error(error)
        else:
            if nearest_dumping_spot:
                st.write(f"**Final Destination:** Dumping Spot {nearest_dumping_spot['spot_id']}")
                
            col1, col2 = st.columns(2)
            with col1:
                st.metric("🚗 Driving Distance", f"{dist_km:.2f} km")
            with col2:
                st.metric("⏳ Estimated Time", f"{duration_mins:.1f} mins")
                
            # Display map with the calculated path
            path_map = create_map(
                bins,
                dumping_spots,
                trucks,
                selected_bins,
                path,
                highlight_item=None,
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