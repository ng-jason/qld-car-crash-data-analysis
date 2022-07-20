from matplotlib.pyplot import text
import streamlit as st
from streamlit_folium import folium_static
import altair as alt
import pandas as pd
import numpy as np
import math
import folium
from folium import Marker
from folium.plugins import MarkerCluster, Fullscreen

st.set_page_config(page_title='QLD Road Crash Location Visualisation',
                   layout='wide')

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

    m = folium.Map(tiles="CartoDB positron")
    
    # add Fullscreen button
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

    # fit map to contain all points from https://stackoverflow.com/a/58185815/11065894
    sw = map_data[['Crash_Latitude', 'Crash_Longitude']].min().values.tolist()
    ne = map_data[['Crash_Latitude', 'Crash_Longitude']].max().values.tolist()
    m.fit_bounds([sw, ne])
    
    return m

rcl = get_data()


####### sidebar #######
with st.sidebar:
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

Code: https://github.com/ng-jason/qld-car-crash-data-analysis
""")



if property_only:
    rcl = rcl[rcl['Crash_Severity'] != 'Property damage only']



####### start of map viz page #######
st.header("QLD Road Crash Location Visualisation")

col1, col2 = st.columns(2)

with col1:
    # visualise data on a map
    map_data = subset_data(rcl, year, suburb, street, severity, property_only)
    m = make_map(map_data)
    folium_static(m)

    # top crash roads
    def get_top_crash_roads(map_data):
        roads = map_data.groupby('Crash_Street').size().reset_index(name='Count')
        roads = roads.sort_values(by='Count', ascending=False)

        return alt.Chart(roads.head(10)).mark_bar().encode(
            x='Count',
            y=alt.Y('Crash_Street:O', sort='-x'),
            tooltip='Count'
        ).properties(
            title=f"Roads with the most car crashes in {street or ''} {suburb or ''} {year or ''}"
        )

    st.altair_chart(get_top_crash_roads(map_data), use_container_width=True)

with col2:

    # Crash severity
    def get_crash_severity(map_data):
        crash_severity = map_data['Crash_Severity'].value_counts(normalize=True).reset_index()

        crash_severity.columns = ['Crash_Severity', 'Percentage']
        
        chart = alt.Chart(crash_severity).mark_arc().encode(
            theta='Percentage',
            color='Crash_Severity',
            tooltip=['Percentage']
        ).properties(title="Crash Severity")
        return chart

    st.altair_chart(get_crash_severity(map_data), use_container_width=True)


    # crash day of week
    def crash_per_day(map_data):
        day_of_weeks = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        crash_per_day = map_data.groupby('Crash_Day_Of_Week').size().reset_index(name='Count')

        return alt.Chart(crash_per_day).mark_bar().encode(
            x=alt.X('Crash_Day_Of_Week', sort=day_of_weeks),
            y='Count',
            tooltip='Count'
        ).properties(title=f"Number of crashes per day of the week in {street or ''}{suburb or ''} {year or ''}")

    st.altair_chart(crash_per_day(map_data), use_container_width=True)


    # top crash hours
    def crash_per_hour(map_data):
        crash_per_hour = map_data.groupby('Crash_Hour').size().reset_index(name='Count')

        return alt.Chart(crash_per_hour).mark_bar().encode(
            x='Crash_Hour:O',
            y='Count',
            tooltip='Count'
        ).properties(title=f"Number of crashes per hour of the day in {street or ''} {suburb or ''} {year or ''}")

    st.altair_chart(crash_per_hour(map_data), use_container_width=True)


st.write("""
---
First five rows of data""", 
rcl[rcl['Crash_Year'] == year].head())
