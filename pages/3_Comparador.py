import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io
import matplotlib.pyplot as plt
from utils.data_loader import load_main_dataset
from utils.metrics import label
from utils.filters import sidebar_filters
from utils.pdf_export import build_report_pdf

# ======= EXPANDIR A ANCHO COMPLETO (como Ranking) =======
st.markdown("""
    <style>
    /* Quita los márgenes laterales del contenido principal */
    section.main > div {
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 100% !important;
    }

    /* Asegura que las columnas se expandan en todo el ancho */
    div[data-testid="column"] {
        width: 100% !important;
        flex: 1 1 100% !important;
    }

    /* Evita centrado forzado del contenedor principal */
    div.block-container {
        max-width: 100% !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }

    /* Reduce los márgenes entre widgets */
    div[data-testid="stVerticalBlock"] {
        gap: 0.7rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# ===================== COMPARADOR (Radar) ===========================

df = load_main_dataset()
dff_view = sidebar_filters(df)

if len(dff_view) == 0:
    st.warning("No hay jugadores que cumplan las condiciones de filtro.")
    st.stop()

st.markdown("""
<h2 style='font-weight:700; margin-bottom:0.25rem; letter-spacing:-0.01em;'>
Duelo de perfiles — Comparativa directa para decisión deportiva
</h2>
<p style='color:#9aa2ad; font-size:0.9rem; margin-bottom:1.2rem;'>
Compara hasta tres jugadores en un mismo radar para decidir altas, continuidad o competencia interna por puesto.
</p>
""", unsafe_allow_html=True)

st.markdown("""
<style>
.cmp .block-container, .cmp [data-testid="stVerticalBlock"]{gap:.35rem !important}
.cmp .stRadio, .cmp .stMultiSelect, .cmp .stSelectbox, .cmp .stSlider,
.cmp .stToggleSwitch{margin: .1rem 0 .35rem 0 !important}
.cmp label{margin-bottom:.15rem !important}
.cmp .metric-note{color:#9aa2ad; font-size:.85rem; margin:.2rem 0 .6rem 0}
.cmp .stMetric{padding-top:.2rem}
</style>
""", unsafe_allow_html=True)

c = st.container()
c.markdown('<div class="cmp">', unsafe_allow_html=True)

kpi_top = c.container()
c.caption(
    '<div class="metric-note">Nota global (0–100): promedio de los indicadores elegidos. '
    'El Δ muestra cuánto rinde cada jugador por encima o por debajo del jugador referencia.</div>',
    unsafe_allow_html=True
)

# ===================== DETECTAR COLUMNA DE JUGADOR =====================
player_col = None
for col in dff_view.columns:
    if col.lower() in ["player", "jugador", "nombre", "name"]:
        player_col = col
        break

if not player_col:
    st.error("❌ No se encuentra la columna de nombres de jugadores en el dataset.")
    st.stop()

# ===================== PRESETS =====================
ROLE_PRESETS = {
    "Portero":     ["ga_per90", "pk_per90", "crdy_per90", "crdr_per90", "ast_per90"],
    "Central":     ["ga_per90", "ast_per90", "crdy_per90", "crdr_per90", "pk_per90", "gpk_per90"],
    "Lateral":     ["ast_per90", "ga_per90", "pk_per90", "crdy_per90", "crdr_per90", "gapk_per90"],
    "Mediocentro": ["ast_per90", "ga_per90", "pk_per90", "crdy_per90", "crdr_per90", "gapk_per90"],
    "Volante":     ["gls_per90", "ast_per90", "ga_per90", "gpk_per90", "gapk_per90", "pk_per90"],
    "Delantero":   ["gls_per90", "ast_per90", "ga_per90", "gpk_per90", "gapk_per90", "pk_per90"],
}

# ===================== SELECCIÓN DE JUGADORES =====================
players_all = dff_view[player_col].dropna().unique().tolist()
pre_sel = st.session_state.get("cmp_players", [])
default_players = [p for p in pre_sel if p in players_all][:3] or players_all[:2]

sel_players = c.multiselect("Jugadores a comparar (máx. 3)", players_all, default=default_players, key="cmp_players")
if not sel_players:
    st.info("Selecciona al menos un jugador.")
    st.stop()
if len(sel_players) > 3:
    sel_players = sel_players[:3]

ref_player = c.selectbox("Jugador de referencia", sel_players, index=0, key="cmp_ref")

# === NUEVO: para forzar actualización del multiselect ===
if "feats_key" not in st.session_state:
    st.session_state["feats_key"] = 0

col_r1, col_r2 = c.columns([0.72, 0.28])
with col_r1:
    cmp_role = st.selectbox(
        "Puesto de juego (carga rápida de indicadores)",
        ["— (ninguno)"] + list(ROLE_PRESETS.keys()),
        index=0,
        key="cmp_role"
    )

with col_r2:
    if cmp_role != "— (ninguno)":
        if st.button("Aplicar preset", use_container_width=True, key="cmp_role_btn"):
            # Normalizar columnas y presets a minúsculas
            cols_lower = {c.lower(): c for c in dff_view.columns}
            preset_raw = [m.lower() for m in ROLE_PRESETS[cmp_role]]
            preset_feats = [cols_lower[m] for m in preset_raw if m in cols_lower]

            if preset_feats:
                st.session_state["feats"] = preset_feats
                st.session_state["feats_key"] += 1
                st.success(f"Perfil cargado: {cmp_role} → {len(preset_feats)} indicadores.")
                try:
                    st.rerun()
                except AttributeError:
                    st.experimental_rerun()
            else:
                st.warning(f"No se encontraron indicadores válidos para el rol '{cmp_role}'.")

# ===================== MULTISELECT DE MÉTRICAS =====================
valid_feats = [
    c for c in dff_view.columns
    if c.endswith("_per90")
    or c.endswith("%")
    or "rate" in c.lower()
    or "ratio" in c.lower()
]

default_feats = st.session_state.get("feats", valid_feats[:6])

radar_feats = c.multiselect(
    "Indicadores para el radar (elige 4–10)",
    options=valid_feats,
    default=[f for f in default_feats if f in valid_feats],
    key=f"feats_{st.session_state['feats_key']}",
    format_func=lambda c: label(c),
)
if len(radar_feats) < 4:
    st.info("Selecciona al menos 4 indicadores para construir el radar.")
    st.stop()

# ===================== CONTROLES DE CONTEXTO =====================
col_ctx1, col_ctx2, col_ctx3 = c.columns([1, 1, 1.2])
ctx_mode = col_ctx1.selectbox(
    "Comparar contra",
    options=["Grupo filtrado", "Solo mismo puesto", "Solo misma competición"],
    index=0,
    key="cmp_ctx",
)
show_baseline = col_ctx2.toggle("Mostrar media del grupo", value=True, key="cmp_baseline")
use_percentiles = col_ctx3.toggle("Ver percentiles en tooltip", value=True, key="cmp_pct_tooltip")

# ===================== FUNCIÓN DE CONTEXTO =====================
def _ctx_mask(df_in: pd.DataFrame) -> pd.Series:
    """Filtra el DataFrame según el modo de contexto seleccionado."""
    if ctx_mode == "Grupo filtrado":
        return pd.Series(True, index=df_in.index)
    if ctx_mode == "Solo mismo puesto" and "rol_tactico" in df_in.columns:
        if any(dff_view[player_col] == ref_player):
            rol_ref = dff_view.loc[dff_view[player_col] == ref_player, "rol_tactico"].iloc[0]
            return (df_in["rol_tactico"] == rol_ref)
    if ctx_mode == "Solo misma competición" and "comp" in df_in.columns:
        if any(dff_view[player_col] == ref_player):
            comp_ref = dff_view.loc[dff_view[player_col] == ref_player, "comp"].iloc[0]
            return (df_in["comp"] == comp_ref)
    return pd.Series(True, index=df_in.index)

# ✅ Crear el grupo de datos según el contexto antes de la normalización
df_group = dff_view[_ctx_mask(dff_view)].copy()
if df_group.empty:
    df_group = dff_view.copy()


# ===================== NORMALIZACIÓN =====================
S_global = df[radar_feats].astype(float)
S = df_group[radar_feats].astype(float).copy()

# FIX anti-errores de alineación usando NumPy (escalares 100% seguros)
mins = S_global.min(axis=0)
maxs = S_global.max(axis=0)
ranges = (maxs - mins + 1e-9)

S_norm = (S - mins.values) / ranges.values * 100
S_norm = S_norm.clip(lower=0, upper=100)

baseline = S_norm.mean(axis=0)
pct = df_group[radar_feats].rank(pct=True) * 100 if use_percentiles else None

# ===================== KPI ARRIBA =====================
with kpi_top:
    cols_kpi = st.columns(len(sel_players))
    # ❌ antes: * 100 (duplicado)
    ref_val = S_norm[df_group[player_col] == ref_player][radar_feats].mean(axis=1).mean()
    for i, pl in enumerate(sel_players):
        val = S_norm[df_group[player_col] == pl][radar_feats].mean(axis=1).mean()
        delta = None if pl == ref_player else round(val - float(ref_val), 1)
        cols_kpi[i].metric(
            pl + (" (ref.)" if pl == ref_player else ""),
            f"{val:,.1f}",
            delta=None if delta is None else (f"{delta:+.1f}")
        )


# ===================== RADAR (MEJORADO TIPO FBREF) =====================
theta_labels = [label(f) for f in radar_feats]
fig = go.Figure()
palette = ["#DA291C", "#FBE122", "#C0C0C0"]

# 🔹 Percentiles globales (0–100)
S_perc = df[radar_feats].rank(pct=True) * 100
S_group_perc = S_perc.loc[df_group.index].copy()
player_means = (
    S_group_perc.assign(player=df_group[player_col])
    .groupby("player")[radar_feats]
    .mean()
)
baseline = player_means.mean(axis=0)

# === Añadir trazas ===
for i, pl in enumerate(sel_players):
    if pl not in player_means.index:
        continue
    r_vec = player_means.loc[pl, radar_feats].fillna(0).values
    fig.add_trace(go.Scatterpolar(
        r=r_vec,
        theta=theta_labels,
        fill='toself',
        mode='lines+markers',
        name=pl + (" (ref.)" if pl == ref_player else ""),
        line=dict(color=palette[i % len(palette)], width=2),
        marker=dict(size=5, color=palette[i % len(palette)], line=dict(width=1, color='white')),
        opacity=0.85 if pl == ref_player else 0.7,
        hovertemplate="<b>%{theta}</b><br>Percentil: %{r:.1f}<extra></extra>",
    ))


fig.update_layout(
    template="plotly_dark",
    polar=dict(
        radialaxis=dict(
            visible=True,
            range=[0, 100],
            gridcolor="#374151",
            linecolor="#4b5563"
        )
    ),
    legend=dict(orientation="h", yanchor="bottom", y=-0.2, x=0),
    margin=dict(l=30, r=30, t=10, b=10),
)
c.plotly_chart(fig, use_container_width=True)

# ===================== TABLA =====================
raw_group = dff_view[_ctx_mask(dff_view)].copy()
rows = {}
for pl in sel_players:
    rows[pl] = raw_group[raw_group[player_col] == pl][radar_feats].astype(float).mean()

df_cmp = pd.DataFrame({"Métrica": [label(f) for f in radar_feats]})
for pl, vals in rows.items():
    df_cmp[pl] = vals.values
for pl in sel_players:
    if pl == ref_player:
        continue
    df_cmp[f"Δ ({pl} − {ref_player})"] = df_cmp[pl] - df_cmp[ref_player]

# ======= FIX DEFINITIVO DEL ERROR DE PERCENTILES =======
if use_percentiles:
    pct_raw = raw_group[radar_feats].rank(pct=True)

    for pl in sel_players:
        pr = pct_raw[raw_group[player_col] == pl][radar_feats].mean(numeric_only=True) * 100

        # Construimos lista alineada EXACTAMENTE al orden de radar_feats
        perc_list = [pr.get(feat, float("nan")) for feat in radar_feats]

        df_cmp[f"% {pl}"] = perc_list
# ========================================================

for ccol in df_cmp.columns:
    if ccol != "Métrica":
        df_cmp[ccol] = pd.to_numeric(df_cmp[ccol], errors="coerce").round(3)

first_delta = [c for c in df_cmp.columns if c.startswith("Δ (")]
if first_delta:
    df_cmp = df_cmp.reindex(df_cmp[first_delta[0]].abs().sort_values(ascending=False).index)

c.caption(
    '<div class="metric-note"><b>Cómo leer la tabla:</b> cada fila representa un aspecto del juego. '
    '<b>Δ</b> = diferencia entre jugadores · <b>%</b> = posición relativa frente al resto de la liga.</div>',
    unsafe_allow_html=True
)
c.dataframe(df_cmp, use_container_width=True, hide_index=True)

# ===================== EXPORTAR RADAR =====================
gen = c.button("🖼️ Generar PNG del radar", key="cmp_png_btn")
if gen:
    try:
        st.session_state["radar_png"] = fig.to_image(format="png", scale=2)
        c.success("PNG generado. Ahora puedes descargarlo.")
    except Exception as e:
        c.error(f"No se pudo generar el PNG. ¿Tienes 'kaleido' instalado? Detalle: {e}")

if "radar_png" in st.session_state:
    c.download_button(
        "⬇️ Descargar radar (PNG)",
        data=st.session_state["radar_png"],
        file_name=f"radar_{'_vs_'.join(sel_players)}.png",
        mime="image/png",
        key="cmp_png_dl"
    )

def _radar_png_for_pdf() -> bytes | None:
    """Genera radar ligero para PDF sin depender de kaleido."""
    try:
        fig_m = plt.figure(figsize=(6.8, 6.0), facecolor="#0B0F17")
        ax = fig_m.add_subplot(111, polar=True)
        ax.set_facecolor("#0B0F17")

        n = len(theta_labels)
        if n == 0:
            plt.close(fig_m)
            return None

        angles = [2 * 3.1415926535 * i / n for i in range(n)]
        angles += angles[:1]
        palette_m = ["#DA291C", "#FBE122", "#C0C0C0"]

        for i, pl in enumerate(sel_players):
            if pl not in player_means.index:
                continue
            vals = player_means.loc[pl, radar_feats].fillna(0).tolist()
            vals += vals[:1]
            ax.plot(angles, vals, color=palette_m[i % len(palette_m)], linewidth=2, label=pl)
            ax.fill(angles, vals, color=palette_m[i % len(palette_m)], alpha=0.12)

        ax.set_ylim(0, 100)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(theta_labels, fontsize=8, color="white")
        ax.tick_params(colors="white")
        ax.grid(color="#374151", alpha=0.45)
        ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.15), frameon=False, fontsize=8)

        buf = io.BytesIO()
        fig_m.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="#0B0F17")
        plt.close(fig_m)
        return buf.getvalue()
    except Exception:
        return None


if c.button("📄 Preparar comparativa (PDF)", key="cmp_pdf_prepare"):
    with st.spinner("Preparando informe comparativo..."):
        radar_img = _radar_png_for_pdf()
        st.session_state["cmp_pdf_bytes"] = build_report_pdf(
            title="Informe comparativo de jugadores",
            subtitle=f"Comparativa directa con referencia en {ref_player}",
            bullet_points=[
                f"Jugadores analizados: {', '.join(sel_players)}",
                f"Indicadores del radar: {len(radar_feats)}",
                f"Contexto de comparacion: {ctx_mode}",
                f"Indicadores usados: {', '.join([label(f) for f in radar_feats])}",
            ],
            table_df=df_cmp.head(16),
            table_title="Resumen de comparativa",
            max_rows=16,
            max_cols=8,
            image_bytes=radar_img,
        )
    c.success("Informe listo para descarga.")

if st.session_state.get("cmp_pdf_bytes"):
    c.download_button(
        "⬇️ Descargar comparativa (PDF)",
        data=st.session_state["cmp_pdf_bytes"],
        file_name=f"comparador_{ref_player}.pdf",
        mime="application/pdf",
        key="cmp_pdf_dl",
    )
