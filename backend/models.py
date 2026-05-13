# models.py
# Define la forma de los datos que entran y salen de la API.
# Separamos Input (lo que recibe) de Output (lo que devuelve)
# para tener control explícito sobre qué exponemos.

from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


# ── SABOR ──────────────────────────────────────────
class SaborOut(BaseModel):
    id:        int
    nombre:    str
    categoria: str
    sin_tacc:  bool
    vegano:    bool
    alergenos: list[str]


# ── PRODUCTO ───────────────────────────────────────
class ProductoOut(BaseModel):
    id:          int
    nombre:      str
    sabores_max: int
    precio:      float


# ── PEDIDO ─────────────────────────────────────────
class SaborElegido(BaseModel):
    id:     int
    nombre: str


class PedidoIn(BaseModel):
    producto_id:      int
    sabores_elegidos: list[SaborElegido]

    # Validación mínima en entrada — la regla de negocio
    # (máximo por producto) se valida en el router con datos de la BD
    @field_validator("sabores_elegidos")
    @classmethod
    def no_vacio(cls, v):
        if len(v) == 0:
            raise ValueError("Debés elegir al menos un sabor")
        return v


class PedidoOut(BaseModel):
    id:               int
    producto_id:      int
    sabores_elegidos: list[SaborElegido]
    total:            float
    estado:           str
    created_at:       datetime


# ── IA ─────────────────────────────────────────────
class IAQuery(BaseModel):
    query: str


class IAResponse(BaseModel):
    answer:  str
    context: list[str]  # chunks recuperados — necesarios para métricas RAG