# Locker Coverage Model

This project is a **quick and dirty analysis** of population data designed to help develop a delivery locker network. It is a portfolio project that demonstrates how to combine geospatial data with population metrics to forecast infrastructure requirements.

The application models locker distribution based on three primary metrics:
1.  **Population-based:** Lockers per 1,000 people.
2.  **Area-based:** Spatial coverage using a defined radius and packing factor.
3.  **Capacity-based:** Estimated parcel volume based on adoption rates and visits per week.

## Features

-   **Interactive Dashboard:** Built with Streamlit for real-time parameter adjustment.
-   **Geospatial Visualization:** Uses Folium and Streamlit-Folium to display results on an interactive map of UK Local Authority Districts.
-   **Rural/Urban Classification:** Applies different forecasting logic depending on population density.
-   **Data Merging:** Combines population statistics, area measurements, and district boundaries.

## Getting Started

### Prerequisites

Ensure you have Python installed. You can install the required dependencies using:

```bash
pip install -r requirements.txt
```

### Running the Application

To launch the Streamlit dashboard, run:

```bash
streamlit run main.py
```

## Data Sources

The project utilizes several datasets (included as CSV and GeoJSON files):
-   `Population_by_district.csv`: UK population data by district.
-   `Standard_Area_Measurements...`: Land area measurements for Local Authority Districts.
-   `Local_Authority_Districts...csv`: Boundary centroids and names.
-   `LAD_simplified.geojson`: Simplified geospatial boundaries for mapping.

## Note
This tool is intended as a high-level modeling exercise and uses simplified assumptions for "quick and dirty" strategic planning.
