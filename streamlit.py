import streamlit as st
import pandas as pd
from streamlit_folium import st_folium
import tempfile
import os
import zipfile
import fungsi

st.write('19-12-2023')

# Masukkan Dataset Awal
df_kabkota = pd.read_excel('Kabupaten_Kota.xlsx')
df_kecamatan = pd.read_excel('Kecamatan.xlsx')
df_keldesa = pd.read_excel('Kelurahan_Desa.xlsx')
df_kabkota['Selected_Processed'] = df_kabkota['Kabupaten/Kota'].apply(fungsi.clean)
df_kecamatan['Selected_Processed'] = df_kecamatan['Kecamatan'].apply(fungsi.clean)
df=None

st.title('Open Data Template')
st.write('### Daerah Sumatera Utara')

# Upload File
uploaded_file = st.file_uploader("Pilih File !", type=["xls", "xlsx", "csv"])

if uploaded_file is not None:
    file_extension = uploaded_file.name.split('.')[-1].lower()
    if file_extension == 'csv':
        separator = st.text_input("CSV Separator (default is ',')", ',')
    else:
        separator = ','  # Default separator for non-CSV files
    df, _ = fungsi.read_file(uploaded_file, separator)

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
            df['Selected_Processed'] = df[pemilihan_kolom].apply(fungsi.clean)
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

        st_map = st_folium(fungsi.map(df, jenis_lokasi), width= 800)

        col3, col4, col5 = st.columns(3)

        with col3:

            df_gdf = df.copy()
            gdf = fungsi.create_shapefile(df_gdf)
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

            csv = fungsi.create_csv(df)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="output_csv.csv",
                key="download_button2",
                mime='text/csv'
            )

        with col5:
            excel = fungsi.create_excel(df).getvalue()
            st.download_button(
                label="Download Excel",
                data=excel,
                file_name="output_excel.xlsx",
                key="download_button3",
            )

    except:
        st.warning('Anda Memasukkan Kolom yang salah!', icon="⚠️")

