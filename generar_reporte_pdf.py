#!/usr/bin/env python3
"""
Genera un reporte PDF con los gráficos del Proyecto de Ciencia de Datos:
Mercado de Triciclos Eléctricos de La Habana.

Usa únicamente fpdf (ya instalado). Lee datos/ y resultados/.
Salida: graficos/reporte_graficos.pdf
"""

import csv
import json
import os

from fpdf import FPDF

BASE = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(BASE, "datos")
RESULTADOS = os.path.join(BASE, "resultados")
GRAFICOS = os.path.join(BASE, "graficos")

AZUL = (33, 158, 188)
CIELO = (142, 202, 230)
AMARILLO = (255, 183, 3)
NARANJA = (251, 133, 0)
OSCURO = (2, 48, 71)
GRIS = (107, 114, 128)
GRIS_CLARO = (229, 231, 235)
TEAL = (18, 103, 130)

PALETA = [AZUL, CIELO, AMARILLO, NARANJA, OSCURO, TEAL]
PAGINA_W, PAGINA_H = 210, 297


# --------------------------------------------------------------------------
def cargar_json(ruta, defecto=None):
    if not os.path.exists(ruta):
        return defecto
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def cargar_csv(ruta):
    if not os.path.exists(ruta):
        return []
    with open(ruta, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def fmt(n):
    if isinstance(n, float):
        if abs(n - round(n)) < 0.01:
            return f"{int(round(n)):,}"
        return f"{n:,.1f}"
    return f"{n:,}"


def nice_max(valor):
    import math
    if valor <= 0:
        return 1
    mag = 10 ** int(math.floor(math.log10(valor)))
    for m in (1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10):
        if valor <= m * mag:
            return m * mag
    return 10 * mag


def texto(pdf, x, y, s, size=10, style="", color=OSCURO, align="L"):
    pdf.set_font("Helvetica", style, size)
    pdf.set_text_color(*color)
    s = str(s)
    ancho = pdf.get_string_width(s)
    if align == "C":
        x -= ancho / 2
    elif align == "R":
        x -= ancho
    pdf.text(x, y, s)


def barra_rellena(pdf, x, y, w, h, color):
    pdf.set_fill_color(*color)
    pdf.rect(x, y, w, h, "F")


def linea(pdf, x1, y1, x2, y2, color=GRIS_CLARO, grosor=0.2):
    pdf.set_draw_color(*color)
    pdf.set_line_width(grosor)
    pdf.line(x1, y1, x2, y2)


def dibujar_titulo(pdf, x0, y, w, titulo, subtitulo):
    texto(pdf, x0 + w / 2, y + 6, titulo, 14, "B", OSCURO, "C")
    if subtitulo:
        texto(pdf, x0 + w / 2, y + 12, subtitulo, 9, "", GRIS, "C")


# --------------------------------------------------------------------------
# Barras horizontales
# --------------------------------------------------------------------------
def grafico_barras_h(pdf, x0, y0, w, h, datos, titulo, subtitulo,
                     color=AZUL, unidad=""):
    dibujar_titulo(pdf, x0, y0, w, titulo, subtitulo)
    datos = [(k, v) for k, v in datos if v is not None]
    datos.sort(key=lambda kv: kv[1], reverse=True)
    if not datos:
        return

    izq = x0 + 52
    der = x0 + w - 22
    arriba = y0 + 22
    abajo = y0 + h - 14
    pw = der - izq
    ph = abajo - arriba
    maxv = nice_max(max(v for _, v in datos))

    for i in range(6):
        gx = izq + pw * i / 5
        linea(pdf, gx, arriba, gx, abajo, GRIS_CLARO, 0.15)
        texto(pdf, gx, abajo + 5, fmt(maxv * i / 5), 7, "", GRIS, "C")

    n = len(datos)
    hueco = 2.0
    alto_b = max(4.0, (ph - hueco * (n - 1)) / n)

    for i, (etq, val) in enumerate(datos):
        y = arriba + i * (alto_b + hueco)
        texto(pdf, izq - 2, y + alto_b / 2 + 2, etq, 8.5, "", OSCURO, "R")
        ancho = pw * (val / maxv) if maxv else 0
        barra_rellena(pdf, izq, y, ancho, alto_b, color)
        sufijo = f" {unidad}" if unidad else ""
        texto(pdf, izq + ancho + 2, y + alto_b / 2 + 2,
              fmt(val) + sufijo, 8, "B", OSCURO, "L")

    linea(pdf, izq, arriba, izq, abajo, GRIS, 0.3)
    linea(pdf, izq, abajo, der, abajo, GRIS, 0.3)


# --------------------------------------------------------------------------
# Barras verticales (simples o agrupadas)
# --------------------------------------------------------------------------
def grafico_barras_v(pdf, x0, y0, w, h, categorias, series, titulo,
                     subtitulo, unidad="", color_por_barra=False,
                     rotar=False, sufijo_cat=None):
    dibujar_titulo(pdf, x0, y0, w, titulo, subtitulo)

    izq = x0 + 16
    der = x0 + w - 6
    arriba = y0 + 24
    abajo = y0 + h - 18
    pw = der - izq
    ph = abajo - arriba

    todos = [v for _, _, vals in series for v in vals]
    maxv = nice_max(max(todos) if todos else 1)

    for i in range(6):
        gy = abajo - ph * i / 5
        linea(pdf, izq, gy, der, gy, GRIS_CLARO, 0.15)
        texto(pdf, izq - 2, gy + 1.5, fmt(maxv * i / 5), 7, "", GRIS, "R")

    ncat = len(categorias)
    grupo = pw / ncat
    nser = len(series)
    ancho_b = grupo * 0.68 / nser

    for j, (nombre_serie, color, vals) in enumerate(series):
        for i, val in enumerate(vals):
            cx = izq + grupo * i + grupo / 2
            off = (j - (nser - 1) / 2) * ancho_b
            bx = cx + off - ancho_b / 2
            alto = ph * (val / maxv) if maxv else 0
            by = abajo - alto
            c = PALETA[i % len(PALETA)] if (color_por_barra and nser == 1) else color
            barra_rellena(pdf, bx, by, ancho_b - 0.4, alto, c)
            if alto > 7:
                texto(pdf, bx + (ancho_b - 0.4) / 2, by + 4, fmt(val),
                      7.5, "B", (255, 255, 255), "C")

    # Etiquetas de categorías
    for i, cat in enumerate(categorias):
        etq = sufijo_cat(cat) if sufijo_cat else str(cat)
        cx = izq + grupo * i + grupo / 2
        if rotar:
            with pdf.rotation(35, cx, abajo + 4):
                texto(pdf, cx, abajo + 8, etq, 7, "", OSCURO, "R")
        else:
            texto(pdf, cx, abajo + 8, etq, 7, "", OSCURO, "C")

    linea(pdf, izq, arriba, izq, abajo, GRIS, 0.3)
    linea(pdf, izq, abajo, der, abajo, GRIS, 0.3)

    if nser > 1:
        lx = izq
        ly = abajo + 15
        for nombre_serie, color, _ in series:
            barra_rellena(pdf, lx, ly - 3, 4, 3, color)
            texto(pdf, lx + 5, ly, nombre_serie, 8, "", OSCURO, "L")
            lx += 5 + pdf.get_string_width(nombre_serie) + 10


# --------------------------------------------------------------------------
def main():
    os.makedirs(GRAFICOS, exist_ok=True)

    filas = cargar_csv(os.path.join(DATOS, "datos_consolidados.csv"))
    mercado = cargar_json(os.path.join(DATOS, "mercadodetriciclos.json"), {})
    analisis = cargar_json(os.path.join(RESULTADOS, "analisis_completo.json"), {})

    precios = [float(f["precio"]) for f in filas if f.get("precio")]

    municipios = {}
    for f in filas:
        municipios[f.get("municipio", "Sin dato")] = municipios.get(f.get("municipio", "Sin dato"), 0) + 1

    barreras = analisis.get("legalidad_obstaculos") or {}
    barreras = [(k, v) for k, v in barreras.items()
                if k not in ("-", "", None) and k.lower() != "en regla"]

    categoria = analisis.get("categoria_uso") or {"Carga": 15, "Pasajeros": 5}
    fuentes = analisis.get("fuentes") or {"Web": 12, "Entrevista": 8}

    por_municipio = {}
    for f in filas:
        if f.get("precio"):
            por_municipio.setdefault(f["municipio"], []).append(float(f["precio"]))
    cats_m = sorted(por_municipio.keys())
    mins = [min(por_municipio[c]) for c in cats_m]
    proms = [sum(por_municipio[c]) / len(por_municipio[c]) for c in cats_m]
    maxs = [max(por_municipio[c]) for c in cats_m]

    marcas = {}
    for r in mercado.get("registros", []):
        m = r.get("marca", "Sin dato")
        marcas[m] = marcas.get(m, 0) + 1

    abrev = {
        "10 de Octubre": "10 Octubre",
        "Centro Habana": "C. Habana",
        "Plaza de la Revolución": "Plaza",
        "Habana del Este": "H. Este",
        "La Lisa": "La Lisa",
    }

    # Histograma de precios
    minimo, maximo = min(precios), max(precios)
    tam = 500
    ini = (int(minimo) // tam) * tam
    finb = ((int(maximo) // tam) + 1) * tam
    bordes = list(range(ini, finb + tam, tam))
    conteos = [0] * (len(bordes) - 1)
    for v in precios:
        idx = min(max(int((v - bordes[0]) // tam), 0), len(conteos) - 1)
        conteos[idx] += 1
    etiquetas_precio = [f"{fmt(bordes[i])}-{fmt(bordes[i+1])}"
                        for i in range(len(conteos))]

    # ------------------------------------------------------------------
    pdf = FPDF("P", "mm", "A4")
    pdf.set_auto_page_break(False)
    pdf.set_margins(15, 15, 15)

    # PORTADA / Página 1
    pdf.add_page()
    barra_rellena(pdf, 0, 0, PAGINA_W, 40, OSCURO)
    texto(pdf, PAGINA_W / 2, 18, "Mercado de Triciclos Eléctricos", 20, "B",
          (255, 255, 255), "C")
    texto(pdf, PAGINA_W / 2, 28, "La Habana · Reporte de gráficos",
          12, "", CIELO, "C")
    texto(pdf, PAGINA_W / 2, 35, f"{len(filas)} registros consolidados · precios en USD",
          9, "", GRIS_CLARO, "C")

    grafico_barras_v(
        pdf, 15, 46, 180, 112, etiquetas_precio, [("Frecuencia", AZUL, conteos)],
        "Distribución de precios del mercado",
        "Número de triciclos por rango de precio (USD)",
    )
    grafico_barras_h(
        pdf, 15, 164, 180, 118, list(municipios.items()),
        "Distribución geográfica por municipio",
        "Cantidad de triciclos registrados por municipio",
        color=AZUL, unidad="triciclos",
    )

    # Página 2
    pdf.add_page()
    grafico_barras_v(
        pdf, 15, 15, 180, 112, list(categoria.keys()),
        [("Triciclos", AZUL, list(categoria.values()))],
        "Distribución por categoría de uso",
        "Orientación de los triciclos: carga vs. pasajeros",
        color_por_barra=True,
    )
    grafico_barras_h(
        pdf, 15, 133, 180, 150, barreras,
        "Principales barreras del mercado",
        "Obstáculos legales y operativos mencionados",
        color=NARANJA, unidad="mención",
    )

    # Página 3
    pdf.add_page()
    grafico_barras_v(
        pdf, 15, 15, 180, 112, list(fuentes.keys()),
        [("Registros", TEAL, list(fuentes.values()))],
        "Fuentes de los datos analizados",
        "Origen de los registros del estudio",
        color_por_barra=True,
    )
    grafico_barras_v(
        pdf, 15, 133, 180, 150, cats_m,
        [("Mínimo", AZUL, mins),
         ("Promedio", AMARILLO, proms),
         ("Máximo", NARANJA, maxs)],
        "Precios por municipio (mínimo, promedio, máximo)",
        "Precios en USD de triciclos eléctricos",
        rotar=False,
        sufijo_cat=lambda c: abrev.get(c, c),
    )

    # Página 4
    pdf.add_page()
    grafico_barras_h(
        pdf, 15, 15, 180, 130, list(marcas.items()),
        "Distribución por marca",
        "Frecuencia de marcas en el mercado (fuente web)",
        color=AZUL, unidad="registros",
    )
    # Resumen de hallazgos
    pdf.set_fill_color(246, 248, 250)
    pdf.rect(15, 158, 180, 118, "F")
    texto(pdf, 22, 170, "Hallazgos principales", 14, "B", OSCURO, "L")
    hallazgos = [
        f"Precio mínimo: {fmt(min(precios))} USD · Precio máximo: {fmt(max(precios))} USD",
        f"Precio promedio: {fmt(sum(precios)/len(precios))} USD",
        f"Municipio con más registros: {max(municipios, key=municipios.get)} "
        f"({max(municipios.values())} registros)",
        f"Categoría de uso dominante: "
        f"{max(categoria, key=categoria.get)} "
        f"({max(categoria.values())} de {sum(categoria.values())})",
        f"Fuente principal: {max(fuentes, key=fuentes.get)} "
        f"({max(fuentes.values())} registros)",
        f"Marca más frecuente: {max(marcas, key=marcas.get)} "
        f"({max(marcas.values())} registros)",
    ]
    y = 184
    for h in hallazgos:
        texto(pdf, 24, y, "-", 11, "B", NARANJA, "L")
        texto(pdf, 30, y, h, 10.5, "", OSCURO, "L")
        y += 10

    salida = os.path.join(GRAFICOS, "reporte_graficos.pdf")
    pdf.output(salida)
    print("PDF generado:", salida)


if __name__ == "__main__":
    main()
