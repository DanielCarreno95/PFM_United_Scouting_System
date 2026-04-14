from __future__ import annotations

from pathlib import Path


BASE = Path("data/raw/fbref_2025_2026")

FILES = [
    "fbref_2025_2026_standard",
    "fbref_2025_2026_shooting",
    "fbref_2025_2026_passing",
    "fbref_2025_2026_passing_types",
    "fbref_2025_2026_gca",
    "fbref_2025_2026_defense",
    "fbref_2025_2026_possession",
    "fbref_2025_2026_misc",
    "fbref_2025_2026_keeper",
    "fbref_2025_2026_keeper_adv",
]


def main() -> int:
    print(f"Checking dropzone: {BASE.as_posix()}")
    if not BASE.exists():
        print("ERROR: dropzone folder does not exist.")
        return 1

    missing: list[str] = []
    found: list[str] = []

    for stem in FILES:
        csv = BASE / f"{stem}.csv"
        xlsx = BASE / f"{stem}.xlsx"
        if csv.exists():
            found.append(csv.as_posix())
        elif xlsx.exists():
            found.append(xlsx.as_posix())
        else:
            missing.append(stem)

    print("\nFound files:")
    for f in found:
        print(f"- {f}")

    if missing:
        print("\nMissing blocks:")
        for m in missing:
            print(f"- {m} (.csv or .xlsx)")
        return 2

    print("\nOK: all required FBref blocks are present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

