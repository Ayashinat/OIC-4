import streamlit as st
from PIL import ExifTags, Image
from streamlit_folium import st_folium


st.set_page_config(page_title="OIC 4.2 - EXIF GPS", layout="wide")
st.title("OIC 4.2 - Edition EXIF + GPS + Cartes")

charger_photo = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])

if charger_photo is not None:
	image = Image.open(charger_photo)
	exif_data = image._getexif()
	
	if exif_data is not None:
		st.subheader("EXIF Data")
		for tag_id, value in exif_data.items():
			tag = ExifTags.TAGS.get(tag_id, tag_id)
			st.write(f"{tag}: {value}")
		
		gps_info = exif_data.get(34853)  # GPSInfo tag
		if gps_info is not None:
			st.subheader("GPS Information")
			gps_data = {}
			for key in gps_info.keys():
				gps_tag = ExifTags.GPSTAGS.get(key, key)
				gps_data[gps_tag] = gps_info[key]
				st.write(f"{gps_tag}: {gps_info[key]}")
			
			# Extract latitude and longitude
			lat = gps_data.get('GPSLatitude')
			lat_ref = gps_data.get('GPSLatitudeRef')
			lon = gps_data.get('GPSLongitude')
			lon_ref = gps_data.get('GPSLongitudeRef')
			
			if lat and lat_ref and lon and lon_ref:
				lat_decimal = (lat[0][0] / lat[0][1]) + (lat[1][0] / lat[1][1]) / 60 + (lat[2][0] / lat[2][1]) / 3600
				if lat_ref == 'S':
					lat_decimal = -lat_decimal
				
				lon_decimal = (lon[0][0] / lon[0][1]) + (lon[1][0] / lon[1][1]) / 60 + (lon[2][0] / lon[2][1]) / 3600
				if lon_ref == 'W':
					lon_decimal = -lon_decimal
				
				st.subheader("Location on Map")
				st_folium({"latitude": lat_decimal, "longitude": lon_decimal}, width=700, height=500)
	else:
		st.warning("No EXIF data found in the image.")