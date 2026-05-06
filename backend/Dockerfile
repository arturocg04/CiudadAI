# Dockerfile mínimo para ejecutar la plantilla en un contenedor.
# Ejemplo: sirve la API con Uvicorn usando la app ubicada en `src.app:app`.

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY scripts ./scripts
RUN python scripts/download_nltk.py

COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]