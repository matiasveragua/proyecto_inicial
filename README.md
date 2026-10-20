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
