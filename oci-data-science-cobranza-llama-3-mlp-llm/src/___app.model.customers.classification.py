import pandas as pd
import tensorflow as tf
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report
import warnings

# Redirigir advertencias a un archivo para evitar que se muestren en la consola
warnings.filterwarnings("ignore", category=UserWarning, module="transformers")

# Leer el archivo CSV
df = pd.read_csv('____source.customers.csv')

# Preparar los datos
X = df[['age', 'income', 'amount_owed']].values
y = df['payment_history'].apply(lambda x: 1 if x == 'defaulted' else 0).values

# Escalar los datos
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Dividir los datos en conjuntos de entrenamiento y prueba utilizando TensorFlow
dataset = tf.data.Dataset.from_tensor_slices((X_scaled, y))
train_size = int(0.8 * len(X_scaled))
train_dataset = dataset.take(train_size).batch(32).cache().prefetch(tf.data.AUTOTUNE)
test_dataset = dataset.skip(train_size).batch(32).cache().prefetch(tf.data.AUTOTUNE)

# Crear el modelo de red neuronal
model = tf.keras.Sequential([
    tf.keras.layers.Dense(64, input_shape=(X_scaled.shape[1],), activation='relu'),
    tf.keras.layers.Dense(32, activation='relu'),
    tf.keras.layers.Dense(1, activation='sigmoid')
])

# Compilar el modelo
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

# Entrenar el modelo
model.fit(train_dataset, epochs=100, validation_data=test_dataset)

# Evaluar el modelo
y_pred = (model.predict(X_scaled) > 0.5).astype("int32")
print(classification_report(y, y_pred))

# Predecir sobre el conjunto de datos completo
df['predicted_default'] = y_pred

# Filtrar clientes morosos
morosos = df[df['predicted_default'] == 1]

# Guardar clientes morosos en un archivo CSV
morosos.to_csv('___model.customers.classification.csv', index=False)

print("\n[MLP]: Se genero la lista de clientes pendietes por pagar...\n")

print(morosos.head())