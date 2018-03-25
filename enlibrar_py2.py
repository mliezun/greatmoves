import PyPDF2
import sys

# Ancho y largo de una hoja A4
(w, h) = (595.276, 841.89)

# Escalado para generar 2 pag/hoja
sx = h / 2
sy = w

# Traslacion para mover la hoja a la derecha
tx = h / 2
ty = 0

import time


def create_section(pdfWriter, pages, start, end):
    for p11, p21, p12, p22 in [(pages[start + i], pages[start + i + 1], pages[end - i - 1], pages[end - i - 2]) for i in
                               range(0, (end - start) // 2, 2)]:
        # Redimensiono las paginas y las copio sobre una hoja horizontal en blanco
        p11.scaleTo(sx, sy)
        p12.scaleTo(sx, sy)
        out = pdfWriter.addBlankPage(h, w)
        out.mergeTranslatedPage(p11, tx, ty)  # A la derecha
        out.mergePage(p12)

        p21.scaleTo(sx, sy)
        p22.scaleTo(sx, sy)
        out = pdfWriter.addBlankPage(h, w)
        out.mergeTranslatedPage(p22, tx, ty)  # A la derecha
        out.mergePage(p21)


def get_formatted_book(pdfReader):
    pdfWriter = PyPDF2.PdfFileWriter()

    # Defino el tamano de la seccion al valor por defecto
    section = 32

    # Si la cantidad de paginas es impar agrego una en blanco al final
    pages = [pdfReader.getPage(i) for i in range(pdfReader.numPages)]

    # Agrego las paginas suficientes para que sean divisibles por 4 (sirve para el create_section)
    while len(pages) % 4 != 0: pages.append(PyPDF2.pdf.PageObject.createBlankPage(width=w, height=h))

    # Si la cantidad de paginas es menor que la de la seccion, seccion = cant pag
    if section > len(pages): section = len(pages)

    # Divido el libro en secciones
    for i in range(len(pages) // section):
        create_section(pdfWriter, pages, i * section, (i + 1) * section)

    if len(pages) % section != 0:
        create_section(pdfWriter, pages[-(len(pages) % section):], 0, len(pages) % section)

    return pdfWriter


def book(book):
    # Abro el archivo del libro y creo un lector de PDF
    in_file = open(book, 'rb')
    pdfReader = PyPDF2.PdfFileReader(in_file)

    pdfWriter = get_formatted_book(pdfReader)

    out_file = open(book.replace('.pdf', '') + "_formatted.pdf", 'wb')
    pdfWriter.write(out_file)
    out_file.close()
