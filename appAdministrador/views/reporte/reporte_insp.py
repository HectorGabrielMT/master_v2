from appAdministrador.models import tbl_Notificacion, tbl_CCPP, tbl_inspeccion, tbl_Cronograma, tbl_Unidad





import os
from datetime import datetime
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.db.models import Q

# Modelos del proyecto
from appAdministrador.models import (
    tbl_Notificacion, tbl_CCPP, tbl_inspeccion, 
    tbl_Cronograma, tbl_Unidad, tbl_CCPP_Unidad
)

# ReportLab Imports
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

def reporte_inspecciones_ccpp_pdf(request, ccpp_id, anio):
    try:
        # 1. PREPARACIÓN DE DATOS Y PARÁMETROS URL
        ccpp = get_object_or_404(tbl_CCPP, id=ccpp_id)
        nombre_tecnico = ccpp.tecnico_cabecera if ccpp.tecnico_cabecera else ""
        
        try:
            anio_calendario = int(anio)
        except (ValueError, TypeError):
            anio_calendario = datetime.now().year

        # Parámetros desde el Modal
        filtro = request.GET.get('filtro', 'todas')
        periodo_raw = request.GET.get('periodo', '1-12')
        orden = request.GET.get('orden', 'orden')

        # Listas de control para meses
        meses_full = [
            'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 
            'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
        ]
        meses_abrv_full = ['ENE', 'FEB', 'MAR', 'ABR', 'MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC']

        # Procesar recorte de meses según el periodo (ej: 1-6)
        try:
            inicio, fin = map(int, periodo_raw.split('-'))
            meses_seleccionados = meses_full[inicio-1 : fin]
            meses_abrv_seleccionados = meses_abrv_full[inicio-1 : fin]
        except:
            meses_seleccionados, meses_abrv_seleccionados = meses_full, meses_abrv_full

        # 2. CONFIGURACIÓN DEL DOCUMENTO
        response = HttpResponse(content_type='application/pdf')
        nombre_archivo = f"Reporte_Inspecciones_{ccpp.nombre}_{anio_calendario}.pdf".replace(" ", "_")
        response['Content-Disposition'] = f'inline; filename="{nombre_archivo}"'

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
        estilo_celda = estilos['Normal'].clone('estilo_celda', fontSize=7, leading=8)
        estilo_celda_centrada = estilo_celda.clone('estilo_celda_centrada', alignment=1)

        # --- FUNCIÓN DE ENCABEZADO Y PIE ---
        def dibujar_hoja(canvas, doc):
            canvas.saveState()
            fecha_hoy = datetime.now().strftime("%d/%m/%Y")
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(colors.grey)
            canvas.drawString(doc.leftMargin, 0.5 * inch, f"Fecha: {fecha_hoy}")
            canvas.drawCentredString(letter[0] / 2, 0.5 * inch, f"{nombre_tecnico}")
            canvas.drawRightString(letter[0] - doc.rightMargin, 0.5 * inch, f"Página {canvas.getPageNumber()}")
            
            if canvas.getPageNumber() > 1:
                st_title = estilos['Normal'].clone('st_tit', fontSize=11, fontName='Helvetica-Bold')
                st_ccpp = estilos['Normal'].clone('st_ccpp', fontSize=10, fontName='Helvetica-Bold', textColor=colors.maroon)
                
                ruta_logo = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo.png')
                img_logo = Image(ruta_logo, width=0.6*inch, height=0.6*inch) if os.path.exists(ruta_logo) else Paragraph("LOGO", estilo_celda)
                
                periodo_label = "ANUAL" if periodo_raw == "1-12" else f"PERIODO {periodo_raw}"
                datos_h = [[img_logo, [
                    Paragraph("CONTROL LIBRO DEL EDIFICIO", st_title),
                    Paragraph(f"{ccpp.id_ccpp} - {ccpp.nombre.upper()}", st_ccpp),
                    Paragraph(f"AÑO {anio_calendario} | FILTRO: {filtro.upper()} | {periodo_label}", estilo_celda.clone('s', textColor=colors.grey))
                ]]]
                header_table = Table(datos_h, colWidths=[0.7*inch, 5.8*inch])
                header_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('LEFTPADDING', (0,0), (-1,-1), 0)]))
                header_table.wrap(doc.width, doc.topMargin)
                header_table.drawOn(canvas, doc.leftMargin, doc.height + doc.bottomMargin + 0.35 * inch)
                
                canvas.setStrokeColor(colors.orange)
                canvas.setLineWidth(0.5)
                canvas.line(doc.leftMargin, doc.height + doc.bottomMargin + 0.32 * inch, doc.width + doc.leftMargin, doc.height + doc.bottomMargin + 0.32 * inch)
            canvas.restoreState()

        # --- 3. PORTADA ---
        ruta_logo_portada = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo.png')
        if os.path.exists(ruta_logo_portada):
            img_p = Image(ruta_logo_portada, width=1.3*inch, height=1.3*inch)
            img_p.hAlign = 'CENTER'
            elementos.append(img_p)
        
        elementos.append(Spacer(1, 0.2 * inch))
        estilo_p_1 = estilos['Normal'].clone('p1', alignment=1, fontSize=18, fontName='Helvetica-Bold')
        estilo_p_2 = estilos['Normal'].clone('p2', alignment=1, fontSize=15, fontName='Helvetica-Bold', textColor=colors.maroon)
        
        elementos.append(Paragraph("CONTROL LIBRO DEL EDIFICIO", estilo_p_1))
        elementos.append(Spacer(1, 0.1 * inch))
        elementos.append(Paragraph(f"{ccpp.id_ccpp} - {ccpp.nombre.upper()}", estilo_p_2))
        elementos.append(Spacer(1, 0.05 * inch))
        elementos.append(Paragraph(f"AÑO {anio_calendario}", estilo_celda_centrada.clone('p3', fontSize=10, textColor=colors.grey)))
        
        elementos.append(Spacer(1, 0.3 * inch))
        ruta_img_reporte = os.path.join(settings.BASE_DIR, 'static', 'img', 'img_reporte.png')
        if os.path.exists(ruta_img_reporte):
            img_central = Image(ruta_img_reporte, width=5.0*inch, height=3.6*inch)
            img_central.hAlign = 'CENTER'
            elementos.append(img_central)
        
        elementos.append(Spacer(1, 0.3 * inch))
        for w_line in [3.5*inch, 2.5*inch, 1.5*inch, 0.8*inch]:
            linea_naranja = Table([['']], colWidths=[w_line], rowHeights=[1.5])
            linea_naranja.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.orange), ('ALIGN', (0,0), (-1,-1), 'CENTER')]))
            elementos.append(linea_naranja)
            elementos.append(Spacer(1, 4))
        elementos.append(PageBreak())

        # --- 4. PROCESAMIENTO Y FILTROS QUERYSET ---
        # Mapa de inspecciones para obtener códigos y colores
        inspecciones_map = {str(i.id): (i.codigo_inspeccion, i.color_inspeccion) for i in tbl_inspeccion.objects.all()}
        
        # Obtener cronograma basado en el año relativo del CCPP
        fecha_ini = ccpp.fecha_entrega.year if ccpp.fecha_entrega else anio_calendario
        anio_rel = anio_calendario - fecha_ini
        
        cronogramas = tbl_Cronograma.objects.filter(ccpp=ccpp, anios=anio_rel).select_related('unidad')

        # Aplicar filtros de fila según selección en Modal
        if filtro == 'con_inspeccion':
            q_filtro = Q()
            for m in meses_seleccionados:
                q_filtro |= Q(**{f'{m}__isnull': False}) & ~Q(**{f'{m}': ''})
            cronogramas = cronogramas.filter(q_filtro)
        elif filtro == 'sin_inspeccion':
            q_filtro = Q()
            for m in meses_seleccionados:
                q_filtro &= (Q(**{f'{m}__isnull': True}) | Q(**{f'{m}': ''}))
            cronogramas = cronogramas.filter(q_filtro)
        elif filtro in ['con_notificacion', 'sin_notificacion', 'con_respuesta', 'sin_respuesta']:
            # Lógica basada en la relación FK_cronograma de tbl_Notificacion
            notif_q = Q(FK_cronograma__ccpp=ccpp)
            if filtro == 'con_respuesta':
                notif_q &= Q(NotificacionContestada=True)
            elif filtro == 'sin_respuesta':
                notif_q &= Q(NotificacionContestada=False)
            
            crono_ids = tbl_Notificacion.objects.filter(notif_q).values_list('FK_cronograma_id', flat=True).distinct()
            
            if 'sin_notificacion' in filtro:
                cronogramas = cronogramas.exclude(id__in=crono_ids)
            else:
                cronogramas = cronogramas.filter(id__in=crono_ids)

        # Orden de la tabla
        if orden == 'doc': cronogramas = cronogramas.order_by('unidad__doc')
        elif orden == 'unidad': cronogramas = cronogramas.order_by('unidad__unidad')
        else: cronogramas = cronogramas.order_by('unidad__orden')

        # --- 5. TABLA DE DATOS ---
        encabezados = [
            Paragraph('<b>DOC</b>', estilo_celda_centrada), 
            Paragraph('<b>UNIDAD</b>', estilo_celda_centrada)
        ] + [Paragraph(f'<b>{m.upper()[:3]}</b>', estilo_celda_centrada) for m in meses_seleccionados]
        
        data_tabla = [encabezados]
        
        for crono in cronogramas:
            fila = [
                Paragraph(crono.unidad.doc or "", estilo_celda_centrada), 
                Paragraph(crono.unidad.unidad, estilo_celda)
            ]
            incluir_fila_por_dato = False

            for m_f in meses_seleccionados:
                val_inspeccion = getattr(crono, m_f)
                
                # Buscar notificación específica para este mes y este cronograma
                notif = tbl_Notificacion.objects.filter(
                    FK_cronograma=crono, 
                    PK_mes__iexact=m_f
                ).first()

                # Validación de visibilidad según filtros específicos de celda
                mostrar_celda = True
                if filtro == 'con_notificacion' and not notif: mostrar_celda = False
                elif filtro == 'sin_notificacion' and notif: mostrar_celda = False
                elif filtro == 'con_respuesta' and (not notif or not notif.NotificacionContestada): mostrar_celda = False
                elif filtro == 'sin_respuesta' and (not notif or notif.NotificacionContestada): mostrar_celda = False

                if val_inspeccion and mostrar_celda:
                    cod, col = inspecciones_map.get(str(val_inspeccion), (val_inspeccion, "#000000"))
                    fila.append(Paragraph(f'<font color="{col}"><b>{cod}</b></font>', estilo_celda_centrada))
                    incluir_fila_por_dato = True
                else:
                    fila.append("")
            
            # Solo añadir fila si tiene datos o si el filtro permite ver todas
            if incluir_fila_por_dato or filtro in ['todas', 'sin_inspeccion']:
                data_tabla.append(fila)

        # Cálculo de anchos de columna
        ancho_doc = 45
        ancho_unidad = 145
        ancho_restante = doc.width - (ancho_doc + ancho_unidad)
        ancho_mes = ancho_restante / len(meses_seleccionados)
        ancho_cols = [ancho_doc, ancho_unidad] + [ancho_mes] * len(meses_seleccionados)

        tabla = Table(data_tabla, colWidths=ancho_cols, repeatRows=1)
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F2E2D2')),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.orange),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ]))
        elementos.append(tabla)

        # --- 6. LEYENDA ---
        elementos.append(Spacer(1, 0.3 * inch))
        datos_leyenda = [
            [Paragraph('<b><font color="maroon">M</font></b>', estilo_celda_centrada), Paragraph('Operario Mantenimiento-Especialista', estilo_celda)],
            [Paragraph('<b><font color="red">E</font></b>', estilo_celda_centrada), Paragraph('Técnico Cabecera-Operario Especialista', estilo_celda)],
            [Paragraph('<b><font color="orange">O</font></b>', estilo_celda_centrada), Paragraph('Operario', estilo_celda)],
            [Paragraph('<b><font color="green">T</font></b>', estilo_celda_centrada), Paragraph('Técnico Cabecera', estilo_celda)],
            [Paragraph('<b><font color="darkgreen">I</font></b>', estilo_celda_centrada), Paragraph('Inspección Reglamentaria', estilo_celda)],
            [Paragraph('<b><font color="dodgerblue">P</font></b>', estilo_celda_centrada), Paragraph('Prueba Reglamentaria', estilo_celda)],
            [Paragraph('<b><font color="darkblue">C</font></b>', estilo_celda_centrada), Paragraph('Control Obligatorio', estilo_celda)],
            [Paragraph('<b><font color="purple">S</font></b>', estilo_celda_centrada), Paragraph('Sustitución Obligatoria', estilo_celda)]
        ]

        tabla_leyenda = Table(datos_leyenda, colWidths=[30, 220])
        tabla_leyenda.hAlign = 'LEFT'
        tabla_leyenda.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#FFE4E1')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0,0), (0, -1), colors.whitesmoke)
        ]))
        elementos.append(tabla_leyenda)

        # 7. GENERACIÓN FINAL
        doc.build(elementos, onFirstPage=dibujar_hoja, onLaterPages=dibujar_hoja)
        return response

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return HttpResponse(f"Error crítico al generar PDF: {str(e)}", status=500)
































































