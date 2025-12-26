
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
import re
from django.contrib import messages
from appAdministrador.models import tbl_Unidad
import logging
from django.contrib.auth.decorators import login_required
logger = logging.getLogger(__name__)

@login_required
def vista_unidad(request):
    if request.method != 'GET':
        messages.error(request, "Método no permitido.")
        return render(request, 'dataMaestra/unidad/panel_unidad.html', {})

    try:
        lista_unidades = tbl_Unidad.objects.all()

        valores_unidad = (
            tbl_Unidad.objects
            .values_list('unidad', flat=True)
            .distinct()
            .order_by('unidad')
        )

        valores_capitulo = (
            tbl_Unidad.objects
            .values_list('capitulo', flat=True)
            .distinct()
            .order_by('capitulo')
        )

        valores_observacion = (
            tbl_Unidad.objects
            .values_list('observacion', flat=True)
            .distinct()
            .order_by('observacion')
        )

        valores_doc = (
            tbl_Unidad.objects
            .values_list('doc', flat=True)
            .distinct()
            .order_by('doc')
        )

        contexto = {
            'unidades': lista_unidades,
            'valores_unidad': valores_unidad,
            'valores_capitulo': valores_capitulo,
            'valores_observacion': valores_observacion,
            'valores_doc': valores_doc,
        }

        return render(request, 'dataMaestra/unidad/panel_unidad.html', contexto)

    except Exception as error:
        logger.exception(f"Error al cargar la vista de unidades: {error}")
        messages.error(request, "Ocurrió un error al cargar los datos de unidades. Intente nuevamente más tarde.")
        return render(request, 'dataMaestra/unidad/panel_unidad.html', {})  






@login_required
def gestionar_unidad(request, unidad_id=None):
    """
    Función unificada para crear (unidad_id=None) o editar (unidad_id) una Unidad
    """
    LIMITE_CARACTERES = 200
    RUTA_EXITO = 'unidad'
    es_edicion = unidad_id is not None
    
    if es_edicion:
        unidad_existente = get_object_or_404(tbl_Unidad, pk=unidad_id)
    else:
        unidad_existente = None
    
    # Lógica GET - Mostrar formulario
    if request.method == 'GET':
        contexto = {'es_edicion': es_edicion}
        
        if es_edicion:
            contexto.update({
                'unidad_id': unidad_id,
                'unidad_val': unidad_existente.unidad,
                'unidad_nombre': unidad_existente.unidad,  
                'capitulo_val': unidad_existente.capitulo,
                'descripcion_val': unidad_existente.descripcion,
                'observacion_val': unidad_existente.observacion,
                'doc_val': unidad_existente.doc,
            })
        else:
            # Contexto vacío para creación
            contexto.update({
                'unidad_val': '',
                'capitulo_val': '',
                'descripcion_val': '',
                'observacion_val': '',
                'doc_val': '',
            })
        
        return render(request, 'dataMaestra/unidad/formulario_unidad.html', contexto)
    
    # Lógica POST - Procesar formulario
    if request.method != 'POST':
        messages.error(request, "Método no permitido.")
        return redirect(reverse(RUTA_EXITO))
    
    datos = request.POST
    errores = {}
    
    # Recoger datos del formulario
    nombre_unidad = datos.get('unidad', '').strip()
    nombre_capitulo = datos.get('capitulo', '').strip()
    descripcion = datos.get('descripcion', '').strip()
    observacion = datos.get('observacion', '').strip()
    codigo_doc = datos.get('doc', '').strip()
    
    # Validaciones comunes
    if not nombre_unidad:
        errores['unidad'] = "El campo 'Unidad' es obligatorio."
    elif len(nombre_unidad) > LIMITE_CARACTERES:
        errores['unidad'] = f"Máximo {LIMITE_CARACTERES} caracteres permitidos."
    elif es_edicion:
        # Para edición: verificar que no haya otra unidad con el mismo nombre
        if tbl_Unidad.objects.filter(unidad=nombre_unidad).exclude(pk=unidad_id).exists():
            errores['unidad'] = "Ya existe otra unidad con ese nombre."
    else:
        # Para creación: verificar que no exista una unidad con el mismo nombre
        if tbl_Unidad.objects.filter(unidad=nombre_unidad).exists():
            errores['unidad'] = "Ya existe una unidad con ese nombre."
    
    if not nombre_capitulo:
        errores['capitulo'] = "El campo 'Capítulo' es obligatorio."
    elif len(nombre_capitulo) > LIMITE_CARACTERES:
        errores['capitulo'] = f"Máximo {LIMITE_CARACTERES} caracteres permitidos."
    
    if descripcion and len(descripcion) > LIMITE_CARACTERES:
        errores['descripcion'] = f"Máximo {LIMITE_CARACTERES} caracteres permitidos."
    
    if observacion and len(observacion) > LIMITE_CARACTERES:
        errores['observacion'] = f"Máximo {LIMITE_CARACTERES} caracteres permitidos."
    
    # Validación del formato del doc
    patron_doc = r'^\d{2}-\d{2}-\d{2}$'
    if not codigo_doc:
        errores['doc'] = "El campo 'Doc' es obligatorio."
    elif not re.match(patron_doc, codigo_doc):
        errores['doc'] = "Formato inválido. Use el formato 00-00-00."
    
    # Preparar contexto para rellenar formulario en caso de errores
    contexto = {
        'es_edicion': es_edicion,
        'unidad_id': unidad_id if es_edicion else None,
        'unidad_val': nombre_unidad,
        'unidad_nombre': nombre_unidad,  # Para mostrar en título y modal
        'capitulo_val': nombre_capitulo,
        'descripcion_val': descripcion,
        'observacion_val': observacion,
        'doc_val': codigo_doc,
    }
    
    # Si hay errores, persistimos datos y mostramos mensajes
    if errores:
        contexto['errores'] = errores
        messages.warning(request, "Por favor corrija los errores del formulario.")
        return render(request, 'dataMaestra/unidad/formulario_unidad.html', contexto)
    
    # Intentamos guardar/actualizar la unidad
    try:
        if es_edicion:
            # --- EDICIÓN ---
            unidad_existente.unidad = nombre_unidad
            unidad_existente.capitulo = nombre_capitulo
            unidad_existente.descripcion = descripcion
            unidad_existente.observacion = observacion
            unidad_existente.doc = codigo_doc
            unidad_existente.save()
            
            messages.success(request, "Unidad actualizada correctamente.")
        else:
            # --- CREACIÓN ---
            tbl_Unidad.objects.create(
                unidad=nombre_unidad,
                capitulo=nombre_capitulo,
                descripcion=descripcion,
                observacion=observacion,
                doc=codigo_doc,
            )
            messages.success(request, "La unidad fue registrada exitosamente.")
        
        return redirect(reverse(RUTA_EXITO))
    
    except Exception as error_guardado:
        error_msg = f"Ocurrió un error al {'editar' if es_edicion else 'guardar'} la unidad. Intente nuevamente."
        errores['error_bd'] = error_msg
        contexto['errores'] = errores
        contexto['errors'] = {'db_error': error_msg}  # Para compatibilidad con el modal de error
        
        messages.error(request, error_msg)
        return render(request, 'dataMaestra/unidad/formulario_unidad.html', contexto)







@login_required
def eliminar_unidad(request, unidad_id):
    RUTA_LISTADO = 'unidad'
    unidad_a_eliminar = get_object_or_404(tbl_Unidad, pk=unidad_id)

    if request.method != 'POST':
        messages.error(request, "Método no permitido para eliminar unidades.")
        return redirect(reverse(RUTA_LISTADO))

    try:
        unidad_a_eliminar.delete()
        messages.success(request, "Unidad eliminada correctamente.")
    except Exception as error_eliminacion:
        messages.error(
            request,
            "No se pudo eliminar la unidad."
        )

    return redirect(reverse(RUTA_LISTADO))