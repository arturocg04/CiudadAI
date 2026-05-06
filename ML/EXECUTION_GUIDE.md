## 🚀 GUÍA DE EJECUCIÓN - Modelo Mejorado CiudadAI

### 📋 Estado de Dependencias

**Instaladas correctamente:**
- ✅ pandas, numpy, matplotlib, seaborn
- ✅ scikit-learn (ML clásico)
- ✅ tensorflow, keras (Deep Learning)
- ✅ transformers (BETO - BERT en español)
- ✅ imbalanced-learn (SMOTE)
- ✅ nltk (stopwords)
- ✅ scipy

**En proceso de instalación:**
- ⏳ torch (PyTorch - Backend para transformers)
  - Tamaño: ~400MB (CPU-only)
  - Tiempo: 5-15 minutos (depende de velocidad de conexión)
  - Estado: Se está descargando...

---

### 🔧 Pre-Requisitos de Ejecución

#### 1. Verificar que PyTorch está instalado
```bash
cd /home/a200530668/bootcamp
source .venv/bin/activate
python -c "import torch; print(f'PyTorch version: {torch.__version__}')"
```

**Salida esperada:**
```
PyTorch version: 2.x.x
```

#### 2. Si PyTorch no está instalado aún
```bash
# Opción A: Instalación estándar (más lenta pero segura)
pip install torch

# Opción B: Instalación rápida sin caché (recomendado si hay errores)
pip install --no-cache-dir torch

# Opción C: Si descargas son muy lentas, versión más ligera
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

**Tiempo estimado**: 5-15 minutos

---

### ▶️ Ejecución del Notebook

#### Paso 1: Abre el Notebook
```
CiudadAI/ML/ModelTraining.ipynb
```

#### Paso 2: Ejecuta las celdas en orden

**Celda 1-2 (Setup)**: ~5 segundos
- Importa librerías
- Verifica dependencias
- Resultado: ✅ "TODAS LAS DEPENDENCIAS INSTALADAS"

**Celda 3 (Data Loading)**: ~2 segundos
- Carga `incidencias.csv`
- Verifica datos
- Resultado: Dataset shape, primeras filas

**Celda 4 (Visualización)**: ~3 segundos
- Gráficos de distribución por urgencia y categoría
- Tabla cruzada

**Celda 5 (Procesamiento de Texto con BETO)**: ⏱️ **5-10 MINUTOS** ⏱️
- Primera ejecución: Descarga modelo BETO (~500MB)
- Extraer embeddings para todas las descripciones
- Aplicar SMOTE y normalizar datos
- **⚠️ ESTA ES LA CELDA MÁS LENTA (solo primera vez)**

**Celdas 6-7 (Entrenamiento)**: ⏱️ **3-5 MINUTOS**
- Construir arquitectura neuronal
- Entrenar modelo con 200 épocas (se detiene antes si no mejora)
- Resultado: Gráficos de pérdida y accuracy

**Celda 8 (Evaluación)**: ~1 minuto
- Predicciones en test set
- Métricas: MAE, Quadratic Weighted Kappa, Confusion Matrix
- Análisis de errores por urgencia

**Celda 9 (Predicciones)**: ~10 segundos
- Función de predicción mejorada
- Pruebas con 3 casos de ejemplo

**Celda 10 (Resumen)**: Markdown (información)

---

### ⏱️ TIEMPO TOTAL DE EJECUCIÓN

| Etapa | Tiempo | Notas |
|-------|--------|-------|
| Setup (Celdas 1-4) | ~10 seg | Rápido |
| Descarga BETO (Celda 5, solo 1ª vez) | 5-10 min | Depende de internet |
| Procesamiento BETO | 2-3 min | Extrae embeddings |
| SMOTE + Preparación datos | 1-2 min | Rebalanceo de clases |
| Entrenamiento Red Neuronal | 3-5 min | CPU: más lento que GPU |
| Evaluación y Visualizaciones | 1-2 min | Generación de gráficos |
| **TOTAL PRIMERA VEZ** | **15-25 min** | Incluye descarga BETO |
| **TOTAL EJECUCIONES SIGUIENTES** | **8-12 min** | BETO ya en caché |

---

### 💻 Rendimiento en CPU vs GPU

**Entrenamiento en CPU** (tu configuración):
- Máquinas: t2.medium (AWS), 4 cores
- Tiempo: 3-5 minutos por entrenamiento
- Embeddings BETO: 2-3 minutos

**Rendimiento esperado:**
- Model size: ~110M de parámetros BETO + 67K de red neuronal
- Memoria RAM: ~2-3GB
- Velocidad: Adecuada para desarrollo, producción recomendaría GPU

---

### 🎯 Qué Esperar en Resultados

#### Métricas de Éxito
```
✅ Accuracy: 70-75%
✅ MAE: 0.4-0.6 (error promedio ~0.5 niveles en escala 1-5)
✅ Quadratic Weighted Kappa: 0.65-0.75 (buen acuerdo ordinal)
✅ Detección de urgencias críticas (4-5): >85%
```

#### Distribución de Predicciones
- Urgencia 1-2: ~50-60% (como en datos reales)
- Urgencia 3: ~20-25%
- Urgencia 4-5: ~15-25% (mejorado vs antes: ~5%)

---

### ⚠️ Errores Comunes y Soluciones

#### ❌ "ImportError: No module named 'torch'"
```bash
# Solución
pip install torch --no-cache-dir
```

#### ❌ "PyTorch was not found. Models won't be available"
```bash
# Indica que torch necesita ser instalado
pip install --no-cache-dir torch
```

#### ❌ "CUDA out of memory" (si tienes GPU)
```bash
# Reducir batch_size en la celda de entrenamiento
# batch_size=32 → batch_size=16 o incluso 8
```

#### ❌ "Connection timeout descargando BETO"
```bash
# Reintentar, a veces es problema de servidor
# Si persiste, usar modelo más pequeño:
model_name = "google-bert/bert-base-spanish-cased"  # 110M vs 180M
```

#### ❌ "SMOTE no pudo aplicarse"
```python
# SMOTE requiere suficientes muestras por clase
# El código ya lo maneja automáticamente, usa dataset sin SMOTE
```

---

### 🔄 Cómo Re-ejecutar Solo Ciertas Celdas

**Para iteración rápida (después de 1ª ejecución):**

1. **Cambiar solo hiperparámetros de entrenamiento**:
   - Edita Celda 7 (learning_rate, epochs, batch_size)
   - Re-ejecuta solo Celda 7
   - Tiempo: 3-5 min

2. **Cambiar arquitectura**:
   - Edita Celda 6 (número de capas, dropout)
   - Re-ejecuta Celda 6 + 7
   - Tiempo: 5-7 min

3. **Cambiar modelo BETO**:
   - Edita Celda 5 (model_name)
   - Re-ejecuta desde Celda 5
   - Tiempo: 10-15 min (nueva descarga)

---

### 📊 Monitoreo del Entrenamiento

La Celda 7 mostrar progreso de entrenamiento:

```
Epoch 1/200
32/32 [====================] - 2s - loss: 0.8234 - accuracy: 0.5612 - val_loss: 0.7456 - val_accuracy: 0.6234
Epoch 2/200
32/32 [====================] - 2s - loss: 0.7123 - accuracy: 0.6345 - val_loss: 0.6234 - val_accuracy: 0.6789
...
```

**Señales de buen entrenamiento:**
- ✅ Loss disminuye consistentemente (mejor modelo)
- ✅ Val_loss sigue a training loss (sin sobreajuste)
- ✅ Accuracy aumenta (predicciones mejoran)

**Señales de problemas:**
- ❌ Loss no baja después de 10 épocas (learning rate muy bajo)
- ❌ Val_loss diverge de training loss (sobreajuste - aumenta dropout)
- ❌ Accuracy estancada (aumenta épocas o capas)

---

### 💾 Guardar Modelo Después del Entrenamiento

Para usar el modelo en producción, añade al final:

```python
# Guardar el modelo
nn_model.save('/path/to/modelo_urgencias.h5')

# Guardar el scaler (necesario para normalizar predicciones)
import pickle
with open('/path/to/scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)

# Guardar el tokenizador (para predecir nuevos textos)
tokenizer.save_pretrained('/path/to/beto_tokenizer')
```

---

### 🎓 Próximos Pasos Sugeridos

1. **Experimentar con arquitecturas**:
   - Añadir más capas Dense
   - Cambiar número de neuronas
   - Ajustar dropout y L2 regularization

2. **Mejorar datos**:
   - Aumentar dataset de entrenamiento
   - Balancear clases manualmente
   - Limpiar textos de descripciones

3. **Optimizaciones**:
   - Cambiar modelo BETO por uno más pequeño si es lento
   - Usar data augmentation en textos
   - Implementar cross-validation

4. **Deployment**:
   - Guardar modelo entrenado
   - Crear API con FastAPI/Flask
   - Integrar en backend de CiudadAI

---

**¡Listo para ejecutar! 🚀**
