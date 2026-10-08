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
