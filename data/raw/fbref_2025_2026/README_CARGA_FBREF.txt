DROPZONE DE CARGA FBREF (PREMIER LEAGUE 2025-2026)
===================================================

Objetivo:
- Recuperar el nivel de detalle del dataset inicial (incluyendo perfiles de portero)
- Mantener la plataforma consistente para Direccion Deportiva (Manchester United)

Ruta de carga:
- data/raw/fbref_2025_2026/

IMPORTANTE:
- Exporta SIEMPRE desde "Player Stats" (no "Squad Stats")
- Formato recomendado: CSV (tambien aceptamos XLSX)
- Misma temporada para todos: 2025-2026 Premier League

Archivos requeridos (nombres exactos recomendados):
1) fbref_2025_2026_standard.csv
2) fbref_2025_2026_shooting.csv
3) fbref_2025_2026_passing.csv
4) fbref_2025_2026_passing_types.csv
5) fbref_2025_2026_gca.csv
6) fbref_2025_2026_defense.csv
7) fbref_2025_2026_possession.csv
8) fbref_2025_2026_misc.csv
9) fbref_2025_2026_keeper.csv
10) fbref_2025_2026_keeper_adv.csv

Si exportas en XLSX:
- usa exactamente los mismos nombres pero con extension .xlsx

Mapeo de valor deportivo por bloque:
- standard/shooting/passing/gca/defense/possession/misc: jugadores de campo
- keeper/keeper_adv: porteros (save%, psxg, cs%, launch%, etc.)

