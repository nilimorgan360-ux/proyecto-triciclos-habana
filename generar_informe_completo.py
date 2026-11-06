#!/usr/bin/env python3
"""
Genera el informe completo del Proyecto de Ciencia de Datos:
Mercado de Triciclos Eléctricos de La Habana.

Salida: reporte_completo.pdf
Requiere: fpdf (y las imagenes PNG en graficos/).
"""

import csv
import json
import os
import statistics

from fpdf import FPDF

BASE = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(BASE, "datos")
RESULTADOS = os.path.join(BASE, "resultados")
GRAFICOS = os.path.join(BASE, "graficos")
SALIDA = os.path.join(BASE, "reporte_completo.pdf")

AZUL = (33, 158, 188)
AMARILLO = (255, 183, 3)
NARANJA = (251, 133, 0)
OSCURO = (2, 48, 71)
GRIS = (100, 106, 115)
GRIS_CLARO = (240, 243, 246)

MAPA_USO = {
    "alta": "Carga", "media": "Carga", "baja": "Pasajeros",
    "alquiler": "Pasajeros", "compra": "Carga",
}


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


def fmt(n, dec=0):
    if dec:
        return f"{n:,.{dec}f}"
    return f"{int(round(n)):,}"


class PDF(FPDF):
    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*GRIS)
        self.cell(0, 8, f"Pagina {self.page_no()} - Mercado de triciclos electricos de La Habana",
                  0, 0, "C")


def h1(pdf, texto, num=None):
    if pdf.get_y() > 250:
        pdf.add_page()
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(*OSCURO)
    etiqueta = f"{num}. {texto}" if num else texto
    pdf.multi_cell(0, 8, etiqueta)
    pdf.set_draw_color(*AZUL)
    pdf.set_line_width(0.6)
    y = pdf.get_y()
    pdf.line(pdf.l_margin, y, pdf.l_margin + 40, y)
    pdf.ln(3)


def h2(pdf, texto):
    if pdf.get_y() > 260:
        pdf.add_page()
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*AZUL)
    pdf.multi_cell(0, 6.5, texto)
    pdf.ln(1)


def p(pdf, texto):
    pdf.set_font("Helvetica", "", 10.5)
    pdf.set_text_color(40, 40, 40)
    pdf.multi_cell(0, 5.6, texto)
    pdf.ln(1.5)


def bullet(pdf, texto):
    pdf.set_font("Helvetica", "", 10.5)
    pdf.set_text_color(40, 40, 40)
    pdf.set_x(pdf.l_margin)
    pdf.cell(5, 5.6, "-")
    pdf.multi_cell(0, 5.6, texto)


def imagen(pdf, archivo, ancho, pie):
    ruta = os.path.join(GRAFICOS, archivo)
    if not os.path.exists(ruta):
        return
    alto = ancho * 760 / 1200
    if pdf.get_y() + alto + 14 > 275:
        pdf.add_page()
    y = pdf.get_y()
    x = (210 - ancho) / 2
    pdf.image(ruta, x=x, y=y, w=ancho)
    pdf.set_y(y + alto + 2)
    pdf.set_font("Helvetica", "I", 8.5)
    pdf.set_text_color(*GRIS)
    pdf.multi_cell(0, 5, pie, align="C")
    pdf.ln(3)


def tabla(pdf, cabeceras, filas, anchos, tam=9):
    if pdf.get_y() + 7 * (len(filas) + 1) > 270:
        pdf.add_page()
    pdf.set_font("Helvetica", "B", tam)
    pdf.set_fill_color(*OSCURO)
    pdf.set_text_color(255, 255, 255)
    for c, w in zip(cabeceras, anchos):
        pdf.cell(w, 7, c, 0, 0, "C", True)
    pdf.ln()
    pdf.set_font("Helvetica", "", tam)
    for i, fila in enumerate(filas):
        if pdf.get_y() > 270:
            pdf.add_page()
            pdf.set_font("Helvetica", "B", tam)
            pdf.set_fill_color(*OSCURO)
            pdf.set_text_color(255, 255, 255)
            for c, w in zip(cabeceras, anchos):
                pdf.cell(w, 7, c, 0, 0, "C", True)
            pdf.ln()
            pdf.set_font("Helvetica", "", tam)
        relleno = i % 2 == 0
        pdf.set_fill_color(*GRIS_CLARO)
        pdf.set_text_color(40, 40, 40)
        for v, w in zip(fila, anchos):
            pdf.cell(w, 6, str(v), 0, 0, "C", relleno)
        pdf.ln()
    pdf.set_text_color(40, 40, 40)
    pdf.ln(3)


def main():
    filas = cargar_csv(os.path.join(DATOS, "datos_consolidados.csv"))
    mercado = cargar_json(os.path.join(DATOS, "mercadodetriciclos.json"), {})
    registros = mercado.get("registros", [])

    precios = [float(f["precio"]) for f in filas if f.get("precio")]
    precios.sort()
    n = len(filas)
    prom = statistics.mean(precios)
    mediana = statistics.median(precios)
    desv = statistics.pstdev(precios)
    pmin, pmax = min(precios), max(precios)

    mun = {}
    mun_precios = {}
    for f in filas:
        m = f.get("municipio", "Sin dato")
        mun[m] = mun.get(m, 0) + 1
        mun_precios.setdefault(m, []).append(float(f["precio"]))

    fuentes = {}
    for f in filas:
        fuentes[f.get("fuente", "Sin dato")] = fuentes.get(f.get("fuente", "Sin dato"), 0) + 1

    uso = {}
    for f in filas:
        cat = MAPA_USO.get(f.get("tipo_de_uso", "").strip().lower(), "Sin clasificar")
        uso[cat] = uso.get(cat, 0) + 1

    barreras = {}
    for f in filas:
        b = (f.get("barrera") or "").strip()
        if b and b != "-":
            barreras[b] = barreras.get(b, 0) + 1

    marcas = {}
    for r in registros:
        marcas[r.get("marca", "Sin dato")] = marcas.get(r.get("marca", "Sin dato"), 0) + 1

    legal = {}
    panel = {}
    for r in registros:
        legal[r.get("legalidad", "-")] = legal.get(r.get("legalidad", "-"), 0) + 1
        panel[r.get("panel_solar", "no")] = panel.get(r.get("panel_solar", "no"), 0) + 1

    # ------------------------------------------------------------------
    pdf = PDF("P", "mm", "A4")
    pdf.set_auto_page_break(True, margin=18)
    pdf.set_margins(20, 18, 20)

    # ================= PORTADA =================
    pdf.add_page()
    pdf.set_fill_color(*OSCURO)
    pdf.rect(0, 0, 210, 120, "F")
    pdf.set_y(45)
    pdf.set_font("Helvetica", "B", 26)
    pdf.set_text_color(255, 255, 255)
    pdf.multi_cell(170, 12, "Mercado de Triciclos Electricos de La Habana", align="C")
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 15)
    pdf.set_text_color(*AMARILLO)
    pdf.multi_cell(170, 9, "Informe completo de ciencia de datos", align="C")
    pdf.ln(6)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(220, 230, 235)
    pdf.multi_cell(170, 6, "Datos de anuncios web y entrevistas directas\nLa Habana, Cuba", align="C")

    pdf.set_y(145)
    pdf.set_text_color(*OSCURO)
    pdf.set_font("Helvetica", "B", 13)
    pdf.multi_cell(170, 8, "Contenido", align="L")
    pdf.ln(2)
    pdf.set_font("Helvetica", "", 11)
    for linea in [
        "Resumen ejecutivo",
        "1. Introduccion y contexto",
        "2. Objetivos y preguntas de investigacion",
        "3. Metodologia",
        "4. Datos analizados",
        "5. Resultados",
        "6. Limitaciones",
        "7. Conclusiones",
        "8. Recomendaciones",
        "9. Reproducibilidad y anexos",
    ]:
        pdf.cell(0, 7, linea, 0, 1)

    pdf.set_y(255)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(*GRIS)
    pdf.multi_cell(170, 5,
                   f"Documento generado a partir de {n} registros consolidados. "
                   "Las cifras corresponden a la muestra disponible y no constituyen un censo del mercado.",
                   align="C")

    # ================= RESUMEN =================
    pdf.add_page()
    h1(pdf, "Resumen ejecutivo")
    p(pdf, f"Este informe analiza el mercado de triciclos electricos de La Habana a partir de "
           f"{n} registros consolidados: {fuentes.get('web', 0)} obtenidos de anuncios web y "
           f"{fuentes.get('entrevista', 0)} de entrevistas directas a operadores y compradores. "
           "Se estudiaron precios, distribucion geografica, categorias de uso, marcas, barreras "
           "legales y fuentes de adquisicion.")
    p(pdf, f"El precio de los triciclos se situa entre {fmt(pmin)} y {fmt(pmax)} USD, con un "
           f"promedio de {fmt(prom)} USD y una mediana de {fmt(mediana)} USD. La mayor "
           f"concentracion de registros se encuentra en {max(mun, key=mun.get)}, mientras que "
           f"el uso de carga domina sobre el de pasajeros ({uso.get('Carga', 0)} frente a "
           f"{uso.get('Pasajeros', 0)} registros).")
    p(pdf, "Las principales barreras identificadas son la falta de documentos, los precios "
           "altos, la burocracia y la lentitud de los tramites. La muestra es pequena y "
           "heterogenea, por lo que los resultados deben interpretarse como una aproximacion "
           "exploratoria al mercado y no como estimaciones representativas del total.")

    # ================= 1. INTRODUCCION =================
    h1(pdf, "Introduccion y contexto", 1)
    p(pdf, "El triciclo electrico se ha consolidado en La Habana como una alternativa de "
           "transporte para el traslado de mercancias y pasajeros. Su bajo costo de operacion "
           "frente a los vehiculos de combustion, junto con la flexibilidad para circular por "
           "calles estrechas, explica su presencia creciente en distintos municipios de la ciudad.")
    p(pdf, "Sin embargo, el mercado presenta caracteristicas poco documentadas: los precios "
           "varian ampliamente, la informacion sobre legalidad y documentacion es escasa y las "
           "condiciones de adquisicion dependen en gran medida de redes informales. Este "
           "proyecto busca caracterizar ese mercado con evidencia descriptiva y visual.")
    p(pdf, "El estudio combina dos fuentes complementarias: anuncios publicados en la web, que "
           "reflejan precios de lista y caracteristicas tecnicas, y entrevistas directas, que "
           "aportan informacion sobre practicas reales de compra, alquiler y barreras percibidas.")

    # ================= 2. OBJETIVOS =================
    h1(pdf, "Objetivos y preguntas de investigacion", 2)
    h2(pdf, "Objetivo general")
    p(pdf, "Caracterizar el mercado de triciclos electricos de La Habana mediante un analisis "
           "descriptivo de precios, distribucion geografica, categorias de uso, marcas, "
           "legalidad y fuentes de adquisicion.")
    h2(pdf, "Objetivos especificos")
    bullet(pdf, "Describir la distribucion de precios del mercado.")
    bullet(pdf, "Identificar la concentracion geografica por municipio.")
    bullet(pdf, "Comparar el uso de carga frente al de pasajeros.")
    bullet(pdf, "Identificar las principales barreras legales y operativas.")
    bullet(pdf, "Analizar las fuentes de adquisicion y las marcas presentes.")
    h2(pdf, "Preguntas clave")
    bullet(pdf, "Cual es el rango y el promedio de precios de los triciclos electricos?")
    bullet(pdf, "Como se distribuyen los registros por municipio y por categoria de uso?")
    bullet(pdf, "Que factores legales o barreras limitan el mercado?")
    bullet(pdf, "Cuales son las fuentes principales de adquisicion?")
    bullet(pdf, "Existe relacion entre el precio y la categoria de uso?")

    # ================= 3. METODOLOGIA =================
    h1(pdf, "Metodologia", 3)
    h2(pdf, "3.1 Fuentes de datos")
    p(pdf, "Se utilizaron dos fuentes principales. La primera es un conjunto de anuncios web de "
           "triciclos electricos, registrado en formato JSON, que incluye marca, precio, "
           "capacidad, potencia, autonomia, velocidad, municipio, legalidad y disponibilidad de "
           "panel solar. La segunda es una serie de entrevistas directas, registrada en formato "
           "CSV, que aporta informacion sobre precios, tipo de uso, barreras y fuente.")
    h2(pdf, "3.2 Consolidacion y limpieza")
    p(pdf, "Los registros se consolidaron en un unico archivo CSV con cinco variables: municipio, "
           "tipo de uso, precio, barrera y fuente. Se normalizaron los nombres de los municipios "
           "y se identificaron los valores faltantes mediante el codigo '-'. Para el analisis de "
           "categorias de uso se aplico una regla de mapeo que agrupa los tipos 'alta', 'media' y "
           "'compra' como Carga, y 'baja' y 'alquiler' como Pasajeros.")
    h2(pdf, "3.3 Analisis y visualizacion")
    p(pdf, "Se realizo un analisis descriptivo: frecuencias, medidas de tendencia central y "
           "dispersion, y comparaciones por municipio y categoria. Los resultados se presentan "
           "mediante histogramas, graficos de barras, diagramas de rango y graficos de dona. "
           "Los graficos se generaron en SVG, PNG y PDF con scripts reproducibles incluidos en el "
           "repositorio.")

    # ================= 4. DATOS =================
    h1(pdf, "Datos analizados", 4)
    p(pdf, f"El archivo consolidado contiene {n} registros. La tabla siguiente resume las "
           "variables utilizadas y su descripcion.")
    tabla(pdf,
          ["Variable", "Descripcion", "Tipo"],
          [["municipio", "Municipio de La Habana", "Categorica"],
           ["tipo_de_uso", "Carga, pasajeros, alta/media/baja", "Categorica"],
           ["precio", "Precio en USD", "Numerica"],
           ["barrera", "Barrera u obstaculo declarado", "Categorica"],
           ["fuente", "Web o entrevista", "Categorica"]],
          [45, 85, 40])
    p(pdf, f"El JSON de mercado contiene {len(registros)} registros web con informacion tecnica "
           "adicional (marca, capacidad, potencia, autonomia, velocidad, legalidad y panel solar). "
           f"En conjunto, la fuente web aporta {fuentes.get('web', 0)} registros y las entrevistas "
           f"{fuentes.get('entrevista', 0)}.")

    # ================= 5. RESULTADOS =================
    h1(pdf, "Resultados", 5)
    h2(pdf, "5.1 Distribucion de precios")
    p(pdf, f"Los precios observados van de {fmt(pmin)} a {fmt(pmax)} USD. El promedio es de "
           f"{fmt(prom)} USD, la mediana de {fmt(mediana)} USD y la desviacion tipica de "
           f"{fmt(desv)} USD, lo que indica una dispersion moderada con una concentracion "
           "principal en el tramo de 3,500 a 4,000 USD.")
    imagen(pdf, "grafico_precios.png", 155,
           "Figura 1. Distribucion de precios de los triciclos electricos (USD).")

    h2(pdf, "5.2 Distribucion geografica")
    filas_mun = sorted(mun.items(), key=lambda kv: kv[1], reverse=True)
    p(pdf, f"La muestra se concentra en {filas_mun[0][0]} con {filas_mun[0][1]} registros, "
           f"seguido de {filas_mun[1][0]} con {filas_mun[1][1]}. El resto de los municipios "
           "aparece con uno o dos registros, lo que refleja una cobertura desigual.")
    imagen(pdf, "grafico_municipios.png", 155,
           "Figura 2. Cantidad de triciclos registrados por municipio.")

    h2(pdf, "5.3 Categoria de uso")
    p(pdf, f"El uso de carga predomina con {uso.get('Carga', 0)} registros, frente a "
           f"{uso.get('Pasajeros', 0)} de pasajeros. Esto sugiere que el mercado esta orientado "
           "principalmente a actividades de transporte de mercancias y logistica urbana.")
    imagen(pdf, "grafico_uso.png", 150,
           "Figura 3. Distribucion por categoria de uso.")

    h2(pdf, "5.4 Marcas")
    marcas_ord = sorted(marcas.items(), key=lambda kv: kv[1], reverse=True)
    p(pdf, "La marca mas frecuente es "
           f"{marcas_ord[0][0]} con {marcas_ord[0][1]} registros, seguida de "
           f"{marcas_ord[1][0]} con {marcas_ord[1][1]}. La oferta esta compuesta por pocas "
           "marcas y un numero reducido de modelos por marca.")
    imagen(pdf, "grafico_marcas.png", 150,
           "Figura 4. Frecuencia de marcas en el mercado (fuente web).")

    h2(pdf, "5.5 Barreras y legalidad")
    p(pdf, f"Del total de registros, {legal.get('En regla', 0)} aparecen como 'En regla' y "
           f"{legal.get('-', 0)} no especifican su situacion legal. Entre las barreras "
           "declaradas destacan la falta de documentos, los precios altos, los horarios "
           "limitados, los tramites lentos, la falta de infraestructura, la burocracia, la "
           "falta de mantenimiento y los requisitos estrictos.")
    imagen(pdf, "grafico_barreras.png", 150,
           "Figura 5. Principales barreras legales y operativas mencionadas.")

    h2(pdf, "5.6 Fuentes de adquisicion")
    p(pdf, f"La fuente web aporta {fuentes.get('web', 0)} registros (precios de lista y "
           f"caracteristicas tecnicas) y las entrevistas {fuentes.get('entrevista', 0)} "
           "(experiencias reales de compra y alquiler). La combinacion permite contrastar la "
           "oferta publicada con la practica declarada por los actores.")
    imagen(pdf, "grafico_fuentes.png", 145,
           "Figura 6. Origen de los registros del estudio.")

    h2(pdf, "5.7 Precios por municipio")
    mun_prom = {m: statistics.mean(v) for m, v in mun_precios.items()}
    mayor = max(mun_prom, key=mun_prom.get)
    menor = min(mun_prom, key=mun_prom.get)
    p(pdf, f"El promedio de precios mas alto se observa en {mayor} "
           f"({fmt(mun_prom[mayor])} USD) y el mas bajo en {menor} "
           f"({fmt(mun_prom[menor])} USD). El grafico de rango muestra, ademas, la amplitud "
           "entre el precio minimo y maximo de cada municipio.")
    imagen(pdf, "grafico_precios_municipio.png", 160,
           "Figura 7. Rango de precios y promedio por municipio.")

    h2(pdf, "5.8 Panel solar y especificaciones tecnicas")
    p(pdf, f"De los {len(registros)} registros web, solo {panel.get('Si', panel.get('Sí', 0))} "
           "incluye panel solar. Las capacidades registradas son de 8 unidades en todos los "
           "casos; la potencia varia entre 400 W y 650 W, la autonomia entre 35 km y 55 km, y "
           "la velocidad maxima entre 20 km/h y 35 km/h. La adopcion de paneles solares es, por "
           "tanto, minoritaria en la muestra.")

    # ================= 6. LIMITACIONES =================
    h1(pdf, "Limitaciones", 6)
    p(pdf, "Los resultados deben interpretarse con cautela debido a las siguientes limitaciones:")
    bullet(pdf, "Muestra pequena: el analisis se basa en 20 registros consolidados, insuficientes "
                "para estimaciones representativas del mercado total de La Habana.")
    bullet(pdf, "Sesgo de seleccion: los anuncios web y las entrevistas no constituyen un muestreo "
                "aleatorio; predominan ciertos municipios y marcas.")
    bullet(pdf, "Datos auto-reportados: precios, legalidad y barreras provienen de anuncios y "
                "declaraciones, sin verificacion documental independiente.")
    bullet(pdf, "Inconsistencias entre archivos: algunos resumenes reportan 32 registros al sumar "
                "JSON y CSV, pero el CSV ya incluye los registros web; el presente informe usa 20 "
                "registros unicos. Tambien se detectaron diferencias en el conteo de panel solar "
                "y en el numero de registros de algunas marcas entre resumenes y datos crudos.")
    bullet(pdf, "Regla de mapeo simplificada: agrupar 'alquiler' como Pasajeros y 'compra' como "
                "Carga es una aproximacion; un triciclo alquilado tambien puede destinarse a carga.")
    bullet(pdf, "Valores faltantes: la legalidad no se especifica en la mayoria de los registros "
                "y varias barreras aparecen una sola vez.")
    bullet(pdf, "Corte transversal: no hay serie temporal, por lo que no es posible analizar "
                "tendencias ni estacionalidad.")
    bullet(pdf, "Variables ausentes: no se recogen costos de operacion, mantenimiento, ingresos, "
                "financiamiento ni condiciones del mercado secundario.")
    bullet(pdf, "Precios en USD de lista o declarados: no se ajustan por inflacion, tipo de cambio "
                "ni capacidad real de negociacion.")

    # ================= 7. CONCLUSIONES =================
    h1(pdf, "Conclusiones", 7)
    p(pdf, "El mercado de triciclos electricos de La Habana, segun la muestra analizada, se "
           "caracteriza por precios relativamente altos y dispersos, una marcada concentracion "
           "geografica y un predominio del uso de carga. La informacion legal es incompleta y "
           "las barreras administrativas y documentales aparecen como obstaculos recurrentes.")
    p(pdf, "La comparacion entre oferta web y entrevistas sugiere una brecha entre los precios "
           "publicados y las condiciones reales de adquisicion. La presencia de marcas es "
           "reducida y la tecnologia solar es todavia marginal.")
    p(pdf, "En conjunto, el estudio ofrece una primera caracterizacion descriptiva y "
           "reproducible del mercado, util como base para investigaciones con muestras mayores "
           "y para el diseno de politicas de formalizacion y acceso.")

    # ================= 8. RECOMENDACIONES =================
    h1(pdf, "Recomendaciones", 8)
    bullet(pdf, "Ampliar la muestra con un diseno de recoleccion sistematico por municipio.")
    bullet(pdf, "Verificar documentacion y situacion legal de los equipos con fuentes oficiales.")
    bullet(pdf, "Incluir variables economicas: costos de operacion, mantenimiento, ingresos y "
                "financiamiento.")
    bullet(pdf, "Profundizar en las barreras regulatorias mediante entrevistas a autoridades y "
                "comerciantes.")
    bullet(pdf, "Evaluar la viabilidad de los triciclos con panel solar como alternativa "
                "sostenible.")
    bullet(pdf, "Repetir el levantamiento periodicamente para construir una serie temporal.")

    # ================= 9. REPRODUCIBILIDAD =================
    h1(pdf, "Reproducibilidad y anexos", 9)
    h2(pdf, "Estructura del proyecto")
    pdf.set_font("Courier", "", 8.5)
    pdf.set_text_color(40, 40, 40)
    estructura = (
        "proyecto_ciencia_datos/\n"
        "  datos/datos_consolidados.csv\n"
        "  datos/mercadodetriciclos.json\n"
        "  introduccion/introduccion.md\n"
        "  resultados/analisis_completo.json\n"
        "  resultados/resumen_ejecutivo.md\n"
        "  graficos/*.svg, *.png, index.html\n"
        "  generar_graficos.py\n"
        "  generar_graficos_png.py\n"
        "  generar_reporte_pdf.py\n"
        "  generar_informe_completo.py\n"
        "  reporte_completo.pdf\n"
    )
    pdf.multi_cell(0, 4.5, estructura)
    pdf.ln(3)
    h2(pdf, "Scripts")
    bullet(pdf, "generar_graficos.py: genera los graficos SVG sin dependencias externas.")
    bullet(pdf, "generar_graficos_png.py: genera los graficos PNG (requiere Pillow).")
    bullet(pdf, "generar_reporte_pdf.py: genera el reporte grafico en PDF (requiere fpdf).")
    bullet(pdf, "generar_informe_completo.py: genera este informe completo (requiere fpdf).")

    h2(pdf, "Anexo: registros por municipio")
    filas_tabla = [[m, c, fmt(statistics.mean(mun_precios[m]))] for m, c in filas_mun]
    tabla(pdf, ["Municipio", "Registros", "Precio promedio (USD)"],
          filas_tabla, [80, 35, 55])

    pdf.output(SALIDA)
    print("Informe generado:", SALIDA)
    print("Paginas:", pdf.page_no())
    print("Registros:", n, "| Precio promedio:", fmt(prom, 2))


if __name__ == "__main__":
    main()
