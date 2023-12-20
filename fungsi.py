import re
import string
import folium
import pandas as pd
import streamlit as st
import geopandas as gpd
from shapely.geometry import Point
from io import BytesIO

def read_file(file, separator=','):
    try:
        if file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file)
            return df, None  # No separator for Excel files
        elif file.name.endswith('.csv'):
            df = pd.read_csv(file, sep=separator)
            return df, separator
        else:
            st.error("Invalid file format. Please upload a valid XLS, XLSX, or CSV file.")
            return None, None
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None, None

def clean(value):
    value = re.sub(f'[{string.punctuation}]', '', value)
    value = value.lower()
    value = re.sub(r'\b(?:kab|kabupaten|kota)\b', '', value).strip()
    value = value.replace(' ','')
    return value

def map(dataframe, jenis_lokasi):
    map = folium.Map(location=[2.6438488227145, 99.04541708926384], zoom_start=8, tiles="cartodbpositron")
    dataframe = dataframe.dropna(subset=['Latitude', 'Longitude'], inplace=False)
    if jenis_lokasi == 'Kabupaten/Kota':
        data = dataframe.iloc[:,0]
    else:
         data = dataframe.Kecamatan
    for lat, lng, Kab in zip(dataframe.Latitude, dataframe.Longitude, data):
        folium.Marker(
            location=[lat, lng],
            icon=folium.Icon(color="red", icon="fire-extinguisher"),
            popup=Kab
        ).add_to(map)
    return map

def shorten_column_name(df, column_name, max_length=9):
    if len(column_name) <= max_length:
        return column_name
    else:
        base_name = column_name[:max_length - 1]
        counter = 1
        new_name = f"{base_name}{counter}"
        while new_name in df.columns:
            counter += 1
            new_name = f"{base_name}{counter}"
        return new_name

def create_shapefile(dataframe):
    dataframe.columns = [shorten_column_name(dataframe,col) for col in dataframe.columns]
    geometry = [Point(xy) for xy in zip(dataframe['Longitude'], dataframe['Latitude'])]
    gdf = gpd.GeoDataFrame(dataframe, crs='EPSG:4326', geometry=geometry)
    return gdf

def create_csv(dataframe):
    return dataframe.to_csv(sep='|', index=False).encode('utf-8')

def create_excel(dataframe):
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        dataframe.to_excel(writer, index=False)
    return excel_buffer