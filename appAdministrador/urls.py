from django.urls import path
from appAdministrador.views.dataMaestra import ordenar_capitulos, unidad, CCPP, correo, inspeccion, confi_correo
from appAdministrador.views.gestion import cronograma, ficha, notificacion, reporte
from appAdministrador.views.autenticacion import autenticacion, usuarios
from appAdministrador.views.reporte import reporte_noti, reporte_insp,reporte_fichas


from . import views

urlpatterns = [

    # CRONOGRAMA
    path('', cronograma.vista_panel_principal , name='panel_principal'),
    path('gestion_ccpp/<int:ccpp_id>/', cronograma.vista_actualizar_cronograma , name='gestion_ccpp'),



    # CCPP
    path('ccpp/', CCPP.vista_panel_ccpp , name='ccpp'),
    path('ccpp/nueva/', CCPP.gestionar_ccpp, name='nueva_ccpp'),
    path('ccpp/editar/<int:ccpp_id>/', CCPP.gestionar_ccpp, name='editar_ccpp'),
    path('ccpp/eliminar/<int:ccpp_id>/', CCPP.eliminar_ccpp , name='eliminar_ccpp'),
    path('ccpp/unidades/<int:ccpp_id>/', CCPP.gestionUnidades_ccpp , name='gestionUnidades_ccpp'),
    path('ccpp/clonar/<int:ccpp_id>/', CCPP.clonar_ccpp, name='clonar_ccpp'),


    # UNIDADES
    path('unidades/', unidad.vista_unidad , name='unidad'),
    path('unidades/nueva', unidad.gestionar_unidad , name='nueva_unidad'),
    path('unidades/eliminar/<int:unidad_id>/', unidad.eliminar_unidad, name='eliminar_unidad'),    
    path('unidades/editar/<int:unidad_id>/', unidad.gestionar_unidad , name='editar_unidad'),


    # CONFIGURACION CORREO
    path('correo/plantilla/', correo.correo , name='correo'),


    # ORDENAR CAPITULOS
    path('ordenar_capitulos/', ordenar_capitulos.ordenar_capitulos, name='ordenar_capitulos'),


    # INSPECCIONES
    path('inspecciones/', inspeccion.vista_inspecciones , name='inspecciones'),
    path('inspecciones/editar/<int:inspeccion_id>/', inspeccion.editar_inspeccion , name='editar_inspeccion'),



    #path('fichas/panel', ficha.lista_fichas, name='lista_fichas'),
    #path('ficha/nueva/', ficha.gestionar_ficha, name='nueva_ficha'),
    #path('ficha/editar/<int:ficha_id>/', ficha.gestionar_ficha, name='editar_ficha'),
    #



    # NOTIFICACION
    #path('ccpp/<int:ccpp_id>/inspecciones/', notificacion.vista_panel_notificacion, name='vista_panel_notificacion'),
    #path('ccpp/<int:ccpp_id>/inspecciones/<int:cronograma_id>/<int:inspeccion_id>/<str:mes>/', notificacion.gestionar_notificacion, name='gestionar_notificacion'),
    #path('documento/eliminar/<int:documento_id>/', notificacion.eliminar_documento, name='eliminar_documento'),




    



     
     # FICHAS
    # path('fichas/unidad/<int:unidad_id>/', ficha.vista_panel_ficha, name='vista_panel_fichas_unidad'),


    # path('fichas/unidad/<int:unidad_id>/ccpp/<int:ccpp_id>/', ficha.vista_panel_ficha, name='vista_panel_fichas'),
     #path('ficha/nueva/<int:unidad_id>/ccpp/<int:ccpp_id>/', ficha.gestionar_ficha, name='nueva_ficha'),
     #path('ficha/editar/<int:ficha_id>/ccpp/<int:ccpp_id>/', ficha.gestionar_ficha, name='editar_ficha'),
     #path('ficha/eliminar/<int:ficha_id>/<int:ccpp_id>/', ficha.eliminar_ficha, name='eliminar_ficha'),



     # Panel de Fichas
     path('fichas/unidad/<int:unidad_id>/ccpp/<int:ccpp_id>/', ficha.vista_panel_ficha, name='vista_panel_fichas'),
     path('fichas/unidad/<int:unidad_id>/', ficha.vista_panel_ficha_sin_ccpp, name='vista_panel_fichas_simple'),

     # Nueva Ficha
     path('ficha/nueva/<int:unidad_id>/ccpp/<int:ccpp_id>/', ficha.gestionar_ficha, name='nueva_ficha'),
     path('ficha/nueva/<int:unidad_id>/', ficha.gestionar_ficha_sin_ccpp, name='nueva_ficha_simple'),

     # Editar Ficha
     path('ficha/editar/<int:ficha_id>/ccpp/<int:ccpp_id>/', ficha.gestionar_ficha, name='editar_ficha'),
     path('ficha/editar/<int:ficha_id>/', ficha.gestionar_ficha_sin_ccpp, name='editar_ficha_simple'),

     # Eliminar Ficha
     path('ficha/eliminar/<int:ficha_id>/<int:ccpp_id>/', ficha.eliminar_ficha, name='eliminar_ficha'),
     path('ficha/eliminar/<int:ficha_id>/', ficha.eliminar_ficha_sin_ccpp, name='eliminar_ficha_simple'),



    # AUTENTICACION
    path('autenticacion/', autenticacion.inicio_sesion , name='login'),
    path('cerrar_sesion/',autenticacion.cerrar_sesion, name='cerrar_sesion'),




    # NOTIFICACION

     path('notificaciones/ccpp/<int:ccpp_id>/', notificacion.vista_panel_notificacion, name='vista_panel_notificacion'),
     path('gestion-notificacion/<int:cronograma_id>/<str:mes_nombre>/', notificacion.gestion_notificacion, name='gestionar_notificacion'),
     path('guardar-notificacion/<int:cronograma_id>/<str:mes_nombre>/', notificacion.guardar_notificacion, name='guardar_notificacion'),
     path('eliminar-documento/<int:documento_id>/', notificacion.eliminar_documento, name='eliminar_documento'),

#    path('ccpp/<int:ccpp_id>/unidad/<int:unidad_id>/inspeccion/<int:inspeccion_id>/enviar-correo/<int:notificacion_id>/', notificacion.preparar_y_enviar_correo, name='enviar_correo'),
    path('correo-enviado/', notificacion.correo_enviado, name='correo_enviado'),

    path('enviar-correo/<int:ccpp_id>/<int:unidad_id>/<int:inspeccion_id>/', 
         notificacion.preparar_y_enviar_correo, name='enviar_correo'),
    



         # Gestión de usuarios
    path('usuarios/', usuarios.vista_panel_usuarios, name='panel_usuarios'),
    path('usuarios/crear/', usuarios.crear_usuario, name='crear_usuario'),
    path('usuarios/editar/<int:usuario_id>/', usuarios.editar_usuario, name='editar_usuario'),
    path('usuarios/eliminar/<int:usuario_id>/', usuarios.eliminar_usuario, name='eliminar_usuario'),


     #REPORTE
     path('reportes/ccpp/<int:ccpp_id>', reporte.vista_reporte_ccpp, name='vista_reporte_ccpp'),

     #EXPORTAR
     path('ficha/pdf/<int:ficha_id>/<int:ccpp_id>', reporte.exportar_ficha_pdf, name='exportar_ficha_pdf'),






    path('configuracion/email/actualizar/', confi_correo.actualizar_configuracion_email, name='actualizar_configuracion_email'),


    path('dashboard-cronograma/', cronograma.dashboard_cronograma, name='dashboard_cronograma'),






    #REPORTE
    path('reporte/notificaciones/<int:ccpp_id>/<int:anio>/<int:mes_inicio>/<int:mes_fin>/<str:mostrar_remitentes>/<str:mostrar_respuesta>/', 
         reporte_noti.reporte_notificaciones_ccpp_pdf, 
         name='reporte_notificaciones_ccpp'),

     path('reporte/inspecciones/<int:ccpp_id>/<int:anio>/', reporte_insp.reporte_inspecciones_ccpp_pdf, name='reporte_inspecciones_pdf'),


     path('exportar-pdf/<int:ccpp_id>/', reporte_fichas.reporte_ccpp_final, name='exportar_pdf_consolidado'),





]