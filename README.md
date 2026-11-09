# G.E.V.I

Aplicación para reportar desperfectos en la vía pública. Proyecto del ramo
IWG-400, equipo 13.

## Para levantarlo

Desde la carpeta del proyecto, la primera vez:

```
python -m venv venv
venv\Scripts\activate
pip install django pillow django-axes
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

No hay usuarios de prueba en el repositorio. Crea el tuyo desde la aplicación

## Como crear un superusuario para acceder al panel municipal

paso a paso:

1. Ejecuta el siguiente comando: `python manage.py createsuperuser`

2. Ingresa un nombre de usuario (ej: `muni`).

3. El correo puedes dejarlo en blanco presionando `Enter`.

4. Escribe una contraseña (no se verán los caracteres mientras escribes por seguridad).

5. Ve a la pantalla de login de la aplicación, ingresa en el apartado de correo el nombre de usuario (ej: `muni`) y la contraseña creados anteriormente.

## Cómo limpiar la base de datos (En caso de ser necesario)

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
