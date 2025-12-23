import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

from evaporateurs import EvaporateurMultiple
from cristallisation import simuler_cristallisation_batch

# --- Import robust des fonctions de sensibilité (selon comment tu as nommé dans sensibilite.py)
try:
    from sensibilite import sensibilite_parametre, sensibilite_2D
except Exception:
    # Si tu as des noms légèrement différents, on tente d'autres variantes
    from sensibilite import sensibilité_parametre as sensibilite_parametre  # type: ignore
    from sensibilite import sensibilité_2D as sensibilite_2D  # type: ignore


# -----------------------------
# Helpers (robustes)
# -----------------------------
def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def pick_key(d: dict, keys: list[str], default=None):
    """Retourne la première clé trouvée dans d, sinon default."""
    for k in keys:
        if k in d:
            return d[k]
    return default


def save_fig(fig, filename: str):
    ensure_dir("figures")
    path = os.path.join("figures", filename)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    return path


# -----------------------------
# Config Streamlit
# -----------------------------
st.set_page_config(page_title="Projet", layout="wide")
st.title("🧪 Projet  — Évaporation multiple & Cristallisation du saccharose")
st.caption("Version sans LaTeX / sans PDF : export CSV + figures PNG (plus stable).")

# Init session state (pour éviter erreurs avant clic)
if "evap_res" not in st.session_state:
    st.session_state.evap_res = None
if "crist_hist" not in st.session_state:
    st.session_state.crist_hist = None
if "sensi_1d" not in st.session_state:
    st.session_state.sensi_1d = None
if "sensi_2d" not in st.session_state:
    st.session_state.sensi_2d = None


# -----------------------------
# Sidebar : paramètres
# -----------------------------
st.sidebar.header("Paramètres")

st.sidebar.subheader("Évaporation")
F = st.sidebar.number_input("Débit F (kg/h)", value=20000.0, step=1000.0)
xF = st.sidebar.slider("xF (fraction massique)", 0.05, 0.25, 0.15, 0.01)
xout = st.sidebar.slider("xout (fraction massique)", 0.40, 0.80, 0.65, 0.01)
Tfeed = st.sidebar.number_input("T_feed (°C)", value=85.0, step=1.0)
Psteam = st.sidebar.slider("P vapeur (bar)", 2.0, 5.0, 3.5, 0.1)
n_effets = st.sidebar.slider("Nombre d'effets", 2, 5, 3, 1)

st.sidebar.divider()

st.sidebar.subheader("Cristallisation (batch)")
M_batch = st.sidebar.number_input("Masse sirop (kg)", value=5000.0, step=500.0)
C_init = st.sidebar.number_input("C_init (g/100g)", value=65.0, step=1.0)
T_init = st.sidebar.number_input("T_init (°C)", value=70.0, step=1.0)
duree_h = st.sidebar.number_input("Durée (h)", value=4.0, step=0.5)
dt_s = st.sidebar.number_input("Pas de temps dt (s)", value=60.0, step=10.0)
profil = st.sidebar.selectbox("Profil refroidissement", ["lineaire", "expo", "S_const"])

st.sidebar.divider()

st.sidebar.subheader("Sensibilité")
param_1d = st.sidebar.selectbox("Paramètre 1D", ["F", "xF", "xout", "Tfeed", "Psteam", "n_effets"])
npoints_1d = st.sidebar.slider("Nb points 1D", 5, 21, 9, 2)

# -----------------------------
# Tabs
# -----------------------------
tab_evap, tab_crist, tab_sensi, tab_export = st.tabs(
    ["⚙️ Évaporation", "❄️ Cristallisation", "📈 Sensibilité", "📥 Export"]
)

# =========================================================
# TAB 1 : Evaporation
# =========================================================
with tab_evap:
    st.subheader("Simulation de la batterie d’évaporation")

    if st.button("▶️ Lancer la simulation d'évaporation"):
        try:
            evap = EvaporateurMultiple(F, xF, xout, Tfeed, Psteam, n_effets)
            res = evap.simuler()
            st.session_state.evap_res = res
        except Exception as e:
            st.error(f"Erreur évaporation : {e}")
            st.session_state.evap_res = None

    res = st.session_state.evap_res

    if res is None:
        st.info("Clique sur **Lancer la simulation d'évaporation** pour afficher les résultats.")
    else:
        # Récupération robuste des clés
        S = pick_key(res, ["S", "m_steam", "vapeur", "steam", "m_vapeur"], default=None)
        E = pick_key(res, ["E", "economie", "econ"], default=None)
        A_tot = pick_key(res, ["A_totale", "A_total", "A_tot"], default=None)

        x = pick_key(res, ["x", "X", "x_effets"], default=None)
        T = pick_key(res, ["T", "T_effets", "Teb", "T_eb"], default=None)
        A = pick_key(res, ["A", "A_effets"], default=None)
        L = pick_key(res, ["L", "L_effets", "debit_liquide"], default=None)
        V = pick_key(res, ["V", "V_effets", "debit_vapeur"], default=None)

        # si x est une liste => nb effets
        if x is not None:
            effets = np.arange(1, len(x) + 1)
        elif A is not None:
            effets = np.arange(1, len(A) + 1)
        else:
            effets = np.arange(1, n_effets + 1)

        # KPI
        c1, c2, c3 = st.columns(3)
        c1.metric("Débit vapeur (S)", "-" if S is None else f"{float(S):.2f} kg/h")
        c2.metric("Économie (E)", "-" if E is None else f"{float(E):.3f}")
        c3.metric("Surface totale", "-" if A_tot is None else f"{float(A_tot):.1f} m²")

        st.markdown("### Courbes (2 par ligne)")

        col1, col2 = st.columns(2)
        with col1:
            fig, ax = plt.subplots()
            if T is not None:
                ax.plot(effets, T, marker="o")
            ax.set_xlabel("Effet")
            ax.set_ylabel("Teb (°C)")
            ax.set_title("Température d'ébullition par effet")
            ax.grid(True)
            st.pyplot(fig)
            save_fig(fig, "evap_Teb.png")

        with col2:
            fig, ax = plt.subplots()
            if A is not None:
                ax.bar(effets, A)
            ax.set_xlabel("Effet")
            ax.set_ylabel("A (m²)")
            ax.set_title("Surface d'échange par effet")
            ax.grid(True)
            st.pyplot(fig)
            save_fig(fig, "evap_A.png")

        col3, col4 = st.columns(2)
        with col3:
            fig, ax = plt.subplots()
            if x is not None:
                ax.plot(effets, x, marker="o")
            ax.set_xlabel("Effet")
            ax.set_ylabel("x (fraction massique)")
            ax.set_title("Concentration en fonction des effets")
            ax.grid(True)
            st.pyplot(fig)
            save_fig(fig, "evap_x.png")

        with col4:
            fig, ax = plt.subplots()
            if (L is not None) and (V is not None):
                ax.plot(effets, L, marker="o", label="L (kg/h)")
                ax.plot(effets, V, marker="s", label="V (kg/h)")
                ax.legend()
            ax.set_xlabel("Effet")
            ax.set_ylabel("Débits (kg/h)")
            ax.set_title("Débits liquide et vapeur vs effets")
            ax.grid(True)
            st.pyplot(fig)
            save_fig(fig, "evap_LV.png")

        # Tableau
        st.markdown("### Tableau des résultats")
        df = pd.DataFrame({"Effet": effets})
        if x is not None:
            df["x"] = x
        if T is not None:
            df["Teb (°C)"] = T
        if A is not None:
            df["A (m²)"] = A
        if L is not None:
            df["L (kg/h)"] = L
        if V is not None:
            df["V (kg/h)"] = V
        st.dataframe(df, use_container_width=True)


# =========================================================
# TAB 2 : Cristallisation
# =========================================================
with tab_crist:
    st.subheader("Cristallisation batch")

    if st.button("▶️ Lancer la simulation de cristallisation"):
        try:
            duree_s = int(duree_h * 3600)
            _, _, hist = simuler_cristallisation_batch(
                M_batch, C_init, T_init, duree_s, dt=float(dt_s), profil=profil
            )
            st.session_state.crist_hist = hist
        except Exception as e:
            st.error(f"Erreur cristallisation : {e}")
            st.session_state.crist_hist = None

    hist = st.session_state.crist_hist

    if hist is None:
        st.info("Clique sur **Lancer la simulation de cristallisation**.")
    else:
        t = np.array(pick_key(hist, ["t", "time"], default=[]))

        # Clés possibles (tu avais L_moy dans ton ancien main)
        T = pick_key(hist, ["T"], default=None)
        S = pick_key(hist, ["S"], default=None)
        C = pick_key(hist, ["C"], default=None)
        Cs = pick_key(hist, ["Cs", "Cstar", "C_eq"], default=None)

        Lmean = pick_key(hist, ["Lmean", "L_moy"], default=None)
        CV = pick_key(hist, ["CV"], default=None)

        c1, c2 = st.columns(2)
        c1.metric("L moyen final", "-" if Lmean is None else f"{float(Lmean[-1]):.3e} m")
        c2.metric("CV final", "-" if CV is None else f"{float(CV[-1]):.3f}")

        st.markdown("### Courbes (2 par ligne)")
        col1, col2 = st.columns(2)
        with col1:
            fig, ax = plt.subplots()
            if (t.size > 0) and (T is not None):
                ax.plot(t, T, label="T (°C)")
            if (t.size > 0) and (S is not None):
                ax.plot(t, S, label="S")
            ax.set_xlabel("Temps (s)")
            ax.set_title("Température et sursaturation")
            ax.grid(True)
            ax.legend()
            st.pyplot(fig)
            save_fig(fig, "crist_TS.png")

        with col2:
            fig, ax = plt.subplots()
            if (t.size > 0) and (Lmean is not None):
                ax.plot(t, Lmean, label="Lmean (m)")
            if (t.size > 0) and (CV is not None):
                ax.plot(t, CV, label="CV")
            ax.set_xlabel("Temps (s)")
            ax.set_title("Taille moyenne et CV")
            ax.grid(True)
            ax.legend()
            st.pyplot(fig)
            save_fig(fig, "crist_Lmean_CV.png")

        col3, col4 = st.columns(2)
        with col3:
            fig, ax = plt.subplots()
            if (t.size > 0) and (C is not None):
                ax.plot(t, C, label="C (g/100g)")
            if (t.size > 0) and (Cs is not None):
                ax.plot(t, Cs, label="C* (solubilité)")
            ax.set_xlabel("Temps (s)")
            ax.set_ylabel("g/100g")
            ax.set_title("Concentration et solubilité")
            ax.grid(True)
            ax.legend()
            st.pyplot(fig)
            save_fig(fig, "crist_C_Cs.png")

        with col4:
            st.markdown("**Notes**")
            st.write("- C* : solubilité (équilibre).")
            st.write("- S : sursaturation (dépend du modèle).")
            st.write("- Lmean et CV : qualité granulométrique.")


# =========================================================
# TAB 3 : Sensibilité
# =========================================================
with tab_sensi:
    st.subheader("Étude de sensibilité")

    st.write("Sensibilité 1D : on fait varier un paramètre autour de sa valeur.")
    if st.button("▶️ Calculer sensibilité 1D"):
        try:
            facteurs = np.linspace(0.5, 1.5, int(npoints_1d))
            vals, S_list, A_list, E_list = sensibilite_parametre(
                F, xF, xout, Tfeed, Psteam, param=param_1d, valeurs=facteurs
            )
            st.session_state.sensi_1d = (vals, S_list, A_list, E_list)
        except Exception as e:
            st.error(f"Erreur sensibilité 1D : {e}")
            st.session_state.sensi_1d = None

    sens1d = st.session_state.sensi_1d
    if sens1d is not None:
        vals, S_list, A_list, E_list = sens1d

        # Axe x réel
        base = {"F": F, "xF": xF, "xout": xout, "Tfeed": Tfeed, "Psteam": Psteam, "n_effets": n_effets}[param_1d]
        x_axis = np.array(vals) * float(base)

        col1, col2 = st.columns(2)
        with col1:
            fig, ax = plt.subplots()
            ax.plot(x_axis, S_list, marker="o", label="S")
            ax.plot(x_axis, A_list, marker="s", label="A_tot")
            ax.set_xlabel(param_1d)
            ax.set_title("Sensibilité 1D : S et A_tot")
            ax.grid(True)
            ax.legend()
            st.pyplot(fig)
            save_fig(fig, "sens_1D_S_A.png")

        with col2:
            fig, ax = plt.subplots()
            ax.plot(x_axis, E_list, marker="o", label="E")
            ax.set_xlabel(param_1d)
            ax.set_title("Sensibilité 1D : Économie E")
            ax.grid(True)
            ax.legend()
            st.pyplot(fig)
            save_fig(fig, "sens_1D_E.png")

    st.divider()
    st.write("Sensibilité 2D : carte de E en fonction de deux paramètres.")
    if st.button("▶️ Calculer sensibilité 2D (E en fonction de F et Psteam)"):
        try:
            X, Y, Egrid = sensibilite_2D(
                F, xF, xout, Tfeed, Psteam, param1="F", param2="Psteam", n1=11, n2=11
            )
            st.session_state.sensi_2d = (X, Y, Egrid)
        except Exception as e:
            st.error(f"Erreur sensibilité 2D : {e}")
            st.session_state.sensi_2d = None

    sens2d = st.session_state.sensi_2d
    if sens2d is not None:
        X, Y, Egrid = sens2d
        fig, ax = plt.subplots()
        cp = ax.contourf(X, Y, Egrid, levels=15)
        fig.colorbar(cp, ax=ax, label="E")
        ax.set_xlabel("F (kg/h)")
        ax.set_ylabel("Psteam (bar)")
        ax.set_title("Carte de sensibilité : E(F, Psteam)")
        st.pyplot(fig)
        save_fig(fig, "sens_2D.png")


# =========================================================
# TAB 4 : Export
# =========================================================
with tab_export:
    st.subheader("Export des résultats (CSV) & Figures (PNG)")
    ensure_dir("figures")

    st.write("✅ Les figures sont automatiquement enregistrées dans le dossier `figures/` après chaque simulation.")

    # Export Evaporation CSV
    if st.session_state.evap_res is not None:
        res = st.session_state.evap_res
        x = pick_key(res, ["x", "X", "x_effets"], default=None)
        T = pick_key(res, ["T", "T_effets", "Teb", "T_eb"], default=None)
        A = pick_key(res, ["A", "A_effets"], default=None)
        L = pick_key(res, ["L", "L_effets"], default=None)
        V = pick_key(res, ["V", "V_effets"], default=None)

        if x is not None:
            effets = np.arange(1, len(x) + 1)
        elif A is not None:
            effets = np.arange(1, len(A) + 1)
        else:
            effets = np.arange(1, n_effets + 1)

        df_evap = pd.DataFrame({"Effet": effets})
        if x is not None: df_evap["x"] = x
        if T is not None: df_evap["Teb (°C)"] = T
        if A is not None: df_evap["A (m²)"] = A
        if L is not None: df_evap["L (kg/h)"] = L
        if V is not None: df_evap["V (kg/h)"] = V

        csv = df_evap.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Télécharger CSV évaporation", data=csv,
                           file_name="evaporation_resultats.csv", mime="text/csv")
    else:
        st.info("Export évaporation : lance d'abord la simulation d'évaporation.")

    st.divider()

    # Export Cristallisation CSV
    if st.session_state.crist_hist is not None:
        hist = st.session_state.crist_hist
        t = np.array(pick_key(hist, ["t"], default=[]))
        df_cr = pd.DataFrame({"t (s)": t})

        for colname, keys in [
            ("T (°C)", ["T"]),
            ("S", ["S"]),
            ("C (g/100g)", ["C"]),
            ("Cs (g/100g)", ["Cs", "Cstar"]),
            ("Lmean (m)", ["Lmean", "L_moy"]),
            ("CV", ["CV"]),
        ]:
            arr = pick_key(hist, keys, default=None)
            if arr is not None:
                df_cr[colname] = arr

        csv = df_cr.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Télécharger CSV cristallisation", data=csv,
                           file_name="cristallisation_resultats.csv", mime="text/csv")
    else:
        st.info("Export cristallisation : lance d'abord la simulation de cristallisation.")

    st.divider()

    st.markdown("### 📁 Dossier figures")
    st.code(os.path.abspath("figures"))
    st.write("Tu peux ouvrir ce dossier et récupérer toutes les images PNG générées.")
