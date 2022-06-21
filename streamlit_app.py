import streamlit as st
from streamlit_folium import folium_static
import altair as alt
import pandas as pd
import numpy as np
import math
import folium
from folium import Marker
from folium.plugins import MarkerCluster, Fullscreen

st.set_page_config()

@st.cache
def get_data():
    # Function to get road crash locations dataset
    # NOTE: url for dataset may change each year
    rcl_url = 'https://www.data.qld.gov.au/datastore/dump/e88943c0-5968-4972-a15f-38e120d72ec0?bom=True'
    rcl = pd.read_csv(rcl_url)
    return rcl

@st.cache
def subset_data(data, year=2021, 
                      suburb=None, 
                      street=None, 
                      severity=None, 
                      ignore_property=True):
    """Subset data given year, suburb and street

    Args:
        data (pd.DataFrame): 
        year (int, optional): Defaults to None.
        suburb (str, optional): Defaults to None.
        street (str, optional): Defaults to None.

    Returns:
        pd.DataFrame: data filtered by given arguments
    """
    if ignore_property:
        data = data[data['Crash_Severity'] != 'Property damage only']

    if year:
        if year != 'All (note: may be very slow)':
            data = data[data['Crash_Year'] == year]

    if suburb:
        try:
            data = data[data['Loc_Suburb'] == suburb]
        except:
            print(f"{suburb} not found")

    if street:
        try:
            data = data[data['Crash_Street'] == street]
        except:
            print(f"{street} not found")

    if severity:
        data = data[data['Crash_Severity'] == severity]

    return data

# https://github.com/python-visualization/folium/tree/master/examples
@st.cache(allow_output_mutation=True)
def make_map(map_data):
    """Creates folium map with Markers and MarkerClusters with popup text containing crash data info

    Args:
        map_data (pd.DataFrame): data from the road crash locations dataset to create map of

    Returns:
        folium Map object
    """

    brisbane = [-27.467778, 153.028056]
    m = folium.Map(location=brisbane,
               zoom_start=7,
               tiles="CartoDB positron")
    
    # add stuff
    Fullscreen(position="topright", force_separate_button=True).add_to(m)

    # add marker cluster
    mc = MarkerCluster()
    
    for idx, row in map_data.iterrows():
        # plot data points that have both latitude/longitude 
        if not np.isnan(row.Crash_Latitude) and \
            not np.isnan(row.Crash_Longitude):
            # display selected data to show in popuptext
            popuptext = f"Crash time: Hour = {row.Crash_Hour}, {row.Crash_Day_Of_Week} {row.Crash_Month} {row.Crash_Year}<br>\
                    Crash Severity: {row.Crash_Severity}<br>\
                    Crash Type: {row.Crash_Type}<br>\
                    Crash Street Location: {row.Crash_Street} {row.Loc_Suburb} {row.Loc_Post_Code}<br>\
                    Crash Street Intersecting: {row.Crash_Street_Intersecting if not math.nan else 'None'}<br>\
                    Local Government Area: {row.Loc_Local_Government_Area}<br>\
                    Speed Limit: {row.Crash_Speed_Limit}<br>\
                    Casualty Total: {row.Count_Casualty_Total}<br>\
                    Fatality Total: {row.Count_Casualty_Fatality}<br>\
                    Crash Ref Number: {row.Crash_Ref_Number}"
            popup = folium.Popup(popuptext, min_width=300, max_width=500)

            # colour the marker depending on crash severity
            if row.Crash_Severity == 'Fatal':
                icon_color = 'red'
            elif row.Crash_Severity == 'Hospitalisation' or row.Crash_Severity == 'Minor injury':
                icon_color = 'orange'
            else:
                icon_color = 'beige'
            
            # finally add Marker to MarkerCluster
            mc.add_child(Marker([row.Crash_Latitude, row.Crash_Longitude], 
                                popup=popup,
                                icon=folium.Icon(color=icon_color)
                               )
                        )
    
    # adds marker cluster to map
    m.add_child(mc)
    
    return m

rcl = get_data()


####### sidebar #######
with st.sidebar:
    st.header("QLD Car Crash Data Visualisation")
    st.write("""
    [Crash data from Queensland roads](https://www.data.qld.gov.au/dataset/crash-data-from-queensland-roads) contains data about road crash locations, road casualties, driver demographics, seatbelt restraints and helmet use, vehicle types and factors in road crashes.
    """)


    with st.form(key='my_form'):
        year = st.selectbox(
                    "Select year to visualise data:",
                    options=['All (note: may be very slow)'] + list(range(2021, 2000, -1)),
                    index=1
                    )

        suburb = st.selectbox("Select suburb", 
                                options=[None] +  rcl['Loc_Suburb'].unique().tolist()
                                )

        street = st.selectbox("Select street", 
                                    options=[None] + rcl['Crash_Street'].unique().tolist()
                                    )
        
        severity = st.selectbox("Select crash severity", 
                                    options=[None] + rcl['Crash_Severity'].unique().tolist()
                                    )

        property_only = st.checkbox("Ignore property damage only crashes", 
                            value=True)

        update_button = st.form_submit_button(label='Update map')


st.sidebar.write("""
In the map:
- yellow marker means crash resulted in: `property damage` or `medical treatment`,
- orange marker means crash resulted in: `minor injury` or `hospitalisation`, and
- red marker means crash resulted: in `fatality`
- click on circles to zoom in

More analysis is available here:
https://github.com/ng-jason/qld-car-crash-data-analysis
""")



if property_only:
    rcl = rcl[rcl['Crash_Severity'] != 'Property damage only']



####### start of map viz page #######

# col1, col2 = st.columns(2)

# with col1:
# for some reason the folium_static map won't go into the col
# visualise data on a map
st.write("""
### Map visualisation of road crash locations
""")

map_data = subset_data(rcl, year, suburb, street, severity, property_only)
m = make_map(map_data)
folium_static(m)

# with col2:
st.write("""
---
### Below are some graphs for the selected year/suburb/street
""")

# Crash severity
@st.cache(allow_output_mutation=True)
def get_crash_severity(map_data):
    crash_severity = map_data['Crash_Severity'].value_counts().reset_index(name='Count')

    return alt.Chart(crash_severity).mark_bar().encode(
        x='Count',
        y=alt.Y('index:O', title='Crash Severity', sort='-x')
    ).properties(title="Crash Severity percentage")

st.altair_chart(get_crash_severity(map_data), use_container_width=True)

# top crash roads
@st.cache(allow_output_mutation=True)
def get_top_crash_roads(map_data):
    roads = map_data.groupby('Crash_Street').size().reset_index(name='Count')
    roads = roads.sort_values(by='Count', ascending=False)

    return alt.Chart(roads.head(10)).mark_bar().encode(
                                x='Count',
                                y=alt.Y('Crash_Street:O', sort='-x') 
    ).properties(title=f"Street with the most car crashes in {street or ''} {suburb or ''} {year or ''}")

st.altair_chart(get_top_crash_roads(map_data), use_container_width=True)

# crash day of week
@st.cache(allow_output_mutation=True)
def crash_per_day(map_data):
    day_of_weeks = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    crash_per_day = map_data.groupby('Crash_Day_Of_Week').size().reset_index(name='Count')

    return alt.Chart(crash_per_day).mark_bar().encode(
        x=alt.X('Crash_Day_Of_Week', sort=day_of_weeks),
        y='Count'
    ).properties(title=f"Number of crashes per day of the week in {street or ''} {suburb or ''} {year or ''}")

st.altair_chart(crash_per_day(map_data), use_container_width=True)


# top crash hours
@st.cache(allow_output_mutation=True)
def crash_per_hour(map_data):
    crash_per_hour = map_data.groupby('Crash_Hour').size().reset_index(name='Count')

    return alt.Chart(crash_per_hour).mark_bar(opacity=0.7).encode(
        x='Crash_Hour:O',
        y='Count'
    ).properties(title=f"Number of crashes per hour of the day in {street or ''} {suburb or ''} {year or ''}")

st.altair_chart(crash_per_hour(map_data), use_container_width=True)


# st.write("""
# ### Below are graphs for the whole data
# """)
# # statistics for whole data

# # total crash count each year chart
# total_year = rcl.groupby('Crash_Year').size().reset_index(name='Count')
# chart = alt.Chart(total_year).mark_bar().encode(
#     x='Crash_Year:O',  # https://altair-viz.github.io/user_guide/encoding.html#encoding-data-types
#     y='Count'
# ).properties(title='Total crash count each year')
# st.altair_chart(chart, use_container_width=True)

# data.head()

st.write("""
---
First five rows of data""", 
rcl[rcl['Crash_Year'] == year].head())
