from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.utils import timezone

from .forms import RegistroForm, ReporteForm, UbicacionForm
from .models import Reporte

# Clave con la que guardamos la ubicacion del paso 1 mientras el usuario
# completa el paso 2. Va en la sesion y no en la base, porque un reporte a
# medio llenar todavia no es un reporte.
UBICACION_EN_CURSO = "ubicacion_en_curso"


class EntrarView(LoginView):
    """Iniciar sesion usando la pantalla que diseño Bastian.

    Django trae toda la logica (revisar la clave, crear la sesion, respetar
    el ?next=); lo unico que le cambiamos es que plantilla dibujar.
    """

    template_name = "reportes/login.html"
    redirect_authenticated_user = True


def inicio(request):
    """La portada: el mapa con los reportes y los dos botones."""
    hace_una_semana = timezone.now() - timedelta(days=7)

    # Los reportes que se dibujan como pines en el mapa. Son los de todos, no
    # solo los del usuario: la gracia es ver lo que pasa en el barrio.
    reportes = (
        Reporte.objects
        .select_related("categoria", "ubicacion")
        .order_by("-fecha_creacion")[:100]
    )

    # json_script en la plantilla necesita algo simple, por eso una lista de
    # diccionarios y no los objetos.
    puntos = [
        {
            "lat": r.ubicacion.latitud,
            "lon": r.ubicacion.longitud,
            "categoria": str(r.categoria),
            "comuna": r.ubicacion.comuna,
            "estado": r.estado_actual,
            "etiqueta": r.get_estado_actual_display(),
        }
        for r in reportes
    ]

    contexto = {
        "puntos": puntos,
        "cantidad_reportes": Reporte.objects.filter(
            fecha_creacion__gte=hace_una_semana
        ).count(),
    }

    # El nombre de usuario es el correo; para saludar basta lo que va antes
    # del arroba.
    if request.user.is_authenticated:
        contexto["saludo"] = request.user.username.split("@")[0]

    return render(request, 'reportes/inicio.html', contexto)


def registro(request):
    # Si ya tiene sesion iniciada no tiene sentido mostrarle el registro.
    if request.user.is_authenticated:
        return redirect("inicio")

    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            # Lo dejamos adentro al tiro, para que no tenga que escribir
            # la clave de nuevo justo despues de crearla.
            login(request, usuario)
            messages.success(request, "Tu cuenta quedó creada.")
            return redirect("inicio")
    else:
        form = RegistroForm()

    return render(request, "reportes/registro.html", {"form": form})


@login_required
def ubicacion(request):
    """Paso 1 de 3: donde esta el desperfecto.

    Todavia no escribimos nada en la base. La direccion queda en la sesion y
    recien en el paso 2, cuando el reporte esta completo, se guardan los dos
    juntos. Asi no quedan ubicaciones huerfanas de gente que se arrepintio.
    """
    if request.method == "POST":
        form = UbicacionForm(request.POST)
        if form.is_valid():
            # cleaned_data son valores de Python (floats), que es lo que
            # la sesion sabe convertir a JSON sin reclamar.
            request.session[UBICACION_EN_CURSO] = {
                "direccion_texto": form.cleaned_data["direccion_texto"],
                "comuna": form.cleaned_data["comuna"],
                "latitud": form.cleaned_data["latitud"],
                "longitud": form.cleaned_data["longitud"],
            }
            return redirect("reportar")
    else:
        form = UbicacionForm()

    return render(request, "reportes/ubicacion.html", {"form": form})


@login_required
def reportar(request):
    """Paso 2 de 3: que es el desperfecto, y la foto."""
    # Sin el paso 1 no hay donde poner el reporte, asi que lo devolvemos.
    datos_ubicacion = request.session.get(UBICACION_EN_CURSO)
    if not datos_ubicacion:
        messages.info(request, "Primero marca dónde está el desperfecto.")
        return redirect("ubicacion")

    if request.method == "POST":
        # request.POST trae los campos de texto, request.FILES trae la foto.
        form = ReporteForm(request.POST, request.FILES)

        # La ubicacion vuelve a pasar por el formulario: no confiamos en la
        # sesion a ojos cerrados, y asi un dato invalido nos manda de vuelta
        # al paso 1 en vez de reventar al guardar.
        form_ubicacion = UbicacionForm(datos_ubicacion)

        if not form_ubicacion.is_valid():
            del request.session[UBICACION_EN_CURSO]
            messages.info(request, "Vuelve a marcar dónde está el desperfecto.")
            return redirect("ubicacion")

        if form.is_valid():
            ubicacion_guardada = form_ubicacion.save()

            # commit=False arma el objeto pero todavia no lo escribe en la base,
            # asi alcanzamos a ponerle los campos que no vienen del formulario.
            reporte = form.save(commit=False)
            reporte.ubicacion = ubicacion_guardada
            reporte.creador = request.user
            reporte.save()

            # El borrador ya es un reporte de verdad; limpiamos la sesion para
            # que el proximo reporte empiece de cero.
            del request.session[UBICACION_EN_CURSO]

            messages.success(request, "Tu reporte quedó registrado.")
            return redirect("mis_reportes")
    else:
        form = ReporteForm()

    contexto = {
        "form": form,
        # Para mostrarle arriba la direccion que eligio en el paso anterior.
        "direccion": datos_ubicacion["direccion_texto"],
        "comuna": datos_ubicacion["comuna"],
    }
    return render(request, 'reportes/reportar.html', contexto)


@login_required
def mis_reportes(request):
    # Solo los reportes del usuario que inicio sesion, del mas nuevo al mas viejo.
    # select_related trae la categoria y la ubicacion en la misma consulta,
    # para no pegarle a la base una vez por cada fila de la lista.
    reportes = (
        Reporte.objects
        .filter(creador=request.user)
        .select_related("categoria", "ubicacion")
        .order_by("-fecha_creacion")
    )
    return render(request, 'reportes/mis_reportes.html', {"reportes": reportes})
@login_required
def mas_detalle(request):
    return render(request, 'reportes/mas_detalle.html')

def panel_municipal(request):
    reportes_obtenidos = Reporte.objects.all()
    
    contexto = {
        'reportes': reportes_obtenidos
    }
    return render(request, 'reportes/panel_municipal.html', contexto)
