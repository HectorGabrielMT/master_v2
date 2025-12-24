from appAdministrador.models import tbl_Ficha, tbl_FichaControl, tbl_CCPP, tbl_CCPP_Unidad, tbl_Cronograma
from django.shortcuts import render
from django.shortcuts import render, get_object_or_404


def vista_reporte_ccpp(request, ccpp_id):
    ccpp = get_object_or_404(tbl_CCPP, id=ccpp_id)
    contexto = {
        'ccpp': ccpp
    }
    return render(request, 'gestion/reportes/reportes.html', contexto)














import io
import os
from django.conf import settings
from django.http import FileResponse
from django.contrib.staticfiles import finders

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, 
    TableStyle, Image, KeepTogether
)
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def obtener_tecnico_cabecera(ccpp_id):
    """
    Extrae la primera línea del campo tecnico_cabecera del modelo tbl_CCPP.
    """
    try:
        registro = tbl_CCPP.objects.get(id=ccpp_id)
        contenido = registro.tecnico_cabecera
        
        if contenido:
            return contenido.splitlines()[0]
        return "No especificado"
    except Exception:
        return "No disponible"


def generar_titulo_seccion(texto, estilo, color_gris):
    """
    Crea una tabla con el título de sección y una línea inferior gruesa.
    """
    tabla = Table([[Paragraph(f"<b>{texto}</b>", estilo)]], colWidths=[194*mm])
    tabla.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, 0), 1.5, color_gris),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
    ]))
    return tabla


def exportar_ficha_pdf(request, ficha_id, ccpp_id):
    # --- 1. CONFIGURACIÓN DE FUENTES Y RECURSOS ---
    try:
        ruta_fuente_reg = finders.find('fonts/Poppins-Regular.ttf') or \
            os.path.join(settings.BASE_DIR, 'static/fonts/Poppins-Regular.ttf')
        ruta_fuente_bold = finders.find('fonts/Poppins-Bold.ttf') or \
            os.path.join(settings.BASE_DIR, 'static/fonts/Poppins-Bold.ttf')
        
        pdfmetrics.registerFont(TTFont('Poppins', ruta_fuente_reg))
        pdfmetrics.registerFont(TTFont('Poppins-Bold', ruta_fuente_bold))
        f_reg, f_bold = 'Poppins', 'Poppins-Bold'
    except Exception:
        f_reg, f_bold = 'Helvetica', 'Helvetica-Bold'

    # --- 2. OBTENCIÓN DE DATOS CON CONTROL DE ERRORES ---
    try:
        ficha = tbl_Ficha.objects.get(id=ficha_id)
        controles = tbl_FichaControl.objects.filter(FK_FichaControl=ficha)
        nombre_tecnico = obtener_tecnico_cabecera(ccpp_id)
    except Exception as e:
        return FileResponse(
            io.BytesIO(f"Error de base de datos: {str(e)}".encode()), 
            content_type='text/plain'
        )

    # --- 3. DEFINICIÓN DE ESTILO VISUAL ---
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

    # --- 4. FUNCIÓN DEL ENCABEZADO PERSISTENTE ---
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

    # --- 5. CONSTRUCCIÓN DEL CONTENIDO (STORY) ---
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, topMargin=35*mm, bottomMargin=10*mm,
        leftMargin=8*mm, rightMargin=8*mm
    )
    historia = [Spacer(1, 2*mm)]

    # Sección de Controles
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

    # Secciones Informativas
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

    # Cuadro de Firma
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

    # Anexos
    if ficha.foto and os.path.exists(ficha.foto.path):
        historia.append(KeepTogether([
            Spacer(1, 6*mm),
            generar_titulo_seccion("✓ ANEXOS", estilo_seccion, color_gris_oscuro),
            Spacer(1, 3*mm),
            Image(ficha.foto.path, width=175*mm, height=85*mm, kind='proportional'),
            Paragraph(os.path.basename(ficha.foto.name), estilo_unidad_gris)
        ]))

    # --- 6. GENERACIÓN DEL DOCUMENTO ---
    try:
        doc.build(
            historia, 
            onFirstPage=dibujar_elementos_fijos, 
            onLaterPages=dibujar_elementos_fijos
        )
    except Exception as e:
        return FileResponse(
            io.BytesIO(f"Error al construir PDF: {str(e)}".encode()), 
            content_type='text/plain'
        )

    buffer.seek(0)
    return FileResponse(
        buffer, 
        as_attachment=False, 
        filename=f'Ficha_{ficha.id}.pdf'
    )
















