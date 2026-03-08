import streamlit as st
from PIL import ExifTags, Image
from streamlit_folium import st_folium
import folium
import piexif



def decimal_vers_dms_rationnel(valeur):
    """Convertit un decimal en DMS pour le format EXIF GPS."""
    valeur = abs(valeur)
    degres = int(valeur)
    minutes_flottantes = (valeur - degres) * 60
    minutes = int(minutes_flottantes)
    secondes = round((minutes_flottantes - minutes) * 60 * 100)
    return ((degres, 1), (minutes, 1), (secondes, 100))


def construire_bloc_gps(latitude, longitude):
    """Construit le bloc GPS EXIF."""
    ref_latitude = b"N" if latitude >= 0 else b"S"
    ref_longitude = b"E" if longitude >= 0 else b"W"
    return {
        piexif.GPSIFD.GPSLatitudeRef: ref_latitude,
        piexif.GPSIFD.GPSLatitude: decimal_vers_dms_rationnel(latitude),
        piexif.GPSIFD.GPSLongitudeRef: ref_longitude,
        piexif.GPSIFD.GPSLongitude: decimal_vers_dms_rationnel(longitude),
    }


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


def extraire_coordonnees_gps(exif_dict):
    """Retourne (latitude, longitude) depuis EXIF GPS, sinon (None, None)."""
    gps = exif_dict.get("GPS", {})
    
    latitude_dms = gps.get(piexif.GPSIFD.GPSLatitude)
    latitude_ref = gps.get(piexif.GPSIFD.GPSLatitudeRef)
    longitude_dms = gps.get(piexif.GPSIFD.GPSLongitude)
    longitude_ref = gps.get(piexif.GPSIFD.GPSLongitudeRef)
    
    if latitude_dms and latitude_ref and longitude_dms and longitude_ref:
        latitude_decimal = dms_vers_decimal(latitude_dms, latitude_ref)
        longitude_decimal = dms_vers_decimal(longitude_dms, longitude_ref)
        return latitude_decimal, longitude_decimal
    
    return None, None


st.set_page_config(page_title="OIC 4.2 - EXIF GPS", layout="wide")
st.title("OIC 4.2 - Edition EXIF + GPS + Cartes")

# État persistant pour le message de réussite
if "exif_sauvegarde" not in st.session_state:
    st.session_state.exif_sauvegarde = False
if "coords_gps_msg" not in st.session_state:
    st.session_state.coords_gps_msg = None

st.subheader("Extraire les EXIF et GPS d'une image")
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
        exif_brut = image.info.get("exif", b"")
        exif_dict = piexif.load(exif_brut) if exif_brut else {"0th": {}, "Exif": {}, "GPS": {}, "Interop": {}, "1st": {}, "thumbnail": None}
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

    # Afficher les coordonnées GPS extraites
    latitude_gps, longitude_gps = extraire_coordonnees_gps(exif_dict)
    if latitude_gps is not None and longitude_gps is not None:
        st.success(f"Coordonnées GPS trouvées dans l'image : Latitude = {latitude_gps:.6f}, Longitude = {longitude_gps:.6f}")
    else:
        st.info("Aucune coordonnée GPS détectée dans l'image.")

    st.subheader("Edition des métadonnées EXIF")

    with st.form("edition_form"):
        colonne_a, colonne_b = st.columns(2)
        with colonne_a:
            auteur = st.text_input("Artist (Auteur)", value="Aya")
            description_image = st.text_input("ImageDescription", value="Photo exercice OIC 4.2")
            marque_appareil = st.text_input("Make (Marque appareil)", value="Smartphone")
            modele_appareil = st.text_input("Model (Modele appareil)", value="Modele inconnu")
            logiciel = st.text_input("Software", value="Streamlit + piexif")
            copyright_texte = st.text_input("Copyright", value="(c) Aya")

        with colonne_b:
            marque_objectif = st.text_input("LensMake", value="Lens simple")
            modele_objectif = st.text_input("LensModel", value="Lens model simple")
            commentaire_utilisateur = st.text_area("UserComment", value="Metadonnees modifiees dans Streamlit")

        st.markdown("#### Coordonnées GPS")
        col_lat, col_lon = st.columns(2)
        with col_lat:
            latitude = st.number_input("Latitude", min_value=-90.0, max_value=90.0, value=latitude_gps if latitude_gps is not None else 48.8566, step=0.0001, format="%.6f")
        with col_lon:
            longitude = st.number_input("Longitude", min_value=-180.0, max_value=180.0, value=longitude_gps if longitude_gps is not None else 2.3522, step=0.0001, format="%.6f")

        soumettre_exif = st.form_submit_button("Modifie EXIF et télécharge l'image")

    if soumettre_exif:
        # Remplir exif_dict avec les valeurs du formulaire
        exif_dict["0th"][piexif.ImageIFD.Artist] = auteur.encode("utf-8") if auteur else b""
        exif_dict["0th"][piexif.ImageIFD.ImageDescription] = description_image.encode("utf-8") if description_image else b""
        exif_dict["0th"][piexif.ImageIFD.Make] = marque_appareil.encode("utf-8") if marque_appareil else b""
        exif_dict["0th"][piexif.ImageIFD.Model] = modele_appareil.encode("utf-8") if modele_appareil else b""
        exif_dict["0th"][piexif.ImageIFD.Software] = logiciel.encode("utf-8") if logiciel else b""
        exif_dict["0th"][piexif.ImageIFD.Copyright] = copyright_texte.encode("utf-8") if copyright_texte else b""
        
        exif_dict["Exif"][piexif.ExifIFD.LensMake] = marque_objectif.encode("utf-8") if marque_objectif else b""
        exif_dict["Exif"][piexif.ExifIFD.LensModel] = modele_objectif.encode("utf-8") if modele_objectif else b""
        exif_dict["Exif"][piexif.ExifIFD.UserComment] = commentaire_utilisateur.encode("utf-8") if commentaire_utilisateur else b""

        # Enregistrer les coordonnées GPS dans EXIF
        exif_dict["GPS"] = construire_bloc_gps(latitude, longitude)

        try:
            exif_bytes = piexif.dump(exif_dict)
            image.save("image_modifiee.jpg", exif=exif_bytes)
            st.session_state.exif_sauvegarde = True
            st.session_state.coords_gps_msg = f"Latitude = {latitude:.6f}, Longitude = {longitude:.6f}"
        except Exception as e:
            st.error(f"Erreur lors de la sauvegarde de l'image : {e}")
    
    # Afficher le message de réussite s'il y a eu une sauvegarde
    if st.session_state.exif_sauvegarde:
        st.success("EXIF modifié et sauvegardé dans 'image_modifiee.jpg'.")
        st.write(f"Coordonnées GPS enregistrées : {st.session_state.coords_gps_msg}")
    
    st.subheader("Carte GPS de la photo")
    st.text("La carte ci-dessous montre la localisation GPS associée à l'image (si disponible) ou les coordonnées saisies dans le formulaire.") 
    carte = folium.Map(location=[latitude, longitude], zoom_start=13)
    folium.Marker(
        [latitude, longitude],
        popup="Position choisie",
        tooltip="Cliquer ici"
    ).add_to(carte)

    st_folium(carte, width=700, height=500)




st.subheader("Carte de voyage")

destinations = [
    ("Paris", 48.8566, 2.3522),
    ("Université", 48.9350, 2.3530),
    ("Chine", 31.2304, 121.4737),
    ("Japon", 35.6762, 139.6503),
    ("Norvège", 59.9139, 10.7522),
]

carte_poi = folium.Map(
    location=[destinations[0][1], destinations[0][2]],
    zoom_start=6
)

for nom, lat, lon in destinations:
    folium.Marker(
        [lat, lon],
        popup=f"{nom}<br>Lat: {lat}<br>Lon: {lon}",
        tooltip=nom
    ).add_to(carte_poi)

ligne = [[lat, lon] for nom, lat, lon in destinations]
folium.PolyLine(ligne, weight=4, opacity=0.8).add_to(carte_poi)

st_folium(carte_poi, width=800, height=500)