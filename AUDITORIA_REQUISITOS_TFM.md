# Auditoria de requisitos (fase actual)

## Referencias revisadas

- `MPAD_TFM.pdf`
- `PFM - Estructura de documentacion.pdf`

## 1) Requisitos funcionales de aplicacion

- **Login / control de acceso**: Cumplido.
- **Menu y navegacion multipagina**: Cumplido.
- **Filtros (dropdown, slider, etc.)**: Cumplido.
- **Home + pagina(s) stats**: Cumplido.
- **Exportacion PDF con `fpdf`**: Cumplido (migrado a `fpdf2` y activo en `Overview`, `Ranking`, `Comparador` y `Similares`).
- **Metrica ML explicita**: Cumplido (Similares usa similitud coseno ponderada).
- **Separacion backend/frontend + scripts/notebooks**: Cumplido (estructura `utils/`, `pages/`, `scripts/`).

## 2) Entregables MPAD (estado)

- **Documento marco**: Pendiente de cierre final.
- **Link app desplegada**: Disponible (ver README), revisar que este actualizado.
- **Link repositorio GitHub**: Pendiente validar version final.
- **Link zip codigo**: Pendiente preparar.
- **Video <= 5 min (YouTube)**: Pendiente grabar/subir.

## 3) Calidad de dato y coherencia deportiva

- App configurada para trabajar solo con **Premier 2025/26** real.
- Se elimino mezcla con dataset `rich` para evitar incoherencias.
- En Overview (scatter) se corrigio la causa del desfase visual:
  - antes se recortaban ejes al percentil 99;
  - ahora se usa rango real completo (coherente con ranking).

## 4) Que podemos eliminar (si confirmas)

Para mantener la carpeta limpia y alineada al alcance actual (solo 2025/26 real):

- `data/processed/premier_rich_df_final_20260413.parquet` (ya no operativo).
- `data/processed/scouting_laliga_df_final_20250923.parquet` (fuente legacy).
- `scripts/build_premier_rich_dataset.py` (pipeline legacy del dataset normalizado).
- `scripts/check_fbref_uploads.py` y `scripts/validate_fbref_quality.py` si no vas a reutilizar carga manual FBref.

## 5) Recomendacion de cierre en 24h

1. Validacion funcional completa app (checklist ya creado).
2. Congelar dataset y narrativa (2025/26, un solo alcance).
3. Cerrar documento marco con estructura del PDF de requisitos.
4. Grabar video de 5 min con flujo: login -> overview -> ranking -> comparador -> similares -> PDF/CSV.
