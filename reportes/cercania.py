"""Buscar reportes cerca de un punto.

Es lo que necesita el paso 2 del flujo: antes de dejar que alguien escriba un
reporte nuevo, hay que mostrarle los que ya existen en ese lugar para que
confirme uno en vez de duplicarlo.

SQLite no sabe de geografia: no trae funciones de distancia ni indices
espaciales. Asi que el filtro va en dos pasos.

1. La base descarta lo que esta claramente lejos comparando latitud y longitud
   con mayor/menor, o sea un cuadrado alrededor del punto. Eso es una consulta
   que SQLite hace rapido.
2. Python le calcula la distancia real a los pocos que quedaron y deja solo
   los que estan dentro del circulo.

Hace falta el paso 2 porque el cuadrado es mas grande que el circulo: le
sobran las cuatro esquinas. Sin el, un reporte en una esquina del cuadrado
pasaria el filtro estando a mas metros que el radio.
"""
from math import asin, cos, radians, sin, sqrt

from .models import Reporte

# Hasta donde buscamos. A 150 m dos avisos son, con cualquier criterio, el
# mismo bache; mas lejos ya es otro problema de la misma cuadra.
# PROPUESTA mia: el equipo todavia no fijo este numero.
RADIO_METROS = 150

# Un reporte atendido ya se arreglo y uno descartado no era un desperfecto:
# ninguno de los dos sirve para confirmar, asi que no se muestran.
ESTADOS_VIGENTES = ("recibido", "en_revision")

# Radio de la Tierra en metros.
RADIO_TIERRA = 6_371_000

# Un grado de latitud son ~111,32 km en cualquier parte del mundo. Con la
# longitud no pasa lo mismo: los meridianos se juntan hacia los polos, por eso
# mas abajo se corrige con el coseno de la latitud.
METROS_POR_GRADO_LAT = 111_320


def distancia_metros(lat1, lon1, lat2, lon2):
    """Distancia en metros entre dos puntos, por la formula de haversine.

    Es la distancia "en linea recta" sobre la superficie de la Tierra, no por
    las calles. Para decidir si dos avisos son del mismo desperfecto basta y
    sobra: no estamos calculando una ruta.
    """
    dif_lat = radians(lat2 - lat1)
    dif_lon = radians(lon2 - lon1)
    a = (
        sin(dif_lat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dif_lon / 2) ** 2
    )
    return 2 * RADIO_TIERRA * asin(sqrt(a))


def reportes_cercanos(latitud, longitud, radio=RADIO_METROS):
    """Reportes vigentes a menos de `radio` metros del punto.

    Devuelve una lista de pares (reporte, metros), del mas cercano al mas
    lejano, para que la pantalla parta por el candidato mas probable.
    """
    grados_lat = radio / METROS_POR_GRADO_LAT

    # Cuanto mide un grado de longitud a esta latitud. El max() es para no
    # dividir por cero si algun dia a alguien le llega una coordenada en el
    # polo, donde el coseno es 0; con un valor chico el cuadrado del paso 1
    # queda mas ancho de lo necesario, pero el paso 2 igual da la respuesta
    # correcta.
    metros_por_grado_lon = METROS_POR_GRADO_LAT * max(abs(cos(radians(latitud))), 0.01)
    grados_lon = radio / metros_por_grado_lon

    candidatos = (
        Reporte.objects
        .filter(
            estado_actual__in=ESTADOS_VIGENTES,
            ubicacion__latitud__gte=latitud - grados_lat,
            ubicacion__latitud__lte=latitud + grados_lat,
            ubicacion__longitud__gte=longitud - grados_lon,
            ubicacion__longitud__lte=longitud + grados_lon,
        )
        # La pantalla muestra la categoria y la direccion de cada uno; sin esto
        # serian dos consultas extra por cada reporte de la lista.
        .select_related("categoria", "ubicacion")
    )

    cercanos = []
    for reporte in candidatos:
        metros = distancia_metros(
            latitud, longitud, reporte.ubicacion.latitud, reporte.ubicacion.longitud
        )
        if metros <= radio:
            cercanos.append((reporte, round(metros)))

    cercanos.sort(key=lambda par: par[1])
    return cercanos
