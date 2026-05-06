from pathlib import Path

import nltk
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from nltk.corpus import stopwords
from pydantic import BaseModel, Field
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from tensorflow import keras
from tensorflow.keras import layers, models
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.regularizers import l2


class PredictInput(BaseModel):
    description: str = Field(min_length=1, max_length=300)
    categoria: str = Field(min_length=1, max_length=60)


class PredictOutput(BaseModel):
    urgency: int = Field(ge=1, le=5)
    category: str
    model_name: str
    model_version: str


DATA_PATH = Path(__file__).resolve().parents[1] / "ML" / "incidencias.csv"
MODEL_NAME = "nn_urgency"
MODEL_VERSION = "1.0.0"

app = FastAPI(title="CiudadIA ML Service")

_tfidf: TfidfVectorizer | None = None
_expected_cat_cols: list[str] | None = None
_scaler: StandardScaler | None = None
_model: keras.Model | None = None


def _ensure_stopwords() -> list[str]:
    try:
        nltk.data.find("corpora/stopwords")
    except LookupError:
        nltk.download("stopwords")
    return list(stopwords.words("spanish"))


def _train_model() -> None:
    global _tfidf, _expected_cat_cols, _scaler, _model

    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset no encontrado en {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    if "description" not in df.columns or "categoria" not in df.columns or "urgencia" not in df.columns:
        raise ValueError("El dataset no contiene las columnas requeridas.")

    df = df.dropna(subset=["description", "categoria", "urgencia"]).copy()

    X_text = df["description"].astype(str)
    X_cat = df[["categoria"]].copy()
    y = df["urgencia"].astype(float)

    stop_words_spanish = _ensure_stopwords()
    tfidf = TfidfVectorizer(max_features=1000, stop_words=stop_words_spanish, ngram_range=(1, 2))
    X_text_tfidf = tfidf.fit_transform(X_text).toarray()

    X_cat_encoded_df = pd.get_dummies(X_cat, columns=["categoria"], drop_first=True)
    expected_cat_cols = list(X_cat_encoded_df.columns)
    X_cat_encoded = X_cat_encoded_df.values

    X = np.hstack((X_text_tfidf, X_cat_encoded))
    X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2, random_state=42)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    y_train_normalized = (y_train - 1.0) / 4.0

    nn_model = models.Sequential(
        [
            layers.Dense(
                256,
                activation="relu",
                input_shape=(X_train_scaled.shape[1],),
                kernel_regularizer=l2(0.001),
            ),
            layers.Dropout(0.2),
            layers.Dense(128, activation="relu", kernel_regularizer=l2(0.001)),
            layers.Dropout(0.2),
            layers.Dense(64, activation="relu", kernel_regularizer=l2(0.001)),
            layers.Dropout(0.2),
            layers.Dense(32, activation="relu", kernel_regularizer=l2(0.001)),
            layers.Dropout(0.2),
            layers.Dense(1, activation="sigmoid"),
        ]
    )

    nn_model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss="mse",
        metrics=["mae"],
    )

    early_stop = EarlyStopping(monitor="val_loss", patience=15, restore_best_weights=True, verbose=0)
    nn_model.fit(
        X_train_scaled,
        y_train_normalized,
        epochs=150,
        batch_size=32,
        validation_split=0.2,
        callbacks=[early_stop],
        verbose=0,
    )

    _tfidf = tfidf
    _expected_cat_cols = expected_cat_cols
    _scaler = scaler
    _model = nn_model


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
    if _model is None or _tfidf is None or _expected_cat_cols is None or _scaler is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    description = payload.description
    categoria = payload.categoria
    categoria_modelo = _map_categoria_for_model(categoria)

    text_tf = _tfidf.transform([description]).toarray()

    cat_df = pd.DataFrame({"categoria": [categoria_modelo]})
    cat_encoded_full = pd.get_dummies(cat_df, columns=["categoria"], drop_first=True)
    cat_encoded = cat_encoded_full.reindex(columns=_expected_cat_cols, fill_value=0).values

    X_new = np.hstack((text_tf, cat_encoded))
    X_new_scaled = _scaler.transform(X_new)

    pred_norm = float(_model.predict(X_new_scaled, verbose=0)[0][0])
    pred_float = (pred_norm * 4.0) + 1.0
    pred_clipped = float(np.clip(pred_float, 1.0, 5.0))
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
