from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.conf import settings


def inicio_sesion(request):
    """
    Vista para manejar el inicio de sesión de usuarios.
    
    Configura una sesión con tiempo de expiración prolongado si el usuario
    selecciona "Recordarme". Valida credenciales y redirige al panel principal.
    """
    
    # Si el usuario ya está autenticado, redirigir al panel
    if request.user.is_authenticated:
        messages.info(request, "Ya tienes una sesión activa.")
        return redirect('panel_principal')

    if request.method == 'POST':
        nombre_usuario = request.POST.get('usuario', '').strip()
        clave = request.POST.get('clave', '').strip()
        recordarme = request.POST.get('recordarme') == 'on'

        # Validar que ambos campos estén completos
        if not nombre_usuario or not clave:
            messages.error(request, "Debes completar ambos campos.")
            return render(
                request,
                'autenticacion/inicio_sesion.html',
                {'usuario_val': nombre_usuario}
            )

        # Verificar existencia del usuario
        try:
            usuario = User.objects.get(username=nombre_usuario)
        except User.DoesNotExist:
            messages.error(
                request,
                "No existe una cuenta con ese nombre de usuario."
            )
            return render(
                request,
                'autenticacion/inicio_sesion.html',
                {'usuario_val': nombre_usuario}
            )

        # Autenticar usuario
        usuario_autenticado = authenticate(
            request,
            username=nombre_usuario,
            password=clave
        )

        if usuario_autenticado is not None:
            # Configurar tiempo de sesión según preferencia del usuario
            if recordarme:
                # Sesión prolongada (2 semanas de inactividad)
                request.session.set_expiry(1209600)  # 14 días en segundos
            else:
                # Sesión normal (cierre al cerrar navegador)
                request.session.set_expiry(0)
            
            login(request, usuario_autenticado)
            messages.success(
                request,
                f"Bienvenido, {usuario_autenticado.username}."
            )
            return redirect('panel_principal')
        else:
            messages.error(request, "Contraseña incorrecta.")
            return render(
                request,
                'autenticacion/inicio_sesion.html',
                {'usuario_val': nombre_usuario}
            )

    return render(request, 'autenticacion/inicio_sesion.html')


def cerrar_sesion(request):
    """
    Vista para cerrar la sesión del usuario actual.
    
    Realiza logout y muestra mensaje apropiado según el estado de autenticación.
    """
    
    if request.user.is_authenticated:
        nombre_usuario = request.user.username
        logout(request)
        messages.success(
            request,
            f"Hasta pronto, {nombre_usuario}. Has cerrado sesión correctamente."
        )
    else:
        messages.info(request, "No has iniciado sesión.")

    return redirect('login')


