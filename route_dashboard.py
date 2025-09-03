import streamlit as st
import folium
from streamlit_folium import folium_static
import requests
import numpy as np
from folium.plugins import MarkerCluster
import json
import altair as alt
import pandas as pd
import datetime
from dateutil import parser as date_parser

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
    print(f"API Response: {response.status_code} - {response.text}")
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
    print(f"Dumping Spot API Response: {response.status_code} - {response.text}")
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
    print(f"Truck API Response: {response.status_code} - {response.text}")
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
    print(f"Add Bin API Response: {response.status_code} - {response.text}")
    return response.status_code == 201

def delete_bin(bin_id):
    """Delete a bin via the API using the RESTful endpoint (by pk/id)"""
    # Find the bin's pk (id) from the bins list
        bins_list = get_bins()
        bin_obj = next((b for b in bins_list if b['bin_id'] == bin_id), None)
        if not bin_obj:
            return False
        pk = bin_obj['id']
    response = requests.delete(f"{API_BASE_URL}/bin-data/{pk}/")
    print(f"Delete Bin API Response: {response.status_code} - {response.text}")
    return response.status_code == 204

def create_map(bins, dumping_spots, trucks, selected_bin=None, path=None):
    m = folium.Map(location=[4.0511, 9.7679], zoom_start=13)
    
    # Add truck markers
    for truck in trucks:
        # Determine truck color based on status
        truck_color = '#1e90ff'  # Default blue
        if truck['status'] == 'MAINTENANCE':
            truck_color = '#ff6b6b'  # Red for maintenance
        elif truck['status'] == 'ACTIVE':
            truck_color = '#51cf66'  # Green for active
        elif truck['status'] == 'IDLE':
            truck_color = '#ffd43b'  # Yellow for idle
            
        # Create enhanced popup content
        popup_content = f"""
            <b>Truck ID:</b> {truck['truck_id']}<br>
            <b>Driver:</b> {truck['driver_name']}<br>
            <b>Status:</b> {truck['status']}<br>
            <b>Fuel Level:</b> {truck['fuel_level']:.1f}%<br>
            <b>Location:</b> ({truck['current_latitude']:.4f}, {truck['current_longitude']:.4f})<br>
            <b>Last Updated:</b> {truck['last_updated']}"""
        
        # Create custom truck marker with ID label
        folium.Marker(
            [truck['current_latitude'], truck['current_longitude']],
            popup=folium.Popup(popup_content, max_width=300),
            icon=folium.DivIcon(
                html=f'''
                <div style="
                    width: 40px; 
                    height: 40px; 
                    background-color: {truck_color}; 
                    border: 3px solid white;
                    border-radius: 12px; 
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.4);
                    position: relative;
                ">
                    <div style="
                        font-size: 20px; 
                        color: white;
                    ">🚛</div>
            </div>
                <div style="
                    position: absolute;
                    top: -24px;
                    left: 50%;
                    transform: translateX(-50%);
                    font-size: 11px; 
                    font-weight: bold; 
                    color: white; 
                    background-color: rgba(30, 144, 255, 0.9); 
                    border: 1px solid white;
                    border-radius: 6px; 
                    padding: 2px 6px; 
                    text-align: center;
                    white-space: nowrap;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                ">{truck['truck_id']}</div>
                ''',
                icon_size=(40, 40),
                icon_anchor=(20, 20)
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
            # Add blinking effect for 100% full bins
            icon_html = f'''
                <div style="background-color: {color}; width: 20px; height: 20px; border-radius: 50%; 
                           animation: blink 1s infinite;">
                </div>
                <style>
                    @keyframes blink {{
                        0% {{ opacity: 1; }}
                        50% {{ opacity: 0.3; }}
                        100% {{ opacity: 1; }}
                    }}
                </style>
            '''
            icon = folium.DivIcon(html=icon_html)
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
        
        # Create popup content
        popup_content = f"""
            <b>Bin ID:</b> {bin['bin_id']}<br>
            <b>Fill Level:</b> {bin['fill_level']:.1f}%<br>
            <b>Organic:</b> {bin['organic_percentage']:.1f}%<br>
            <b>Plastic:</b> {bin['plastic_percentage']:.1f}%<br>
            <b>Metal:</b> {bin['metal_percentage']:.1f}%<br>
            <b>Last Updated:</b> {bin['last_updated']}"""
        
        # Create custom marker with bin ID label
        # For 100% full bins with blinking effect, keep the special icon
        if bin['fill_level'] == 100:
        folium.Marker(
            [bin['latitude'], bin['longitude']],
            popup=folium.Popup(popup_content, max_width=300),
            icon=icon
        ).add_to(m)

            # Add text label for bin ID
            folium.Marker(
                [bin['latitude'], bin['longitude']],
                icon=folium.DivIcon(
                    html=f'''
                    <div style="
                        font-size: 10px; 
                        font-weight: bold; 
                        color: white; 
                        background-color: rgba(220, 20, 60, 0.8); 
                        border: 2px solid white;
                        border-radius: 8px; 
                        padding: 2px 6px; 
                        text-align: center;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                        white-space: nowrap;
                        transform: translate(-50%, -100%);
                        margin-top: -25px;
                    ">{bin['bin_id']}</div>
                    ''',
                    icon_size=(50, 20),
                    icon_anchor=(25, 35)
                )
            ).add_to(m)
        else:
            # For regular bins, create a custom marker with bin ID
            # Get color name for styling
            color_map = {
                'red': '#dc143c',
                'orange': '#ff8c00', 
                'yellow': '#ffd700',
                'green': '#32cd32',
                'gray': '#808080'
            }
            
            marker_color = color_map.get(color, '#808080')
            text_color = 'white' if color in ['red', 'green', 'gray'] else 'black'
            
            # Create custom marker with bin ID displayed
            folium.Marker(
                [bin['latitude'], bin['longitude']],
                popup=folium.Popup(popup_content, max_width=300),
                icon=folium.DivIcon(
                    html=f'''
                    <div style="
                        width: 30px; 
                        height: 30px; 
                        background-color: {marker_color}; 
                        border: 3px solid white;
                        border-radius: 50%; 
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        box-shadow: 0 3px 6px rgba(0,0,0,0.3);
                        position: relative;
                    ">
                        <div style="
                            font-size: 8px; 
                            font-weight: bold; 
                            color: {text_color};
                            text-align: center;
                            line-height: 1;
                        ">{bin['fill_level']:.0f}%</div>
                    </div>
                    <div style="
                        position: absolute;
                        top: -20px;
                        left: 50%;
                        transform: translateX(-50%);
                        font-size: 10px; 
                        font-weight: bold; 
                        color: white; 
                        background-color: rgba(0, 0, 0, 0.7); 
                        border-radius: 4px; 
                        padding: 1px 4px; 
                        text-align: center;
                        white-space: nowrap;
                        box-shadow: 0 1px 3px rgba(0,0,0,0.3);
                    ">{bin['bin_id']}</div>
                    ''',
                    icon_size=(30, 30),
                    icon_anchor=(15, 15)
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
        
        popup_content = f"""
            <b>Dumping Spot ID:</b> {spot['spot_id']}<br>
            <b>Fill Level:</b> {fill_level:.1f}%<br>
            <b>Total Capacity:</b> {spot['total_capacity']:.1f} tons<br>
            <b>Organic Content:</b> {organic_percentage:.1f}%<br>
            <b>Plastic Content:</b> {plastic_percentage:.1f}%<br>
            <b>Metal Content:</b> {metal_percentage:.1f}%
         """
        # Create custom dumping spot marker with ID label
        folium.Marker(
            [spot['latitude'], spot['longitude']],
            popup=folium.Popup(popup_content, max_width=300),
            icon=folium.DivIcon(
                html=f'''
                <div style="
                    width: 35px; 
                    height: 35px; 
                    background-color: #2c3e50; 
                    border: 3px solid white;
                    border-radius: 8px; 
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.4);
                    position: relative;
                ">
                    <div style="
                        font-size: 18px; 
                        color: white;
                    ">🗑️</div>
                </div>
                <div style="
                    position: absolute;
                    top: -22px;
                    left: 50%;
                    transform: translateX(-50%);
                    font-size: 11px; 
                    font-weight: bold; 
                    color: white; 
                    background-color: rgba(44, 62, 80, 0.9); 
                    border: 1px solid white;
                    border-radius: 6px; 
                    padding: 2px 6px; 
                    text-align: center;
                    white-space: nowrap;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                ">{spot['spot_id']}</div>
                ''',
                icon_size=(35, 35),
                icon_anchor=(17, 17)
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
    
    return m

def main():
    st.title("Smart Waste Management Route Dashboard - Douala 5")
    
    # Remove single truck location input
    # Get bins data
            bins = get_bins()
    # Get dumping spot data
            dumping_spots = get_dumping_spots()
    # Get trucks data
        trucks = get_trucks()
    
    # Search and highlight item on the map
    st.header("Search Item by ID on Map")
    map_search_type = st.selectbox("Select Item Type to Search", ["Bin", "Truck", "Dumping Spot"], key="map_search_type")
    map_search_id = st.text_input("Enter ID to Search on Map (e.g., BIN001, TRUCK01, DS01)", "", key="map_search_id")
    highlight_item = None
    if map_search_id:
        if map_search_type == "Bin":
            highlight_item = next((b for b in bins if b['bin_id'] == map_search_id), None)
        elif map_search_type == "Truck":
            highlight_item = next((t for t in trucks if t['truck_id'] == map_search_id), None)
        else:
            highlight_item = next((d for d in dumping_spots if d['spot_id'] == map_search_id), None)
        if not highlight_item:
            st.warning(f"No {map_search_type.lower()} found with ID '{map_search_id}'")
    # Create main map, centering/highlighting if search is active
    if highlight_item:
        if map_search_type == "Bin":
            center = [highlight_item['latitude'], highlight_item['longitude']]
            main_map = create_map(bins, dumping_spots, trucks, selected_bin=highlight_item)
        elif map_search_type == "Truck":
            center = [highlight_item['current_latitude'], highlight_item['current_longitude']]
            main_map = create_map(bins, dumping_spots, trucks, selected_bin=None, path=None)
        else:
            center = [highlight_item['latitude'], highlight_item['longitude']]
            main_map = create_map(bins, dumping_spots, trucks, selected_bin=None, path=None)
        main_map.location = center
        main_map.zoom_start = 16
    else:
        main_map = create_map(bins, dumping_spots, trucks)
    folium_static(main_map)

    # Add any item form in the sidebar
    st.sidebar.header("Add New Item")
    add_item_type = st.sidebar.selectbox("Select Item Type to Add", ["Bin", "Truck", "Dumping Spot"], key="add_item_type")
    with st.sidebar.form("add_item_form"):
        if add_item_type == "Bin":
            bin_id = st.text_input("Bin ID")
            fill_level = st.slider("Fill Level (%)", 0, 100, 50)
            lat = st.number_input("Latitude", value=DOUALA5_CENTER[0], format="%.4f", key="bin_lat")
            lon = st.number_input("Longitude", value=DOUALA5_CENTER[1], format="%.4f", key="bin_lon")
            organic = st.slider("Organic (%)", 0, 100, 33)
            plastic = st.slider("Plastic (%)", 0, 100, 33)
            metal = st.slider("Metal (%)", 0, 100, 34)
            submitted = st.form_submit_button("Add Bin")
            if submitted:
                if organic + plastic + metal != 100:
                    st.error("Percentages must sum to 100%")
                else:
                    bin_data = {
                        "bin_id": bin_id,
                        "fill_level": fill_level,
                        "latitude": lat,
                        "longitude": lon,
                        "organic_percentage": organic,
                        "plastic_percentage": plastic,
                        "metal_percentage": metal
                    }
                    if add_bin(bin_data):
                        st.success("Bin added successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to add bin")
        elif add_item_type == "Truck":
            truck_id = st.text_input("Truck ID")
            driver_name = st.text_input("Driver Name")
            current_lat = st.number_input("Latitude", value=DOUALA5_CENTER[0], format="%.4f", key="truck_lat")
            current_lon = st.number_input("Longitude", value=DOUALA5_CENTER[1], format="%.4f", key="truck_lon")
            fuel_level = st.number_input("Fuel Level", value=100.0, format="%.2f")
            status = st.selectbox("Status", ["ACTIVE", "IDLE", "MAINTENANCE"])
            submitted = st.form_submit_button("Add Truck")
            if submitted:
                truck_data = {
                    "truck_id": truck_id,
                    "driver_name": driver_name,
                    "current_latitude": current_lat,
                    "current_longitude": current_lon,
                    "fuel_level": fuel_level,
                    "status": status
                }
                response = requests.post(f"{API_BASE_URL}/trucks/", json=truck_data)
                if response.status_code == 201:
                    st.success("Truck added successfully!")
                    st.rerun()
                else:
                    st.error(f"Failed to add truck: {response.text}")
        else:
            spot_id = st.text_input("Dumping Spot ID")
            lat = st.number_input("Latitude", value=DOUALA5_CENTER[0], format="%.4f", key="spot_lat")
            lon = st.number_input("Longitude", value=DOUALA5_CENTER[1], format="%.4f", key="spot_lon")
            total_capacity = st.number_input("Total Capacity", value=1000.0, format="%.2f")
            organic_content = st.number_input("Organic Content", value=0.0, format="%.2f")
            plastic_content = st.number_input("Plastic Content", value=0.0, format="%.2f")
            metal_content = st.number_input("Metal Content", value=0.0, format="%.2f")
            submitted = st.form_submit_button("Add Dumping Spot")
            if submitted:
                spot_data = {
                    "spot_id": spot_id,
                    "latitude": lat,
                    "longitude": lon,
                    "total_capacity": total_capacity,
                    "organic_content": organic_content,
                    "plastic_content": plastic_content,
                    "metal_content": metal_content
                }
                response = requests.post(f"{API_BASE_URL}/dumping-spots/", json=spot_data)
                if response.status_code == 201:
                    st.success("Dumping Spot added successfully!")
                    st.rerun()
                else:
                    st.error(f"Failed to add dumping spot: {response.text}")

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
    now = datetime.datetime.utcnow()
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
    calculate_route_button = st.sidebar.button("Calculate Route")

    # Create main map
    main_map = create_map(bins, dumping_spots, trucks, selected_bins)
    folium_static(main_map)

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
            path
        )
        folium_static(path_map)
    elif calculate_route_button and not selected_truck:
        st.warning("Please select a truck to calculate a route.")
    elif calculate_route_button and not selected_bins:
        st.warning("Please select at least one bin to calculate a route.")

    # Generalized Delete Section
    st.header("Delete Item by ID")
    item_type = st.selectbox("Select Item Type", ["Bin", "Truck", "Dumping Spot"])
    item_id = st.text_input("Enter ID to Delete (e.g., BIN001, TRUCK01, DS01)", "")
    item_found = None
    if item_type == "Bin":
        items = bins
        id_field = "bin_id"
        delete_func = delete_bin
    elif item_type == "Truck":
        items = trucks
        id_field = "truck_id"
        def delete_truck(truck_id):
            response = requests.delete(f"{API_BASE_URL}/trucks/{truck_id}/")
            print(f"Delete Truck API Response: {response.status_code} - {response.text}")
            return response.status_code == 204
        delete_func = delete_truck
    else:
        items = dumping_spots
        id_field = "spot_id"
        def delete_dumping_spot(spot_id):
            response = requests.delete(f"{API_BASE_URL}/dumping-spots/{spot_id}/")
            print(f"Delete Dumping Spot API Response: {response.status_code} - {response.text}")
            return response.status_code == 204
        delete_func = delete_dumping_spot
    if item_id:
        item_found = next((item for item in items if item[id_field] == item_id), None)
        if item_found:
            st.write(f"**{item_type} Details:**")
            st.json(item_found)
            if st.button(f"Delete {item_type}", key=f"delete_{item_type}_{item_id}"):
                if delete_func(item_id):
                    st.success(f"{item_type} {item_id} deleted!")
                    st.rerun()
                else:
                    st.error(f"Failed to delete {item_type} {item_id}")
        else:
            st.warning(f"No {item_type.lower()} found with ID '{item_id}'")

if __name__ == "__main__":
    main() 