# database.py
# Manejo de conexión a PostgreSQL con psycopg2.
# Usamos un pool simple para no abrir una conexión nueva
# en cada request — patrón mínimo sin ORM.

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
import os
from contextlib import contextmanager
from dotenv import load_dotenv

# Debes llamar a la función para que lea el archivo .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:secret@localhost:5432/heladeria_punto")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:secret@localhost:5432/heladeria_punto")

# Pool de 2 a 10 conexiones — suficiente para un kiosco
connection_pool = pool.SimpleConnectionPool(
    minconn=2,
    maxconn=10,
    dsn=DATABASE_URL
)


@contextmanager ### Garantiza que la conexión se devuelva al pool incluso si hay un error (línea 33 con conn.rollback()).
###Evita fugas de memoria, algo vital para un proyecto de e-commerce que reciba múltiples peticiones.
def get_conn():
    """
    Context manager que toma una conexión del pool,ss
    la devuelve al terminar y hace rollback si hay error.
    Uso: with get_conn() as conn: ...
    """
    conn = connection_pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        connection_pool.putconn(conn)


@contextmanager
def get_cursor():
    """
    Context manager que devuelve un cursor con RealDictCursor
    para obtener resultados como diccionarios en vez de tuplas.
    Uso: with get_cursor() as cur: cur.execute(...)
    """
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            yield cur