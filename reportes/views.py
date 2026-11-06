from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .cercania import RADIO_METROS, reportes_cercanos
from .forms import RegistroForm, ReporteForm, UbicacionForm
from .models import Confirmacion, Reporte

UBICACION_EN_CURSO = "ubicacion_en_curso"

# Cuantos reportes cercanos se muestran a la vez.
MAXIMO_EN_PANTALLA = 6


class EntrarView(LoginView):
    #Iniciar sesion

    template_name = "reportes/login.html"
    redirect_authenticated_user = True

def calculate_severity(report_type, confirmations):
    base_score = 0
    high_risk_types = ['Árbol con riesgo de caída', 'Cable o poste']
    
    if report_type in high_risk_types:
        base_score = 5 
        
    total_score = base_score + confirmations
    
    if total_score < 5:
        return 'Baja'
    elif total_score < 15:
        return 'Media'
    else:
        return 'Alta'



def inicio(request):
    hace_una_semana = timezone.now() - timedelta(days=7)

    # Los reportes que se dibujan como pines en el mapa.
    reportes = (
        Reporte.objects
        .select_related("categoria", "ubicacion")
        .order_by("-fecha_creacion")[:100]
    )

    puntos = [
        {
            "id": r.id,
            "lat": r.ubicacion.latitud,
            "lon": r.ubicacion.longitud,
            "categoria": str(r.categoria),
            "comuna": r.ubicacion.comuna,
            "estado": r.estado_actual,
            "etiqueta": r.get_estado_actual_display(),
            "gravedad": calculate_severity(str(r.categoria), r.confirmacion_set.count()) 
        }
        for r in reportes
    ]

    contexto = {
        "puntos": puntos,
        "cantidad_reportes": Reporte.objects.filter(
            fecha_creacion__gte=hace_una_semana
        ).count(),
    }

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
            # No va derecho a escribir el reporte: primero el sistema le
            # muestra lo que ya hay reportado en ese lugar.
            return redirect("cercanos")
    else:
        form = UbicacionForm()

    return render(request, "reportes/ubicacion.html", {"form": form})


@login_required
def cercanos(request):

    datos_ubicacion = request.session.get(UBICACION_EN_CURSO)
    if not datos_ubicacion:
        messages.info(request, "Primero marca dónde está el desperfecto.")
        return redirect("ubicacion")

    encontrados = reportes_cercanos(
        datos_ubicacion["latitud"], datos_ubicacion["longitud"]
    )

    if request.method == "POST":
        # Solo se puede confirmar algo que esta en esta misma pantalla. La
        # lista de permitidos se rearma en vez de confiar en el id que llego:
        # si no, con cualquier id se podria confirmar un reporte del otro lado
        # de la ciudad sin haber estado nunca ahi.
        permitidos = {
            str(reporte.id): reporte
            for reporte, _ in encontrados[:MAXIMO_EN_PANTALLA]

            if reporte.creador_id != request.user.id
        }
        reporte = permitidos.get(request.POST.get("reporte"))

        if reporte is None:

            messages.info(request, "Ese reporte ya no está disponible para confirmar.")
            return redirect("cercanos")


        Confirmacion.objects.get_or_create(reporte=reporte, usuario=request.user)

        del request.session[UBICACION_EN_CURSO]

        messages.success(request, "Listo, confirmaste el reporte.")
        return redirect("detalle", reporte_id=reporte.id)

    # Si no hay nada cerca, una pantalla vacia solo le suma un clic: se va
    # derecho a escribir el reporte.
    if not encontrados:
        return redirect("reportar")

    contexto = {
        # La plantilla recibe los metros ya calculados junto a cada reporte,
        # porque la distancia no es un campo de la base.
        "cercanos": [
            {
                "reporte": reporte,
                "metros": metros,
                "confirmaciones": reporte.confirmacion_set.count(),
                "lo_reporte_yo": reporte.creador_id == request.user.id,
            }
            for reporte, metros in encontrados[:MAXIMO_EN_PANTALLA]
        ],
        "direccion": datos_ubicacion["direccion_texto"],
        "comuna": datos_ubicacion["comuna"],
        "radio": RADIO_METROS,
    }
    return render(request, "reportes/cercanos.html", contexto)


@login_required
def reportar(request):
    datos_ubicacion = request.session.get(UBICACION_EN_CURSO)
    if not datos_ubicacion:
        messages.info(request, "Primero marca dónde está el desperfecto.")
        return redirect("ubicacion")

    if request.method == "POST":
        # request.POST trae los campos de texto, request.FILES trae la foto.
        form = ReporteForm(request.POST, request.FILES)

        form_ubicacion = UbicacionForm(datos_ubicacion)

        if not form_ubicacion.is_valid():
            del request.session[UBICACION_EN_CURSO]
            messages.info(request, "Vuelve a marcar dónde está el desperfecto.")
            return redirect("ubicacion")

        if form.is_valid():
            ubicacion_guardada = form_ubicacion.save()

            reporte = form.save(commit=False)
            reporte.ubicacion = ubicacion_guardada
            reporte.creador = request.user
            reporte.save()

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

    # distinct() porque un reporte propio que ademas confirmo calzaria con los
    # dos lados del OR y saldria dos veces en la lista.
    # select_related trae la categoria y la ubicacion en la misma consulta,
    # para no pegarle a la base una vez por cada fila.
    reportes = (
        Reporte.objects
        .filter(Q(creador=request.user) | Q(confirmacion__usuario=request.user))
        .select_related("categoria", "ubicacion")
        .distinct()
        .order_by("-fecha_creacion")
    )

    for reporte in reportes:
        reporte.lo_reporte_yo = reporte.creador_id == request.user.id

    return render(request, 'reportes/mis_reportes.html', {"reportes": reportes})

@login_required
def mas_detalle(request):
    return render(request, 'reportes/mas_detalle.html')

def panel_municipal(request):
    reportes_obtenidos = Reporte.objects.all()
    ahora = timezone.now()

    for reporte in reportes_obtenidos:
        diferencia = ahora - reporte.fecha_creacion
        reporte.dias_antiguedad = diferencia.days

    cantidad_recibidos = Reporte.objects.filter(estado_actual="recibido").count()
    cantidad_revision = Reporte.objects.filter(estado_actual="en_revision").count()
    cantidad_atendidos = Reporte.objects.filter(estado_actual="atendido").count()
    
    contexto = {
        'reportes': reportes_obtenidos,
        'total_recibidos': cantidad_recibidos,
        'total_revision': cantidad_revision, 
        'total_atendidos': cantidad_atendidos
    }
    return render(request, 'reportes/panel_municipal.html', contexto)

def actualizar_estado(request):
    if request.method == 'POST':
        reporte_id = request.POST.get('reporte_id')
        nuevo_estado = request.POST.get('estado_rep')
        comentario = request.POST.get('comentario', '')
        
        if reporte_id and nuevo_estado:
            reporte = Reporte.objects.get(id=reporte_id)
            reporte.estado_actual = nuevo_estado
            reporte.save()
            
    return redirect('panel_municipal')

def terminos(request):
    return render(request, 'reportes/terminos.html')


@login_required
def detalle(request, reporte_id):

    reporte = get_object_or_404(
        Reporte.objects.select_related("categoria", "ubicacion"), pk=reporte_id
    )

    etiquetas = dict(Reporte.ESTADOS)

    contexto = {
        "reporte": reporte,
        # Del mas viejo al mas nuevo: asi se lee como una historia.
        "historial": [
            {
                "estado": etiquetas.get(cambio.estado_nuevo, cambio.estado_nuevo),
                "comentario": cambio.comentario,
                "fecha": cambio.fecha,
            }
            for cambio in reporte.cambioestado_set.order_by("fecha")
        ],
        "confirmaciones": reporte.confirmacion_set.count(),
        "lo_reporte_yo": reporte.creador_id == request.user.id,
        "lo_confirme_yo": reporte.confirmacion_set.filter(
            usuario=request.user
        ).exists(),
    }
    return render(request, "reportes/detalle.html", contexto)
