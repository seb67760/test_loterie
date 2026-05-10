import streamlit as st
import pandas as pd
import numpy as np
import requests
import itertools
from itertools import product

st.set_page_config(page_title="Analyse Loto", layout="wide")

st.title("🎯 Analyse Loto")

# =====================================================
# RÉCUPÉRATION DES DONNÉES
# =====================================================

@st.cache_data
def load_data(nb_tirages=150):

    url = "https://loto.akroweb.fr/loto-historique-tirages"

    html = requests.get(url).content

    df = pd.read_html(html)[0][[2,4,5,6,7,8,9]]

    df.columns = [
        "date_de_tirage",
        "boule_1",
        "boule_2",
        "boule_3",
        "boule_4",
        "boule_5",
        "numero_chance"
    ]

    df = df.iloc[0:nb_tirages].iloc[::-1].reset_index(drop=True)

    return df

# =====================================================
# PARAMÈTRES
# =====================================================

col1, col2 = st.columns(2)

with col1:
    nb_tirages = st.slider("Nombre de tirages", 50, 500, 150)

with col2:
    WINDOW_SIZE = st.slider("Fenêtre d'analyse", 5, 100, 10)

# =====================================================
# CHARGEMENT
# =====================================================

with st.spinner("Chargement des données..."):
    df = load_data(nb_tirages)

st.subheader("Derniers tirages")
st.dataframe(df)

values = df[
    [
        "boule_1",
    st.dataframe(df_scores)