# =======================================
# pages/1_Overview.py | Overview FINAL DEFINITIVO
# =======================================

import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_loader import load_main_dataset
from utils.metrics import METRIC_LABELS
from utils.filters import sidebar_filters   # ✅ AÑADE ESTA LÍNEA

st.set_page_config(page_title="United Elite Scouting Hub — Overview", layout="wide")

PALETTE = ["#DA291C", "#FBE122", "#C0C0C0", "#2B2A29", "#8B0000", "#FFFFFF"]

st.title("Mapa competitivo — Lectura ejecutiva de la Premier")
st.caption(
    "Foto global de la competición para Dirección Deportiva: carga de minutos, edad competitiva "
    "y perfiles de juego dominantes en el grupo filtrado."
)

# ==============================
# CARGA DE DATOS
# ==============================
df = load_main_dataset()
if df is None or df.empty:
    st.error("No se pudo cargar el dataset principal.")
    st.stop()

df.columns = [c.strip().replace(" ", "_").lower() for c in df.columns]

# ==============================
# FILTROS LATERALES (centralizados)
# ==============================
f = sidebar_filters(df)

def _weighted_by_minutes(data: pd.DataFrame, group_cols: list[str], metrics: list[str]) -> pd.DataFrame:
    """
    Promedio ponderado por minutos jugados.
    Evita que suplentes con pocos minutos distorsionen comparativas por equipo.
    """
    if not metrics:
        return pd.DataFrame()

    work = data.copy()
    work["min_num"] = pd.to_numeric(work.get("min"), errors="coerce")
    work = work[work["min_num"] > 0]
    if work.empty:
        return pd.DataFrame()

    rows = []
    for keys, g in work.groupby(group_cols):
        row = {}
        if isinstance(keys, tuple):
            for k, v in zip(group_cols, keys):
                row[k] = v
        else:
            row[group_cols[0]] = keys

        w = g["min_num"]
        for m in metrics:
            vals = pd.to_numeric(g[m], errors="coerce") if m in g.columns else pd.Series(dtype=float)
            mask = vals.notna() & w.notna() & (w > 0)
            row[m] = (vals[mask] * w[mask]).sum() / w[mask].sum() if mask.any() else pd.NA
        rows.append(row)

    return pd.DataFrame(rows)


# ==============================
# BLOQUE 1: CURVA DE MADUREZ COMPETITIVA
# ==============================
st.subheader("Edad y protagonismo por demarcación")
st.caption("Muestra en qué tramo de edad cada demarcación asume más minutos y peso competitivo.")

curve_df = (
    f.groupby(["rol_tactico", "age"], as_index=False)["min"]
    .mean()
    .dropna()
)

fig_curve = px.line(
    curve_df,
    x="age",
    y="min",
    color="rol_tactico",
    color_discrete_sequence=PALETTE,
    template="plotly_dark",
)
fig_curve.update_layout(
    height=400,
    xaxis_title="Edad",
    yaxis_title="Minutos promedio por jugador",
    legend_title="Rol táctico",
)
st.plotly_chart(fig_curve, use_container_width=True)

st.markdown(
    "_Lectura deportiva:_ los picos de cada curva señalan la edad de mayor protagonismo en partido."
)

st.markdown("---")

# ==============================
# BLOQUE 2: DISTRIBUCIÓN TÁCTICA POR COMPETICIÓN
# ==============================
st.subheader("Reparto de perfiles en la liga")
st.caption("Proporción de jugadores por demarcación para entender oferta real de mercado por perfil.")

dist_df = (
    f.groupby(["league", "rol_tactico"])
    .size()
    .reset_index(name="jugadores")
)
total_league = dist_df.groupby("league")["jugadores"].sum().reset_index(name="total")
dist_df = dist_df.merge(total_league, on="league")
dist_df["pct"] = dist_df["jugadores"] / dist_df["total"]

fig_dist = px.bar(
    dist_df,
    x="pct",
    y="league",
    color="rol_tactico",
    orientation="h",
    color_discrete_sequence=PALETTE,
    template="plotly_dark",
    text=dist_df["jugadores"],
)
fig_dist.update_layout(
    height=450,
    xaxis_title="Proporción de jugadores",
    yaxis_title="Competición",
    legend_title="Rol táctico",
)
st.plotly_chart(fig_dist, use_container_width=True)

st.markdown(
    "_Lectura deportiva:_ cuando el reparto es equilibrado, el mercado ofrece más alternativas por puesto."
)

st.markdown("---")

# ==============================
# BLOQUE 3: EXPLORADOR DE MÉTRICAS
# ==============================
st.subheader("Cruce de indicadores de rendimiento")
st.caption(
    "Cada punto representa un jugador. Cruza dos indicadores para detectar perfiles dominantes, "
    "equilibrados o de nicho."
)

metric_pool = [c for c in df.columns if c.endswith("_per90") or c in ["cmp%", "save%", "xg", "xa"]]
if not metric_pool:
    st.warning("No hay indicadores disponibles para mostrar en este dataset.")
    st.stop()

colx, coly = st.columns(2)
with colx:
    x_metric = st.selectbox(
        "Eje X",
        metric_pool,
        index=metric_pool.index("gls_per90") if "gls_per90" in metric_pool else 0,
        format_func=lambda x: METRIC_LABELS.get(x, x)
    )
with coly:
    y_default_idx = metric_pool.index("xg_per90") if "xg_per90" in metric_pool else (1 if len(metric_pool) > 1 else 0)
    y_metric = st.selectbox(
        "Eje Y",
        metric_pool,
        index=y_default_idx,
        format_func=lambda x: METRIC_LABELS.get(x, x)
    )

min_cut = st.slider("Minutos mínimos para entrar en el análisis", min_value=90, max_value=2000, value=450, step=30)

scatter_df = f.copy()
scatter_df["min"] = pd.to_numeric(scatter_df["min"], errors="coerce")
scatter_df[x_metric] = pd.to_numeric(scatter_df[x_metric], errors="coerce")
scatter_df[y_metric] = pd.to_numeric(scatter_df[y_metric], errors="coerce")
scatter_df = scatter_df[
    (scatter_df["min"] >= min_cut) &
    scatter_df[x_metric].notna() &
    scatter_df[y_metric].notna()
]

if scatter_df.empty:
    st.warning("No hay jugadores con ese mínimo de minutos para este cruce.")
    st.stop()

# Rango real completo para mantener coherencia con ranking y realidad observada.
x_cap = float(scatter_df[x_metric].max())
y_cap = float(scatter_df[y_metric].max())

fig_scatter = px.scatter(
    scatter_df,
    x=x_metric,
    y=y_metric,
    color="rol_tactico",
    size="min",
    hover_name="player",
    color_discrete_sequence=PALETTE,
    template="plotly_dark",
)
fig_scatter.update_layout(
    height=620,
    xaxis_title=METRIC_LABELS.get(x_metric, x_metric),
    yaxis_title=METRIC_LABELS.get(y_metric, y_metric),
    legend_title="Puesto de juego",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
)
fig_scatter.update_xaxes(range=[0, max(x_cap * 1.05, 0.1)])
fig_scatter.update_yaxes(range=[0, max(y_cap * 1.05, 0.1)])
st.plotly_chart(fig_scatter, use_container_width=True)

st.markdown(
    f"_Lectura rápida:_ el gráfico usa jugadores con al menos **{min_cut} minutos** para evitar ruido por poca muestra y muestra el rango completo de valores. "
    f"Eje X: **{METRIC_LABELS.get(x_metric, x_metric)}** · Eje Y: **{METRIC_LABELS.get(y_metric, y_metric)}**."
)

st.markdown("---")

# ==============================
# BLOQUE 4: PERFIL MEDIO POR EQUIPO
# ==============================
st.subheader("Cómo compite cada equipo (perfil medio)")
st.caption(
    "Compara el estilo promedio de cada equipo con ponderación por minutos, "
    "dando más peso a quienes realmente sostienen el juego."
)

# --- Defaults
DEFAULT_METRICS_TEAM = ["xg_per90"] if "xg_per90" in metric_pool else [metric_pool[0]]
DEFAULT_TOPN_TEAM = 10

# --- Estado inicial seguro ---
if "metrics_team" not in st.session_state:
    st.session_state["metrics_team"] = DEFAULT_METRICS_TEAM.copy()
if "top_n_team" not in st.session_state:
    st.session_state["top_n_team"] = DEFAULT_TOPN_TEAM

# --- Función de reseteo ---
def _reset_team_filters():
    st.session_state["metrics_team"] = DEFAULT_METRICS_TEAM.copy()
    st.session_state["top_n_team"] = DEFAULT_TOPN_TEAM

# --- Botón reset ---
st.button("Restablecer filtros de equipos", on_click=_reset_team_filters)

# --- Selector de métricas ---
metrics_team = st.multiselect(
    "Selecciona indicadores (máximo 3)",
    metric_pool,
    key="metrics_team",
    max_selections=3,
    format_func=lambda x: METRIC_LABELS.get(x, x),
)

# --- Slider sin conflicto de SessionState ---
top_n_teams = st.slider(
    "Número de equipos a mostrar",
    min_value=5,
    max_value=30,
    key="top_n_team",  # no pasamos 'value' → evita el warning
)

# --- Garantía de valores por defecto ---
if not metrics_team:
    metrics_team = DEFAULT_METRICS_TEAM.copy()
    st.session_state["metrics_team"] = metrics_team

# --- Cálculo de ranking (mayor a menor) ---
team_avg = _weighted_by_minutes(f, ["squad"], metrics_team).dropna()

if team_avg.empty:
    st.warning("No hay información suficiente para ordenar equipos con fiabilidad.")
    st.stop()

# Promedio conjunto de métricas seleccionadas
team_avg["__orden__"] = team_avg[metrics_team].mean(axis=1)
team_avg = team_avg.sort_values("__orden__", ascending=False)

# Top N equipos
top_squads_ordered = team_avg["squad"].head(top_n_teams).tolist()

# Pasar a formato largo (long)
long_team = (
    team_avg.melt(id_vars=["squad", "__orden__"], var_name="métrica", value_name="valor")
    .query("squad in @top_squads_ordered")
)
long_team["squad"] = pd.Categorical(long_team["squad"], categories=top_squads_ordered, ordered=True)

# --- Visualización ---
fig_team = px.bar(
    long_team,
    x="valor",
    y="squad",
    color="métrica",
    barmode="group",
    color_discrete_sequence=PALETTE,
    template="plotly_dark",
)
fig_team.update_layout(
    height=460,
    xaxis_title="Valor promedio",
    yaxis_title="Equipo",
    legend_title="Métrica",
)
fig_team.update_yaxes(autorange="reversed")  # Mejor equipo arriba

st.plotly_chart(fig_team, use_container_width=True)

st.markdown(
    "_Lectura deportiva:_ el orden refleja el rendimiento colectivo medio en los indicadores elegidos."
)
st.markdown("---")

# ==============================
# BLOQUE 5: EVOLUCIÓN TÁCTICA POR EQUIPO
# ==============================
st.subheader("Evolución del rendimiento por equipo")
st.caption(
    "Sigue cómo cambia el rendimiento de cada equipo entre temporadas con el mismo criterio de minutos."
)

# --- Defaults ---
DEFAULT_METRICS_EVOL = ["xg_per90"] if "xg_per90" in metric_pool else [metric_pool[0]]
DEFAULT_TOPN_EVOL = 3  # empieza en 3 como pediste

# --- Inicializar estado si no existe ---
if "metrics_evol" not in st.session_state:
    st.session_state["metrics_evol"] = DEFAULT_METRICS_EVOL.copy()
if "top_n_evol" not in st.session_state:
    st.session_state["top_n_evol"] = DEFAULT_TOPN_EVOL

# --- Función de reseteo ---
def _reset_evol_filters():
    st.session_state["metrics_evol"] = DEFAULT_METRICS_EVOL.copy()
    st.session_state["top_n_evol"] = DEFAULT_TOPN_EVOL

# --- Botón reset ---
st.button("Restablecer filtros de evolución", on_click=_reset_evol_filters)

# --- Multiselect controlado SIN default ---
metrics_selected = st.multiselect(
    "Selecciona indicadores (máximo 4)",
    metric_pool,
    key="metrics_evol",
    max_selections=4,
    format_func=lambda x: METRIC_LABELS.get(x, x),
)

# --- Slider controlado SIN value ---
top_n_evol = st.slider(
    "Número de equipos a mostrar",
    min_value=3,
    max_value=10,
    key="top_n_evol",
)

# --- Garantizar al menos 1 métrica ---
if not metrics_selected:
    metrics_selected = DEFAULT_METRICS_EVOL.copy()
    st.session_state["metrics_evol"] = metrics_selected

# --- Serie temporal por equipo ---
if "season" in f.columns and metrics_selected:
    # Calcular score promedio para top N equipos (ponderado por minutos)
    score_by_team_df = _weighted_by_minutes(f, ["squad"], metrics_selected).dropna()
    if score_by_team_df.empty:
        st.warning("No hay datos suficientes para calcular la evolución por equipos.")
        st.stop()

    score_by_team = score_by_team_df.set_index("squad")[metrics_selected].mean(axis=1)
    top_teams = score_by_team.sort_values(ascending=False).head(st.session_state["top_n_evol"]).index.tolist()

    evol_weighted = _weighted_by_minutes(
        f[f["squad"].isin(top_teams)],
        ["season", "squad"],
        metrics_selected
    ).dropna()
    long_evol = evol_weighted.melt(id_vars=["season", "squad"], var_name="métrica", value_name="valor").dropna()

    long_evol["squad"] = pd.Categorical(long_evol["squad"], categories=top_teams, ordered=True)

    # --- Gráfico de barras verticales ---
import plotly.express as px

fig_evol = px.bar(
    long_evol,
    x="season",
    y="valor",
    color="squad",
    facet_col="métrica",
    facet_col_wrap=2,
    barmode="group",  # Barras agrupadas (no apiladas)
    color_discrete_sequence=PALETTE,
    template="plotly_dark",
)

# --- Ajustes estéticos ---
fig_evol.update_layout(
    height=520 + 80 * max(0, len(metrics_selected) - 2),
    xaxis_title="Temporada",
    yaxis_title="Valor medio",
    legend_title="Equipo",
    bargap=0.25,  # separación entre barras
    bargroupgap=0.15,  # separación entre grupos
)

# Mejorar legibilidad de etiquetas
fig_evol.update_xaxes(type="category", tickangle=-30)

st.plotly_chart(fig_evol, use_container_width=True)

# ==============================
# 📄 Exportar infografía (1 página grande, Hero + 2×2)
# ==============================
import io
import os
from datetime import datetime
import tempfile
import matplotlib.pyplot as plt
from fpdf import FPDF
try:
    from PIL import Image
except Exception:  # pragma: no cover
    Image = None

# ---- Tamaño de página optimizado (1 lámina horizontal) ----
# Se reduce tamaño para acelerar generación sin perder legibilidad.
PAGE_W, PAGE_H = 1300, 960


def _safe_pdf_text(value: object) -> str:
    """Convierte texto a latin-1 seguro para fuentes base de FPDF."""
    return str(value).encode("latin-1", "replace").decode("latin-1")

def _mpl_to_png_bytes(fig: plt.Figure, dpi: int = 130) -> bytes:
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=dpi, facecolor="#0B0F17")
    plt.close(fig)
    return buf.getvalue()


def _pdf_img_scatter() -> bytes:
    fig, ax = plt.subplots(figsize=(8.7, 4.8))
    fig.patch.set_facecolor("#0B0F17")
    ax.set_facecolor("#0B0F17")
    roles = sorted(scatter_df["rol_tactico"].dropna().unique().tolist())
    for i, role in enumerate(roles):
        d = scatter_df[scatter_df["rol_tactico"] == role]
        ax.scatter(
            d[x_metric],
            d[y_metric],
            s=((d["min"] / max(float(d["min"].max()), 1.0)) * 65).clip(lower=8),
            alpha=0.7,
            color=PALETTE[i % len(PALETTE)],
            label=role,
        )
    ax.set_xlabel(METRIC_LABELS.get(x_metric, x_metric), color="white")
    ax.set_ylabel(METRIC_LABELS.get(y_metric, y_metric), color="white")
    ax.tick_params(colors="white", labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#374151")
    lg = ax.legend(frameon=False, fontsize=7, ncol=3, loc="upper left")
    for t in lg.get_texts():
        t.set_color("white")
    ax.grid(color="#1f2937", alpha=0.35)
    return _mpl_to_png_bytes(fig)


def _pdf_img_curve() -> bytes:
    fig, ax = plt.subplots(figsize=(4.7, 3.2))
    fig.patch.set_facecolor("#0B0F17")
    ax.set_facecolor("#0B0F17")
    for i, role in enumerate(sorted(curve_df["rol_tactico"].dropna().unique())):
        d = curve_df[curve_df["rol_tactico"] == role].sort_values("age")
        ax.plot(d["age"], d["min"], label=role, color=PALETTE[i % len(PALETTE)], linewidth=1.8)
    ax.set_title("Edad y protagonismo", color="white", fontsize=10)
    ax.tick_params(colors="white", labelsize=8)
    ax.grid(color="#1f2937", alpha=0.35)
    for spine in ax.spines.values():
        spine.set_color("#374151")
    return _mpl_to_png_bytes(fig)


def _pdf_img_distribution() -> bytes:
    fig, ax = plt.subplots(figsize=(4.7, 3.2))
    fig.patch.set_facecolor("#0B0F17")
    ax.set_facecolor("#0B0F17")
    pivot = dist_df.pivot_table(index="league", columns="rol_tactico", values="pct", aggfunc="sum").fillna(0)
    left = None
    for i, col in enumerate(pivot.columns):
        vals = pivot[col].values
        ax.barh(
            pivot.index.astype(str),
            vals,
            left=left,
            color=PALETTE[i % len(PALETTE)],
            label=str(col),
            alpha=0.95,
        )
        left = vals if left is None else left + vals
    ax.set_xlim(0, 1.0)
    ax.set_title("Reparto de perfiles", color="white", fontsize=10)
    ax.tick_params(colors="white", labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#374151")
    return _mpl_to_png_bytes(fig)


def _pdf_img_team_profile() -> bytes:
    fig, ax = plt.subplots(figsize=(4.7, 3.2))
    fig.patch.set_facecolor("#0B0F17")
    ax.set_facecolor("#0B0F17")
    pivot = long_team.pivot_table(index="squad", columns="métrica", values="valor", aggfunc="mean").fillna(0)
    pivot = pivot.head(10)
    if not pivot.empty:
        x = range(len(pivot.index))
        n = max(1, len(pivot.columns))
        width = 0.75 / n
        for j, col in enumerate(pivot.columns):
            ax.bar(
                [i + j * width for i in x],
                pivot[col].values,
                width=width,
                color=PALETTE[j % len(PALETTE)],
                label=str(col),
            )
        ax.set_xticks([i + (n - 1) * width / 2 for i in x])
        ax.set_xticklabels([str(v)[:12] for v in pivot.index], rotation=35, ha="right", color="white", fontsize=7)
    ax.set_title("Perfil medio por equipo", color="white", fontsize=10)
    ax.tick_params(colors="white", labelsize=8)
    ax.grid(color="#1f2937", alpha=0.3, axis="y")
    for spine in ax.spines.values():
        spine.set_color("#374151")
    return _mpl_to_png_bytes(fig)


def _pdf_img_evolution() -> bytes:
    fig, ax = plt.subplots(figsize=(4.7, 3.2))
    fig.patch.set_facecolor("#0B0F17")
    ax.set_facecolor("#0B0F17")
    if "long_evol" in globals() and isinstance(long_evol, pd.DataFrame) and not long_evol.empty:
        d = long_evol.copy()
        d["season"] = d["season"].astype(str)
        for i, team in enumerate(sorted(d["squad"].astype(str).unique())):
            ts = d[d["squad"].astype(str) == team].groupby("season", as_index=False)["valor"].mean()
            ax.plot(ts["season"], ts["valor"], marker="o", linewidth=1.8, color=PALETTE[i % len(PALETTE)], label=team)
        lg = ax.legend(frameon=False, fontsize=7, ncol=2, loc="best")
        for t in lg.get_texts():
            t.set_color("white")
    else:
        ax.text(0.5, 0.5, "Sin datos de evolucion", ha="center", va="center", color="white")
        ax.set_xticks([])
        ax.set_yticks([])
    ax.set_title("Evolucion por equipo", color="white", fontsize=10)
    ax.tick_params(colors="white", labelsize=8)
    ax.grid(color="#1f2937", alpha=0.3)
    for spine in ax.spines.values():
        spine.set_color("#374151")
    return _mpl_to_png_bytes(fig)

def build_infographic_pdf_5(
    hero, tl, tr, bl, br,
    title="Scouting Hub — Data Performance Summary",
    subtitle="Análisis integral de rendimiento y evolución táctica",
):
    """Crea un PDF 1 página (hero + rejilla 2x2) con FPDF."""
    # Márgenes y rejilla
    M, HDR, GUT = 26, 72, 16
    W, H = PAGE_W, PAGE_H
    content_w = W - 2 * M
    content_h = H - HDR - M
    hero_h = content_h * 0.47
    grid_h = content_h - hero_h - GUT
    cell_w = (content_w - GUT) / 2
    cell_h = (grid_h - GUT) / 2

    pdf = FPDF(unit="pt", format=(W, H))
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()

    # Fondo
    pdf.set_fill_color(11, 15, 23)
    pdf.rect(0, 0, W, H, style="F")

    # Cabecera
    pdf.set_text_color(243, 244, 246)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_xy(M, 24)
    pdf.cell(w=W - 2 * M, h=34, txt=_safe_pdf_text(title))

    pdf.set_text_color(154, 162, 173)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_xy(M, 48)
    pdf.cell(w=W - 2 * M, h=14, txt=_safe_pdf_text(subtitle))

    pdf.set_xy(W - M - 120, 24)
    pdf.cell(w=120, h=12, txt=_safe_pdf_text(datetime.now().strftime("%d/%m/%Y")), align="R")

    # Posiciones (coordenadas top-left)
    x_hero, y_hero = M, HDR
    x_tl, y_tl = M, y_hero + hero_h + GUT
    x_tr, y_tr = M + cell_w + GUT, y_tl
    x_bl, y_bl = M, y_tl + cell_h + GUT
    x_br, y_br = x_tr, y_bl

    temp_paths: list[str] = []

    def _add_png(img_bytes: bytes | None, x: float, y: float, w: float, h: float) -> None:
        if not img_bytes:
            return
        tf = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        tf.write(img_bytes)
        tf.flush()
        tf.close()
        temp_paths.append(tf.name)
        # Encaja la imagen respetando relación de aspecto (evita estiramientos).
        if Image is not None:
            try:
                with Image.open(tf.name) as im:
                    iw, ih = im.size
                if iw > 0 and ih > 0:
                    scale = min(w / iw, h / ih)
                    draw_w = iw * scale
                    draw_h = ih * scale
                    dx = x + (w - draw_w) / 2
                    dy = y + (h - draw_h) / 2
                    pdf.image(tf.name, x=dx, y=dy, w=draw_w, h=draw_h)
                    return
            except Exception:
                pass
        pdf.image(tf.name, x=x, y=y, w=w, h=h)

    try:
        _add_png(hero, x_hero, y_hero, content_w, hero_h)
        _add_png(tl, x_tl, y_tl, cell_w, cell_h)
        _add_png(tr, x_tr, y_tr, cell_w, cell_h)
        _add_png(bl, x_bl, y_bl, cell_w, cell_h)
        _add_png(br, x_br, y_br, cell_w, cell_h)
        raw = pdf.output(dest="S")
        if isinstance(raw, (bytes, bytearray)):
            return bytes(raw)
        return raw.encode("latin-1")
    finally:
        for p in temp_paths:
            try:
                os.unlink(p)
            except Exception:
                pass

# ---- Generación + descarga (5 figuras en 1 lámina) ----
# Asegúrate de tener: fig_scatter, fig_curve, fig_dist, fig_team, fig_evol
if st.button("📄 Preparar informe PDF (1 lámina)"):
    try:
        with st.spinner("Generando informe... (normalmente 10-20 segundos)"):
            # Calculamos tamaños exactos de la rejilla
            M, HDR, GUT = 26, 72, 16
            W, H = PAGE_W, PAGE_H
            content_w = W - 2 * M
            content_h = H - HDR - M
            hero_h = content_h * 0.44
            grid_h = content_h - hero_h - GUT
            cell_w = (content_w - GUT) / 2
            cell_h = (grid_h - GUT) / 2

            # Exportación optimizada para no bloquear la app
            imgs = {
                "hero": _pdf_img_scatter(),
                "tl": _pdf_img_curve(),
                "tr": _pdf_img_distribution(),
                "bl": _pdf_img_team_profile(),
                "br": _pdf_img_evolution(),
            }

            st.session_state["overview_pdf_bytes"] = build_infographic_pdf_5(
                hero=imgs["hero"],
                tl=imgs["tl"], tr=imgs["tr"],
                bl=imgs["bl"], br=imgs["br"],
                title="UNITED ELITE SCOUTING HUB — Informe para Direccion Deportiva",
                subtitle="Premier League · Seguimiento de rendimiento y mercado",
            )
        st.success("Informe preparado correctamente. Ya puedes descargarlo.")
    except Exception as e:
        st.error(
            f"❌ No se pudo generar el PDF: {e}\n"
            f"Sugerencia: confirma que 'fpdf2' y 'matplotlib' están instalados."
        )

if st.session_state.get("overview_pdf_bytes"):
    st.download_button(
        "⬇️ Descargar informe visual (PDF)",
        data=st.session_state["overview_pdf_bytes"],
        file_name=f"Informe_Direccion_Deportiva_{datetime.now().strftime('%Y%m%d')}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )
