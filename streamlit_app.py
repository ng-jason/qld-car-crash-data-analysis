import streamlit as st
from streamlit_folium import folium_static
import altair as alt
import pandas as pd
import numpy as np
import math
import folium
from folium import Marker
from folium.plugins import MarkerCluster, Fullscreen

# this was done after the jupyter notebook so most code below is from there

st.set_page_config()

@st.cache
def get_data():
    rcl_url = 'https://www.data.qld.gov.au/dataset/f3e0ca94-2d7b-44ee-abef-d6b06e9b0729/resource/e88943c0-5968-4972-a15f-38e120d72ec0/download/1_crash_locations.csv'
    rcl = pd.read_csv(rcl_url)
    return rcl

@st.cache
def subset_data(data, year=2020, suburb=None, street=None, ignore_property=True):
    if ignore_property:
        data = data[data['Crash_Severity'] != 'Property damage only']

    if year:
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
    return data

# https://github.com/python-visualization/folium/tree/master/examples
@st.cache(allow_output_mutation=True)
def make_map(map_data):
    
    brisbane = [-27.467778, 153.028056]
    m = folium.Map(location=brisbane,
               zoom_start=7,
               tiles="CartoDB positron")
    
    # add stuff
    Fullscreen(position="topright", force_separate_button=True).add_to(m)

    # add marker cluster
    mc = MarkerCluster()
    # TODO: try use FastMarkerCluster
    
    for idx, row in map_data.iterrows():
        if not np.isnan(row.Crash_Latitude_GDA94) and \
            not np.isnan(row.Crash_Longitude_GDA94):
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
            if row.Crash_Severity == 'Fatal':
                icon_color = 'red'
            elif row.Crash_Severity == 'Hospitalisation' or row.Crash_Severity == 'Minor injury':
                icon_color = 'orange'
            else:
                icon_color = 'beige'
            mc.add_child(Marker([row.Crash_Latitude_GDA94, row.Crash_Longitude_GDA94], 
                                popup=popup,
                                icon=folium.Icon(color=icon_color)
                               )
                        )
    
    # adds marker cluster to map
    m.add_child(mc)
    
    return m

rcl = get_data()


# sidebar
with st.sidebar:
    st.header("QLD Car Crash Data Visualisation")
    st.write("""
    [Crash data from Queensland roads](https://www.data.qld.gov.au/dataset/crash-data-from-queensland-roads) contains data about road crash locations, road casualties, driver demographics, seatbelt restraits and helmet use, vehicle types and factors in road crashes.
    """)

    with st.form(key='my_form'):
        year = st.selectbox(
                    "Select year to visualise data:",
                    options=list(range(2020, 2000, -1))
                    )

        suburb = st.selectbox("Select suburb", 
                                options=[None] +  rcl['Loc_Suburb'].unique().tolist()
                                )

        street = st.selectbox("Select street", 
                                    options=[None] + rcl['Crash_Street'].unique().tolist()
                                    )

        property_only = st.checkbox("Ignore property damage only crashes", 
                            value=True)

        update_button = st.form_submit_button(label='Update map')


st.sidebar.write("""
In the map:
- light orange icon means crash resulted in property damage or medical treatment,
- orange icon means crash resulted in minor injury or hospitalisation, and
- red icon means crash resulted in fatality

More analysis is done here:
https://github.com/ng-jason/qld-car-crash-data-analysis
""")



if property_only:
    rcl = rcl[rcl['Crash_Severity'] != 'Property damage only']

# visualise data on a map
st.write("""
### Map visualisation of road crash locations
""")

map_data = subset_data(rcl, year, suburb, street, property_only)
m = make_map(map_data)
folium_static(m)



# left_col, right_col = st.columns(2)

st.write("""
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
st.write("First five rows of data", rcl[rcl['Crash_Year'] == year].head())

    



