from django.test import TestCase

from .models import Categoria


class CategoriasInicialesTest(TestCase):
    """Que las opciones de "Tipo de desperfecto" lleguen solas.

    Django arma la base de las pruebas corriendo todas las migraciones desde
    cero, igual que cuando alguien clona el repo. Si esta prueba pasa, es que
    a cualquiera del equipo le van a quedar cargadas con un simple migrate,
    sin tener que acordarse de ningun comando extra.
    """

    def test_las_seis_categorias_quedan_cargadas(self):
        nombres = list(Categoria.objects.order_by("id").values_list("nombre", flat=True))
        self.assertEqual(
            nombres,
            [
                "Bache o calzada rota",
                "Vereda dañada",
                "Semáforo o señalética",
                "Cable o poste",
                "Árbol con riesgo de caída",
                "Otro",
            ],
        )

    def test_no_quedan_duplicadas(self):
        self.assertEqual(Categoria.objects.count(), 6)

    def test_el_formulario_las_ofrece(self):
        # Lo que de verdad le fallaba a Bastian: el selector salia vacio.
        from .forms import ReporteForm

        opciones = list(ReporteForm().fields["categoria"].queryset)
        self.assertEqual(len(opciones), 6)
