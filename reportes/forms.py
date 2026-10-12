from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Reporte, Ubicacion


class RegistroForm(UserCreationForm):
    """Crear una cuenta.

    Usamos el correo como nombre de usuario: Django acepta el arroba y los
    puntos sin configuracion extra, asi el usuario escribe su correo y entra.
    """

    class Meta:
        model = User
        fields = ["username"]
        labels = {"username": "Correo electrónico"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].label = "Contraseña"
        self.fields["password2"].label = "Repite la contraseña"

        # Los textos de ayuda de Django son largos; la plantilla ya muestra
        # una pista corta debajo del formulario.
        for campo in self.fields.values():
            campo.help_text = ""
            # "v" es la clase con la que Bastian da estilo a las cajas de texto.
            campo.widget.attrs["class"] = "v"

        self.fields["username"].widget.attrs["placeholder"] = "ejemplo@correo.cl"
        self.fields["password1"].widget.attrs["placeholder"] = "••••••••"
        self.fields["password2"].widget.attrs["placeholder"] = "••••••••"

    def clean_username(self):
        correo = self.cleaned_data["username"].strip().lower()
        if User.objects.filter(username__iexact=correo).exists():
            raise forms.ValidationError("Ya existe una cuenta con ese correo.")
        return correo

    def save(self, commit=True):
        usuario = super().save(commit=False)
        # Guardamos el correo tambien en su campo propio, para poder avisarle
        # por mail cuando cambie el estado de su reporte.
        usuario.email = usuario.username
        if commit:
            usuario.save()
        return usuario


# Centro de Santiago. Es el punto que usamos cuando el navegador no nos da
# la coordenada (el usuario no apreto "usar mi ubicacion" o la rechazo).
LAT_POR_DEFECTO = -33.4489
LON_POR_DEFECTO = -70.6693


class UbicacionForm(forms.ModelForm):
    """Donde esta el desperfecto. Es el paso 1 del reporte."""

    class Meta:
        model = Ubicacion
        fields = ["direccion_texto", "comuna", "latitud", "longitud"]
        labels = {
            "direccion_texto": "Dirección o referencia",
            "comuna": "Comuna",
        }
        widgets = {
            "direccion_texto": forms.TextInput(
                attrs={"placeholder": "Ej: Av. Vicuña Mackenna 3900"}
            ),
            "comuna": forms.TextInput(attrs={"placeholder": "Ej: Ñuñoa"}),
            # El boton de geolocalizacion las rellena por JavaScript.
            "latitud": forms.HiddenInput(),
            "longitud": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # La coordenada es un extra: si el navegador no la entrega, el reporte
        # igual tiene que poder enviarse. La direccion escrita si es obligatoria.
        self.fields["latitud"].required = False
        self.fields["longitud"].required = False

        for campo in self.fields.values():
            # "v" es la clase con la que Bastian da estilo a las cajas de texto.
            campo.widget.attrs["class"] = "v"

    def clean_latitud(self):
        return self.cleaned_data.get("latitud") or LAT_POR_DEFECTO

    def clean_longitud(self):
        return self.cleaned_data.get("longitud") or LON_POR_DEFECTO


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Por defecto el selector parte con un texto en ingles.
        self.fields["categoria"].empty_label = "Elige una opción"
