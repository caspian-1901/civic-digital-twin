import json
import pickle
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

# ============================================================
# CONFIGURATION
# ============================================================

INPUT_HOURS = 24
FEATURES = 1
HIDDEN_UNITS = 64
OUTPUT_HOURS = 48

LEARNING_RATE = 0.001
MAX_EPOCHS = 100
BATCH_SIZE = 64
PATIENCE = 10

tf.keras.utils.set_random_seed(42)

# ============================================================
# LOAD DATA
# ============================================================

print("=" * 75)
print("LOADING LSTM DATA")
print("=" * 75)

X_train = np.load("X_train.npy")
y_train = np.load("y_train.npy")

X_val = np.load("X_val.npy")
y_val = np.load("y_val.npy")

print("X_train:", X_train.shape)
print("y_train:", y_train.shape)
print("X_val:  ", X_val.shape)
print("y_val:  ", y_val.shape)

assert X_train.shape[1:] == (24, 1)
assert y_train.shape[1] == 48
assert X_val.shape[1:] == (24, 1)
assert y_val.shape[1] == 48

# ============================================================
# MODEL
# ============================================================

model = keras.Sequential([
    layers.Input(
        shape=(INPUT_HOURS, FEATURES),
        name="pm25_input"
    ),

    layers.LSTM(
        HIDDEN_UNITS,
        return_sequences=True,
        name="lstm_1"
    ),

    layers.LSTM(
        HIDDEN_UNITS,
        return_sequences=False,
        name="lstm_2"
    ),

    layers.Dense(
        OUTPUT_HOURS,
        name="forecast_48h"
    )
])

model.compile(
    optimizer=keras.optimizers.Adam(
        learning_rate=LEARNING_RATE
    ),
    loss="mae",
    metrics=["mae"]
)

model.summary()

# ============================================================
# CALLBACKS
# ============================================================

early_stopping = keras.callbacks.EarlyStopping(
    monitor="val_loss",
    patience=PATIENCE,
    mode="min",
    restore_best_weights=True,
    verbose=1
)

checkpoint = keras.callbacks.ModelCheckpoint(
    filepath="best_lstm_model.keras",
    monitor="val_loss",
    mode="min",
    save_best_only=True,
    verbose=1
)

# ============================================================
# TRAIN
# ============================================================

print("\n" + "=" * 75)
print("STARTING LSTM TRAINING")
print("=" * 75)

history = model.fit(
    X_train,
    y_train,

    validation_data=(
        X_val,
        y_val
    ),

    epochs=MAX_EPOCHS,
    batch_size=BATCH_SIZE,

    shuffle=False,

    callbacks=[
        early_stopping,
        checkpoint
    ],

    verbose=1
)

# ============================================================
# SAVE FINAL RESTORED MODEL
# ============================================================

model.save("final_lstm_model.keras")

with open("training_history.json", "w") as f:
    json.dump(
        {
            key: [float(v) for v in values]
            for key, values in history.history.items()
        },
        f,
        indent=2
    )

# Save scaler alongside model
with open("pm25_scaler.pkl", "rb") as f:
    scaler = pickle.load(f)

with open("final_pm25_scaler.pkl", "wb") as f:
    pickle.dump(scaler, f)

# ============================================================
# TRAINING SUMMARY
# ============================================================

val_losses = history.history["val_loss"]

best_epoch = int(np.argmin(val_losses)) + 1
best_val_loss = float(np.min(val_losses))

print("\n" + "=" * 75)
print("TRAINING COMPLETE")
print("=" * 75)

print("Epochs actually run:", len(val_losses))
print("Best epoch:", best_epoch)
print("Best validation MAE (scaled):", best_val_loss)

print("\nSaved:")
print("best_lstm_model.keras")
print("final_lstm_model.keras")
print("final_pm25_scaler.pkl")
print("training_history.json")

print("\nIMPORTANT:")
print("Test set has NOT been used during training.")
print("Next step is final held-out test evaluation.")
