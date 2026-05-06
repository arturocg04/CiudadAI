"""Servicio de Machine Learning para clasificación de urgencia.

Propósito: cargar el modelo entrenado y predecir urgencia a partir de descripciones.
Nota: Este es un mock que retorna urgencias aleatorias. En producción,
se cargaría un modelo real entrenado con el dataset.
"""

import logging
import random
from typing import Optional

logger = logging.getLogger(__name__)


class MLService:
    """Servicio para predicción de urgencia usando ML."""

    def __init__(self):
        """Inicializa el servicio ML.

        En producción, aquí se cargaría el modelo entrenado:
        - Importar joblib: from joblib import load
        - Cargar modelo: self.model = load('path/to/model.pkl')
        """
        logger.info("Inicializando MLService")
        # TODO: Cargar modelo real en producción
        # self.model = load('models/urgency_classifier.pkl')
        self.model = None

    def predict_urgency(self, description: str) -> int:
        """Predice la urgencia (1-5) a partir de una descripción.

        Args:
            description: Texto de descripción de la incidencia

        Returns:
            int: Valor de urgencia entre 1 y 5

        En producción:
        - Preprocesar description (limpieza, tokenización)
        - Vectorizar con TF-IDF o embeddings
        - Usar self.model.predict() para obtener urgencia
        """

        if not description or len(description.strip()) == 0:
            return 1

        # Mock: predicción basada en palabras clave
        urgency_keywords = {
            5: [
                "emergencia",
                "grave",
                "crítico",
                "incendio",
                "explosión",
                "herida",
                "sangre",
            ],
            4: ["urgente", "peligro", "accidente", "colisión", "caída", "rotura"],
            3: ["problema", "daño", "mal funcionamiento", "basura", "alcantarilla"],
            2: ["molestia", "incómodo", "falta", "señal", "pintura"],
            1: ["consulta", "información", "mejora", "sugerencia", "comentario"],
        }

        description_lower = description.lower()

        for urgency_level in sorted(urgency_keywords.keys(), reverse=True):
            for keyword in urgency_keywords[urgency_level]:
                if keyword in description_lower:
                    logger.info(
                        f"Detected keyword '{keyword}' -> urgency {urgency_level}"
                    )
                    return urgency_level

        # Default: urgencia media
        return 3

    def validate_category(self, description: str, suggested_category: str) -> str:
        """Valida o confirma la categoría a partir de la descripción.

        Args:
            description: Texto de descripción
            suggested_category: Categoría sugerida por el usuario

        Returns:
            str: Categoría confirmada/predicha

        En producción:
        - Usar modelo de clasificación de categorías
        - Retornar la categoría más probable
        """

        category_keywords = {
            "Movilidad": [
                "calle",
                "acera",
                "bache",
                "semáforo",
                "carril",
                "tráfico",
                "conducir",
            ],
            "Limpieza": [
                "basura",
                "suciedad",
                "residuos",
                "limpio",
                "escombros",
                "polvo",
            ],
            "Alumbrado": ["luz", "lámpara", "faro", "oscuro", "iluminación", "apagado"],
            "Seguridad": [
                "robo",
                "delito",
                "peligro",
                "seguridad",
                "vigilancia",
                "cámara",
            ],
            "Agua": [
                "fugas",
                "agua",
                "inundación",
                "tubería",
                "desagüe",
                "alcantarilla",
            ],
        }

        description_lower = description.lower()

        for category, keywords in category_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                return category

        # Si no hay coincidencia, retornar la categoría sugerida
        return suggested_category


# Instancia singleton del servicio ML
ml_service = MLService()
