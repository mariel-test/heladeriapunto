# Frío & Punto — Kiosco de autoservicio

Sistema de kiosco para una heladería ficticia. Sirve como base para practicar **API testing con pytest**, **UI testing con Playwright** y **IA/RAG testing con RAGAS y DeepEval**.

---

## Cómo levantar

```bash
docker-compose up --build
```

| Servicio   | URL                        |
|------------|----------------------------|
| Backend    | http://localhost:8000      |
| Docs (Swagger) | http://localhost:8000/docs |
| Frontend   | http://localhost:3000      |
| ChromaDB   | http://localhost:8001      |
| Ollama     | http://localhost:11434     |

Conexión DBeaver (verificar datos):
- Host: `localhost` · Port: `5432` · Database: `heladeria` · User: `admin` · Password: `secret`

---

## Cómo correr los tests

```bash
# Todos los tests (requiere stack levantado)
docker-compose run tests

# Solo API
docker-compose run tests pytest tests/api/ -v

# Solo UI
docker-compose run tests pytest tests/ui/ -v

# Solo IA
docker-compose run tests pytest tests/ia/ -v

# Con reporte Allure
docker-compose run tests pytest tests/ -v --alluredir=tests/reports/allure-results
allure serve tests/reports/allure-results
```

---

## Métricas que se miden

| Capa | Herramienta | Métrica | Umbral |
|------|-------------|---------|--------|
| API  | pytest + requests | cobertura de endpoints y reglas de negocio | 100% casos definidos |
| UI   | Playwright  | flujo completo sin errores | — |
| IA   | RAGAS       | Faithfulness | ≥ 0.80 |
| IA   | RAGAS       | Answer Relevancy | ≥ 0.75 |
| IA   | DeepEval    | HallucinationMetric (preguntas trampa) | ≤ 0.50 |

---

## Reporte de APIs — scope de automatización

**Total de endpoints:** 8 rutas · **Total de casos de prueba:** 26 · **Archivos de test:** 3

### `GET /sabores` — 8 casos

| # | Tipo | Escenario | Qué verifica |
|---|------|-----------|--------------|
| 1 | ✅ Happy | Sin filtros | 200 · retorna exactamente 10 items |
| 2 | ✅ Happy | `?categoria=crema` | Solo items con `categoria == "crema"` |
| 3 | ✅ Happy | `?categoria=agua` | Solo items con `categoria == "agua"` |
| 4 | ✅ Happy | `?sin_tacc=true` | Solo items donde `sin_tacc == true` |
| 5 | ✅ Happy | `?sin_tacc=false` | Solo items donde `sin_tacc == false` |
| 6 | ✅ Happy | `?categoria=agua&sin_tacc=true` | Intersección de ambos filtros |
| 7 | 🔍 Estructura | Sin filtros | Response tiene `id, nombre, categoria, sin_tacc, vegano, alergenos` |
| 8 | ❌ Negativo | `?categoria=medialuna` | 200 con lista vacía (no error) |

### `GET /productos` — 2 casos

| # | Tipo | Escenario | Qué verifica |
|---|------|-----------|--------------|
| 9 | ✅ Happy | Sin params | 200 · exactamente 5 productos |
| 10 | 🔍 Estructura | Sin params | Cada item tiene `sabores_max` (int) y `precio` (float) |

### `GET /productos/{id}` — 3 casos

| # | Tipo | Escenario | Qué verifica |
|---|------|-----------|--------------|
| 11 | ✅ Happy | ID existente (`1`) | 200 · devuelve el producto correcto |
| 12 | ❌ Negativo | ID inexistente (`9999`) | 404 |
| 13 | ❌ Negativo | ID tipo string (`/productos/abc`) | 422 |

### `POST /pedido` — 12 casos

| # | Tipo | Escenario | Qué verifica |
|---|------|-----------|--------------|
| 14 | ✅ Happy | Pedido válido (producto_id=5, 4 sabores) | 201 · response tiene `id`, `total`, `estado` |
| 15 | 🔍 Negocio | Happy path | `total` == precio del producto (calculado por backend) |
| 16 | 🔍 Negocio | Happy path | `estado` inicial == `"pendiente"` |
| 17 | 🔍 Negocio | Pote 1/4kg con 1 sabor | Acepta: `sabores_max=1` con 1 sabor enviado |
| 18 | ❌ Negativo | `producto_id` inexistente | 404 |
| 19 | ❌ Negativo | Más sabores que `sabores_max` | 422 con mensaje que incluye el límite |
| 20 | ❌ Negativo | `sabor_id` inexistente | 422 con los IDs inválidos en el mensaje |
| 21 | ❌ Negativo | `sabores_elegidos: []` (lista vacía) | 422 — validado por Pydantic |
| 22 | ❌ Negativo | Body sin `producto_id` | 422 |
| 23 | ❌ Negativo | Body no es JSON válido | 422 |

### `GET /pedido/{id}` — 3 casos

| # | Tipo | Escenario | Qué verifica |
|---|------|-----------|--------------|
| 24 | ✅ Happy | ID de pedido creado en test anterior | 200 · `sabores_elegidos` es lista con `id` y `nombre` |
| 25 | ❌ Negativo | ID inexistente (`9999`) | 404 |
| 26 | 🔍 Negocio | Persistencia en BD (BUG-004) | POST crea pedido · GET devuelve `producto_id`, `total`, `estado="pendiente"` y `sabores_elegidos` exactos |

### `POST /ia/ask` — fuera de scope (paso 8)

El endpoint devuelve 503 (stub) hasta que el módulo IA esté construido. Los tests viven en `tests/ia/`.

### Distribución en archivos

| Archivo | Casos |
|---------|-------|
| `tests/api/test_sabores.py` | 8 |
| `tests/api/test_productos.py` | 5 |
| `tests/api/test_pedidos.py` | 13 |
| **Total** | **26** |

---

## Defectos conocidos

| ID | Componente | Descripción | Severidad | Estado |
|----|-----------|-------------|-----------|--------|
| BUG-001 | `frontend/index.html` + `style.css` | Badge de alérgeno mostraba el texto solapado con el nombre del sabor en tarjetas con nombre largo. **Fix:** etiqueta mantenida como "Sin TACC" y ajuste de CSS (font-size, padding, line-height) para que entre dentro del cuadro sin superposición. Detectado en TC-INT02 y TC-INT05. | Minor | ✅ Cerrado en `dev` |
| BUG-002 | `frontend/index.html` | Checkbox de filtro mostraba la etiqueta incorrecta. **Estado final:** etiqueta correcta es **"Filtrar sin TACC"** (muestra sabores aptos para celíacos, es decir, los que no contienen TACC). Detectado en TC-INT03. | Minor | ✅ Cerrado en `dev` |
| BUG-003 | `frontend/style.css` | En la pantalla "¿Qué tamaño?" al hacer hover sobre las tarjetas superiores el header las cubría. Causa: `.grid-productos` tiene `overflow-y: auto` que genera un scroll container y recorta el `transform: translateY(-3px)` del hover en las tarjetas de la fila superior. **Pendiente de corrección por desarrollador frontend.** Este defecto fue identificado por el equipo de QA (automatización); la corrección requiere intervención de un desarrollador frontend ya que implica modificar estilos CSS de layout. **TC-INT03: NO PASS** por este defecto. | Minor | 🔴 Abierto |
| BUG-004 | `backend/` · `DATABASE_URL` | Los pedidos no se persistían en la base de datos. **Causa raíz — dos problemas encadenados:** (1) el nombre de la base de datos en `DATABASE_URL` no coincidía con el nombre real de la BD (`heladeria` vs el nombre con el que fue creada); (2) la contraseña del usuario `admin` había sido reseteada al recrear el contenedor de PostgreSQL, dejando la conexión del backend inválida. Ambos problemas hacían que el backend fallara silenciosamente al intentar persistir el pedido. **Síntoma:** la UI mostraba el mensaje "✓ Pedido confirmado" pero el registro no existía en BD y `GET /pedido/{id}` devolvía 404. **Fix:** corregido `DATABASE_URL` en `.env` (nombre de BD y contraseña correctos). Adicionalmente, TC-E2E01 fue reforzado para verificar persistencia real via `GET /pedido/{id}` y se añadió TC-PD13 (TC-26) en la suite API. | Major | ✅ Cerrado en `dev` |

---

## Estructura del proyecto

```
heladeriapunto/
├── backend/
│   ├── main.py
│   ├── models.py
│   ├── database.py
│   ├── routers/
│   │   ├── sabores.py
│   │   ├── productos.py
│   │   ├── pedidos.py
│   │   └── ia.py
│   └── data/
│       └── seed.sql
├── frontend/
│   ├── index.html
│   └── style.css
├── ia/
│   ├── rag_pipeline.py
│   ├── ingest.py
│   └── knowledge_base/
│       └── heladeria_faq.json
├── tests/
│   ├── conftest.py
│   ├── api/
│   │   ├── test_sabores.py
│   │   ├── test_productos.py
│   │   └── test_pedidos.py
│   ├── ui/
│   │   └── test_flujo_kiosco.py
│   └── ia/
│       ├── test_hallucination.py
│       └── test_rag_metrics.py
├── docker-compose.yml
├── Dockerfile
└── .env
```
