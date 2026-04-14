from __future__ import annotations

import os
import tempfile
from datetime import datetime

import pandas as pd
from fpdf import FPDF


def _safe_text(value: object) -> str:
    """FPDF core fonts use latin-1; replace unsupported chars safely."""
    text = str(value)
    return text.encode("latin-1", "replace").decode("latin-1")


def _trim_text(value: object, max_len: int = 28) -> str:
    txt = _safe_text(value)
    return txt if len(txt) <= max_len else f"{txt[: max_len - 3]}..."


def _effective_width(pdf: FPDF) -> float:
    return max(20.0, pdf.w - pdf.l_margin - pdf.r_margin)


def _write_line(pdf: FPDF, text: str, h: float = 5.0) -> None:
    pdf.set_x(pdf.l_margin)
    pdf.cell(_effective_width(pdf), h, _trim_text(text, 180), ln=True)


def _write_multiline(pdf: FPDF, text: str, h: float = 5.0) -> None:
    # Limita tokens enormes que rompen el line-break de FPDF.
    safe = " ".join(_safe_text(text).replace("\n", " ").split())
    words = []
    for token in safe.split(" "):
        if len(token) > 45:
            words.extend([token[i : i + 45] for i in range(0, len(token), 45)])
        else:
            words.append(token)
    safe = " ".join(words)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(_effective_width(pdf), h, safe)
    pdf.set_x(pdf.l_margin)


def build_report_pdf(
    *,
    title: str,
    subtitle: str = "",
    bullet_points: list[str] | None = None,
    table_df: pd.DataFrame | None = None,
    table_title: str = "Resumen",
    max_rows: int = 35,
    max_cols: int = 8,
    image_bytes: bytes | None = None,
) -> bytes:
    """Build a compact one-page PDF report for module exports."""
    pdf = FPDF(unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    temp_img_path: str | None = None

    try:
        pdf.set_font("Helvetica", "B", 15)
        _write_line(pdf, _safe_text(title), 8)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(100, 100, 100)
        _write_line(pdf, _safe_text(datetime.now().strftime("%d/%m/%Y")), 6)
        pdf.set_text_color(0, 0, 0)

        if subtitle:
            pdf.ln(1)
            _write_multiline(pdf, subtitle, 5)

        if bullet_points:
            pdf.ln(1)
            for item in bullet_points:
                _write_line(pdf, f"- {_safe_text(item)}", 5)

        if image_bytes:
            try:
                tf = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                tf.write(image_bytes)
                tf.flush()
                tf.close()
                temp_img_path = tf.name
                pdf.ln(2)
                pdf.set_x(pdf.l_margin)
                pdf.image(temp_img_path, w=_effective_width(pdf))
            except Exception:
                temp_img_path = None

        if table_df is not None and not table_df.empty:
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 11)
            _write_line(pdf, _safe_text(table_title), 6)

            tbl = table_df.copy()
            if len(tbl) > max_rows:
                tbl = tbl.head(max_rows)
            if tbl.shape[1] > max_cols:
                tbl = tbl.iloc[:, :max_cols]

            cols = [str(c) for c in tbl.columns]
            ncols = max(1, len(cols))
            col_w = _effective_width(pdf) / ncols
            hdr_font = 8 if ncols <= 8 else 7
            row_font = 7 if ncols <= 8 else 6
            hdr_trim = 20 if ncols <= 8 else 14
            row_trim = 20 if ncols <= 8 else 14
            row_h = 5 if ncols <= 8 else 4.5

            pdf.set_font("Helvetica", "B", hdr_font)
            pdf.set_fill_color(235, 235, 235)
            pdf.set_x(pdf.l_margin)
            for col in cols:
                pdf.cell(col_w, 6, _trim_text(col, hdr_trim), border=1, fill=True)
            pdf.ln()

            pdf.set_font("Helvetica", "", row_font)
            for _, row in tbl.iterrows():
                pdf.set_x(pdf.l_margin)
                for col in cols:
                    pdf.cell(col_w, row_h, _trim_text(row[col], row_trim), border=1)
                pdf.ln()

            if len(table_df) > len(tbl):
                pdf.ln(1)
                pdf.set_font("Helvetica", "I", 8)
                _write_line(pdf, f"* Se muestran {len(tbl)} de {len(table_df)} filas.", 4)

        raw = pdf.output(dest="S")
        if isinstance(raw, (bytes, bytearray)):
            return bytes(raw)
        return raw.encode("latin-1")
    except Exception as e:
        # Fallback para que nunca rompa la pagina de Streamlit.
        safe = FPDF(unit="mm", format="A4")
        safe.set_auto_page_break(auto=True, margin=12)
        safe.add_page()
        safe.set_font("Helvetica", "B", 13)
        safe.cell(0, 8, _safe_text(title), ln=True)
        safe.set_font("Helvetica", "", 10)
        safe.multi_cell(_effective_width(safe), 6, _safe_text("No se pudo renderizar el informe completo."))
        safe.multi_cell(_effective_width(safe), 6, _safe_text(f"Detalle tecnico: {e}"))
        raw = safe.output(dest="S")
        if isinstance(raw, (bytes, bytearray)):
            return bytes(raw)
        return raw.encode("latin-1")
    finally:
        if temp_img_path:
            try:
                os.unlink(temp_img_path)
            except Exception:
                pass

