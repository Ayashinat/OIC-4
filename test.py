import streamlit as st
from PIL import ExifTags, Image
from streamlit_folium import st_folium
import folium
import piexif

st.set_page_config(page_title="OIC 4.2 - EXIF GPS", layout="wide")
st.title("OIC 4.2 - Edition EXIF + GPS + Cartes")

charger_photo = st.file_uploader("Choisir une image", type=["jpg", "jpeg", "png"])

if charger_photo:
    image = Image.open(charger_photo)
    st.image(image, caption="Image chargée", width=350)

    exif = image.getexif()

    if exif:
        exif_lisible = {}
        for tag_id, valeur in exif.items():
            nom_tag = ExifTags.TAGS.get(tag_id, tag_id)
            exif_lisible[nom_tag] = valeur

        st.subheader("Métadonnées EXIF")
        st.write(exif_lisible)

        gps = exif_lisible.get("GPSInfo")

        if gps is not None:
            st.subheader("Balise GPS brute")
            st.write(gps)
            st.write("Type :", type(gps))
        else:
            st.info("Aucune donnée GPS trouvée.")
    else:
        st.info("Aucune métadonnée EXIF détectée.")

    try:
        exif_dict = piexif.load(image.info.get("exif", b""))
    except Exception:
        exif_dict = {
            "0th": {},
            "Exif": {},
            "GPS": {},
            "Interop": {},
            "1st": {},
            "thumbnail": None
        }

    st.subheader("EXIF via piexif")
    st.write(exif_dict)