from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from textwrap import wrap

def generate_pdf(text, output_path):
    c = canvas.Canvas(output_path, pagesize=A4)
    c.setFont("Helvetica", 10)

    width, height = A4
    x_margin = 40
    y_start = height - 50
    line_height = 14
    max_chars_per_line = 110  # increased for better alignment

    y = y_start
    lines = text.split('\n')

    for line in lines:
        wrapped = wrap(line, width=max_chars_per_line)
        for wrap_line in wrapped:
            if y < 50:
                c.showPage()
                c.setFont("Helvetica", 10)
                y = y_start
            c.drawString(x_margin, y, wrap_line)
            y -= line_height

    c.save()
