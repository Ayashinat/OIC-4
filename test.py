import streamlit as st
from PIL import Image
import piexif






st.title("OIC 4.2 - Edition EXIF + GPS + Cartes")

def rationnel_vers_decimal(rationnel):
    """Convertit une valeur EXIF de type (num, den) en float."""
    return rationnel[0] / rationnel[1] if rationnel[1] != 0 else 0.0


def dms_vers_decimal(dms, ref):
    """Convertit DMS EXIF en decimal signe."""
    degres = rationnel_vers_decimal(dms[0])
    minutes = rationnel_vers_decimal(dms[1])
    secondes = rationnel_vers_decimal(dms[2])
    decimal = degres + (minutes / 60.0) + (secondes / 3600.0)
    if ref in (b"S", b"W"):
        decimal = -decimal
    return decimal

def extraire_coordonnees_gps_exif(image):
    """Retourne (latitude, longitude) depuis EXIF GPS, sinon (None, None)."""
    exif_brut = image.info.get("exif", b"")
    if not exif_brut:
        return None, None

    try:
        exif_dict = piexif.load(exif_brut)
        gps = exif_dict.get("GPS", {})

        latitude_dms = gps.get(piexif.GPSIFD.GPSLatitude)
        latitude_ref = gps.get(piexif.GPSIFD.GPSLatitudeRef)
        longitude_dms = gps.get(piexif.GPSIFD.GPSLongitude)
        longitude_ref = gps.get(piexif.GPSIFD.GPSLongitudeRef)

        if latitude_dms and latitude_ref and longitude_dms and longitude_ref:
            latitude_decimal = dms_vers_decimal(latitude_dms, latitude_ref)
            longitude_decimal = dms_vers_decimal(longitude_dms, longitude_ref)
            return latitude_decimal, longitude_decimal
    except Exception:
        return None, None

    return None, None


st.markdown("### 1) Inserer une photo")
fichier = st.file_uploader("Choisir une image", type=["jpg", "jpeg"])


if fichier is not None:
    image = Image.open(fichier)
    st.image(image, width=300)

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

    def lire_texte(ifd, tag):
        valeur = exif_dict[ifd].get(tag, b"")
        if isinstance(valeur, bytes):
            try:
                return valeur.decode("utf-8", errors="ignore")
            except Exception:
                return ""
        return str(valeur)

    with st.form("form_exif"):
        artiste = st.text_input(
            "Auteur",
            value=lire_texte("0th", piexif.ImageIFD.Artist)
        )
        description = st.text_input(
            "Description",
            value=lire_texte("0th", piexif.ImageIFD.ImageDescription)
        )
        marque = st.text_input(
            "Marque appareil",
            value=lire_texte("0th", piexif.ImageIFD.Make)
        )
        modele = st.text_input(
            "Modèle appareil",
            value=lire_texte("0th", piexif.ImageIFD.Model)
        )

        valider = st.form_submit_button("Enregistrer les modifications")

    if valider:
        exif_dict["0th"][piexif.ImageIFD.Artist] = artiste.encode("utf-8")
        exif_dict["0th"][piexif.ImageIFD.ImageDescription] = description.encode("utf-8")
        exif_dict["0th"][piexif.ImageIFD.Make] = marque.encode("utf-8")
        exif_dict["0th"][piexif.ImageIFD.Model] = modele.encode("utf-8")

        st.success("Les valeurs du formulaire ont bien été récupérées.")
        st.write(exif_dict["0th"])


    st.markdown("### 2) Localisation sur la carte")
    latitude = st.number_input(
            "Latitude actuelle",
            min_value=-90.0,
            max_value=90.0,
            value=48.8566,
            step=0.0001,
            format="%.6f",
        )
    longitude = st.number_input(
        "Longitude actuelle",
        min_value=-180.0,
        max_value=180.0,
        value=2.3522,
        step=0.0001,
        format="%.6f",
    )
    soumettre_exif = st.form_submit_button("Ecrire EXIF + GPS dans l'image")
    

    st.success("Image EXIF modifiée.")
    st.download_button(
        "Télécharger l'image modifiée",
        data=buffer,
        file_name="image_modifiee.jpg",
        mime="image/jpeg"
        )