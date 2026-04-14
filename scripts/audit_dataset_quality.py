"""
Auditoría interna del parquet operativo (misma lógica de selección que la app).

Uso (desde la raíz del proyecto):
    python scripts/audit_dataset_quality.py
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def pick_operational_parquet(folder: Path | None = None) -> Path:
    """Misma prioridad que `utils.data_loader.get_latest_processed_file` (sin Streamlit)."""
    p = folder or (ROOT / "data" / "processed")
    rich = sorted(p.glob("premier_rich_df_final_*.parquet"), key=lambda x: x.stat().st_mtime, reverse=True)
    if rich:
        return rich[0]
    all_p = sorted(p.glob("*.parquet"), key=lambda x: x.stat().st_mtime, reverse=True)
    if not all_p:
        raise FileNotFoundError(f"No hay parquet en {p}")
    return all_p[0]


def _metric_cols(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if str(c).endswith("_per90") or str(c) in ("cmp%", "save%")]


def main() -> int:
    path = pick_operational_parquet()
    print("=" * 72)
    print("AUDITORÍA DATASET — United Elite Scouting Hub")
    print("=" * 72)
    print(f"Archivo: {path.resolve()}")
    df = pd.read_parquet(path)
    df.columns = [str(c).strip().lower() for c in df.columns]
    print(f"Filas: {len(df):,} | Columnas: {len(df.columns)}")

    for col in ("league", "comp", "season", "squad", "player", "min", "age", "rol_tactico", "pos"):
        if col in df.columns:
            print(f"  [OK] {col}")
        else:
            print(f"  [--] falta: {col}")

    if "season" in df.columns:
        vc = df["season"].astype(str).value_counts().sort_index()
        print("\n--- Distribución por temporada ---")
        for s, n in vc.items():
            print(f"  {s}: {n:,}")

    mcols = _metric_cols(df)
    print(f"\n--- Métricas detectadas ({len(mcols)}) ---")
    if not mcols:
        print("  (ninguna columna *_per90 / cmp% / save%)")
        return 1

    null_pct = (df[mcols].isna().mean() * 100).sort_values(ascending=False)
    worst = null_pct.head(12)
    print("Top ausencias (% de filas nulas):")
    for c, v in worst.items():
        print(f"  {c}: {v:.1f}%")

    all_ok = null_pct.max()
    full = (null_pct == 0).sum()
    print(f"\nColumnas métricas sin nulos: {full}/{len(mcols)} | Peor caso: {all_ok:.1f}% nulos")

    if "min" in df.columns:
        mn = pd.to_numeric(df["min"], errors="coerce")
        low = (mn < 300).sum()
        print(f"\nFilas con min < 300: {low:,} ({100 * low / len(df):.1f}%)")

    if "player" in df.columns and "season" in df.columns:
        dup = df.duplicated(subset=["player", "season", "squad"], keep=False).sum()
        print(f"Filas en posible duplicado (player+season+squad): {dup:,}")

    print("\n" + "=" * 72)
    print("Fin auditoría.")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
