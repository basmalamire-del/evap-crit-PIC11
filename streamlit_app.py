# streamlit_app.py
import numpy as np
import pandas as pd
import streamlit as st
import altair as alt

from evaporateurs import simuler_evaporation_multi_effets
from cristallisation import simuler_cristallisation_batch

st.set_page_config(page_title="PIC - Evaporation & Cristallisation", layout="wide")

st.title("🧪 Projet — Évaporation multiple & Cristallisation du saccharose")
st.caption("Interface web (Streamlit) — graphes interactifs (Altair/Vega-Lite, style D3).")

# -----------------------------
# Sidebar paramètres
# -----------------------------
st.sidebar.header("Paramètres généraux")

F = st.sidebar.number_input("Débit F (kg/h)", min_value=1.0, value=20000.0, step=100.0)
xF = st.sidebar.slider("xF (fraction massique)", 0.01, 0.50, 0.15, 0.01)
xout = st.sidebar.slider("xout (fraction massique)", 0.20, 0.80, 0.65, 0.01)
Tfeed = st.sidebar.number_input("T_feed (°C)", min_value=10.0, value=85.0, step=1.0)
Psteam = st.sidebar.slider("P vapeur (bar)", 1.0, 6.0, 3.5, 0.1)

tabs = st.tabs(["⚙️ Évaporation", "❄️ Cristallisation", "📈 Sensibilité", "📦 Export"])

# -----------------------------
# TAB 1 — Évaporation
# -----------------------------
with tabs[0]:
    st.subheader("Simulation de la batterie d’évaporation")
    n_eff = st.number_input("Nombre d'effets", min_value=1, max_value=6, value=3, step=1)

    run_evap = st.button("▶ Lancer la simulation d'évaporation", use_container_width=True)

    if run_evap:
        try:
            res = simuler_evaporation_multi_effets(
                n_effets=int(n_eff),
                F_kg_h=float(F),
                xF=float(xF),
                xout=float(xout),
                T_feed_C=float(Tfeed),
                P_vapeur_bar=float(Psteam),
            )

            c1, c2, c3 = st.columns(3)
            c1.metric("Débit vapeur S (kg/h)", f"{res['S']:.2f}")
            c2.metric("Économie", f"{res['economie']:.2f}")
            c3.metric("Surface totale A (m²)", f"{res['A_total']:.2f}")

            df = pd.DataFrame({
                "Effet": res["effets"],
                "V_i (kg/h)": res["V_i"],
                "L_i (kg/h)": res["L_i"],
                "x_i (-)": res["x_i"],
                "T_boil (°C)": res["T_boil"],
                "A_i (m²)": res["A_i"],
            })

            st.dataframe(df, use_container_width=True)

            # Graphes Altair (2 par ligne)
            row1 = st.columns(2)
            row2 = st.columns(2)
            row3 = st.columns(2)

            base = alt.Chart(df).encode(x=alt.X("Effet:O"))

            ch_x = base.mark_line(point=True).encode(y="x_i (-):Q").properties(title="Concentration x par effet")
            ch_L = base.mark_line(point=True).encode(y="L_i (kg/h):Q").properties(title="Débit liquide L par effet")
            ch_V = base.mark_line(point=True).encode(y="V_i (kg/h):Q").properties(title="Évaporation V par effet")
            ch_T = base.mark_line(point=True).encode(y="T_boil (°C):Q").properties(title="Température d’ébullition par effet")
            ch_A = base.mark_line(point=True).encode(y="A_i (m²):Q").properties(title="Surface par effet")

            row1[0].altair_chart(ch_x, use_container_width=True)
            row1[1].altair_chart(ch_L, use_container_width=True)
            row2[0].altair_chart(ch_V, use_container_width=True)
            row2[1].altair_chart(ch_T, use_container_width=True)
            row3[0].altair_chart(ch_A, use_container_width=True)

            st.success("✅ Évaporation : OK")

        except Exception as e:
            st.error(f"Erreur evaporation : {e}")

# -----------------------------
# TAB 2 — Cristallisation
# -----------------------------
with tabs[1]:
    st.subheader("Cristallisation batch")

    M = st.number_input("M (masse solution, kg)", min_value=1.0, value=200.0, step=10.0)
    C_init = st.number_input("C_init (g/100g solution)", min_value=10.0, value=70.0, step=1.0)
    T_init = st.number_input("T_init (°C)", min_value=20.0, value=80.0, step=1.0)
    duree = st.number_input("Durée (s)", min_value=600.0, value=7200.0, step=300.0)
    dt = st.number_input("dt (s)", min_value=10.0, value=60.0, step=10.0)
    profil = st.selectbox("Profil de refroidissement", ["lineaire", "expo", "S_const"])

    run_crist = st.button("▶ Lancer la simulation de cristallisation", use_container_width=True)

    if run_crist:
        try:
            L, nL, hist = simuler_cristallisation_batch(M, C_init, T_init, duree, dt=float(dt), profil=profil)
            dfh = pd.DataFrame(hist)

            c1, c2, c3 = st.columns(3)
            c1.metric("Lmean final (m)", f"{dfh['Lmean'].iloc[-1]:.3e}")
            c2.metric("CV final (-)", f"{dfh['CV'].iloc[-1]:.3f}")
            c3.metric("S final (-)", f"{dfh['S'].iloc[-1]:.3f}")

            st.dataframe(dfh.tail(20), use_container_width=True)

            # Graphes (2 par ligne)
            r1 = st.columns(2)
            r2 = st.columns(2)

            base = alt.Chart(dfh).encode(x=alt.X("t:Q", title="t (s)"))

            ch_T = base.mark_line().encode(y=alt.Y("T:Q", title="T (°C)")).properties(title="Température")
            ch_C = base.mark_line().encode(y=alt.Y("C:Q", title="C (g/100g)")).properties(title="Concentration")
            ch_S = base.mark_line().encode(y=alt.Y("S:Q", title="S (-)")).properties(title="Sursaturation")
            ch_Lm = base.mark_line().encode(y=alt.Y("Lmean:Q", title="Lmean (m)")).properties(title="Taille moyenne")

            r1[0].altair_chart(ch_T, use_container_width=True)
            r1[1].altair_chart(ch_C, use_container_width=True)
            r2[0].altair_chart(ch_S, use_container_width=True)
            r2[1].altair_chart(ch_Lm, use_container_width=True)

            st.success("✅ Cristallisation : OK")

        except Exception as e:
            st.error(f"Erreur cristallisation : {e}")

# -----------------------------
# TAB 3 — Sensibilité (simple)
# -----------------------------
with tabs[2]:
    st.subheader("Étude de sensibilité (simple)")
    st.info("À enrichir : variations de xF, xout, P vapeur, nombre d'effets, etc.")

# -----------------------------
# TAB 4 — Export
# -----------------------------
with tabs[3]:
    st.subheader("Export")
    st.write("Export CSV + figures (stable sur Streamlit Cloud).")
