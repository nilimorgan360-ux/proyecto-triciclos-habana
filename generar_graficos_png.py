#!/usr/bin/env python3
"""
Genera gráficos PNG del Proyecto de Ciencia de Datos:
Mercado de Triciclos Eléctricos de La Habana.

Requiere Pillow. Lee datos/ y resultados/ y escribe en graficos/.
"""

import csv
import json
import math
import os

from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(BASE, "datos")
RESULTADOS = os.path.join(BASE, "resultados")
GRAFICOS = os.path.join(BASE, "graficos")

W, H = 1200, 760
S = 2  # supersampling para bordes suaves

AZUL = (33, 158, 188)
CIELO = (142, 202, 230)
AMARILLO = (255, 183, 3)
NARANJA = (251, 133, 0)
OSCURO = (2, 48, 71)
GRIS = (107, 114, 128)
GRIS_CLARO = (229, 231, 235)
TEAL = (18, 103, 130)
FONDO = (255, 255, 255)

PALETA = [AZUL, CIELO, AMARILLO, NARANJA, OSCURO, TEAL]
FONT_DIR = "/usr/share/fonts/truetype/dejavu"
FONT_REG = os.path.join(FONT_DIR, "DejaVuSans.ttf")
FONT_BOLD = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")


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


def eje_enteros(maxv, objetivo=5):
    """Devuelve (tope, ticks) con marcas enteras legibles para conteos."""
    maxv = max(1, int(math.ceil(maxv)))
    if maxv <= objetivo:
        return maxv, list(range(maxv + 1))
    paso = math.ceil(maxv / objetivo)
    tope = paso * math.ceil(maxv / paso)
    return tope, list(range(0, tope + 1, paso))


def nice_max(valor):
    if valor <= 0:
        return 1
    mag = 10 ** int(math.floor(math.log10(valor)))
    for m in (1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10):
        if valor <= m * mag:
            return m * mag
    return 10 * mag


class Lienzo:
    def __init__(self):
        self.img = Image.new("RGB", (W * S, H * S), FONDO)
        self.d = ImageDraw.Draw(self.img)

    def fuente(self, size, bold=False):
        return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, int(size * S))

    def texto(self, x, y, s, size=16, bold=False, color=OSCURO, anchor="la"):
        self.d.text((x * S, y * S), str(s), font=self.fuente(size, bold),
                    fill=color, anchor=anchor)

    def rect(self, x, y, w, h, color, r=0):
        box = [x * S, y * S, (x + w) * S, (y + h) * S]
        if r:
            self.d.rounded_rectangle(box, radius=r * S, fill=color)
        else:
            self.d.rectangle(box, fill=color)

    def linea(self, x1, y1, x2, y2, color=GRIS_CLARO, grosor=1):
        self.d.line([(x1 * S, y1 * S), (x2 * S, y2 * S)], fill=color,
                    width=max(1, int(grosor * S)))

    def linea_discontinua(self, x1, y1, x2, y2, color, grosor=2, dash=10, gap=7):
        longitud = math.hypot(x2 - x1, y2 - y1)
        if longitud == 0:
            return
        ux, uy = (x2 - x1) / longitud, (y2 - y1) / longitud
        pos = 0
        while pos < longitud:
            fin = min(pos + dash, longitud)
            self.d.line([((x1 + ux * pos) * S, (y1 + uy * pos) * S),
                         ((x1 + ux * fin) * S, (y1 + uy * fin) * S)],
                        fill=color, width=max(1, int(grosor * S)))
            pos += dash + gap

    def dona(self, cx, cy, r_ext, r_int, valores, colores):
        total = sum(valores)
        inicio = -90
        for val, color in zip(valores, colores):
            fin = inicio + 360 * val / total
            self.d.pieslice([cx * S - r_ext * S, cy * S - r_ext * S,
                             cx * S + r_ext * S, cy * S + r_ext * S],
                            inicio, fin, fill=color, outline=FONDO, width=3 * S)
            inicio = fin
        self.d.ellipse([cx * S - r_int * S, cy * S - r_int * S,
                        cx * S + r_int * S, cy * S + r_int * S], fill=FONDO)

    def guardar(self, nombre):
        ruta = os.path.join(GRAFICOS, nombre)
        final = self.img.resize((W, H), Image.LANCZOS)
        final.save(ruta, "PNG")
        print(f"  guardado: graficos/{nombre}")


def cabecera(c, titulo, subtitulo):
    c.texto(W / 2, 44, titulo, 30, True, OSCURO, "mm")
    c.texto(W / 2, 78, subtitulo, 17, False, GRIS, "mm")


# --------------------------------------------------------------------------
def barras_horizontales(nombre, datos, titulo, subtitulo, color=AZUL,
                        unidad=""):
    datos = [(k, v) for k, v in datos if v is not None]
    datos.sort(key=lambda kv: kv[1], reverse=True)
    if not datos:
        return
    c = Lienzo()
    cabecera(c, titulo, subtitulo)

    izq, der = 300, 1060
    arriba, abajo = 130, 690
    pw, ph = der - izq, abajo - arriba
    maxv, ticks = eje_enteros(max(v for _, v in datos))

    for tv in ticks:
        x = izq + pw * tv / maxv
        c.linea(x, arriba, x, abajo, GRIS_CLARO, 1)
        c.texto(x, abajo + 18, str(tv), 14, False, GRIS, "mt")

    n = len(datos)
    hueco = 10
    alto_b = max(22, (ph - hueco * (n - 1)) / n)

    for i, (etq, val) in enumerate(datos):
        y = arriba + i * (alto_b + hueco)
        if i % 2 == 0:
            c.rect(izq, y - hueco / 2, pw, alto_b + hueco, (249, 250, 251))
        c.texto(izq - 16, y + alto_b / 2, etq, 17, False, OSCURO, "rm")
        ancho = pw * (val / maxv) if maxv else 0
        c.rect(izq, y, ancho, alto_b, color, r=4)
        u = unidad
        if val == 1 and u.endswith("s"):
            u = u[:-1]
        suf = f" {u}" if u else ""
        c.texto(izq + ancho + 12, y + alto_b / 2, fmt(val) + suf, 16, True,
                OSCURO, "lm")

    c.linea(izq, arriba, izq, abajo, GRIS, 2)
    c.linea(izq, abajo, der, abajo, GRIS, 2)
    c.texto(W / 2, H - 18, "Mercado de triciclos eléctricos · La Habana",
            12, False, GRIS, "mm")
    c.guardar(nombre)


# --------------------------------------------------------------------------
def barras_verticales(nombre, categorias, series, titulo, subtitulo,
                      color_por_barra=False, sufijo_cat=None):
    c = Lienzo()
    cabecera(c, titulo, subtitulo)

    izq, der = 110, 1160
    arriba, abajo = 150, 610
    pw, ph = der - izq, abajo - arriba

    todos = [v for _, _, vals in series for v in vals]
    maxv = nice_max(max(todos) if todos else 1)

    for i in range(6):
        y = abajo - ph * i / 5
        c.linea(izq, y, der, y, GRIS_CLARO, 1)
        c.texto(izq - 14, y, fmt(maxv * i / 5), 14, False, GRIS, "rm")

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
            col = PALETA[i % len(PALETA)] if (color_por_barra and nser == 1) else color
            c.rect(bx, by, ancho_b - 4, alto, col, r=4)
            if alto > 28:
                c.texto(bx + (ancho_b - 4) / 2, by + 14, fmt(val), 15, True,
                        FONDO, "mm")

    for i, cat in enumerate(categorias):
        etq = sufijo_cat(cat) if sufijo_cat else str(cat)
        cx = izq + grupo * i + grupo / 2
        c.texto(cx, abajo + 22, etq, 14, False, OSCURO, "mt")

    c.linea(izq, arriba, izq, abajo, GRIS, 2)
    c.linea(izq, abajo, der, abajo, GRIS, 2)

    if nser > 1:
        lx = izq
        ly = abajo + 58
        for nombre_serie, color, _ in series:
            c.rect(lx, ly - 10, 18, 18, color, r=3)
            c.texto(lx + 26, ly, nombre_serie, 15, False, OSCURO, "lm")
            lx += 26 + len(nombre_serie) * 9 + 34

    c.texto(W / 2, H - 18, "Mercado de triciclos eléctricos · La Habana",
            12, False, GRIS, "mm")
    c.guardar(nombre)


# --------------------------------------------------------------------------
def grafico_rango(nombre, datos, titulo, subtitulo, unidad="USD"):
    """datos: lista de (etiqueta, minimo, promedio, maximo)."""
    datos = sorted(datos, key=lambda t: t[2])
    c = Lienzo()
    cabecera(c, titulo, subtitulo)

    izq, der = 250, 1080
    arriba, abajo = 140, 650
    pw, ph = der - izq, abajo - arriba

    dmin = math.floor(min(t[1] for t in datos) / 500) * 500
    dmax = math.ceil(max(t[3] for t in datos) / 500) * 500
    if dmax == dmin:
        dmax += 500

    def X(v):
        return izq + pw * (v - dmin) / (dmax - dmin)

    ticks = int((dmax - dmin) / 500)
    for i in range(ticks + 1):
        v = dmin + i * 500
        x = X(v)
        c.linea(x, arriba, x, abajo, GRIS_CLARO, 1)
        c.texto(x, abajo + 18, fmt(v), 14, False, GRIS, "mt")

    n = len(datos)
    hueco = 16
    alto_fila = (ph - hueco * (n - 1)) / n

    for i, (etq, minimo, prom, maximo) in enumerate(datos):
        yc = arriba + i * (alto_fila + hueco) + alto_fila / 2
        if i % 2 == 0:
            c.rect(izq, yc - alto_fila / 2, pw, alto_fila, (249, 250, 251))
        c.texto(izq - 18, yc, etq, 17, False, OSCURO, "rm")

        # Barra del promedio
        c.rect(izq, yc - 13, X(prom) - izq, 26, CIELO, r=5)
        # Rango mínimo-máximo
        c.linea(X(minimo), yc, X(maximo), yc, NARANJA, 3)
        c.linea(X(minimo), yc - 10, X(minimo), yc + 10, NARANJA, 3)
        c.linea(X(maximo), yc - 10, X(maximo), yc + 10, NARANJA, 3)
        # Punto del promedio
        r = 7
        c.d.ellipse([(X(prom) - r) * S, (yc - r) * S,
                     (X(prom) + r) * S, (yc + r) * S], fill=OSCURO)
        c.texto(X(maximo) + 14, yc, f"{fmt(prom)} {unidad}", 15, True,
                OSCURO, "lm")

    c.linea(izq, arriba, izq, abajo, GRIS, 2)
    c.linea(izq, abajo, der + 20, abajo, GRIS, 2)

    # Leyenda
    lx, ly = izq, abajo + 55
    c.linea(lx, ly, lx + 28, ly, NARANJA, 3)
    c.linea(lx, ly - 7, lx, ly + 7, NARANJA, 3)
    c.linea(lx + 28, ly - 7, lx + 28, ly + 7, NARANJA, 3)
    c.texto(lx + 38, ly, "Rango (mínimo-máximo)", 14, False, OSCURO, "lm")

    lx2 = lx + 260
    c.d.ellipse([(lx2 - 7) * S, (ly - 7) * S, (lx2 + 7) * S, (ly + 7) * S],
                fill=OSCURO)
    c.texto(lx2 + 16, ly, "Promedio", 14, False, OSCURO, "lm")

    c.texto(W / 2, H - 18, "Mercado de triciclos eléctricos · La Habana",
            12, False, GRIS, "mm")
    c.guardar(nombre)


# --------------------------------------------------------------------------
def histograma(nombre, valores, titulo, subtitulo, tam_bin=500, color=AZUL):
    minimo, maximo = min(valores), max(valores)
    ini = (int(minimo) // tam_bin) * tam_bin
    finb = ((int(maximo) // tam_bin) + 1) * tam_bin
    bordes = list(range(ini, finb + tam_bin, tam_bin))
    conteos = [0] * (len(bordes) - 1)
    for v in valores:
        idx = min(max(int((v - bordes[0]) // tam_bin), 0), len(conteos) - 1)
        conteos[idx] += 1
    etiquetas = [f"{fmt(bordes[i])}-{fmt(bordes[i+1])}"
                 for i in range(len(conteos))]

    c = Lienzo()
    cabecera(c, titulo, subtitulo)

    izq, der = 110, 1160
    arriba, abajo = 160, 620
    pw, ph = der - izq, abajo - arriba
    maxc, ticks = eje_enteros(max(conteos))
    n = len(conteos)
    ancho_b = pw / n

    for tv in ticks:
        y = abajo - ph * tv / maxc
        c.linea(izq, y, der, y, GRIS_CLARO, 1)
        c.texto(izq - 14, y, str(tv), 14, False, GRIS, "rm")

    for i, cnt in enumerate(conteos):
        x = izq + i * ancho_b + ancho_b * 0.12
        alto = ph * (cnt / maxc) if maxc else 0
        y = abajo - alto
        c.rect(x, y, ancho_b * 0.76, alto, color, r=4)
        if cnt:
            c.texto(x + ancho_b * 0.38, y - 12, cnt, 16, True, OSCURO, "mb")
        c.texto(izq + i * ancho_b + ancho_b / 2, abajo + 24, etiquetas[i],
                13, False, OSCURO, "mt")

    promedio = sum(valores) / len(valores)
    xp = izq + pw * (promedio - bordes[0]) / (bordes[-1] - bordes[0])
    c.linea_discontinua(xp, arriba, xp, abajo, NARANJA, 2)
    c.texto(xp, arriba - 16, f"Promedio: {fmt(promedio)} USD", 15, True,
            NARANJA, "mb")

    c.linea(izq, arriba, izq, abajo, GRIS, 2)
    c.linea(izq, abajo, der, abajo, GRIS, 2)
    c.texto((izq + der) / 2, H - 70, "Rango de precio (USD)", 15, False, GRIS, "mm")
    c.texto(W / 2, H - 18, "Mercado de triciclos eléctricos · La Habana",
            12, False, GRIS, "mm")
    c.guardar(nombre)


# --------------------------------------------------------------------------
def dona(nombre, etiquetas, valores, titulo, subtitulo, colores, unidad=""):
    c = Lienzo()
    cabecera(c, titulo, subtitulo)
    total = sum(valores)
    cx, cy = 420, 400
    r_ext, r_int = 210, 120
    rmid = (r_ext + r_int) / 2

    c.dona(cx, cy, r_ext, r_int, valores, colores)

    inicio = -90
    for etq, val, color in zip(etiquetas, valores, colores):
        fin = inicio + 360 * val / total
        medio = math.radians((inicio + fin) / 2)
        px = cx + rmid * math.cos(medio)
        py = cy + rmid * math.sin(medio)
        if 100 * val / total > 6:
            c.texto(px, py, f"{100 * val / total:.1f}%", 20, True, FONDO, "mm")
        inicio = fin

    c.texto(cx, cy - 12, fmt(total), 48, True, OSCURO, "mm")
    c.texto(cx, cy + 30, "registros", 18, False, GRIS, "mm")

    lx, ly = 720, 320
    for i, (etq, val, color) in enumerate(zip(etiquetas, valores, colores)):
        y = ly + i * 74
        c.rect(lx, y - 13, 26, 26, color, r=5)
        c.texto(lx + 40, y, etq, 21, False, OSCURO, "lm")
        c.texto(lx + 40, y + 28, f"{fmt(val)}{(' ' + unidad) if unidad else ''} "
                f"({100 * val / total:.1f}%)", 15, False, GRIS, "lm")

    c.texto(W / 2, H - 18, "Mercado de triciclos eléctricos · La Habana",
            12, False, GRIS, "mm")
    c.guardar(nombre)


# --------------------------------------------------------------------------
def main():
    os.makedirs(GRAFICOS, exist_ok=True)
    filas = cargar_csv(os.path.join(DATOS, "datos_consolidados.csv"))
    mercado = cargar_json(os.path.join(DATOS, "mercadodetriciclos.json"), {})
    analisis = cargar_json(os.path.join(RESULTADOS, "analisis_completo.json"), {})

    precios = [float(f["precio"]) for f in filas if f.get("precio")]

    municipios = {}
    for f in filas:
        m = f.get("municipio", "Sin dato")
        municipios[m] = municipios.get(m, 0) + 1

    categoria = analisis.get("categoria_uso") or {"Carga": 15, "Pasajeros": 5}
    fuentes = analisis.get("fuentes") or {"Web": 12, "Entrevista": 8}
    barreras = analisis.get("legalidad_obstaculos") or {}
    barreras = [(k, v) for k, v in barreras.items()
                if k not in ("-", "", None) and k.lower() != "en regla"]

    marcas = {}
    for r in mercado.get("registros", []):
        m = r.get("marca", "Sin dato")
        marcas[m] = marcas.get(m, 0) + 1

    por_municipio = {}
    for f in filas:
        if f.get("precio"):
            por_municipio.setdefault(f["municipio"], []).append(float(f["precio"]))
    cats_m = sorted(por_municipio.keys())
    mins = [min(por_municipio[k]) for k in cats_m]
    proms = [sum(por_municipio[k]) / len(por_municipio[k]) for k in cats_m]
    maxs = [max(por_municipio[k]) for k in cats_m]

    abrev = {
        "10 de Octubre": "10 Octubre",
        "Centro Habana": "C. Habana",
        "Plaza de la Revolución": "Plaza",
        "Habana del Este": "H. Este",
    }

    histograma("grafico_precios.png", precios,
               "Distribución de precios del mercado",
               "Triciclos eléctricos en La Habana · datos consolidados")

    barras_horizontales("grafico_municipios.png", list(municipios.items()),
                        "Distribución geográfica por municipio",
                        "Cantidad de triciclos registrados por municipio",
                        AZUL, "triciclos")

    dona("grafico_uso.png", list(categoria.keys()), list(categoria.values()),
         "Distribución por categoría de uso",
         "Orientación de los triciclos: carga vs. pasajeros",
         [AZUL, AMARILLO])

    barras_horizontales("grafico_barreras.png", barreras,
                        "Principales barreras del mercado",
                        "Obstáculos legales y operativos mencionados",
                        NARANJA, "mención")

    dona("grafico_fuentes.png", list(fuentes.keys()), list(fuentes.values()),
         "Fuentes de los datos analizados",
         "Origen de los registros del estudio",
         [AZUL, AMARILLO])

    grafico_rango("grafico_precios_municipio.png",
                  [(abrev.get(k, k), mins[i], proms[i], maxs[i])
                   for i, k in enumerate(cats_m)],
                  "Precios por municipio (rango y promedio)",
                  "Precio mínimo, promedio y máximo en USD")

    barras_horizontales("grafico_marcas.png", list(marcas.items()),
                        "Distribución por marca",
                        "Frecuencia de marcas en el mercado (fuente web)",
                        AZUL, "registros")

    print("Listo. PNG en:", GRAFICOS)


if __name__ == "__main__":
    main()
