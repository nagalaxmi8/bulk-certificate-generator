
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


OUTPUT_DIR = Path("storage/certificates")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def generate_certificate(name: str, event_name: str, certificate_id: int) -> str:
    file_path = OUTPUT_DIR / f"certificate_{certificate_id}.pdf"

    pdf = canvas.Canvas(str(file_path), pagesize=A4)
    width, height = A4

    pdf.setTitle("Certificate of Participation")

    # Certificate border
    pdf.setLineWidth(3)
    pdf.rect(40, 40, width - 80, height - 80)

    # Certificate text
    pdf.setFont("Helvetica-Bold", 26)
    pdf.drawCentredString(width / 2, height - 150, "CERTIFICATE")

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(width / 2, height - 185, "OF PARTICIPATION")

    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(
        width / 2, height - 250, "This certificate is proudly presented to"
    )

    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawCentredString(width / 2, height - 300, name)

    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(
        width / 2, height - 350, f"For participating in {event_name}"
    )

    pdf.setFont("Helvetica", 10)
    pdf.drawCentredString(
        width / 2, 80, f"Certificate ID: {certificate_id}"
    )

    pdf.save()
    return str(file_path)
