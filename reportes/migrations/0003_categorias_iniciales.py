# Migracion de DATOS, no de estructura.
#
# Las seis opciones de "Tipo de desperfecto" son filas de la tabla Categoria,
# y db.sqlite3 esta en .gitignore, asi que por git no viajan: a quien clona el
# repo le llega la tabla creada pero vacia y el selector le sale sin opciones.
#
# Poniendolas aca, un "python manage.py migrate" las deja cargadas en la base
# de cualquiera, sin que nadie tenga que acordarse de ningun comando extra.
# Django no genera sola una migracion como esta; makemigrations solo mira si
# cambiaron los modelos, y aca no cambio ninguno.

from django.db import migrations

CATEGORIAS = [
    "Bache o calzada rota",
    "Vereda dañada",
    "Semáforo o señalética",
    "Cable o poste",
    "Árbol con riesgo de caída",
    "Otro",
]


def cargar(apps, schema_editor):
    # Se pide el modelo por apps.get_model y no por un import normal, porque
    # la migracion tiene que trabajar con el modelo tal como era en este punto
    # de la historia, aunque mas adelante alguien le agregue campos.
    Categoria = apps.get_model("reportes", "Categoria")

    for nombre in CATEGORIAS:
        # get_or_create para que, si alguien ya las tenia cargadas a mano,
        # no le queden duplicadas.
        Categoria.objects.get_or_create(
            nombre=nombre, defaults={"gravedad_referencial": ""}
        )


def borrar(apps, schema_editor):
    # Solo se borran las que no esta usando ningun reporte, para no romper
    # datos de alguien que vuelva atras la migracion.
    Categoria = apps.get_model("reportes", "Categoria")
    Categoria.objects.filter(nombre__in=CATEGORIAS, reporte__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("reportes", "0002_ubicacion_reporte_confirmacion_cambioestado"),
    ]

    operations = [
        migrations.RunPython(cargar, borrar),
    ]
