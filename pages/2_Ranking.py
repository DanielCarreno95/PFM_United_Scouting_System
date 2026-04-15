# =====================================
# pages/2_Ranking.py | Ranking FINAL (fix columnas duplicadas)
# =====================================

import streamlit as st
import pandas as pd
import numpy as np
from utils.data_loader import load_main_dataset
from utils.metrics import label, round_numeric_for_display
from utils.filters import render_global_filters
from utils.pdf_export import build_report_pdf

st.set_page_config(page_title="United Elite Scouting Hub — Ranking", layout="wide")


def _render_rank_table(df_table: pd.DataFrame, key: str) -> None:
    """Tabla robusta en cloud/local sin dependencia de componentes JS."""
    st.dataframe(df_table, use_container_width=True, hide_index=True, key=key)


# ==============================
# Cargar dataset
# ==============================
df = load_main_dataset()
if df is None or df.empty:
    st.error("No se encontró el dataset principal.")
    st.stop()

df.columns = [c.strip().replace(" ", "_").lower() for c in df.columns]
if "comp" not in df.columns and "league" in df.columns:
    league_src = df["league"]
    if isinstance(league_src, pd.DataFrame):
        league_src = league_src.iloc[:, 0]
    df["comp"] = league_src
elif "comp" not in df.columns:
    df["comp"] = "Desconocida"

# ==============================
# Filtros globales laterales
# ==============================
df_filtered = render_global_filters(df)
if df_filtered.empty:
    st.warning("⚠️ No hay datos tras aplicar los filtros.")
    st.stop()

# ==============================
# Encabezado del módulo Ranking
# ==============================
st.markdown("""
    <style>
    /* Expande el contenido principal (como en Comparador) */
    section.main > div {
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 100% !important;
    }

    /* Ajuste visual para títulos */
    h2 {
        font-weight: 700 !important;
        letter-spacing: -0.01em !important;
        margin-bottom: 0.25rem !important;
    }

    .ranking-caption {
        color: #9aa2ad;
        font-size: 0.9rem;
        margin-bottom: 1.5rem;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown(
    "<h2>Ranking deportivo — Prioridades reales de mercado</h2>",
    unsafe_allow_html=True,
)
st.markdown(
    "<div class='ranking-caption'>Ordena jugadores dentro del grupo filtrado. "
    "<strong>Valor de ranking</strong> = aporte en campo según el indicador elegido. "
    "<strong>Percentil (vs. filtro)</strong> = posición del jugador frente al resto del grupo (100 arriba, 0 abajo). "
    "Úsalo junto a vídeo y contexto táctico.</div>",
    unsafe_allow_html=True,
)

# ==============================
# KPIs
# ==============================
col1, col2, col3, col4 = st.columns(4)
col1.metric("Número de Jugadores", f"{len(df_filtered):,}")
col2.metric("Equipos", f"{df_filtered['squad'].nunique():,}")
col3.metric("Edad media", f"{pd.to_numeric(df_filtered['age'], errors='coerce').mean():.1f}")
col4.metric("Minutos medios", f"{int(pd.to_numeric(df_filtered.get('min', 0), errors='coerce').median()):,}")

st.markdown("---")

# ==============================
# Configuración superior
# ==============================
left, right = st.columns([0.55, 0.45])
with left:
    st.subheader("Enfoque del ranking")
    rank_mode = st.radio(
        "Cómo quieres ordenar a los jugadores",
        ["Ranking por indicador", "Ranking integral del perfil"],
        horizontal=True,
        label_visibility="collapsed",
        key="rank_mode_toggle"
    )
with right:
    st.caption("Ajustes de plantilla y minutos")
    quick_age = st.radio("Tramo de edad", ["Todos", "Sub-22", "Sub-28"], horizontal=True)

df_view = df_filtered.copy()
if "age" in df_view.columns and quick_age != "Todos":
    ages = pd.to_numeric(df_view["age"], errors="coerce")
    df_view = df_view[ages <= (22 if quick_age == "Sub-22" else 28)]

df_view["min"] = pd.to_numeric(df_view.get("min"), errors="coerce")
max_mins = int(df_view["min"].max()) if df_view["min"].notna().any() else 900
min_floor = st.slider(
    "Minutos mínimos en campo",
    min_value=90,
    max_value=max(180, max_mins),
    value=min(300, max_mins) if max_mins >= 90 else 90,
    step=30,
)
df_view = df_view[df_view["min"] >= min_floor]

if df_view.empty:
    st.warning("⚠️ No hay jugadores con esa combinación de filtros y minutos mínimos.")
    st.stop()

season_count = df_view["season"].astype(str).nunique() if "season" in df_view.columns else 0
if season_count == 1 and max_mins <= 600:
    st.warning(
        "Muestra parcial de temporada: el máximo de minutos es bajo. "
        "Para una lectura más sólida, combina temporadas o sube el mínimo de minutos."
    )

st.markdown("---")

# ==============================
# RANKING UNA MÉTRICA
# ==============================
if rank_mode == "Ranking por indicador":
    metrics = [c for c in df_view.columns if c.endswith("_per90") or c in ["cmp%", "save%"]]
    st.caption("Elige el dato principal que quieres priorizar")
    metric_to_rank = st.selectbox(
        "Indicador principal",
        metrics,
        index=0,
        format_func=lambda x: label(x),
        key="single_metric"
    )
    direction = st.radio("Cómo interpretar el indicador", ["Mayor valor = mejor", "Menor valor = mejor"], horizontal=True)
    higher_is_better = direction.startswith("Mayor")
    is_per90 = metric_to_rank.endswith("_per90")

    # --- cálculo del ranking ---
    df_rank = df_view.copy()
    df_rank[metric_to_rank] = pd.to_numeric(df_rank[metric_to_rank], errors="coerce")
    if is_per90:
        # Convierte ritmo por 90' en aporte acumulado real para evitar sesgos de muestra corta.
        df_rank["Valor de ranking"] = df_rank[metric_to_rank] * (df_rank["min"] / 90.0)
    else:
        df_rank["Valor de ranking"] = df_rank[metric_to_rank]

    # Percentil: pandas rank(pct=True) asigna ~0 al mejor valor cuando ascending=False.
    # Invertimos para que el líder del ranking tenga percentil alto (intuitivo en heatmap).
    if higher_is_better:
        pct = df_rank["Valor de ranking"].rank(pct=True, ascending=False, method="average")
        df_rank["Índice Final"] = (1.0 - pct) * 100.0
        df_rank = df_rank.sort_values("Valor de ranking", ascending=False)
    else:
        pct = df_rank["Valor de ranking"].rank(pct=True, ascending=True, method="average")
        df_rank["Índice Final"] = (1.0 - pct) * 100.0
        df_rank = df_rank.sort_values("Valor de ranking", ascending=True)

    # --- columnas visibles ---
    cols_show = ["player", "squad", "season", "rol_tactico", "comp", "min", "age", metric_to_rank, "Valor de ranking", "Índice Final"]
    df_disp = round_numeric_for_display(df_rank[cols_show], 3)

    ranking_label = "Aporte acumulado" if is_per90 else "Valor de ranking"
    df_disp.columns = [
        "Jugador", "Equipo", "Temporada", "Rol Táctico", "Competición", "Minutos", "Edad",
        f"{label(metric_to_rank)}", ranking_label, "Percentil (vs. filtro)"
    ]

    _render_rank_table(df_disp, "single_table")


# ==============================
# RANKING MULTI-MÉTRICA
# ==============================
else:
    metrics = [c for c in df_view.columns if c.endswith("_per90") or c in ["cmp%", "save%"]]
    st.caption("Selecciona entre 3 y 12 indicadores para la nota global de rendimiento")
    feats = st.multiselect(
        "Indicadores a ponderar",
        metrics,
        default=metrics[:5],
        format_func=lambda x: label(x),
        key="multi_feats"
    )

    if len(feats) < 3:
        st.info("Selecciona al menos 3 indicadores para continuar.")
        st.stop()

    st.markdown("Peso de cada indicador")
    weights = {f: st.slider(f"{label(f)}", 0.0, 2.0, 1.0, 0.1, key=f"w_{f}") for f in feats}

    X = df_view[feats].astype(float).fillna(0)
    Xn = (X - X.min()) / (X.max() - X.min() + 1e-9)
    w = np.array([weights[f] for f in feats])
    w /= (w.sum() + 1e-9)
    base_idx = (Xn @ w) * 100
    reliability = pd.to_numeric(df_view["min"], errors="coerce") / (pd.to_numeric(df_view["min"], errors="coerce") + 900)
    idx_norm = base_idx * reliability.fillna(0)

    df_rank = df_view[["player", "squad", "season", "rol_tactico", "comp", "min", "age"]].copy()
    df_rank["Índice compuesto"] = idx_norm

    # Añadir métricas ponderadas
    for m in feats:
        df_rank[f"{label(m)}"] = (df_view[m] * weights[m]).round(3)

    df_rank = df_rank.sort_values("Índice compuesto", ascending=False)

    cols_show = ["player", "squad", "season", "rol_tactico", "comp", "min", "age"] + [f"{label(m)}" for m in feats] + ["Índice compuesto"]
    df_disp = round_numeric_for_display(df_rank[cols_show], 3)
    df_disp.columns = ["Jugador", "Equipo", "Temporada", "Rol Táctico", "Competición", "Minutos", "Edad"] + [f"{label(m)}" for m in feats] + ["Índice compuesto (0–100)"]

    _render_rank_table(df_disp, "multi_table")

# ==============================
# BOTONES
# ==============================
st.markdown("---")
colb1, colb2, colb3 = st.columns([0.34, 0.33, 0.33])
with colb1:
    if st.button("Restablecer filtros", use_container_width=True):
        st.session_state.clear()
        st.rerun()
with colb2:
    st.download_button(
        "📥 Exportar CSV",
        data=df_view.to_csv(index=False).encode("utf-8-sig"),
        file_name="ranking_jugadores.csv",
        mime="text/csv",
        use_container_width=True
    )
with colb3:
    metric_col_name = f"{label(metric_to_rank)}" if rank_mode == "Ranking por indicador" else "Índice compuesto (0–100)"
    if rank_mode == "Ranking por indicador":
        rank_pdf_df = df_disp.copy()
        keep = [c for c in ["Jugador", "Equipo", "Minutos", "Edad", metric_col_name, ranking_label, "Percentil (vs. filtro)"] if c in rank_pdf_df.columns]
        rank_pdf_df = rank_pdf_df[keep]
    else:
        rank_pdf_df = df_disp.copy()
        keep = [c for c in ["Jugador", "Equipo", "Minutos", "Edad", "Índice compuesto (0–100)"] if c in rank_pdf_df.columns]
        rank_pdf_df = rank_pdf_df[keep]

    if st.button("Preparar informe PDF", use_container_width=True, key="rank_prepare_pdf"):
        with st.spinner("Generando informe de ranking..."):
            st.session_state["rank_pdf_bytes"] = build_report_pdf(
                title="Informe de ranking de mercado",
                subtitle="Priorizacion de jugadores del grupo filtrado",
                bullet_points=[
                    f"Registros evaluados: {len(df_view):,}",
                    f"Minutos minimos aplicados: {min_floor}",
                    f"Modo: {rank_mode}",
                    (
                        f"Indicador principal: {label(metric_to_rank)}"
                        if rank_mode == "Ranking por indicador"
                        else f"Indicadores ponderados: {', '.join([label(m) for m in feats])}"
                    ),
                ],
                table_df=rank_pdf_df,
                table_title="Tabla de ranking",
                max_rows=25,
                max_cols=7,
            )
            st.success("Informe preparado. Ya puedes descargarlo.")

    rank_pdf_bytes = st.session_state.get("rank_pdf_bytes")
    if rank_pdf_bytes:
        st.download_button(
            "📄 Descargar informe PDF",
            data=rank_pdf_bytes,
            file_name="ranking_jugadores.pdf",
            mime="application/pdf",
            use_container_width=True,
            key="rank_download_pdf",
        )
