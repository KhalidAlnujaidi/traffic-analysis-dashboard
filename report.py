import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
import numpy as np
import streamlit.components.v1 as components 

# Function to get coordinates from the stop name
def get_coordinates_from_stop_name(stop_name):
    for stop in metro_stops_list:
        if stop['stop_name'] == stop_name:
            return stop['location']
    return None  # If stop is not found


# Read the JSON file into a DataFrame
df = pd.read_json('stations.json')
# Initialize an empty list to store stop details
metro_stops_list = []

# Iterate over all metro lines to match stops with their line
for line in df['metro']['line']:
    line_color = line['routeColor']
    line_name = line['lineName'][0]['en']  # Using English name
    
    # Iterate over the coordinates to gather stops within this line
    for coord_segment in line['coords']:
        for stop in df['metro']['stops']:
            # Match the stop coordinates to the line coordinates (this might need more logic)
            stop_location = [float(stop['stop_lat']), float(stop['stop_lon'])]  # Extract lat and lon
            
            # Find the stop name in English (if available)
            stop_name = next((s['translation'] for s in stop['stop'] if s['language'] == 'en'), '')
            
            # Create the df for each stop
            metro_stops_list.append({
                'stop_name': stop_name,
                'location': stop_location,
                'route_color': line_color,  # Line's color
                'route_name': line_name,    # Line's name
            })

# Extract unique stop names from metro_stops_list
unique_stop_names = list({stop['stop_name'] for stop in metro_stops_list})

# Title of the dashboard
st.title('Riyadh Traffic Data Analysis Dashboard')

# Directly load the CSV files
# Make sure to replace these file paths with your actual file paths
file_paths = ['/Users/khalid/Desktop/Work/Traffic Analysis/google maps/riyadh_traffic_analysis.csv']

# Read the CSV file into a dataframe
df_traffic = pd.read_csv(file_paths[0])

# Initialize the dataframe with the traffic data
filtered_df = df_traffic

# 1. Filter by specific column ('Origin') with an "All" option
column_name = 'Origin'  # Hardcode the column to 'origin'
if column_name in filtered_df.columns:
    unique_values = ['All'] + list(filtered_df[column_name].unique())  # Add 'All' option
    selected_value = st.selectbox(f"Select value to filter by {column_name}", unique_values, index=0)
    
    if selected_value != 'All':
        filtered_df = filtered_df[filtered_df[column_name] == selected_value]
else:
    st.write(f"Column '{column_name}' not found in the dataframe.")

# 2. Filter the boolean column 'Transit is Faster'
if 'Transit is Faster' in filtered_df.columns:
    transit_faster_option = st.radio(
        "Filter by 'Transit is Faster'",
        options=["True", "False"],
        index=0  # Default to "True"
    )
    # Convert radio button selection to boolean
    if transit_faster_option == "True":
        filtered_df = filtered_df[filtered_df['Transit is Faster'] == True]
    else:
        filtered_df = filtered_df[filtered_df['Transit is Faster'] == False]
else:
    st.write("Column 'Transit is Faster' not found in the dataframe.")

# 3. Filter numerical columns (for two columns: 'Driving Distance (KM)' and 'Transit Percentage Faster')
numeric_columns = ['Driving Distance (KM)', 'Transit Percentage Faster']

# Initialize the filtered dataframe
if any(col in filtered_df.columns for col in numeric_columns):
    # Filter for 'Driving Distance (KM)'
    if 'Driving Distance (KM)' in filtered_df.columns:
        min_distance = filtered_df['Driving Distance (KM)'].min()
        max_distance = filtered_df['Driving Distance (KM)'].max()
        distance_range = st.slider(
            "Select range for Driving Distance (KM)",
            min_distance, max_distance,
            (min_distance, max_distance)  # Default range is the full range
        )
        filtered_df = filtered_df[(filtered_df['Driving Distance (KM)'] >= distance_range[0]) & 
                                  (filtered_df['Driving Distance (KM)'] <= distance_range[1])]

    # Filter for 'Transit Percentage Faster'
    if 'Transit Percentage Faster' in filtered_df.columns:
        min_transit = filtered_df['Transit Percentage Faster'].min()
        max_transit = filtered_df['Transit Percentage Faster'].max()
        transit_range = st.slider(
            "Select range for Transit Percentage Faster",
            min_transit, max_transit,
            (min_transit, max_transit)  # Default range is the full range
        )
        filtered_df = filtered_df[(filtered_df['Transit Percentage Faster'] >= transit_range[0]) & 
                                  (filtered_df['Transit Percentage Faster'] <= transit_range[1])]
else:
    st.write("One or both of the numerical columns ('Driving Distance (KM)', 'Transit Percentage Faster') are not available for filtering.")

# Display the filtered dataframe
st.write("Filtered Dataframe after applying the selected ranges:")
st.dataframe(filtered_df)

if not filtered_df.empty:
    # Allow the user to select origin and destination from the filtered dataframe
    origin_name = st.selectbox("Select Origin", filtered_df['Origin'].unique())
    destination_name = st.selectbox("Select Destination", filtered_df['Destination'].unique())

    # Get the coordinates for the origin and destination
    origin_coords = get_coordinates_from_stop_name(origin_name)
    destination_coords = get_coordinates_from_stop_name(destination_name)

    if origin_coords and destination_coords:
        # Create a map centered around the origin
        map_center = origin_coords  # Center the map at the origin location
        m = folium.Map(location=map_center, zoom_start=12)

        # Add markers for the origin and destination
        folium.Marker(location=origin_coords, popup=f"Origin: {origin_name}", icon=folium.Icon(color='green')).add_to(m)
        folium.Marker(location=destination_coords, popup=f"Destination: {destination_name}", icon=folium.Icon(color='red')).add_to(m)

        # Draw a line between the origin and destination
        folium.PolyLine([origin_coords, destination_coords], color='blue', weight=2.5, opacity=1).add_to(m)

        # Display the map in Streamlit using HTML rendering
        st.write("Route between Origin and Destination:")
        map_html = m._repr_html_()  # Get the map as HTML
        components.html(map_html, height=500)  # Display the map
    else:
        st.write("Coordinates for Origin or Destination not found.")
else:
    st.write("No data available for mapping.")
