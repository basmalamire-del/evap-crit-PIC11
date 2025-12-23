# streamlit_app.py
import os
import numpy as np
import pandas as pd
import streamlit as st
import altair as alt

from evaporateurs import EvaporateurMultiple
from cristallisation import simuler_cristallisation_batch

# Sensibilité : adapte si tes fonctions ont des noms différents
try:
    from sensibilite import sensibilite_parametre, sensibilite_2D
except Exception:
    # fallback si ton fichier a un nom légèrement différent
    from sensibilite import sensibilité_parametre as sensibilite_parametre  # type: ignore
    from sensibilite import sensibilité_2D as sensibilite_2D  # type: ignore


st.set_page_config(page_title="PIC — Evaporation & Cristallisation", layout="wide")

st.title("🧪 Projet — Évaporation multiple & Cristallisation du saccharose")
st.caption("Version web (Altair/interactive). Les calculs utilisent vos modèles Python.")

# -----------------------
# Sidebar paramètres
# -----------------------
st.sidebar.header("Paramètres généraux")

F = st.sidebar.number_input("Débit F (kg/h)", value=20000.0, step=500.0, min_value=1000.0)
xF = st.sidebar.slider("xF (fraction massique)", 0.01, 0.30, 0.15, 0.01)
xout = st.sidebar.slider("xout (fraction massique)", 0.20, 0.80, 0.65, 0.01)
Tfeed = st.sidebar.number_input("T_feed (°C)", value=85.0, step=1.0, min_value=10.0, max_value=150.0)
Psteam = st.sidebar.number_input("P vapeur (bar)", value=3.5, step=0.1, min_value=0.5, max_value=20.0)

tabs = st.tabs(["⚙️ Evaporation", "❄️ Cristallisation", "📈 Sensibilité", "📦 Export"])

# -----------------------
# Helpers Altair
# -----------------------
def line_chart(df, x, y, title, tooltip=None):
    tooltip = tooltip or [x, y]
    return (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X(x, title=x),
            y=alt.Y(y, title=y),
            tooltip=tooltip,
        )
        .properties(title=title, height=300)
        .interactive()
    )

def ensure_dir(p):
    os.makedirs(p, exist_ok=True)

# ==========================================================
# TAB 1 — EVAPORATION
# ==========================================================
with tabs[0]:
    st.subheader("Simulation de la batterie d’évaporation")

    n_eff = st.number_input("Nombre d'effets", value=3, step=1, min_value=1, max_value=8)

    run_evap = st.button("▶ Lancer la simulation d'évaporation", use_container_width=True)

    if run_evap:
        try:
            evap = EvaporateurMultiple(F, xF, xout, Tfeed, Psteam, int(n_eff))
            res = evap.simuler()

            # Affichage robuste (si certaines clés n’existent pas, on ne plante pas)
            c1, c2, c3 = st.columns(3)
            c1.metric("Débit vapeur S (kg/h)", f"{res.get('S', np.nan):.2f}")
            c2.metric("Économie", f"{res.get('E', np.nan):.2f}")
            c3.metric("Surface totale A (m²)", f"{res.get('A_totale', np.nan):.2f}")

            # Courbes "par effet" si dispo
            # On tente plusieurs noms possibles pour rester compatible avec tes modules
            effets = res.get("effets", None)
            if effets is None:
                # si tu n’as pas un vecteur "effets", on fabrique 1..n_eff
                effets = list(range(1, int(n_eff) + 1))

            # Essaye de récupérer concentration et débits par effet
            x_vec = res.get("x", None) or res.get("x_effects", None) or res.get("x_effets", None)
            L_vec = res.get("L", None) or res.get("debit_liquide", None)
            V_vec = res.get("V", None) or res.get("debit_vapeur", None)

            st.markdown("### Résultats par effet (courbes interactives)")

            charts = []
            if x_vec is not None:
                df_x = pd.DataFrame({"Effet": effets, "x": list(x_vec)})
                charts.append(line_chart(df_x, "Effet", "x", "Concentration x vs Effet"))

            if L_vec is not None:
                df_L = pd.DataFrame({"Effet": effets, "L (kg/h)": list(L_vec)})
                charts.append(line_chart(df_L, "Effet", "L (kg/h)", "Débit liquide L vs Effet"))

            if V_vec is not None:
                df_V = pd.DataFrame({"Effet": effets, "V (kg/h)": list(V_vec)})
                charts.append(line_chart(df_V, "Effet", "V (kg/h)", "Débit vapeur V vs Effet"))

            # Affichage 2 graphes par ligne
            for i in range(0, len(charts), 2):
                colA, colB = st.columns(2)
                with colA:
                    st.altair_chart(charts[i], use_container_width=True)
                if i + 1 < len(charts):
                    with colB:
                        st.altair_chart(charts[i + 1], use_container_width=True)

            if not charts:
                st.info("Aucune série 'x', 'L' ou 'V' trouvée dans res. (Ton module evap renvoie peut-être d’autres clés.)")

            st.success("✅ Evaporation terminée")

        except Exception as e:
            st.error(f"Erreur evaporation : {e}")


# ==========================================================
# TAB 2 — CRISTALLISATION
# ==========================================================
with tabs[1]:
    st.subheader("Cristallisation batch")

    M = st.number_input("Masse de solution M (kg)", value=5000.0, step=100.0, min_value=100.0)
    C_init = st.number_input("Concentration initiale C_init (g/100g)", value=65.0, step=0.5, min_value=1.0)
    T_init = st.number_input("Température initiale T_init (°C)", value=70.0, step=1.0, min_value=10.0, max_value=120.0)
    duree_h = st.number_input("Durée (heures)", value=4.0, step=0.5, min_value=0.5)
    dt = st.number_input("Pas de temps dt (s)", value=60.0, step=10.0, min_value=10.0)

    profil = st.selectbox("Profil de refroidissement", ["lineaire", "expo", "S_const"], index=0)

    run_crist = st.button("▶ Lancer la simulation de cristallisation", use_container_width=True)

    if run_crist:
        try:
            L, n, hist = simuler_cristallisation_batch(
                M=float(M),
                C_init=float(C_init),
                T_init=float(T_init),
                duree=float(duree_h) * 3600.0,
                dt=float(dt),
                profil=str(profil),
            )

            # DataFrame temporel
            df = pd.DataFrame(hist)
            df["t_min"] = df["t"] / 60.0

            c1, c2, c3 = st.columns(3)
            c1.metric("Lmean final (m)", f"{df['Lmean'].iloc[-1]:.3e}")
            c2.metric("CV final", f"{df['CV'].iloc[-1]:.3f}")
            c3.metric("S final", f"{df['S'].iloc[-1]:.3f}")

            st.markdown("### Evolution temporelle (2 graphes par ligne)")

            ch1 = line_chart(df, "t_min", "T", "Température T(t)", tooltip=["t_min", "T"])
            ch2 = line_chart(df, "t_min", "C", "Concentration C(t)", tooltip=["t_min", "C"])
            ch3 = line_chart(df, "t_min", "Cs", "Solubilité Cs(t)", tooltip=["t_min", "Cs"])
            ch4 = line_chart(df, "t_min", "S", "Sursaturation S(t)", tooltip=["t_min", "S"])
            ch5 = line_chart(df, "t_min", "Lmean", "Taille moyenne Lmean(t)", tooltip=["t_min", "Lmean"])
            ch6 = line_chart(df, "t_min", "CV", "Coefficient de variation CV(t)", tooltip=["t_min", "CV"])

            for a, b in [(ch1, ch2), (ch3, ch4), (ch5, ch6)]:
                colA, colB = st.columns(2)
                with colA:
                    st.altair_chart(a, use_container_width=True)
                with colB:
                    st.altair_chart(b, use_container_width=True)

            # Distribution finale n(L)
            df_n = pd.DataFrame({"L (m)": L, "n(L)": n})
            ch_dist = (
                alt.Chart(df_n)
                .mark_line(point=False)
                .encode(x=alt.X("L (m)", title="L (m)"), y=alt.Y("n(L)", title="n(L)"), tooltip=["L (m)", "n(L)"])
                .properties(title="Distribution finale n(L)", height=320)
                .interactive()
            )
            st.altair_chart(ch_dist, use_container_width=True)

            st.success("✅ Cristallisation terminée")

        except Exception as e:
            st.error(f"Erreur cristallisation : {e}")


# ==========================================================
# TAB 3 — SENSIBILITE
# ==========================================================
with tabs[2]:
    st.subheader("Étude de sensibilité (1D / 2D)")

    st.markdown("#### Sensibilité 1D")
    param = st.selectbox("Paramètre", ["F", "xF", "xout", "Tfeed", "Psteam"], index=0)

    run_sens1 = st.button("▶ Lancer sensibilité 1D", use_container_width=True)

    if run_sens1:
        try:
            # ta fonction doit renvoyer (val, S, A, E) comme dans ton main.py
            val, S, A, E = sensibilite_parametre(F, xF, xout, Tfeed, Psteam, param=param)

            df1 = pd.DataFrame({param: val, "S (kg/h)": S, "A_totale (m²)": A, "Economie": E})

            chS = line_chart(df1, param, "S (kg/h)", f"S vs {param}")
            chA = line_chart(df1, param, "A_totale (m²)", f"A_totale vs {param}")
            chE = line_chart(df1, param, "Economie", f"Economie vs {param}")

            # 2 par ligne
            cA, cB = st.columns(2)
            with cA:
                st.altair_chart(chS, use_container_width=True)
            with cB:
                st.altair_chart(chA, use_container_width=True)
            st.altair_chart(chE, use_container_width=True)

            st.dataframe(df1, use_container_width=True)
            st.success("✅ Sensibilité 1D terminée")

        except Exception as e:
            st.error(f"Erreur sensibilité 1D : {e}")

    st.markdown("---")
    st.markdown("#### Sensibilité 2D")
    col1, col2 = st.columns(2)
    with col1:
        p1 = st.selectbox("Paramètre 1", ["F", "xF", "xout", "Tfeed", "Psteam"], index=0, key="p1")
    with col2:
        p2 = st.selectbox("Paramètre 2", ["F", "xF", "xout", "Tfeed", "Psteam"], index=1, key="p2")

    run_sens2 = st.button("▶ Lancer sensibilité 2D", use_container_width=True)

    if run_sens2:
        try:
            # On suppose que ta fonction renvoie une grille (df ou arrays). On rend robuste.
            out = sensibilite_2D(F, xF, xout, Tfeed, Psteam, p1=p1, p2=p2)

            # Si la fonction renvoie déjà un DataFrame long (p1,p2,metric)
            if isinstance(out, pd.DataFrame):
                df2 = out.copy()
            else:
                # sinon essayer de le convertir (à adapter selon ton code)
                df2 = pd.DataFrame(out)

            st.dataframe(df2, use_container_width=True)
            st.success("✅ Sensibilité 2D terminée")

        except Exception as e:
            st.error(f"Erreur sensibilité 2D : {e}")


# ==========================================================
# TAB 4 — EXPORT
# ==========================================================
with tabs[3]:
    st.subheader("Export (CSV)")

    st.info("Cette version exporte en CSV (plus stable que générer un PDF LaTeX sur Streamlit Cloud).")

    export_dir = "exports"
    ensure_dir(export_dir)

    if st.button("📥 Exporter un exemple de template CSV", use_container_width=True):
        df_template = pd.DataFrame(
            {"info": ["Evaporation", "Cristallisation", "Sensibilité"], "commentaire": ["ok", "ok", "ok"]}
        )
        path = os.path.join(export_dir, "export_template.csv")
        df_template.to_csv(path, index=False)
        with open(path, "rb") as f:
            st.download_button("Télécharger export_template.csv", f, file_name="export_template.csv")
