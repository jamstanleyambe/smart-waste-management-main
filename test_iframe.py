import folium
m = folium.Map()
html = """
    <div>Fill Level: <span id="fill">0%</span></div>
    <button onclick="document.getElementById('fill').innerText='100%'">Pull Latest Data</button>
"""
iframe = folium.IFrame(html, width=200, height=100)
folium.Marker([0,0], popup=folium.Popup(iframe)).add_to(m)
print("Success")
