# =====================================
# utils/data_loader.py  ✅ VERSIÓN LIMPIA (sin mensaje de carga)
# =====================================

import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path

# ==============================
# Funciones de carga de datos
# ==============================

@st.cache_data
def load_parquet_data(path: str):
    """Carga un archivo Parquet con cacheo para optimizar rendimiento."""
    return pd.read_parquet(path)

@st.cache_data
def load_csv_data(path: str):
    """Carga un archivo CSV con cacheo."""
    return pd.read_csv(path)

# ==============================
# Funciones auxiliares
# ==============================

def normalize_0_1(series: pd.Series):
    """Normaliza una serie numérica entre 0 y 1."""
    if series.max() == series.min():
        return np.zeros_like(series)
    return (series - series.min()) / (series.max() - series.min())

def build_row_key(df: pd.DataFrame, cols: list):
    """Crea una columna única de clave combinada."""
    return df[cols].astype(str).agg('_'.join, axis=1)

def get_latest_processed_file(folder="data/processed", ext=".parquet"):
    """
    Elige el parquet operativo para la app.

    Prioridad (modo TFM actual):
    1) `premier_df_final_*.parquet` (dataset real de temporada 2025/26).
    2) Cualquier `premier*_df_final_*.parquet` no `rich` como respaldo.
    3) `premier_rich_df_final_*.parquet` solo como último recurso.
    """
    p = Path(folder)
    if not p.is_dir():
        raise FileNotFoundError(f"No existe la carpeta de datos procesados: {folder}")

    primary = sorted(p.glob(f"premier_df_final_*{ext}"), key=lambda x: x.stat().st_mtime, reverse=True)
    if primary:
        return primary[0]

    all_df_final = sorted(p.glob(f"*_df_final_*{ext}"), key=lambda x: x.stat().st_mtime, reverse=True)
    premier_real = [
        f for f in all_df_final
        if ("premier" in f.name.lower())
        and ("rich" not in f.name.lower())
        and ("scouting_laliga" not in f.name.lower())
    ]
    if premier_real:
        return premier_real[0]

    rich = sorted(p.glob(f"premier_rich_df_final_*{ext}"), key=lambda x: x.stat().st_mtime, reverse=True)
    if rich:
        return rich[0]

    archivos = sorted(p.glob(f"*{ext}"), key=lambda x: x.stat().st_mtime, reverse=True)
    if not archivos:
        raise FileNotFoundError(f"No se encontró ningún archivo {ext} en {folder}")
    return archivos[0]

# ==============================
# Función principal de carga
# ==============================

@st.cache_data
def load_main_dataset():
    """
    Carga el dataset procesado más reciente y lo prepara para uso en la app.
    - Detecta automáticamente el último archivo exportado.
    - Convierte nombres de columnas a minúsculas.
    - Crea 'row_key' combinando player + season + squad.
    - Asegura columna 'league'.
    - Verifica rango 0–100 solo en métricas escaladas.
    """
    # Buscar el archivo más reciente generado por el ETL
    latest_file = get_latest_processed_file()

    # Leer el parquet
    df = load_parquet_data(str(latest_file))

    # Estandarizar nombres de columnas
    df.columns = [c.lower() for c in df.columns]
    # Evita fallos cuando existen nombres duplicados (p.ej. league repetida).
    df = df.loc[:, ~df.columns.duplicated(keep="first")].copy()

    # Modo operativo del TFM: trabajar exclusivamente temporada 2025/26.
    if "season" in df.columns:
        s = df["season"].astype(str).str.strip()
        mask = s.isin(["2025-2026", "2025/26"])
        if mask.any():
            df = df.loc[mask].copy()
            df["season"] = "2025/26"

    # Crear columna clave única
    base_cols = [c for c in ["player", "season", "squad"] if c in df.columns]
    if len(base_cols) == 3:
        df["row_key"] = build_row_key(df, base_cols)
    else:
        st.warning("⚠️ No se pudieron crear las claves únicas: faltan columnas base (player, season o squad).")

    # Renombrar 'comp' → 'league' solo si league no existe ya.
    if "comp" in df.columns and "league" not in df.columns:
        df.rename(columns={"comp": "league"}, inplace=True)
    elif "league" not in df.columns:
        df["league"] = "Desconocida"

    # ✅ Validar solo métricas escaladas (las *_per90 y los %)
    cols_check = [c for c in df.columns if c.endswith("_per90") or c.endswith("%")]
    if cols_check:
        fuera_de_rango = df[(df[cols_check] < 0).any(axis=1) | (df[cols_check] > 100).any(axis=1)]
        if not fuera_de_rango.empty:
            st.warning(f"⚠️ {len(fuera_de_rango)} filas tienen valores fuera del rango esperado (0–100) en métricas escaladas.")

    return df
