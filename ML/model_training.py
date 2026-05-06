"""Training script for the CiudadIA urgency model.

This script is the notebook-to-script version of the training workflow.
It loads the dataset, builds BETO embeddings with TensorFlow, encodes the
category with OneHotEncoder, trains the neural network, evaluates it, and
exports immutable artifacts for inference.
"""

from __future__ import annotations

import argparse
import os
import warnings
from dataclasses import dataclass
from pathlib import Path

import joblib
import nltk
import numpy as np
import pandas as pd
import tensorflow as tf
from imblearn.over_sampling import SMOTE
from nltk.corpus import stopwords
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    mean_absolute_error,
    precision_recall_fscore_support,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.utils.class_weight import compute_class_weight
from tensorflow import keras
from tensorflow.keras import layers, models
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.regularizers import l2
from transformers import AutoTokenizer, TFAutoModel


warnings.filterwarnings("ignore")
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_USE_LEGACY_KERAS"] = "1"


MODEL_NAME = "dccuchile/bert-base-spanish-wwm-uncased"
RANDOM_STATE = 42
MAX_LENGTH = 128
BATCH_SIZE = 8


@dataclass(frozen=True)
class Artifacts:
    scaler: StandardScaler
    encoder: OneHotEncoder
    model: keras.Model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the CiudadIA urgency model.")
    parser.add_argument(
        "--data-path",
        type=Path,
        default=Path(__file__).resolve().parent / "incidencias.csv",
        help="Path to the training CSV file.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Directory where artifacts will be written.",
    )
    return parser.parse_args()


def ensure_nltk_resources() -> None:
    try:
        nltk.data.find("corpora/stopwords")
    except LookupError:
        nltk.download("stopwords")


def load_dataset(data_path: Path) -> pd.DataFrame:
    df = pd.read_csv(data_path)
    df = df.dropna(subset=["description", "categoria", "urgencia"])
    return df


def load_beto_model() -> tuple[AutoTokenizer, tf.keras.Model]:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = TFAutoModel.from_pretrained(MODEL_NAME)
    return tokenizer, model


def build_embeddings(
    texts: list[str], tokenizer: AutoTokenizer, beto_model: tf.keras.Model
) -> np.ndarray:
    embeddings: list[np.ndarray] = []

    for start in range(0, len(texts), BATCH_SIZE):
        batch_texts = texts[start : start + BATCH_SIZE]
        inputs = tokenizer(
            batch_texts,
            truncation=True,
            max_length=MAX_LENGTH,
            padding="max_length",
            return_tensors="tf",
        )
        outputs = beto_model(inputs)
        batch_embeddings = outputs.last_hidden_state[:, 0, :].numpy()
        embeddings.append(batch_embeddings)

    return np.vstack(embeddings)


def maybe_apply_smote(x_train: np.ndarray, y_train: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    try:
        class_counts = np.bincount(y_train)
        minority = class_counts[class_counts > 0].min()
        k_neighbors = max(1, min(3, minority - 1))
        smote = SMOTE(random_state=RANDOM_STATE, k_neighbors=k_neighbors)
        return smote.fit_resample(x_train, y_train)
    except Exception:
        return x_train, y_train


def compute_class_weights_dict(y_train: np.ndarray) -> dict[int, float]:
    classes = np.unique(y_train)
    weights = compute_class_weight(class_weight="balanced", classes=classes, y=y_train)
    return dict(zip(classes.tolist(), weights.tolist()))


def build_model(input_dim: int) -> keras.Model:
    model = models.Sequential(
        [
            layers.Dense(256, kernel_regularizer=l2(0.001), input_shape=(input_dim,)),
            layers.BatchNormalization(),
            layers.Activation("relu"),
            layers.Dropout(0.2),
            layers.Dense(128, kernel_regularizer=l2(0.001)),
            layers.BatchNormalization(),
            layers.Activation("relu"),
            layers.Dropout(0.2),
            layers.Dense(64, kernel_regularizer=l2(0.001)),
            layers.BatchNormalization(),
            layers.Activation("relu"),
            layers.Dropout(0.2),
            layers.Dense(32, kernel_regularizer=l2(0.001)),
            layers.BatchNormalization(),
            layers.Activation("relu"),
            layers.Dropout(0.2),
            layers.Dense(5, activation="softmax"),
        ]
    )
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


def quadratic_weighted_kappa(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    labels = np.arange(max(y_true.max(), y_pred.max()) + 1)
    conf_mat = confusion_matrix(y_true, y_pred, labels=labels).astype(float)
    conf_mat /= conf_mat.sum()

    hist_true = conf_mat.sum(axis=1)
    hist_pred = conf_mat.sum(axis=0)
    expected = np.outer(hist_true, hist_pred)

    n_classes = len(labels)
    weights = np.zeros((n_classes, n_classes))
    for i in range(n_classes):
        for j in range(n_classes):
            weights[i, j] = ((i - j) ** 2) / ((n_classes - 1) ** 2)

    numerator = np.sum(weights * conf_mat)
    denominator = np.sum(weights * expected)
    if denominator == 0:
        return 0.0
    return 1.0 - numerator / denominator


def export_artifacts(output_dir: Path, artifacts: Artifacts) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifacts.scaler, output_dir / "scaler.pkl")
    joblib.dump(artifacts.encoder, output_dir / "ohe_categoria.pkl")
    artifacts.model.save(output_dir / "modelo_urgencias.keras")


def train(data_path: Path, output_dir: Path) -> None:
    ensure_nltk_resources()
    _ = stopwords.words("spanish")

    df = load_dataset(data_path)
    tokenizer, beto_model = load_beto_model()

    x_text = df["description"].astype(str).tolist()
    x_text_beto = build_embeddings(x_text, tokenizer, beto_model)

    encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    x_cat = df[["categoria"]].astype(str)
    x_cat_encoded = encoder.fit_transform(x_cat)

    x = np.hstack((x_text_beto, x_cat_encoded))
    y = df["urgencia"].astype(int).values - 1

    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )

    x_train_resampled, y_train_resampled = maybe_apply_smote(x_train, y_train)
    class_weight_dict = compute_class_weights_dict(y_train_resampled)

    scaler = StandardScaler()
    x_train_scaled = scaler.fit_transform(x_train_resampled)
    x_test_scaled = scaler.transform(x_test)

    tf.config.threading.set_inter_op_parallelism_threads(4)
    tf.config.threading.set_intra_op_parallelism_threads(4)

    model = build_model(x_train_scaled.shape[1])
    early_stop = EarlyStopping(monitor="val_loss", patience=20, restore_best_weights=True, verbose=1)
    reduce_lr = ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=10, min_lr=1e-7, verbose=1)

    history = model.fit(
        x_train_scaled,
        y_train_resampled,
        validation_data=(x_test_scaled, y_test),
        epochs=200,
        batch_size=32,
        class_weight=class_weight_dict,
        callbacks=[early_stop, reduce_lr],
        verbose=1,
    )

    y_pred_probs = model.predict(x_test_scaled, verbose=0)
    y_pred_classes = np.argmax(y_pred_probs, axis=1)
    y_pred_urgencia = y_pred_classes + 1
    y_test_urgencia = y_test + 1

    accuracy = accuracy_score(y_test, y_pred_classes)
    mae = mean_absolute_error(y_test_urgencia, y_pred_urgencia)
    qwk = quadratic_weighted_kappa(y_test_urgencia - 1, y_pred_classes)

    print("=" * 80)
    print("Training complete")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"MAE: {mae:.4f}")
    print(f"QWK: {qwk:.4f}")
    print(classification_report(y_test, y_pred_classes, digits=4))
    precision, recall, f1, support = precision_recall_fscore_support(
        y_test, y_pred_classes, average=None, zero_division=0
    )
    print("Per-class metrics:")
    for idx in range(len(precision)):
        print(
            f"  class {idx + 1}: precision={precision[idx]:.3f}, "
            f"recall={recall[idx]:.3f}, f1={f1[idx]:.3f}, support={support[idx]}"
        )
    print(f"Final train loss: {history.history['loss'][-1]:.4f}")
    print(f"Final val loss: {history.history['val_loss'][-1]:.4f}")

    export_artifacts(output_dir, Artifacts(scaler=scaler, encoder=encoder, model=model))


def main() -> None:
    args = parse_args()
    train(args.data_path, args.output_dir)


if __name__ == "__main__":
    main()