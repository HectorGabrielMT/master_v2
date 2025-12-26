from appAdministrador.models import tbl_Notificacion, tbl_CCPP, tbl_inspeccion



import os
from datetime import datetime
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.http import HttpResponse

# ReportLab Imports
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

def reporte_notificaciones_ccpp_pdf(request, ccpp_id, anio, mes_inicio, mes_fin, mostrar_remitentes, mostrar_respuesta):
    try:
        # 1. PREPARACIÓN DE DATOS
        mostrar_remitentes = str(mostrar_remitentes).lower() == 'true'
        mostrar_respuesta = str(mostrar_respuesta).lower() == 'true'
        ccpp = get_object_or_404(tbl_CCPP, id=ccpp_id)
        
        # Nombre del técnico desde el modelo
        nombre_tecnico = ccpp.tecnico_cabecera if ccpp.tecnico_cabecera else ""
        
        try:
            anio_calendario = int(anio)
        except (ValueError, TypeError):
            anio_calendario = datetime.now().year

        response = HttpResponse(content_type='application/pdf')
        nombre_archivo = f"Reporte_{ccpp.nombre}_{anio_calendario}.pdf".replace(" ", "_")
        response['Content-Disposition'] = f'inline; filename="{nombre_archivo}"'

        # CONFIGURACIÓN DEL DOCUMENTO
        # Reducimos topMargin de 1.5 a 1.2 para acercar la tabla al encabezado
        doc = SimpleDocTemplate(
            response,
            pagesize=letter,
            leftMargin=30,
            rightMargin=30,
            topMargin=1.2 * inch,  
            bottomMargin=0.8 * inch
        )

        elementos = []
        estilos = getSampleStyleSheet()
        estilo_celda = estilos['Normal'].clone('estilo_celda')
        estilo_celda.fontSize, estilo_celda.leading = 7, 8

        # --- FUNCIÓN DE DIBUJO (Encabezado y Pie de Página) ---
        def dibujar_hoja(canvas, doc):
            canvas.saveState()
            
            # --- PIE DE PÁGINA (Fecha | Nombre Técnico | Página) ---
            fecha_hoy = datetime.now().strftime("%d/%m/%Y")
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(colors.grey)
            
            # Izquierda: Fecha
            canvas.drawString(doc.leftMargin, 0.5 * inch, f"Fecha: {fecha_hoy}")
            
            # Centro: Solo el nombre del Técnico (Etiqueta "Responsable:" eliminada)
            canvas.drawCentredString(letter[0] / 2, 0.5 * inch, f"{nombre_tecnico}")
            
            # Derecha: Numeración
            canvas.drawRightString(letter[0] - doc.rightMargin, 0.5 * inch, f"Página {canvas.getPageNumber()}")
            
            # --- ENCABEZADO (Aparece a partir de la página 2) ---
            if canvas.getPageNumber() > 1:
                st_title = estilos['Normal'].clone('st_tit')
                st_title.fontSize, st_title.fontName = 12, 'Helvetica-Bold'
                st_ccpp = estilos['Normal'].clone('st_ccpp')
                st_ccpp.fontSize, st_ccpp.fontName, st_ccpp.textColor = 11, 'Helvetica-Bold', colors.maroon
                st_sub = estilos['Normal'].clone('st_sub')
                st_sub.fontSize, st_sub.fontName, st_sub.textColor = 9, 'Helvetica-Bold', colors.grey

                ruta_logo = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo.png')
                try:
                    img_logo = Image(ruta_logo, width=0.7*inch, height=0.7*inch) if os.path.exists(ruta_logo) else Paragraph("LOGO", estilo_celda)
                except:
                    img_logo = Paragraph("LOGO", estilo_celda)
                
                periodo_txt = request.GET.get('periodo_nombre', 'ANUAL').upper()
                datos_h = [[img_logo, [
                    Paragraph("CONTROL LIBRO DEL EDIFICIO", st_title),
                    Paragraph(f"{ccpp.id_ccpp} - {ccpp.nombre.upper()}", st_ccpp),
                    Paragraph(f"AÑO {anio_calendario} | NOTIFICACIONES - {periodo_txt}", st_sub)
                ]]]
                
                header_table = Table(datos_h, colWidths=[0.8*inch, 5.7*inch])
                header_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('LEFTPADDING', (0,0), (-1,-1), 0)]))
                
                w, h = header_table.wrap(doc.width, doc.topMargin)
                # Ajustamos la posición vertical para que el encabezado esté pegado al contenido
                header_table.drawOn(canvas, doc.leftMargin, doc.height + doc.bottomMargin + 0.3 * inch)
                
                canvas.setStrokeColor(colors.orange)
                canvas.setLineWidth(0.5)
                y_line = doc.height + doc.bottomMargin + 0.28 * inch
                canvas.line(doc.leftMargin, y_line, doc.width + doc.leftMargin, y_line)

            canvas.restoreState()

        # --- 2. CONSTRUCCIÓN DE LA PORTADA ---
        elementos.append(Spacer(1, 0.5 * inch))
        
        ruta_logo_portada = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo.png')
        if os.path.exists(ruta_logo_portada):
            img_p = Image(ruta_logo_portada, width=1.5*inch, height=1.5*inch)
            img_p.hAlign = 'CENTER'
            elementos.append(img_p)
        
        elementos.append(Spacer(1, 0.3 * inch))
        
        estilo_p_1 = estilos['Normal'].clone('p1')
        estilo_p_1.alignment, estilo_p_1.fontSize, estilo_p_1.fontName = 1, 22, 'Helvetica-Bold'
        estilo_p_2 = estilos['Normal'].clone('p2')
        estilo_p_2.alignment, estilo_p_2.fontSize, estilo_p_2.fontName, estilo_p_2.textColor = 1, 18, 'Helvetica-Bold', colors.maroon
        estilo_p_3 = estilos['Normal'].clone('p3')
        estilo_p_3.alignment, estilo_p_3.fontSize, estilo_p_3.textColor = 1, 12, colors.grey

        elementos.append(Paragraph("CONTROL LIBRO DEL EDIFICIO", estilo_p_1))
        elementos.append(Spacer(1, 0.1 * inch))
        elementos.append(Paragraph(f"{ccpp.id_ccpp} - {ccpp.nombre.upper()}", estilo_p_2))
        elementos.append(Spacer(1, 0.1 * inch))
        elementos.append(Paragraph(f"AÑO {anio_calendario}", estilo_p_3))
        
        elementos.append(Spacer(1, 0.5 * inch))

        ruta_img_reporte = os.path.join(settings.BASE_DIR, 'static', 'img', 'img_reporte.png')
        if os.path.exists(ruta_img_reporte):
            img_central = Image(ruta_img_reporte, width=5.5*inch, height=4*inch)
            img_central.hAlign = 'CENTER'
            elementos.append(img_central)
        
        elementos.append(Spacer(1, 0.4 * inch))
        for w_line in [4*inch, 3*inch, 2*inch, 1*inch]:
            linea_naranja = Table([['']], colWidths=[w_line], rowHeights=[2])
            linea_naranja.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.orange), ('ALIGN', (0,0), (-1,-1), 'CENTER')]))
            elementos.append(linea_naranja)
            elementos.append(Spacer(1, 5))

        elementos.append(PageBreak())

        # --- 3. TABLA DE CONTENIDO ---
        nombres_meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
        try:
            periodo_query = [m.capitalize() for m in nombres_meses[int(mes_inicio)-1:int(mes_fin)]]
        except:
            periodo_query = [m.capitalize() for m in nombres_meses]

        titulos = [Paragraph(f"<b>{h}</b>", estilo_celda) for h in ['DOC', 'UNIDAD', 'MES', 'ENVIADO', 'RESPONDIDO', 'INSP.']]
        data_tabla = [titulos]
        estilos_tabla = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F2E2D2')),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.orange),
            ('ALIGN', (2, 0), (4, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]

        # Carga de datos
        inspecciones_map = {str(i.id): (i.codigo_inspeccion, i.color_inspeccion) for i in tbl_inspeccion.objects.all()}
        anio_rel = anio_calendario - (ccpp.fecha_entrega.year if ccpp.fecha_entrega else anio_calendario)

        notificaciones = tbl_Notificacion.objects.filter(
            FK_cronograma__ccpp=ccpp, FK_cronograma__anios=anio_rel,
            PK_mes__in=periodo_query + [m.lower() for m in periodo_query] + [m.upper() for m in periodo_query]
        ).select_related('FK_cronograma', 'FK_cronograma__unidad').order_by('fecha')

        if not notificaciones.exists():
            data_tabla.append([Paragraph("No hay datos registrados.", estilo_celda)] * 6)
            estilos_tabla.append(('SPAN', (0, 1), (5, 1)))
        else:
            for n in notificaciones:
                crono = n.FK_cronograma
                m_ref = n.PK_mes.lower()
                id_i = next((str(getattr(crono, m, "")) for m in nombres_meses if m in m_ref), "")
                cod, col = inspecciones_map.get(id_i, (id_i, "#000000"))
                col = col if str(col).startswith('#') else "#000000"

                data_tabla.append([
                    Paragraph(crono.unidad.doc or "--", estilo_celda),
                    Paragraph(crono.unidad.unidad, estilo_celda),
                    Paragraph(n.PK_mes[:3].upper(), estilo_celda),
                    Paragraph(n.fecha.strftime('%d-%m-%Y %I:%M %p') if n.fecha else "--", estilo_celda),
                    Paragraph(n.FechaResp.strftime('%d-%m-%Y') if n.FechaResp else "--", estilo_celda),
                    Paragraph(f'<b><font color="{col}">{cod}</font></b>', estilo_celda.clone('c', alignment=1))
                ])

                if mostrar_remitentes or mostrar_respuesta:
                    det = []
                    if mostrar_remitentes:
                        for f, v in [('Para', n.para), ('Cc', n.cc), ('Cco', n.cco)]:
                            if v: det.append(Paragraph(f"<b>{f}:</b> {v}", estilo_celda.clone('b', textColor=colors.HexColor('#003399'))))
                    if mostrar_respuesta:
                        for f, v in [('Revision', n.RespRevision), ('Controlador', n.RespControlador), ('Vía', n.RespVia), ('Observacion', n.RespObservacion)]:
                            if v: det.append(Paragraph(f"<i>{f}:</i> {v}", estilo_celda.clone('g', textColor=colors.HexColor('#4D4D4D'))))
                    if det:
                        data_tabla.append([det, '', '', '', '', ''])
                        idx = len(data_tabla) - 1
                        estilos_tabla.extend([('SPAN', (0, idx), (5, idx)), ('BOTTOMPADDING', (0, idx), (5, idx), 5)])

        tabla_final = Table(data_tabla, colWidths=[45, 260, 40, 95, 80, 40], repeatRows=1)
        tabla_final.setStyle(TableStyle(estilos_tabla))
        elementos.append(tabla_final)

        # 4. CONSTRUCCIÓN FINAL
        doc.build(elementos, onFirstPage=dibujar_hoja, onLaterPages=dibujar_hoja)
        return response

    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)










