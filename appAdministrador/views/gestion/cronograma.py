from django.shortcuts import render, get_object_or_404, redirect
from collections import defaultdict # Necesitas importar defaultdict
# ... (Imports) ...
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from datetime import date

from appAdministrador.models import *
from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Prefetch

from django.contrib.auth.decorators import login_required

@login_required
def vista_panel_principal(request):
    """
    Recupera solo las CCPP habilitadas de la base de datos y las pasa a la plantilla.
    """
    ccpp_listado = tbl_CCPP.objects.filter(habilitada=True)

    contexto = {
        'ccpp_listado': ccpp_listado,
    }
    return render(request, 'gestion/panel_principal.html', contexto)




# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import date







def contar_notificaciones_respuestas(cronograma_ids):
    """
    Función auxiliar que cuenta notificaciones y respuestas por cronograma
    """
    notificaciones_totales = {}
    
    # Usar una sola consulta para mayor eficiencia - AJUSTADO
    notificaciones = tbl_Notificacion.objects.filter(
        FK_cronograma_id__in=cronograma_ids
    ).only('FK_cronograma_id', 'NotificacionContestada')
    
    for notif in notificaciones:
        cronograma_id = notif.FK_cronograma_id
        
        if cronograma_id not in notificaciones_totales:
            notificaciones_totales[cronograma_id] = {
                'total_noti': 0,
                'total_resp': 0
            }
        
        # Sumar notificación
        notificaciones_totales[cronograma_id]['total_noti'] += 1
        
        # Sumar respuesta si está contestada
        if notif.NotificacionContestada:
            notificaciones_totales[cronograma_id]['total_resp'] += 1
    
    return notificaciones_totales


@login_required
def vista_actualizar_cronograma(request, ccpp_id):
    MESES_TITULOS = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    MESES_CAMPOS = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
                    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

    ccpp = get_object_or_404(tbl_CCPP, pk=ccpp_id)
    
    # Obtener año actual
    anio_actual_real = date.today().year
    anio_base = ccpp.fecha_entrega.year if ccpp.fecha_entrega else anio_actual_real
    
    # Calcular años disponibles
    anos_disponibles = []
    try:
        cantidad_anios = int(ccpp.cantidad_anios or 0)
        if cantidad_anios >= 0:
            anos_disponibles = [
                f"{indice} - {anio_base + indice}"
                for indice in range(cantidad_anios + 1)
            ]
    except ValueError:
        pass
    
    # Determinar el año a filtrar por defecto (solo para el select)
    anio_a_filtrar_por_defecto = None
    
    # Buscar el año actual en los años disponibles de la CCPP
    for indice, anio_formateado in enumerate(anos_disponibles):
        # Extraer el año calendario del formato "indice - año"
        anio_calendario_str = anio_formateado.split(' - ')[1]
        try:
            anio_calendario = int(anio_calendario_str)
            if anio_calendario == anio_actual_real:
                anio_a_filtrar_por_defecto = anio_formateado
                break
        except (ValueError, IndexError):
            continue
    
    # Si no se encuentra el año actual, filtrar por el primer año (índice 0)
    if anio_a_filtrar_por_defecto is None and anos_disponibles:
        anio_a_filtrar_por_defecto = anos_disponibles[0]
    
    # Cargar inspecciones y mapear por PK
    inspecciones = tbl_inspeccion.objects.all().only('pk', 'codigo_inspeccion', 'color_inspeccion', 'nombre_inspeccion')
    inspecciones_map = {
        str(insp.pk): {'codigo': insp.codigo_inspeccion, 'color': insp.color_inspeccion}
        for insp in inspecciones
    }
    opciones_inspeccion_data = [
        {
            'id': insp.pk,
            'codigo_inspeccion': insp.codigo_inspeccion,
            'nombre_inspeccion': insp.nombre_inspeccion,
            'color_inspeccion': insp.color_inspeccion
        }
        for insp in inspecciones
    ]

    # Guardado de cronograma (POST) - CORREGIDO PARA NOTAS
    if request.method == 'POST':
        actualizaciones = 0
        errores = 0

        for key, value in request.POST.items():
            if key == 'csrfmiddlewaretoken':
                continue
                
            try:
                # Manejar campos de nota - IMPORTANTE: key es 'nota_X'
                if key.startswith('nota_'):
                    pk_str = key.split('_')[1]
                    try:
                        cronograma = tbl_Cronograma.objects.get(pk=int(pk_str))
                        valor_actual = cronograma.nota or ""
                        nuevo_valor = value.strip() if value else ""
                        
                        if valor_actual != nuevo_valor:
                            cronograma.nota = nuevo_valor
                            cronograma.save(update_fields=['nota'])
                            actualizaciones += 1
                    except tbl_Cronograma.DoesNotExist:
                        errores += 1
                        messages.error(request, f"No se encontró el cronograma con pk {pk_str}")
                    continue
                
                # Manejar campos de meses
                if '_' not in key:
                    continue
                
                # IMPORTANTE: Separar correctamente 'mes_pk' usando rsplit
                parts = key.rsplit('_', 1)
                if len(parts) != 2:
                    continue
                
                mes, pk_str = parts
                if mes not in MESES_CAMPOS:
                    continue

                try:
                    cronograma = tbl_Cronograma.objects.get(pk=int(pk_str))
                    nuevo_valor = str(value) if value else ''
                    valor_actual = str(getattr(cronograma, mes) or '')
                    
                    if valor_actual != nuevo_valor:
                        setattr(cronograma, mes, nuevo_valor)
                        cronograma.save(update_fields=[mes])
                        actualizaciones += 1
                except tbl_Cronograma.DoesNotExist:
                    errores += 1
                    messages.error(request, f"No se encontró el cronograma con pk {pk_str}")
                except ValueError:
                    errores += 1
                    messages.error(request, f"ID inválido en campo {key}")

            except Exception as error:
                    errores += 1
                    messages.error(request, f"Error en campo {key}: {str(error)[:100]}")

        if errores:
            messages.warning(request, f"Se omitieron {errores} errores durante el guardado.")
        if actualizaciones:
            messages.success(request, f"Se actualizaron {actualizaciones} registros.")
        elif errores == 0:
            messages.info(request, "No se detectaron cambios.")

        return redirect('gestion_ccpp', ccpp_id=ccpp_id)

    # Lectura de cronograma (GET) - CARGAR TODOS LOS AÑOS
    unidades_ccpp = tbl_CCPP_Unidad.objects.filter(ccpp=ccpp).select_related('unidad').order_by('unidad__orden')
    
    # Obtener todos los capítulos únicos para el filtro
    capitulos_disponibles = sorted(set(unidad.unidad.capitulo for unidad in unidades_ccpp))
    
    # IMPORTANTE: Cargar TODOS los cronogramas, no filtrar por año en la consulta
    cronogramas = tbl_Cronograma.objects.filter(ccpp=ccpp).select_related('unidad').order_by('unidad__orden', 'anios')
    
    # Obtener IDs de cronogramas
    cronograma_ids = [c.pk for c in cronogramas]
    
    # Consultar notificaciones en una sola consulta usando la función auxiliar - AJUSTADO
    notificaciones_totales = contar_notificaciones_respuestas(cronograma_ids)
    
    # Para contar por mes también (si aún se necesita) - AJUSTADO
    notificaciones_por_mes = tbl_Notificacion.objects.filter(
        FK_cronograma_id__in=cronograma_ids
    ).values('FK_cronograma_id', 'PK_mes', 'NotificacionContestada')
    
    # Crear diccionario para contar notificaciones por cronograma y mes
    notificaciones_por_cronograma_mes = {}
    notificaciones_contestadas_por_cronograma_mes = {}
    
    for notif in notificaciones_por_mes:
        cronograma_id = notif['FK_cronograma_id']
        mes = notif['PK_mes']
        contestada = notif['NotificacionContestada']
        
        # Contador total de notificaciones
        key_total = f"{cronograma_id}_{mes}"
        notificaciones_por_cronograma_mes[key_total] = notificaciones_por_cronograma_mes.get(key_total, 0) + 1
        
        # Contador de notificaciones contestadas
        if contestada:
            key_contestada = f"{cronograma_id}_{mes}_contestada"
            notificaciones_contestadas_por_cronograma_mes[key_contestada] = notificaciones_contestadas_por_cronograma_mes.get(key_contestada, 0) + 1

    # Agrupar cronogramas por unidad y obtener datos adicionales
    cronograma_por_unidad = {}
    for registro in cronogramas:
        nombre_unidad = registro.unidad.unidad
        capitulo_unidad = registro.unidad.capitulo
        observacion_unidad = registro.unidad.observacion
        anio_servicio = registro.anios
        anio_calendario = anio_base + anio_servicio
        anio_formateado = f"{anio_servicio} - {anio_calendario}"

        # Obtener contadores totales para este cronograma
        contadores = notificaciones_totales.get(registro.pk, {'total_noti': 0, 'total_resp': 0})
        total_noti = contadores['total_noti']
        total_resp = contadores['total_resp']
        
        meses_data = []
        
        for mes in MESES_CAMPOS:
            pk_guardado = getattr(registro, mes)
            codigo = '--'
            color = '#1F2937'
            if pk_guardado and str(pk_guardado) in inspecciones_map:
                codigo = inspecciones_map[str(pk_guardado)]['codigo']
                color = inspecciones_map[str(pk_guardado)]['color']
            
            # Contar notificaciones para este mes y cronograma
            noti_count = 0
            resp_count = 0
            if pk_guardado:  # Solo si hay inspección
                key_total = f"{registro.pk}_{mes}"
                key_contestada = f"{registro.pk}_{mes}_contestada"
                
                noti_count = notificaciones_por_cronograma_mes.get(key_total, 0)
                resp_count = notificaciones_contestadas_por_cronograma_mes.get(key_contestada, 0)

            meses_data.append({
                'nombre': mes,
                'valor_select_pk': pk_guardado,
                'codigo_inspeccion_actual': codigo,
                'color_inicial': color,
                'noti_count': noti_count,
                'resp_count': resp_count,
            })

        if nombre_unidad not in cronograma_por_unidad:
            cronograma_por_unidad[nombre_unidad] = []

        cronograma_por_unidad[nombre_unidad].append({
            'anio': anio_formateado,
            'registro_cronograma_pk': registro.pk,
            'unidad_id': registro.unidad.pk,
            'nota_actual': registro.nota or "",
            'observacion_unidad': observacion_unidad,
            'capitulo_unidad': capitulo_unidad,
            'total_noti': total_noti,  # Total de notificaciones para todo el cronograma
            'total_resp': total_resp,  # Total de respuestas para todo el cronograma
            'meses_con_valores': meses_data
        })

    # Preparar datos para el filtro de unidades
    unidades_para_filtro = []
    for nombre_unidad, cronogramas_list in cronograma_por_unidad.items():
        if cronogramas_list:
            unidades_para_filtro.append({
                'nombre': nombre_unidad,
                'capitulo': cronogramas_list[0]['capitulo_unidad']
            })

    ultima_modificacion = None
    if cronogramas.exists():
        ultimo_registro = cronogramas.order_by('-ahora').first()
        ultima_modificacion = ultimo_registro.ahora if ultimo_registro else None

    contexto = {
        'ccpp': ccpp,
        'meses_titulos': MESES_TITULOS,
        'cronograma_por_unidad': cronograma_por_unidad,
        'unidades_para_filtro': unidades_para_filtro,
        'opciones_inspeccion': opciones_inspeccion_data,
        'anos_disponibles': anos_disponibles,
        'capitulos_disponibles': capitulos_disponibles,
        'ultima_modificacion': ultima_modificacion,
        'anio_filtrado_por_defecto': anio_a_filtrar_por_defecto,
    }

    return render(request, 'gestion/cronograma/cronograma.html', contexto)











from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, date
import calendar

@login_required
def dashboard_cronograma(request):
    """
    Dashboard especializado para visualización de cronogramas
    de las CCPPs asignadas al usuario
    """
    try:
        # Obtener perfil del usuario
        user_profile = UserProfile.objects.get(user=request.user)
        ccpps_asignadas = user_profile.ccpps_asignadas.all()
        
        if not ccpps_asignadas.exists():
            context = {
                'error': 'No tienes CCPPs asignadas. Contacta al administrador.'
            }
            return render(request, 'cronograma/dashboard.html', context)
        
        # Parámetros de filtrado
        ccpp_id = request.GET.get('ccpp')
        mes_seleccionado = request.GET.get('mes', str(datetime.now().month))
        anio_seleccionado = request.GET.get('anio', str(datetime.now().year))
        unidad_filtro = request.GET.get('unidad', '')
        estado_filtro = request.GET.get('estado', '')
        
        try:
            mes_seleccionado = int(mes_seleccionado)
            anio_seleccionado = int(anio_seleccionado)
        except (ValueError, TypeError):
            mes_seleccionado = datetime.now().month
            anio_seleccionado = datetime.now().year
        
        # Obtener CCPP seleccionada o usar la primera
        ccpp_actual = None
        if ccpp_id:
            ccpp_actual = get_object_or_404(tbl_CCPP, id=ccpp_id)
            # Verificar que el usuario tenga acceso
            if ccpp_actual not in ccpps_asignadas:
                ccpp_actual = ccpps_asignadas.first()
        else:
            ccpp_actual = ccpps_asignadas.first()
        
        # Obtener cronogramas filtrados
        cronogramas = tbl_Cronograma.objects.filter(ccpp=ccpp_actual)
        
        # Aplicar filtros adicionales
        if unidad_filtro:
            cronogramas = cronogramas.filter(
                Q(unidad__unidad__icontains=unidad_filtro) |
                Q(unidad__descripcion__icontains=unidad_filtro)
            )
        
        # Ordenar cronogramas
        cronogramas = cronogramas.select_related('unidad').order_by('unidad__orden')
        
        # Procesar datos para el dashboard
        datos_cronograma = []
        for crono in cronogramas:
            # Obtener valor del mes seleccionado
            meses_campos = [
                'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
                'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
            ]
            
            valor_mes = getattr(crono, meses_campos[mes_seleccionado - 1], None)
            
            # Determinar estado
            estado = 'pendiente'
            if valor_mes:
                # Intentar determinar si está completado o programado
                if any(keyword in str(valor_mes).lower() for keyword in ['completado', 'realizado', 'terminado', 'ok']):
                    estado = 'completado'
                elif any(keyword in str(valor_mes).lower() for keyword in ['programado', 'planificado', 'agendado']):
                    estado = 'programado'
                else:
                    estado = 'registrado'
            
            # Aplicar filtro por estado si existe
            if estado_filtro and estado != estado_filtro:
                continue
            
            # Calcular días restantes si está programado
            dias_restantes = None
            if estado == 'programado' and ccpp_actual.fecha_entrega:
                # Lógica simple para cálculo de días
                hoy = datetime.now().date()
                dias_restantes = (date(anio_seleccionado, mes_seleccionado, 15) - hoy).days
            
            datos_cronograma.append({
                'cronograma': crono,
                'unidad': crono.unidad,
                'valor_mes': valor_mes,
                'estado': estado,
                'dias_restantes': dias_restantes,
                'clase_estado': f'estado-{estado}',
            })
        
        # Estadísticas
        total_unidades = cronogramas.count()
        completadas = sum(1 for item in datos_cronograma if item['estado'] == 'completado')
        programadas = sum(1 for item in datos_cronograma if item['estado'] == 'programado')
        pendientes = total_unidades - completadas - programadas
        
        # Generar datos para gráficos
        meses_nombres = list(calendar.month_name)[1:]  # Excluir el primer elemento vacío
        meses_grafico = meses_nombres
        datos_grafico = []
        
        for i, mes_nombre in enumerate(meses_nombres):
            mes_num = i + 1
            actividades_mes = 0
            for crono in cronogramas:
                valor = getattr(crono, meses_campos[i], None)
                if valor:
                    actividades_mes += 1
            datos_grafico.append(actividades_mes)
        
        # Calcular próximas actividades (próximos 30 días)
        proximas_actividades = []
        hoy = datetime.now().date()
        
        for crono in cronogramas:
            for i, mes_campo in enumerate(meses_campos):
                mes_num = i + 1
                valor = getattr(crono, mes_campo, None)
                
                if valor and 'programado' in str(valor).lower():
                    # Suponemos que la actividad es para el día 15 del mes
                    fecha_actividad = date(anio_seleccionado, mes_num, 15)
                    dias_hasta = (fecha_actividad - hoy).days
                    
                    if 0 <= dias_hasta <= 30:  # Próximos 30 días
                        proximas_actividades.append({
                            'unidad': crono.unidad,
                            'mes': meses_nombres[i],
                            'valor': valor,
                            'dias_hasta': dias_hasta,
                            'fecha': fecha_actividad,
                        })
        
        # Ordenar por fecha más próxima
        proximas_actividades.sort(key=lambda x: x['dias_hasta'])
        
        # Obtener todas las unidades para filtros
        todas_unidades = tbl_Unidad.objects.filter(
            id__in=cronogramas.values_list('unidad_id', flat=True)
        ).order_by('orden')
        
        # Preparar contexto
        context = {
            'ccpp_actual': ccpp_actual,
            'ccpps_asignadas': ccpps_asignadas,
            'datos_cronograma': datos_cronograma,
            'total_unidades': total_unidades,
            'completadas': completadas,
            'programadas': programadas,
            'pendientes': pendientes,
            'porcentaje_completado': round((completadas / total_unidades * 100) if total_unidades > 0 else 0, 1),
            
            'mes_seleccionado': mes_seleccionado,
            'anio_seleccionado': anio_seleccionado,
            'meses_nombres': meses_nombres,
            'mes_actual_nombre': meses_nombres[mes_seleccionado - 1],
            'mes_actual_num': datetime.now().month,
            
            'unidad_filtro': unidad_filtro,
            'estado_filtro': estado_filtro,
            'todas_unidades': todas_unidades,
            
            'datos_grafico': datos_grafico,
            'meses_grafico': meses_grafico,
            
            'proximas_actividades': proximas_actividades[:5],  # Solo las 5 más próximas
            
            'anios_disponibles': range(anio_seleccionado - 2, anio_seleccionado + 3),
            'hoy': datetime.now().strftime("%d/%m/%Y"),
        }
        
        return render(request, 'cronograma/dashboard.html', context)
        
    except UserProfile.DoesNotExist:
        context = {'error': 'Perfil de usuario no configurado.'}
        return render(request, 'cronograma/dashboard.html', context)
    except Exception as e:
        context = {'error': f'Error al cargar el dashboard: {str(e)}'}
        return render(request, 'cronograma/dashboard.html', context)
