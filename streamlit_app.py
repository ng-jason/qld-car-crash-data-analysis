import streamlit as st
from streamlit_folium import folium_static
import altair as alt
import pandas as pd
import math
import folium
from folium import Marker
from folium.plugins import MarkerCluster, Fullscreen

st.set_page_config(layout='wide')

st.header("QLD Car Crash Data Visualisation")
st.write("""
[Crash data from Queensland roads](https://www.data.qld.gov.au/dataset/crash-data-from-queensland-roads) contains data about road crash locations, road casualties, driver demographics, seatbelt restraits and helmet use, vehicle types and factors in road crashes.
""")

left_col, right_col = st.columns(2)


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

    for idx, row in data[:100].iterrows():
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

with left_col:
    year = st.select_slider(
                "Select year to visualise data:",
                options=range(rcl.Crash_Year.min(), rcl.Crash_Year.max()+1)
                )
    
    rcl_year = rcl[rcl.Crash_Year == year]

    
    st.write(f"Roads with the most crashes in **{year}** were", 
             (rcl_year.groupby('Crash_Street').size().reset_index(name='Count').
                      sort_values(by='Count', ascending=False)[:10])
            )


    # total crash count each year chart
    total_year = rcl.groupby('Crash_Year').size().reset_index(name='Count')
    chart = alt.Chart(total_year).mark_bar().encode(
        x='Crash_Year:O',  # https://altair-viz.github.io/user_guide/encoding.html#encoding-data-types
        y='Count'
    ).properties(title='Total crash count each year')
    st.altair_chart(chart, use_container_width=True)

    # data.head()
    st.write("First five rows of data", rcl[rcl['Crash_Year'] == year].head())
    
    

with right_col:
    
    
    m = make_map(year)

    folium_static(m)

