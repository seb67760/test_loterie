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

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)

    tables = pd.read_html(response.text)

    df = tables[0][[2,4,5,6,7,8,9]]

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
        "boule_2",
        "boule_3",
        "boule_4",
        "boule_5",
        "numero_chance"
    ]
].values.tolist()

# =====================================================
# FONCTIONS DE RANKING
# =====================================================

def rank_frequencies(window):

    freq = {}

    for tirage in window:
        for n in tirage:
            freq[n] = freq.get(n, 0) + 1

    return {
        n: r
        for r, (n, _) in enumerate(
            sorted(freq.items(), key=lambda x: (-x[1], x[0])),
            start=1
        )
    }


def rank_recency(window):

    rec = {}

    for idx, tirage in enumerate(window):
        for n in tirage:
            rec[n] = idx

    return {
        n: r
        for r, (n, _) in enumerate(
            sorted(rec.items(), key=lambda x: (x[1], x[0])),
            start=1
        )
    }


def rank_duos(window):

    duo_freq = {}

    for tirage in window:
        for a, b in itertools.combinations(sorted(tirage), 2):
            duo_freq[(a, b)] = duo_freq.get((a, b), 0) + 1

    score = {n: 0 for n in range(1, 50)}

    for (a, b), f in duo_freq.items():
        score[a] += f
        score[b] += f

    return {
        n: r
        for r, (n, _) in enumerate(
            sorted(score.items(), key=lambda x: (-x[1], x[0])),
            start=1
        )
    }

# =====================================================
# CALCUL SCORES
# =====================================================

if st.button("Calculer"):

    block = values[-WINDOW_SIZE:]

    nums = [row[:5] for row in block]

    F = rank_frequencies(nums)
    R = rank_recency(nums)
    D = rank_duos(nums)

    # Coefficients simples
    C1, C2, C3 = 5, 3, 2

    scores = {}

    for n in range(1, 50):
        scores[n] = (
            C1 * F.get(n, 50)
            + C2 * R.get(n, 50)
            + C3 * D.get(n, 50)
        )

    classement = sorted(scores.items(), key=lambda x: x[1])

    top5 = [n for n, s in classement[:5]]

    st.success(f"Numéros proposés : {sorted(top5)}")

    df_scores = pd.DataFrame(classement, columns=["Numéro", "Score"])

    st.subheader("Classement")
    st.dataframe(df_scores)
