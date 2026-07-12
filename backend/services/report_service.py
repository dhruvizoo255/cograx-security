"""PDF report generation service — bundles a prediction result, SHAP
explanation, security checklist, and blockchain evidence into a shareable
PDF, using reportlab (no external system dependencies)."""

from __future__ import annotations

from io import BytesIO

from backend.api.schemas.response_schemas import PredictionResponse


def generate_pdf_report(prediction: PredictionResponse) -> bytes:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, title="Cograx Security Report")
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Cograx Security — Risk Assessment Report", styles["Title"]))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(f"Token: {prediction.token_address}", styles["Normal"]))
    story.append(Paragraph(f"Generated: {prediction.timestamp}", styles["Normal"]))
    story.append(Spacer(1, 0.2 * inch))

    story.append(
        Paragraph(f"Risk Level: {prediction.risk_level.value}", styles["Heading2"])
    )
    story.append(
        Paragraph(
            f"Risk Score: {prediction.risk_score}/100 &nbsp;&nbsp; "
            f"Confidence: {prediction.confidence * 100:.1f}%",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph(prediction.natural_language_explanation, styles["BodyText"]))
    story.append(Spacer(1, 0.25 * inch))

    story.append(Paragraph("Top Risk-Increasing Factors", styles["Heading3"]))
    pos_rows = [["Feature", "Value", "SHAP Contribution"]] + [
        [c.feature, f"{c.value:.2f}", f"{c.shap_value:+.4f}"]
        for c in prediction.top_positive_factors
    ]
    story.append(_make_table(pos_rows))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("Top Risk-Reducing Factors", styles["Heading3"]))
    neg_rows = [["Feature", "Value", "SHAP Contribution"]] + [
        [c.feature, f"{c.value:.2f}", f"{c.shap_value:+.4f}"]
        for c in prediction.top_negative_factors
    ]
    story.append(_make_table(neg_rows))
    story.append(Spacer(1, 0.25 * inch))

    story.append(Paragraph("Security Checklist", styles["Heading3"]))
    check_rows = [["Check", "Passed", "Severity", "Detail"]] + [
        [c.name, "Yes" if c.passed else "No", c.severity, c.detail]
        for c in prediction.security_checklist
    ]
    story.append(_make_table(check_rows))
    story.append(Spacer(1, 0.25 * inch))

    if prediction.recommendations:
        story.append(Paragraph("Recommendations", styles["Heading3"]))
        for rec in prediction.recommendations:
            story.append(Paragraph(f"• {rec}", styles["Normal"]))
        story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("Blockchain Audit", styles["Heading3"]))
    bc = prediction.blockchain_status
    bc_text = (
        f"Stored on-chain: {bc.stored}. Tx hash: {bc.tx_hash or 'N/A'}. "
        f"Block: {bc.block_number or 'N/A'}."
        if bc.stored
        else f"Not stored on-chain ({bc.error or 'not requested'})."
    )
    story.append(Paragraph(bc_text, styles["Normal"]))
    story.append(Spacer(1, 0.15 * inch))
    story.append(
        Paragraph(f"Prediction Hash: {prediction.prediction_hash}", styles["Code"])
    )
    story.append(
        Paragraph(f"Model Version: {prediction.model_version}", styles["Normal"])
    )

    doc.build(story)
    return buffer.getvalue()


def _make_table(rows: list[list[str]]):
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle

    table = Table(rows, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#f3f4f6")],
                ),
            ]
        )
    )
    return table
