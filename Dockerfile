FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos solo lo necesario para el runtime, no tests ni venv
COPY backend/ ./backend/
COPY ia/ ./ia/

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
