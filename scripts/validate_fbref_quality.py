from __future__ import annotations

from pathlib import Path
import pandas as pd


BASE = Path("data/raw/fbref_2025_2026")

EXPECTED = {
    "fbref_2025_2026_standard": ["90s", "gls", "ast"],
    "fbref_2025_2026_shooting": ["sh", "sot"],
    "fbref_2025_2026_passing": ["cmp", "att", "kp"],
    "fbref_2025_2026_passing_types": ["att", "live", "dead"],
    "fbref_2025_2026_gca": ["sca", "sca90", "gca", "gca90"],
    "fbref_2025_2026_defense": ["tkl", "int"],
    "fbref_2025_2026_possession": ["touches", "carries"],
    "fbref_2025_2026_misc": ["crdy", "crdr"],
    "fbref_2025_2026_keeper": ["min", "ga90", "saves", "save%"],
    "fbref_2025_2026_keeper_adv": ["psxg", "psxg+/-", "launch%", "#opa/90"],
}


def parse_fbref_xlsx(path: Path) -> pd.DataFrame:
    x = pd.read_excel(path, header=None)
    h1 = x.iloc[0].astype(str).str.strip()
    h2 = x.iloc[1].astype(str).str.strip()
    cols: list[str] = []
    for a, b in zip(h1, h2):
        a = "" if a.lower() == "nan" else a
        b = "" if b.lower() == "nan" else b
        cols.append((b if b else a) or "col")

    seen: dict[str, int] = {}
    out_cols: list[str] = []
    for c in cols:
        c2 = c.lower().replace(" ", "_")
        if c2 not in seen:
            seen[c2] = 0
            out_cols.append(c2)
        else:
            seen[c2] += 1
            out_cols.append(f"{c2}.{seen[c2]}")

    df = x.iloc[2:].copy()
    df.columns = out_cols
    if "player" in df.columns:
        df = df[df["player"].astype(str).str.lower() != "player"]
    return df


def main() -> int:
    if not BASE.exists():
        print(f"ERROR: no existe {BASE.as_posix()}")
        return 1

    failed = False
    for stem, critical in EXPECTED.items():
        file = next((p for p in [BASE / f"{stem}.xlsx", BASE / f"{stem}.csv"] if p.exists()), None)
        if file is None:
            print(f"[MISSING] {stem}")
            failed = True
            continue

        if file.suffix.lower() == ".xlsx":
            df = parse_fbref_xlsx(file)
        else:
            df = pd.read_csv(file)
            df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

        print(f"\n[{stem}] rows={len(df)} cols={len(df.columns)}")
        for col in critical:
            candidates = [c for c in df.columns if c == col or c.startswith(col + ".")]
            if not candidates:
                print(f"  - {col}: MISSING_COL")
                failed = True
                continue
            c = candidates[0]
            nn = float(df[c].notna().mean() * 100)
            print(f"  - {c}: {nn:.1f}% non-null")
            if nn < 20.0:
                failed = True

    if failed:
        print("\nRESULT: FAILED (hay tablas/columnas clave incompletas).")
        return 2

    print("\nRESULT: OK (calidad mínima superada).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

