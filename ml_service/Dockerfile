# Archivo: Dockerfile
FROM python:3.10-slim

# Evitar que Python escriba archivos .pyc y forzar logs sin buffer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Definir la ruta interna de la caché de Hugging Face para que la API sepa dónde buscar
ENV HF_HOME=/app/.cache/huggingface

WORKDIR /app

# 1. Copiar e instalar dependencias primero (Aprovecha la caché si no cambias el requirements)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Copiar el script de descarga y ejecutarlo
# Esto "hornea" el modelo de 500MB en esta capa de la imagen Docker
COPY download_model.py .
RUN python download_model.py

# 3. Copiar todo el código fuente y los artefactos locales (.pkl y .keras)
COPY . .

# Exponer el puerto de Uvicorn
EXPOSE 8000

# Arrancar el servidor
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]