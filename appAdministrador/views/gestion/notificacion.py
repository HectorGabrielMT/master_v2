from django.shortcuts import render, get_object_or_404, redirect
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from appAdministrador.models import *
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import re
from django.http import Http404
from datetime import date, datetime
from datetime import date
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.db import transaction
import logging
from django.db import transaction
# Configuración del logger para este módulo
logger = logging.getLogger(__name__)
import logging
import re
from django.db import transaction, DatabaseError
from django.http import Http404


# FUNCIONES 
def reemplazar_etiquetas(texto, contexto):
    if not texto: return ""
    hoy = datetime.now()
    reemplazos = {
        '<FECHA>': hoy.strftime('%d/%m/%Y'),
        '<AÑO>': str(hoy.year),
        '<CCPP-I>': contexto.get('id_ccpp', ''),
        '<CCPP-N>': contexto.get('nombre_ccpp', ''),
        '<UNIDAD>': contexto.get('unidad', ''),
        '<UNIDAD-D>': contexto.get('descripcion_unidad', ''),
        '<INSPECCION>': contexto.get('inspeccion', ''),
        '<INSPECCION-D>': contexto.get('descripcion_inspeccion', ''),
        '<INSPECCION-N>': contexto.get('notificacion_inspeccion', ''),
    }
    for tag, val in reemplazos.items():
        texto = texto.replace(tag, str(val))
    return texto


def extraer_correos(texto):
    """
    Busca todas las direcciones de correo electrónico dentro de un texto
    y las retorna como una lista de strings para que el template de Django
    pueda iterar sobre ellas correctamente.
    """
    # Si el texto es None o está vacío, retornamos una lista vacía
    if not texto:
        return []

    # Expresión regular para encontrar correos electrónicos
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    
    # findall busca todas las coincidencias y las devuelve en una lista
    emails = re.findall(pattern, texto)
    
    # Retornamos la lista directamente. 
    # NO usamos ", ".join(emails) porque eso convertiría la lista en un solo string,
    # causando que el template itere sobre cada letra en lugar de cada correo.
    return emails



# --------------------------------------------------------------------------------
@login_required
def vista_panel_notificacion(request, ccpp_id):
    """
    Vista optimizada del panel de notificaciones.
    - Usa diccionarios en memoria para procesar estados rápidamente.
    - Valida existencia de cronogramas y notificaciones.
    - Devuelve retroalimentación clara en español.
    """
    ccpp = get_object_or_404(tbl_CCPP, pk=ccpp_id)

    # 1. Parámetros de filtro
    anio_filtro = request.GET.get("anio", "todos")
    mes_filtro = request.GET.get("mes", "todos").lower()
    estado_filtro = request.GET.get("estado", "todos")

    # 2. Cronogramas base
    cronogramas = tbl_Cronograma.objects.filter(ccpp=ccpp).select_related("unidad")

    # Definición de meses y estados
    meses_nombres = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]

    estados_opciones = [
        ("todos", "Todos"),
        ("sin_notificar", "Sin notificar"),
        ("notificado_sin_respuesta", "Notificado (Sin respuesta)"),
        ("notificado_con_respuesta", "Notificado (Con respuesta)"),
        ("notificado_ejecutado", "Notificado (Ejecutado)"),
    ]

    if not cronogramas.exists():
        messages.warning(
            request,
            f"No hay cronogramas configurados para {ccpp.nombre}."
        )
        return render(
            request,
            "gestion/notificacion/panel_notificacion.html",
            {
                "ccpp": ccpp,
                "inspecciones": [],
                "anos_disponibles": [],
                "meses_disponibles": meses_nombres,
                "estados_disponibles": estados_opciones,
                "anio_filtro": anio_filtro,
                "mes_filtro": mes_filtro,
                "estado_filtro": estado_filtro,
                "sin_cronogramas": True,
            },
        )

    # 3. Preparación de datos en memoria
    anio_base = ccpp.fecha_entrega.year if ccpp.fecha_entrega else date.today().year

    # Notificaciones relacionadas
    notificaciones_qs = tbl_Notificacion.objects.filter(FK_cronograma__in=cronogramas)
    notificaciones_dict = {
        (n.FK_cronograma_id, n.PK_mes.lower()): n for n in notificaciones_qs
    }

    # Inspecciones
    inspecciones_dict = {
        str(insp.id): insp for insp in tbl_inspeccion.objects.all()
    }

    inspecciones_lista = []
    campos_meses = {
        "enero": "Enero", "febrero": "Febrero", "marzo": "Marzo", "abril": "Abril",
        "mayo": "Mayo", "junio": "Junio", "julio": "Julio", "agosto": "Agosto",
        "septiembre": "Septiembre", "octubre": "Octubre", "noviembre": "Noviembre", "diciembre": "Diciembre",
    }

    # 4. Procesamiento Cronograma x Meses
    for cronograma in cronogramas:
        anio_calendario = anio_base + cronograma.anios

        # Filtro de año
        if anio_filtro != "todos" and str(anio_calendario) != anio_filtro:
            continue

        for campo_mes, mes_nombre in campos_meses.items():
            # Filtro de mes
            if mes_filtro != "todos" and campo_mes != mes_filtro:
                continue

            id_inspeccion_str = getattr(cronograma, campo_mes, "")
            if not id_inspeccion_str or not str(id_inspeccion_str).strip():
                continue

            inspeccion = inspecciones_dict.get(str(id_inspeccion_str).strip())
            if not inspeccion:
                continue

            # Estado de notificación
            notificacion = notificaciones_dict.get((cronograma.id, mes_nombre.lower()))
            if notificacion:
                if notificacion.RespInspEjecutada:
                    estado = "notificado_ejecutado"
                elif notificacion.NotificacionContestada:
                    estado = "notificado_con_respuesta"
                else:
                    estado = "notificado_sin_respuesta"
            else:
                estado = "sin_notificar"

            # Filtro de estado
            if estado_filtro != "todos" and estado != estado_filtro:
                continue

            # Construcción del objeto para la vista
            inspecciones_lista.append({
                "cronograma_id": cronograma.id,
                "inspeccion_id": inspeccion.id,
                "unidad": cronograma.unidad.unidad if cronograma.unidad else "Sin unidad",
                "unidad_desc": cronograma.unidad.descripcion if cronograma.unidad else "",
                "mes": mes_nombre,
                "anio_calendario": anio_calendario,
                "inspeccion_codigo": inspeccion.codigo_inspeccion,
                "inspeccion_nombre": inspeccion.nombre_inspeccion,
                "inspeccion_descripcion": inspeccion.descripcion_inspeccion,
                "color_inspeccion": inspeccion.color_inspeccion,
                "estado": estado,
                "notificacion_id": notificacion.id if notificacion else None,
                "notificacion_fecha": notificacion.fecha if notificacion else None,
                "notificacion_fecha_respuesta": notificacion.FechaResp if notificacion else None,
                "inspeccion_ejecutada": notificacion.RespInspEjecutada if notificacion else False,
                "notificacion_contestada": notificacion.NotificacionContestada if notificacion else False,
            })

    # 5. Ordenamiento final
    orden_meses_lista = list(campos_meses.keys())
    inspecciones_lista.sort(
        key=lambda x: (
            x["anio_calendario"],
            orden_meses_lista.index(x["mes"].lower()),
            x["unidad"],
        )
    )

    # 6. Años disponibles para el selector
    anos_calendario = sorted(
        list(set(insp["anio_calendario"] for insp in inspecciones_lista))
    )

    context = {
        "ccpp": ccpp,
        "inspecciones": inspecciones_lista,
        "anos_disponibles": anos_calendario,
        "meses_disponibles": meses_nombres,
        "estados_disponibles": estados_opciones,
        "anio_filtro": anio_filtro,
        "mes_filtro": mes_filtro,
        "estado_filtro": estado_filtro,
        "debug_info": {
            "total_cronogramas": cronogramas.count(),
            "total_inspecciones": len(inspecciones_lista),
            "anio_base": anio_base,
        },
    }

    return render(request, "gestion/notificacion/panel_notificacion.html", context)



@login_required
def guardar_notificacion(request, cronograma_id, mes_nombre):
    """
    Vista para crear, actualizar o eliminar notificaciones asociadas a un cronograma.
    - Maneja activación/desactivación de notificaciones.
    - Elimina todos los archivos asociados cuando se desactiva.
    """
    if request.method != "POST":
        logger.warning(
            "Acceso inválido a guardar_notificacion con método %s",
            request.method
        )
        return redirect("panel_principal")

    cronograma = get_object_or_404(tbl_Cronograma, id=cronograma_id)
    mes_campo = mes_nombre.lower().strip()

    try:
        with transaction.atomic():
            # 1. Lógica de activación/desactivación
            if request.POST.get("notificacion_activa") != "on":
                notificacion_existente = tbl_Notificacion.objects.filter(
                    FK_cronograma=cronograma,
                    PK_mes=mes_campo
                ).first()

                if notificacion_existente:
                    # Obtener todos los documentos asociados
                    documentos = notificacion_existente.documentos.all()
                    total_documentos = documentos.count()
                    
                    # Eliminar archivos físicos de todos los documentos
                    documentos_eliminados = 0
                    for documento in documentos:
                        try:
                            if documento.archivo:
                                documento.archivo.delete(save=False)
                                documentos_eliminados += 1
                        except Exception as e:
                            logger.warning(
                                "Error al eliminar archivo físico %s (doc_id=%s): %s",
                                documento.archivo.name if documento.archivo else "N/A",
                                documento.id,
                                e
                            )
                    
                    # Guardar información para logging antes de eliminar
                    nombre_ficha = (
                        notificacion_existente.FK_ficha.PK_titulo
                        if notificacion_existente.FK_ficha else "Sin ficha"
                    )
                    
                    # Guardar ID para logging
                    notificacion_id = notificacion_existente.id
                    
                    # Eliminar todos los documentos y la notificación
                    # Esto se hace automáticamente por CASCADE en el modelo
                    notificacion_existente.delete()
                    
                    logger.info(
                        "Notificación eliminada completamente: "
                        "cronograma=%s, mes=%s, notificacion_id=%s, ficha=%s, "
                        "documentos_eliminados=%s/%s",
                        cronograma.id, mes_campo, notificacion_id, nombre_ficha,
                        documentos_eliminados, total_documentos
                    )
                    messages.success(
                        request, 
                        f"Notificación y todos sus archivos ({documentos_eliminados} documentos) "
                        "han sido eliminados correctamente."
                    )
                else:
                    logger.info(
                        "Intento de desactivación sin notificación existente: cronograma=%s, mes=%s",
                        cronograma.id, mes_campo
                    )
                    messages.info(request, "La notificación ya estaba inactiva.")

                return redirect(
                    "gestionar_notificacion",
                    cronograma_id=cronograma_id,
                    mes_nombre=mes_nombre
                )

            # 2. Obtener ficha seleccionada
            ficha_id = request.POST.get("ficha_seleccionada")
            ficha_obj = None
            if ficha_id:
                try:
                    ficha_obj = tbl_Ficha.objects.get(id=ficha_id)
                except tbl_Ficha.DoesNotExist:
                    logger.warning(
                        "Ficha seleccionada no encontrada: ficha_id=%s", ficha_id
                    )
                    ficha_obj = None

            # 3. Procesar destinatarios
            para_str = ",".join(request.POST.getlist("destinatarios_para"))
            cc_str = ",".join(request.POST.getlist("destinatarios_cc"))
            cco_str = ",".join(request.POST.getlist("destinatarios_cco"))

            # 4. Obtener datos de respuesta
            fecha_respuesta = request.POST.get("fecha_respuesta")
            revision = request.POST.get("revision", "").strip()
            controlador = request.POST.get("controlador", "").strip()
            via = request.POST.get("via", "").strip()
            observaciones = request.POST.get("observaciones", "").strip()
            inspeccion_ejecutada = request.POST.get("inspeccion_ejecutada") == "on"

            # 5. Determinar si la notificación está contestada
            notificacion_contestada = bool(
                fecha_respuesta or revision or controlador or via or observaciones or inspeccion_ejecutada
            )

            # 6. Preparar datos para actualizar/crear
            datos_notificacion = {
                "fecha": request.POST.get("fecha") or None,
                "para": para_str,
                "cc": cc_str,
                "cco": cco_str,
                "FK_ficha": ficha_obj,
                "FechaResp": fecha_respuesta or None,
                "RespRevision": revision,
                "RespControlador": controlador,
                "RespVia": via,
                "RespObservacion": observaciones,
                "RespInspEjecutada": inspeccion_ejecutada,
                "NotificacionContestada": notificacion_contestada,
            }

            # 7. Guardar o actualizar notificación
            notificacion, created = tbl_Notificacion.objects.update_or_create(
                FK_cronograma=cronograma,
                PK_mes=mes_campo,
                defaults=datos_notificacion
            )

            # 8. Manejo de documentos adjuntos
            archivos = request.FILES.getlist("archivos")
            archivos_guardados = 0
            for archivo in archivos:
                try:
                    tbl_NotificacionDocumento.objects.create(
                        FK_notificacion=notificacion,
                        archivo=archivo,
                        nombre_original=archivo.name,
                        tamano=archivo.size,
                    )
                    archivos_guardados += 1
                    logger.info(
                        "Documento adjunto guardado: notificacion=%s, archivo=%s, tamaño=%s",
                        notificacion.id, archivo.name, archivo.size
                    )
                except Exception as e:
                    logger.error(
                        "Error al guardar documento adjunto: notificacion=%s, archivo=%s, error=%s",
                        notificacion.id, archivo.name, e
                    )

            # 9. Mensajes de éxito y logging
            if created:
                logger.info(
                    "Notificación creada: cronograma=%s, mes=%s, notificacion_id=%s, archivos=%s",
                    cronograma.id, mes_campo, notificacion.id, archivos_guardados
                )
                messages.success(
                    request, 
                    f"Notificación creada exitosamente."
                )
            else:
                logger.info(
                    "Notificación actualizada: cronograma=%s, mes=%s, notificacion_id=%s, archivos=%s",
                    cronograma.id, mes_campo, notificacion.id, archivos_guardados
                )
                messages.success(
                    request, 
                    f"Cambios guardados exitosamente. "
                )

    except Exception as error:
        logger.error(
            "Error inesperado en guardar_notificacion: cronograma=%s, mes=%s, error=%s",
            cronograma.id, mes_campo, error
        )
        messages.error(request, f"Ocurrió un error inesperado: {error}")

    return redirect("gestionar_notificacion", cronograma_id=cronograma_id, mes_nombre=mes_nombre)



@login_required
def gestion_notificacion(request, cronograma_id, mes_nombre):
    try:
        cronograma = get_object_or_404(tbl_Cronograma, id=cronograma_id)
    except Exception as e:
        logger.error(f"Error al obtener cronograma {cronograma_id}: {e}")
        messages.error(request, "No se pudo cargar el cronograma solicitado.")
        return redirect("panel_principal")

    mes_campo = mes_nombre.lower().strip()

    if not hasattr(cronograma, mes_campo):
        logger.warning(f"Mes inválido solicitado: {mes_campo}")
        raise Http404(f"El mes '{mes_campo}' no es válido.")

    try:
        codigo_inspeccion_id = getattr(cronograma, mes_campo)
    except Exception as e:
        logger.error(f"Error al obtener inspección del mes {mes_campo}: {e}")
        messages.error(request, "No se pudo obtener la inspección asignada.")
        return redirect("panel_principal")

    if not codigo_inspeccion_id:
        messages.error(request, f"No hay una inspección asignada para {mes_nombre}")
        return redirect("panel_principal")

    try:
        inspeccion = get_object_or_404(tbl_inspeccion, id=codigo_inspeccion_id)
    except Exception as e:
        logger.error(f"Error al obtener inspección {codigo_inspeccion_id}: {e}")
        messages.error(request, "No se pudo cargar la inspección solicitada.")
        return redirect("panel_principal")

    try:
        with transaction.atomic():
            notificacion_obj = tbl_Notificacion.objects.filter(
                FK_cronograma=cronograma,
                PK_mes=mes_campo
            ).first()

            notificacion_existe = notificacion_obj is not None
            documentos = notificacion_obj.documentos.all() if notificacion_existe else []

            unidad = cronograma.unidad
            fichas_unidad = []
            if unidad:
                try:
                    fichas_unidad = tbl_Ficha.objects.filter(
                        FK_FichaUnidad=unidad
                    ).order_by("PK_titulo")
                except Exception as e:
                    logger.error(f"Error al obtener fichas de unidad {unidad.id}: {e}")
                    fichas_unidad = []

            def extract_emails(texto):
                if not texto:
                    return []
                return re.findall(
                    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
                    texto
                )

            correos_ccpp = {
                "para": extract_emails(cronograma.ccpp.administracion_edificio)
                + extract_emails(cronograma.ccpp.tecnico_cabecera),
                "cc": extract_emails(cronograma.ccpp.operario_comunidad)
                + extract_emails(cronograma.ccpp.tecnico_especialista)
                + extract_emails(cronograma.ccpp.empresa_especializada),
                "cco": extract_emails(cronograma.ccpp.copia_oculta),
            }

            for key in correos_ccpp:
                correos_ccpp[key] = list(dict.fromkeys(correos_ccpp[key]))

            asunto_procesado = ""
            cuerpo_procesado = ""
            try:
                correo_base = tbl_Correo.objects.first()
                if correo_base:
                    contexto_reemplazo = {
                        "id_ccpp": cronograma.ccpp.id_ccpp,
                        "nombre_ccpp": cronograma.ccpp.nombre,
                        "unidad": cronograma.unidad.unidad if cronograma.unidad else "",
                        "inspeccion": inspeccion.codigo_inspeccion,
                        "descripcion_inspeccion": inspeccion.descripcion_inspeccion,
                        "mes": mes_nombre.capitalize(),
                    }
                    asunto_procesado = reemplazar_etiquetas(
                        correo_base.asunto, contexto_reemplazo
                    )
                    cuerpo_procesado = reemplazar_etiquetas(
                        correo_base.cuerpo, contexto_reemplazo
                    )
            except Exception as e:
                logger.error(f"Error al procesar correo base: {e}")

            pdf_download_url = ""
            if notificacion_existe and notificacion_obj.FK_ficha:
                pdf_download_url = (
                    f"/notificaciones/{notificacion_obj.id}/descargar-pdf-ficha/"
                )

            context = {
                "cronograma": cronograma,
                "mes_nombre": mes_nombre,
                "inspeccion": inspeccion,
                "notificacion_obj": notificacion_obj,
                "notificacion_existe": notificacion_existe,
                "documentos": documentos,
                "fichas_unidad": fichas_unidad,
                "correos_ccpp": correos_ccpp,
                "asunto_correo": asunto_procesado,
                "cuerpo_correo": cuerpo_procesado,
                "pdf_download_url": pdf_download_url,
            }

    except DatabaseError as db_err:
        logger.error(f"Error de base de datos en gestión de notificación: {db_err}")
        messages.error(request, "Error de base de datos al gestionar la notificación.")
        return redirect("panel_principal")
    except Exception as e:
        logger.error(f"Error inesperado en gestión de notificación: {e}")
        messages.error(request, "Ocurrió un error inesperado al gestionar la notificación.")
        return redirect("panel_principal")

    try:
        print(1)
        return render(
            request,
            "gestion/notificacion/formulario_notificacion.html",
            context,
        )
        print(2)
    except Exception as e:
        logger.error(f"Error al renderizar formulario de notificación: {e}")
        messages.error(request, "No se pudo generar el formulario de notificación.")
        return redirect("panel_principal")



@login_required
def eliminar_documento(request, documento_id):
    """
    Vista para eliminar un documento específico de una notificación.
    Elimina tanto el registro de la base de datos como el archivo físico.
    """
    if request.method != "POST":
        logger.warning(
            "Intento de eliminar documento con método %s, documento_id=%s",
            request.method, documento_id
        )
        return redirect("panel_principal")
    
    try:
        documento = get_object_or_404(tbl_NotificacionDocumento, id=documento_id)
        notificacion = documento.FK_notificacion
        
        # Guardar información para logging
        cronograma_id = notificacion.FK_cronograma.id
        mes = notificacion.PK_mes
        nombre_archivo = documento.nombre_original
        
        with transaction.atomic():
            # Eliminar documento (la eliminación del archivo físico se maneja en el modelo)
            documento.delete()
            
            logger.info(
                "Documento eliminado exitosamente: documento_id=%s, "
                "notificacion_id=%s, archivo=%s, cronograma_id=%s, mes=%s",
                documento_id, notificacion.id, nombre_archivo, cronograma_id, mes
            )
            messages.success(request, f"Documento '{nombre_archivo}' eliminado correctamente.")
            
        return redirect("gestionar_notificacion", cronograma_id=cronograma_id, mes_nombre=mes)
        
    except tbl_NotificacionDocumento.DoesNotExist:
        logger.error(f"Documento no encontrado: documento_id={documento_id}")
        messages.error(request, "El documento no existe o ya fue eliminado.")
        return redirect("panel_principal")
        
    except Exception as e:
        logger.error(
            "Error inesperado al eliminar documento: documento_id=%s, error=%s",
            documento_id, e
        )
        messages.error(request, "Ocurrió un error inesperado al eliminar el documento.")
        
        # Intentar redirigir de todas formas si tenemos la información
        try:
            if 'cronograma_id' in locals() and 'mes' in locals():
                return redirect("gestionar_notificacion", cronograma_id=cronograma_id, mes_nombre=mes)
        except:
            pass
            
        return redirect("panel_principal")





#--------------------------ENVIAR CORREO-----------------------------------------------------------------


import base64
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.core.mail import EmailMessage


def preparar_y_enviar_correo__(request, ccpp_id, unidad_id, inspeccion_id):
    """
    Prepara y envía un correo con opción de adjuntar PDF de ficha.
    
    URL: /enviar-correo/<ccpp_id>/<unidad_id>/<inspeccion_id>/?ficha_id=<opcional>
    """
    # Obtención de objetos
    ccpp = get_object_or_404(tbl_CCPP, id=ccpp_id)
    unidad = get_object_or_404(tbl_Unidad, id=unidad_id)
    insp = get_object_or_404(tbl_inspeccion, id=inspeccion_id)
    
    if request.method == 'GET':
        correo_base = tbl_Correo.objects.first()
        
        # 1. Extraer correos según la lógica solicitada
        emails_para = extraer_correos(f"{ccpp.administracion_edificio}, {ccpp.tecnico_cabecera}")
        emails_cc = extraer_correos(f"{ccpp.tecnico_especialista}, {ccpp.operario_comunidad}, {ccpp.empresa_especializada}")
        emails_cco = extraer_correos(ccpp.copia_oculta)

        # 2. Reemplazar etiquetas en Asunto y Cuerpo
        contexto_tags = {
            'id_ccpp': ccpp.id_ccpp,
            'nombre_ccpp': ccpp.nombre,
            'unidad': unidad.unidad,
            'descripcion_unidad': unidad.descripcion,
            'inspeccion': insp.nombre_inspeccion,
            'descripcion_inspeccion': insp.descripcion_inspeccion,
            'notificacion_inspeccion': insp.notificacionA_inspeccion,
        }
        
        asunto_render = reemplazar_etiquetas(correo_base.asunto, contexto_tags)
        cuerpo_render = reemplazar_etiquetas(correo_base.cuerpo, contexto_tags)

        # 3. Verificar si se solicita adjuntar ficha PDF
        ficha_pdf_data = None
        ficha_nombre = None
        
        ficha_id = request.GET.get('ficha_id')
        if ficha_id:
            try:
                # Verificar que la ficha existe
                ficha = tbl_Ficha.objects.get(id=ficha_id)
                
                # Generar PDF en memoria (return_buffer=True)
                pdf_content = exportar_ficha_pdf(request, ficha_id, ccpp_id, return_buffer=True)
                
                if pdf_content:
                    # Convertir PDF a base64 para enviar al template
                    ficha_pdf_data = base64.b64encode(pdf_content).decode('utf-8')
                    ficha_nombre = f'Ficha_{ficha_id}.pdf'
                else:
                    print("No se pudo generar el contenido del PDF")
                    
            except tbl_Ficha.DoesNotExist:
                print(f"Ficha con ID {ficha_id} no existe")
            except Exception as e:
                print(f"Error generando PDF de ficha: {e}")

        return render(request, 'gestion/notificacion/enviar_correo.html', {
            'asunto': asunto_render,
            'cuerpo': cuerpo_render,
            'para': emails_para, 
            'cc': emails_cc,
            'cco': emails_cco,
            'ficha_pdf_data': ficha_pdf_data,
            'ficha_nombre': ficha_nombre,
        })

    if request.method == 'POST':
        # Procesamiento del envío (POST)
        # Solo enviar campos si no están ocultos
        para_list = [e.strip() for e in request.POST.get('para', '').split(',') if e.strip()]
        
        # Verificar si los campos están presentes (no ocultos)
        cc_list = []
        if 'cc' in request.POST:  # Si el campo está en el formulario (no oculto)
            cc_list = [e.strip() for e in request.POST.get('cc', '').split(',') if e.strip()]
        
        cco_list = []
        if 'cco' in request.POST:  # Si el campo está en el formulario (no oculto)
            cco_list = [e.strip() for e in request.POST.get('cco', '').split(',') if e.strip()]

        email = EmailMessage(
            subject=request.POST.get('asunto'),
            body=request.POST.get('cuerpo'),
            from_email='madrizgt@gmail.com',
            to=para_list,
            cc=cc_list if cc_list else None,
            bcc=cco_list if cco_list else None,
        )

        # Adjuntos acumulados desde JavaScript
        for f in request.FILES.getlist('adjuntos_finales'):
            email.attach(f.name, f.read(), f.content_type)

        # Adjuntar PDF de ficha si se generó (desde campo oculto base64)
        ficha_pdf_base64 = request.POST.get('ficha_pdf_data')
        if ficha_pdf_base64:
            try:
                pdf_content = base64.b64decode(ficha_pdf_base64)
                ficha_nombre = request.POST.get('ficha_nombre', 'Ficha_adjunta.pdf')
                email.attach(ficha_nombre, pdf_content, 'application/pdf')
            except Exception as e:
                print(f"Error adjuntando PDF base64: {e}")

        try:
            email.send(fail_silently=False)
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)




def preparar_y_enviar_correo_(request, ccpp_id, unidad_id, inspeccion_id, notificacion_id=None):
    """
    Prepara y envía un correo con opción de adjuntar PDF de ficha.
    
    Parámetros:
        request: Objeto HttpRequest
        ccpp_id: ID del CCPP específico
        unidad_id: ID de la unidad específica
        inspeccion_id: ID de la inspección específica
        notificacion_id: ID opcional de notificación existente
    
    Comportamiento:
        - Los correos en los inputs vienen de tbl_Notificacion (si existe registro previo)
        - Los contactos disponibles vienen únicamente del CCPP específico (tbl_CCPP)
        - Los correos se organizan según categorías específicas
    """
    # Obtener objetos base con get_object_or_404 para manejo de errores
    ccpp_especifico = get_object_or_404(tbl_CCPP, id=ccpp_id)
    unidad = get_object_or_404(tbl_Unidad, id=unidad_id)
    inspeccion = get_object_or_404(tbl_inspeccion, id=inspeccion_id)
    
    # Obtener notificación si se proporciona ID
    ficha_id = request.GET.get('ficha_id')
    notificacion = None
    if notificacion_id:
        notificacion = get_object_or_404(tbl_Notificacion, id=notificacion_id)
    
    # Compatibilidad con parámetro GET para notificación
    if not notificacion:
        notificacion_id_get = request.GET.get('notificacion_id')
        if notificacion_id_get:
            notificacion = get_object_or_404(tbl_Notificacion, id=notificacion_id_get)

    if request.method == 'GET':
        # Obtener plantilla de correo base
        plantilla_correo = tbl_Correo.objects.first()
        
        # 1. CORREOS PARA LOS INPUTS - provienen de notificación previa si existe
        if notificacion:
            # Usar correos guardados en notificación anterior
            correos_para_input = extraer_correos(notificacion.para)
            correos_cc_input = extraer_correos(notificacion.cc)
            correos_cco_input = extraer_correos(notificacion.cco)
        else:
            # Para nueva notificación, usar estructura del CCPP específico
            correos_para_input = extraer_correos(
                f"{ccpp_especifico.administracion_edificio}, {ccpp_especifico.tecnico_cabecera}"
            )
            correos_cc_input = extraer_correos(
                f"{ccpp_especifico.operario_comunidad}, "
                f"{ccpp_especifico.empresa_especializada}, "
                f"{ccpp_especifico.tecnico_especialista}"
            )
            correos_cco_input = extraer_correos(ccpp_especifico.copia_oculta)

        # 2. CONTACTOS DISPONIBLES - ÚNICAMENTE del CCPP específico
        contactos_disponibles = {
            'para': [],  # administracion_edificio y tecnico_cabecera
            'cc': [],    # operario_comunidad, empresa_especializada, tecnico_especialista
            'cco': []    # copia_oculta
        }
        
        # Extraer y organizar contactos del CCPP específico
        contactos_disponibles['para'].extend(
            extraer_correos(
                f"{ccpp_especifico.administracion_edificio}, {ccpp_especifico.tecnico_cabecera}"
            )
        )
        
        contactos_disponibles['cc'].extend(
            extraer_correos(
                f"{ccpp_especifico.operario_comunidad}, "
                f"{ccpp_especifico.empresa_especializada}, "
                f"{ccpp_especifico.tecnico_especialista}"
            )
        )
        
        contactos_disponibles['cco'].extend(
            extraer_correos(ccpp_especifico.copia_oculta)
        )
        
        # Limpiar duplicados, eliminar vacíos y ordenar alfabéticamente
        for categoria in contactos_disponibles:
            contactos_filtrados = [
                email.strip() 
                for email in contactos_disponibles[categoria] 
                if email.strip()
            ]
            contactos_disponibles[categoria] = sorted(list(set(contactos_filtrados)))

        # 3. REEMPLAZAR ETIQUETAS en asunto y cuerpo
        contexto_etiquetas = {
            'id_ccpp': ccpp_especifico.id_ccpp,
            'nombre_ccpp': ccpp_especifico.nombre,
            'unidad': unidad.unidad,
            'descripcion_unidad': unidad.descripcion,
            'inspeccion': inspeccion.nombre_inspeccion,
            'descripcion_inspeccion': inspeccion.descripcion_inspeccion,
            'notificacion_inspeccion': inspeccion.notificacionA_inspeccion,
        }
        
        asunto_renderizado = reemplazar_etiquetas(plantilla_correo.asunto, contexto_etiquetas)
        cuerpo_renderizado = reemplazar_etiquetas(plantilla_correo.cuerpo, contexto_etiquetas)

        # 4. VERIFICAR SI SE DEBE ADJUNTAR FICHA PDF
        datos_pdf_ficha = None
        nombre_ficha = None
        ficha_id = request.GET.get('ficha_id')
        
        if ficha_id:
            try:
                # Generar PDF en memoria
                contenido_pdf = exportar_ficha_pdf(
                    request, 
                    ficha_id, 
                    ccpp_id, 
                    return_buffer=True
                )
                if contenido_pdf:
                    datos_pdf_ficha = base64.b64encode(contenido_pdf).decode('utf-8')
                    nombre_ficha = f'Ficha_{ficha_id}.pdf'
            except Exception as error:
                print(f"Error generando PDF de ficha: {error}")

        return render(request, 'gestion/notificacion/enviar_correo.html', {
            'asunto': asunto_renderizado,
            'cuerpo': cuerpo_renderizado,
            'para': correos_para_input, 
            'cc': correos_cc_input,
            'cco': correos_cco_input,
            'contactos_disponibles': contactos_disponibles,
            'ficha_pdf_data': datos_pdf_ficha,
            'ficha_nombre': nombre_ficha,
            'notificacion_id': notificacion_id or request.GET.get('notificacion_id'),
            'ccpp_actual': ccpp_especifico,
            'unidad_actual': unidad,
            'inspeccion_actual': inspeccion,
        })

    if request.method == 'POST':
        # PROCESAMIENTO DEL ENVÍO
        lista_para = [
            email.strip() 
            for email in request.POST.get('para', '').split(',') 
            if email.strip()
        ]
        
        lista_cc = [
            email.strip() 
            for email in request.POST.get('cc', '').split(',') 
            if email.strip()
        ] if 'cc' in request.POST else []
        
        lista_cco = [
            email.strip() 
            for email in request.POST.get('cco', '').split(',') 
            if email.strip()
        ] if 'cco' in request.POST else []

        # Crear mensaje de correo
        mensaje_correo = EmailMessage(
            subject=request.POST.get('asunto'),
            body=request.POST.get('cuerpo'),
            from_email='madrizgt@gmail.com',
            to=lista_para,
            cc=lista_cc if lista_cc else None,
            bcc=lista_cco if lista_cco else None,
        )

        # Adjuntar archivos manuales
        for archivo in request.FILES.getlist('adjuntos_finales'):
            mensaje_correo.attach(
                archivo.name, 
                archivo.read(), 
                archivo.content_type
            )

        # Adjuntar PDF de ficha si existe
        datos_pdf_base64 = request.POST.get('ficha_pdf_data')
        if datos_pdf_base64:
            try:
                contenido_pdf = base64.b64decode(datos_pdf_base64)
                nombre_adjunto = request.POST.get('ficha_nombre', 'Ficha_adjunta.pdf')
                mensaje_correo.attach(
                    nombre_adjunto, 
                    contenido_pdf, 
                    'application/pdf'
                )
            except Exception as error:
                print(f"Error adjuntando PDF: {error}")

        try:
            # Enviar correo
            mensaje_correo.send(fail_silently=False)
            
            # ACTUALIZAR O CREAR REGISTRO EN tbl_Notificacion
            if notificacion:
                # Actualizar notificación existente
                notificacion.fecha = date.today()
                notificacion.para = ", ".join(lista_para)
                notificacion.cc = ", ".join(lista_cc) if lista_cc else ""
                notificacion.cco = ", ".join(lista_cco) if lista_cco else ""
                notificacion.save()
                mensaje_accion = "actualizada"
            else:
                # Crear nueva notificación
                nueva_notificacion = tbl_Notificacion.objects.create(
                    fecha=date.today(),
                    para=", ".join(lista_para),
                    cc=", ".join(lista_cc) if lista_cc else "",
                    cco=", ".join(lista_cco) if lista_cco else "",
                    # Relacionar con objetos si es necesario
                    # ccpp=ccpp_especifico,
                    # unidad=unidad,
                    # inspeccion=inspeccion,
                )
                mensaje_accion = "creada"

            return JsonResponse({
                'status': 'ok',
                'message': f'Correo enviado y notificación {mensaje_accion} exitosamente'
            })
            
        except Exception as error:
            return JsonResponse({
                'status': 'error', 
                'message': f'Error al enviar correo: {str(error)}'
            }, status=500)


def preparar_y_enviar_correo_____(request, ccpp_id, unidad_id, inspeccion_id):
    """
    Prepara y envía un correo con opción de adjuntar PDF de ficha.
    Se han eliminado las referencias a tbl_Notificacion.
    """
    # 1. Obtención de objetos base
    ccpp_especifico = get_object_or_404(tbl_CCPP, id=ccpp_id)
    unidad = get_object_or_404(tbl_Unidad, id=unidad_id)
    inspeccion = get_object_or_404(tbl_inspeccion, id=inspeccion_id)
    
    if request.method == 'GET':
        # Obtener plantilla de correo base
        plantilla_correo = tbl_Correo.objects.first()
        
        # 2. CORREOS PARA LOS INPUTS - Provienen siempre del CCPP
        correos_para_input = extraer_correos(
            f"{ccpp_especifico.administracion_edificio}, {ccpp_especifico.tecnico_cabecera}"
        )
        correos_cc_input = extraer_correos(
            f"{ccpp_especifico.operario_comunidad}, "
            f"{ccpp_especifico.empresa_especializada}, "
            f"{ccpp_especifico.tecnico_especialista}"
        )
        correos_cco_input = extraer_correos(ccpp_especifico.copia_oculta)

        # 3. CONTACTOS DISPONIBLES (Para el selector de la interfaz)
        contactos_disponibles = {
            'para': sorted(list(set([e.strip() for e in correos_para_input if e.strip()]))),
            'cc': sorted(list(set([e.strip() for e in correos_cc_input if e.strip()]))),
            'cco': sorted(list(set([e.strip() for e in correos_cco_input if e.strip()])))
        }
        
        # 4. REEMPLAZAR ETIQUETAS
        contexto_etiquetas = {
            'id_ccpp': ccpp_especifico.id_ccpp,
            'nombre_ccpp': ccpp_especifico.nombre,
            'unidad': unidad.unidad,
            'descripcion_unidad': unidad.descripcion,
            'inspeccion': inspeccion.nombre_inspeccion,
            'descripcion_inspeccion': inspeccion.descripcion_inspeccion,
            'notificacion_inspeccion': inspeccion.notificacionA_inspeccion,
        }
        
        asunto_renderizado = reemplazar_etiquetas(plantilla_correo.asunto, contexto_etiquetas)
        cuerpo_renderizado = reemplazar_etiquetas(plantilla_correo.cuerpo, contexto_etiquetas)

        # 5. VERIFICAR PDF DE FICHA
        datos_pdf_ficha = None
        nombre_ficha = None
        ficha_id = request.GET.get('ficha_id')
        
        if ficha_id:
            try:
                contenido_pdf = exportar_ficha_pdf(request, ficha_id, ccpp_id, return_buffer=True)
                if contenido_pdf:
                    datos_pdf_ficha = base64.b64encode(contenido_pdf).decode('utf-8')
                    nombre_ficha = f'Ficha_{ficha_id}.pdf'
            except Exception as error:
                print(f"Error generando PDF de ficha: {error}")

        return render(request, 'gestion/notificacion/enviar_correo.html', {
            'asunto': asunto_renderizado,
            'cuerpo': cuerpo_renderizado,
            'para': correos_para_input, 
            'cc': correos_cc_input,
            'cco': correos_cco_input,
            'contactos_disponibles': contactos_disponibles,
            'ficha_pdf_data': datos_pdf_ficha,
            'ficha_nombre': nombre_ficha,
            'ccpp_actual': ccpp_especifico,
            'unidad_actual': unidad,
            'inspeccion_actual': inspeccion,
        })

    if request.method == 'POST':
        # 6. PROCESAMIENTO DEL ENVÍO
        lista_para = [e.strip() for e in request.POST.get('para', '').split(',') if e.strip()]
        lista_cc = [e.strip() for e in request.POST.get('cc', '').split(',') if e.strip()]
        lista_cco = [e.strip() for e in request.POST.get('cco', '').split(',') if e.strip()]

        mensaje_correo = EmailMessage(
            subject=request.POST.get('asunto'),
            body=request.POST.get('cuerpo'),
            from_email='madrizgt@gmail.com',
            to=lista_para,
            cc=lista_cc if lista_cc else None,
            bcc=lista_cco if lista_cco else None,
        )

        # Adjuntos manuales
        for archivo in request.FILES.getlist('adjuntos_finales'):
            mensaje_correo.attach(archivo.name, archivo.read(), archivo.content_type)

        # Adjuntar PDF si existe en el POST
        datos_pdf_base64 = request.POST.get('ficha_pdf_data')
        if datos_pdf_base64:
            try:
                contenido_pdf = base64.b64decode(datos_pdf_base64)
                nombre_adjunto = request.POST.get('ficha_nombre', 'Ficha_adjunta.pdf')
                mensaje_correo.attach(nombre_adjunto, contenido_pdf, 'application/pdf')
            except Exception as error:
                print(f"Error adjuntando PDF: {error}")

        try:
            mensaje_correo.send(fail_silently=False)
            
            # Se elimina la creación/actualización de tbl_Notificacion
            return JsonResponse({
                'status': 'ok',
                'message': 'Correo enviado exitosamente'
            })
            
        except Exception as error:
            return JsonResponse({
                'status': 'error', 
                'message': f'Error al enviar correo: {str(error)}'
            }, status=500)




import base64
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.core.mail import get_connection, EmailMessage
from appAdministrador.models import ConfiguracionEmail  # Importante: verifica esta ruta

def preparar_y_enviar_correo(request, ccpp_id, unidad_id, inspeccion_id):
    """
    Prepara y envía un correo con opción de adjuntar PDF de ficha.
    Utiliza configuración SMTP dinámica desde la base de datos.
    """
    # 1. Obtención de objetos base
    ccpp_especifico = get_object_or_404(tbl_CCPP, id=ccpp_id)
    unidad = get_object_or_404(tbl_Unidad, id=unidad_id)
    inspeccion = get_object_or_404(tbl_inspeccion, id=inspeccion_id)
    
    if request.method == 'GET':
        # Obtener plantilla de correo base
        plantilla_correo = tbl_Correo.objects.first()
        
        # 2. CORREOS PARA LOS INPUTS - Provienen siempre del CCPP
        correos_para_input = extraer_correos(
            f"{ccpp_especifico.administracion_edificio}, {ccpp_especifico.tecnico_cabecera}"
        )
        correos_cc_input = extraer_correos(
            f"{ccpp_especifico.operario_comunidad}, "
            f"{ccpp_especifico.empresa_especializada}, "
            f"{ccpp_especifico.tecnico_especialista}"
        )
        correos_cco_input = extraer_correos(ccpp_especifico.copia_oculta)

        # 3. CONTACTOS DISPONIBLES (Para el selector de la interfaz)
        contactos_disponibles = {
            'para': sorted(list(set([e.strip() for e in correos_para_input if e.strip()]))),
            'cc': sorted(list(set([e.strip() for e in correos_cc_input if e.strip()]))),
            'cco': sorted(list(set([e.strip() for e in correos_cco_input if e.strip()])))
        }
        
        # 4. REEMPLAZAR ETIQUETAS
        contexto_etiquetas = {
            'id_ccpp': ccpp_especifico.id_ccpp,
            'nombre_ccpp': ccpp_especifico.nombre,
            'unidad': unidad.unidad,
            'descripcion_unidad': unidad.descripcion,
            'inspeccion': inspeccion.nombre_inspeccion,
            'descripcion_inspeccion': inspeccion.descripcion_inspeccion,
            'notificacion_inspeccion': inspeccion.notificacionA_inspeccion,
        }
        
        asunto_renderizado = reemplazar_etiquetas(plantilla_correo.asunto, contexto_etiquetas)
        cuerpo_renderizado = reemplazar_etiquetas(plantilla_correo.cuerpo, contexto_etiquetas)

        # 5. VERIFICAR PDF DE FICHA
        datos_pdf_ficha = None
        nombre_ficha = None
        ficha_id = request.GET.get('ficha_id')
        
        if ficha_id:
            try:
                contenido_pdf = exportar_ficha_pdf(request, ficha_id, ccpp_id, return_buffer=True)
                if contenido_pdf:
                    datos_pdf_ficha = base64.b64encode(contenido_pdf).decode('utf-8')
                    nombre_ficha = f'Ficha_{ficha_id}.pdf'
            except Exception as error:
                print(f"Error generando PDF de ficha: {error}")

        return render(request, 'gestion/notificacion/enviar_correo.html', {
            'asunto': asunto_renderizado,
            'cuerpo': cuerpo_renderizado,
            'para': correos_para_input, 
            'cc': correos_cc_input,
            'cco': correos_cco_input,
            'contactos_disponibles': contactos_disponibles,
            'ficha_pdf_data': datos_pdf_ficha,
            'ficha_nombre': nombre_ficha,
            'ccpp_actual': ccpp_especifico,
            'unidad_actual': unidad,
            'inspeccion_actual': inspeccion,
        })

    if request.method == 'POST':
        # --- NUEVA LÓGICA DE CONEXIÓN DINÁMICA ---
        # Obtener la configuración guardada por el usuario
        config_db = ConfiguracionEmail.objects.first()
        
        if not config_db:
            return JsonResponse({
                'status': 'error', 
                'message': 'No se encontró configuración SMTP. Por favor, configure el servidor de correo.'
            }, status=500)

        try:
            # Crear conexión SMTP al vuelo
            conexion_personalizada = get_connection(
                backend='django.core.mail.backends.smtp.EmailBackend',
                host=config_db.servidor_smtp,
                port=config_db.puerto,
                username=config_db.usuario_email,
                password=config_db.password_aplicacion,
                use_tls=config_db.usar_tls,
                fail_silently=False
            )
        except Exception as e:
            return JsonResponse({
                'status': 'error', 
                'message': f'Error al conectar con el servidor SMTP: {str(e)}'
            }, status=500)

        # 6. PROCESAMIENTO DEL ENVÍO
        lista_para = [e.strip() for e in request.POST.get('para', '').split(',') if e.strip()]
        lista_cc = [e.strip() for e in request.POST.get('cc', '').split(',') if e.strip()]
        lista_cco = [e.strip() for e in request.POST.get('cco', '').split(',') if e.strip()]

        mensaje_correo = EmailMessage(
            subject=request.POST.get('asunto'),
            body=request.POST.get('cuerpo'),
            from_email=config_db.usuario_email, # El remitente ahora es el configurado
            to=lista_para,
            cc=lista_cc if lista_cc else None,
            bcc=lista_cco if lista_cco else None,
            connection=conexion_personalizada, # Asignamos la conexión dinámica
        )

        # Adjuntos manuales
        for archivo in request.FILES.getlist('adjuntos_finales'):
            mensaje_correo.attach(archivo.name, archivo.read(), archivo.content_type)

        # Adjuntar PDF si existe en el POST
        datos_pdf_base64 = request.POST.get('ficha_pdf_data')
        if datos_pdf_base64:
            try:
                contenido_pdf = base64.b64decode(datos_pdf_base64)
                nombre_adjunto = request.POST.get('ficha_nombre', 'Ficha_adjunta.pdf')
                mensaje_correo.attach(nombre_adjunto, contenido_pdf, 'application/pdf')
            except Exception as error:
                print(f"Error adjuntando PDF: {error}")

        try:
            # Intentar el envío
            mensaje_correo.send(fail_silently=False)
            
            return JsonResponse({
                'status': 'ok',
                'message': 'Correo enviado exitosamente'
            })
            
        except Exception as error:
            return JsonResponse({
                'status': 'error', 
                'message': f'Error al enviar correo: {str(error)}'
            }, status=500)

def correo_enviado(request):
    return render(request, 'gestion/notificacion/correo_enviado.html')







        
#-------------GENERAR FICHA PDF----------------------------------------------------------------------------

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


def exportar_ficha_pdf(request, ficha_id, ccpp_id, return_buffer=False):
    """
    Genera el PDF de una ficha.
    
    Args:
        request: HttpRequest object
        ficha_id: ID de la ficha a generar
        ccpp_id: ID del CCPP
        return_buffer: Si True, retorna el buffer en bytes. Si False, retorna FileResponse.
    
    Returns:
        FileResponse si return_buffer=False, bytes si return_buffer=True
    """
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
        if return_buffer:
            return None
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
        if return_buffer:
            return None
        return FileResponse(
            io.BytesIO(f"Error al construir PDF: {str(e)}".encode()), 
            content_type='text/plain'
        )

    buffer.seek(0)
    
    if return_buffer:
        # Retorna el contenido en bytes para uso en memoria
        return buffer.getvalue()
    else:
        # Retorna FileResponse para descarga directa
        return FileResponse(
            buffer, 
            as_attachment=False, 
            filename=f'Ficha_{ficha.id}.pdf'
        )


