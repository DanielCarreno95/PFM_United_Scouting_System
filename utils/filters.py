import streamlit as st
import pandas as pd


def sidebar_filters(df: pd.DataFrame):
    """
    Filtros laterales globales unificados para todas las páginas del proyecto.
    Devuelve el dataframe filtrado según los parámetros seleccionados.
    """

    # ==============================
    # 🎨 ESTILOS MODERNOS PARA SIDEBAR
    # ==============================
    st.markdown("""
        <style>
        /* Fondo oscuro con gradiente sutil */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #13090a 0%, #1b1b1b 100%) !important;
            color: #e5e7eb !important;
            border-right: 1px solid rgba(218,41,28,0.35);
            padding-top: 1rem !important;
        }

        /* 🔥 Ocultar solo la PRIMERA opción del menú lateral ("app") */
        section[data-testid="stSidebar"] div[data-testid="stSidebarNav"] [role="radiogroup"] > label:first-child {
            display: none !important;
        }
        section[data-testid="stSidebar"] [role="radiogroup"] > label:first-child {
            display: none !important;
        }
        section[data-testid="stSidebar"] nav ul li:first-child {
            display: none !important;
        }

        /* Tipografía y colores del texto */
        section[data-testid="stSidebar"] h1, 
        section[data-testid="stSidebar"] h2, 
        section[data-testid="stSidebar"] h3, 
        section[data-testid="stSidebar"] p, 
        section[data-testid="stSidebar"] label {
            color: #e5e7eb !important;
            font-weight: 500 !important;
        }

        /* Controles multiselect y selectbox */
        div[data-baseweb="select"] > div {
            background-color: #1f2937 !important;
            border-radius: 8px !important;
            border: 1px solid #374151 !important;
        }

        div[data-baseweb="select"]:hover > div {
            border-color: #DA291C !important;
        }

        /* Slider color */
        div[data-testid="stSlider"] > div > div > div {
            background-color: #DA291C !important;
        }

        /* Botones */
        div[data-testid="stButton"] button {
            background: linear-gradient(90deg, #9A0000, #DA291C);
            color: white;
            font-weight: 600;
            border-radius: 8px;
            border: none;
            transition: all 0.3s ease;
        }
        div[data-testid="stButton"] button:hover {
            background: linear-gradient(90deg, #DA291C, #FBE122);
            transform: translateY(-1px);
            box-shadow: 0 4px 10px rgba(218, 41, 28, 0.35);
        }

        /* Separadores y márgenes */
        section[data-testid="stSidebar"] hr {
            border-color: rgba(255,255,255,0.1);
        }

        /* Espaciado más limpio */
        section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] {
            gap: 0.7rem !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # ==============================
    # FILTROS
    # ==============================
    st.sidebar.header("Filtros de scouting")

    DEFAULTS = {
        "league_sel": [],
        "team_sel": [],
        "age_range": (int(df["age"].min()), int(df["age"].max())),
        "min_range": (
            max(int(df["min"].min()), 180) if int(df["min"].max()) >= 180 else int(df["min"].min()),
            int(df["min"].max())
        ),
        "role_sel": [],
        "pos_sel": [],
    }

    leagues = sorted(df["league"].dropna().astype(str).unique())
    if len(leagues) <= 1:
        lab = leagues[0] if leagues else "Premier League"
        st.sidebar.markdown(f"**Competición activa:** {lab}")
        league_sel = []
        st.session_state["league_sel"] = []
    else:
        league_sel = st.sidebar.multiselect(
            "Competición",
            leagues,
            default=st.session_state.get("league_sel", []),
            placeholder="Una o varias",
        )
        st.session_state["league_sel"] = league_sel

    team_sel = st.sidebar.multiselect(
        "Equipo",
        sorted(df["squad"].dropna().unique()),
        default=st.session_state.get("team_sel", []),
        placeholder="Uno o varios",
    )
    st.session_state["team_sel"] = team_sel

    age_range = st.sidebar.slider(
        "Edad",
        int(df["age"].min()), int(df["age"].max()),
        st.session_state.get("age_range", (int(df["age"].min()), int(df["age"].max()))),
    )
    st.session_state["age_range"] = age_range

    min_range = st.sidebar.slider(
        "Minutos jugados",
        int(df["min"].min()), int(df["min"].max()),
        st.session_state.get("min_range", (int(df["min"].min()), int(df["min"].max()))),
    )
    st.session_state["min_range"] = min_range

    role_sel = st.sidebar.multiselect(
        "Puesto de juego",
        sorted(df["rol_tactico"].dropna().astype(str).unique()),
        default=st.session_state.get("role_sel", []),
        placeholder="Todos (si se deja vacío)",
    )
    st.session_state["role_sel"] = role_sel

    pos_col = "pos" if "pos" in df.columns else None
    if pos_col:
        pos_opts = sorted(df[pos_col].dropna().astype(str).unique())
        pos_sel = st.sidebar.multiselect(
            "Posición natural",
            pos_opts,
            default=st.session_state.get("pos_sel", []),
            placeholder="Todas (si se deja vacío)",
            help="Posición declarada en la fuente. Útil para acotar búsquedas por perfil de juego.",
        )
        st.session_state["pos_sel"] = pos_sel
    else:
        pos_sel = []
        st.session_state.pop("pos_sel", None)

    # ==============================
    # APLICAR FILTROS
    # ==============================
    f = df.copy()
    if league_sel:
        f = f[f["league"].isin(league_sel)]
    if team_sel:
        f = f[f["squad"].isin(team_sel)]
    f = f[(f["age"].between(*age_range)) & (f["min"].between(*min_range))]
    if role_sel:
        f = f[f["rol_tactico"].astype(str).isin(role_sel)]
    if pos_sel and pos_col:
        f = f[f[pos_col].astype(str).isin(pos_sel)]

    st.sidebar.markdown(f"**Jugadores en radar:** {len(f):,}")
    st.sidebar.caption("Consejo de secretaría técnica: usar al menos 300' para lecturas más estables.")

    # ==============================
    # BOTÓN RESET
    # ==============================
    def reset_global_filters():
        for k, v in DEFAULTS.items():
            st.session_state[k] = v
        st.session_state.pop("season_sel", None)  # limpieza de estado heredado
        st.rerun()

    st.sidebar.button("🔄 Restablecer filtros", on_click=reset_global_filters)

    # ==============================
    # BOTÓN CERRAR SESIÓN
    # ==============================
    st.sidebar.markdown("---")
    if st.sidebar.button("Cerrar sesión"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.session_state["auth"] = False
        st.session_state["page"] = "login"
        st.success("Sesión cerrada correctamente. Redirigiendo al inicio...")
        st.switch_page("app.py")

    return f


# ==============================
# Alias para compatibilidad
# ==============================
render_global_filters = sidebar_filters
