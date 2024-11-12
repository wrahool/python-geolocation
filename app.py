import streamlit as st
from geopy.geocoders import Nominatim
import folium
from io import BytesIO
import streamlit.components.v1 as components
import re

st.set_page_config(layout="wide")
st.title("Map My Locations")

# Instructions panel toggle using a checkbox
st.session_state["show_instructions"] = st.checkbox("Show Instructions", value=False)

# Conditionally display instructions based on checkbox state
if st.session_state["show_instructions"]:
    st.write("""
        ### Instructions
        This app allows you to add and view locations on an interactive map. Here’s how to use it:

        1. Enter a location in the search box and start typing. Suggestions will when you press Enter.
        2. Select the correct location from the suggestions in the drop down.
        3. Click "Add Selected Location" to add it to the map.
        4. You can remove any location by clicking the '×' button next to it.
        5. Once you're done, click "Export Map with Locations" to download the map as an HTML file.
    """)

# Main app content
sidebar = st.sidebar
map_area = st.container()

if "locations" not in st.session_state:
    st.session_state["locations"] = []
if "location_options" not in st.session_state:
    st.session_state["location_options"] = []
if "selected_location" not in st.session_state:
    st.session_state["selected_location"] = None

def contains_non_english(text):
    return bool(re.search(r'[^\x00-\x7F]', text))

def remove_postal_code(x):
    return re.sub(r'\b\d{4,}\b,?', '', x).strip()

with sidebar:
    st.header("List of Locations")
    
    location_name = st.text_input("Search for a location (type 3+ characters for suggestions):", "")

    if len(location_name) >= 3:
        geolocator = Nominatim(user_agent="multi_location_app")
        locations = geolocator.geocode(location_name, exactly_one=False, limit=5)
        
        if locations:
            st.session_state["location_options"] = [
                {"name": loc.address, "latitude": loc.latitude, "longitude": loc.longitude}
                for loc in locations
            ]
        else:
            st.session_state["location_options"] = []
    
    if st.session_state["location_options"]:
        option_names = [remove_postal_code(loc["name"]) for loc in st.session_state["location_options"]]
        selected_option = st.selectbox("Suggestions:", option_names)

        if selected_option:
            st.session_state["selected_location"] = next(
                loc for loc in st.session_state["location_options"] if remove_postal_code(loc["name"]) == selected_option
            )

        if st.button("Add Selected Location"):
            if st.session_state["selected_location"]:
                selected_location = st.session_state["selected_location"]
                existing_names = [loc["name"].lower() for loc in st.session_state["locations"]]
                if selected_location["name"].lower() in existing_names:
                    st.warning("Location already exists")
                else:
                    location_display_name = remove_postal_code(selected_location["name"])
                    if contains_non_english(location_display_name):
                        location_display_name += f" ({location_name.title()})"
                    st.session_state["locations"].append({
                        "name": location_name,
                        "full_address": selected_location["name"],
                        "latitude": selected_location["latitude"],
                        "longitude": selected_location["longitude"],
                        "display_name": location_display_name
                    })
                    st.success(f"Location '{location_display_name}' added.")

                st.session_state["location_options"] = []
                st.session_state["selected_location"] = None

    if st.session_state["locations"]:
        for idx, loc in enumerate(st.session_state["locations"]):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(loc['display_name'])
            with col2:
                remove_button = st.button("×", key=f"remove_{idx}")
                if remove_button:
                    st.session_state["locations"].pop(idx)

with map_area:
    if st.button("Export Map with Locations"):
        map_ = folium.Map(location=[20, 0], zoom_start=2)
        for loc in st.session_state["locations"]:
            folium.Marker(
                [loc["latitude"], loc["longitude"]],
                popup=loc["display_name"]
            ).add_to(map_)
        
        map_file = BytesIO()
        map_.save(map_file, close_file=False)
        map_file.seek(0)

        st.download_button(
            label="Download Exported Map with Locations",
            data=map_file,
            file_name="exported_map.html",
            mime="text/html"
        )
    
    map_ = folium.Map(location=[20, 0], zoom_start=2)

    for loc in st.session_state["locations"]:
        folium.Marker(
            [loc["latitude"], loc["longitude"]],
            popup=loc["display_name"]
        ).add_to(map_)

    map_html = map_._repr_html_()
    components.html(map_html, height=600)
