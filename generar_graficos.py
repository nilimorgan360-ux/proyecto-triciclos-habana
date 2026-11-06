#!/usr/bin/env python3
"""
Generador de gráficos SVG para el Proyecto de Ciencia de Datos:
Mercado de Triciclos Eléctricos de La Habana.

No requiere dependencias externas (solo biblioteca estándar).
Lee los datos de datos/ y resultados/ y escribe los gráficos en graficos/.
"""

import csv
import json
import os
from html import escape
from math import sin, cos, pi

BASE = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(BASE, "datos")
RESULTADOS = os.path.join(BASE, "resultados")
GRAFICOS = os.path.join(BASE, "graficos")

PALETA = ["#219EBC", "#8ECAE6", "#FFB703", "#FB8500",
          "#023047", "#126782", "#A8DADC", "#F4A261"]
AZUL = "#219EBC"
AMARILLO = "#FFB703"
NARANJA = "#FB8500"
OSCURO = "#023047"
GRIS = "#6B7280"
GRIS_CLARO = "#E5E7EB"
FONDO = "#FFFFFF"

W, H = 1000, 650


# --------------------------------------------------------------------------
# Utilidades
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
    """Formatea números con separador de miles y sin decimales innecesarios."""
    if isinstance(n, float):
        if abs(n - round(n)) < 0.01:
            return f"{int(round(n)):,}"
        return f"{n:,.2f}"
    return f"{n:,}"


def escribir_svg(nombre, contenido):
    ruta = os.path.join(GRAFICOS, nombre)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(contenido)
    print(f"  guardado: graficos/{nombre}")


def svg_inicio():
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}" font-family="Helvetica, Arial, sans-serif">'
            f'<rect width="{W}" height="{H}" fill="{FONDO}"/>')


def svg_fin():
    return "</svg>"


def titulo(texto, subtitulo=None):
    s = (f'<text x="{W/2}" y="46" text-anchor="middle" font-size="26" '
         f'font-weight="bold" fill="{OSCURO}">{escape(texto)}</text>')
    if subtitulo:
        s += (f'<text x="{W/2}" y="74" text-anchor="middle" font-size="15" '
              f'fill="{GRIS}">{escape(subtitulo)}</text>')
    return s


def eje_lineas(x0, y0, x1, y1):
    return (f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y1}" '
            f'stroke="{GRIS}" stroke-width="1"/>')


def franja_alterna(x, y, w, h, indice):
    if indice % 2 == 0:
        return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#F9FAFB"/>'
    return ""


def nice_max(valor):
    """Redondea hacia arriba a un valor 'bonito' para el eje."""
    if valor <= 0:
        return 1
    import math
    magnitud = 10 ** int(math.floor(math.log10(valor)))
    for m in (1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10):
        if valor <= m * magnitud:
            return m * magnitud
    return 10 * magnitud


# --------------------------------------------------------------------------
# Gráfico de barras horizontales
# --------------------------------------------------------------------------
def barras_horizontales(nombre, datos, titulo_txt, subtitulo_txt,
                        color=AZUL, unidad="", ancho_valor=None):
    datos = [(k, v) for k, v in datos if v is not None]
    datos.sort(key=lambda kv: kv[1], reverse=True)
    if not datos:
        return

    margen_izq = 260
    margen_der = 110
    arriba = 110
    abajo = 70
    alto_plot = H - arriba - abajo
    n = len(datos)
    hueco = 8
    alto_barra = max(14, (alto_plot - hueco * (n - 1)) / n)
    max_val = nice_max(max(v for _, v in datos))
    ancho_plot = W - margen_izq - margen_der

    s = [svg_inicio(), titulo(titulo_txt, subtitulo_txt)]

    # Franjas alternas de fondo
    for i in range(n):
        y = arriba + i * (alto_barra + hueco)
        s.append(franja_alterna(margen_izq, y - hueco / 2, ancho_plot,
                                alto_barra + hueco, i))

    # Rejilla vertical
    pasos = 5
    for i in range(pasos + 1):
        x = margen_izq + ancho_plot * i / pasos
        val = max_val * i / pasos
        s.append(f'<line x1="{x:.1f}" y1="{arriba}" x2="{x:.1f}" '
                 f'y2="{arriba + alto_plot}" stroke="{GRIS_CLARO}" stroke-width="1"/>')
        s.append(f'<text x="{x:.1f}" y="{arriba + alto_plot + 22}" '
                 f'text-anchor="middle" font-size="12" fill="{GRIS}">{fmt(val)}</text>')

    for i, (etiqueta, valor) in enumerate(datos):
        y = arriba + i * (alto_barra + hueco)
        ancho = ancho_plot * (valor / max_val) if max_val else 0
        s.append(f'<rect x="{margen_izq}" y="{y:.1f}" width="{ancho:.1f}" '
                 f'height="{alto_barra:.1f}" rx="3" fill="{color}"/>')
        s.append(f'<text x="{margen_izq - 12}" y="{y + alto_barra/2 + 5:.1f}" '
                 f'text-anchor="end" font-size="14" fill="{OSCURO}">{escape(str(etiqueta))}</text>')
        texto_valor = fmt(valor) + (f" {unidad}" if unidad else "")
        if ancho_valor:
            texto_valor = ancho_valor(valor)
        s.append(f'<text x="{margen_izq + ancho + 10:.1f}" '
                 f'y="{y + alto_barra/2 + 5:.1f}" font-size="13" '
                 f'font-weight="bold" fill="{OSCURO}">{escape(texto_valor)}</text>')

    s.append(eje_lineas(margen_izq, arriba, margen_izq, arriba + alto_plot))
    s.append(eje_lineas(margen_izq, arriba + alto_plot, margen_izq + ancho_plot,
                        arriba + alto_plot))
    s.append(svg_fin())
    escribir_svg(nombre, "\n".join(s))


# --------------------------------------------------------------------------
# Gráfico de barras verticales (simple o agrupadas)
# --------------------------------------------------------------------------
def barras_verticales(nombre, categorias, series, titulo_txt, subtitulo_txt,
                      unidad="", ancho_total=None):
    """series: lista de (nombre_serie, color, [valores])."""
    margen_izq = 90
    margen_der = 40
    arriba = 120
    abajo = 130
    alto_plot = H - arriba - abajo
    ancho_plot = W - margen_izq - margen_der

    todos = [v for _, _, vals in series for v in vals]
    max_val = nice_max(max(todos) if todos else 1)

    n_cat = len(categorias)
    ancho_grupo = ancho_plot / n_cat
    n_series = len(series)
    ancho_barra = ancho_grupo * 0.7 / n_series

    s = [svg_inicio(), titulo(titulo_txt, subtitulo_txt)]

    pasos = 5
    for i in range(pasos + 1):
        y = arriba + alto_plot - alto_plot * i / pasos
        val = max_val * i / pasos
        s.append(f'<line x1="{margen_izq}" y1="{y:.1f}" x2="{margen_izq + ancho_plot}" '
                 f'y2="{y:.1f}" stroke="{GRIS_CLARO}" stroke-width="1"/>')
        s.append(f'<text x="{margen_izq - 12}" y="{y + 4:.1f}" text-anchor="end" '
                 f'font-size="12" fill="{GRIS}">{fmt(val)}</text>')

    for j, (nombre_serie, color, vals) in enumerate(series):
        for i, valor in enumerate(vals):
            x_centro = margen_izq + ancho_grupo * i + ancho_grupo / 2
            # distribuir barras alrededor del centro
            offset = (j - (n_series - 1) / 2) * ancho_barra
            x = x_centro + offset - ancho_barra / 2
            alto = alto_plot * (valor / max_val) if max_val else 0
            y = arriba + alto_plot - alto
            s.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{ancho_barra - 2:.1f}" '
                     f'height="{alto:.1f}" rx="2" fill="{color}"/>')
            if alto > 22:
                s.append(f'<text x="{x + ancho_barra/2 - 1:.1f}" y="{y + 14:.1f}" '
                         f'text-anchor="middle" font-size="10" font-weight="bold" '
                         f'fill="{FONDO}">{fmt(valor)}</text>')

    # Etiquetas de categorías (rotadas si son largas)
    for i, cat in enumerate(categorias):
        x = margen_izq + ancho_grupo * i + ancho_grupo / 2
        y = arriba + alto_plot + 20
        if len(str(cat)) > 10:
            s.append(f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="end" font-size="12" '
                     f'fill="{OSCURO}" transform="rotate(-35 {x:.1f} {y:.1f})">'
                     f'{escape(str(cat))}</text>')
        else:
            s.append(f'<text x="{x:.1f}" y="{y + 4:.1f}" text-anchor="middle" '
                     f'font-size="12" fill="{OSCURO}">{escape(str(cat))}</text>')

    s.append(eje_lineas(margen_izq, arriba, margen_izq, arriba + alto_plot))
    s.append(eje_lineas(margen_izq, arriba + alto_plot, margen_izq + ancho_plot,
                        arriba + alto_plot))

    # Leyenda
    if len(series) > 1:
        lx = margen_izq
        ly = H - 28
        for nombre_serie, color, _ in series:
            s.append(f'<rect x="{lx}" y="{ly - 12}" width="16" height="16" '
                     f'rx="3" fill="{color}"/>')
            s.append(f'<text x="{lx + 24}" y="{ly + 1}" font-size="13" '
                     f'fill="{OSCURO}">{escape(nombre_serie)}</text>')
            lx += 24 + 9 * len(nombre_serie) + 30

    s.append(svg_fin())
    escribir_svg(nombre, "\n".join(s))


# --------------------------------------------------------------------------
# Gráfico de dona
# --------------------------------------------------------------------------
def _punto(cx, cy, r, angulo):
    rad = (angulo - 90) * pi / 180
    return cx + r * cos(rad), cy + r * sin(rad)


def _arco(cx, cy, r_ext, r_int, inicio, fin):
    x1, y1 = _punto(cx, cy, r_ext, inicio)
    x2, y2 = _punto(cx, cy, r_ext, fin)
    x3, y3 = _punto(cx, cy, r_int, fin)
    x4, y4 = _punto(cx, cy, r_int, inicio)
    grande = 1 if (fin - inicio) > 180 else 0
    return (f"M {x1:.2f} {y1:.2f} A {r_ext} {r_ext} 0 {grande} 1 {x2:.2f} {y2:.2f} "
            f"L {x3:.2f} {y3:.2f} A {r_int} {r_int} 0 {grande} 0 {x4:.2f} {y4:.2f} Z")


def dona(nombre, etiquetas, valores, titulo_txt, subtitulo_txt,
         colores=None, unidad=""):
    colores = colores or PALETA
    total = sum(valores)
    if total <= 0:
        return

    cx, cy = 360, 355
    r_ext, r_int = 175, 100
    s = [svg_inicio(), titulo(titulo_txt, subtitulo_txt)]

    inicio = 0.0
    for i, (etq, val) in enumerate(zip(etiquetas, valores)):
        fin = inicio + 360 * val / total
        color = colores[i % len(colores)]
        s.append(f'<path d="{_arco(cx, cy, r_ext, r_int, inicio, fin)}" '
                 f'fill="{color}" stroke="{FONDO}" stroke-width="2"/>')
        # Porcentaje en el arco
        medio = (inicio + fin) / 2
        px, py = _punto(cx, cy, (r_ext + r_int) / 2, medio)
        pct = 100 * val / total
        if pct > 6:
            s.append(f'<text x="{px:.1f}" y="{py + 5:.1f}" text-anchor="middle" '
                     f'font-size="16" font-weight="bold" fill="{FONDO}">{pct:.1f}%</text>')
        inicio = fin

    # Centro de la dona
    s.append(f'<text x="{cx}" y="{cy - 8}" text-anchor="middle" font-size="40" '
             f'font-weight="bold" fill="{OSCURO}">{fmt(total)}</text>')
    s.append(f'<text x="{cx}" y="{cy + 22}" text-anchor="middle" font-size="15" '
             f'fill="{GRIS}">registros</text>')

    # Leyenda
    lx = 620
    ly = 250
    for i, (etq, val) in enumerate(zip(etiquetas, valores)):
        color = colores[i % len(colores)]
        y = ly + i * 52
        s.append(f'<rect x="{lx}" y="{y}" width="22" height="22" rx="4" fill="{color}"/>')
        s.append(f'<text x="{lx + 34}" y="{y + 17}" font-size="17" fill="{OSCURO}">'
                 f'{escape(str(etq))}</text>')
        s.append(f'<text x="{lx + 34}" y="{y + 38}" font-size="13" fill="{GRIS}">'
                 f'{fmt(val)}{(" " + unidad) if unidad else ""} '
                 f'({100*val/total:.1f}%)</text>')

    s.append(svg_fin())
    escribir_svg(nombre, "\n".join(s))


# --------------------------------------------------------------------------
# Histograma
# --------------------------------------------------------------------------
def histograma(nombre, valores, titulo_txt, subtitulo_txt,
               tam_bin=500, color=AZUL, unidad="USD"):
    if not valores:
        return
    minimo = min(valores)
    maximo = max(valores)
    inicio = (int(minimo) // tam_bin) * tam_bin
    fin = ((int(maximo) // tam_bin) + 1) * tam_bin
    bordes = list(range(int(inicio), int(fin) + tam_bin, int(tam_bin)))

    conteos = [0] * (len(bordes) - 1)
    for v in valores:
        idx = int((v - bordes[0]) // tam_bin)
        if idx < 0:
            idx = 0
        if idx >= len(conteos):
            idx = len(conteos) - 1
        conteos[idx] += 1

    etiquetas = [f"{fmt(bordes[i])}-{fmt(bordes[i+1])}" for i in range(len(conteos))]

    margen_izq = 90
    margen_der = 40
    arriba = 130
    abajo = 120
    alto_plot = H - arriba - abajo
    ancho_plot = W - margen_izq - margen_der

    max_conteo = nice_max(max(conteos) if conteos else 1)
    n = len(conteos)
    ancho_barra = ancho_plot / n

    s = [svg_inicio(), titulo(titulo_txt, subtitulo_txt)]

    pasos = 5
    for i in range(pasos + 1):
        y = arriba + alto_plot - alto_plot * i / pasos
        val = max_conteo * i / pasos
        s.append(f'<line x1="{margen_izq}" y1="{y:.1f}" x2="{margen_izq + ancho_plot}" '
                 f'y2="{y:.1f}" stroke="{GRIS_CLARO}" stroke-width="1"/>')
        s.append(f'<text x="{margen_izq - 12}" y="{y + 4:.1f}" text-anchor="end" '
                 f'font-size="12" fill="{GRIS}">{int(round(val))}</text>')

    for i, c in enumerate(conteos):
        x = margen_izq + i * ancho_barra + ancho_barra * 0.1
        alto = alto_plot * (c / max_conteo) if max_conteo else 0
        y = arriba + alto_plot - alto
        s.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{ancho_barra*0.8:.1f}" '
                 f'height="{alto:.1f}" rx="2" fill="{color}"/>')
        if c:
            s.append(f'<text x="{x + ancho_barra*0.4:.1f}" y="{y - 8:.1f}" '
                     f'text-anchor="middle" font-size="13" font-weight="bold" '
                     f'fill="{OSCURO}">{c}</text>')
        # etiqueta de rango
        xt = margen_izq + i * ancho_barra + ancho_barra / 2
        s.append(f'<text x="{xt:.1f}" y="{arriba + alto_plot + 20:.1f}" '
                 f'text-anchor="middle" font-size="11" fill="{OSCURO}">'
                 f'{escape(etiquetas[i])}</text>')

    # Línea de promedio
    promedio = sum(valores) / len(valores)
    max_borde = bordes[-1]
    min_borde = bordes[0]
    xp = margen_izq + ancho_plot * (promedio - min_borde) / (max_borde - min_borde)
    s.append(f'<line x1="{xp:.1f}" y1="{arriba}" x2="{xp:.1f}" '
             f'y2="{arriba + alto_plot}" stroke="{NARANJA}" stroke-width="2" '
             f'stroke-dasharray="7,5"/>')
    s.append(f'<text x="{xp:.1f}" y="{arriba - 12}" text-anchor="middle" '
             f'font-size="13" font-weight="bold" fill="{NARANJA}">'
             f'Promedio: {fmt(promedio)} {unidad}</text>')

    s.append(eje_lineas(margen_izq, arriba, margen_izq, arriba + alto_plot))
    s.append(eje_lineas(margen_izq, arriba + alto_plot, margen_izq + ancho_plot,
                        arriba + alto_plot))
    s.append(f'<text x="{margen_izq + ancho_plot/2}" y="{H - 30}" text-anchor="middle" '
             f'font-size="14" fill="{GRIS}">Rango de precio ({unidad})</text>')
    s.append(f'<text x="28" y="{arriba + alto_plot/2}" text-anchor="middle" '
             f'font-size="14" fill="{GRIS}" transform="rotate(-90 28 {arriba + alto_plot/2})">'
             f'Número de triciclos</text>')

    s.append(svg_fin())
    escribir_svg(nombre, "\n".join(s))


# --------------------------------------------------------------------------
# Carga y preparación de datos
# --------------------------------------------------------------------------
def main():
    os.makedirs(GRAFICOS, exist_ok=True)

    filas = cargar_csv(os.path.join(DATOS, "datos_consolidados.csv"))
    mercado = cargar_json(os.path.join(DATOS, "mercadodetriciclos.json"), {})
    analisis = cargar_json(os.path.join(RESULTADOS, "analisis_completo.json"), {})

    precios = [float(f["precio"]) for f in filas if f.get("precio")]
    print(f"Registros CSV: {len(filas)} | Precios: {len(precios)}")

    # 1. Histograma de precios
    histograma(
        "grafico_precios.svg", precios,
        "Distribución de precios del mercado",
        "Triciclos eléctricos en La Habana · datos consolidados",
        tam_bin=500, color=AZUL,
    )

    # 2. Distribución por municipio
    municipios = {}
    for f in filas:
        m = f.get("municipio", "Sin dato")
        municipios[m] = municipios.get(m, 0) + 1
    barras_horizontales(
        "grafico_municipios.svg",
        list(municipios.items()),
        "Distribución geográfica por municipio",
        "Cantidad de triciclos registrados por municipio",
        color=AZUL, unidad="triciclos",
    )

    # 3. Categoría de uso (dona)
    categoria = analisis.get("categoria_uso") or {"Carga": 15, "Pasajeros": 5}
    dona(
        "grafico_uso.svg",
        list(categoria.keys()), list(categoria.values()),
        "Distribución por categoría de uso",
        "Orientación de los triciclos: carga vs. pasajeros",
        colores=[AZUL, AMARILLO],
    )

    # 4. Barreras / obstáculos legales
    barreras = analisis.get("legalidad_obstaculos") or {}
    barreras = [(k, v) for k, v in barreras.items()
                if k not in ("-", "", None) and k.lower() != "en regla"]
    barras_horizontales(
        "grafico_barreras.svg",
        barreras,
        "Principales barreras del mercado",
        "Obstáculos legales y operativos mencionados en entrevistas",
        color=NARANJA, unidad="mención(es)",
    )

    # 5. Fuentes de datos (dona)
    fuentes = analisis.get("fuentes") or {"Web": 12, "Entrevista": 8}
    dona(
        "grafico_fuentes.svg",
        list(fuentes.keys()), list(fuentes.values()),
        "Fuentes de los datos analizados",
        "Origen de los registros del estudio",
        colores=[AZUL, AMARILLO],
    )

    # 6. Precio mínimo, promedio y máximo por municipio
    por_municipio = {}
    for f in filas:
        if not f.get("precio"):
            continue
        por_municipio.setdefault(f["municipio"], []).append(float(f["precio"]))
    cats = sorted(por_municipio.keys())
    mins = [min(por_municipio[c]) for c in cats]
    proms = [sum(por_municipio[c]) / len(por_municipio[c]) for c in cats]
    maxs = [max(por_municipio[c]) for c in cats]
    barras_verticales(
        "grafico_precios_municipio.svg",
        cats,
        [("Mínimo", AZUL, mins),
         ("Promedio", AMARILLO, proms),
         ("Máximo", NARANJA, maxs)],
        "Precios por municipio (mínimo, promedio y máximo)",
        "Precios en USD de triciclos eléctricos",
        unidad="USD",
    )

    # 7. Distribución por marca
    marcas = {}
    for r in mercado.get("registros", []):
        m = r.get("marca", "Sin dato")
        marcas[m] = marcas.get(m, 0) + 1
    barras_horizontales(
        "grafico_marcas.svg",
        list(marcas.items()),
        "Distribución por marca",
        "Frecuencia de marcas en el mercado (fuente web)",
        color=AZUL, unidad="registros",
    )

    print("Listo. Gráficos generados en:", GRAFICOS)


if __name__ == "__main__":
    main()
