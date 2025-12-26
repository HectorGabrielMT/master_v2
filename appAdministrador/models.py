from django.db import models
import logging
logger = logging.getLogger(__name__)
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import User











class tbl_inspeccion(models.Model):
    codigo_inspeccion = models.CharField(max_length=100, verbose_name="Código de Inspección", unique=True)
    nombre_inspeccion = models.CharField(max_length=255, verbose_name="Nombre de la Inspección")
    descripcion_inspeccion = models.CharField(max_length=255,verbose_name="Descripción de la Inspección")
    notificacionA_inspeccion = models.CharField(max_length=255, verbose_name="Notificación")
    color_inspeccion = models.CharField(max_length=10, verbose_name="Color de la Inspección", default="#FFFFFF")




class tbl_CCPP(models.Model):
    
    id_ccpp = models.CharField(max_length=150, verbose_name="ID CCPP", unique=True)
    nombre = models.CharField(max_length=150, verbose_name="CCPP Residencial")
    fecha_entrega = models.DateField(null=True, blank=True, verbose_name="Fecha de Entrega")
    cantidad_anios = models.IntegerField(default=0, verbose_name="Cantidad de Años")
    direccion = models.CharField(max_length=255, verbose_name="Dirección de la CCPP")
    habilitada = models.BooleanField(default=True, verbose_name="CCPP Habilitada")

    operario_comunidad = models.TextField(verbose_name="Operario Comunidad", blank=True)
    empresa_especializada = models.TextField(verbose_name="Empresa Especializada", blank=True)
    administracion_edificio = models.TextField(verbose_name="Administración del Edificio", blank=True)
    tecnico_especialista = models.TextField(verbose_name="Técnico Especialista", blank=True)
    tecnico_cabecera = models.TextField(verbose_name="Técnico de Cabecera", blank=True)
    copia_oculta = models.TextField(verbose_name="Copia Oculta (Contactos)", blank=True)

    clon_ccpp = models.CharField(max_length=150, verbose_name="Clon", blank=True)

    imagen = models.ImageField(upload_to='imagenes/', null=True, blank=True, verbose_name="Imagen de la ccpp")


class tbl_Unidad(models.Model):
    
    capitulo = models.CharField(max_length=255, verbose_name="Capitulo")
    unidad = models.CharField(max_length=255, verbose_name="Unidad")
    descripcion = models.CharField(max_length=255, verbose_name="Descripcion")
    observacion = models.CharField(max_length=255, verbose_name="Observacion")
    doc = models.CharField(max_length=255, verbose_name="DOC")
    orden = models.IntegerField(verbose_name="Orden", default=0)


class tbl_CCPP_Unidad (models.Model):
    ccpp = models.ForeignKey(tbl_CCPP, on_delete=models.CASCADE, verbose_name="CCPP")
    unidad = models.ForeignKey(tbl_Unidad, on_delete=models.CASCADE, verbose_name="Unidad")


class tbl_Cronograma(models.Model):
    ccpp = models.ForeignKey(tbl_CCPP, on_delete=models.CASCADE, verbose_name="CCPP")
    unidad = models.ForeignKey(tbl_Unidad, on_delete=models.CASCADE, verbose_name="Unidad")
    anios = models.IntegerField(verbose_name="Años")

    nota = models.TextField(verbose_name="Nota", blank=True, null=True)

    enero = models.CharField(verbose_name="Enero", max_length=10, null=True, blank=True)
    febrero = models.CharField(verbose_name="Febrero", max_length=10, null=True, blank=True)
    marzo = models.CharField(verbose_name="Marzo",max_length=10, null=True, blank=True)
    abril = models.CharField(verbose_name="Abril", max_length=10, null=True, blank=True)
    mayo = models.CharField(verbose_name="Mayo", max_length=10, null=True, blank=True)
    junio = models.CharField(verbose_name="Junio", max_length=10, null=True, blank=True)
    julio = models.CharField(verbose_name="Julio", max_length=10, null=True, blank=True)
    agosto = models.CharField(verbose_name="Agosto", max_length=10, null=True, blank=True)
    septiembre = models.CharField(verbose_name="Septiembre", max_length=10, null=True, blank=True)
    octubre = models.CharField(verbose_name="Octubre", max_length=10, null=True, blank=True)
    noviembre = models.CharField(verbose_name="Noviembre", max_length=10, null=True, blank=True)
    diciembre = models.CharField(verbose_name="Diciembre", max_length=10, null=True, blank=True)

    ahora = models.DateField(auto_now=True, verbose_name="Fecha de Modificación")



class tbl_Ficha(models.Model):
    FK_FichaUnidad = models.ForeignKey(tbl_Unidad, on_delete=models.CASCADE)
    PK_titulo = models.CharField(max_length=255, verbose_name='Título de la Ficha', unique=True)
    precaucion = models.TextField(verbose_name='Precaución')
    prescripcion = models.TextField(verbose_name='Prescripción')
    prohibicion = models.TextField(verbose_name='Prohibición')
    logo = models.ImageField(upload_to='logos_ficha/', null=True, blank=True, verbose_name="Logo")
    foto = models.ImageField(upload_to='imagenes_ficha/', null=True, blank=True, verbose_name="Imagen de anexo")
    fecha_creacion = models.DateField(auto_now_add=True, verbose_name='Fecha de la Ficha')




class tbl_FichaControl(models.Model):
    FK_FichaControl = models.ForeignKey(tbl_Ficha, on_delete=models.CASCADE)
    FK_FichaControlInspeccion = models.ForeignKey(tbl_inspeccion, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Inspección')
    periodo = models.CharField(max_length=255, verbose_name='Período Ficha')
    premisa = models.CharField(max_length=255, verbose_name='Premisa Ficha')
    control = models.TextField(verbose_name='Control Ficha')
    
    ejecutado = models.BooleanField(default=False, verbose_name='Ejecutado')
    opacar = models.BooleanField(default=False, verbose_name='Opacar')
    ocultar = models.BooleanField(default=False, verbose_name='Ocultar')



class tbl_Notificacion(models.Model):

    FK_cronograma = models.ForeignKey(tbl_Cronograma, on_delete=models.CASCADE, verbose_name="Cronograma Relacionado", related_name="notificaciones")
    PK_mes = models.CharField(max_length=20, verbose_name="Mes")
    FK_ficha = models.ForeignKey(tbl_Ficha, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Ficha relacionada")

    fecha = models.DateField(auto_now_add=True, verbose_name="Fecha de Notificación", null=True, blank=True)
    para = models.TextField(verbose_name="Para", blank=True)
    cc = models.TextField(verbose_name="CC", blank=True)
    cco = models.TextField(verbose_name="CCO", blank=True)
    
    FechaResp = models.DateField(verbose_name="Fecha de Respuesta", null=True, blank=True)
    RespRevision = models.TextField(verbose_name="Revisión de Respuesta", blank=True)
    RespControlador = models.TextField(verbose_name="Controlador de Respuesta", null=True, blank=True)
    RespVia = models.TextField(verbose_name="Via de Respuesta",null=True, blank=True)
    RespObservacion = models.TextField(verbose_name="Observación de Respuesta",null=True, blank=True)
    RespInspEjecutada = models.BooleanField(default=False, verbose_name="Inspección Ejecutada")
    NotificacionContestada = models.BooleanField(default=False, verbose_name="Notificación Contestada")


class tbl_NotificacionDocumento(models.Model):
    FK_notificacion = models.ForeignKey(tbl_Notificacion, on_delete=models.CASCADE, related_name='documentos')
    archivo = models.FileField(upload_to='notificaciones/documentos/%Y/%m/%d/')
    nombre_original = models.CharField(max_length=255)
    fecha_subida = models.DateField(auto_now_add=True)
    tamano = models.BigIntegerField()
    
    def delete(self, *args, **kwargs):
        """Eliminar el archivo físico al eliminar el documento"""
        try:
            if self.archivo:
                self.archivo.delete(save=False)
        except Exception as e:
            logger.warning(f"Error al eliminar archivo físico del documento {self.id}: {e}")
        
        super().delete(*args, **kwargs)
    
    class Meta:
        verbose_name = "Documento de Notificación"
        verbose_name_plural = "Documentos de Notificaciones"





class tbl_Correo(models.Model):
    asunto = models.CharField(max_length=255, verbose_name="Asunto")
    cuerpo = models.TextField(verbose_name="Cuerpo del Correo")














class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    ccpp_asignada = models.ForeignKey(
        tbl_CCPP,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="CCPP Asignada"
    )
    
    def __str__(self):
        return f"Perfil de {self.user.username}"
    




class ConfiguracionEmail(models.Model):
    servidor_smtp = models.CharField(max_length=255, default='smtp.gmail.com')
    puerto = models.IntegerField(default=587)
    usar_tls = models.BooleanField(default=True)
    usuario_email = models.EmailField(max_length=255)
    password_aplicacion = models.CharField(max_length=255, help_text="Usa la contraseña de aplicación, no la personal.")

    class Meta:
        verbose_name = "Configuración de Email"
        verbose_name_plural = "Configuraciones de Email"

    def __str__(self):
        return f"Configuración para {self.usuario_email}"