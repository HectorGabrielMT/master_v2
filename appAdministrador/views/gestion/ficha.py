import logging
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction, DatabaseError
from django.db.models import Count
from django.shortcuts import render, get_object_or_404, redirect
from appAdministrador.models import tbl_Unidad, tbl_Ficha, tbl_FichaControl, tbl_inspeccion, tbl_CCPP


logger = logging.getLogger(__name__)


@login_required
def vista_panel_ficha(request, unidad_id, ccpp_id=None):
    ccpp=None
    print(unidad_id)
    try:
        unidad = get_object_or_404(tbl_Unidad, id=unidad_id)
        if ccpp_id:
            ccpp = get_object_or_404(tbl_CCPP, id=ccpp_id)
        
    except Exception as e:
        logger.error(f"Error al obtener unidad {unidad_id} o CCPP {ccpp_id}: {e}")
        messages.error(request, "No se pudo cargar la unidad o CCPP solicitada.")
        return redirect("panel_principal")

    try:
        fichas = (
            tbl_Ficha.objects.filter(FK_FichaUnidad=unidad)
            .annotate(num_controles=Count("tbl_fichacontrol"))
            .order_by("-fecha_creacion")
        )
    except DatabaseError as db_err:
        logger.error(f"Error de base de datos al cargar fichas de unidad {unidad_id}: {db_err}")
        fichas = []
        messages.error(request, "Error de base de datos al cargar las fichas.")
    except Exception as e:
        logger.error(f"Error inesperado al cargar fichas de unidad {unidad_id}: {e}")
        fichas = []
        messages.error(request, "Ocurrió un error al cargar las fichas.")

    context = {
        "fichas": fichas,
        "unidad": unidad,
        "ccpp": ccpp,
    }

    try:
        return render(request, "gestion/fichas/panel_fichas.html", context)
    except Exception as e:
        logger.error(f"Error al renderizar panel de fichas para unidad {unidad_id}: {e}")
        messages.error(request, "No se pudo generar el panel de fichas.")
        return redirect("panel_principal")


@login_required
def gestionar_ficha(request, unidad_id=None, ficha_id=None, ccpp_id=None):
    ficha = None
    edicion = False
    unidad = None
    errores = {}
    ccpp = None

    try:
        if ccpp_id:
            ccpp = get_object_or_404(tbl_CCPP, pk=ccpp_id)
        
        if ficha_id:
            ficha = get_object_or_404(tbl_Ficha, id=ficha_id)
            unidad = ficha.FK_FichaUnidad
            edicion = True
        elif unidad_id:
            unidad = get_object_or_404(tbl_Unidad, id=unidad_id)
        else:
            messages.error(request, "Referencia de unidad o ficha no encontrada.")
            return redirect("panel_principal")
    except Exception as e:
        logger.error(f"Error al obtener unidad/ficha/ccpp: {e}")
        messages.error(request, "Error al cargar la ficha, unidad o CCPP.")
        return redirect("panel_principal")

    try:
        inspecciones = tbl_inspeccion.objects.all().order_by("codigo_inspeccion")
    except Exception as e:
        logger.error(f"Error al cargar inspecciones: {e}")
        inspecciones = []

    if request.method == "POST":
        titulo = request.POST.get("titulo", "").strip()
        precaucion = request.POST.get("precaucion", "").strip()
        prescripcion = request.POST.get("prescripcion", "").strip()
        prohibicion = request.POST.get("prohibicion", "").strip()
        eliminar_logo = request.POST.get("eliminar_logo") == "true"
        eliminar_foto = request.POST.get("eliminar_foto") == "true"

        if not titulo:
            errores["titulo"] = "El título es requerido."

        try:
            qs_duplicados = tbl_Ficha.objects.filter(PK_titulo=titulo)
            if edicion:
                qs_duplicados = qs_duplicados.exclude(id=ficha.id)
            if qs_duplicados.exists():
                errores["titulo"] = "Ya existe una ficha con ese título."
        except Exception as e:
            logger.error(f"Error al validar duplicados: {e}")
            errores["titulo"] = "Error al validar título."

        controles_data = []
        indices_controles = []
        for key in request.POST.keys():
            if key.startswith('controles-') and '-periodo' in key:
                idx = key.split('-')[1]
                indices_controles.append(idx)

        for idx in sorted(set(indices_controles)):
            periodo = request.POST.get(f'controles-{idx}-periodo', '').strip()
            premisa = request.POST.get(f'controles-{idx}-premisa', '').strip()
            inspeccion_id = request.POST.get(f'controles-{idx}-inspeccion', '')
            control_texto = request.POST.get(f'controles-{idx}-control', '').strip()

            if periodo or premisa or control_texto:
                inspeccion_obj = None
                if inspeccion_id:
                    try:
                        inspeccion_obj = tbl_inspeccion.objects.get(id=inspeccion_id)
                    except tbl_inspeccion.DoesNotExist:
                        errores[f"controles_{idx}_inspeccion"] = "Inspección no válida"
                        continue
                    except Exception as e:
                        logger.error(f"Error al obtener inspección: {e}")
                        errores[f"controles_{idx}_inspeccion"] = "Error al validar inspección"
                        continue

                ejecutado = request.POST.get(f'controles-{idx}-ejecutado') == 'on'
                opacar = request.POST.get(f'controles-{idx}-opacar') == 'on'
                ocultar = request.POST.get(f'controles-{idx}-ocultar') == 'on'

                controles_data.append({
                    'indice': idx,
                    'periodo': periodo,
                    'premisa': premisa,
                    'inspeccion': inspeccion_obj,
                    'control': control_texto,
                    'ejecutado': ejecutado,
                    'opacar': opacar,
                    'ocultar': ocultar,
                    'id_control': request.POST.get(f'controles-{idx}-id', ''),
                })

        if errores:
            return render(
                request,
                "gestion/fichas/formulario_ficha.html",
                {
                    "unidad": unidad,
                    "ficha": ficha,
                    "edicion": edicion,
                    "ccpp": ccpp,
                    "errores": errores,
                    "titulo_value": titulo,
                    "precaucion_value": precaucion,
                    "prescripcion_value": prescripcion,
                    "prohibicion_value": prohibicion,
                    "inspecciones": inspecciones,
                    "controles_data": controles_data,
                },
            )

        try:
            with transaction.atomic():
                if edicion:
                    ficha.PK_titulo = titulo
                    ficha.precaucion = precaucion
                    ficha.prescripcion = prescripcion
                    ficha.prohibicion = prohibicion

                    if eliminar_logo and ficha.logo:
                        try:
                            ficha.logo.delete(save=False)
                        except Exception as e:
                            logger.warning(f"Error al eliminar logo: {e}")
                        ficha.logo = None

                    if eliminar_foto and ficha.foto:
                        try:
                            ficha.foto.delete(save=False)
                        except Exception as e:
                            logger.warning(f"Error al eliminar foto: {e}")
                        ficha.foto = None

                    if "logo" in request.FILES:
                        if ficha.logo:
                            try:
                                ficha.logo.delete(save=False)
                            except Exception as e:
                                logger.warning(f"Error al reemplazar logo: {e}")
                        ficha.logo = request.FILES["logo"]

                    if "foto" in request.FILES:
                        if ficha.foto:
                            try:
                                ficha.foto.delete(save=False)
                            except Exception as e:
                                logger.warning(f"Error al reemplazar foto: {e}")
                        ficha.foto = request.FILES["foto"]

                    ficha.save()

                    ids_controles_existentes = set(
                        tbl_FichaControl.objects.filter(FK_FichaControl=ficha)
                        .values_list('id', flat=True)
                    )
                    ids_controles_presentes = set()

                    for control_data in controles_data:
                        id_control = control_data['id_control']
                        if id_control:
                            try:
                                control = tbl_FichaControl.objects.get(
                                    id=id_control,
                                    FK_FichaControl=ficha
                                )
                                ids_controles_presentes.add(int(id_control))
                            except tbl_FichaControl.DoesNotExist:
                                continue
                            except Exception as e:
                                logger.error(f"Error al actualizar control: {e}")
                                continue
                        else:
                            control = tbl_FichaControl(FK_FichaControl=ficha)

                        control.periodo = control_data['periodo']
                        control.premisa = control_data['premisa']
                        control.FK_FichaControlInspeccion = control_data['inspeccion']
                        control.control = control_data['control']
                        control.ejecutado = control_data['ejecutado']
                        control.opacar = control_data['opacar']
                        control.ocultar = control_data['ocultar']
                        control.save()

                    ids_a_eliminar = ids_controles_existentes - ids_controles_presentes
                    if ids_a_eliminar:
                        tbl_FichaControl.objects.filter(
                            id__in=ids_a_eliminar,
                            FK_FichaControl=ficha
                        ).delete()

                    messages.success(request, "Ficha actualizada correctamente.")
                else:
                    ficha = tbl_Ficha.objects.create(
                        FK_FichaUnidad=unidad,
                        PK_titulo=titulo,
                        precaucion=precaucion,
                        prescripcion=prescripcion,
                        prohibicion=prohibicion,
                        logo=request.FILES.get("logo"),
                        foto=request.FILES.get("foto"),
                    )

                    for control_data in controles_data:
                        tbl_FichaControl.objects.create(
                            FK_FichaControl=ficha,
                            FK_FichaControlInspeccion=control_data['inspeccion'],
                            periodo=control_data['periodo'],
                            premisa=control_data['premisa'],
                            control=control_data['control'],
                            ejecutado=control_data['ejecutado'],
                            opacar=control_data['opacar'],
                            ocultar=control_data['ocultar']
                        )

                    messages.success(request, "Ficha creada exitosamente.")

                return redirect("editar_ficha", ficha_id=ficha.id, ccpp_id=ccpp_id)

        except DatabaseError as db_err:
            logger.error(f"Error de base de datos: {db_err}")
            messages.error(request, "Error de base de datos al guardar la ficha.")
        except Exception as error:
            logger.error(f"Error inesperado: {error}")
            messages.error(request, f"Ocurrió un error inesperado: {error}")

    try:
        controles = []
        if ficha:
            controles = tbl_FichaControl.objects.filter(FK_FichaControl=ficha)
    except Exception as e:
        logger.error(f"Error al cargar controles: {e}")
        controles = []

    return render(
        request,
        "gestion/fichas/formulario_ficha.html",
        {
            "unidad": unidad,
            "ficha": ficha,
            "edicion": edicion,
            "ccpp": ccpp,
            "controles": controles,
            "inspecciones": inspecciones,
        },
    )


@login_required
def eliminar_ficha(request, ficha_id, ccpp_id):
    try:
        ficha = get_object_or_404(tbl_Ficha, id=ficha_id)
        ccpp = get_object_or_404(tbl_CCPP, pk=ccpp_id)
        id_unidad = ficha.FK_FichaUnidad.id
    except Exception as e:
        logger.error(f"Error al obtener ficha {ficha_id}: {e}")
        messages.error(request, "No se pudo cargar la ficha solicitada.")
        return redirect("panel_principal")

    if request.method == "POST":
        try:
            with transaction.atomic():
                nombre_ficha = ficha.PK_titulo
                ficha.delete()
                messages.success(
                    request,
                    f"La ficha '{nombre_ficha}' y sus controles han sido eliminados correctamente."
                )
                if ccpp_id:
                    return redirect("vista_panel_fichas", unidad_id=id_unidad, ccpp_id=ccpp_id)
                return redirect("vista_panel_fichas_unidad", unidad_id=id_unidad)
        except DatabaseError as db_err:
            logger.error(f"Error de base de datos al eliminar ficha {ficha_id}: {db_err}")
            messages.error(request, "Error de base de datos al eliminar la ficha.")
            return redirect("vista_panel_fichas", unidad_id=id_unidad, ccpp_id=ccpp_id)
        except Exception as error:
            logger.error(f"Error inesperado al eliminar ficha {ficha_id}: {error}")
            messages.error(request, f"Ocurrió un error al eliminar la ficha: {error}")
            return redirect("vista_panel_fichas", unidad_id=id_unidad, ccpp_id=ccpp_id)

    return redirect("vista_panel_fichas", unidad_id=id_unidad, ccpp_id=ccpp_id)
















@login_required
def vista_panel_ficha_sin_ccpp(request, unidad_id):
    ccpp=None
    print(unidad_id)
    try:
        unidad = get_object_or_404(tbl_Unidad, id=unidad_id)
        
    except Exception as e:
        logger.error(f"Error al obtener unidad {unidad_id}")
        messages.error(request, "No se pudo cargar la unidad o CCPP solicitada.")
        return redirect("panel_principal")

    try:
        fichas = (
            tbl_Ficha.objects.filter(FK_FichaUnidad=unidad)
            .annotate(num_controles=Count("tbl_fichacontrol"))
            .order_by("-fecha_creacion")
        )
    except DatabaseError as db_err:
        logger.error(f"Error de base de datos al cargar fichas de unidad {unidad_id}: {db_err}")
        fichas = []
        messages.error(request, "Error de base de datos al cargar las fichas.")
    except Exception as e:
        logger.error(f"Error inesperado al cargar fichas de unidad {unidad_id}: {e}")
        fichas = []
        messages.error(request, "Ocurrió un error al cargar las fichas.")

    context = {
        "fichas": fichas,
        "unidad": unidad,
        "ccpp": ccpp,
    }

    try:
        return render(request, "gestion/fichas/panel_fichas.html", context)
    except Exception as e:
        logger.error(f"Error al renderizar panel de fichas para unidad {unidad_id}: {e}")
        messages.error(request, "No se pudo generar el panel de fichas.")
        return redirect("panel_principal")


@login_required
def gestionar_ficha_sin_ccpp(request, unidad_id=None, ficha_id=None):
    ficha = None
    edicion = False
    unidad = None
    errores = {}
    ccpp = None

    try:
        
        if ficha_id:
            ficha = get_object_or_404(tbl_Ficha, id=ficha_id)
            unidad = ficha.FK_FichaUnidad
            edicion = True
        elif unidad_id:
            unidad = get_object_or_404(tbl_Unidad, id=unidad_id)
        else:
            messages.error(request, "Referencia de unidad o ficha no encontrada.")
            return redirect("panel_principal")
    except Exception as e:
        logger.error(f"Error al obtener unidad/ficha/ccpp: {e}")
        messages.error(request, "Error al cargar la ficha, unidad o CCPP.")
        return redirect("panel_principal")

    try:
        inspecciones = tbl_inspeccion.objects.all().order_by("codigo_inspeccion")
    except Exception as e:
        logger.error(f"Error al cargar inspecciones: {e}")
        inspecciones = []

    if request.method == "POST":
        titulo = request.POST.get("titulo", "").strip()
        precaucion = request.POST.get("precaucion", "").strip()
        prescripcion = request.POST.get("prescripcion", "").strip()
        prohibicion = request.POST.get("prohibicion", "").strip()
        eliminar_logo = request.POST.get("eliminar_logo") == "true"
        eliminar_foto = request.POST.get("eliminar_foto") == "true"

        if not titulo:
            errores["titulo"] = "El título es requerido."

        try:
            qs_duplicados = tbl_Ficha.objects.filter(PK_titulo=titulo)
            if edicion:
                qs_duplicados = qs_duplicados.exclude(id=ficha.id)
            if qs_duplicados.exists():
                errores["titulo"] = "Ya existe una ficha con ese título."
        except Exception as e:
            logger.error(f"Error al validar duplicados: {e}")
            errores["titulo"] = "Error al validar título."

        controles_data = []
        indices_controles = []
        for key in request.POST.keys():
            if key.startswith('controles-') and '-periodo' in key:
                idx = key.split('-')[1]
                indices_controles.append(idx)

        for idx in sorted(set(indices_controles)):
            periodo = request.POST.get(f'controles-{idx}-periodo', '').strip()
            premisa = request.POST.get(f'controles-{idx}-premisa', '').strip()
            inspeccion_id = request.POST.get(f'controles-{idx}-inspeccion', '')
            control_texto = request.POST.get(f'controles-{idx}-control', '').strip()

            if periodo or premisa or control_texto:
                inspeccion_obj = None
                if inspeccion_id:
                    try:
                        inspeccion_obj = tbl_inspeccion.objects.get(id=inspeccion_id)
                    except tbl_inspeccion.DoesNotExist:
                        errores[f"controles_{idx}_inspeccion"] = "Inspección no válida"
                        continue
                    except Exception as e:
                        logger.error(f"Error al obtener inspección: {e}")
                        errores[f"controles_{idx}_inspeccion"] = "Error al validar inspección"
                        continue

                ejecutado = request.POST.get(f'controles-{idx}-ejecutado') == 'on'
                opacar = request.POST.get(f'controles-{idx}-opacar') == 'on'
                ocultar = request.POST.get(f'controles-{idx}-ocultar') == 'on'

                controles_data.append({
                    'indice': idx,
                    'periodo': periodo,
                    'premisa': premisa,
                    'inspeccion': inspeccion_obj,
                    'control': control_texto,
                    'ejecutado': ejecutado,
                    'opacar': opacar,
                    'ocultar': ocultar,
                    'id_control': request.POST.get(f'controles-{idx}-id', ''),
                })

        if errores:
            return render(
                request,
                "gestion/fichas/formulario_ficha.html",
                {
                    "unidad": unidad,
                    "ficha": ficha,
                    "edicion": edicion,
                    "ccpp": ccpp,
                    "errores": errores,
                    "titulo_value": titulo,
                    "precaucion_value": precaucion,
                    "prescripcion_value": prescripcion,
                    "prohibicion_value": prohibicion,
                    "inspecciones": inspecciones,
                    "controles_data": controles_data,
                },
            )

        try:
            with transaction.atomic():
                if edicion:
                    ficha.PK_titulo = titulo
                    ficha.precaucion = precaucion
                    ficha.prescripcion = prescripcion
                    ficha.prohibicion = prohibicion

                    if eliminar_logo and ficha.logo:
                        try:
                            ficha.logo.delete(save=False)
                        except Exception as e:
                            logger.warning(f"Error al eliminar logo: {e}")
                        ficha.logo = None

                    if eliminar_foto and ficha.foto:
                        try:
                            ficha.foto.delete(save=False)
                        except Exception as e:
                            logger.warning(f"Error al eliminar foto: {e}")
                        ficha.foto = None

                    if "logo" in request.FILES:
                        if ficha.logo:
                            try:
                                ficha.logo.delete(save=False)
                            except Exception as e:
                                logger.warning(f"Error al reemplazar logo: {e}")
                        ficha.logo = request.FILES["logo"]

                    if "foto" in request.FILES:
                        if ficha.foto:
                            try:
                                ficha.foto.delete(save=False)
                            except Exception as e:
                                logger.warning(f"Error al reemplazar foto: {e}")
                        ficha.foto = request.FILES["foto"]

                    ficha.save()

                    ids_controles_existentes = set(
                        tbl_FichaControl.objects.filter(FK_FichaControl=ficha)
                        .values_list('id', flat=True)
                    )
                    ids_controles_presentes = set()

                    for control_data in controles_data:
                        id_control = control_data['id_control']
                        if id_control:
                            try:
                                control = tbl_FichaControl.objects.get(
                                    id=id_control,
                                    FK_FichaControl=ficha
                                )
                                ids_controles_presentes.add(int(id_control))
                            except tbl_FichaControl.DoesNotExist:
                                continue
                            except Exception as e:
                                logger.error(f"Error al actualizar control: {e}")
                                continue
                        else:
                            control = tbl_FichaControl(FK_FichaControl=ficha)

                        control.periodo = control_data['periodo']
                        control.premisa = control_data['premisa']
                        control.FK_FichaControlInspeccion = control_data['inspeccion']
                        control.control = control_data['control']
                        control.ejecutado = control_data['ejecutado']
                        control.opacar = control_data['opacar']
                        control.ocultar = control_data['ocultar']
                        control.save()

                    ids_a_eliminar = ids_controles_existentes - ids_controles_presentes
                    if ids_a_eliminar:
                        tbl_FichaControl.objects.filter(
                            id__in=ids_a_eliminar,
                            FK_FichaControl=ficha
                        ).delete()

                    messages.success(request, "Ficha actualizada correctamente.")
                else:
                    ficha = tbl_Ficha.objects.create(
                        FK_FichaUnidad=unidad,
                        PK_titulo=titulo,
                        precaucion=precaucion,
                        prescripcion=prescripcion,
                        prohibicion=prohibicion,
                        logo=request.FILES.get("logo"),
                        foto=request.FILES.get("foto"),
                    )

                    for control_data in controles_data:
                        tbl_FichaControl.objects.create(
                            FK_FichaControl=ficha,
                            FK_FichaControlInspeccion=control_data['inspeccion'],
                            periodo=control_data['periodo'],
                            premisa=control_data['premisa'],
                            control=control_data['control'],
                            ejecutado=control_data['ejecutado'],
                            opacar=control_data['opacar'],
                            ocultar=control_data['ocultar']
                        )

                    messages.success(request, "Ficha creada exitosamente.")

                return redirect("editar_ficha_simple", ficha_id=ficha.id)

        except DatabaseError as db_err:
            logger.error(f"Error de base de datos: {db_err}")
            messages.error(request, "Error de base de datos al guardar la ficha.")
        except Exception as error:
            logger.error(f"Error inesperado: {error}")
            messages.error(request, f"Ocurrió un error inesperado: {error}")

    try:
        controles = []
        if ficha:
            controles = tbl_FichaControl.objects.filter(FK_FichaControl=ficha)
    except Exception as e:
        logger.error(f"Error al cargar controles: {e}")
        controles = []

    return render(
        request,
        "gestion/fichas/formulario_ficha.html",
        {
            "unidad": unidad,
            "ficha": ficha,
            "edicion": edicion,
            "ccpp": ccpp,
            "controles": controles,
            "inspecciones": inspecciones,
        },
    )


@login_required
def eliminar_ficha_sin_ccpp(request, ficha_id):
    try:
        ficha = get_object_or_404(tbl_Ficha, id=ficha_id)
        id_unidad = ficha.FK_FichaUnidad.id
    except Exception as e:
        logger.error(f"Error al obtener ficha {ficha_id}: {e}")
        messages.error(request, "No se pudo cargar la ficha solicitada.")
        return redirect("panel_principal")

    if request.method == "POST":
        try:
            with transaction.atomic():
                nombre_ficha = ficha.PK_titulo
                ficha.delete()
                messages.success(
                    request,
                    f"La ficha '{nombre_ficha}' y sus controles han sido eliminados correctamente."
                )
                return redirect("vista_panel_fichas_simple", unidad_id=id_unidad)
        except DatabaseError as db_err:
            logger.error(f"Error de base de datos al eliminar ficha {ficha_id}: {db_err}")
            messages.error(request, "Error de base de datos al eliminar la ficha.")
            return redirect("vista_panel_fichas_simple", unidad_id=id_unidad)
        except Exception as error:
            logger.error(f"Error inesperado al eliminar ficha {ficha_id}: {error}")
            messages.error(request, f"Ocurrió un error al eliminar la ficha: {error}")
            return redirect("vista_panel_fichas_simple", unidad_id=id_unidad)

    return redirect("vista_panel_fichas_simple", unidad_id=id_unidad)


