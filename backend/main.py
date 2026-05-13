# main.py
# Punto de entrada de FastAPI.
# CORS habilitado para el frontend en puerto 3000 (nginx del docker-compose).

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import sabores, productos, pedidos, ia

app = FastAPI(title="Frío & Punto — API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sabores.router)
app.include_router(productos.router)
app.include_router(pedidos.router)
app.include_router(ia.router)
