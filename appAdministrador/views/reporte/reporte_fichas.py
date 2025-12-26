from appAdministrador.models import *
import io
import os
from django.conf import settings
from django.http import FileResponse
from django.contrib.staticfiles import finders

# ReportLab
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, 
    TableStyle, Image, KeepTogether, PageBreak
)
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

# PyPDF2
from PyPDF2 import PdfWriter, PdfReader

# --- 1. CONFIGURACIÓN DE FUENTES ---

def registrar_fuentes():
    try:
        ruta_reg = finders.find('fonts/Poppins-Regular.ttf') or \
                   os.path.join(settings.BASE_DIR, 'static/fonts/Poppins-Regular.ttf')
        ruta_bold = finders.find('fonts/Poppins-Bold.ttf') or \
                    os.path.join(settings.BASE_DIR, 'static/fonts/Poppins-Bold.ttf')
        
        pdfmetrics.registerFont(TTFont('Poppins', ruta_reg))
        pdfmetrics.registerFont(TTFont('Poppins-Bold', ruta_bold))
        return 'Poppins', 'Poppins-Bold'
    except:
        return 'Helvetica', 'Helvetica-Bold'

f_reg, f_bold = registrar_fuentes()

# --- 2. FUNCIONES DE APOYO ---

def obtener_tecnico_cabecera(ccpp_id):
    try:
        registro = tbl_CCPP.objects.get(id=ccpp_id)
        if registro.tecnico_cabecera:
            return registro.tecnico_cabecera.splitlines()[0]
        return "No especificado"
    except: 
        return "No disponible"

def generar_titulo_seccion(texto, estilo, color_gris):
    tabla = Table([[Paragraph(f"<b>{texto}</b>", estilo)]], colWidths=[194*mm])
    tabla.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, 0), 1.5, color_gris),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
    ]))
    return tabla

# --- 3. COMPONENTES DEL REPORTE (PORTADA, INDICE, FIRMAS) ---

def generar_pdf_portada(ccpp_nombre):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    estilo_t = ParagraphStyle('Port', fontSize=26, fontName=f_bold, alignment=TA_CENTER)
    
    historia = [
        Spacer(1, 80*mm),
        Paragraph("LIBRO DEL EDIFICIO", estilo_t),
        Spacer(1, 15*mm),
        Paragraph(ccpp_nombre.upper(), estilo_t),
        Spacer(1, 20*mm),
        Paragraph("REPORTE CONSOLIDADO DE FICHAS", estilo_t)
    ]
    doc.build(historia)
    buffer.seek(0)
    return buffer

def generar_pdf_indice(ccpp_nombre, datos_indice):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20*mm)
    est_t = ParagraphStyle('T', fontSize=18, fontName=f_reg, alignment=TA_CENTER, spaceAfter=20)
    est_h = ParagraphStyle('H', fontSize=10, fontName=f_reg, textColor=colors.whitesmoke)
    est_c = ParagraphStyle('C', fontSize=9, fontName=f_reg)

    historia = [Paragraph(f"INDICE DE FICHAS - {ccpp_nombre.upper()}", est_t), Spacer(1, 10*mm)]
    tabla_datos = [[Paragraph("UNIDAD / DOCUMENTO", est_h), Paragraph("PAG", est_h)]]
    
    for item in datos_indice:
        tabla_datos.append([
            Paragraph(f"{item['unidad']} - {item['titulo']}", est_c),
            Paragraph(str(item['pagina']), est_c)
        ])

    tabla = Table(tabla_datos, colWidths=[165*mm, 15*mm])
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4b5563")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    historia.append(tabla)
    doc.build(historia)
    buffer.seek(0)
    return buffer

def generar_pdf_firmas_final(incluir_firmas_final=True):
    """
    Genera la página de firmas final.
    
    Args:
        incluir_firmas_final: Booleano que indica si se incluyen los cuadros de firma
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=30*mm, leftMargin=15*mm, rightMargin=15*mm)
    est_legal = ParagraphStyle('Legal', fontName=f_reg, fontSize=9, leading=14, alignment=TA_JUSTIFY, textColor=colors.HexColor("#4b5563"))
    
    historia = [
        Paragraph("EL PRESENTE DOCUMENTO ES INFORMATIVO EN CUANTO A LAS FICHAS APORTADAS Y QUE CORRESPONDEN CON EL PERIODO INDICADO EN EL INFORME.", est_legal),
        Spacer(1, 6*mm),
        Paragraph("ESTAS REVISIONES HAN PODIDO EFECTUARSE TOTAL O PARCIALMENTE DEPENDIENDO DE LA OBLIGATORIEDAD DE CADA UNA DE ELLAS. ES ACONSEJABLE QUE TODAS Y CADA UNA DE ELLAS SE COMPRUEBE AL MENOS VISUALMENTE Y SI ES POSIBLE APORTAR UN DOCUMENTO FOTOGRÁFICO.", est_legal),
        Spacer(1, 6*mm),
        Paragraph("EL DOCUMENTO VÁLIDO PARA INCLUIRLO EN LA DOCUMENTACIÓN DE MANTENIMIENTO DEL EDIFICIO SERÁ EL RESUMEN ANUAL QUE DEBERÁ SER FIRMADO POR EL TÉCNICO COMPETENTE, LA ADMINISTRACIÓN Y EL PRESIDENTE.", est_legal),
        Spacer(1, 15*mm),
    ]
    
    # Solo incluir los cuadros de firma si se solicita
    if incluir_firmas_final:
        historia.append(Paragraph("ESTE DOCUMENTO SE FIRMA EL __________________________", est_legal))
        historia.append(Spacer(1, 50*mm))
        
        est_f_label = ParagraphStyle('FLab', fontName=f_reg, fontSize=8, alignment=TA_CENTER)
        data_firmas = [
            ["________________________", "________________________", "________________________"],
            [Paragraph("TÉCNICO ASIGNADO", est_f_label), Paragraph("ADMINISTRACIÓN", est_f_label), Paragraph("PRESIDENTE CP.", est_f_label)]
        ]
        t_firmas = Table(data_firmas, colWidths=[60*mm, 60*mm, 60*mm])
        t_firmas.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('BOTTOMPADDING', (0,0), (-1,0), 10)]))
        historia.append(t_firmas)
    
    doc.build(historia)
    buffer.seek(0)
    return buffer

# --- 4. MOTOR DE FICHA MODIFICADO (CON FORMATO IDÉNTICO A LA APP) ---

def generar_pdf_ficha_individual(ficha, ccpp_id, incluir_anexo=True, incluir_firma_ficha=True):
    """
    Genera el PDF de una ficha individual con formato idéntico al de la app.
    
    Args:
        ficha: Objeto de la ficha
        ccpp_id: ID del CCPP
        incluir_anexo: Booleano que indica si se incluye la imagen/anexo
        incluir_firma_ficha: Booleano que indica si se incluye la sección de firma con tres cuadros
    """
    # --- DEFINICIÓN DE ESTILO VISUAL (IGUAL A LA APP) ---
    color_gris_oscuro = colors.HexColor("#4b5563")
    color_gris_suave = colors.HexColor("#94a3b8")
    color_rojo_enfasis = colors.HexColor("#b91c1c")
    color_fondo_cabecera = colors.HexColor("#f8fafc")

    estilo_encabezado_negro = ParagraphStyle(
        'EncNegro', fontSize=10, fontName=f_bold, 
        alignment=TA_CENTER, textColor=color_gris_oscuro
    )
    estilo_subtitulo_rojo = ParagraphStyle(
        'SubRojo', fontSize=15, fontName=f_bold, 
        textColor=color_rojo_enfasis, alignment=TA_CENTER, leading=17
    )
    estilo_capitulo = ParagraphStyle(
        'Capitulo', fontSize=9, fontName=f_bold, 
        alignment=TA_CENTER, textColor=color_gris_oscuro
    )
    estilo_unidad_gris = ParagraphStyle(
        'Unidad', fontSize=7, fontName=f_reg, 
        alignment=TA_CENTER, textColor=color_gris_suave
    )
    estilo_tecnico_izq = ParagraphStyle(
        'TecIzq', fontSize=7, fontName=f_reg, 
        alignment=TA_LEFT, textColor=color_gris_suave
    )
    estilo_fecha_der = ParagraphStyle(
        'FecDer', fontSize=7, fontName=f_reg, 
        alignment=TA_RIGHT, textColor=color_gris_suave
    )
    estilo_seccion = ParagraphStyle(
        'Seccion', fontSize=9, fontName=f_bold, textColor=color_gris_oscuro
    )
    estilo_cuerpo = ParagraphStyle(
        'Cuerpo', fontSize=8.5, fontName=f_reg, 
        leading=11, textColor=color_gris_oscuro
    )
    estilo_firma_mini = ParagraphStyle(
        'FirmaMini', fontSize=6, fontName=f_reg, 
        textColor=color_gris_suave, alignment=TA_LEFT
    )

    nombre_tecnico = obtener_tecnico_cabecera(ccpp_id)
    controles = tbl_FichaControl.objects.filter(FK_FichaControl=ficha)

    # --- FUNCIÓN DEL ENCABEZADO PERSISTENTE (IGUAL A LA APP) ---
    def dibujar_elementos_fijos(canvas, doc):
        canvas.saveState()
        try:
            ruta_logo = finders.find('img/logo.png') or \
                os.path.join(settings.BASE_DIR, 'static/img/logo.png')
            img_izq = Image(ruta_logo, width=15*mm, height=15*mm) if \
                os.path.exists(ruta_logo) else Paragraph("", estilo_cuerpo)
            
            img_der = Image(ficha.logo.path, width=15*mm, height=15*mm) if \
                ficha.logo and os.path.exists(ficha.logo.path) else ""
        except Exception:
            img_izq = img_der = ""

        bloque_central = [
            Paragraph("CONTROL LIBRO DEL EDIFICIO", estilo_encabezado_negro),
            Paragraph(
                ficha.FK_FichaUnidad.doc if ficha.FK_FichaUnidad else "S/D", 
                estilo_subtitulo_rojo
            ),
            Paragraph(
                f"<b>{ficha.FK_FichaUnidad.capitulo if ficha.FK_FichaUnidad else ''}</b>", 
                estilo_capitulo
            ),
            Paragraph(
                ficha.FK_FichaUnidad.unidad if ficha.FK_FichaUnidad else "", 
                estilo_unidad_gris
            )
        ]

        tabla_header = Table(
            [[img_izq, bloque_central, img_der]], 
            colWidths=[25*mm, 144*mm, 25*mm]
        )
        tabla_header.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LINEBELOW', (0, 0), (-1, 0), 1.5, color_gris_oscuro),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1*mm),
        ]))
        
        tabla_header.wrapOn(canvas, doc.width, doc.topMargin)
        y_pos_base = doc.height + doc.topMargin - 18*mm
        tabla_header.drawOn(canvas, doc.leftMargin, y_pos_base)

        # Dibujo de Técnico y Fecha bajo la línea
        info_tecnica = [[
            Paragraph(f"Técnico Cabecera: {nombre_tecnico}", estilo_tecnico_izq),
            Paragraph(
                f"Fecha: {ficha.fecha_creacion.strftime('%d/%m/%Y')}", 
                estilo_fecha_der
            )
        ]]
        tabla_info = Table(info_tecnica, colWidths=[114*mm, 80*mm])
        tabla_info.setStyle(TableStyle([
            ('LEFTPADDING', (0, 0), (-1, -1), 0), 
            ('RIGHTPADDING', (0, 0), (-1, -1), 0)
        ]))
        tabla_info.wrapOn(canvas, 194*mm, 5*mm)
        tabla_info.drawOn(canvas, doc.leftMargin, y_pos_base - 6*mm)
        
        canvas.restoreState()

    # --- CONSTRUCCIÓN DEL CONTENIDO (STORY) ---
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, topMargin=35*mm, bottomMargin=10*mm,
        leftMargin=8*mm, rightMargin=8*mm
    )
    historia = [Spacer(1, 2*mm)]

    # Sección de Controles (SIEMPRE)
    historia.append(generar_titulo_seccion("✓ CONTROLES", estilo_seccion, color_gris_oscuro))
    historia.append(Spacer(1, 2*mm))
    
    datos_controles = [[
        Paragraph('<b>PERIODO</b>', estilo_cuerpo), 
        Paragraph('<b>INSPECCIÓN</b>', estilo_cuerpo), 
        Paragraph('<b>OK</b>', estilo_cuerpo)
    ]]
    
    for c in controles:
        if not c.ocultar:
            estilo_fila = estilo_cuerpo
            if c.opacar:
                estilo_fila = ParagraphStyle('Op', parent=estilo_cuerpo, textColor=color_gris_suave)
            
            insp = c.FK_FichaControlInspeccion
            color_cod = color_gris_suave if c.opacar else (
                insp.color_inspeccion if insp else color_gris_oscuro
            )
            cod_ins = insp.codigo_inspeccion if insp else "N/A"
            nom_ins = f"<u>{insp.nombre_inspeccion.upper()}</u>" if insp else "<u>S/I</u>"
            
            prefijo = f'<font color="{color_cod}"><b>{cod_ins}</b></font> - ' \
                      f'<font color="{color_gris_oscuro}">{nom_ins}:</font>'
            
            contenido_txt = c.control.replace('\n', '<br/>')
            check = '✓' if c.ejecutado else ''
            
            datos_controles.append([
                Paragraph(c.periodo, estilo_fila),
                Paragraph(f"{prefijo} {contenido_txt}", estilo_fila),
                Paragraph(f"<b>{check}</b>", estilo_encabezado_negro)
            ])

    tabla_c = Table(datos_controles, colWidths=[34*mm, 140*mm, 20*mm], repeatRows=1)
    tabla_c.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), color_fondo_cabecera),
        ('GRID', (0, 0), (-1, -1), 0.3, color_gris_suave),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (2, 0), (2, -1), 'CENTER'),
    ]))
    historia.append(tabla_c)

    # Secciones Informativas (SIEMPRE)
    secciones = [
        ("✓ PRECAUCIONES", ficha.precaucion),
        ("✓ PRESCRIPCIONES", ficha.prescripcion),
        ("✓ PROHIBICIONES", ficha.prohibicion)
    ]
    for titulo, contenido in secciones:
        if contenido:
            historia.append(KeepTogether([
                Spacer(1, 4*mm),
                generar_titulo_seccion(titulo, estilo_seccion, color_gris_oscuro),
                Spacer(1, 1*mm),
                Paragraph(contenido.replace('\n', '<br/>'), estilo_cuerpo)
            ]))

    # Cuadro de Firma (CONDICIONAL)
    if incluir_firma_ficha:
        historia.append(Spacer(1, 5*mm))
        datos_firma = [
            [
                Paragraph('<b>FECHA INSPECCIÓN</b>', estilo_cuerpo), 
                Paragraph('<b>CONTROL</b>', estilo_cuerpo), 
                Paragraph('<b>OBSERVACIONES</b>', estilo_cuerpo)
            ],
            ['', Paragraph('Firma', estilo_firma_mini), '']
        ]
        tabla_firma = Table(
            datos_firma, 
            colWidths=[44*mm, 50*mm, 100*mm], 
            rowHeights=[None, 24*mm]
        )
        tabla_firma.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, color_gris_oscuro),
            ('VALIGN', (0, 1), (-1, 1), 'TOP'),
            ('BACKGROUND', (0, 0), (-1, 0), color_fondo_cabecera),
        ]))
        historia.append(KeepTogether([tabla_firma]))

    # Anexos (CONDICIONAL)
    if incluir_anexo and ficha.foto and os.path.exists(ficha.foto.path):
        historia.append(KeepTogether([
            Spacer(1, 6*mm),
            generar_titulo_seccion("✓ ANEXOS", estilo_seccion, color_gris_oscuro),
            Spacer(1, 3*mm),
            Image(ficha.foto.path, width=175*mm, height=85*mm, kind='proportional'),
            Paragraph(os.path.basename(ficha.foto.name), estilo_unidad_gris)
        ]))

    # --- GENERACIÓN DEL DOCUMENTO ---
    try:
        doc.build(
            historia, 
            onFirstPage=dibujar_elementos_fijos, 
            onLaterPages=dibujar_elementos_fijos
        )
    except Exception as e:
        # En caso de error, devolver un PDF vacío con mensaje de error
        error_buffer = io.BytesIO()
        error_doc = SimpleDocTemplate(error_buffer, pagesize=A4)
        error_style = ParagraphStyle('Error', fontSize=10, fontName=f_reg)
        error_doc.build([Paragraph(f"Error al generar ficha: {str(e)}", error_style)])
        error_buffer.seek(0)
        return error_buffer

    buffer.seek(0)
    return buffer

# --- 5. VISTA DE EXPORTACIÓN CONSOLIDADA MODIFICADA ---

def reporte_ccpp_final(request, ccpp_id):
    ccpp = tbl_CCPP.objects.get(id=ccpp_id)
    unidades_rel = tbl_CCPP_Unidad.objects.filter(ccpp=ccpp).select_related('unidad')
    
    # Obtener parámetros del GET
    incluir_portada = request.GET.get('portada', 'true').lower() == 'true'
    incluir_indice = request.GET.get('indice', 'true').lower() == 'true'
    incluir_anexo = request.GET.get('anexo', 'true').lower() == 'true'
    incluir_firma_ficha = request.GET.get('firma_ficha', 'true').lower() == 'true'
    incluir_firmas_final = request.GET.get('firmas_final', 'true').lower() == 'true'

    fichas_bufs = []
    datos_indice = []
    
    # Calcular página inicial según qué elementos se incluyen
    pagina_actual = 1  # Inicializar contador
    
    if incluir_portada:
        pagina_actual += 1  # Portada ocupa página 1
    
    if incluir_indice:
        pagina_actual += 1  # Índice ocupa página siguiente
    
    # Ahora pagina_actual apunta a la primera página de fichas
    
    # 1. Generar fichas y recolectar datos del índice (si se incluye índice)
    for rel in unidades_rel:
        fichas = tbl_Ficha.objects.filter(FK_FichaUnidad=rel.unidad)
        for f in fichas:
            # Pasar los parámetros a la función de generación de ficha
            buf = generar_pdf_ficha_individual(f, ccpp_id, incluir_anexo, incluir_firma_ficha)
            num_p = len(PdfReader(buf).pages)
            
            # Solo recolectar datos para el índice si se va a incluir
            if incluir_indice:
                datos_indice.append({
                    'unidad': rel.unidad.unidad, 
                    'titulo': f.FK_FichaUnidad.doc if f.FK_FichaUnidad else "S/D", 
                    'pagina': pagina_actual
                })
            
            fichas_bufs.append(buf)
            pagina_actual += num_p

    # 2. Unión de documentos con PyPDF2
    escritor = PdfWriter()
    
    # Portada (condicional)
    if incluir_portada:
        for p in PdfReader(generar_pdf_portada(ccpp.nombre)).pages: 
            escritor.add_page(p)
    
    # Índice (condicional)
    if incluir_indice and datos_indice:
        for p in PdfReader(generar_pdf_indice(ccpp.nombre, datos_indice)).pages: 
            escritor.add_page(p)
    
    # Fichas (siempre)
    for b in fichas_bufs:
        for p in PdfReader(b).pages: 
            escritor.add_page(p)
    
    # Página de firmas final (condicional)
    if incluir_firmas_final:
        for p in PdfReader(generar_pdf_firmas_final(incluir_firmas_final)).pages: 
            escritor.add_page(p)

    # 3. Aplicar numeración (Overlay)
    total_total = len(escritor.pages)
    buf_num = io.BytesIO()
    can = canvas.Canvas(buf_num, pagesize=A4)
    for i in range(1, total_total + 1):
        can.setFont("Helvetica", 8)
        can.drawRightString(200*mm, 10*mm, f"Página {i} de {total_total}")
        can.showPage()
    can.save()
    
    num_reader = PdfReader(io.BytesIO(buf_num.getvalue()))
    final_writer = PdfWriter()
    for i in range(total_total):
        page = escritor.pages[i]
        page.merge_page(num_reader.pages[i])
        final_writer.add_page(page)

    salida = io.BytesIO()
    final_writer.write(salida)
    salida.seek(0)
    
    return FileResponse(salida, filename=f"Reporte_{ccpp.nombre}.pdf", content_type='application/pdf')