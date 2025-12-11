"""
Name: Victoria Korbačková
CS230: Final Project
Data: NJ Maritime Museum Shipwreck Database
Section: CS230-2
Dataset: Shipwrecks_clean.csv
URL: https://interactive-data-explorer-shipwrecks.streamlit.app/
Description:
This Streamlit application allows interactive exploration of shipwrecks in New Jersey.
Users can filter shipwrecks by year, vessel type, cause of loss, and draft (depth),
and visualize patterns over time with charts and maps. Queries supported:
1. Trends of shipwrecks over time.
2. Vessel type distribution and top 10 vessel types.
3. Causes of shipwrecks and geographic distribution.
4. Depth (draft) distribution.

References:
- Streamlit Docs: https://docs.streamlit.io
- PyDeck Docs: https://pydeck.gl/
- Pandas Docs: https://pandas.pydata.org/docs/
"""

import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import matplotlib.pyplot as plt
import re


# Mapbox token
mapbox_token = "pk.eyJ1Ijoic2ltbWlrIiwiYSI6ImNtaXNlbnMwcjE3d28zZm9ueGVyc3E3OXcifQ.ZIlAjWR2eZU5S3ZtLuqoHQ"  # Replace if needed
pdk.settings.mapbox_api_key = mapbox_token

# ------------------------
# Functions
# ------------------------

# #[APPLY] Convert DMS strings to decimal degrees
def dms_to_decimal(coord):
    if pd.isnull(coord):
        return None
    match = re.match(r"(\d+)-(\d+)-(\d+)\s*([NSEW]?)", str(coord))
    if not match:
        return None
    deg, minutes, sec, direction = match.groups()
    decimal = float(deg) + float(minutes)/60 + float(sec)/3600
    if direction in ['S', 'W']:
        decimal = -decimal
    return decimal


# Load and preprocess data
@st.cache_data
def load_data():
    df = pd.read_csv("Shipwrecks_clean.csv")
    # #[COLUMNS] Add lat/lon columns from DMS conversion
    df["lat"] = df["LATITUDE"].apply(dms_to_decimal)
    df["lon"] = df["LONGITUDE"].apply(dms_to_decimal)
    return df




def filter_by_year_and_type(data, start_year, end_year, vessel_type=None):
    # #[FILTER2] Filter by multiple conditions: year and vessel type
    filtered = data[(data["YEAR"] >= start_year) & (data["YEAR"] <= end_year)]
    if vessel_type and vessel_type != "All":
        filtered = filtered[filtered["VESSEL TYPE"] == vessel_type]
    return filtered

def compute_summary_stats(data):
    # #[MAXMIN] Compute min/max years and total shipwrecks
    total = len(data)
    earliest = data["YEAR"].min()
    latest = data["YEAR"].max()
    return total, earliest, latest


# Sidebar Filters
df = load_data()

st.sidebar.header("Filters")

# Vessel type dropdown
vessel_types = ["All"] + sorted(df["VESSEL TYPE"].dropna().unique().tolist())
selected_type = st.sidebar.selectbox("Select Vessel Type", vessel_types)

# Year range slider
min_year = int(df["YEAR"].min())
max_year = int(df["YEAR"].max())
year_range = st.sidebar.slider("Select Year Range", min_year, max_year, (min_year, max_year))

# Cause of loss multiselect
causes = df["CAUSE OF LOSS"].dropna().unique().tolist()
selected_causes = st.sidebar.multiselect("Select Causes of Loss", causes)

# Max draft (depth) slider
max_depth = st.sidebar.slider("Select Maximum Draft (Depth)", 0, int(df["DRAFT"].max()), int(df["DRAFT"].max()))

# Apply filters
start_year, end_year = year_range
filtered_df = filter_by_year_and_type(df, start_year, end_year, selected_type)

if selected_causes:
    filtered_df = filtered_df[filtered_df["CAUSE OF LOSS"].isin(selected_causes)]

filtered_df = filtered_df[filtered_df["DRAFT"] <= max_depth]


# ------------------------
# Summary stats
# ------------------------
summary_total, summary_earliest, summary_latest = compute_summary_stats(filtered_df)


# ------------------------
# Page Title
# ------------------------
st.title("NJ Maritime Museum Shipwreck Explorer")
st.write(f"Showing {int(summary_total)} shipwrecks between {int(summary_earliest)} and {int(summary_latest)}.")

# ------------------------
# Display filtered table
# ------------------------
st.subheader("Filtered Shipwreck Records")
st.dataframe(filtered_df)

# ------------------------
# #[CHART1] Shipwrecks over time (Line chart)
# ------------------------
st.subheader("Shipwrecks Over Time")
year_counts = filtered_df["YEAR"].value_counts().sort_index()  # #[SORT]
fig, ax = plt.subplots()
ax.plot(year_counts.index, year_counts.values, color="navy", marker='o')
ax.set_title("Shipwreck Count by Year")
ax.set_xlabel("Year")
ax.set_ylabel("Count")
st.pyplot(fig)


# ------------------------
# #[CHART2] Top 10 Vessel Types + Others (Bar chart)
# ------------------------
st.subheader("Top 10 Vessel Types by Shipwreck Count (Others grouped)")
vessel_counts = filtered_df["VESSEL TYPE"].value_counts()
top_10 = vessel_counts.head(10)
others_count = vessel_counts[10:].sum()
top_10_with_others = pd.concat([top_10, pd.Series({"Others": others_count})])

fig2, ax2 = plt.subplots()
ax2.bar(top_10_with_others.index, top_10_with_others.values, color="orange")
ax2.set_xlabel("Vessel Type")
ax2.set_ylabel("Count")
ax2.set_title("Top 10 Vessel Types by Shipwrecks")
plt.xticks(rotation=45, ha='right')
st.pyplot(fig2)


# ------------------------
# Depth histogram
# ------------------------
st.subheader("Depth Distribution")
fig3, ax3 = plt.subplots()
ax3.hist(filtered_df["DRAFT"].dropna(), bins=20, color="teal")
ax3.set_title("Draft (Depth) Histogram")
ax3.set_xlabel("Draft (Feet)")
ax3.set_ylabel("Frequency")
st.pyplot(fig3)

# Pivot table
st.subheader("Shipwrecks by Cause and Vessel Type (Pivot Table)")
pivot_table = pd.pivot_table(
    filtered_df,
    index="CAUSE OF LOSS",
    columns="VESSEL TYPE",
    values="SHIP'S NAME",
    aggfunc="count",
    fill_value=0
)
st.dataframe(pivot_table)

# ------------------------
# PyDeck Map
# ------------------------
st.subheader("Shipwreck Map")

# Prepare data for map
map_data = filtered_df[["lat", "lon", "DRAFT", "CAUSE OF LOSS", "VESSEL TYPE", "SHIP'S NAME", "YEAR"]].dropna(subset=["lat", "lon"])

# Ensure DRAFT is numeric and fill missing
map_data["DRAFT"] = pd.to_numeric(map_data["DRAFT"], errors="coerce").fillna(10)

# Marker radius: avoid zero or negative values
map_data["marker_radius"] = map_data["DRAFT"].apply(lambda x: max(x*1000, 5000))

# PyDeck layer: simpler color mapping
cause_colors = {cause: [np.random.randint(0,255), np.random.randint(0,255), np.random.randint(0,255)] for cause in map_data["CAUSE OF LOSS"].unique()}
map_data["color_rgb"] = map_data["CAUSE OF LOSS"].map(cause_colors)

deck = pdk.Deck(
    map_style="mapbox://styles/mapbox/light-v10",
    initial_view_state=pdk.ViewState(
        latitude=39.5,
        longitude=-74.5,
        zoom=7,
        pitch=0,
    ),
    layers=[
        pdk.Layer(
            "ScatterplotLayer",
            data=map_data,
            get_position=["lon", "lat"],  
            get_radius="marker_radius",
            get_fill_color="color_rgb",
            pickable=True,
            auto_highlight=True,
        )
    ],
    tooltip={
        "html": "<b>Ship Name:</b> {SHIP'S NAME} <br/>"
                "<b>Year Lost:</b> {YEAR} <br/>"
                "<b>Cause:</b> {CAUSE OF LOSS} <br/>"
                "<b>Draft:</b> {DRAFT} ft",
        "style": {"color": "white"}
    }
)

st.pydeck_chart(deck)


# ------------------------
# Plotly Express Scatter (fixed)
# ------------------------
import plotly.express as px

fig = px.scatter_geo(
    map_data,
    lat="lat",
    lon="lon",
    color="CAUSE OF LOSS",   
    hover_name="SHIP'S NAME",
    size="DRAFT",         
    projection="natural earth",
    title="NJ Shipwreck Locations",
)

fig.update_geos(
    showcountries=True,
    showcoastlines=True,
    coastlinecolor="RebeccaPurple",
    showland=True,
    landcolor="LightGreen",
    showocean=True,
    oceancolor="LightBlue",
    projection_type="natural earth"
)

fig.update_traces(marker=dict(sizemode='area', sizeref=0, line=dict(width=0.5, color='black')))
fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
st.plotly_chart(fig, use_container_width=True)


# Filter out rows without coordinates
map_df = filtered_df.dropna(subset=['LAT', 'LON']).copy()

# Replace NaN in '# CREW' with 1 for sizing
map_df['# CREW'] = map_df['# CREW'].fillna(1)

# Create interactive map
fig = px.scatter_mapbox(
    map_df,
    lat='LAT',
    lon='LON',
    hover_name="SHIP'S NAME",
    hover_data={
        "VESSEL TYPE": True,
        "DATE LOST": True,
        "CAUSE OF LOSS": True,
        "MASTER": True,
        "# CREW": True,
        "# PASS": True,
        "LIVES LOST": True
    },
    color='VESSEL TYPE',   
    size='# CREW',        
    size_max=15,
    zoom=3,
    height=600
)

# Map style
fig.update_layout(
    mapbox_style="open-street-map",
    margin={"r":0,"t":0,"l":0,"b":0}
)

# Display in Streamlit
st.plotly_chart(fig, use_container_width=True)
