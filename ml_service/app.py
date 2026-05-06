import os
import contextlib
import joblib
import numpy as np
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Suprimir warnings de TensorFlow en producción
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

from tensorflow import keras
from transformers import AutoTokenizer, TFAutoModel

# 1. Anclaje de rutas absolutas (Nunca confíes en el directorio de trabajo)
BASE_DIR = Path(__file__).resolve().parent
# Para producción, el modelo BETO debería estar descargado físicamente en esta carpeta
# Si no está, la librería lo descargará, pero DEBES pre-descargarlo en tu Dockerfile.
BETO_MODEL_PATH = "dccuchile/bert-base-spanish-wwm-uncased" 

ml_models = {}

MODEL_NAME = "nn_urgency_multiclass"
MODEL_VERSION = "2.0.0"

# 2. Validación Estricta: Si no es una de estas, FastAPI devuelve error 422 automáticamente
class PredictInput(BaseModel):
    description: str = Field(min_length=1, max_length=300)
    categoria: Literal[
        "movilidad", 
        "limpieza", 
        "alumbrado_publico", 
        "parques_y_jardines", 
        "mobiliario_urbano", 
        "otros"
    ]

class PredictOutput(BaseModel):
    urgency_predicha: int = Field(ge=1, le=5)
    confianza: float
    category: str
    model_name: str
    model_version: str


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # Cargar BETO
        ml_models["tokenizer"] = AutoTokenizer.from_pretrained(BETO_MODEL_PATH)
        ml_models["beto"] = TFAutoModel.from_pretrained(BETO_MODEL_PATH)
        
        # 3. Cargar artefactos usando rutas absolutas seguras
        ml_models["scaler"] = joblib.load(BASE_DIR / "scaler.pkl")
        ml_models["ohe"] = joblib.load(BASE_DIR / "ohe_categoria.pkl")
        ml_models["nn_model"] = keras.models.load_model(BASE_DIR / "modelo_urgencias.keras")
        
        yield
    except Exception as e:
        raise RuntimeError(f"Fallo crítico al cargar los artefactos del modelo: {str(e)}")
    finally:
        ml_models.clear()

app = FastAPI(title="CiudadIA ML Service", lifespan=lifespan)

def map_categoria(categoria: str) -> str:
    mapping = {
        "movilidad": "Movilidad",
        "limpieza": "Limpieza",
        "alumbrado_publico": "Alumbrado Público",
        "parques_y_jardines": "Parques y Jardines",
        "mobiliario_urbano": "Mobiliario Urbano",
        "otros": "Otros",
    }
    return mapping.get(categoria.strip().lower(), categoria)

@app.get("/health")
def health():
    if not ml_models:
        raise HTTPException(status_code=503, detail="Modelos no cargados en memoria.")
    return {"status": "ok", "message": "API de inferencia lista y artefactos cargados."}

@app.post("/predict", response_model=PredictOutput)
def predict(payload: PredictInput):
    if not ml_models:
        raise HTTPException(status_code=503, detail="Servicio no disponible.")

    # Preprocesamiento de la Categoría
    cat_mapeada = map_categoria(payload.categoria)
    cat_array = np.array([[cat_mapeada]])
    cat_encoded = ml_models["ohe"].transform(cat_array)

    # Extracción de Embeddings (BETO con TensorFlow)
    inputs = ml_models["tokenizer"](
        [payload.description],
        truncation=True,
        max_length=128,
        padding='max_length',
        return_tensors='tf'
    )
    
    outputs = ml_models["beto"](**inputs)
    text_embedding = outputs.last_hidden_state[:, 0, :].numpy()

    # Fusión y Escalado
    X_new = np.hstack((text_embedding, cat_encoded))
    X_new_scaled = ml_models["scaler"].transform(X_new)

    # 4. Latencia Optimizada: Usar __call__ en lugar de .predict()
    pred_probs = ml_models["nn_model"](X_new_scaled, training=False).numpy()[0]
    pred_class = int(np.argmax(pred_probs))
    urgencia_final = pred_class + 1 
    confianza = float(pred_probs[pred_class])

    # Filtro de seguridad
    palabras_criticas = ['bomba', 'terrorista', 'asesinato', 'fuego', 'incendio', 'muerto', 'atropello', 'explosión', 'explosion', 'herido', 'violencia', 'secuestro']
    if any(palabra in payload.description.lower() for palabra in palabras_criticas):
        urgencia_final = 5
        confianza = 1.0

    return PredictOutput(
        urgency_predicha=urgencia_final,
        confianza=confianza,
        category=cat_mapeada,
        model_name=MODEL_NAME,
        model_version=MODEL_VERSION
    )