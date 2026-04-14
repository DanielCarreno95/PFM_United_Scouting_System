from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd


SOURCE = Path("data/processed/scouting_laliga_df_final_20250923.parquet")
OUT_DIR = Path("data/processed")
OUT_PREFIX = "premier_rich_df_final_"


def main() -> int:
    if not SOURCE.exists():
        raise FileNotFoundError(f"No se encontró el parquet fuente: {SOURCE.as_posix()}")

    df = pd.read_parquet(SOURCE).copy()
    df.columns = [str(c).strip().lower() for c in df.columns]

    if "comp" not in df.columns:
        raise RuntimeError("El parquet fuente no contiene columna 'comp'.")

    # Solo Premier League (mantiene temporadas históricas disponibles)
    out = df[df["comp"].astype(str) == "Premier League"].copy()
    if out.empty:
        raise RuntimeError("No hay filas de Premier League en el parquet fuente.")

    # Estandarizaciones para la app
    out["league"] = "Premier League"
    if "season" in out.columns:
        out["season"] = out["season"].astype(str)

    # Conversión numérica para columnas operativas
    for c in ["age", "min"]:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")

    # Garantía de columnas mínimas
    required = ["player", "squad", "season", "league", "rol_tactico", "age", "min"]
    missing = [c for c in required if c not in out.columns]
    if missing:
        raise RuntimeError(f"Faltan columnas mínimas en dataset curado: {missing}")

    # Limpieza de filas sin identidad básica
    out = out[out["player"].notna() & out["squad"].notna() & out["season"].notna()].copy()

    # Orden estable para inspección
    out = out.sort_values(["season", "squad", "player"]).reset_index(drop=True)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{OUT_PREFIX}{date.today().strftime('%Y%m%d')}.parquet"
    out.to_parquet(out_path, index=False)
    print(f"OK: wrote {out_path.as_posix()} | shape={out.shape}")
    print(f"Seasons: {sorted(out['season'].dropna().unique().tolist())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

