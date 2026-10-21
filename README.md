# Desperfectos RM

Aplicación para reportar desperfectos en la vía pública. Proyecto del ramo
IWG-400, equipo 13.

## Para levantarlo

Desde la carpeta del proyecto, la primera vez:

```
python -m venv venv
venv\Scripts\activate
pip install django pillow
python manage.py migrate
python manage.py runserver
```

Y queda andando en http://127.0.0.1:8000

De ahí en adelante basta con activar el venv y correr el servidor.

## Después de cada merge, corre migrate

```
python manage.py migrate
```

La base de datos (`db.sqlite3`) **no está en el repositorio** y no tiene que
estarlo: es un archivo binario, git no lo sabe mezclar, y el último que hiciera
push le borraría los datos a los demás.

Por eso todo lo que tiene que existir en la base de todos viaja como migración,
no como archivo. Las seis opciones de "Tipo de desperfecto" son un ejemplo: las
crea la migración `0003_categorias_iniciales`. Si no corres `migrate` después de
un merge, el selector te va a salir vacío.

Si alguna vez hay que agregar una opción nueva, se agrega en una migración de
datos igual que esa, nunca a mano en la base de uno.

## Cuentas

No hay usuarios de prueba en el repositorio. Crea el tuyo desde
`/accounts/registro/`, o uno de administrador con:

```
python manage.py createsuperuser
```

## Cómo está organizado

| Ruta | Qué es |
|---|---|
| `/` | Inicio, el mapa con los reportes |
| `/ubicacion/` | Paso 1, dónde está el desperfecto |
| `/reportar/` | Paso 2, qué es y la foto |
| `/mis-reportes/` | Los reportes del usuario conectado |
| `/accounts/login/` | Iniciar sesión |
| `/accounts/registro/` | Crear una cuenta |
| `/admin/` | Administración de Django |

Las plantillas están todas en `reportes/templates/reportes/`.


## Cómo limpiar la base de datos (Solución al error del mapa en Inicio)

¿Por qué hacer esto?
Durante las pruebas de la pantalla de ubicación, se guardaron reportes sin coordenadas GPS (campos de latitud y longitud vacíos). Cuando la pantalla de inicio (inicio.html) intenta dibujar esos puntos invisibles usando Leaflet, el mapa colapsa y deja de mostrar todos los pines.

Para que el mapa vuelva a funcionar, debemos eliminar esos reportes corruptos de la base de datos siguiendo estos pasos:

Paso a paso:

1. Detener el servidor: Ve a la terminal de VS Code donde está corriendo Django y presiona Ctrl + C.

2. Abrir la consola de Django: Escribe el siguiente comando para entrar al entorno interactivo (verás que aparecen tres flechas >>>):

```
python manage.py shell
```

3. Importar la tabla de Reportes: Una vez dentro de la consola, escribe esto y presiona Enter:

```
from reportes.models import Reporte
```

4. Borrar todos los registros: Ejecuta el comando de eliminación masiva. (La consola te devolverá un número confirmando cuántos reportes borró).

```
Reporte.objects.all().delete()
```

5. Salir de la consola: Escribe el comando para cerrar el entorno interactivo y presiona Enter:

```
exit()
```

6. Reiniciar el proyecto: Vuelve a levantar el servidor normalmente:

```
python manage.py runserver
```

> **Nota:** *Ya se agregó un seguro en el código de ubicacion.html para forzar que el formulario siempre capture las coordenadas exactas.*
