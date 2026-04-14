# =====================================
# pages/4_Similares.py | Jugadores Similares (versión final pulida)
# =====================================

import streamlit as st
import pandas as pd
import numpy as np
from utils.data_loader import load_main_dataset
from utils.metrics import label, round_numeric_for_display
from utils.filters import sidebar_filters
from utils.pdf_export import build_report_pdf
from st_aggrid import AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode, GridUpdateMode, JsCode

# ======= CONFIGURACIÓN BASE =======
st.set_page_config(page_title="United Elite Scouting Hub — Similares", layout="wide")

# ======= ESTILO ANCHO COMPLETO =======
st.markdown("""
    <style>
    section.main > div {
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 100% !important;
    }
    div[data-testid="column"] { flex: 1 1 100% !important; }
    div.block-container { max-width: 100% !important; padding-left: 1rem !important; padding-right: 1rem !important; }
    div[data-testid="stVerticalBlock"] { gap: 0.7rem !important; }
    .stSelectbox, .stMultiSelect, .stRadio, .stSlider, .stCheckbox,
    .stNumberInput, .stTextInput { margin:.2rem 0 !important; }
    .kpi-row .stMetric { text-align:center; }
    </style>
""", unsafe_allow_html=True)

# ======= ENCABEZADO =======
st.markdown("""
<h2 style='font-weight:700; margin-bottom:0.25rem; letter-spacing:-0.01em;'>
Alternativas directas — Jugadores del mismo perfil
</h2>
<p style='color:#9aa2ad; font-size:0.9rem; margin-bottom:1.2rem;'>
Detecta futbolistas de características parecidas al objetivo para cubrir bajas, reforzar competencia interna o abrir opciones de mercado.
</p>
""", unsafe_allow_html=True)
st.caption(
    "Modelo ML utilizado: similitud coseno sobre indicadores normalizados (0–1) con pesos definidos por Dirección Deportiva."
)

# ======= CARGA DE DATOS =======
df = load_main_dataset()
if df is None or df.empty:
    st.error("No se pudo cargar el dataset principal.")
    st.stop()

df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
if "comp" not in df.columns and "league" in df.columns:
    df["comp"] = df["league"]

dff_view = sidebar_filters(df)
if dff_view.empty:
    st.warning("No hay jugadores que cumplan las condiciones de filtro.")
    st.stop()

# ======= KPIs UNIVERSO =======
st.markdown("---")

num_players = len(dff_view)
num_teams = dff_view["squad"].nunique() if "squad" in dff_view.columns else "—"
avg_age = pd.to_numeric(dff_view.get("age", pd.Series(dtype=float)), errors="coerce").mean()
avg_minutes = pd.to_numeric(dff_view.get("min", pd.Series(dtype=float)), errors="coerce").mean()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Número de Jugadores", f"{num_players:,}")
k2.metric("Equipos", f"{num_teams:,}")
k3.metric("Edad media", f"{avg_age:.1f}" if not np.isnan(avg_age) else "—")
k4.metric("Minutos medios", f"{avg_minutes:.0f}" if not np.isnan(avg_minutes) else "—")

# ======= SELECCIÓN DE JUGADOR =======
players_all = sorted(dff_view["player"].dropna().unique().tolist())
ref_player = st.selectbox(
    "Jugador referencia",
    options=players_all,
    index=0,
    placeholder="Empieza a escribir un nombre"
)

# ======= INDICADORES (manual) =======
metric_pool = [
    c for c in dff_view.columns
    if c.endswith("_per90") or c in ["age", "min", "starts", "mp", "90s", "pkatt", "gls", "ast", "g+a", "g-pk", "g+a-pk"]
]
metric_pool = sorted(set(metric_pool))
default_feats = [c for c in ["gls_per90", "ast_per90", "ga_per90", "pk_per90"] if c in metric_pool]
if len(default_feats) < 4:
    default_feats = metric_pool[:4]

feats = st.multiselect(
    "Selecciona los indicadores del perfil (4–6)",
    options=metric_pool,
    default=default_feats,
    max_selections=6,
    format_func=lambda c: label(c),
)
if len(feats) < 4:
    st.info("Para una comparación fiable, selecciona al menos 4 indicadores.")
    st.stop()

unique_suffix = f"manual_{hash(tuple(feats))}".replace("-", "_")

with st.expander("Ajusta la importancia de cada indicador (0.0–2.0)", expanded=True):
    weights = {
        f: st.slider(
            label(f),
            0.0, 2.0, 1.0, 0.1,
            key=f"sim_w_{f}_{unique_suffix}"
        )
        for f in feats
    }

st.markdown("---")

# ======= NORMALIZACIÓN =======
pool = dff_view.copy()
feats = [f for f in feats if f in pool.columns]
X_raw = pool[feats].astype(float).copy()
Xn = (X_raw - X_raw.min()) / (X_raw.max() - X_raw.min() + 1e-9)
Xn = Xn.fillna(0.0)

w = np.array([weights[f] for f in feats], dtype=float)
w = w / (w.sum() + 1e-9)

if any(pool["player"] == ref_player):
    v = Xn[pool["player"] == ref_player].mean(axis=0).to_numpy()
    pool_no_ref = pool[pool["player"] != ref_player].copy()
    X_no_ref = Xn.loc[pool_no_ref.index].copy()
else:
    st.warning("El jugador referencia no está dentro del grupo filtrado.")
    st.stop()

v_w = v * w
V_unit = v_w / (np.linalg.norm(v_w) + 1e-12)
U = X_no_ref.to_numpy() * w
norms = np.linalg.norm(U, axis=1)
valid_mask = norms > 1e-10
pool_no_ref = pool_no_ref.loc[valid_mask].copy()
if pool_no_ref.empty:
    st.warning("No hay jugadores comparables con los indicadores seleccionados. Prueba otro conjunto.")
    st.stop()
U = U[valid_mask]
norms = norms[valid_mask]
U_unit = U / (norms.reshape(-1, 1) + 1e-12)
sim = (U_unit @ V_unit)

# ======= RESULTADOS =======
st.subheader("Perfiles más parecidos")
col_left, col_right = st.columns([0.65, 0.35], gap="large")

strengths_txt: list[str] = []
needs_txt: list[str] = []
mask_ref = (pool["player"] == ref_player)
if mask_ref.any():
    S_ref = pool[feats].astype(float)
    ref_pct_all = S_ref.rank(pct=True)[mask_ref].mean().sort_values(ascending=False)
    strengths_txt = [f"{label(k)} ({v*100:.0f} pct)" for k, v in ref_pct_all.head(3).items()]
    needs_txt = [f"{label(k)} ({v*100:.0f} pct)" for k, v in ref_pct_all.tail(3).items()]

# ------- TABLA IZQUIERDA --------
with col_left:

    cols_id = [c for c in ["player", "squad", "rol_tactico", "min", "age"] if c in pool.columns]
    feats_preview = feats[:4]
    cols_show = cols_id + feats_preview + ["similitud"]

    out = pool_no_ref.copy()
    out["similitud"] = sim * 100.0
    out = out.sort_values("similitud", ascending=False).head(25)
    out = out[cols_show].copy()

    out.rename(columns={"player": "Jugador"}, inplace=True)
    disp = round_numeric_for_display(out, ndigits=2)

    gb = GridOptionsBuilder.from_dataframe(disp)
    gb.configure_default_column(sortable=True, filter=True, resizable=True, floatingFilter=True)
    gb.configure_column("Jugador", pinned="left", minWidth=230, tooltipField="Jugador")

    heat_js = JsCode("""
        function(params){
            var v = Number(params.value);
            if(isNaN(v)) return {};
            v = Math.max(0, Math.min(100.0, v));
            var hue = 120 * (v / 100.0);
            return {'backgroundColor':'hsl(' + hue + ',65%,25%)','color':'white'};
        }
    """)

    for col in feats_preview + ["similitud"]:
        if col in disp.columns:
            gb.configure_column(col, cellStyle=heat_js, minWidth=110)

    AgGrid(
        disp,
        gridOptions=gb.build(),
        theme="streamlit",
        update_mode=GridUpdateMode.NO_UPDATE,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
        height=500,
        allow_unsafe_jscode=True
    )

    st.download_button(
        "⬇️ Descargar comparables (CSV)",
        data=out.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"similares_{ref_player}.csv",
        mime="text/csv"
    )
    sim_pdf = build_report_pdf(
        title="Informe de perfiles similares",
        subtitle=f"Jugador referencia: {ref_player}",
        bullet_points=[
            f"Jugadores comparables listados: {len(out):,}",
            f"Indicadores evaluados: {len(feats)} (vista PDF: {len(feats_preview)})",
            "Metodo: similitud coseno ponderada",
            f"Fortalezas: {', '.join(strengths_txt) if strengths_txt else 'N/D'}",
            f"Aspectos a reforzar: {', '.join(needs_txt) if needs_txt else 'N/D'}",
        ],
        table_df=disp.head(10),
        table_title="Top perfiles similares",
        max_rows=10,
        max_cols=10,
    )
    st.download_button(
        "📄 Descargar comparables (PDF)",
        data=sim_pdf,
        file_name=f"similares_{ref_player}.pdf",
        mime="application/pdf",
    )

# ------- PERFIL DEL JUGADOR (DERECHA) --------
with col_right:
    st.markdown(f"### Informe rápido de {ref_player}")
    if mask_ref.any():
        S = pool[feats].astype(float)
        pcts = S.rank(pct=True)
        ref_pct = pcts[mask_ref].mean().sort_values(ascending=False)
        strengths = ref_pct.head(5)
        needs = ref_pct.tail(5)

        cA, cB = st.columns(2)

        with cA:
            st.markdown("**Fortalezas**")
            for k, v_ in strengths.items():
                st.write(f"• {label(k)} — {v_*100:.0f}º pct")

        with cB:
            st.markdown("**Aspectos a reforzar**")
            for k, v_ in needs.items():
                st.write(f"• {label(k)} — {v_*100:.0f}º pct")

    else:
        st.info("El jugador referencia no se encuentra en el grupo filtrado actual.")
