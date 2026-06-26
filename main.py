# app.py
import pandas as pd
import math
import streamlit as st
import folium
import json
from streamlit_folium import st_folium

pop_path = "Population_by_district.csv"
area_path = "Standard_Area_Measurements_for_the_Local_Authority_Districts_(December_2024)_in_the_United_Kingdom.csv"
centroid_path = "Local_Authority_Districts_DEC_2025_Boundaries_UK_BFC_-6066750386826267615.csv"

pop = pd.read_csv(pop_path, skiprows=7)
area = pd.read_csv(area_path)
centroids = pd.read_csv(centroid_path)

pop = pop.dropna(subset=["mnemonic", "2021"])
pop = pop.rename(columns={
    "mnemonic": "lad_code",
    "2021": "population"
})

area = area.rename(columns={
    "LAD24CD": "lad_code",
    "AREALHECT": "area_hectares"
})

centroids = centroids.rename(columns={
    "LAD25CD": "lad_code",
    "LAD25NM": "district_name",
    "LAT": "lat",
    "LONG": "lon"
})

df = (
    pop[["lad_code", "population"]]
    .merge(area[["lad_code", "area_hectares"]], on="lad_code", how="left")
    .merge(centroids[["lad_code", "district_name", "lat", "lon"]], on="lad_code", how="left")
)

df["area_km2"] = df["area_hectares"] / 100
df["population_per_km2"] = df["population"] / df["area_km2"]

st.title("Locker Coverage Model")

lockers_per_1000 = st.number_input("Lockers per 1000 people", value=1.2, min_value=0.0, step=0.1)
radius_km = st.number_input("Locker radius coverage km", value=1.0, min_value=0.1)

# New Inputs
visits_per_week = st.number_input("Locker visits per person per week", value=1.0, min_value=0.0, step=0.1)
adoption_pct = st.slider("Adoption Percentage", value=20, min_value=0, max_value=100)
locker_capacity = st.number_input("Locker capacity (parcels per day)", value=50, min_value=1)
packing_factor = st.slider("Packing factor (circular overlap)", value=1.2, min_value=1.0, max_value=2.0, step=0.05)
rural_threshold = st.slider("Rural threshold (people per km²)", value=350, min_value=0, max_value=1000, step=10)

coverage_area_km2 = math.pi * radius_km**2

if lockers_per_1000 > 0:
    people_per_locker = 1000 / lockers_per_1000
    df["lockers_by_population"] = df["population"] / people_per_locker
else:
    df["lockers_by_population"] = 0

df["lockers_by_area"] = (df["area_km2"] / coverage_area_km2) * packing_factor

# New Calculation: Capacity-based
df["lockers_by_capacity"] = (df["population"] * (adoption_pct / 100) * visits_per_week) / (locker_capacity * 7)

# Identify Rural vs Urban
df["classification"] = df["population_per_km2"].apply(lambda x: "Rural" if x < rural_threshold else "Urban")

# Forecasted: Average calculation depends on classification
def calculate_forecast(row):
    if row["classification"] == "Rural":
        # Only utilize capacity for rural areas
        return math.ceil(row["lockers_by_capacity"])
    else:
        # Average of all three for urban areas
        return math.ceil((row["lockers_by_population"] + row["lockers_by_area"] + row["lockers_by_capacity"]) / 3)

df["forecasted_lockers"] = df.apply(calculate_forecast, axis=1)

# New Calculation: Percentage of total forecasted
total_forecasted = df["forecasted_lockers"].sum()
if total_forecasted > 0:
    df["pct_of_total_forecasted"] = (df["forecasted_lockers"] / total_forecasted) * 100
else:
    df["pct_of_total_forecasted"] = 0

st.metric("Total lockers required (Forecasted)", int(df["forecasted_lockers"].sum()))
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total population-based", int(df["lockers_by_population"].sum()))
with col2:
    st.metric("Total area-based", int(df["lockers_by_area"].sum()))
with col3:
    st.metric("Total capacity-based", int(df["lockers_by_capacity"].sum()))

st.metric("Total population", int(df["population"].sum()))
st.metric("Total area km²", round(df["area_km2"].sum(), 1))

# Reorder columns for display
display_columns = [
    "district_name", 
    "classification",
    "forecasted_lockers", 
    "pct_of_total_forecasted",
    "lockers_by_population", 
    "lockers_by_area", 
    "lockers_by_capacity",
    "population",
    "area_km2",
    "population_per_km2"
]
# Ensure we only include columns that actually exist in df
actual_display_columns = [col for col in display_columns if col in df.columns]
st.dataframe(df[actual_display_columns])

m = folium.Map(location=[54.5, -2.5], zoom_start=6)

# Load simplified boundaries from the local GeoJSON
geojson_path = "LAD_simplified.geojson"
try:
    with open(geojson_path, "r") as f:
        geojson_data = json.load(f)
    
    # Merge data into GeoJSON
    data_dict = df.set_index("lad_code").to_dict(orient="index")
    for feature in geojson_data["features"]:
        code = feature["properties"].get("LAD25CD")
        if code in data_dict:
            feature["properties"].update(data_dict[code])
        else:
            # Initialize with default values if no data found
            feature["properties"].update({
                "population": 0,
                "area_km2": 0,
                "population_per_km2": 0,
                "classification": "Unknown",
                "lockers_by_population": 0,
                "lockers_by_area": 0,
                "lockers_by_capacity": 0,
                "forecasted_lockers": 0,
                "pct_of_total_forecasted": 0,
                "district_name": feature["properties"].get("LAD25NM", "Unknown")
            })

    folium.GeoJson(
        geojson_data,
        name="Boundaries",
        style_function=lambda x: {
            "color": "black",
            "weight": 1.5,
            "fillOpacity": 0.0,
        },
        highlight_function=lambda x: {"fillColor": "cyan", "fillOpacity": 0.5},
        tooltip=folium.GeoJsonTooltip(fields=["LAD25NM", "classification", "forecasted_lockers"], aliases=["District:", "Type:", "Forecasted Lockers:"]),
        popup=folium.GeoJsonPopup(
            fields=[
                "district_name", "classification", "population", "area_km2", "population_per_km2",
                "lockers_by_population", "lockers_by_area", "lockers_by_capacity", "forecasted_lockers", "pct_of_total_forecasted"
            ],
            aliases=[
                "District:", "Type:", "Population:", "Area (km²):", "Pop / km²:",
                "Lockers (Pop-based):", "Lockers (Area-based):", "Lockers (Capacity-based):", "Forecasted:", "% of Total:"
            ],
            localize=True
        )
    ).add_to(m)
except Exception as e:
    st.error(f"Error loading GeoJSON: {e}")

st_folium(m, width=1000, height=700)