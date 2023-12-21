import streamlit as st
import pandas as pd
from streamlit_folium import st_folium
import tempfile
import os
import zipfile
import fungsi
import datetime

st.write('ver.1, 22-12-2023')

# Masukkan Dataset Awal
df_kabkota = pd.read_excel('Kabupaten_Kota.xlsx')
df_kecamatan = pd.read_excel('Kecamatan.xlsx')
df_keldesa = pd.read_excel('Kelurahan_Desa.xlsx')
df_kabkota['Selected_Processed'] = df_kabkota['Kabupaten/Kota'].apply(fungsi.clean)
df_kecamatan['Selected_Processed'] = df_kecamatan['Kecamatan'].apply(fungsi.clean)
df=None

st.title('Open Data Template')
st.write('### Daerah Sumatera Utara')

'''
Template ini menyediakan injeksi koordinat terhadap wilayah administrasi Kabupaten/Kota dan Kecamatan di Provinsi Sumatera Utara serta menyediakan data yang dapat di-download dalam bentuk Shapefile (.shp), Comma Separated Value (.csv) dan Excel (.xlsx)
'''

# Upload File
uploaded_file = st.file_uploader("Pilih File !", type=["xls", "xlsx", "csv"])

if uploaded_file is not None:
    file_extension = uploaded_file.name.split('.')[-1].lower()
    if file_extension == 'csv':
        separator = st.text_input("CSV Separator (default is ',')", ',')
    else:
        separator = ','  # Default separator for non-CSV files
    df, _ = fungsi.read_file(uploaded_file, separator)

show_input_data = st.checkbox("Lihat dan Edit Data !")

if show_input_data and df is not None:
    df = st.data_editor(df)

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

        # try:
        #     map_df = df.copy()
        #     select_date = st.selectbox("Pilih Kolom Waktu", list_column)
        #     map_df['Date'] = pd.to_datetime(map_df[select_date], format='%Y', infer_datetime_format=True, errors='coerce')
        #     map_df['Date'] = map_df['Date'].dt.strftime('%Y')
        #     st.dataframe(map_df)
        #     # selection_dates = st.slider("Select Date Range",
        #     #                             min_value=min(map_df['Date']),
        #     #                             max_value=max(map_df['Date']),
        #     #                             value=(min(map_df['Date']),max(map_df['Date'])),format='YYYY')
        #     selection_dates = st.slider("Select Date Range",
        #                                 min_value=2020,
        #                                 max_value=2023)
        #     # map_df = map_df[(map_df['Date'] >= start_date) & (map_df['Date'] <= end_date)]
        #     mask = map_df['Date'].between(*selection_dates)
        #     map_df = map_df[mask]
        #     st_map = st_folium(fungsi.map(map_df, jenis_lokasi), width= 800)
        # except:
        #     st.warning('Kolom Waktu Anda Salah !')

        st_folium(fungsi.map(df, jenis_lokasi), width=800)

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

        make_metadata = st.checkbox("Buat Metadata !")

        if make_metadata is True:
            default_ket = {'Kabupaten/Kota':'Nama Kabupaten/Kota',
                           'Status Kabupaten/Kota':'Status administrasi Kabupaten/Kota',
                           'Kecamatan':'Nama Kecamatan',
                           'Kode Kemendagri':'Kode wilayah administrasi',
                           'Latitude':'Garis lintang wilayah administrasi',
                           'Longitude':'Garis bujur wilayah administrasi'}
            tipe_list = ['String', 'Float', 'Integer', 'Number', 'Date', 'Lainnya']
            metadata = {}

            for i in df.columns:
                col6, col7 = st.columns(2)
                with col6:
                    default_value = default_ket.get(i, "Isi Keterangan")
                    keterangan = st.text_input(f"Keterangan {i}", default_value)
                    non_null_count = df[i].count()
                    null_count = df[i].isnull().sum()
                with col7:
                    tipe_data = st.selectbox(f"Tipe Data {i}", tipe_list)
                    tipe_data_ = tipe_data
                    if tipe_data_ == 'Lainnya':
                        tipe_data_ = st.text_input(f"Masukkan Tipe Data !")

                metadata[i] = {
                    'keterangan': keterangan,
                    'tipe_data': tipe_data_,
                    'non_null_count':non_null_count,
                    'null_count':null_count
                }

            metadata_text = f"Metadata Tabel \n\n{uploaded_file}\n\nKeterangan Kolom :\n\n"
            for col, info in metadata.items():
                metadata_text += f"{col}:\n"
                metadata_text += f"  Keterangan: {info['keterangan']}\n"
                metadata_text += f"  Tipe Data: {info['tipe_data']}\n"
                metadata_text += f"  Non Null Count: {info['non_null_count']}\n"
                metadata_text += f"  Null Count: {info['null_count']}\n\n"

            # Provide a download button for the text file
            st.download_button(
                label="Download Metadata",
                data=metadata_text.encode("utf-8"),
                key="download_button",
                file_name="metadata.txt",
                mime="text/plain"
            )

    except:
        st.warning('Anda Memasukkan Kolom yang salah!', icon="⚠️")

st.write('©Muaaz Atqa')

