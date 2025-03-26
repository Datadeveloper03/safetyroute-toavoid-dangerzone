import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from folium.plugins import HeatMap
import networkx as nx
import osmnx as ox
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# --- Load the dataset ---
file_path = "chennai_crime_dataset.csv"
df = pd.read_csv(file_path)

# --- Sidebar: Filters and Routing Options ---
st.sidebar.title("🔍 Filter and Navigate")

# Crime Type Filter
crime_types = df['Crime Type'].unique().tolist()
selected_crime_types = st.sidebar.multiselect("Select Crime Types", crime_types, default=crime_types)

# Date Range Filter
df['Date'] = pd.to_datetime(df['Date'])
start_date = df['Date'].min()
end_date = df['Date'].max()
date_range = st.sidebar.date_input("Select Date Range", [start_date, end_date])

# Case Status Filter
status_options = df['Case Status'].unique().tolist()
selected_status = st.sidebar.multiselect("Select Case Status", status_options, default=status_options)

# --- Filter Data Based on Selections ---
filtered_df = df[
    (df['Crime Type'].isin(selected_crime_types)) &
    (df['Date'].between(pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1]))) &
    (df['Case Status'].isin(selected_status))
]

# --- Safe Route Navigation Inputs ---
st.sidebar.title("🚦 Safe Route Navigation")

start_location = st.sidebar.text_input("Enter Start Location (e.g., T. Nagar, Chennai)")
end_location = st.sidebar.text_input("Enter Destination (e.g., Guindy, Chennai)")

# --- Map Display ---
st.title("📍 Chennai Crime Map + Safe Routing")

# --- Geolocation ---
geolocator = Nominatim(user_agent="geoapi")

def get_coordinates(location):
    """Convert address to latitude and longitude."""
    try:
        location = geolocator.geocode(location)
        if location:
            return (location.latitude, location.longitude)
    except:
        return None

# Convert start and end locations
start_coords = get_coordinates(start_location)
end_coords = get_coordinates(end_location)

# --- Map with Crime Locations and Route ---
st.subheader("📌 Crime Map and Safe Route")

# Base Map
m = folium.Map(location=[13.0827, 80.2707], zoom_start=12)

# --- Add Crime Heatmap ---
heatmap_data = filtered_df[['Latitude', 'Longitude']].values.tolist()
HeatMap(heatmap_data, radius=15, blur=10).add_to(m)

# --- Add Crime Markers ---
for _, row in filtered_df.iterrows():
    folium.Marker(
        location=[row['Latitude'], row['Longitude']],
        popup=(
            f"<b>Crime Type:</b> {row['Crime Type']}<br>"
            f"<b>Location:</b> {row['Location']}<br>"
            f"<b>Date:</b> {row['Date'].strftime('%Y-%m-%d')}<br>"
            f"<b>Suspect:</b> {row['Suspect Gender']}, {row['Suspect Age']} yrs<br>"
            f"<b>Victim:</b> {row['Victim Gender']}, {row['Victim Age']} yrs<br>"
            f"<b>Arrest Made:</b> {row['Arrest Made']}<br>"
            f"<b>Case Status:</b> {row['Case Status']}<br>"
            f"<b>Description:</b> {row['Description']}"
        ),
        icon=folium.Icon(color="red" if row['Arrest Made'] == "No" else "green")
    ).add_to(m)

# --- Safe Route Navigation ---
if start_coords and end_coords:
    try:
        # Load road network
        G = ox.graph_from_place("Chennai, India", network_type='walk')

        # Use NetworkX's built-in method (slower but doesn't need scikit-learn)
        orig_node = ox.nearest_nodes(G, start_coords[1], start_coords[0])
        dest_node = ox.nearest_nodes(G, end_coords[1], end_coords[0])


        # Compute the shortest path
        route = nx.shortest_path(G, orig_node, dest_node, weight="length")
        route_coords = [(G.nodes[node]['y'], G.nodes[node]['x']) for node in route]

        # Plot the route
        folium.PolyLine(
            locations=route_coords,
            color="blue",
            weight=6,
            opacity=0.7,
            tooltip="Safe Route"
        ).add_to(m)

        # Add markers for start and destination
        folium.Marker(start_coords, popup="Start Location", icon=folium.Icon(color="green")).add_to(m)
        folium.Marker(end_coords, popup="Destination", icon=folium.Icon(color="red")).add_to(m)

        folium_static(m)

        # --- Distance and Travel Information ---
        distance = geodesic(start_coords, end_coords).km
        st.write(f"🚶‍♂️ **Distance:** {distance:.2f} km")

    except Exception as e:
        st.error(f"Error finding route: {e}")
else:
    folium_static(m)
    if start_location and end_location:
        st.warning("Invalid coordinates. Please enter valid start and destination locations.")

# --- Summary Statistics ---
st.subheader("📊 Crime Summary Statistics")
st.write(f"Total Crimes Displayed: {len(filtered_df)}")
st.write("Crime Types Count:")
st.write(filtered_df['Crime Type'].value_counts())
