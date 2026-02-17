import streamlit as st
prenom = st.text_input('Quel est votre prénom ?')
message = st.text_input(' Quel est votre message ?')
st.write(message," ", prenom)
