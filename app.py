import streamlit as st
from geopy.geocoders import Nominatim
import folium
from io import BytesIO
import streamlit.components.v1 as components
import re

# Set up the app with a wide layout (must be the first Streamlit command)
st.set_page_config(layout="wide")

# Title spanning across the top
st.title("Map My Locations")

# Split the layout into two parts: Sidebar for list of locations and main area for the map
sidebar = st.sidebar
map_area = st.container()

# Initialize session state to store marker data
if "locations" not in st.session_state:
    st.session_state["locations"] = []

# Function to check if a string contains non-English characters
def contains_non_english(text):
    return bool(re.search(r'[^\x00-\x7F]', text))

# Sidebar: Add input for location name and display list of locations
with sidebar:
    st.header("List of Locations")
    
    # Input for location name
    location_name = st.text_input("Search for a location:", "")

    # Button to add the marker
    if st.button("Add Location"):
        if location_name:
            # Check if location already exists
            existing_names = [loc["name"].lower() for loc in st.session_state["locations"]]
            if location_name.lower() in existing_names:
                st.warning("Location already exists")
            else:
                # Initialize the geocoder
                geolocator = Nominatim(user_agent="multi_location_app")

                # Get the location from the geolocator
                location = geolocator.geocode(location_name)

                if location:
                    # Check if the returned location name contains non-English characters
                    location_display_name = location.address
                    if contains_non_english(location_display_name):
                        location_display_name += f" ({location_name.title()})"

                    # Add the new location with full address to the session state
                    st.session_state["locations"].append({
                        "name": location_name,
                        "full_address": location.address,  # Store the full address
                        "latitude": location.latitude,
                        "longitude": location.longitude,
                        "display_name": location_display_name
                    })
                    st.success(f"Location '{location_name}' added.")
                else:
                    st.error(f"Location '{location_name}' not found.")

    # Add a list of locations in the sidebar with a remove button for each
    if st.session_state["locations"]:
        for idx, loc in enumerate(st.session_state["locations"]):
            col1, col2 = st.columns([3, 1])  # Split into two columns for name and button
            with col1:
                st.write(loc['name'])
            with col2:
                # Create a remove button
                remove_button = st.button("×", key=f"remove_{idx}")
                if remove_button:
                    # Remove the location from session state
                    st.session_state["locations"].pop(idx)
                    st.rerun()  # Rerun to update the map and sidebar

# Map Area: Display the map in the right area
with map_area:
    # Create a folium map centered at a default location (if at least one location is valid, it will be updated)
    map_ = folium.Map(location=[20, 0], zoom_start=2)  # Default center location (approximate center of world)

    # Loop through all stored locations and add them to the map with tooltips
    for loc in st.session_state["locations"]:
        folium.Marker(
            [loc["latitude"], loc["longitude"]],
            popup=loc["display_name"],
            # tooltip=loc["display_name"]  # Tooltip shows the full address on hover
        ).add_to(map_)

    # Render the map HTML as a string and display it in Streamlit
    map_html = map_._repr_html_()
    components.html(map_html, height=600)

    # Button to export the map and provide it as a downloadable file
    if st.button("Export Map with Locations"):
        # Save the map to an in-memory file
        map_file = BytesIO()
        map_.save(map_file, close_file=False)
        
        # Seek to the beginning of the BytesIO object
        map_file.seek(0)

        # Provide a download button for the in-memory map file
        st.download_button(
            label="Download Exported Map with Locations",
            data=map_file,
            file_name="exported_map.html",
            mime="text/html"
        )
