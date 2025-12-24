#---------------------------------------------------------

import io
import os
from datetime import datetime
from django.conf import settings
from django.http import FileResponse, HttpResponse
from django.contrib.staticfiles import finders
from django.shortcuts import get_object_or_404

# ReportLab imports
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, 
    TableStyle, Image, PageBreak, KeepTogether, Flowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Diccionario para mapear meses a nombres de campos
MESES_CAMPOS = {
    'enero': 'enero',
    'febrero': 'febrero',
    'marzo': 'marzo',
    'abril': 'abril',
    'mayo': 'mayo',
    'junio': 'junio',
    'julio': 'julio',
    'agosto': 'agosto',
    'septiembre': 'septiembre',
    'octubre': 'octubre',
    'noviembre': 'noviembre',
    'diciembre': 'diciembre'
}

# --- CLASE AUXILIAR PARA EL ENCABEZADO Y MARCADORES ---
class UpdateFichaFlowable(Flowable):
    def __init__(self, ficha, key):
        Flowable.__init__(self)
        self.ficha = ficha
        self.key = key
        
    def draw(self):
        self.canv.ficha_actual = self.ficha
        self.canv.bookmarkPage(self.key)

def generar_titulo_seccion(texto, estilo, color_linea):
    return KeepTogether([
        Paragraph(f"<b>{texto}</b>", estilo),
        Spacer(1, 1*mm),
        Table([[""]], colWidths=[190*mm], rowHeights=[0.4*mm], 
              style=[('LINEBELOW', (0,0), (-1,0), 1, color_linea),
                     ('LEFTPADDING', (0,0), (-1,-1), 0)])
    ])

def dibujar_encabezado_pagina_indice(canvas, doc):
    """Encabezado especial solo para la página del índice"""
    canvas.saveState()
    
    # Fondo del encabezado
    canvas.setFillColor(colors.HexColor("#f8fafc"))
    canvas.rect(0, A4[1] - 30*mm, A4[0], 30*mm, fill=1, stroke=0)
    
    # Título principal
    canvas.setFont(f_bold, 16)
    canvas.setFillColor(colors.HexColor("#b91c1c"))
    canvas.drawCentredString(A4[0]/2, A4[1] - 15*mm, "CONTROL LIBRO DEL EDIFICIO")
    
    # Subtítulo - Nombre del CCPP
    canvas.setFont(f_bold, 12)
    canvas.setFillColor(colors.HexColor("#4b5563"))
    canvas.drawCentredString(A4[0]/2, A4[1] - 22*mm, f"{ccpp.id_ccpp} - {ccpp.nombre}")
    
    # Año
    canvas.setFont(f_bold, 10)
    canvas.drawCentredString(A4[0]/2, A4[1] - 28*mm, f"AÑO {ano}")
    
    # Línea divisoria
    canvas.setStrokeColor(colors.HexColor("#b91c1c"))
    canvas.setLineWidth(1)
    canvas.line(20*mm, A4[1] - 32*mm, A4[0] - 20*mm, A4[1] - 32*mm)
    
    # Título del índice
    canvas.setFont(f_bold, 14)
    canvas.setFillColor(colors.HexColor("#1e293b"))
    canvas.drawCentredString(A4[0]/2, A4[1] - 45*mm, "ÍNDICE DE UNIDADES")
    
    # Línea bajo el título del índice
    canvas.setStrokeColor(colors.HexColor("#94a3b8"))
    canvas.setLineWidth(0.5)
    canvas.line(20*mm, A4[1] - 48*mm, A4[0] - 20*mm, A4[1] - 48*mm)
    
    canvas.restoreState()

def dibujar_elementos_fijos(canvas, doc):
    """Encabezado normal para el resto de páginas"""
    canvas.saveState()
    f = getattr(canvas, 'ficha_actual', None)
    if not f and fichas.exists(): f = fichas[0]
    if not f: return

    y_top = A4[1] - 8*mm 
    try:
        ruta_logo_est = finders.find('img/logo.png') or os.path.join(settings.BASE_DIR, 'static/img/logo.png')
        img_izq = Image(ruta_logo_est, width=13*mm, height=13*mm) if os.path.exists(ruta_logo_est) else ""
        img_der = Image(f.logo.path, width=13*mm, height=13*mm) if f.logo and os.path.exists(f.logo.path) else ""
    except: img_izq = img_der = ""

    bloque_central = [
        Paragraph("CONTROL LIBRO DEL EDIFICIO", estilos['enc_negro']),
        Paragraph(f.FK_FichaUnidad.doc if f.FK_FichaUnidad else "S/D", estilos['sub_rojo']),
        Paragraph(f"<b>{f.FK_FichaUnidad.capitulo if f.FK_FichaUnidad else ''}</b>", estilos['capitulo']),
        Paragraph(f.FK_FichaUnidad.unidad if f.FK_FichaUnidad else "", estilos['unidad'])
    ]

    t_header = Table([[img_izq, bloque_central, img_der]], colWidths=[18*mm, 154*mm, 18*mm])
    t_header.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
    t_header.wrapOn(canvas, doc.width, doc.topMargin)
    t_header.drawOn(canvas, doc.leftMargin, y_top - 16*mm)
    
    t_info = Table([[Paragraph(f"Técnico: {nombre_tecnico}", estilos['tecnico_h']), 
                     Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y')}", estilos['fecha_h'])]], colWidths=[95*mm, 95*mm])
    t_info.setStyle(TableStyle([('LINEBELOW', (0,0), (-1,0), 0.8, color_gris_oscuro), ('LEFTPADDING', (0,0), (-1,-1), 0)]))
    t_info.wrapOn(canvas, doc.width, doc.topMargin)
    t_info.drawOn(canvas, doc.leftMargin, y_top - 22*mm)

    canvas.setFont(f_reg, 7)
    canvas.drawCentredString(A4[0]/2, 10*mm, f"Página {canvas.getPageNumber()}")
    canvas.restoreState()

def dibujar_pie_pagina_indice(canvas, doc):
    """Pie de página solo para el índice"""
    canvas.saveState()
    canvas.setFont(f_reg, 7)
    canvas.drawCentredString(A4[0]/2, 10*mm, f"Página {canvas.getPageNumber()}")
    canvas.restoreState()

def exportar_ccpp_completo_pdf(request, ccpp_id):
    global ccpp, ano, fichas, nombre_tecnico, f_reg, f_bold, estilos, color_gris_oscuro, color_gris_suave, color_rojo_enfasis, color_fondo_cabecera, incluir_indice
    
    # --- PARÁMETROS ---
    incluir_firmas = request.GET.get('firmas', '1').lower() in ['1', 'true']
    incluir_anexos = request.GET.get('anexos', '1').lower() in ['1', 'true']
    incluir_indice = request.GET.get('indice', '1').lower() in ['1', 'true']
    
    ano = request.GET.get('ano') or request.GET.get('año')
    mes_inicio = request.GET.get('mes_inicio')
    mes_fin = request.GET.get('mes_fin')
    
    if not (ano and mes_inicio and mes_fin):
        return HttpResponse("Faltan parámetros de fecha.", content_type='text/plain')

    # --- 1. CONFIGURACIÓN DE FUENTES ---
    try:
        ruta_reg = finders.find('fonts/Poppins-Regular.ttf') or os.path.join(settings.BASE_DIR, 'static/fonts/Poppins-Regular.ttf')
        ruta_bold = finders.find('fonts/Poppins-Bold.ttf') or os.path.join(settings.BASE_DIR, 'static/fonts/Poppins-Bold.ttf')
        pdfmetrics.registerFont(TTFont('Poppins', ruta_reg))
        pdfmetrics.registerFont(TTFont('Poppins-Bold', ruta_bold))
        f_reg, f_bold = 'Poppins', 'Poppins-Bold'
    except:
        f_reg, f_bold = 'Helvetica', 'Helvetica-Bold'

    ccpp = get_object_or_404(tbl_CCPP, id=ccpp_id)
    nombre_tecnico = ccpp.tecnico_cabecera if ccpp.tecnico_cabecera else "No asignado"
    
    # --- 2. LÓGICA DE DATOS CORREGIDA ---
    # Obtener cronogramas para el año específico
    cronogramas = tbl_Cronograma.objects.filter(ccpp=ccpp, anios=int(ano) - ccpp.fecha_entrega.year)
    
    # Filtrar unidades que tengan inspección programada en el rango de meses
    unidades_con_inspeccion = []
    
    # Convertir nombres de meses a minúsculas
    mes_inicio_lower = mes_inicio.lower()
    mes_fin_lower = mes_fin.lower()
    
    # Obtener los índices de los meses para el rango
    meses_lista = list(MESES_CAMPOS.keys())
    
    try:
        indice_inicio = meses_lista.index(mes_inicio_lower)
        indice_fin = meses_lista.index(mes_fin_lower)
        
        # Si el mes_fin es anterior a mes_inicio, asumimos que es del mismo año
        if indice_fin < indice_inicio:
            indice_fin = indice_inicio
            
        # Obtener los meses en el rango
        meses_rango = meses_lista[indice_inicio:indice_fin + 1]
        
        # Para cada cronograma, verificar si tiene inspección en algún mes del rango
        for cronograma in cronogramas:
            tiene_inspeccion = False
            
            # Verificar cada mes en el rango
            for mes in meses_rango:
                campo_mes = MESES_CAMPOS[mes]
                valor_mes = getattr(cronograma, campo_mes, None)
                
                # Si el campo no es nulo ni vacío, hay inspección programada
                if valor_mes and valor_mes.strip():
                    tiene_inspeccion = True
                    break
            
            if tiene_inspeccion:
                unidades_con_inspeccion.append(cronograma.unidad_id)
                
    except ValueError as e:
        # Si hay error con los meses, usar todas las unidades (fallback)
        unidades_con_inspeccion = cronogramas.values_list('unidad_id', flat=True)
    
    # Obtener fichas SOLO de las unidades con inspección programada
    fichas = tbl_Ficha.objects.filter(
        FK_FichaUnidad_id__in=unidades_con_inspeccion
    ).order_by('FK_FichaUnidad__orden')

    # --- 3. ESTILOS ---
    color_gris_oscuro = colors.HexColor("#4b5563")
    color_gris_suave = colors.HexColor("#94a3b8")
    color_rojo_enfasis = colors.HexColor("#b91c1c")
    color_fondo_cabecera = colors.HexColor("#f8fafc")

    estilos = {
        'enc_negro': ParagraphStyle('EncNegro', fontSize=10, fontName=f_bold, alignment=TA_CENTER, textColor=color_gris_oscuro),
        'sub_rojo': ParagraphStyle('SubRojo', fontSize=14, fontName=f_bold, textColor=color_rojo_enfasis, alignment=TA_CENTER, leading=16),
        'capitulo': ParagraphStyle('Capitulo', fontSize=8, fontName=f_bold, alignment=TA_CENTER, textColor=color_gris_oscuro),
        'unidad': ParagraphStyle('Unidad', fontSize=7, fontName=f_reg, alignment=TA_CENTER, textColor=color_gris_suave),
        'tecnico_h': ParagraphStyle('TecH', fontSize=7, fontName=f_reg, alignment=TA_LEFT, textColor=color_gris_suave),
        'fecha_h': ParagraphStyle('FecH', fontSize=7, fontName=f_reg, alignment=TA_RIGHT, textColor=color_gris_suave),
        'seccion': ParagraphStyle('Seccion', fontSize=9, fontName=f_bold, textColor=color_gris_oscuro),
        'cuerpo': ParagraphStyle('Cuerpo', fontSize=8, fontName=f_reg, leading=10, textColor=color_gris_oscuro),
        'firma': ParagraphStyle('FirmaMini', fontSize=6, fontName=f_reg, textColor=color_gris_suave),
        'indice_titulo': ParagraphStyle('IndiceTit', fontSize=14, fontName=f_bold, textColor=color_rojo_enfasis, alignment=TA_CENTER),
        'indice_item': ParagraphStyle('IndiceItem', fontSize=9, fontName=f_reg, textColor=color_gris_oscuro),
        'indice_pag': ParagraphStyle('IndicePag', fontSize=9, fontName=f_bold, textColor=color_gris_oscuro, alignment=TA_RIGHT),
        'periodo_titulo': ParagraphStyle('PeriodoTit', fontSize=14, fontName=f_bold, textColor=color_rojo_enfasis, alignment=TA_CENTER),
        'indice_unidad': ParagraphStyle('IndiceUnidad', fontSize=9, fontName=f_reg, textColor=color_gris_oscuro, leftIndent=0),
    }

    # --- 5. CONSTRUCCIÓN CON ÍNDICE ESPECIAL ---
    buffer = io.BytesIO()
    
    # Configuración principal del documento
    # El encabezado del índice ocupa aproximadamente 50mm desde el borde superior
    # Por lo tanto, el margen superior debe ser de 50mm para que el contenido empiece justo debajo
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        topMargin=50*mm,  # Justo debajo del encabezado del índice
        bottomMargin=20*mm, 
        leftMargin=15*mm, 
        rightMargin=15*mm
    )
    historia = []

    # Portada (página 1) - sin encabezado
    historia.append(Spacer(1, 40*mm))
    historia.append(Paragraph("REPORTE DE INSPECCIONES", estilos['periodo_titulo']))
    historia.append(Paragraph(f"{mes_inicio.upper()} a {mes_fin.upper()} {ano}", estilos['periodo_titulo']))
    historia.append(PageBreak())

    # --- ÍNDICE CON ENCABEZADO ESPECIAL (página 2) ---
    if incluir_indice and fichas.exists():
        # Primero calculamos las páginas estimadas
        # Página 1: Portada, Página 2: Índice, Página 3: Primera ficha
        
        pagina_actual = 3  # Después de portada (1) e índice (2)
        indice_entries = []
        
        for ficha in fichas:
            # Texto para el índice: "Nombre de la unidad (PK_titulo)"
            unidad_nombre = ficha.FK_FichaUnidad.unidad if ficha.FK_FichaUnidad else "Sin Unidad"
            texto_indice = f"{unidad_nombre} ({ficha.PK_titulo})"
            indice_entries.append((texto_indice, pagina_actual))
            pagina_actual += 1  # Cada ficha ocupa al menos una página
        
        # Crear tabla para el índice con encabezados
        datos_indice = []
        
        # NO agregamos Spacer aquí porque el margen superior ya está configurado
        # El contenido comenzará automáticamente justo debajo del encabezado dibujado
        
        # Encabezados de la tabla del índice
        datos_indice.append([
            Paragraph("<b>Unidad</b>", ParagraphStyle('IndiceHeader', fontSize=10, fontName=f_bold, textColor=color_gris_oscuro)),
            Paragraph("<b>Pág.</b>", ParagraphStyle('IndiceHeader', fontSize=10, fontName=f_bold, textColor=color_gris_oscuro, alignment=TA_RIGHT))
        ])
        
        # Agregar línea divisoria después del encabezado
        datos_indice.append([Spacer(1, 1*mm), Spacer(1, 1*mm)])
        
        # Agregar cada entrada del índice
        for txt, pagina in indice_entries:
            # Para cada entrada, crear una fila con dos celdas
            datos_indice.append([
                Paragraph(txt, estilos['indice_unidad']),
                Paragraph(str(pagina), ParagraphStyle('IndiceNum', fontSize=9, fontName=f_bold, textColor=color_gris_oscuro, alignment=TA_RIGHT))
            ])
            datos_indice.append([Spacer(1, 2*mm), Spacer(1, 2*mm)])  # Espacio entre filas
        
        # Crear tabla del índice
        t_indice = Table(datos_indice, colWidths=[150*mm, 20*mm])
        
        # Estilo especial para la tabla del índice
        t_indice.setStyle(TableStyle([
            # Línea debajo del encabezado
            ('LINEBELOW', (0, 0), (-1, 0), 0.5, color_gris_suave),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
            # Alineación vertical
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            # Padding
            ('LEFTPADDING', (0, 0), (0, -1), 0),
            ('RIGHTPADDING', (1, 0), (1, -1), 0),
            ('TOPPADDING', (0, 2), (-1, -1), 0),  # A partir de la fila 2 (después del header)
            ('BOTTOMPADDING', (0, 2), (-1, -1), 0),
        ]))
        
        # Agregar la tabla del índice al documento
        historia.append(t_indice)
        historia.append(PageBreak())

    # --- CONTENIDO DE FICHAS CON ENCABEZADO NORMAL ---
    # Para las fichas normales, necesitamos un margen superior diferente
    # porque el encabezado normal es más pequeño que el del índice
    
    for idx, ficha in enumerate(fichas):
        # Marcador de posición
        historia.append(UpdateFichaFlowable(ficha, f"ficha_{ficha.id}"))
        
        historia.append(generar_titulo_seccion("✓ CONTROLES", estilos['seccion'], color_gris_oscuro))
        historia.append(Spacer(1, 2*mm))
        
        datos_controles = [[Paragraph('<b>PERIODO</b>', estilos['cuerpo']), Paragraph('<b>INSPECCION</b>', estilos['cuerpo']), Paragraph('<b>OK</b>', estilos['cuerpo'])]]
        controles = tbl_FichaControl.objects.filter(FK_FichaControl=ficha)
        for c in controles:
            if not c.ocultar:
                insp = c.FK_FichaControlInspeccion
                color_h = insp.color_inspeccion if (insp and insp.color_inspeccion) else "#4b5563"
                datos_controles.append([
                    Paragraph(c.periodo, estilos['cuerpo']),
                    Paragraph(f'<font color="{color_h}"><b>{insp.codigo_inspeccion if insp else ""}</b></font> - {c.control}', estilos['cuerpo']),
                    Paragraph('✓' if c.ejecutado else '', estilos['enc_negro'])
                ])

        t_controles = Table(datos_controles, colWidths=[30*mm, 140*mm, 20*mm], repeatRows=1)
        t_controles.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), color_fondo_cabecera), ('GRID', (0,0), (-1,-1), 0.3, color_gris_suave), ('VALIGN', (0,0), (-1,-1), 'TOP')]))
        historia.append(t_controles)

        for tit, cont in [("✓ PRECAUCIONES", ficha.precaucion), ("✓ PRESCRIPCIONES", ficha.prescripcion), ("✓ PROHIBICIONES", ficha.prohibicion)]:
            if cont:
                historia.append(Spacer(1, 4*mm))
                historia.append(generar_titulo_seccion(tit, estilos['seccion'], color_gris_oscuro))
                historia.append(Paragraph(cont.replace('\n', '<br/>'), estilos['cuerpo']))

        if incluir_firmas:
            historia.append(Spacer(1, 8*mm))
            t_firma = Table([[Paragraph('<b>FECHA INSPECCION</b>', estilos['cuerpo']), Paragraph('<b>CONTROL</b>', estilos['cuerpo']), Paragraph('<b>OBSERVACIONES</b>', estilos['cuerpo'])], ['', Paragraph('Firma', estilos['firma']), '']], colWidths=[40*mm, 50*mm, 100*mm], rowHeights=[None, 12*mm])
            t_firma.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.5, color_gris_oscuro), ('BACKGROUND', (0, 0), (-1, 0), color_fondo_cabecera)]))
            historia.append(KeepTogether([t_firma]))

        if incluir_anexos and ficha.foto and os.path.exists(ficha.foto.path):
            try:
                img = Image(ficha.foto.path, width=150*mm, height=50*mm, kind='proportional')
                img.hAlign = 'CENTER'
                historia.append(KeepTogether([Spacer(1, 8*mm), generar_titulo_seccion("✓ ANEXOS", estilos['seccion'], color_gris_oscuro), Spacer(1, 4*mm), img]))
            except: pass

        if idx < len(fichas) - 1:
            historia.append(PageBreak())

    # --- GENERAR EL DOCUMENTO CON ENCABEZADOS DIFERENCIADOS ---
    def on_first_page(canvas, doc):
        # Para la portada (página 1) - no dibujar encabezado
        # Solo dibujar el número de página si es necesario
        canvas.saveState()
        canvas.setFont(f_reg, 7)
        canvas.drawCentredString(A4[0]/2, 10*mm, f"Página {canvas.getPageNumber()}")
        canvas.restoreState()
    
    def on_later_pages(canvas, doc):
        """Manejador para páginas posteriores con encabezado diferenciado"""
        # Para la página del índice (página 2)
        if canvas.getPageNumber() == 2 and incluir_indice:
            # Dibujar el encabezado del índice
            dibujar_encabezado_pagina_indice(canvas, doc)
            # Luego dibujar el pie de página del índice
            dibujar_pie_pagina_indice(canvas, doc)
        else:
            # Para las demás páginas usar el encabezado normal
            dibujar_elementos_fijos(canvas, doc)
    
    # Generar el documento
    doc.build(historia, onFirstPage=on_first_page, onLaterPages=on_later_pages)
    
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=False, filename=f'Reporte_{ccpp.nombre}.pdf')












































