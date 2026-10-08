from django import forms

from .models import Reporte, Ubicacion


class UbicacionForm(forms.ModelForm):
    """Donde esta el desperfecto."""

    class Meta:
        model = Ubicacion
        fields = ["direccion_texto", "comuna", "latitud", "longitud"]
        labels = {
            "direccion_texto": "Dirección",
            "comuna": "Comuna",
        }
        widgets = {
            "direccion_texto": forms.TextInput(
                attrs={"placeholder": "Av. Grecia 1234"}
            ),
            "comuna": forms.TextInput(attrs={"placeholder": "Ñuñoa"}),
            # Estas dos las va a rellenar el mapa mas adelante, por eso van
            # ocultas. Mientras tanto la vista les pone el centro de Santiago.
            "latitud": forms.HiddenInput(),
            "longitud": forms.HiddenInput(),
        }


class ReporteForm(forms.ModelForm):
    """Que se esta reportando."""

    class Meta:
        model = Reporte
        # creador, ubicacion y estado_actual NO se piden al usuario:
        # los dos primeros los pone la vista y el tercero tiene default.
        fields = ["categoria", "descripcion", "foto"]
        labels = {
            "categoria": "Tipo de desperfecto",
            "descripcion": "Descripción",
            "foto": "Foto (opcional)",
        }
        widgets = {
            "descripcion": forms.Textarea(
                attrs={"rows": 4, "placeholder": "Cuenta brevemente qué pasa"}
            ),
        }
