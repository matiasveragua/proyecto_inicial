from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import ReporteForm, UbicacionForm

# Centro de Santiago. Es el punto por defecto mientras el mapa no entregue
# la coordenada real donde el usuario marco el desperfecto.
LAT_POR_DEFECTO = -33.4489
LON_POR_DEFECTO = -70.6693


def inicio(request):
    return render(request, 'reportes/inicio.html')


@login_required
def reportar(request):
    if request.method == "POST":
        # request.POST trae los campos de texto, request.FILES trae la foto.
        form_ubicacion = UbicacionForm(request.POST)
        form_reporte = ReporteForm(request.POST, request.FILES)

        # Los dos formularios tienen que estar correctos antes de guardar nada,
        # para no dejar una ubicacion suelta sin su reporte.
        if form_ubicacion.is_valid() and form_reporte.is_valid():
            ubicacion = form_ubicacion.save()

            # commit=False arma el objeto pero todavia no lo escribe en la base,
            # asi alcanzamos a ponerle los campos que no vienen del formulario.
            reporte = form_reporte.save(commit=False)
            reporte.ubicacion = ubicacion
            reporte.creador = request.user
            reporte.save()

            messages.success(request, "Tu reporte quedó registrado.")
            return redirect("inicio")
    else:
        # Primera visita: formularios vacios.
        form_ubicacion = UbicacionForm(
            initial={"latitud": LAT_POR_DEFECTO, "longitud": LON_POR_DEFECTO}
        )
        form_reporte = ReporteForm()

    contexto = {
        "form_ubicacion": form_ubicacion,
        "form_reporte": form_reporte,
    }
    return render(request, "reportes/reportar.html", contexto)
