# ===========================================
# app.py — Plataforma de Scouting (FINAL FUNCIONAL)
# ===========================================

import streamlit as st
import os
from dotenv import load_dotenv
from pathlib import Path
import time

# ===========================================
# CONFIGURACIÓN GLOBAL
# ===========================================
dotenv_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=dotenv_path, override=True)

USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

st.set_page_config(
    page_title="United Elite Scouting Hub",
    page_icon="⚽",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# -------------------------------------------
# Router: si llega ?go=... -> st.switch_page
# -------------------------------------------
def _handle_go_param():
    # Soporte nuevas y viejas versiones de Streamlit para query params
    try:
        qp = st.query_params
        go = qp.get("go", None)
    except Exception:
        qp = st.experimental_get_query_params()
        go = qp.get("go", [None])[0] if isinstance(qp.get("go"), list) else qp.get("go")

    if not go:
        return

    mapping = {
        "overview":   "pages/1_Overview.py",
        "ranking":    "pages/2_Ranking.py",
        "comparador": "pages/3_Comparador.py",
        "similares":  "pages/4_Similares.py",
    }

    page = mapping.get(str(go).lower())
    if page:
        # Limpiamos el parámetro y navegamos en la MISMA pestaña
        try:
            st.query_params.clear()
        except Exception:
            st.experimental_set_query_params()
        st.switch_page(page)

# Llamar al router lo antes posible
_handle_go_param()

# ===========================================
# LOGIN PAGE
# ===========================================
def login_page():
    st.markdown("""
        <style>
        [data-testid="stSidebar"], [data-testid="stToolbar"], header[data-testid="stHeader"] {
            display: none !important;
        }
        [data-testid="stAppViewContainer"] {
            background:
              linear-gradient(rgba(6,11,25,0.8), rgba(6,11,25,0.9)),
              url("https://images.pexels.com/photos/399187/pexels-photo-399187.jpeg?auto=compress&cs=tinysrgb&w=1920");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }
        div.block-container > div:first-child:empty {
            background: rgba(17, 24, 39, 0.85);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px;
            box-shadow: 0 15px 40px rgba(0,0,0,0.45);
            backdrop-filter: blur(10px);
            width: 460px;
            padding: 2.5rem 2.5rem;
            margin: auto;
            display: flex !important;
            flex-direction: column;
            justify-content: center;
            align-items: stretch;
            transform: translateY(15vh);
        }
        div.block-container {
            display: flex !important;
            justify-content: center !important;
            align-items: flex-start !important;
            height: 100vh !important;
            padding-top: 0 !important;
        }
        .login-title {
            font-size: 1.7rem;
            font-weight: 800;
            color: #DA291C;
            margin-bottom: .3rem;
            text-align: center;
        }
        .login-sub {
            text-align: center;
            color: #b5c0ce;
            font-size: .95rem;
            margin-bottom: 1.5rem;
        }
        label { color: #d7dee8 !important; font-weight: 600 !important; }
        input[type="text"], input[type="password"] {
            background-color: #0f1625 !important;
            color: #e8eef7 !important;
            border: 1px solid rgba(255,255,255,0.12) !important;
            border-radius: 10px !important;
            height: 44px !important;
        }
        button[kind="primary"] {
            background: linear-gradient(90deg,#9A0000,#DA291C) !important;
            border-radius: 10px !important;
            color: white !important;
            height: 44px !important;
            font-weight: 700 !important;
            border: none !important;
        }
        button[kind="primary"]:hover {
            filter: brightness(1.1);
            box-shadow: 0 0 20px rgba(218,41,28,0.35);
        }
        </style>
    """, unsafe_allow_html=True)

    placeholder = st.empty()
    with placeholder.container():
        st.markdown('<div class="login-title">United Elite Scouting Hub</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-sub">Plataforma de inteligencia deportiva para direccion tecnica y scouting de alto rendimiento</div>', unsafe_allow_html=True)
        user = st.text_input("Usuario", placeholder="Introduce tu usuario")
        pwd = st.text_input("Contraseña", placeholder="Introduce tu contraseña", type="password")
        if st.button("Iniciar sesión", use_container_width=True):
            if user == USERNAME and pwd == PASSWORD:
                st.session_state["auth"] = True
                st.session_state["page"] = "hub"
                st.success("Inicio de sesión correcto ✅")
                time.sleep(0.8)
                st.rerun()
            else:
                st.error("Credenciales incorrectas ❌")

# ===========================================
# HUB PAGE (CENTRO DE NAVEGACIÓN)
# ===========================================

def main_hub():
    import streamlit.components.v1 as components

    # ======== CSS ========
    st.markdown("""
        <style>
        [data-testid="stSidebar"], [data-testid="stToolbar"], header[data-testid="stHeader"] {
            display: none !important;
        }
        [data-testid="stAppViewContainer"] {
            background:
              linear-gradient(rgba(6,11,25,0.85), rgba(6,11,25,0.9)),
              url("https://images.pexels.com/photos/399187/pexels-photo-399187.jpeg?auto=compress&cs=tinysrgb&w=1920");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }

        .hub-title {
            font-size: 2.6rem;
            font-weight: 800;
            color: #DA291C;
            text-align: center;
            margin-top: 6vh;
            margin-bottom: 0.4rem;
            text-shadow: 0 0 10px rgba(218,41,28,0.45);
        }

        .hub-subtitle {
            text-align: center;
            color: #cfd6df;
            font-size: 1rem;
            margin-bottom: 3rem;
        }

        .module-card {
            background: rgba(17,24,39,0.9);
            border: 1.5px solid rgba(218,41,28,0.35);
            border-radius: 18px;
            height: 230px;
            padding: 24px 16px;
            text-align: center;
            color: #DA291C;
            box-shadow: 0 10px 25px rgba(0,0,0,0.35);
            transition: all 0.3s ease;
            cursor: pointer;
        }

        .module-card:hover {
            transform: translateY(-6px);
            background: rgba(22,30,50,0.98);
            border-color: rgba(251,225,34,0.8);
            box-shadow: 0 15px 35px rgba(218,41,28,0.28);
        }

        .module-title {
            color: #DA291C;
            font-size: 1.3rem;
            font-weight: 800;
            margin-bottom: .7rem;
        }

        .module-desc {
            font-size: 0.93rem;
            color: #ffffff;
            line-height: 1.4;
            max-width: 230px;
            margin: 0 auto;
        }
        </style>
    """, unsafe_allow_html=True)

    # ======== TITULOS ========
    st.markdown("<div class='hub-title'>United Elite Scouting Hub</div>", unsafe_allow_html=True)
    st.markdown("<div class='hub-subtitle'>Plataforma profesional para direccion tecnica, reclutamiento y analitica de rendimiento</div>", unsafe_allow_html=True)

    # ======== MÓDULOS ========
    modules = [
        ("Overview", "Contexto competitivo de Premier 2025/26 para decisiones de direccion deportiva.", "pages/1_Overview.py"),
        ("Ranking", "Prioriza targets por rendimiento y encaje para Manchester United.", "pages/2_Ranking.py"),
        ("Comparador", "Contrasta perfiles y percentiles de candidatos clave.", "pages/3_Comparador.py"),
        ("Similares", "Localiza alternativas de mercado con patrón estadístico equivalente.", "pages/4_Similares.py"),
    ]

    # ======== FILA 1 (2 TARJETAS) ========
    cols1 = st.columns(2, gap="large")
    for i, (title, desc, page) in enumerate(modules[:2]):
        with cols1[i]:
            if st.button(f"**{title}**", use_container_width=True, key=f"btn_{i}"):
                st.switch_page(page)
            st.markdown(
                f"<p style='text-align:center; color:#FF6B61; margin-top:10px;'>{desc}</p>",
                unsafe_allow_html=True
            )

    # ======== ESPACIADOR ========
    st.markdown("<br><br>", unsafe_allow_html=True)

    # ======== FILA 2 (2 TARJETAS) ========
    cols2 = st.columns(2, gap="large")
    for j, (title, desc, page) in enumerate(modules[2:]):
        with cols2[j]:
            if st.button(f"**{title}**", use_container_width=True, key=f"btn_b_{j}"):
                st.switch_page(page)
            st.markdown(
                f"<p style='text-align:center; color:#FF6B61; margin-top:10px;'>{desc}</p>",
                unsafe_allow_html=True
            )

# ===========================================
# CONTROL DE AUTENTICACIÓN Y FLUJO
# ===========================================
if "auth" not in st.session_state:
    st.session_state["auth"] = False
    st.session_state["page"] = "login"

if not st.session_state["auth"]:
    login_page()
else:
    if st.session_state.get("page") != "hub":
        st.session_state["page"] = "hub"
    main_hub()
