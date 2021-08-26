import streamlit as st
from streamlit_folium import folium_static
import pandas as pd
import math
import folium
from folium import Marker
from folium.plugins import MarkerCluster, Fullscreen



st.header("QLD Car Crash Data Visualisation")
st.write("""
[Crash data from Queensland roads](https://www.data.qld.gov.au/dataset/crash-data-from-queensland-roads) contains data about road crash locations, road casualties, driver demographics, seatbelt restraits and helmet use, vehicle types and factors in road crashes.

This app aims to visualise the data. 
""")


@st.cache
def get_data():
    rcl_url = 'https://www.data.qld.gov.au/dataset/f3e0ca94-2d7b-44ee-abef-d6b06e9b0729/resource/e88943c0-5968-4972-a15f-38e120d72ec0/download/1_crash_locations.csv'
    rcl = pd.read_csv(rcl_url)
    return rcl


@st.cache(allow_output_mutation=True)
def make_map(year):
    assert year >= rcl.Crash_Year.min() and year <= rcl.Crash_Year.max()
    
    brisbane = [-27.467778, 153.028056]
    m = folium.Map(location=brisbane,
               zoom_start=7,
               tiles="CartoDB positron")
    
    Fullscreen(position="topright", force_separate_button=True).add_to(m)

    # add marker cluster
    mc = MarkerCluster()
    # TODO: try use FastMarkerCluster
    
    data = rcl[rcl['Crash_Year'] == year]

    for idx, row in data[:5].iterrows():
        if not math.isnan(row.Crash_Latitude_GDA94) and \
            not math.isnan(row.Crash_Longitude_GDA94):
            popuptext = f"Crash time: Hour = {row.Crash_Hour}, {row.Crash_Day_Of_Week} {row.Crash_Month} {row.Crash_Year}<br>\
                    Crash Severity: {row.Crash_Severity}<br>\
                    Crash Type: {row.Crash_Type}<br>\
                    Crash Street Location: {row.Crash_Street} {row.Loc_Suburb} {row.Loc_Post_Code}<br>\
                    Crash Street Intersecting: {row.Crash_Street_Intersecting if not math.nan else 'None'}<br>\
                    Local Government Area: {row.Loc_Local_Government_Area}<br>\
                    Speed Limit: {row.Crash_Speed_Limit}<br>\
                    Casualty Total: {row.Count_Casualty_Total}<br>\
                    Crash Ref Number: {row.Crash_Ref_Number}"
            popup = folium.Popup(popuptext, min_width=300, max_width=500)
            mc.add_child(Marker([row.Crash_Latitude_GDA94, row.Crash_Longitude_GDA94], popup=popup))
    
    # adds marker cluster to map
    m.add_child(mc)
    
    return m



rcl = get_data()

year = st.select_slider(
            "Select year to visualise data:",
            options=range(rcl.Crash_Year.min(), rcl.Crash_Year.max()+1)
            )

m = make_map(year)

folium_static(m)
