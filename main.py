import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import base64

# Function to convert DataFrame to GeoDataFrame with Point geometries
def create_geodataframe(dataframe):
    geometry = [Point(xy) for xy in zip(dataframe.longitude, dataframe.latitude)]
    return gpd.GeoDataFrame(dataframe, geometry=geometry)

# Function to create a download link for a GeoDataFrame as a shapefile
def download_shapefile(geodataframe, filename="download_shapefile"):
    with st.spinner("Converting to shapefile..."):
        temp_path = filename + ".shp"
        geodataframe.to_file(temp_path, driver='ESRI Shapefile')
    with open(temp_path, "rb") as f:
        shapefile_bytes = f.read()
    b64 = base64.b64encode(shapefile_bytes).decode()
    href = f'<a href="data:application/zip;base64,{b64}" download="{filename}.zip">Download {filename}.zip</a>'
    return href

# Streamlit app
def main():
    st.title("CSV to Shapefile Converter")

    # Upload CSV file
    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

    if uploaded_file is not None:
        # Read CSV file into a Pandas DataFrame
        df = pd.read_csv(uploaded_file)

        # Display the uploaded data
        st.subheader("Uploaded Data:")
        st.dataframe(df)

        # Convert DataFrame to GeoDataFrame with Point geometries
        gdf = create_geodataframe(df)

        # Display the GeoDataFrame
        st.subheader("Data with Geometry:")
        st.map(gdf)

        # Download shapefile
        st.markdown(download_shapefile(gdf, filename="shapefile_conversion"), unsafe_allow_html=True)

# Run the app
if __name__ == "__main__":
    main()

