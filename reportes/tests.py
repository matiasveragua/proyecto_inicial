from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .cercania import (
    METROS_POR_GRADO_LAT,
    RADIO_METROS,
    distancia_metros,
    reportes_cercanos,
)
from .models import CambioEstado, Categoria, Confirmacion, Reporte, Ubicacion
from .views import UBICACION_EN_CURSO


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


# Centro de Santiago. Es el punto desde donde se mide en todas las pruebas de
# cercania; da igual cual sea, lo que importa son las distancias relativas.
LAT = -33.4489
LON = -70.6693


def mover_al_norte(latitud, metros):
    """La latitud que queda a `metros` al norte de `latitud`.

    Sirve para armar reportes a una distancia conocida sin escribir
    coordenadas a mano. Al norte y no al este porque un grado de latitud mide
    lo mismo en cualquier parte del mundo, asi que la cuenta es directa.
    """
    return latitud + metros / METROS_POR_GRADO_LAT


class AyudaParaReportes(TestCase):
    """Cosas que varias pruebas necesitan armar."""

    def crear_usuario(self, correo="vecina@correo.cl"):
        return User.objects.create_user(username=correo, password="clave-de-prueba-1")

    def crear_reporte(self, creador, latitud=LAT, longitud=LON, estado="recibido"):
        ubicacion = Ubicacion.objects.create(
            latitud=latitud,
            longitud=longitud,
            direccion_texto="Av. Vicuña Mackenna 3900",
            comuna="Ñuñoa",
        )
        return Reporte.objects.create(
            creador=creador,
            ubicacion=ubicacion,
            categoria=Categoria.objects.first(),
            descripcion="Hay un hoyo grande en la calzada.",
            estado_actual=estado,
        )


class DistanciaTest(TestCase):
    """La formula de haversine, suelta."""

    def test_el_mismo_punto_esta_a_cero_metros(self):
        self.assertEqual(distancia_metros(LAT, LON, LAT, LON), 0)

    def test_un_grado_de_latitud_son_unos_111_kilometros(self):
        metros = distancia_metros(-33.0, -70.0, -34.0, -70.0)
        # El valor exacto es 111.195 m; con 500 m de holgura la prueba no se
        # rompe si alguien ajusta el radio de la Tierra que usamos.
        self.assertAlmostEqual(metros, 111_195, delta=500)

    def test_la_distancia_no_depende_del_orden(self):
        ida = distancia_metros(LAT, LON, LAT + 0.01, LON + 0.01)
        vuelta = distancia_metros(LAT + 0.01, LON + 0.01, LAT, LON)
        self.assertAlmostEqual(ida, vuelta, places=6)


class CercaniaTest(AyudaParaReportes):
    """A quienes muestra y a quienes deja fuera la consulta de cercanos."""

    def setUp(self):
        self.usuario = self.crear_usuario()

    def test_muestra_lo_que_esta_al_lado(self):
        reporte = self.crear_reporte(self.usuario, latitud=mover_al_norte(LAT, 50))

        encontrados = reportes_cercanos(LAT, LON)

        self.assertEqual([r for r, _ in encontrados], [reporte])

    def test_deja_fuera_lo_que_esta_lejos(self):
        self.crear_reporte(
            self.usuario, latitud=mover_al_norte(LAT, RADIO_METROS * 3)
        )

        self.assertEqual(reportes_cercanos(LAT, LON), [])

    def test_la_esquina_del_cuadrado_no_pasa(self):
        """El filtro de la base es un cuadrado; la respuesta tiene que ser un circulo.

        Este reporte queda dentro del cuadrado que arma la consulta, porque su
        latitud y su longitud estan las dos dentro del rango, pero en diagonal
        la distancia real es el radio por raiz de dos: 212 m con un radio de
        150. Si esta prueba falla, es que se perdio el segundo paso del filtro
        y la pantalla esta ofreciendo reportes de mas lejos de lo que dice.
        """
        from math import cos, radians

        metros_por_grado_lon = METROS_POR_GRADO_LAT * cos(radians(LAT))
        esquina = self.crear_reporte(
            self.usuario,
            latitud=LAT + RADIO_METROS / METROS_POR_GRADO_LAT,
            longitud=LON + RADIO_METROS / metros_por_grado_lon,
        )

        # Esta a mas de 200 m, o sea fuera del radio.
        real = distancia_metros(
            LAT, LON, esquina.ubicacion.latitud, esquina.ubicacion.longitud
        )
        self.assertGreater(real, RADIO_METROS)

        self.assertEqual(reportes_cercanos(LAT, LON), [])

    def test_van_del_mas_cercano_al_mas_lejano(self):
        lejano = self.crear_reporte(self.usuario, latitud=mover_al_norte(LAT, 120))
        cercano = self.crear_reporte(self.usuario, latitud=mover_al_norte(LAT, 20))
        medio = self.crear_reporte(self.usuario, latitud=mover_al_norte(LAT, 70))

        encontrados = reportes_cercanos(LAT, LON)

        self.assertEqual([r for r, _ in encontrados], [cercano, medio, lejano])

    def test_devuelve_los_metros(self):
        self.crear_reporte(self.usuario, latitud=mover_al_norte(LAT, 50))

        _, metros = reportes_cercanos(LAT, LON)[0]

        self.assertAlmostEqual(metros, 50, delta=2)

    def test_no_ofrece_los_atendidos_ni_los_descartados(self):
        """Un desperfecto arreglado o descartado no se puede confirmar.

        Si apareciera, alguien confirmaria un bache que ya se tapo y el panel
        municipal lo veria revivir.
        """
        for estado in ("atendido", "descartado"):
            self.crear_reporte(
                self.usuario, latitud=mover_al_norte(LAT, 30), estado=estado
            )

        self.assertEqual(reportes_cercanos(LAT, LON), [])

    def test_si_ofrece_los_que_estan_en_revision(self):
        reporte = self.crear_reporte(
            self.usuario, latitud=mover_al_norte(LAT, 30), estado="en_revision"
        )

        self.assertEqual([r for r, _ in reportes_cercanos(LAT, LON)], [reporte])


class PasoDeCercanosTest(AyudaParaReportes):
    """La pantalla del paso 2 y la confirmacion."""

    def setUp(self):
        self.usuario = self.crear_usuario()
        self.vecino = self.crear_usuario("vecino@correo.cl")
        self.client.force_login(self.usuario)

    def dejar_ubicacion_en_la_sesion(self):
        sesion = self.client.session
        sesion[UBICACION_EN_CURSO] = {
            "direccion_texto": "Av. Vicuña Mackenna 3900",
            "comuna": "Ñuñoa",
            "latitud": LAT,
            "longitud": LON,
        }
        sesion.save()

    def test_pide_sesion(self):
        self.client.logout()

        respuesta = self.client.get(reverse("cercanos"))

        self.assertIn(reverse("login"), respuesta["Location"])

    def test_el_paso_1_ahora_lleva_a_la_consulta_de_cercanos(self):
        respuesta = self.client.post(
            reverse("ubicacion"),
            {
                "direccion_texto": "Av. Vicuña Mackenna 3900",
                "comuna": "Ñuñoa",
                "latitud": LAT,
                "longitud": LON,
            },
        )

        self.assertRedirects(respuesta, reverse("cercanos"), target_status_code=302)

    def test_sin_ubicacion_en_la_sesion_vuelve_al_paso_1(self):
        respuesta = self.client.get(reverse("cercanos"))

        self.assertRedirects(respuesta, reverse("ubicacion"))

    def test_si_no_hay_nada_cerca_pasa_derecho_a_escribir(self):
        self.dejar_ubicacion_en_la_sesion()

        respuesta = self.client.get(reverse("cercanos"))

        self.assertRedirects(respuesta, reverse("reportar"))

    def test_muestra_el_reporte_del_vecino(self):
        self.dejar_ubicacion_en_la_sesion()
        self.crear_reporte(self.vecino, latitud=mover_al_norte(LAT, 40))

        respuesta = self.client.get(reverse("cercanos"))

        self.assertContains(respuesta, "Es este, lo confirmo")
        self.assertContains(respuesta, "a 40 m")

    def test_no_se_imprimen_comentarios_de_la_plantilla(self):
        """Un {# ... #} de varias lineas sale impreso en la pantalla.

        Django solo trata como comentario lo que va entre {# y #} en una misma
        linea; si el comentario sigue en la linea de abajo, el texto se dibuja
        tal cual. Paso de verdad en esta pantalla y ninguna prueba lo vio,
        porque todas revisaban que el contenido estuviera, no que no hubiera
        contenido de mas.
        """
        self.dejar_ubicacion_en_la_sesion()
        self.crear_reporte(self.usuario, latitud=mover_al_norte(LAT, 40))
        self.crear_reporte(self.vecino, latitud=mover_al_norte(LAT, 60))

        respuesta = self.client.get(reverse("cercanos"))

        self.assertNotContains(respuesta, "{#")
        self.assertNotContains(respuesta, "{%")

    def test_el_propio_no_se_puede_confirmar_desde_la_pantalla(self):
        self.dejar_ubicacion_en_la_sesion()
        self.crear_reporte(self.usuario, latitud=mover_al_norte(LAT, 40))

        respuesta = self.client.get(reverse("cercanos"))

        self.assertNotContains(respuesta, "Es este, lo confirmo")
        self.assertContains(respuesta, "Este lo reportaste tú.")

    def test_confirmar_guarda_la_confirmacion_y_lleva_al_seguimiento(self):
        self.dejar_ubicacion_en_la_sesion()
        reporte = self.crear_reporte(self.vecino, latitud=mover_al_norte(LAT, 40))

        respuesta = self.client.post(reverse("cercanos"), {"reporte": reporte.id})

        self.assertRedirects(respuesta, reverse("detalle", args=[reporte.id]))
        self.assertTrue(
            Confirmacion.objects.filter(reporte=reporte, usuario=self.usuario).exists()
        )

    def test_confirmar_limpia_el_borrador_de_ubicacion(self):
        """Ya no va a escribir un reporte, asi que la ubicacion no debe quedar.

        Si quedara, el siguiente reporte partiria con la direccion de este.
        """
        self.dejar_ubicacion_en_la_sesion()
        reporte = self.crear_reporte(self.vecino, latitud=mover_al_norte(LAT, 40))

        self.client.post(reverse("cercanos"), {"reporte": reporte.id})

        self.assertNotIn(UBICACION_EN_CURSO, self.client.session)

    def test_no_se_puede_confirmar_el_propio_mandando_el_id_a_mano(self):
        self.dejar_ubicacion_en_la_sesion()
        reporte = self.crear_reporte(self.usuario, latitud=mover_al_norte(LAT, 40))

        self.client.post(reverse("cercanos"), {"reporte": reporte.id})

        self.assertEqual(Confirmacion.objects.count(), 0)

    def test_no_se_puede_confirmar_uno_que_no_esta_cerca(self):
        """El id llega por el navegador, asi que la vista no se puede confiar.

        Sin la revision, alguien confirmaria desde la casa un desperfecto del
        otro lado de la ciudad, que es justo lo que la confirmacion no debe
        permitir: dice "yo lo vi".
        """
        self.dejar_ubicacion_en_la_sesion()
        lejano = self.crear_reporte(
            self.vecino, latitud=mover_al_norte(LAT, RADIO_METROS * 10)
        )

        respuesta = self.client.post(reverse("cercanos"), {"reporte": lejano.id})

        self.assertRedirects(respuesta, reverse("cercanos"), target_status_code=302)
        self.assertEqual(Confirmacion.objects.count(), 0)

    def test_apretar_dos_veces_no_cuenta_dos_veces(self):
        self.dejar_ubicacion_en_la_sesion()
        reporte = self.crear_reporte(self.vecino, latitud=mover_al_norte(LAT, 40))

        self.client.post(reverse("cercanos"), {"reporte": reporte.id})
        self.dejar_ubicacion_en_la_sesion()
        self.client.post(reverse("cercanos"), {"reporte": reporte.id})

        self.assertEqual(Confirmacion.objects.count(), 1)


class SeguimientoTest(AyudaParaReportes):
    """La lista de "Mis reportes" y la pantalla de detalle."""

    def setUp(self):
        self.usuario = self.crear_usuario()
        self.vecino = self.crear_usuario("vecino@correo.cl")
        self.client.force_login(self.usuario)

    def test_el_detalle_pide_sesion(self):
        reporte = self.crear_reporte(self.usuario)
        self.client.logout()

        respuesta = self.client.get(reverse("detalle", args=[reporte.id]))

        self.assertIn(reverse("login"), respuesta["Location"])

    def test_un_reporte_que_no_existe_es_404(self):
        respuesta = self.client.get(reverse("detalle", args=[9999]))

        self.assertEqual(respuesta.status_code, 404)

    def test_el_detalle_muestra_el_estado_y_el_lugar(self):
        reporte = self.crear_reporte(self.usuario)

        respuesta = self.client.get(reverse("detalle", args=[reporte.id]))

        self.assertContains(respuesta, "Recibido")
        self.assertContains(respuesta, "Av. Vicuña Mackenna 3900")
        self.assertContains(respuesta, "Lo reportaste tú")

    def test_sin_movimientos_el_detalle_lo_dice(self):
        reporte = self.crear_reporte(self.usuario)

        respuesta = self.client.get(reverse("detalle", args=[reporte.id]))

        self.assertContains(respuesta, "Nadie ha movido el estado todavía")

    def test_el_historial_sale_con_la_etiqueta_y_no_con_el_codigo(self):
        """CambioEstado guarda "en_revision"; en pantalla va "En revisión"."""
        reporte = self.crear_reporte(self.usuario, estado="en_revision")
        CambioEstado.objects.create(
            reporte=reporte,
            gestor=self.vecino,
            estado_anterior="recibido",
            estado_nuevo="en_revision",
            comentario="Lo derivamos a la unidad de pavimentos.",
        )

        respuesta = self.client.get(reverse("detalle", args=[reporte.id]))

        self.assertContains(respuesta, "En revisión")
        self.assertContains(respuesta, "Lo derivamos a la unidad de pavimentos.")
        self.assertNotContains(respuesta, "en_revision")

    def test_el_detalle_no_muestra_quien_cambio_el_estado(self):
        """El gestor es una cuenta municipal; su nombre no va en pantalla."""
        reporte = self.crear_reporte(self.usuario)
        CambioEstado.objects.create(
            reporte=reporte,
            gestor=self.vecino,
            estado_anterior="recibido",
            estado_nuevo="atendido",
        )

        respuesta = self.client.get(reverse("detalle", args=[reporte.id]))

        self.assertNotContains(respuesta, self.vecino.username)

    def test_el_detalle_cuenta_las_confirmaciones(self):
        reporte = self.crear_reporte(self.usuario)
        Confirmacion.objects.create(reporte=reporte, usuario=self.vecino)

        respuesta = self.client.get(reverse("detalle", args=[reporte.id]))

        self.assertContains(respuesta, "1 persona lo confirmó")

    def test_mis_reportes_muestra_los_propios(self):
        reporte = self.crear_reporte(self.usuario)

        respuesta = self.client.get(reverse("mis_reportes"))

        self.assertEqual(list(respuesta.context["reportes"]), [reporte])

    def test_mis_reportes_tambien_muestra_lo_confirmado(self):
        """Si confirmar no dejara el reporte en la lista, se perderia de vista."""
        del_vecino = self.crear_reporte(self.vecino)
        Confirmacion.objects.create(reporte=del_vecino, usuario=self.usuario)

        respuesta = self.client.get(reverse("mis_reportes"))

        self.assertEqual(list(respuesta.context["reportes"]), [del_vecino])
        self.assertContains(respuesta, "Lo confirmaste")

    def test_mis_reportes_no_muestra_los_de_otros(self):
        self.crear_reporte(self.vecino)

        respuesta = self.client.get(reverse("mis_reportes"))

        self.assertEqual(list(respuesta.context["reportes"]), [])

    def test_un_reporte_propio_y_confirmado_sale_una_sola_vez(self):
        """El OR de la consulta calza por los dos lados; distinct() lo arregla."""
        reporte = self.crear_reporte(self.usuario)
        Confirmacion.objects.create(reporte=reporte, usuario=self.usuario)

        respuesta = self.client.get(reverse("mis_reportes"))

        self.assertEqual(list(respuesta.context["reportes"]), [reporte])

    def test_la_lista_lleva_al_detalle(self):
        reporte = self.crear_reporte(self.usuario)

        respuesta = self.client.get(reverse("mis_reportes"))

        self.assertContains(respuesta, reverse("detalle", args=[reporte.id]))


class CandadoDeConfirmacionTest(AyudaParaReportes):
    """El candado de la base, por si alguien escribe desde otro lado."""

    def test_la_base_no_acepta_dos_confirmaciones_de_la_misma_persona(self):
        from django.db import IntegrityError

        usuario = self.crear_usuario()
        reporte = self.crear_reporte(usuario)
        Confirmacion.objects.create(reporte=reporte, usuario=usuario)

        with self.assertRaises(IntegrityError):
            Confirmacion.objects.create(reporte=reporte, usuario=usuario)
