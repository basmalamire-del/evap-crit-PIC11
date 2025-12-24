# streamlit_app.py
import streamlit as st
import numpy as np
import pandas as pd
import altair as alt

from evaporateurs import simulation_evaporation_multi_effets
from cristallisation import simuler_cristallisation_batch


st.set_page_config(page_title="PIC — Évaporation & Cristallisation", layout="wide")

st.title("🧪 Projet — Évaporation multiple & Cristallisation du saccharose")
st.caption("Interface web (Streamlit) — graphes interactifs (Altair/Vega-Lite, style D3).")

tab_evap, tab_crist, tab_sens, tab_export = st.tabs(
    ["⚙️ Évaporation", "❄️ Cristallisation", "📈 Sensibilité", "📦 Export"]
)

# -----------------------------
# Helpers Altair (safe)
# -----------------------------
def line_chart(df: pd.DataFrame, x: str, y: str, title: str):
    return (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X(x, title=x),
            y=alt.Y(y, title=y),
            tooltip=list(df.columns),
        )
        .properties(title=title, height=260)
    )


# =============================
# TAB 1 — ÉVAPORATION
# =============================
with tab_evap:
    st.header("Simulation de la batterie d’évaporation")

    with st.sidebar:
        st.subheader("Paramètres — Évaporation")
        n_effets = st.number_input("Nombre d'effets", min_value=1, max_value=10, value=3, step=1)

        F_kg_h = st.number_input("Débit d'alimentation F (kg/h)", min_value=1.0, value=15000.0, step=100.0)
        xF = st.slider("xF (fraction massique)", min_value=0.01, max_value=0.50, value=0.15, step=0.01)
        xout = st.slider("xout (fraction massique)", min_value=0.02, max_value=0.90, value=0.65, step=0.01)

        Tsteam = st.number_input("Température vapeur (°C)", min_value=50.0, value=120.0, step=1.0)
        Tlast = st.number_input("Température dernier effet (°C)", min_value=20.0, value=60.0, step=1.0)

        U = st.number_input("Coefficient U (W/m²/K)", min_value=100.0, value=1500.0, step=50.0)
        lamb = st.number_input("Chaleur latente λ (kJ/kg)", min_value=1000.0, value=2257.0, step=10.0)

    run_evap = st.button("▶ Lancer la simulation d'évaporation", use_container_width=True)

    if run_evap:
        try:
            res = simulation_evaporation_multi_effets(
                F_kg_h=F_kg_h,
                xF=xF,
                xout=xout,
                n_effets=n_effets,
                T_steam_C=Tsteam,
                T_last_C=Tlast,
                U=U,
                lambda_kJ_kg=lamb,
            )
            st.session_state["evap_res"] = res
        except Exception as e:
            st.error(f"Erreur evaporation : {e}")

    if "evap_res" in st.session_state:
        res = st.session_state["evap_res"]
        c1, c2, c3 = st.columns(3)
        c1.metric("Débit vapeur S (kg/h)", f"{res['S']:.2f}")
        c2.metric("Économie", f"{res['economie']:.2f}")
        c3.metric("Surface totale A (m²)", f"{res['A_total']:.2f}")

        df = pd.DataFrame(res["details"])

        st.subheader("📊 Courbes par effet (4 courbes)")
        colA, colB = st.columns(2)
        colC, colD = st.columns(2)

        with colA:
            st.altair_chart(line_chart(df, "effect", "V_kg_h", "1) Eau évaporée par effet V (kg/h)"), use_container_width=True)
        with colB:
            st.altair_chart(line_chart(df, "effect", "dT_K", "2) ΔT par effet (K)"), use_container_width=True)
        with colC:
            st.altair_chart(line_chart(df, "effect", "A_m2", "3) Surface par effet A (m²)"), use_container_width=True)
        with colD:
            dfT = df[["effect", "T_hot_C", "T_cold_C"]].copy()
            dfT_m = dfT.melt("effect", var_name="temp_type", value_name="T_C")
            chartT = (
                alt.Chart(dfT_m)
                .mark_line(point=True)
                .encode(
                    x=alt.X("effect:Q", title="effect"),
                    y=alt.Y("T_C:Q", title="Température (°C)"),
                    color=alt.Color("temp_type:N", title="Temp"),
                    tooltip=["effect", "temp_type", "T_C"]
                )
                .properties(title="4) Profil de température (Thot/Tcold)", height=260)
            )
            st.altair_chart(chartT, use_container_width=True)

        st.subheader("📋 Détails numériques")
        st.dataframe(df, use_container_width=True)


# =============================
# TAB 2 — CRISTALLISATION
# =============================
with tab_crist:
    st.header("Cristallisation batch")

    col1, col2, col3 = st.columns(3)
    with col1:
        M = st.number_input("M (masse solution) [kg]", min_value=1.0, value=100.0, step=10.0)
    with col2:
        C_init = st.number_input("C_init (g/100g)", min_value=10.0, value=70.0, step=1.0)
    with col3:
        T_init = st.number_input("T_init (°C)", min_value=40.0, value=75.0, step=1.0)

    col4, col5 = st.columns(2)
    with col4:
        duree = st.number_input("Durée (s)", min_value=600.0, value=7200.0, step=600.0)
    with col5:
        profil = st.selectbox("Profil de refroidissement", ["lineaire", "expo", "S_const"])

    run_crist = st.button("▶ Lancer la simulation de cristallisation", use_container_width=True)

    if run_crist:
        try:
            L, n, hist = simuler_cristallisation_batch(M, C_init, T_init, duree, dt=60.0, profil=profil)
            st.session_state["crist"] = {"L": L, "n": n, "hist": hist}
        except Exception as e:
            st.error(f"Erreur cristallisation : {e}")

    if "crist" in st.session_state:
        data = st.session_state["crist"]
        hist_df = pd.DataFrame(data["hist"])

        st.subheader("Évolution temporelle")
        cA, cB = st.columns(2)
        cC, cD = st.columns(2)

        with cA:
            st.altair_chart(line_chart(hist_df, "t", "T", "Température T(t)"), use_container_width=True)
        with cB:
            st.altair_chart(line_chart(hist_df, "t", "S", "Sursaturation S(t)"), use_container_width=True)
        with cC:
            st.altair_chart(line_chart(hist_df, "t", "Lmean", "Taille moyenne Lmean(t)"), use_container_width=True)
        with cD:
            st.altair_chart(line_chart(hist_df, "t", "CV", "Coefficient de variation CV(t)"), use_container_width=True)

        st.subheader("Distribution finale n(L)")
        dist_df = pd.DataFrame({"L": data["L"], "n": data["n"]})
        st.altair_chart(line_chart(dist_df, "L", "n", "Distribution finale n(L)"), use_container_width=True)


# =============================
# TAB 3 — SENSIBILITÉ
# =============================
with tab_sens:
    st.header("Étude de sensibilité (simple)")
    st.info("Analyse de l’influence du nombre d’effets sur la consommation de vapeur et la surface totale d’échange.")

    nmin, nmax = st.slider("Nombre d'effets (plage)", 1, 10, (2, 6), step=1)
    run_sens = st.button("▶ Lancer la sensibilité", use_container_width=True)

    if run_sens:
        rows = []
        for n in range(nmin, nmax + 1):
            r = simulation_evaporation_multi_effets(
                F_kg_h=float(F_kg_h),
                xF=float(xF),
                xout=float(xout),
                n_effets=int(n),
                T_steam_C=float(Tsteam),
                T_last_C=float(Tlast),
                U=float(U),
                lambda_kJ_kg=float(lamb),
            )
            rows.append({
                "n_effets": n,
                "S_kg_h": r["S"],
                "A_total_m2": r["A_total"],
                "economie": r["economie"],
            })
        dfS = pd.DataFrame(rows)
        st.session_state["sens_df"] = dfS

    if "sens_df" in st.session_state:
        dfS = st.session_state["sens_df"]
        a, b = st.columns(2)
        with a:
            st.altair_chart(line_chart(dfS, "n_effets", "S_kg_h", "Consommation vapeur S vs n_effets"), use_container_width=True)
        with b:
            st.altair_chart(line_chart(dfS, "n_effets", "A_total_m2", "Surface totale A vs n_effets"), use_container_width=True)
        st.dataframe(dfS, use_container_width=True)


# =============================
# TAB 4 — EXPORT
# =============================
with tab_export:
    st.header("Export")

    st.write("Téléchargements simples (CSV) depuis les derniers résultats calculés.")

    if "evap_res" in st.session_state:
        df_ev = pd.DataFrame(st.session_state["evap_res"]["details"])
        st.download_button(
            "⬇️ Télécharger résultats évaporation (CSV)",
            data=df_ev.to_csv(index=False).encode("utf-8"),
            file_name="resultats_evaporation.csv",
            mime="text/csv",
            use_container_width=True,
        )

    if "crist" in st.session_state:
        hist_df = pd.DataFrame(st.session_state["crist"]["hist"])
        st.download_button(
            "⬇️ Télécharger historique cristallisation (CSV)",
            data=hist_df.to_csv(index=False).encode("utf-8"),
            file_name="historique_cristallisation.csv",
            mime="text/csv",
            use_container_width=True,
        )

    if "sens_df" in st.session_state:
        dfS = st.session_state["sens_df"]
        st.download_button(
            "⬇️ Télécharger sensibilité (CSV)",
            data=dfS.to_csv(index=False).encode("utf-8"),
            file_name="sensibilite.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.caption("Astuce : après commit + push sur GitHub, Streamlit Cloud redéploie automatiquement.")
