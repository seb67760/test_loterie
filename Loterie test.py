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

# url = "https://loto.akroweb.fr/loto-historique-tirages"
html = requests.get("https://loto.akroweb.fr/loto-historique-tirages").content
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

    df = df.iloc[0:150].iloc[::-1].reset_index(drop=True)

values = df[["boule_1","boule_2","boule_3","boule_4","boule_5","numero_chance"]].values.tolist()

# VARIABLE PRINCIPALE À MODIFIER => les 100 derniers tirages
WINDOW_SIZE = 10


st.subheader("Derniers tirages")
st.dataframe(df)

# =====================================================
# FONCTIONS DE RANKING
# =====================================================

def get_windows(values, window=WINDOW_SIZE):
    Xn, Xc, Yn, Yc = [], [], [], []

    for i in range(len(values) - window):
        block     = values[i:i+window]
        next_draw = values[i+window]

        Xn.append([row[:5] for row in block])
        Xc.append([row[5]   for row in block])
        Yn.append(next_draw[:5])
        Yc.append(next_draw[5])

    return Xn, Xc, Yn, Yc

# Frequence
def rank_frequencies(window):
    freq = {}
    for tirage in window:
        for n in tirage:
            freq[n] = freq.get(n, 0) + 1

    return {n: r for r,(n,_) in 
            enumerate(sorted(freq.items(), key=lambda x:(-x[1], x[0])), start=1)}

# Récence
def rank_recency(window):
    rec = {}
    for idx, tirage in enumerate(window):
        for n in tirage:
            rec[n] = idx

    return {n: r for r,(n,_) in 
            enumerate(sorted(rec.items(), key=lambda x:(x[1], x[0])), start=1)}

# Duos
def rank_duos(window):
    duo_freq = {}

    for tirage in window:
        for a, b in itertools.combinations(sorted(tirage), 2):
            duo_freq[(a,b)] = duo_freq.get((a,b), 0) + 1

    score = {n: 0 for n in range(1, 50)}
    for (a,b), f in duo_freq.items():
        score[a] += f
        score[b] += f

    return {n: r for r,(n,_) in 
            enumerate(sorted(score.items(), key=lambda x:(-x[1], x[0])), start=1)}


# Frequence
def rank_frequencies_ch(chances):
    freq = {}
    for s in chances:
        freq[s] = freq.get(s,0)+1

    return {s:r for r,(s,_) in 
            enumerate(sorted(freq.items(), key=lambda x:(-x[1], x[0])), start=1)}

# Récence
def rank_recency_ch(chances):
    rec = {}
    for idx, s in enumerate(chances):
        rec[s] = idx

    return {s:r for r,(s,_) in 
            enumerate(sorted(rec.items(), key=lambda x:(x[1], x[0])), start=1)}

# Duos (étoiles consécutives)
def rank_duos_ch(chances):
    duo_freq = {}

    for i in range(len(chances)-1):
        a,b = sorted([chances[i], chances[i+1]])
        duo_freq[(a,b)] = duo_freq.get((a,b),0)+1

    score = {n:0 for n in range(1,11)}
    for (a,b), f in duo_freq.items():
        score[a]+=f
        score[b]+=f

    return {s:r for r,(s,_) in 
            enumerate(sorted(score.items(), key=lambda x:(-x[1], x[0])), start=1)}


# Score pour les numéros
def score_numbers(F,R,D, C1,C2,C3):
    return {n: C1*F.get(n,50) + C2*R.get(n,50) + C3*D.get(n,50)
            for n in range(1,50)}

# Score pour le numéro chance
def score_chance(F,R,D, K1,K2,K3):
    return {s: K1*F.get(s,10) + K2*R.get(s,10) + K3*D.get(s,10)
            for s in range(1,11)}


def build_FRD_matrix(values, window):
    N = len(values) - window
    F = np.zeros((N,49), dtype=int)
    R = np.zeros((N,49), dtype=int)
    D = np.zeros((N,49), dtype=int)

    for i in range(N):
        block = values[i:i+window]
        nums  = [row[:5] for row in block]

        f = rank_frequencies(nums)
        r = rank_recency(nums)
        d = rank_duos(nums)

        for n in range(1,50):
            F[i,n-1] = f.get(n,50)
            R[i,n-1] = r.get(n,50)
            D[i,n-1] = d.get(n,50)

    return F, R, D


def build_FRD_star_matrix(values, window):
    N = len(values) - window
    F = np.zeros((N,10), dtype=int)
    R = np.zeros((N,10), dtype=int)
    D = np.zeros((N,10), dtype=int)

    for i in range(N):
        block = values[i:i+window]
        stars = [row[5] for row in block]

        f = rank_frequencies_ch(stars)
        r = rank_recency_ch(stars)
        d = rank_duos_ch(stars)

        for s in range(1,11):
            F[i,s-1] = f.get(s,10)
            R[i,s-1] = r.get(s,10)
            D[i,s-1] = d.get(s,10)

    return F,R,D

def optimize_C_numpy(F, R, D, Yn):
    best = None
    best_score = -1

    Yn_sets = [set(y) for y in Yn]

    for C1, C2, C3 in product(range(1,11), repeat=3):

        # Scores combinés
        S = C1*F + C2*R + C3*D

        # Top 5 numéros par ligne
        preds = np.argsort(S, axis=1)[:, :5] + 1

        total = 0

        for p, target in zip(preds, Yn_sets):
            inter = len(set(p).intersection(target))
            # Permet de déterminter à partir de combien de boules trouver on compte
            if inter == 2:
                total += 1   # sinon +0
            if inter == 3:
                total += 100  # sinon +0
            if inter == 4:
                total += 10000  # sinon +0
            if inter == 5:
                total += 1000000  # sinon +0
        if total > best_score:
            best_score = total
            best = (C1, C2, C3)

    return best, best_score

def optimize_K_numpy(F,R,D, Yc):
    best = None
    best_score = -1

    for K1,K2,K3 in product(range(1,11), repeat=3):

        S = K1*F + K2*R + K3*D
        preds = np.argmin(S, axis=1) + 1
        score = np.sum(preds == Yc)

        if score > best_score:
            best_score = score
            best = (K1,K2,K3)

    return best, best_score

F,R,D = build_FRD_matrix(values, WINDOW_SIZE)
Yn = [row[:5] for row in values[WINDOW_SIZE:]]
best_C, best_score_C = optimize_C_numpy(F,R,D, Yn)

Fs,Rs,Ds = build_FRD_star_matrix(values, WINDOW_SIZE)
Yc = [row[5] for row in values[WINDOW_SIZE:]]
best_K, best_score_K = optimize_K_numpy(Fs,Rs,Ds, Yc)

print("Meilleurs C :", best_C, "Score :", best_score_C)
print("Meilleurs K :", best_K, "Score :", best_score_K)


def next_full_prediction(values, C1,C2,C3, K1,K2,K3, window):
    nums_window  = [row[:5] for row in values[-window:]]
    stars_window = [row[5]   for row in values[-window:]]

    f = rank_frequencies(nums_window)
    r = rank_recency(nums_window)
    d = rank_duos(nums_window)
    scores_n = score_numbers(f, r, d, C1,C2,C3)
    sorted_nums = sorted(scores_n, key=scores_n.get)

    f = rank_frequencies_ch(stars_window)
    r = rank_recency_ch(stars_window)
    d = rank_duos_ch(stars_window)
    scores_s = score_chance(f, r, d, K1,K2,K3)
    sorted_stars = sorted(scores_s, key=scores_s.get)

    return sorted_nums, sorted_stars

sorted_nums, sorted_stars = next_full_prediction(
    values,
    best_C[0], best_C[1], best_C[2],
    best_K[0], best_K[1], best_K[2],
    WINDOW_SIZE
)

print("NUMÉROS CLASSÉS :", sorted_nums)
print("ÉTOILES CLASSÉES :", sorted_stars)

# Calcul sans coefficient
sorted_nums, sorted_stars = next_full_prediction(
    values,
    1, 1, 1,
    1, 1, 1,
    WINDOW_SIZE
)

print("NUMÉROS CLASSÉS :", sorted_nums)
print("ÉTOILES CLASSÉES :", sorted_stars)

print((datetime.datetime.now()))

