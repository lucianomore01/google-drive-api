# google-drive-api
API en Python con Flask para comunicarnos con Google drive para leer y crear archivos.

## Instrucciones.

Descargar [Visual Studio Code](https://code.visualstudio.com/download).

Descargar e instalar [Python](https://www.python.org/downloads/?source=post_page---------------------------).

Una vez instalado abrir una ventana de terminal, consola, cmd o Power Shell e ingresar para instalar Flask:
```
pip install Flask
//O
py -m pip install Flask
```

### Guardar variables de entorno:

Linux:
```
export FLASK_ENV=development
export FLASK_APP=app.py
```

Windows
```
set FLASK_ENV=development
set FLASK_APP=app.py
```

### Ejecutar:
En la carpeta sandbox
```
python app.py
```

### Authentication
Para volver a loguear el cliente en Google Drive borrar el archivo token.pickle

# Autor
Luciano More.

# Licencia
Ver [Licencia](https://github.com/lucianomore01/google-drive-api/blob/master/LICENSE).
