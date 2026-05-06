# Archivo: download_model.py
import os
from transformers import AutoTokenizer, TFAutoModel

# Suprimir warnings durante la descarga
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

model_id = "dccuchile/bert-base-spanish-wwm-uncased"

print(f"Descargando {model_id} para hornearlo en la imagen Docker...")
AutoTokenizer.from_pretrained(model_id)
TFAutoModel.from_pretrained(model_id)
print("Descarga y cacheo completados con éxito.")