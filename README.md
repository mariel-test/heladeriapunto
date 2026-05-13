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

**Total de endpoints:** 8 rutas · **Total de casos de prueba:** 25 · **Archivos de test:** 3

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

### `GET /pedido/{id}` — 2 casos

| # | Tipo | Escenario | Qué verifica |
|---|------|-----------|--------------|
| 24 | ✅ Happy | ID de pedido creado en test anterior | 200 · `sabores_elegidos` es lista con `id` y `nombre` |
| 25 | ❌ Negativo | ID inexistente (`9999`) | 404 |

### `POST /ia/ask` — fuera de scope (paso 8)

El endpoint devuelve 503 (stub) hasta que el módulo IA esté construido. Los tests viven en `tests/ia/`.

### Distribución en archivos

| Archivo | Casos |
|---------|-------|
| `tests/api/test_sabores.py` | 8 |
| `tests/api/test_productos.py` | 5 |
| `tests/api/test_pedidos.py` | 12 |
| **Total** | **25** |

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
