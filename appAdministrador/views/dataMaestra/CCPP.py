import logging
import re
from datetime import date, datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction, IntegrityError
from django.db.models import IntegerField
from django.db.models.functions import Substr, Cast
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect

# Importaciones locales
from appAdministrador.models import *

# Configuración de logger
logger = logging.getLogger(__name__)



"""
Función para mostrar el panel de CCPP
"""
@login_required
def vista_panel_ccpp(request):
    contexto = {}

    try:
        lista_ccpp = tbl_CCPP.objects.all()

        valores_id_ccpp = (
            tbl_CCPP.objects
            .values_list('id_ccpp', flat=True)
            .distinct()
            .order_by('id')
        )

        valores_anios_entrega = (
            tbl_CCPP.objects
            .exclude(fecha_entrega__isnull=True)
            .values_list('fecha_entrega__year', flat=True)
            .distinct()
            .order_by('fecha_entrega__year')
        )

        valores_cantidad_anios = (
            tbl_CCPP.objects
            .values_list('cantidad_anios', flat=True)
            .distinct()
            .order_by('cantidad_anios')
        )

        contexto = {
            'ccpps': lista_ccpp,
            'valores_id_ccpp': valores_id_ccpp,
            'valores_fecha_entrega': valores_anios_entrega,
            'valores_cantidad_anios': valores_cantidad_anios,
        }

    except Exception as error:
        mensaje_error = f"Ocurrió un error al cargar los datos de CCPP: {error}"
        logger.exception(mensaje_error)
        messages.error(request, "Error al cargar el panel de CCPP. Intente nuevamente más tarde.")

    return render(request, 'dataMaestra/ccpp/panel_ccpp.html', contexto)



"""
Función para crear o editar una CCPP
"""
@login_required
@csrf_protect
def gestionar_ccpp(request, ccpp_id=None):

    LIMITE_CARACTERES = 200
    RUTA_EXITO = 'ccpp'
    es_edicion = ccpp_id is not None
    
    if es_edicion:
        ccpp_actual = get_object_or_404(tbl_CCPP, pk=ccpp_id)
        cantidad_anios_original = ccpp_actual.cantidad_anios if ccpp_actual else 0
    else:
        ccpp_actual = None
        cantidad_anios_original = 0
    
    if request.method == 'GET':
        contexto = {'es_edicion': es_edicion}
        
        if es_edicion:
            fecha_entrega_str = ccpp_actual.fecha_entrega.strftime('%Y-%m-%d') if ccpp_actual.fecha_entrega else ''
            
            contexto.update({
                'ccpp': ccpp_actual,
                'ccpp_id': ccpp_id,
                'nuevo_id': ccpp_actual.id_ccpp,
                'ccpp_nombre': ccpp_actual.nombre,
                'fecha_entrega': fecha_entrega_str,
                'cantidad_anios': ccpp_actual.cantidad_anios,
                'direccion': ccpp_actual.direccion,
                'habilitada': ccpp_actual.habilitada,
                'operario_comunidad': ccpp_actual.operario_comunidad or '',
                'empresa_especializada': ccpp_actual.empresa_especializada or '',
                'administracion_edificio': ccpp_actual.administracion_edificio or '',
                'tecnico_especialista': ccpp_actual.tecnico_especialista or '',
                'tecnico_cabecera': ccpp_actual.tecnico_cabecera or '',
                'copia_oculta': ccpp_actual.copia_oculta or '',
            })
        else:
            ultimo = tbl_CCPP.objects.order_by('-id').first()
            if ultimo and ultimo.id_ccpp.startswith('CCPP'):
                try:
                    numero = int(ultimo.id_ccpp[4:])
                except ValueError:
                    numero = 0
            else:
                numero = 0
            nuevo_id = f"CCPP{str(numero + 1).zfill(3)}"
            
            contexto.update({
                'nuevo_id': nuevo_id,
                'ccpp_nombre': '',
                'fecha_entrega': date.today().isoformat(),
                'cantidad_anios': 10,
                'direccion': '',
                'habilitada': True,
                'operario_comunidad': '',
                'empresa_especializada': '',
                'administracion_edificio': '',
                'tecnico_especialista': '',
                'tecnico_cabecera': '',
                'copia_oculta': '',
            })
        
        return render(request, 'dataMaestra/ccpp/formulario_ccpp.html', contexto)
    
    # Lógica POST - Procesar formulario
    if request.method != 'POST':
        messages.error(request, "Método no permitido.")
        return redirect(reverse(RUTA_EXITO))
    
    datos_formulario = request.POST
    archivo_imagen = request.FILES.get('imagen')
    errores = {}
    
    # Recoger datos del formulario
    nombre = datos_formulario.get('ccpp_residencial', '').strip()
    fecha_entrega = datos_formulario.get('fecha_entrega') or None
    cantidad_anios_str = datos_formulario.get('cant_anos', '0').strip()
    direccion = datos_formulario.get('direccion', '').strip()
    habilitada = bool(datos_formulario.get('habilitada'))
    
    # Validaciones
    if not nombre:
        errores['ccpp_residencial'] = "El campo 'CCPP Residencial' es obligatorio."
    elif len(nombre) > LIMITE_CARACTERES:
        errores['ccpp_residencial'] = f"Máximo {LIMITE_CARACTERES} caracteres permitidos."
    
    if not direccion:
        errores['direccion'] = "El campo 'Dirección' es obligatorio."
    elif len(direccion) > LIMITE_CARACTERES:
        errores['direccion'] = f"Máximo {LIMITE_CARACTERES} caracteres permitidos."
    
    try:
        cantidad_anios = int(cantidad_anios_str)
        if cantidad_anios < 0:
            errores['cant_anos'] = "La cantidad de años no puede ser negativa."
        if cantidad_anios > 50:
            errores['cant_anos'] = "La cantidad de años no puede ser mayor a 50."
    except ValueError:
        errores['cant_anos'] = "Debe ingresar un número entero válido."
        cantidad_anios = 0
    
    if not fecha_entrega:
        errores['fecha_entrega'] = "El campo 'Fecha de entrega' es obligatorio."
    
    if archivo_imagen and archivo_imagen.size > 5 * 1024 * 1024:
        errores['imagen'] = "La imagen no debe superar los 5MB."
    
    if errores:
        contexto = {
            'es_edicion': es_edicion,
            'errores': errores,
            'ccpp': ccpp_actual,
            'ccpp_id': ccpp_id if es_edicion else None,
            'nuevo_id': id_ccpp if 'id_ccpp' in locals() else None,
            'ccpp_nombre': nombre,
            'fecha_entrega': fecha_entrega or '',
            'cantidad_anios': cantidad_anios_str,
            'direccion': direccion,
            'habilitada': habilitada,
            'operario_comunidad': datos_formulario.get('operario_comunidad', '').strip(),
            'empresa_especializada': datos_formulario.get('empresa_especializada', '').strip(),
            'administracion_edificio': datos_formulario.get('administracion_edificio', '').strip(),
            'tecnico_especialista': datos_formulario.get('tecnico_especialista', '').strip(),
            'tecnico_cabecera': datos_formulario.get('tecnico_cabecera', '').strip(),
            'copia_oculta': datos_formulario.get('copia_oculta', '').strip(),
        }
        
        messages.warning(request, "Por favor corrija los errores del formulario.")
        return render(request, 'dataMaestra/ccpp/formulario_ccpp.html', contexto)
    
    # Procesar fecha
    try:
        fecha_entrega_obj = datetime.strptime(fecha_entrega, '%Y-%m-%d').date()
    except ValueError:
        errores['fecha_entrega'] = "Formato de fecha inválido. Use YYYY-MM-DD."
        contexto = {
            'es_edicion': es_edicion,
            'errores': errores,
            'ccpp': ccpp_actual,
            'ccpp_id': ccpp_id if es_edicion else None,
            'ccpp_nombre': nombre,
            'fecha_entrega': fecha_entrega or '',
            'cantidad_anios': cantidad_anios_str,
            'direccion': direccion,
            'habilitada': habilitada,
            'operario_comunidad': datos_formulario.get('operario_comunidad', '').strip(),
            'empresa_especializada': datos_formulario.get('empresa_especializada', '').strip(),
            'administracion_edificio': datos_formulario.get('administracion_edificio', '').strip(),
            'tecnico_especialista': datos_formulario.get('tecnico_especialista', '').strip(),
            'tecnico_cabecera': datos_formulario.get('tecnico_cabecera', '').strip(),
            'copia_oculta': datos_formulario.get('copia_oculta', '').strip(),
        }
        messages.warning(request, "Error en formato de fecha.")
        return render(request, 'dataMaestra/ccpp/formulario_ccpp.html', contexto)
    
    try:
        with transaction.atomic():
            if es_edicion:
                # --- EDICIÓN ---
                # Primero, capturar el estado original para posibles rollbacks
                datos_originales = {
                    'cantidad_anios': ccpp_actual.cantidad_anios,
                    'nombre': ccpp_actual.nombre,
                    'fecha_entrega': ccpp_actual.fecha_entrega,
                    'direccion': ccpp_actual.direccion,
                }
                
                ccpp_actual.nombre = nombre
                ccpp_actual.fecha_entrega = fecha_entrega_obj
                ccpp_actual.cantidad_anios = cantidad_anios
                ccpp_actual.direccion = direccion
                ccpp_actual.habilitada = habilitada
                ccpp_actual.operario_comunidad = datos_formulario.get('operario_comunidad', '').strip()
                ccpp_actual.empresa_especializada = datos_formulario.get('empresa_especializada', '').strip()
                ccpp_actual.administracion_edificio = datos_formulario.get('administracion_edificio', '').strip()
                ccpp_actual.tecnico_especialista = datos_formulario.get('tecnico_especialista', '').strip()
                ccpp_actual.tecnico_cabecera = datos_formulario.get('tecnico_cabecera', '').strip()
                ccpp_actual.copia_oculta = datos_formulario.get('copia_oculta', '').strip()
                
                if archivo_imagen:
                    ccpp_actual.imagen = archivo_imagen
                
                ccpp_actual.save()
                
                if cantidad_anios != cantidad_anios_original:
                    unidades_asociadas = list(tbl_CCPP_Unidad.objects.filter(
                        ccpp=ccpp_actual
                    ).values_list('unidad_id', flat=True))
                    
                    if unidades_asociadas:
                        if cantidad_anios < cantidad_anios_original:
                            años_a_eliminar = range(cantidad_anios + 1, cantidad_anios_original + 1)
                            registros_a_eliminar = tbl_Cronograma.objects.filter(
                                ccpp=ccpp_actual, 
                                anios__in=años_a_eliminar
                            )
                            if registros_a_eliminar.exists():
                                registros_a_eliminar.delete()
                        
                        elif cantidad_anios > cantidad_anios_original:
                            años_a_agregar = range(cantidad_anios_original + 1, cantidad_anios + 1)
                            nuevos_cronogramas = []
                            
                            for unidad_id in unidades_asociadas:
                                for anio in años_a_agregar:
                                    nuevos_cronogramas.append(
                                        tbl_Cronograma(
                                            ccpp=ccpp_actual,
                                            unidad_id=unidad_id,
                                            anios=anio
                                        )
                                    )
                            
                            if nuevos_cronogramas:
                                for cronograma in nuevos_cronogramas:
                                    if tbl_Cronograma.objects.filter(
                                        ccpp=ccpp_actual,
                                        unidad_id=cronograma.unidad_id,
                                        anios=cronograma.anios
                                    ).exists():
                                        raise IntegrityError(
                                            f"Ya existe un cronograma para la unidad {cronograma.unidad_id} en el año {cronograma.anios}"
                                        )
                                
                                tbl_Cronograma.objects.bulk_create(nuevos_cronogramas)
                
                logger.info(f"CCPP {ccpp_actual.id_ccpp} actualizada por usuario {request.user.username}")
                messages.success(request, "CCPP actualizada correctamente y cronograma sincronizado.")
                
            else:
                # --- CREACIÓN ---
                ultimo = tbl_CCPP.objects.order_by('-id').first()
                if ultimo and ultimo.id_ccpp.startswith('CCPP'):
                    try:
                        numero = int(ultimo.id_ccpp[4:])
                    except ValueError:
                        numero = 0
                else:
                    numero = 0
                
                nuevo_numero = numero + 1
                id_ccpp = f"CCPP{str(nuevo_numero).zfill(3)}"
                
                if tbl_CCPP.objects.filter(id_ccpp=id_ccpp).exists():
                    raise IntegrityError(f"El ID {id_ccpp} ya existe en la base de datos")
                
                datos_creacion = {
                    'id_ccpp': id_ccpp,
                    'nombre': nombre,
                    'fecha_entrega': fecha_entrega_obj,
                    'cantidad_anios': cantidad_anios,
                    'direccion': direccion,
                    'habilitada': habilitada,
                    'operario_comunidad': datos_formulario.get('operario_comunidad', '').strip(),
                    'empresa_especializada': datos_formulario.get('empresa_especializada', '').strip(),
                    'administracion_edificio': datos_formulario.get('administracion_edificio', '').strip(),
                    'tecnico_especialista': datos_formulario.get('tecnico_especialista', '').strip(),
                    'tecnico_cabecera': datos_formulario.get('tecnico_cabecera', '').strip(),
                    'copia_oculta': datos_formulario.get('copia_oculta', '').strip(),
                }
                
                if archivo_imagen:
                    datos_creacion['imagen'] = archivo_imagen
                
                nueva_ccpp = tbl_CCPP.objects.create(**datos_creacion)
                
                logger.info(f"CCPP {id_ccpp} creada por usuario {request.user.username}")
                messages.success(request, "La CCPP fue registrada exitosamente.")
            
            return redirect(reverse(RUTA_EXITO))
    
    except IntegrityError as e:
        logger.exception(f"Error de integridad en BD al {'editar' if es_edicion else 'crear'} CCPP: {e}")
        error_msg = "Error de integridad de datos. Verifique que los datos sean consistentes."
        
    except Exception as error_guardado:
        logger.exception(f"Error al {'editar' if es_edicion else 'guardar'} la CCPP: {error_guardado}")
        error_msg = f"Ocurrió un error al {'editar' if es_edicion else 'guardar'} la CCPP. Intente nuevamente."
    

    contexto = {
        'es_edicion': es_edicion,
        'errores': {'error_bd': error_msg},
        'ccpp': ccpp_actual,
        'ccpp_id': ccpp_id if es_edicion else None,
        'nuevo_id': id_ccpp if 'id_ccpp' in locals() else None,
        'ccpp_nombre': nombre,
        'fecha_entrega': fecha_entrega or '',
        'cantidad_anios': cantidad_anios_str,
        'direccion': direccion,
        'habilitada': habilitada,
        'operario_comunidad': datos_formulario.get('operario_comunidad', '').strip(),
        'empresa_especializada': datos_formulario.get('empresa_especializada', '').strip(),
        'administracion_edificio': datos_formulario.get('administracion_edificio', '').strip(),
        'tecnico_especialista': datos_formulario.get('tecnico_especialista', '').strip(),
        'tecnico_cabecera': datos_formulario.get('tecnico_cabecera', '').strip(),
        'copia_oculta': datos_formulario.get('copia_oculta', '').strip(),
    }
    
    messages.error(request, error_msg)
    return render(request, 'dataMaestra/ccpp/formulario_ccpp.html', contexto)



"""
Función para eliminar una CCPP y todas sus dependencias de forma atómica
"""
@login_required
@csrf_protect
def eliminar_ccpp(request, ccpp_id):
    """
    Elimina una CCPP, sus archivos y dependencias (Cronogramas, Notificaciones, Documentos)
    """
    nombre_ruta_listado = 'ccpp'
    
    try:
        with transaction.atomic():
            # Obtenemos la CCPP y bloqueamos la fila para la transacción
            ccpp_actual = get_object_or_404(tbl_CCPP.objects.select_for_update(), pk=ccpp_id)
            
            # --- PREPARAR RESUMEN (Antes de borrar) ---
            cronogramas_qs = tbl_Cronograma.objects.filter(ccpp=ccpp_actual)
            c_count = cronogramas_qs.count()
            
            # Contar notificaciones que dependen de esos cronogramas
            n_count = tbl_Notificacion.objects.filter(FK_cronograma__in=cronogramas_qs).count()
            
            # Contar relaciones con unidades
            r_count = tbl_CCPP_Unidad.objects.filter(ccpp=ccpp_actual).count()
            
            info_ccpp = {
                'id': ccpp_actual.id_ccpp,
                'nombre': ccpp_actual.nombre,
                'cronogramas': c_count,
                'notificaciones': n_count,
                'relaciones_unidades': r_count
            }

            # --- EJECUTAR ELIMINACIÓN ---
            
            # 1. Eliminar archivos físicos primero (mientras existan los registros en BBDD)
            eliminar_archivos_ccpp(ccpp_actual)
            
            # 2. Eliminar el objeto principal
            # Al eliminar ccpp_actual, Django/SQL activará el CASCADE en:
            # - tbl_CCPP_Unidad (FK ccpp)
            # - tbl_Cronograma (FK ccpp) -> Y este a su vez borrará tbl_Notificacion -> y este tbl_NotificacionDocumento
            ccpp_actual.delete()
            
            # --- LOGS Y MENSAJES ---
            logger.info(f"CCPP eliminada completamente: {info_ccpp} por usuario {request.user.username}")
            
            mensaje_exito = f"La CCPP '{info_ccpp['nombre']}' fue eliminada con éxito."
            
            detalles = []
            if info_ccpp['cronogramas'] > 0: detalles.append(f"{info_ccpp['cronogramas']} cronogramas")
            if info_ccpp['notificaciones'] > 0: detalles.append(f"{info_ccpp['notificaciones']} notificaciones")
            if info_ccpp['relaciones_unidades'] > 0: detalles.append(f"{info_ccpp['relaciones_unidades']} unidades vinculadas")
            
            if detalles:
                mensaje_exito += f" Se limpiaron automáticamente: {', '.join(detalles)}."
            
            messages.success(request, mensaje_exito)
            return redirect(reverse(nombre_ruta_listado))

    except tbl_CCPP.DoesNotExist:
        logger.warning(f"Intento de eliminar CCPP inexistente: {ccpp_id}")
        messages.error(request, "La CCPP ya no existe en el sistema.")
        return redirect(reverse(nombre_ruta_listado))
    
    except Exception as e:
        logger.exception(f"ERROR al eliminar CCPP {ccpp_id}: {str(e)}")
        messages.error(
            request, 
            "No se pudo eliminar la CCPP debido a un error de integridad. "
            "Los cambios han sido revertidos."
        )
        return redirect(reverse(nombre_ruta_listado))

def eliminar_archivos_ccpp(ccpp):
    """
    Elimina archivos físicos asociados a la CCPP navegando por sus relaciones.
    Nota: No elimina Fichas ya que estas dependen de Unidades (catálogo general).
    """
    try:
        # 1. Eliminar imagen principal de la CCPP
        if ccpp.imagen and hasattr(ccpp.imagen, 'storage'):
            if ccpp.imagen.storage.exists(ccpp.imagen.name):
                ccpp.imagen.delete(save=False)
                logger.info(f"Imagen de CCPP eliminada: {ccpp.imagen.name}")

        # 2. Eliminar documentos de Notificaciones asociados a través del Cronograma
        # Buscamos todos los cronogramas de esta CCPP
        cronogramas = tbl_Cronograma.objects.filter(ccpp=ccpp)
        
        for crono in cronogramas:
            # Buscamos las notificaciones de cada cronograma
            notificaciones = tbl_Notificacion.objects.filter(FK_cronograma=crono)
            
            for noti in notificaciones:
                # Buscamos los documentos de cada notificación
                documentos = tbl_NotificacionDocumento.objects.filter(FK_notificacion=noti)
                
                for doc in documentos:
                    if doc.archivo and hasattr(doc.archivo, 'storage'):
                        if doc.archivo.storage.exists(doc.archivo.name):
                            doc.archivo.delete(save=False)
                            logger.info(f"Archivo de notificación eliminado: {doc.archivo.name}")
        
    except Exception as e:
        logger.warning(f"Error al eliminar archivos físicos de CCPP {ccpp.id_ccpp}: {e}")


"""
Clona una CCPP existente (tbl_CCPP), copia sus unidades asignadas (tbl_CCPP_Unidad)
y genera automáticamente su cronograma vacío (tbl_Cronograma), incluyendo el Año 0.
"""
@login_required
@csrf_protect
def clonar_ccpp(request, ccpp_id):

    RUTA_EXITO = 'ccpp'
    
    # Verificar método HTTP
    if request.method != 'POST':
        messages.error(request, "Método no permitido para esta acción.")
        return redirect(reverse(RUTA_EXITO))
    
    # Obtener la CCPP original o devolver 404
    try:
        ccpp_original = get_object_or_404(tbl_CCPP, pk=ccpp_id)
    except Exception:
        messages.error(request, "La CCPP original no existe o no se pudo cargar.")
        return redirect(reverse(RUTA_EXITO))
    
    # Bloque de clonación atómica
    try:
        with transaction.atomic():
            # 1. Generar nuevo ID único
            nuevo_id = generar_nuevo_id_ccpp()
            
            # 2. Verificar que el ID no exista (doble seguridad)
            if tbl_CCPP.objects.filter(id_ccpp=nuevo_id).exists():
                raise IntegrityError(f"El ID {nuevo_id} ya existe en la base de datos.")
            
            # 3. Obtener relaciones originales y sus IDs de unidad
            relaciones_originales = list(tbl_CCPP_Unidad.objects.filter(ccpp=ccpp_original))
            unidades_ids = [rel.unidad_id for rel in relaciones_originales]
            
            # 4. CLONAR LA CCPP (sin guardar aún)
            ccpp_clon = tbl_CCPP(
                id_ccpp=nuevo_id,
                nombre=f"CLON de {ccpp_original.nombre}",  # Nombre más claro
                fecha_entrega=ccpp_original.fecha_entrega,
                cantidad_anios=ccpp_original.cantidad_anios,
                direccion=ccpp_original.direccion,
                habilitada=ccpp_original.habilitada,
                operario_comunidad=ccpp_original.operario_comunidad,
                empresa_especializada=ccpp_original.empresa_especializada,
                administracion_edificio=ccpp_original.administracion_edificio,
                tecnico_especialista=ccpp_original.tecnico_especialista,
                tecnico_cabecera=ccpp_original.tecnico_cabecera,
                copia_oculta=ccpp_original.copia_oculta,
                clon_ccpp=ccpp_original.id_ccpp,
                # No clonar imagen por defecto (evita problemas con archivos)
                imagen=None
            )
            
            # 5. Guardar la CCPP clonada
            ccpp_clon.save()
            
            # 6. Copiar relaciones de unidades (si existen)
            if relaciones_originales:
                nuevas_relaciones = [
                    tbl_CCPP_Unidad(ccpp=ccpp_clon, unidad=relacion.unidad)
                    for relacion in relaciones_originales
                ]
                tbl_CCPP_Unidad.objects.bulk_create(nuevas_relaciones)
            
            # 7. Crear cronograma completo (si hay unidades y años definidos)
            cronogramas_a_crear = []
            if unidades_ids and ccpp_clon.cantidad_anios:
                # Definir el rango de años, incluyendo el Año 0
                rango_anios = range(ccpp_clon.cantidad_anios + 1)
                
                for anio in rango_anios:
                    for unidad_id in unidades_ids:
                        cronogramas_a_crear.append(
                            tbl_Cronograma(
                                ccpp=ccpp_clon,
                                unidad_id=unidad_id,
                                anios=anio
                            )
                        )
                
                if cronogramas_a_crear:
                    # Verificar que no existan cronogramas duplicados (seguridad adicional)
                    cronogramas_existentes = tbl_Cronograma.objects.filter(
                        ccpp=ccpp_clon,
                        unidad_id__in=unidades_ids
                    ).values_list('unidad_id', 'anios')
                    
                    for cronograma in cronogramas_a_crear:
                        if (cronograma.unidad_id, cronograma.anios) in cronogramas_existentes:
                            raise IntegrityError(
                                f"Ya existe un cronograma para la unidad {cronograma.unidad_id} "
                                f"en el año {cronograma.anios}"
                            )
                    
                    # Crear todos los cronogramas en una sola operación
                    tbl_Cronograma.objects.bulk_create(cronogramas_a_crear)
            
            # NOTA: NO se clonan las fichas técnicas (tbl_Ficha) ni sus controles
            
            # 8. Registrar la clonación en logs
            logger.info(
                f"CCPP clonada: {ccpp_original.id_ccpp} -> {ccpp_clon.id_ccpp} - "
                f"Usuario: {request.user.username} - "
                f"Unidades copiadas: {len(relaciones_originales)} - "
                f"Cronogramas creados: {len(cronogramas_a_crear)}"
            )
        
        # 9. Mensaje de éxito (fuera del bloque atómico)
        resumen = [
            f"Nuevo ID: {ccpp_clon.id_ccpp}",
            f"Unidades copiadas: {len(relaciones_originales)}",
            f"Cronogramas creados: {len(cronogramas_a_crear)}"
        ]
        
        messages.success(
            request,
            f"CCPP '{ccpp_original.nombre}' clonada exitosamente. " +
            " | ".join(resumen)
        )
        
        # 10. Redirigir a edición del clon
        return redirect('editar_ccpp', ccpp_id=ccpp_clon.pk)
        
    except IntegrityError as e:
        logger.error(f"Error de integridad al clonar CCPP: {e}")
        messages.error(
            request,
            f"Error de integridad de datos: {str(e)[:100]}. "
            "La operación fue revertida completamente."
        )
        
    except Exception as error:
        logger.exception(f"Error inesperado al clonar la CCPP: {error}")
        messages.error(
            request,
            f"Ocurrió un error inesperado al clonar la CCPP. "
            "Todos los cambios fueron revertidos para mantener la integridad de los datos."
        )
    
    # Si hay error, redirigir a la lista
    return redirect(reverse(RUTA_EXITO))

def generar_nuevo_id_ccpp():
    """
    Genera un nuevo ID único para CCPP en formato CCPPXXX
    Optimizado y más robusto que la versión anterior
    """
    try:
        # Método 1: Usar el sistema original de numeración con Cast
        ultimo = (
            tbl_CCPP.objects
            .filter(id_ccpp__regex=r'^CCPP\d+$')  # Solo IDs con formato correcto
            .annotate(numero_id=Cast(Substr('id_ccpp', 5), IntegerField()))
            .order_by('-numero_id')
            .first()
        )
        
        if ultimo and ultimo.numero_id:
            numero = ultimo.numero_id + 1
        else:
            # Método 2: Buscar manualmente como fallback
            import re
            max_numero = 0
            ccpps = tbl_CCPP.objects.filter(id_ccpp__startswith='CCPP')
            
            for ccpp in ccpps:
                match = re.search(r'CCPP(\d+)', ccpp.id_ccpp)
                if match:
                    try:
                        num = int(match.group(1))
                        max_numero = max(max_numero, num)
                    except ValueError:
                        continue
            
            numero = max_numero + 1 if max_numero > 0 else 1
        
        # Formatear con ceros a la izquierda
        return f"CCPP{str(numero).zfill(3)}"
        
    except Exception as e:
        logger.warning(f"Error al generar nuevo ID CCPP: {e}")
        # Método 3: Fallback simple
        ultimo_simple = tbl_CCPP.objects.order_by('-id').first()
        if ultimo_simple and ultimo_simple.id_ccpp.startswith('CCPP'):
            try:
                match = re.search(r'CCPP(\d+)', ultimo_simple.id_ccpp)
                if match:
                    numero = int(match.group(1)) + 1
                else:
                    numero = 1
            except (ValueError, AttributeError):
                numero = 1
        else:
            numero = 1
        
        return f"CCPP{str(numero).zfill(3)}"




"""
Asigna o remueve unidades a una CCPP específica y actualiza el cronograma en consecuencia.
"""
@login_required
def gestionUnidades_ccpp(request, ccpp_id):
    ccpp = get_object_or_404(tbl_CCPP, pk=ccpp_id) 

    if request.method == 'POST':
        selected_unit_ids = set(int(uid) for uid in request.POST.getlist('selected_units') if uid.isdigit()) 
        current_unit_ids = set(
            tbl_CCPP_Unidad.objects.filter(ccpp=ccpp).values_list('unidad_id', flat=True)
        )

        unidades_a_eliminar = current_unit_ids - selected_unit_ids
        unidades_a_agregar = selected_unit_ids - current_unit_ids

        with transaction.atomic():
            if unidades_a_eliminar:
                tbl_Cronograma.objects.filter(ccpp=ccpp, unidad_id__in=unidades_a_eliminar).delete()
                tbl_CCPP_Unidad.objects.filter(ccpp=ccpp, unidad_id__in=unidades_a_eliminar).delete()

            nuevas_asociaciones = []
            unidades_existentes_a_agregar = []
            
            for unit_id in unidades_a_agregar:
                try:
                    unidad = tbl_Unidad.objects.get(pk=unit_id)
                    nuevas_asociaciones.append(tbl_CCPP_Unidad(ccpp=ccpp, unidad=unidad))
                    unidades_existentes_a_agregar.append(unidad)
                except tbl_Unidad.DoesNotExist:
                    continue

            tbl_CCPP_Unidad.objects.bulk_create(nuevas_asociaciones)            
            
            cantidad_anios = ccpp.cantidad_anios or 1 
            cronogramas_a_crear = []
            
            for unidad_obj in unidades_existentes_a_agregar: 
                for anio in range(cantidad_anios + 1):  
                    cronogramas_a_crear.append(
                        tbl_Cronograma(
                            ccpp=ccpp,
                            unidad=unidad_obj,
                            anios=anio 
                        )
                    )

            if cronogramas_a_crear:
                 tbl_Cronograma.objects.bulk_create(cronogramas_a_crear)

        messages.success(request, f'Unidades y cronograma actualizados correctamente para {ccpp.nombre}')
        return redirect('gestionUnidades_ccpp', ccpp_id=ccpp_id)

    else:
        unidades = tbl_Unidad.objects.all()
        assigned_unit_ids = tbl_CCPP_Unidad.objects.filter(ccpp=ccpp).values_list('unidad_id', flat=True)

        valores_unidad = tbl_Unidad.objects.values_list('unidad', flat=True).distinct().order_by('unidad')
        valores_capitulo = tbl_Unidad.objects.values_list('capitulo', flat=True).distinct().order_by('capitulo')
        valores_observacion = tbl_Unidad.objects.values_list('observacion', flat=True).distinct().order_by('observacion')
        valores_doc = tbl_Unidad.objects.values_list('doc', flat=True).distinct().order_by('doc')

        context = {
            'ccpp': ccpp,
            'unidades': unidades,
            'assigned_unit_ids': list(assigned_unit_ids),
            'valores_unidad': valores_unidad,
            'valores_capitulo': valores_capitulo,
            'valores_observacion': valores_observacion,
            'valores_doc': valores_doc,
        }

        return render(request, 'dataMaestra/ccpp/gestionUnidades_ccpp.html', context)
    



