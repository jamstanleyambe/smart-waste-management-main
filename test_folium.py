import folium
m = folium.Map()
html = """<div>Hello</div><script>console.log("test");</script>"""
folium.Marker([0,0], popup=folium.Popup(html)).add_to(m)
print("Success")
