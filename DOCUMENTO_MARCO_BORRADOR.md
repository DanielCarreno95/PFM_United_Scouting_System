# Documento Marco (Borrador Finalizable)

## 1. Portada
- **Proyecto:** United Elite Scouting Hub
- **Autor:** Daniel Carreno
- **Programa:** Master en Python Avanzado aplicado al Deporte (MPAD)
- **Modulo:** M11 - Proyecto Final
- **Fecha:** Abril 2026

## 2. Indice
- Incluir tabla de contenido automatica en Word/Docs.

## 3. Recursos
- **Aplicacion desplegada:** (pegar link final)
- **Repositorio GitHub:** (pegar link final)
- **Video explicativo (YouTube):** (pegar link final)
- **ZIP del codigo:** (pegar link OneDrive/Drive final)

## 4. Resumen Ejecutivo
Este proyecto desarrolla una plataforma de apoyo a la Direccion Deportiva de Manchester United para priorizar decisiones de scouting en Premier League 2025/26. La herramienta integra analitica de rendimiento, comparacion de perfiles, ranking de mercado y busqueda de alternativas por similitud estadistica, con una interfaz orientada a usuarios deportivos no tecnicos.

El resultado es una aplicacion web funcional con autenticacion, filtros transversales, exportaciones en PDF/CSV y un flujo de analisis replicable. La plataforma permite reducir tiempos de analisis, mejorar la trazabilidad de decisiones y elevar la calidad del filtrado inicial de candidatos.

## 5. Introduccion
Los departamentos de scouting necesitan transformar volumen de datos en decisiones accionables. En un contexto de mercado competitivo, el valor no solo reside en detectar talento, sino en compararlo con coherencia tactica, disponibilidad de minutos y encaje deportivo.

Este trabajo propone una solucion aplicada al caso Manchester United, centrada en Premier League 2025/26, con una arquitectura modular y orientacion practica para uso diario de Direccion Tecnica y Scouting.

## 6. Objetivos
### Objetivo general
Desarrollar una aplicacion de scouting profesional, desplegable y mantenible, que convierta datos publicos en analisis utiles para la toma de decisiones deportivas.

### Objetivos especificos
- Implementar un dashboard multi-modulo con autenticacion.
- Estandarizar y consumir un dataset operativo unico (Premier 2025/26).
- Incluir filtros clave (equipo, puesto, posicion, edad, minutos).
- Permitir exportacion de informes en PDF y tablas en CSV.
- Incorporar una metrica de Machine Learning explicita (similitud coseno ponderada).

## 7. Escenario temporal
- Definicion del caso de uso y alcance.
- Preparacion de datos y validaciones de coherencia.
- Desarrollo de modulos Streamlit.
- Auditoria funcional y de requisitos MPAD.
- Preparacion de entregables finales (documento, links, video).

## 8. Arquitectura conceptual y tecnologica
- **Frontend:** Streamlit (paginas de Overview, Ranking, Comparador, Similares).
- **Backend funcional:** `utils/` para carga de datos, filtros y utilidades PDF.
- **Datos:** parquet procesado de Premier 2025/26.
- **Visualizacion:** Plotly + Matplotlib (export de imagen para PDF).
- **Exportes:** `fpdf2` para PDF, CSV para tablas.

## 9. Metodologia (CRISP-DM)
### Comprension del negocio
Caso de uso orientado a priorizacion de candidatos y comparacion de perfiles de mercado.

### Comprension de datos
Revision de campos de rendimiento, minutos y consistencia por jugador/equipo.

### Preparacion de datos
Normalizacion de columnas, filtrado competitivo y consolidacion en dataset unico operativo.

### Modelado
Uso de similitud coseno ponderada en modulo de Similares para ranking de cercania de perfiles.

### Evaluacion
Validacion cruzada entre modulos para coherencia deportiva (ranking, comparador y overview).

### Despliegue
Aplicacion desplegada en Streamlit y documentada para uso y entrega.

## 10. Desarrollo del trabajo
### Modulo Overview
Vision global de la competicion: cruce de indicadores, reparto de perfiles, perfil por equipo y evolucion.

### Modulo Ranking
Priorizacion por indicador unico o composicion de indicadores ponderados.

### Modulo Comparador
Radar y tabla comparativa de hasta tres jugadores con lectura por contexto de grupo.

### Modulo Similares
Busqueda de alternativas de mercado por similitud estadistica.

## 11. Discusion de resultados
La plataforma demuestra utilidad en la fase de pre-filtrado de mercado, especialmente al combinar visualizacion y comparacion estructurada. Las decisiones finales siguen requiriendo contexto de scouting cualitativo (video, seguimiento en vivo, situacion contractual).

## 12. Conclusiones y trabajo futuro
- Se cumple una solucion funcional, deployable y orientada a negocio deportivo.
- La metrica ML aporta valor practico en deteccion de reemplazos.
- Como evolucion: ampliar cobertura temporal y enriquecer variables contractuales y fisicas.

## 13. Bibliografia
- FBref (fuente principal de estadisticas).
- Documentacion oficial Streamlit, Plotly, FPDF2, Pandas, NumPy.
- Material del Master MPAD.

## 14. Anexos
- Capturas de cada modulo.
- Checklist funcional de entrega.
- Auditoria de requisitos.
- Estructura de carpetas del proyecto.
