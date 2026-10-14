# Levantar el SGR en local con Git Bash (MariaDB o SQLite) y probar la API con Apidog

Guía única para Windows con **Git Bash**. Proyecto: `ChristianInacapBarrera/Proyecto_Integrado_SGR`, rama `main` (Django 6.1 con API REST y JWT).

**Cuentas de prueba:**
- **Web** (`http://127.0.0.1:8000/`): `admin_sgr`, `admin_centro`, `funcionario_centro`, `verificador_leia`, con la clave `DEMO_PASSWORD`.
- **API**: `api_admin` (lee y escribe), `api_operador` (solo lee) y `api_sin_rol` (recibe 403), con la clave `API_PASSWORD`.

---

## 0. Elige la base de datos

Los dos modos usan **el mismo código y los mismos datos**. Solo cambia el `.env`.

| | **A · MariaDB** | **B · SQLite** |
| --- | --- | --- |
| Instalación extra | MariaDB 10.11 o superior | Ninguna |
| Dónde queda la base | Servicio de MariaDB | Archivo `db.sqlite3` en la carpeta del proyecto (no se sube a Git) |
| Cuándo usarla | Es la base del proyecto; la que se usa en AWS | Laboratorio o computador sin MariaDB |
| Pasos que se saltan | — | La sección 3 completa |

Todo lo demás (secciones 1, 2 y 4 en adelante) es igual en los dos modos.

### Reglas de Git Bash
- Las rutas se escriben con `/`, no con `\`. En bash la barra invertida se borra: `.venv\Scripts\activate` se convierte en `.venvScriptsactivate`.
- Si un comando de MariaDB pide una clave, antepón `winpty`; si no, la ventana se queda colgada sin mostrar el prompt.
- Cada ventana nueva de Git Bash empieza **sin** el entorno virtual activado: hay que volver a activarlo (sección 2).

---

## 1. Programas necesarios (una vez)

1. **Git (incluye Git Bash):** https://git-scm.com/download/win, con las opciones por defecto.
2. **Python 3.12:** https://www.python.org/downloads/. En la primera pantalla, marca **«Add python.exe to PATH»**.
3. **Solo modo A, MariaDB 10.11 o superior:** https://mariadb.org/download/ (instalador MSI). Durante la instalación:
   - define una clave para el usuario `root` y anótala;
   - deja marcado «Install as service» y el puerto 3306;
   - deja marcada la opción para agregar MariaDB al PATH, si aparece.

Comprueba en una ventana **nueva** de Git Bash:
```bash
git --version
python --version          # 3.12.x  (si abre la Microsoft Store o no responde, usa: py -3.12 --version)
mariadb --version         # solo modo A. Si no lo reconoce, abre «MariaDB Command Prompt» desde el menú Inicio
```

---

## 2. Proyecto y entorno virtual

Si ya tienes clonado el repositorio, salta el `git clone` y entra a su carpeta.
```bash
cd ~
git clone https://github.com/ChristianInacapBarrera/Proyecto_Integrado_SGR.git
cd Proyecto_Integrado_SGR
git checkout main
git pull
python -m venv .venv
source .venv/Scripts/activate
```
Desde aquí, el prompt muestra `(.venv)`. Para comprobarlo, ejecuta `which python`: debe apuntar a `.../Proyecto_Integrado_SGR/.venv/Scripts/python`.

Si `python` no funciona, crea el entorno con `py -3.12 -m venv .venv`; una vez activado, `python` ya funciona. Comprueba con `python --version` (dentro del entorno) que diga **3.12.x**.

### Instalar las dependencias
```bash
pip install -r requirements.txt
```

**Solo modo B (SQLite), si `mysqlclient` da error de instalación:** ese paquete solo se usa con MariaDB, así que se puede omitir:
```bash
grep -v '^mysqlclient' requirements.txt > req_sqlite.txt
pip install -r req_sqlite.txt
rm req_sqlite.txt
```

> La carpeta del proyecto puede estar en otro lugar (por ejemplo, el Escritorio). En ese caso usa su ruta en los `cd` de esta guía, por ejemplo `cd ~/Desktop/Proyecto_Integrado_SGR`. Con `pwd -W` ves su ruta de Windows (`C:\Users\...`), que necesitarás en Apidog.

---

## 3. Solo modo A: crear la base de datos y el usuario en MariaDB (una vez)

```bash
winpty mariadb -u root -p
```
Escribe la clave de `root` (no se ve mientras la escribes; es normal). Dentro de MariaDB, cambia `TuClaveBD#2026` por una tuya:
```sql
CREATE DATABASE IF NOT EXISTS sgr CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'sgr_app'@'localhost' IDENTIFIED BY 'TuClaveBD#2026';
ALTER USER 'sgr_app'@'localhost' IDENTIFIED BY 'TuClaveBD#2026';
GRANT ALL PRIVILEGES ON sgr.* TO 'sgr_app'@'localhost';
GRANT ALL PRIVILEGES ON test_sgr.* TO 'sgr_app'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```
Comprueba la conexión:
```bash
winpty mariadb -u sgr_app -p -h 127.0.0.1 sgr -e "SELECT 'conexion OK';"
```
Debe responder `conexion OK`. Si no, mira «Si algo falla» al final.

---

## 4. Archivo `.env`

El `.env` tiene la clave secreta de Django, la base de datos y las claves de las cuentas de prueba. **No se sube a Git.** Este bloque lo crea y lo completa solo, y genera la `SECRET_KEY` por ti (más seguro que copiarla a mano).

Primero define tus valores. Cambia el modo (`mariadb` o `sqlite`) y las claves; `CLAVE_BD` solo se usa en MariaDB y debe ser la misma del paso anterior:
```bash
export MODO=mariadb                 # o: export MODO=sqlite
export CLAVE_BD='TuClaveBD#2026'
export CLAVE_DEMO='Demo#Local-2026'
export CLAVE_API='Api#Local-2026'
```
Las claves de las cuentas deben tener al menos 10 caracteres, con mayúscula, minúscula, número y símbolo. Luego copia el `.env` de ejemplo y ejecuta el generador:
```bash
cp .env.example .env
python - <<'PY'
import os, pathlib, re
from django.core.management.utils import get_random_secret_key

modo = os.environ.get('MODO', 'mariadb')
valores = {
    'SECRET_KEY': get_random_secret_key(),
    'DEBUG': 'True',
    'DEMO_PASSWORD': os.environ['CLAVE_DEMO'],
    'API_PASSWORD': os.environ['CLAVE_API'],
}
if modo == 'sqlite':
    valores['DB_ENGINE'] = 'django.db.backends.sqlite3'
else:
    valores.update({'DB_ENGINE': 'django.db.backends.mysql', 'DB_NAME': 'sgr', 'DB_USER': 'sgr_app',
                    'DB_PASSWORD': os.environ['CLAVE_BD'], 'DB_HOST': '127.0.0.1', 'DB_PORT': '3306'})

ruta = pathlib.Path('.env')
texto = ruta.read_text(encoding='utf-8')
for clave, valor in valores.items():
    entre_comillas = clave in ('SECRET_KEY', 'DB_PASSWORD', 'DEMO_PASSWORD', 'API_PASSWORD')
    linea = f"{clave}='{valor}'" if entre_comillas else f'{clave}={valor}'
    if re.search(rf'(?m)^{clave}=', texto):
        texto = re.sub(rf'(?m)^{clave}=.*$', lambda m: linea, texto)
    else:
        texto += f'\n{linea}\n'
ruta.write_text(texto, encoding='utf-8')
print('Listo: .env escrito en modo', modo)
PY
unset MODO CLAVE_BD CLAVE_DEMO CLAVE_API
```
Revisa que quedó bien (este comando no muestra ninguna clave):
```bash
grep -E '^(DEBUG|DB_ENGINE|DB_NAME|DB_USER|DB_HOST|DB_PORT)=' .env
```
- Modo A: debe mostrar `DB_ENGINE=django.db.backends.mysql`, `DB_NAME=sgr`, `DB_USER=sgr_app`, `DB_HOST=127.0.0.1` y `DB_PORT=3306`.
- Modo B: debe mostrar `DB_ENGINE=django.db.backends.sqlite3`. Las líneas `DB_NAME`, `DB_USER`, `DB_HOST` y `DB_PORT` que vengan del ejemplo también aparecerán, pero con SQLite no se usan.

Si prefieres editarlo a mano: `notepad .env`. Las claves con símbolos (`#`, `$`…) van **entre comillas simples**, por ejemplo `DB_PASSWORD='TuClaveBD#2026'`.

---

## 5. Tablas y datos

```bash
python manage.py check
python manage.py migrate
python manage.py flush --noinput
python manage.py seed_data --volumen 1000
```
- `check` debe responder `System check identified no issues (0 silenced).`
- `flush` vacía la base por si tenía datos antiguos (si es nueva, no hace daño).
- `seed_data --volumen 1000` carga datos de demostración: **más de 3.000 registros** repartidos en los 6 modelos de la API, y los 3 usuarios `api_*`. Al final imprime el conteo de cada modelo. Demora unos segundos o un par de minutos.

---

## 6. Levantar el servidor

```bash
python manage.py runserver
```
- Sitio: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/ (usuario `admin_sgr`)
- API: http://127.0.0.1:8000/api/

Deja esta ventana abierta mientras pruebas. Para detener el servidor: `Ctrl+C`.

---

## 7. Verificar la API desde la terminal (antes de abrir Apidog)

En **otra ventana** de Git Bash:
```bash
cd ~/Proyecto_Integrado_SGR
source .venv/Scripts/activate
SGR_CLAVE_API='Api#Local-2026' python scripts/probar_api.py
```
Al final debe decir **`48/48 casos con el estado esperado`**. Usa aquí tu `API_PASSWORD`.

Si vas a repetirlo varias veces en la misma ventana: `export SGR_CLAVE_API='Api#Local-2026'` una vez, y después solo `python scripts/probar_api.py`.

---

## 8. Apidog

### 8.1 Antes de empezar
1. **El servidor debe estar corriendo** (sección 6) en una ventana de Git Bash, con el entorno activado. No la cierres mientras pruebas.
2. **La base debe tener datos de prueba** (sección 5). Eso crea `api_admin`, `api_operador` y `api_sin_rol`.
3. **Ten a mano la clave de la API:** el valor de `API_PASSWORD` en tu `.env`.

### 8.2 Instalar Apidog
Descarga la versión de **escritorio** desde https://apidog.com/download/, instálala e inicia sesión (puede ser con Google). Crea un proyecto nuevo, por ejemplo **SGR**, de tipo HTTP.

> Usa la versión de escritorio. La versión web no puede llegar a `127.0.0.1` sin instalar un agente aparte.

### 8.3 Importar la colección
1. Dentro del proyecto, abre **Importar Datos** (en Configuración del proyecto, o con el botón **+** del panel izquierdo).
2. En «Importar datos de API», elige **Postman**.
3. Arrastra o selecciona el archivo:
   ```
   C:\Users\<tu usuario>\Proyecto_Integrado_SGR\docs\api\SGR_API_JWT.postman_collection.json
   ```
   (Si clonaste en otra carpeta, por ejemplo el Escritorio, usa esa ruta; en Git Bash, `pwd -W` dentro del proyecto te la muestra.) Si el explorador no muestra la carpeta `docs`, pega la ruta de `...\Proyecto_Integrado_SGR\docs\api` en su barra de direcciones y presiona Enter.
4. Se abre **Previsualización de importación y configuración**. A la izquierda deben aparecer marcadas las carpetas 01 a 13; déjalas todas marcadas. A la derecha, configura así:

   | Opción | Qué elegir |
   | --- | --- |
   | **Importar en** | **Crear nuevo módulo**. Es obligatoria; si no la eliges, aparece «Por favor seleccione al menos una opción» |
   | **Carpeta destino (Datos de prueba)** | **Carpeta raíz** |
   | **Formatear nombres de variables no admitidos** | Activada |
   | **Eliminar "{{baseUrl}}" de la URL** | **Activada**. Las rutas quedan como `/api/...` y la dirección del servidor pasa al entorno |
   | **Modificar de forma sincronizada la Base URL del módulo… en los entornos** | **Activada**. Debe mostrar `http://127.0.0.1:8000` en los entornos desarrollo, prueba y producción |
   | **Importar "por ejemplo" en Postman como casos de depuración** | Activada. No afecta |
   | **Cómo actuar cuando ya existe el mismo recurso** | Déjala como está. Solo importa si vuelves a importar la colección |

5. Presiona **Confirmar**. En el panel izquierdo debe aparecer el módulo **SGR · API REST con JWT (Evaluación 3)** con las carpetas **01. JWT** a **13. Limpieza**.

### 8.4 Configurar el entorno
Gracias a la importación, la dirección del servidor ya quedó configurada. Solo falta agregar la clave.

1. Arriba a la derecha, haz clic en el selector de entorno y entra a la gestión de entornos. Abre **Entorno desarrollo**.
2. **Servicios (URL Base):**
   - La fila **SGR · API REST con JWT (Evaluación 3)** ya debe tener `http://127.0.0.1:8000`. No la cambies.
   - La fila **Módulo predeterminado** trae un ejemplo (`https://dev.your-api-server.com`, con un triángulo naranja) que la colección no usa. Puedes dejarla así; si quieres quitar el aviso, cámbiala también a `http://127.0.0.1:8000`.
3. **Variables:** haz clic en **Agregar una nueva variable** y completa:

   | Variable | Valor compartido | Valor local |
   | --- | --- | --- |
   | `clave_api` | *(vacío)* | tu `API_PASSWORD` (ej. `Api#Local-2026`) |

   Pon la clave en **Valor local**. Ese valor queda solo en tu computador; el **valor compartido**, en cambio, se sincroniza con la nube de Apidog y lo ve cualquiera con quien compartas el proyecto. Al enviar las peticiones, Apidog usa el valor local.
4. Guarda con **Guardar** o con `Ctrl+S` y cierra la ventana.
5. Arriba a la derecha, deja seleccionado **Entorno desarrollo**. Si cambias de entorno, las peticiones no encuentran la clave ni el servidor.

**Prueba rápida:** abre **01. JWT → Token api_admin** y presiona **Send**. Debe responder **200** con un `access` y un `refresh`. Si responde 401, la variable `clave_api` no quedó bien guardada o no coincide con tu `.env`.

#### Variables que se llenan solas
Los scripts de cada petición (pestaña **Post Processors**, o **Tests** en Postman) guardan valores para las peticiones siguientes:

| Variable | La llena | La usan |
| --- | --- | --- |
| `access_admin`, `access_operador`, `access_sin_rol` | 01. JWT | todas las peticiones con token |
| `refresh_access_admin` | 01. JWT → Token api_admin | 01. Renovar access |
| `employee_id`, `period_id`, `activity_type_id`, `tipo_social_id`, `delegation_id`, `responsable_id`, `otra_delegacion_id` | 05. Referencias | 06 a 11 |
| `actividad_id`, `atencion_id`, `compromiso_id`, `evidencia_id`, `actividad_social_id` | el «crear» de cada CRUD | detalle, modificar y eliminar |

Por eso **el orden importa**: si ejecutas «Actividad: detalle» sin haber ejecutado antes «Actividad: crear», la variable `actividad_id` estará vacía y la petición fallará.

### 8.5 Ejecutar las carpetas en orden
Abre cada petición, presiona **Send** y comprueba el código de estado que aparece junto a la respuesta. Recorre las carpetas de arriba hacia abajo.

| Carpeta | Qué prueba | Resultado esperado |
| --- | --- | --- |
| **01. JWT** | Obtiene los tokens de los 3 usuarios, renueva el access y prueba una clave incorrecta | 200, 200, 200, 200, **401** |
| **02. Sin token** | GET de los 6 recursos sin cabecera `Authorization` | **401** en las 6 |
| **03. Operador** | `api_operador` lee los 6 recursos e intenta crear un compromiso | 200 ×6, **403** al crear |
| **04. Sin rol API** | `api_sin_rol` intenta leer los 6 recursos | **403** en las 6 |
| **05. Referencias** | Busca ids reales de la base (funcionario, período abierto, tipos, delegaciones) | 200 en las 4 |
| **06. CRUD Actividad** | Crear → detalle → PATCH → eliminar → comprobar que no figura | 201, 200, 200, 204, **404** |
| **07. CRUD Atención social** | Crea una actividad social de apoyo y luego aplica el CRUD a su atención | 201, 201, 200, 200, 204, **404** |
| **08. CRUD Compromiso** | Crear (vence en 15 días) → detalle → PATCH `in_progress` → eliminar → comprobar | 201, 200, 200, 204, **404** |
| **09. CRUD Evidencia** | Sube un archivo y lo gestiona (ver nota abajo) | 201, 200, 200, 204, **404** |
| **10. Operacionales** | Lista y detalle de validaciones y seguimientos (solo lectura) | 200 en las 4 |
| **11. Errores** | Título demasiado corto, responsable de otra delegación, id inexistente | **400**, **400**, **404** |
| **12. Paginación** | Página 1 (20 resultados) y página 2 (ids distintos) | 200, 200 |
| **13. Limpieza** | Borra la actividad social creada en la 07 | 204 |

Los códigos 401, 403, 400 y 404 en negrita **son el resultado correcto** de esas pruebas: demuestran que la API protege, valida y responde bien.

Las eliminaciones son **borrado lógico**: el registro queda en la base, pero la API deja de mostrarlo. Por eso el GET posterior da 404.

#### Nota para «09. CRUD Evidencia → Evidencia: crear»
Antes de enviar esta petición:
1. Abre la pestaña **Body**; el tipo es `form-data`.
2. En la fila `file`, haz clic en **Upload** o **Select File** y elige un **JPG, PNG o PDF de hasta 2 MB**.
3. Presiona **Send**.

Si no adjuntas archivo, responde 400 y las 4 peticiones siguientes de la carpeta también fallan.

#### Ejecutar todo de una vez (opcional)
En **Tests → Test Scenarios → New**, agrega las peticiones en el mismo orden (01 a 13) con **Add Step → Import from API**, elige el entorno **Entorno desarrollo** y presiona **Run**. La petición de evidencia necesita su archivo adjunto también dentro del escenario.

### 8.6 Capturas para el informe
- Toma la captura cuando se vean el **código de estado** y el cuerpo de la respuesta.
- **No deben aparecer el token ni la clave.** Antes de capturar, oculta la pestaña **Headers** de la petición (donde va `Authorization: Bearer ...`), la ventana del entorno (donde está `clave_api`) y la respuesta de las peticiones de la carpeta 01, que traen `access` y `refresh`.
- En la 01, conviene capturar solo el código 200 y recortar el cuerpo, o mostrar la prueba «Clave incorrecta (401)».

---

## 9. Cada vez que vuelvas a trabajar

Funciona igual en los dos modos:
```bash
cd ~/Proyecto_Integrado_SGR
source .venv/Scripts/activate
git pull
python manage.py migrate
python manage.py runserver
```
Si usas MariaDB, comprueba antes que el servicio esté iniciado (Windows: «Servicios» → **MariaDB**).

### Cambiar de MariaDB a SQLite (o al revés)
1. Vuelve a ejecutar la sección 4 con el otro modo (`export MODO=sqlite` o `export MODO=mariadb`).
2. Carga los datos en la base nueva:
   ```bash
   python manage.py migrate
   python manage.py flush --noinput
   python manage.py seed_data --volumen 1000
   ```
3. Reinicia el servidor.

### Empezar de cero con SQLite
Detén el servidor y borra el archivo de la base, luego repite la sección 5:
```bash
rm db.sqlite3
```

### Pruebas automáticas (opcional)
```bash
python manage.py test api     # las 27 pruebas de la API
python manage.py test         # todas las pruebas (varios minutos)
```
En modo A necesitan el permiso sobre `test_sgr` de la sección 3; en modo B no hace falta nada más.

---

## 10. Si algo falla

### Instalación y servidor
| Mensaje | Solución |
| --- | --- |
| `bash: .venvScriptsactivate.ps1: command not found` | Estás en Git Bash usando el comando de PowerShell. Usa `source .venv/Scripts/activate` |
| `'python' no se reconoce` o abre la Microsoft Store | Reinstala Python marcando «Add python.exe to PATH», o usa `py -3.12` en vez de `python` |
| Falla la instalación de `mysqlclient` | Con SQLite, usa la instalación sin ese paquete (sección 2). Con MariaDB, revisa que Python sea la versión 3.12 de 64 bits |
| `No matching distribution found for Django==6.1.1` | Python es anterior a la 3.12 (Django 6.1 lo exige). Instala Python 3.12 (sección 1), borra la carpeta `.venv` con `rm -rf .venv` y repite la sección 2 |
| `ModuleNotFoundError: No module named 'django'` | El entorno no está activado, o no se instalaron las dependencias: `source .venv/Scripts/activate` y `pip install -r requirements.txt` |
| `Falta SECRET_KEY en el .env` | El `.env` no existe o no tiene la clave, o el comando se ejecutó fuera de la carpeta del proyecto. Repite la sección 4 |
| La página no carga (`ERR_CONNECTION_REFUSED`) | El servidor no está corriendo: `python manage.py runserver` en otra ventana |

### MariaDB (modo A)
| Mensaje | Solución |
| --- | --- |
| Git Bash se queda en blanco tras `mariadb -u ... -p` | Falta `winpty` al inicio del comando: `winpty mariadb -u root -p` |
| `Access denied for user 'sgr_app'` | La clave de `DB_PASSWORD` en el `.env` no coincide con la del `ALTER USER` de la sección 3. Repite el `ALTER USER` o la sección 4 |
| `Can't connect to server on '127.0.0.1'` | MariaDB está detenido. Abre «Servicios» e inicia **MariaDB** |
| `Can't create database 'sgr'; database exists` o `CREATE USER failed` | Ya existían de una instalación anterior; ignora el aviso y sigue: el `ALTER USER` fija la clave |
| Error al crear `test_sgr` al correr las pruebas | Falta el `GRANT ... ON test_sgr.*` de la sección 3 |

### SQLite (modo B)
| Mensaje | Solución |
| --- | --- |
| `no such table` | Falta `python manage.py migrate` |
| Los datos no aparecen después de cambiar de modo | La base nueva está vacía: `migrate`, `flush --noinput` y `seed_data --volumen 1000` (sección 9) |
| `database is locked` | Hay dos servidores usando el mismo archivo: cierra el otro `runserver` |

### Datos y API
| Mensaje | Solución |
| --- | --- |
| El token da 401 con la clave correcta | Los usuarios de la API se crearon con otra clave: `python manage.py flush --noinput` y luego `python manage.py seed_data --volumen 1000` |
| `probar_api.py` dice «No se pudo obtener el token» | Falta `seed_data`, o `SGR_CLAVE_API` no es la `API_PASSWORD` de tu `.env` |
| `«20 por página» falla` en la carpeta 12 | La base tiene pocas actividades: `python manage.py seed_data --volumen 1000` |

### Apidog
| Síntoma | Causa probable | Solución |
| --- | --- | --- |
| `Could not connect` / `ECONNREFUSED` | El servidor no está corriendo, o estás en Apidog web | Ejecuta `python manage.py runserver` y usa Apidog de escritorio |
| La petición va a `https://dev.your-api-server.com` o sin servidor | No está seleccionado **Entorno desarrollo**, o la petición quedó en el «Módulo predeterminado» | Selecciona **Entorno desarrollo** arriba a la derecha. Si aun así falla, cambia también la URL del «Módulo predeterminado» a `http://127.0.0.1:8000` (8.4) |
| En una prueba que espera 401, 403, 400 o 404 aparece en rojo «El código de estado HTTP debería ser 200» | Es la **Validación de Respuesta** de Apidog, que compara contra la respuesta «Éxito (200)» creada al importar. No es la prueba de la colección | No es un error. Lo que vale es **Resultados de aserción** (ej. «Estado 401 ✅»). Para quitar el aviso, desactiva el interruptor **Validación** del panel de respuesta |
| «Por favor seleccione al menos una opción» al importar | Falta elegir dónde importar | En **Importar en**, marca **Crear nuevo módulo** |
| 401 en «Token api_admin» | `clave_api` vacía o distinta de `API_PASSWORD`, o guardada en otro entorno | Revisa el **Valor local** de `clave_api` en **Entorno desarrollo** y que ese entorno esté seleccionado. Si la clave es correcta, recrea los usuarios (ver «Datos y API») |
| 401 en las carpetas 03 a 13 | El token no se guardó o expiró (dura 30 minutos) | Vuelve a ejecutar la carpeta **01**. Si sigue fallando, abre el panel de variables y revisa que `access_admin` tenga un valor `eyJ...` |
| Las variables `access_*` siguen vacías después de la 01 | Apidog no convirtió el script de Postman | Abre «Token api_admin» → **Post Processors**. Debe haber un script con `pm.collectionVariables.set('access_admin', ...)`; si no está, agrégalo con **Add Post Processor → Custom Script**. Como alternativa, copia el `access` de la respuesta y pégalo a mano en la variable `access_admin` del entorno |
| 400 en «Actividad: crear» o en «Compromiso: crear» | No se ejecutó la carpeta 05 y faltan los ids | Ejecuta **05. Referencias** y repite |
| 404 en «detalle» justo después de crear | El «crear» falló, así que el id quedó vacío o es antiguo | Revisa que el «crear» haya dado 201 |
| 400 en «Evidencia: crear» | Falta el archivo, pesa más de 2 MB o no es JPG, PNG o PDF | Adjunta un archivo válido en la fila `file` |
