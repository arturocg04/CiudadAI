from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_extraction.text import TfidfVectorizer


class PredictInput(BaseModel):
    description: str = Field(min_length=1, max_length=300)
    categoria: str = Field(min_length=1, max_length=60)


class PredictOutput(BaseModel):
    urgency: int = Field(ge=1, le=5)
    category: str
    model_name: str
    model_version: str


DATA_PATH = Path(__file__).resolve().parents[1] / "ML" / "incidencias.csv"
MODEL_NAME = "random_forest_urgency"
MODEL_VERSION = "1.0.0"

app = FastAPI(title="CiudadIA ML Service")

_tfidf: TfidfVectorizer | None = None
_expected_cat_cols: list[str] | None = None
_model: RandomForestRegressor | None = None


def _train_model() -> None:
    global _tfidf, _expected_cat_cols, _model

    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset no encontrado en {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    if "description" not in df.columns or "categoria" not in df.columns or "urgencia" not in df.columns:
        raise ValueError("El dataset no contiene las columnas requeridas.")

    df["description"] = df["description"].fillna("")
    df["categoria"] = df["categoria"].fillna("")

    tfidf = TfidfVectorizer(max_features=1000, stop_words="english", ngram_range=(1, 2))
    X_text = tfidf.fit_transform(df["description"]).toarray()

    X_cat_encoded_df = pd.get_dummies(df[["categoria"]], columns=["categoria"], drop_first=True)
    expected_cat_cols = list(X_cat_encoded_df.columns)
    X_cat = X_cat_encoded_df.values

    X = np.hstack((X_text, X_cat))
    y = df["urgencia"].astype(float).values

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)

    _tfidf = tfidf
    _expected_cat_cols = expected_cat_cols
    _model = model


@app.on_event("startup")
def load_model() -> None:
    _train_model()


@app.get("/health")
def health() -> dict:
    if _model is None:
        return {"status": "error", "detail": "model_not_loaded"}
    return {"status": "ok"}


@app.post("/predict", response_model=PredictOutput)
def predict(payload: PredictInput) -> PredictOutput:
    if _model is None or _tfidf is None or _expected_cat_cols is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    description = payload.description
    categoria = payload.categoria
    categoria_modelo = _map_categoria_for_model(categoria)

    text_tf = _tfidf.transform([description]).toarray()

    cat_df = pd.DataFrame({"categoria": [categoria_modelo]})
    cat_encoded_full = pd.get_dummies(cat_df, columns=["categoria"], drop_first=True)
    cat_encoded = cat_encoded_full.reindex(columns=_expected_cat_cols, fill_value=0).values

    X_new = np.hstack((text_tf, cat_encoded))

    pred_raw = float(_model.predict(X_new)[0])
    pred_clipped = float(np.clip(pred_raw, 1.0, 5.0))
    urgency = int(round(pred_clipped))

    return PredictOutput(
        urgency=urgency,
        category=categoria,
        model_name=MODEL_NAME,
        model_version=MODEL_VERSION,
    )


def _map_categoria_for_model(categoria: str) -> str:
    mapping = {
        "movilidad": "Movilidad",
        "limpieza": "Limpieza",
        "alumbrado_publico": "Alumbrado Público",
        "parques_y_jardines": "Parques y Jardines",
        "mobiliario_urbano": "Mobiliario Urbano",
        "otros": "Otros",
    }
    key = categoria.strip().lower()
    return mapping.get(key, categoria)
