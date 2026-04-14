# Checklist entrega 24h (TFM)

## Estado actual

- [x] Dataset operativo unico: Premier League 2025/26 (`premier_df_final_*`).
- [x] Sidebar sin filtro de temporada.
- [x] Copy deportivo en filtros y paginas principales.
- [x] Ranking y visualizaciones con datos reales (no normalizados 0-1).
- [x] Exportacion PDF en todos los modulos activos (`Overview`, `Ranking`, `Comparador`, `Similares`) con `fpdf2`.
- [x] Metrica ML explicita en Similares (similitud coseno ponderada).

## Verificaciones obligatorias antes de entregar

- [ ] Prueba funcional completa en Streamlit:
  - [ ] Login
  - [ ] Overview (graficas + PDF)
  - [ ] Ranking (filtros + CSV + PDF)
  - [ ] Comparador (radar + PNG + PDF)
  - [ ] Similares (tabla + CSV + PDF)
- [ ] Capturas finales de cada modulo para memoria.
- [ ] Revisar README final (coherente con 2025/26 y `fpdf2`).
- [ ] Generar video demo corto de flujo completo.

## Riesgos conocidos y mitigacion

- FBref puede devolver 403 para automatizacion: mantener CSV local exportado como respaldo.
- Datos parciales por minutos bajos: usar umbral minimo de minutos en analisis.
- Caches de Streamlit: reiniciar app tras cambios de dataset/configuracion.

## Comandos de apoyo

```bash
streamlit run app.py
python -m py_compile pages/1_Overview.py pages/2_Ranking.py pages/3_Comparador.py pages/4_Similares.py
```
