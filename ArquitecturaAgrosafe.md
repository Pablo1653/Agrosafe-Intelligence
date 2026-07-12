# AgroSafe Intelligence — Documento de Arquitectura

> **Documento vivo.** Se actualiza a medida que el proyecto crece. Última revisión: apps `core`, `companies`, `contacts`, `interactions`, `scraping`. Pendientes de documentar cuando existan: `compliance`, `documents`, `intelligence`.

---

# PARTE 1 — Cómo funciona Django (fundamentos)

Django es un framework web en Python que sigue el patrón **MVT** (Model-View-Template), una variante de MVC. La idea central: separar **datos** (Model), **lógica** (View) y **presentación** (Template) para que cada capa se pueda cambiar sin romper las otras.

## 1.1 El patrón MVT

| Capa | Rol | Dónde vive en AgroSafe |
|---|---|---|
| **Model** | Define la estructura de los datos y habla con la base de datos | `apps/<app>/models.py` |
| **View** | Recibe el request, ejecuta la lógica, decide qué datos mostrar | `apps/<app>/views.py` |
| **Template** | HTML con mini-lenguaje de plantillas, solo presentación | `apps/<app>/templates/` y `templates/` (global) |

A diferencia de MVC clásico, en Django la "View" no es la pantalla (eso es el Template) — la View es el controlador. Esto confunde a quien viene de otros frameworks, tenelo presente.

## 1.2 Ciclo de vida de un request

Cuando alguien entra a una URL, esto es lo que pasa, en orden:

1. **`urls.py`** (raíz del proyecto, `agrosafe/urls.py`) recibe la URL y busca qué patrón coincide.
2. Si el patrón usa `include()`, delega a un `urls.py` de una app específica (ej. `apps/companies/urls.py`).
3. Django encuentra la **view** asociada a ese patrón y le pasa el `request` (más cualquier parámetro capturado en la URL, como un UUID).
4. La view ejecuta lógica: valida datos, consulta la base vía el ORM, arma un `context` (diccionario de datos).
5. La view llama a `render(request, "template.html", context)`, que combina el HTML del template con los datos del context.
6. El HTML final se devuelve como `HttpResponse` al navegador.

Todo esto pasa por **middleware** antes y después (definido en `settings.py` → `MIDDLEWARE`): capas que interceptan cada request/response para tareas transversales (seguridad, sesiones, CSRF, mensajes, etc.).

## 1.3 Proyecto vs Apps

- **Proyecto** (`agrosafe/`): la configuración global. Un solo proyecto por sitio. Contiene `settings.py`, el `urls.py` raíz, `wsgi.py`/`asgi.py` (puntos de entrada para servidores de producción).
- **App** (`apps/companies/`, `apps/contacts/`, etc.): un módulo autocontenido que resuelve **una responsabilidad de negocio**. Un proyecto Django se arma combinando varias apps. La idea es que cada app se pueda razonar, testear y (idealmente) reutilizar por separado.

Cada app tiene su propio `models.py`, `views.py`, `urls.py`, `forms.py`, `admin.py`, `migrations/`, `templates/<nombre_app>/`.

## 1.4 Modelos y el ORM

Un modelo es una clase Python que hereda de `models.Model`. Cada atributo de clase es un campo de la tabla:

```python
class Company(models.Model):
    business_name = models.CharField(max_length=255, unique=True)
    email = models.EmailField(blank=True)
```

Django traduce esto a SQL automáticamente (esto es el **ORM** — Object-Relational Mapper). Nunca escribís SQL a mano salvo casos muy específicos.

**Tipos de campo comunes que usa el proyecto:**
- `CharField` — texto corto, requiere `max_length`.
- `TextField` — texto largo, sin límite.
- `EmailField` / `URLField` — como `CharField` pero valida formato.
- `UUIDField` — identificador único de 128 bits, usado para IDs públicos.
- `BooleanField` — verdadero/falso.
- `DateTimeField` / `DateField` — fecha y hora / solo fecha.
- `ForeignKey` — relación muchos-a-uno (ej. un `Contact` pertenece a una `Company`).
- `JSONField` — guarda un diccionario/lista tal cual, sin tabla propia (usado en `RawCompany.raw_data`).

**Opciones de campo clave:**
- `blank=True` → el campo puede quedar vacío en un **formulario**.
- `null=True` → el campo puede ser `NULL` en la **base de datos**. Son cosas distintas: `blank` es validación de formulario, `null` es esquema de base de datos. Regla general: en campos de texto usá solo `blank=True` (nunca `null=True`, para no tener dos formas de "vacío": `""` y `NULL`); en `ForeignKey`/`DateField` sí tiene sentido `null=True`.
- `db_index=True` → crea un índice en la base para acelerar búsquedas por ese campo.
- `unique=True` → no puede haber dos filas con el mismo valor.
- `related_name` → el nombre que usás para navegar la relación "hacia atrás" (ej. `company.contacts.all()` gracias a `related_name="contacts"` en `Contact.company`).
- `on_delete` → qué hacer si se borra el registro relacionado. `CASCADE` (borra en cadena), `SET_NULL` (deja el campo en null), `PROTECT` (impide el borrado).

**Métodos que se repiten en todos los modelos del proyecto:**
- `class Meta:` → configuración que no es un campo: orden por default (`ordering`), nombres para el admin (`verbose_name`), índices compuestos, constraints.
- `__str__(self)` → cómo se representa el objeto como texto (aparece en el admin, en el shell, en logs).

## 1.5 Migraciones

Las migraciones son el historial versionado de cambios al esquema de la base de datos. Viven en `apps/<app>/migrations/000X_descripcion.py`. Flujo:

```bash
python manage.py makemigrations   # Django compara tus modelos actuales contra el
                                    # último estado migrado y genera el archivo de cambios
python manage.py migrate          # Aplica esos cambios a la base de datos real
```

**Nunca se edita una migración ya aplicada en producción.** Si necesitás corregir algo, generás una migración nueva. Cada migración es un paso incremental — por eso en el historial del proyecto vas a ver cosas como `0002_company_email.py`, `0003_company_phone.py`: cada una agregó un campo en un momento distinto.

Caso particular que ya vivimos: agregar un campo `unique=True` con un `default` dinámico (como `uuid.uuid4`) a un modelo que ya tiene filas — Django te pregunta cómo proceder porque necesita generar un valor único por fila existente, no puede usar el mismo default para todas. Por eso apareció el prompt de "Select an option" al agregar `interaction_uuid`.

## 1.6 URLs y routing

Cada patrón de URL mapea una ruta a una view:

```python
path("<uuid:company_uuid>/editar/", views.company_update, name="company_update")
```

- `<uuid:company_uuid>` — captura un UUID de la URL y lo pasa como argumento `company_uuid` a la view. Los conversores comunes son `str`, `int`, `uuid`, `slug`.
- `name="company_update"` — nombre interno de la URL, usado en templates (`{% url 'companies:company_update' company_uuid=x %}`) y en `redirect()`, para no hardcodear rutas.
- `app_name = "companies"` (definido arriba en el archivo) — crea un namespace, así `companies:company_update` no choca con una URL de otra app que se llame igual.

El `urls.py` raíz del proyecto (`agrosafe/urls.py`) usa `include()` para delegar cada prefijo de ruta a una app:

```python
path("companies/", include("apps.companies.urls"))
```

## 1.7 Views

Una view es una función (o clase) que recibe `request` y devuelve una respuesta. El proyecto usa **function-based views** (no class-based) en todos lados — es una decisión de estilo válida, más explícita y fácil de leer para un equipo chico, a costa de repetir un poco de boilerplate (el patrón GET/POST se repite en cada view de creación/edición).

Patrón que se repite en casi todas las views del proyecto:

```python
def algo_create(request):
    if request.method == "POST":
        form = AlgoForm(request.POST)
        if form.is_valid():
            obj = form.save()
            messages.success(request, "...")
            return redirect(...)
    else:
        form = AlgoForm()
    return render(request, "template.html", {"form": form})
```

Esto es el patrón **Post/Redirect/Get**: si el POST fue exitoso, redirigís (para que un F5 del navegador no reenvíe el formulario). Si es GET, o el POST falló validación, volvés a mostrar el formulario.

`get_object_or_404(Model, campo=valor)` — trae un objeto o corta con un 404 automáticamente, evita el `try/except` manual.

## 1.8 Forms

Un `ModelForm` genera automáticamente los campos de un formulario a partir de un modelo:

```python
class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ["business_name", "email", ...]
```

Ventajas: la validación (tipos, `max_length`, `unique`, formato de email/URL) se hereda del modelo sin repetir código. `widgets` permite customizar cómo se renderiza cada campo (clases CSS, placeholders) sin tocar el modelo.

`form.is_valid()` corre todas las validaciones. `form.save()` crea/actualiza el objeto en la base. `form.save(commit=False)` arma el objeto en memoria sin guardarlo — útil cuando necesitás completar un campo antes de guardar (ej. `interaction.company = company` antes del `.save()` en `interaction_create`).

## 1.9 Templates

El lenguaje de templates de Django no es Python — es intencionalmente limitado (sin lógica compleja) para separar presentación de lógica de negocio.

- `{{ variable }}` — imprime un valor.
- `{% tag %}` — lógica de control: `{% if %}`, `{% for %}`, `{% url %}`, `{% csrf_token %}`.
- `{% extends "base.html" %}` + `{% block nombre %}...{% endblock %}` — herencia de templates. `base.html` define la estructura común (navbar, sidebar, CSS/JS), y cada página hija sobreescribe bloques específicos (`{% block content %}`).
- `{% load static %}` + `{% static 'ruta' %}` — referencia archivos estáticos (CSS/JS/imágenes) con la URL correcta según configuración.
- `{% csrf_token %}` — **obligatorio en todo `<form method="post">`**. Genera un token oculto que Django valida en el servidor para prevenir ataques CSRF (que un sitio malicioso mande un POST a tu app usando la sesión del usuario sin que se entere).

## 1.10 Admin

Django trae un panel de administración generado automáticamente a partir de tus modelos, accesible en `/admin/`. Para activarlo por modelo:

```python
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = (...)   # columnas en el listado
    search_fields = (...)  # activa la barra de búsqueda
    list_filter = (...)    # filtros laterales
```

Es una herramienta de gestión rápida para el dueño del proyecto (o staff), no reemplaza la interfaz de usuario final que construís con views/templates propios.

## 1.11 Settings

`agrosafe/settings.py` es la configuración central: qué apps están instaladas (`INSTALLED_APPS`), qué middleware corre (`MIDDLEWARE`), cómo conectarse a la base (`DATABASES`), dónde buscar templates (`TEMPLATES`), etc. En este proyecto, los secretos (contraseña de base, API keys) no están hardcodeados acá — se leen de variables de entorno vía `django-environ`, desde un archivo `.env` que **no** se sube al repositorio (está en `.gitignore`).

---

# PARTE 2 — Arquitectura general de AgroSafe Intelligence

## 2.1 Qué es el proyecto

Un CRM (Customer Relationship Management) hecho a medida para gestionar la cartera comercial de Pablo como asesor en seguridad, higiene y gestión ambiental en el agro. Django 6.0, PostgreSQL, sin frontend framework (HTML server-rendered con Bootstrap 5).

## 2.2 Estructura de carpetas

```
AgroSafe_Intelligence/
│
├── agrosafe/              # Configuración global del proyecto
│   ├── settings.py
│   ├── urls.py             # Root URLconf, incluye las urls de cada app
│   ├── wsgi.py / asgi.py   # Puntos de entrada para servidores
│
├── apps/                   # Todas las apps de negocio viven acá adentro
│   │                        # (no en la raíz — decisión de organización:
│   │                        #  agrupa todo lo "de negocio" en un solo paquete)
│   ├── core/                # Dashboard / home
│   ├── companies/           # Entidad central: empresas
│   ├── contacts/            # Personas dentro de una empresa
│   ├── interactions/        # Historial de actividad comercial
│   └── scraping/            # Pipeline de importación externa
│
├── templates/               # Templates globales (base.html, partials compartidos)
├── static/                  # CSS/imágenes propios del proyecto
├── requirements.txt
└── manage.py
```

Cada app en `apps/<nombre>/` sigue esta forma interna (cuando aplica):

```
apps/<nombre>/
├── models.py       # Esquema de datos
├── forms.py         # Formularios (ModelForm normalmente)
├── views.py          # Lógica de request/response
├── urls.py            # Rutas de esta app
├── admin.py            # Registro en el panel /admin/
├── services.py          # Lógica de negocio que NO es CRUD simple
├── migrations/            # Historial de cambios de esquema
├── templates/<nombre>/    # Templates propios de esta app
└── tests.py                # (hoy vacío en todas las apps — ver Parte 4)
```

## 2.3 Patrones de diseño que ya están instalados en el proyecto

Estos son los criterios que **deberías replicar** cuando armes una app nueva (`compliance`, `documents`, `intelligence`), para mantener consistencia:

### a) UUID público, PK privada
Todo modelo que se expone en una URL (`Company`, `Contact`, `Interaction`) tiene un campo `xxx_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)`, y las URLs usan ese UUID (`<uuid:company_uuid>`), nunca la PK numérica autoincremental. Esto evita exponer cuántos registros tenés o permitir que alguien recorra `/1/`, `/2/`, `/3/...` adivinando IDs.

### b) Soft-delete con `is_active`
Nada se borra físicamente salvo que sea puramente un log de actividad (`Interaction` sí se borra de verdad — está documentado en el propio código por qué). Todo lo demás usa `is_active = models.BooleanField(default=True)` + vistas `xxx_deactivate` / `xxx_activate` que cambian el flag en vez de hacer `DELETE`. Las listas filtran `is_active=True` por default, con un query param (`?mostrar_inactivas=1`) para verlas igual.

### c) Capa de `services.py` para lógica de negocio no trivial
Cuando una operación es más que "guardar el form", se saca de la view y va a `services.py`:
- `contacts/services.py::set_primary_contact()` — reglas de negocio sobre el contacto principal.
- `scraping/services.py::clean_raw_company / validate_raw_company / promote_raw_company` — el pipeline completo de limpieza y promoción.

Esto mantiene las views delgadas (reciben el request, arman el form, delegan la regla de negocio) y hace la lógica testeable sin tener que simular un request HTTP.

### d) Staging pipeline para datos externos (`scraping`)
Ningún dato que viene de afuera (CSV, Excel, Google Places) toca `Company` directamente. Primero aterriza en `RawCompany` (una tabla "sucia"), pasa por limpieza y validación automática, y solo un click humano lo "promueve" a `Company`. Esto es el patrón a replicar para cualquier fuente de datos externa futura.

### e) `created_by` + `created_at`/`updated_at` en (casi) todo
Todos los modelos de negocio tienen estos tres campos de auditoría. Hoy `created_by` siempre queda en `None` porque no hay login — el día que se active autenticación, ya está todo el esquema listo para asignarlo (`request.user`), no hace falta migrar nada.

## 2.4 Stack tecnológico

| Pieza | Qué es | Versión |
|---|---|---|
| Django | Framework web | 6.0.6 (recomendado actualizar a 6.0.7) |
| PostgreSQL | Base de datos | vía `psycopg` 3 |
| django-environ | Variables de entorno / `.env` | 0.14.0 |
| Bootstrap 5 | CSS framework (vía CDN, no paquete Python) | 5.3.3 |
| openpyxl | Lectura de archivos `.xlsx` | 3.1.5 |
| requests | Cliente HTTP (para la API de Google Places) | 2.34.2 |

## 2.5 Flujo de datos entre apps (cómo se relacionan)

```
                     ┌─────────────┐
   CSV/Excel ───────▶│             │
                      │  scraping   │──promote──▶┌───────────┐
   Google Places ────▶│ RawCompany  │            │           │
                      └─────────────┘            │ companies │
                                                   │  Company  │◀────┐
                                                   └───────────┘     │
                                                       │  ▲          │
                                                       │  │FK        │FK
                                                       ▼  │          │
                                              ┌──────────────┐  ┌──────────┐
                                              │ interactions │  │ contacts │
                                              │ Interaction  │  │ Contact  │
                                              └──────────────┘  └──────────┘
                                                       │
                                                       ▼
                                              ┌──────────────┐
                                              │     core     │
                                              │  (dashboard, │
                                              │  lee de todas)│
                                              └──────────────┘
```

`Company` es el nodo central. `Contact` e `Interaction` cuelgan de ella por `ForeignKey`. `scraping` alimenta a `Company` desde afuera. `core` no tiene modelo propio (su `models.py` está vacío) — solo lee de las demás apps para armar el dashboard.

---

# PARTE 3 — Cada app en detalle

## 3.1 `core`

**Responsabilidad:** Dashboard de inicio. No tiene modelo propio.

**Archivos relevantes:**
- `views.py::home()` — arma 5 bloques de información para la página de inicio:
  1. `pending_followups` — de todas las interacciones, agarra solo la **más reciente por empresa** (usando un diccionario `latest_by_company` keyed por `company_id`, sobrescribiendo a medida que itera en orden ascendente de fecha — así el último valor que queda por cada key es el más reciente) y filtra las que tienen `follow_up_date` vencido o de hoy.
  2. `companies_never_contacted` — empresas activas sin ninguna interacción cargada (`interactions__isnull=True`, un filtro que atraviesa la relación inversa).
  3. `scraping_counts` — cuántos `RawCompany` están en `NEEDS_REVIEW` y `PENDING`, para avisar si hay cola de revisión pendiente.
  4. `recent_interactions` — las últimas 8 interacciones registradas, sin importar la empresa.
  5. `total_active_companies` — contador simple.

**Punto técnico interesante:** el cálculo de `pending_followups` es O(n) en Python (itera todas las interacciones una vez), no una query SQL agregada. Funciona bien con el volumen actual; si la tabla `Interaction` crece mucho, se podría reemplazar por una subquery con `Window functions` de Django (`Window(expression=FirstValue(...), ...)`) — no es necesario hoy, pero es el próximo paso natural cuando el dashboard empiece a sentirse lento.

**URLs:** una sola, la raíz (`""`) → `home`. No tiene `app_name`, así que su URL se referencia como `{% url 'home' %}` sin namespace (a diferencia de todas las demás apps).

## 3.2 `companies` — la entidad central

**Modelo `Company`:**

| Campo | Tipo | Notas |
|---|---|---|
| `business_name` | CharField, unique | Razón social |
| `company_uuid` | UUIDField, unique | ID público |
| `trade_name` | CharField, blank | Nombre comercial |
| `cuit` | CharField, unique, null=True | Puede no tener CUIT todavía |
| `website`, `email`, `phone` | — | Datos de contacto de la empresa (a nivel organización, no de una persona) |
| `industry`, `city` | CharField | Segmentación |
| `status` | CharField + choices | `PROSPECT / QUALIFIED / CLIENT / INACTIVE` — ciclo de vida comercial |
| `is_active` | BooleanField | Soft-delete |
| `created_by` | FK a User | Auditoría (hoy siempre None, sin login) |

**Índices:** `status`, `industry`, `city` — los tres campos por los que más se filtra en el listado.

**Views (`views.py`):** CRUD completo con el patrón estándar (ver 2.3-a y 2.3-b): `company_list`, `company_detail`, `company_create`, `company_update`, `company_deactivate`, `company_activate`. Todas usan `company_uuid` en vez de PK.

**`forms.py`:** `CompanyForm` expone explícitamente solo los campos editables por el usuario (nunca `company_uuid`, `created_at`, etc. — esos se manejan fuera del form, por diseño).

**`services.py`:** hoy está **vacío**. Es el candidato natural para mover ahí, en el futuro, lógica como "calcular el score de una empresa" o "detectar duplicados al crear" si crece más allá de un CRUD simple.

**Por qué es "la entidad central":** todas las demás apps de negocio (`contacts`, `interactions`, `scraping`) tienen un `ForeignKey` hacia `Company`, directa o indirectamente (vía `promoted_company` en `RawCompany`). Cualquier app nueva que agregues (`compliance`, `documents`, `intelligence`) casi seguro también va a colgar de `Company`.

## 3.3 `contacts` — personas dentro de una empresa

**Modelo `Contact`:**

Igual esqueleto que `Company` (UUID público, soft-delete, auditoría) más:
- `company` — `ForeignKey(Company, related_name="contacts")`. Por esto podés hacer `company.contacts.all()`.
- `first_name`, `last_name`, `position`, `email`, `phone`, `mobile`, `linkedin`, `notes`.
- `is_primary` — booleano con una regla de negocio importante: **solo puede haber un contacto principal por empresa**, garantizado a nivel de base de datos con:
  ```python
  constraints = [
      models.UniqueConstraint(
          fields=["company"],
          condition=models.Q(is_primary=True),
          name="unique_primary_contact_per_company",
      )
  ]
  ```
  Esto es un **índice único parcial** (`UNIQUE ... WHERE is_primary = true` en SQL) — Postgres solo aplica la restricción de unicidad a las filas donde `is_primary` es `True`. Es la forma correcta de modelar "a lo sumo uno de estos" sin usar un campo separado en `Company`.

**`services.py::set_primary_contact(contact)`** — la función que resuelve la regla de negocio que la constraint por sí sola no puede resolver: antes de marcar un contacto como principal, desmarca a cualquier otro que ya lo fuera para esa empresa, todo dentro de una transacción (`transaction.atomic()`) para que sea una operación atómica (o se hacen los dos cambios, o ninguno — no puede quedar un estado intermedio inconsistente si algo falla a mitad de camino).

**Ordering:** `["company__business_name", "last_name", "first_name"]` — nota el `__` (doble guión bajo): es la sintaxis del ORM para atravesar una relación (`company__business_name` = "el `business_name` de la `company` relacionada"). Así el listado queda agrupado por empresa alfabéticamente.

**`views.py`:** mismo patrón CRUD que `companies`, con la particularidad de que `contact_create` y `contact_update` llaman a `set_primary_contact()` después de `form.save()` cuando corresponde (ver Parte 4, fue el primer bug que corregimos).

## 3.4 `interactions` — historial de actividad comercial

**Modelo `Interaction`:** registra un contacto puntual con una empresa (llamada, email, reunión, WhatsApp, visita).

| Campo | Notas |
|---|---|
| `interaction_uuid` | UUID público (agregado — antes usaba `pk` en las URLs) |
| `company` | FK obligatoria |
| `contact_name` | **Texto libre**, no FK a `Contact` — ver nota abajo |
| `interaction_type` | choices: CALL/EMAIL/MEETING/WHATSAPP/VISIT/OTHER |
| `date` | Cuándo pasó |
| `outcome` | choices: POSITIVE/NEUTRAL/NEGATIVE/NO_RESPONSE |
| `follow_up_date` | Si hay que hacer seguimiento, cuándo (alimenta el dashboard) |

**Deuda técnica documentada en el propio código:** el docstring del modelo dice literalmente que `contact_name` es un campo temporal "hasta que exista la app `contacts`". Esa app **ya existe**, pero `Interaction` todavía no la usa — sigue guardando el nombre como texto libre en vez de un `ForeignKey(Contact, null=True, blank=True)`. Es la próxima mejora natural de esta app: cuando cargues una interacción, poder elegir un `Contact` real de la empresa (con autocomplete) en vez de tipear el nombre de nuevo cada vez, evitando "Juan Pérez" vs "Juan Perez" vs "J. Pérez" como si fueran tres personas distintas.

**`views.py`:**
- `interaction_list` — todas las interacciones, con un filtro `?filtro=pendientes` que muestra solo las que tienen seguimiento vencido.
- `interaction_create(request, company_uuid)` — se accede desde el detalle de una empresa puntual, no desde un menú genérico (la URL exige `company_uuid`).
- `interaction_update` / `interaction_delete` — ahora usan `interaction_uuid` (corregido, ver Parte 4).
- **Único borrado físico real del sistema:** `interaction_delete` hace `.delete()` de verdad, no soft-delete. La razón está documentada en el propio código: una interacción es un registro de actividad puntual, no una entidad de negocio que valga la pena conservar inactiva (a diferencia de una `Company` o un `Contact`, que podés necesitar reactivar).

## 3.5 `scraping` — pipeline de importación externa

La app más elaborada del proyecto. Resuelve un problema concreto: traer datos de afuera (Google Maps, un CSV que te pasó alguien, LinkedIn a futuro) sin ensuciar la tabla `Company` con datos a medio validar.

### Modelo `RawCompany` — la "sala de espera"

Espeja los campos editables de `Company` (`business_name`, `cuit`, `email`, `phone`, etc.) más:
- `source` — de dónde vino (`GOOGLE_MAPS`, `CSV_IMPORT`, `MANUAL`, etc.)
- `raw_data` — `JSONField` con el payload **crudo** tal cual llegó, sin procesar. Es el respaldo para auditoría/debug: si la limpieza automática rompió algo, siempre podés volver a mirar el dato original.
- `status` — máquina de estados: `PENDING → NEEDS_REVIEW / PROMOTED / REJECTED`.
- `promoted_company` — FK a la `Company` que terminó generando, una vez promovida.

### `sources/google_places.py` — el conector externo

Envuelve la API "Text Search (New)" de Google Places. Puntos a destacar:
- Usa un `FIELD_MASK` explícito, pidiendo solo los campos que se van a usar — Google cobra por campo solicitado, así que esto es directamente ahorro de dinero, no solo prolijidad.
- Excepción propia `GooglePlacesError` — cualquier falla (sin conexión, key inválida, error HTTP) se homogeneiza en un solo tipo de error, para que la view lo capture con un único `except` y muestre un mensaje claro, sin que un error crudo de `requests` llegue a romper la página.
- `_extract_city()` — Google no devuelve "ciudad" como campo directo, hay que buscarlo dentro de `addressComponents` filtrando por `type == "locality"`. Es el tipo de detalle de integración que, si no está comentado en el código (y acá lo está), alguien pierde una hora reconstruyendo por qué está ese loop.

### `services.py` — el corazón de la app, en 4 funciones puras

1. **`clean_raw_company(raw)`** — normaliza formato (espacios, mayúsculas de dominio de email, formato de CUIT `XX-XXXXXXXX-X`, agrega `https://` al sitio si falta). No decide validez, solo prolijidad.
2. **`validate_raw_company(raw)`** — decide el `status`:
   - Sin nombre ni CUIT → `REJECTED` (no hay nada rescatable).
   - CUIT con longitud inválida, o email con formato inválido → `NEEDS_REVIEW` (Pablo tiene que mirarlo a mano).
   - Coincide por CUIT o nombre con una `Company` que ya existe → `NEEDS_REVIEW` (posible duplicado).
   - Si pasó todos los filtros → `PENDING`, listo para promover con un click.
3. **`promote_raw_company(raw, user)`** — convierte el `RawCompany` en `Company` real. Si ya existe una empresa parecida, **completa los campos vacíos de la existente en vez de crear un duplicado** — nunca pisa un dato que ya estaba cargado. Si no existe, crea una `Company` nueva. En ambos casos, marca el `RawCompany` como `PROMOTED` y guarda la referencia.
4. **`reject_raw_company(raw, reason)`** — descarte manual desde la cola de revisión.

### `views.py` — tres formas de alimentar el pipeline

- **`import_view`** — sube un CSV o `.xlsx`. Usa un diccionario `HEADER_ALIASES` para aceptar nombres de columna en español o inglés indistintamente (`"razon_social"` o `"business_name"` funcionan igual) — así no le exigís al usuario un formato exacto de archivo. Cada fila se convierte en un `RawCompany` y se le corre `clean_raw_company` + `validate_raw_company` automáticamente al toque.
- **`google_maps_search_view`** — arma un `textQuery` combinando lo que escribe el usuario con la ciudad ("acopio de granos" + "Rosario" → "acopio de granos en Rosario, Argentina") y llama a `search_google_places`.
- **`raw_company_list`** — la cola de revisión, con contador por estado y filtro por `status`.
- **`raw_company_edit`** — corrige un registro a mano y vuelve a correr la validación (para que pueda salir de `NEEDS_REVIEW` si la corrección resolvió el problema).
- **`raw_company_promote` / `raw_company_reject`** — las dos acciones finales de la cola de revisión. Ambas soportan un parámetro `next` en el POST para volver a la misma pantalla desde la que se llamó (con chequeo de que `next_url` empiece con `/`, evitando que alguien te mande a redirigir a un sitio externo).

**Por qué esta arquitectura importa para el futuro:** si el día de mañana agregás una fuente nueva (scraping de LinkedIn, un formulario público de "dejanos tus datos", una integración con otro CRM), el patrón a seguir es siempre el mismo: la fuente nueva solo sabe crear `RawCompany`, nunca toca `Company` directamente. Toda la lógica de "¿esto es válido? ¿es un duplicado?" queda centralizada en `scraping/services.py`, sin importar de dónde vino el dato.

---

# PARTE 4 — Historial de decisiones y fixes aplicados

Registro de lo que ya se corrigió, para no perder el porqué con el tiempo:

| Fecha | App | Qué se corrigió | Por qué |
|---|---|---|---|
| — | `contacts` | `set_primary_contact()` en `services.py` | La `UniqueConstraint` de `is_primary` explotaba con `IntegrityError` si se marcaba un segundo contacto principal sin desmarcar antes al anterior |
| — | `contacts` | Indentación de `contact_create` | Un bug de indentación dejaba `if contact.is_primary` fuera del `if form.is_valid()`, causando `UnboundLocalError` con formularios inválidos y mensaje de éxito condicionado por error |
| — | `contacts` | `return redirect(...)` faltante en `contact_update` | Después de guardar, la vista no redirigía al detalle, solo volvía a mostrar el form |
| — | `interactions` | Import muerto `from ast import Delete` | Resto de un autocompletado, sin uso |
| — | `interactions` | `interaction_uuid` + migración de datos existentes | URLs pasaron de `<int:pk>` a `<uuid:interaction_uuid>`, alineado con el resto del sistema. Se actualizó modelo, migración, `urls.py`, `views.py` y el template `company_detail.html` (tenía dos links con `interaction.pk` colgados que rompían con `NoReverseMatch`) |
| — | `scraping` | Campo `phone` agregado a `RawCompanyEditForm` | El modelo y el import de CSV ya manejaban `phone`, pero no se podía editar desde la cola de revisión |
| — | `contacts` | `Contact` registrado en `admin.py` | Antes solo `Company` e `Interaction` estaban en el panel `/admin/` |

## Pendientes conocidos (no bloqueantes, quedan para cuando corresponda)

- **Autenticación:** deliberadamente sin implementar — uso local, un solo usuario, decisión consciente de Pablo. Si algún día se expone la app en una red no confiable, revisar esto primero.
- **Tests:** los 5 `tests.py` están vacíos (boilerplate default de `startapp`). Cuando el proyecto crezca, priorizar tests sobre `scraping/services.py` (es la lógica más compleja y con más ramas de decisión) y sobre `set_primary_contact()`.
- **`Interaction.contact_name` vs FK a `Contact`:** documentado en 3.4, es la mejora arquitectónica más clara pendiente.
- **`requirements.txt` con BOM UTF-8:** puede volver a aparecer si se regenera desde PowerShell sin cuidar el encoding.
- **`companies/services.py` vacío:** candidato a app que va a necesitar lógica de negocio propia (scoring, detección de duplicados) más adelante.

---

## Cómo mantener este documento

Cada vez que agreguemos una app nueva o hagamos un cambio de arquitectura importante:
1. Sumar la app a la Parte 3, siguiendo el mismo formato (modelo, views, services, particularidades).
2. Actualizar el diagrama de flujo de datos (2.5) si la app nueva se conecta con las existentes.
3. Agregar una fila a la tabla de historial (Parte 4) si corregimos algo.

Así este archivo queda como la referencia técnica real del proyecto, no un documento que se desactualiza a la semana.
