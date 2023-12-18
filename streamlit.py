import streamlit as st
import pandas as pd
import re
import string
import folium
from streamlit_folium import st_folium
import geopandas as gpd
from shapely.geometry import Point
import tempfile
import os
import zipfile
from io import BytesIO

st.write('19-12-2023')

# Fungsi-Fungsi
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

def map(dataframe):
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

def shorten_column_name(column_name, max_length=9):
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

# Masukkan Dataset Awal
df_kabkota = pd.read_excel('Kabupaten_Kota.xlsx')
df_kecamatan = pd.read_excel('Kecamatan.xlsx')
df_keldesa = pd.read_excel('Kelurahan_Desa.xlsx')
df_kabkota['Selected_Processed'] = df_kabkota['Kabupaten/Kota'].apply(clean)
df_kecamatan['Selected_Processed'] = df_kecamatan['Kecamatan'].apply(clean)
df=None

st.title('Open Data Template')

# Upload File
uploaded_file = st.file_uploader("Pilih File !", type=["xls", "xlsx", "csv"])

if uploaded_file is not None:
    file_extension = uploaded_file.name.split('.')[-1].lower()
    if file_extension == 'csv':
        separator = st.text_input("CSV Separator (default is ',')", ',')
    else:
        separator = ','  # Default separator for non-CSV files
    df, _ = read_file(uploaded_file, separator)

show_input_data = st.checkbox("Lihat Data !")

if show_input_data and df is not None:
    st.dataframe(df)

# Cleaning Dataframe
if df is not None:
    list_column = df.columns.tolist()
    col1, col2 = st.columns(2)
    with col1:
        jenis_lokasi = st.selectbox('Pilih Jenis Lokasi !',('Kabupaten/Kota', 'Kecamatan'))
    with col2:
        kode_kemendagri = st.checkbox('Gunakan Kode Kemendagri ?')

    pemilihan_kolom = st.selectbox(f'Pilih Kolom {jenis_lokasi}', list_column)

    if jenis_lokasi == 'Kabupaten/Kota':
        df1 = df_kabkota
    else:
        df1 = df_kecamatan

    try:
        if kode_kemendagri is False:
            df['Selected_Processed'] = df[pemilihan_kolom].apply(clean)
            df = pd.merge(df, df1, left_on='Selected_Processed', right_on='Selected_Processed', how='left')
            df.drop(['Selected_Processed', pemilihan_kolom], axis=1, inplace=True)
        else:
            df = pd.merge(df, df1, left_on=pemilihan_kolom, right_on='Kode Kemendagri', how='left')
            df.drop(['Selected_Processed', pemilihan_kolom], axis=1, inplace=True)

        if jenis_lokasi == 'Kabupaten/Kota':
            column_order = list(df.columns[-5:-2]) + list(df.columns[:-5]) + ['Latitude', 'Longitude']
        else:
            column_order = list(df.columns[-6:-2]) + list(df.columns[:-6]) + ['Latitude', 'Longitude']
        df = df[column_order]
        st.dataframe(df)

        st_map = st_folium(map(df), width=725)

    except:
        st.warning('Anda Memasukkan Kolom yang salah!', icon="⚠️")

    col3, col4, col5 = st.columns(3)

    with col3:
        def create_shapefile(dataframe):
            dataframe.columns = [shorten_column_name(col) for col in dataframe.columns]
            geometry = [Point(xy) for xy in zip(dataframe['Longitude'], dataframe['Latitude'])]
            gdf = gpd.GeoDataFrame(dataframe, crs='EPSG:4326', geometry=geometry)
            return gdf
        df_gdf = df.copy()
        gdf = create_shapefile(df_gdf)
        temp_dir = tempfile.mkdtemp()
        gdf.to_file(temp_dir, driver='ESRI Shapefile')
        # Zip the files in the temporary directory
        zip_file_path = os.path.join(temp_dir, "output_shapefile.zip")
        with zipfile.ZipFile(zip_file_path, 'w') as zip_file:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    zip_file.write(file_path, os.path.relpath(file_path, temp_dir))
        # Read the binary data from the zip file
        with open(zip_file_path, "rb") as zip_file:
            zip_binary_data = zip_file.read()
        # Display the download button
        st.download_button(
            label="Download Shapefile",
            data=zip_binary_data,
            file_name="output_shapefile.zip",
            key="download_button1"
        )

    with col4:
        def create_csv(dataframe):
            return dataframe.to_csv(sep='|',index=False).encode('utf-8')
        csv = create_csv(df)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="output_csv.csv",
            key="download_button2",
            mime='text/csv'
        )

    with col5:
        def create_excel(dataframe):
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                dataframe.to_excel(writer, index=False)
            return excel_buffer
        excel = create_excel(df).getvalue()
        st.download_button(
            label="Download Excel",
            data=excel,
            file_name="output_excel.xlsx",
            key="download_button3",
        )



