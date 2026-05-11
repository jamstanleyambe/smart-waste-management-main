import re

with open('route_dashboard.py', 'r') as f:
    content = f.read()

# 1. Update standard bin popup
# Add id to fill level
content = content.replace(
    '">{bin[\'fill_level\']:.1f}%</span>',
    '" id="fill-level">{bin[\'fill_level\']:.1f}%</span>'
)
# Add id to last_updated and add button + script + iframe logic
standard_bin_replacement = """            ">
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
                function updateData() {
                    const btn = document.querySelector('button');
                    btn.innerText = '🔄 Pulling...';
                    fetch('http://localhost:8000/api/bin-data/?bin_id=' + '{bin["bin_id"]}')
                    .then(r => r.json())
                    .then(data => {
                        let b = (data.results && data.results.length > 0) ? data.results[0] : (data.length > 0 ? data[0] : data);
                        if (b && b.fill_level !== undefined) {
                            document.getElementById('fill-level').innerText = parseFloat(b.fill_level).toFixed(1) + '%';
                            if (b.last_updated) {
                                document.getElementById('last-updated').innerText = b.last_updated.substring(0,16).replace('T', ' ');
                            }
                        }
                        btn.innerText = '✅ Updated!';
                        setTimeout(() => btn.innerText = '🔄 Pull Latest Data', 2000);
                    }).catch(e => {
                        btn.innerText = '❌ Failed';
                        setTimeout(() => btn.innerText = '🔄 Pull Latest Data', 2000);
                    });
                }
            </script>
        </div>
        \"\"\"
        
        iframe = folium.IFrame(html=popup_content, width=320, height=420)
        
        # Add marker to map
        folium.Marker(
            [bin['latitude'], bin['longitude']],
            popup=folium.Popup(iframe, max_width=320),
            icon=icon
        ).add_to(m)"""

content = re.sub(
    r'            ">\n                📅 Updated: \{bin\[\'last_updated\'\]\[:16\]\.replace\(\'T\', \' \'\)\}\n            </div>\n        </div>\n        \"\"\"\n        \n        # Add marker to map\n        folium\.Marker\(\n            \[bin\[\'latitude\'\], bin\[\'longitude\'\]\],\n            popup=folium\.Popup\(popup_content, max_width=320\),\n            icon=icon\n        \)\.add_to\(m\)',
    standard_bin_replacement,
    content,
    flags=re.MULTILINE
)

# 2. Update star bin popup
# Add id to star fill level
content = content.replace(
    'style="font-weight: bold; font-size: 14px;">{bin_data[\'fill_level\']:.1f}%</span>',
    'id="star-fill" style="font-weight: bold; font-size: 14px;">{bin_data[\'fill_level\']:.1f}%</span>'
)
# Add id to star last_updated and add button + script + iframe logic
star_bin_replacement = """                    ">
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
                        function updateStarData() {
                            const btn = document.querySelector('button');
                            btn.innerText = '🔄 Pulling...';
                            fetch('http://localhost:8000/api/bin-data/?bin_id=' + '{bin_data["bin_id"]}')
                            .then(r => r.json())
                            .then(data => {
                                let b = (data.results && data.results.length > 0) ? data.results[0] : (data.length > 0 ? data[0] : data);
                                if (b && b.fill_level !== undefined) {
                                    document.getElementById('star-fill').innerText = parseFloat(b.fill_level).toFixed(1) + '%';
                                    if (b.last_updated) {
                                        document.getElementById('star-updated').innerText = b.last_updated.substring(0,16).replace('T', ' ');
                                    }
                                }
                                btn.innerText = '✅ Updated!';
                                setTimeout(() => btn.innerText = '🔄 Pull Latest Data', 2000);
                            }).catch(e => {
                                btn.innerText = '❌ Failed';
                                setTimeout(() => btn.innerText = '🔄 Pull Latest Data', 2000);
                            });
                        }
                    </script>
                </div>
                \"\"\"
            else:
                # Fallback if bin data not found
                star_popup_content = f"⭐ {highlight_type}: {highlight_id} (SEARCHED)"
        else:
            # For trucks and dumping spots, use simple popup
            star_popup_content = f"⭐ {highlight_type}: {highlight_id} (SEARCHED)"
        
        # Add the star marker with custom icon
        if highlight_type == "Bin" and 'bin_data' in locals() and bin_data:
            iframe_star = folium.IFrame(html=star_popup_content, width=320, height=420)
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
            ).add_to(m)"""

content = re.sub(
    r'                    ">\n                        Last updated: \{bin_data\.get\(\'last_updated\', \'Unknown\'\)\}\n                    </div>\n                </div>\n                \"\"\"\n            else:\n                # Fallback if bin data not found\n                star_popup_content = f"⭐ \{highlight_type\}: \{highlight_id\} \(SEARCHED\)"\n        else:\n            # For trucks and dumping spots, use simple popup\n            star_popup_content = f"⭐ \{highlight_type\}: \{highlight_id\} \(SEARCHED\)"\n        \n        # Add the star marker with custom icon\n        folium\.Marker\(\n            highlight_coords,\n            popup=folium\.Popup\(star_popup_content, max_width=320\),\n            icon=folium\.Icon\(color=\'red\', icon=\'star\', prefix=\'fa\'\),\n            tooltip=f"⭐ \{highlight_type\}: \{highlight_id\} \(SEARCHED\)"\n        \)\.add_to\(m\)',
    star_bin_replacement,
    content,
    flags=re.MULTILINE
)

with open('route_dashboard.py', 'w') as f:
    f.write(content)
