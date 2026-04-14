from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class BuildConfig:
    season_slug: str = "2025-2026"
    out_dir: Path = Path("data/processed")
    out_prefix: str = "premier_df_final_"
    # Fallback manual (100% reproducible) si FBref bloquea descargas automatizadas.
    # Debe ser el CSV exportado desde la tabla "Player Standard Stats".
    local_csv: Path | None = None


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).strip().lower().replace(" ", "_") for c in out.columns]
    return out


def _dedupe_cols(cols: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    out: list[str] = []
    for c in cols:
        k = c if c else "col"
        if k not in seen:
            seen[k] = 0
            out.append(k)
        else:
            seen[k] += 1
            out.append(f"{k}.{seen[k]}")
    return out


def _read_local_file(path: Path) -> pd.DataFrame:
    """
    Lee CSV o XLSX exportado desde FBref.
    Soporta XLSX con cabecera agrupada (dos niveles) como la que has descargado.
    """
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)

    if suffix in {".xlsx", ".xls"}:
        # Intento 1: leer con header multinivel y usar el nivel inferior como nombre real.
        try:
            x = pd.read_excel(path, header=[0, 1])
            if isinstance(x.columns, pd.MultiIndex):
                flat_cols: list[str] = []
                for a, b in x.columns:
                    a_s = str(a).strip()
                    b_s = str(b).strip()
                    if b_s and "unnamed" not in b_s.lower():
                        flat_cols.append(b_s)
                    elif a_s and "unnamed" not in a_s.lower():
                        flat_cols.append(a_s)
                    else:
                        flat_cols.append("col")
                x.columns = _dedupe_cols(flat_cols)
                return x
        except Exception:
            pass

        # Intento 2: hoja simple donde la primera fila de datos trae los headers reales.
        x = pd.read_excel(path)
        if len(x) > 0:
            first = x.iloc[0].astype(str).str.strip().str.lower()
            if ("player" in first.values) and ("squad" in first.values):
                new_cols = [
                    (str(v).strip() if str(v).strip() and str(v).strip().lower() != "nan" else str(c))
                    for c, v in zip(x.columns, x.iloc[0].tolist())
                ]
                x = x.iloc[1:].copy()
                x.columns = _dedupe_cols(new_cols)
        return x

    raise RuntimeError(f"Formato no soportado: {path.suffix}. Usa CSV o XLSX.")


def _coalesce_columns(df: pd.DataFrame, candidates: list[str], out_col: str) -> pd.DataFrame:
    """
    Crea out_col tomando el primer valor no nulo de columnas candidatas.
    """
    present = [c for c in candidates if c in df.columns]
    if not present:
        return df
    out = df.copy()
    out[out_col] = out[present].bfill(axis=1).iloc[:, 0]
    return out


def _safe_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    for c in cols:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")
    return out


def _map_role_tactico(pos: str | None) -> str:
    """
    Mapeo simple y reproducible desde FBref 'pos' (e.g. 'MF,DF') a los roles usados por la app.
    Mantiene la taxonomía del proyecto original:
    (delantero, volante, mediocentro, lateral, central, portero)
    """
    if not pos:
        return "Desconocido"

    p = str(pos).upper().replace(" ", "")
    if "GK" in p:
        return "Portero"
    if "DF" in p and "FW" in p:
        return "Volante"
    if "MF" in p and "FW" in p:
        return "Volante"
    if "DF" in p:
        # FBref no diferencia claramente lateral/central en 'pos' sin más columnas.
        # Para no inventar: asignamos "Central" por defecto (se puede refinar luego).
        return "Central"
    if "MF" in p:
        return "Mediocentro"
    if "FW" in p:
        return "Delantero"
    return "Desconocido"


def _fetch_fbref_player_standard_table(season_slug: str) -> pd.DataFrame:
    """
    Devuelve la tabla de "Player Standard Stats" para Premier League.

    Nota: FBref suele bloquear requests sin navegador. Usamos cloudscraper (anti-bot)
    y, si aun así falla, este script permite un modo 100% reproducible con CSV local.
    """
    try:
        import cloudscraper
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "Falta dependencia 'cloudscraper'. Ejecuta: pip install -r requirements.txt"
        ) from e

    # URL "player stats" (a menudo bloqueado con 403 desde scripts).
    # Si FBref cambia la ruta o bloquea, usa el modo --local-csv.
    url = f"https://fbref.com/en/comps/9/{season_slug}/stats/players/{season_slug}-Premier-League-Stats"

    scraper = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "desktop": True}
    )
    try:
        resp = scraper.get(url, timeout=60)
        resp.raise_for_status()
    except Exception as e:
        raise RuntimeError(
            "FBref bloqueó la descarga automática (403) o no se pudo acceder.\n"
            "Solución 100% reproducible: exporta el CSV desde tu navegador y vuelve a ejecutar:\n"
            "  python scripts/build_premier_2025_2026_dataset.py --local-csv data/raw/fbref_premier_2025_2026_standard.csv\n"
        ) from e

    # FBref a veces mete comentarios HTML; read_html suele funcionar con html5lib+lxml instalados
    tables = pd.read_html(resp.text)
    if not tables:
        raise RuntimeError("No se encontraron tablas en la página de FBref.")

    # Heurística: la tabla de jugadores suele tener columna 'Player' y 'Squad'
    candidates: list[pd.DataFrame] = []
    for t in tables:
        cols = {str(c).strip().lower() for c in t.columns}
        if "player" in cols and ("squad" in cols or "team" in cols):
            candidates.append(t)

    if not candidates:
        raise RuntimeError(
            "No pude localizar la tabla de jugadores (Player/Squad) en el HTML descargado."
        )

    # Si hay varias, nos quedamos con la más ancha (más métricas)
    return max(candidates, key=lambda d: d.shape[1]).copy()


def build_dataset(cfg: BuildConfig) -> Path:
    """
    Construye dataset Premier League 2025-2026 con columnas compatibles con la app.

    Salida:
    - Parquet en data/processed/ con columnas compatibles con la app:
      player, squad, season, league, age, min, rol_tactico, + métricas *_per90 (cuando existan)
    """
    if cfg.local_csv is not None:
        if not cfg.local_csv.exists():
            raise FileNotFoundError(f"No existe el archivo local: {cfg.local_csv}")
        df = _read_local_file(cfg.local_csv)
    else:
        df = _fetch_fbref_player_standard_table(cfg.season_slug)

    df = _normalize_columns(df)

    # Limpieza básica de filas no jugador (cabeceras repetidas)
    if "player" in df.columns:
        df["player"] = df["player"].astype(str).str.strip()
        df = df[df["player"].str.lower() != "player"]
        df = df[df["player"].notna()]

    # Renombrar claves a la convención de la app
    if "team" in df.columns and "squad" not in df.columns:
        df = df.rename(columns={"team": "squad"})
    if "comp" in df.columns and "league" not in df.columns:
        df = df.rename(columns={"comp": "league"})
    if "squad" not in df.columns:
        raise RuntimeError("El dataset no contiene columna 'squad'/'team'.")
    if "player" not in df.columns:
        raise RuntimeError("El dataset no contiene columna 'player'.")

    # FBref CSV suele traer duplicados tipo gls, gls.1 (totales vs per90).
    # Coalescencia defensiva para columnas base.
    df = _coalesce_columns(df, ["age", "age_"], "age")
    df = _coalesce_columns(df, ["min", "minutes"], "min")
    df = _coalesce_columns(df, ["pos", "position"], "pos")
    df = _coalesce_columns(df, ["90s", "_90s"], "90s")
    df = _coalesce_columns(df, ["gls", "goals"], "gls")
    df = _coalesce_columns(df, ["ast", "assists"], "ast")
    df = _coalesce_columns(df, ["xg"], "xg")
    df = _coalesce_columns(df, ["xag", "xa"], "xag")
    df = _coalesce_columns(df, ["npxg"], "npxg")
    df = _coalesce_columns(df, ["prgc"], "prgc")
    df = _coalesce_columns(df, ["prgp"], "prgp")

    # Añadir season/league para sidebar (constantes y reproducibles)
    df["season"] = cfg.season_slug
    df["league"] = "Premier League"

    # Age FBref puede venir como "25-173": nos quedamos con la edad en años.
    if "age" in df.columns:
        age_txt = df["age"].astype(str)
        df["age"] = age_txt.str.extract(r"^(\d+)")[0]

    # Normalizaciones claves
    df = _safe_numeric(df, ["age", "min", "90s", "gls", "ast", "xg", "xag", "npxg", "npxg+xag", "prgc", "prgp"])

    # Rol táctico
    pos_col = "pos" if "pos" in df.columns else ("position" if "position" in df.columns else None)
    if pos_col:
        df["rol_tactico"] = df[pos_col].map(_map_role_tactico)
    else:
        df["rol_tactico"] = "Central"

    # Métricas per90: si FBref trae 90s y las métricas totales, calculamos per90 de forma determinista
    if "90s" in df.columns:
        ninety = pd.to_numeric(df["90s"], errors="coerce")
        with pd.option_context("mode.use_inf_as_na", True):
            for src, outc in [
                ("gls", "gls_per90"),
                ("ast", "ast_per90"),
                ("xg", "xg_per90"),
                ("xag", "xa_per90"),
                ("prgc", "prgc_per90"),
                ("prgp", "prgp_per90"),
            ]:
                if src in df.columns:
                    df[outc] = (pd.to_numeric(df[src], errors="coerce") / ninety).replace([pd.NA], pd.NA)

    # Si el CSV ya trae columnas per90 (a veces como gls.1/ast.1/xg.1...), las usamos como fallback.
    per90_fallbacks = {
        "gls_per90": ["gls.1", "per_90_minutes_gls"],
        "ast_per90": ["ast.1", "per_90_minutes_ast"],
        "ga_per90": ["g+a.1", "per_90_minutes_g+a", "per_90_minutes_g_a"],
        "gpk_per90": ["g-pk.1", "per_90_minutes_g-pk", "per_90_minutes_g_pk"],
        "gapk_per90": ["g+a-pk", "per_90_minutes_g+a-pk", "per_90_minutes_g_a_pk"],
        "xg_per90": ["xg.1", "per_90_minutes_xg"],
        "xa_per90": ["xag.1", "xag.1", "per_90_minutes_xag"],
        "npxg_per90": ["npxg.1", "per_90_minutes_npxg"],
    }
    for target, srcs in per90_fallbacks.items():
        if target not in df.columns:
            df = _coalesce_columns(df, srcs, target)

    # Extras per90 derivados de columnas estándar cuando existen.
    if "90s" in df.columns:
        ninety = pd.to_numeric(df["90s"], errors="coerce")
        deriv = {
            "pk_per90": "pk",
            "crdy_per90": "crdy",
            "crdr_per90": "crdr",
        }
        for out_col, src_col in deriv.items():
            if out_col not in df.columns and src_col in df.columns:
                df[out_col] = pd.to_numeric(df[src_col], errors="coerce") / (ninety + 1e-9)

    # Columnas mínimas que la app usa en casi todas las páginas
    keep_first = ["player", "squad", "season", "league", "rol_tactico", "age", "min"]
    existing_keep_first = [c for c in keep_first if c in df.columns]
    rest = [c for c in df.columns if c not in existing_keep_first]
    df = df[existing_keep_first + rest]

    # Drop filas claramente inválidas
    if "player" in df.columns:
        df = df[df["player"].notna()]

    cfg.out_dir.mkdir(parents=True, exist_ok=True)
    out_path = cfg.out_dir / f"{cfg.out_prefix}{date.today().strftime('%Y%m%d')}.parquet"
    df.to_parquet(out_path, index=False)
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--season-slug", default="2025-2026")
    parser.add_argument("--out-dir", default="data/processed")
    parser.add_argument("--out-prefix", default="premier_df_final_")
    parser.add_argument(
        "--local-csv",
        default=None,
        help="Ruta a archivo local FBref (CSV o XLSX) (fallback si hay 403).",
    )
    args = parser.parse_args()

    cfg = BuildConfig(
        season_slug=args.season_slug,
        out_dir=Path(args.out_dir),
        out_prefix=args.out_prefix,
        local_csv=Path(args.local_csv) if args.local_csv else None,
    )
    out = build_dataset(cfg)
    print(f"OK: wrote {out.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

