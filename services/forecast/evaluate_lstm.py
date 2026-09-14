import pickle
import numpy as np
import pandas as pd
from tensorflow import keras

# ============================================================
# LOCKED BASELINE VALUES
# ============================================================

PERSISTENCE_MICRO_MAE = 7.6273
PERSISTENCE_MACRO_MAE = 8.6916

# ============================================================
# LOAD MODEL, SCALER, TEST DATA
# ============================================================

model = keras.models.load_model(
    "best_lstm_model.keras"
)

with open("final_pm25_scaler.pkl", "rb") as f:
    scaler = pickle.load(f)

X_test = np.load("X_test.npy")
y_test = np.load("y_test.npy")

y_test_raw = np.load("y_test_raw.npy")

metadata = pd.read_csv(
    "lstm_test_metadata.csv"
)

print("=" * 80)
print("FINAL HELD-OUT LSTM EVALUATION")
print("=" * 80)

print("\nTEST DATA")
print("X_test:", X_test.shape)
print("y_test:", y_test.shape)
print("Metadata rows:", len(metadata))

assert len(X_test) == len(y_test)
assert len(X_test) == len(metadata)
assert y_test.shape[1] == 48

# ============================================================
# PREDICT
# ============================================================

print("\nGenerating predictions...")

pred_scaled = model.predict(
    X_test,
    batch_size=64,
    verbose=1
)

print("Predicted shape:", pred_scaled.shape)

assert pred_scaled.shape == y_test.shape

# ============================================================
# INVERSE TRANSFORM INTO REAL PM2.5 UNITS
# ============================================================

pred_raw = scaler.inverse_transform(
    pred_scaled.reshape(-1, 1)
).reshape(pred_scaled.shape)

# Compare saved raw targets with inverse transformed scaled targets
y_inverse = scaler.inverse_transform(
    y_test.reshape(-1, 1)
).reshape(y_test.shape)

reconstruction_error = np.max(
    np.abs(y_inverse - y_test_raw)
)

print(
    "\nTarget reconstruction error:",
    reconstruction_error
)

assert reconstruction_error < 1e-3

# ============================================================
# MICRO MAE
# Every forecasted hour gets equal weight
# ============================================================

absolute_errors = np.abs(
    pred_raw - y_test_raw
)

micro_mae = float(
    absolute_errors.mean()
)

# ============================================================
# SAMPLE-LEVEL MAE
# ============================================================

sample_mae = (
    absolute_errors.mean(axis=1)
)

metadata["lstm_mae"] = sample_mae

# ============================================================
# WARD-LEVEL MAE
# ============================================================

ward_results = (
    metadata.groupby("ward_name")["lstm_mae"]
    .agg(["count", "mean", "median"])
    .sort_values("mean")
)

macro_mae = float(
    ward_results["mean"].mean()
)

# ============================================================
# HORIZON MAE
# How error changes from hour 1 to hour 48
# ============================================================

horizon_mae = absolute_errors.mean(axis=0)

horizon_df = pd.DataFrame({
    "forecast_hour": np.arange(1, 49),
    "mae": horizon_mae
})

# ============================================================
# BASELINE COMPARISON
# ============================================================

micro_improvement = (
    (PERSISTENCE_MICRO_MAE - micro_mae)
    / PERSISTENCE_MICRO_MAE
    * 100
)

macro_improvement = (
    (PERSISTENCE_MACRO_MAE - macro_mae)
    / PERSISTENCE_MACRO_MAE
    * 100
)

print("\n" + "=" * 80)
print("LSTM TEST RESULTS")
print("=" * 80)

print(
    "LSTM micro-average MAE:",
    round(micro_mae, 4),
    "ug/m3"
)

print(
    "LSTM macro-average MAE:",
    round(macro_mae, 4),
    "ug/m3"
)

print("\n" + "=" * 80)
print("PERSISTENCE BASELINE")
print("=" * 80)

print(
    "Persistence micro MAE:",
    PERSISTENCE_MICRO_MAE,
    "ug/m3"
)

print(
    "Persistence macro MAE:",
    PERSISTENCE_MACRO_MAE,
    "ug/m3"
)

print("\n" + "=" * 80)
print("IMPROVEMENT VS BASELINE")
print("=" * 80)

print(
    "Micro improvement:",
    round(micro_improvement, 2),
    "%"
)

print(
    "Macro improvement:",
    round(macro_improvement, 2),
    "%"
)

print("\n" + "=" * 80)
print("TEST MAE BY WARD")
print("=" * 80)

print(
    ward_results.to_string()
)

print("\n" + "=" * 80)
print("MAE BY FORECAST HORIZON")
print("=" * 80)

print(
    horizon_df.to_string(index=False)
)

# ============================================================
# DECISION
# ============================================================

print("\n" + "=" * 80)
print("FINAL MODEL DECISION")
print("=" * 80)

if (
    micro_mae < PERSISTENCE_MICRO_MAE
    and macro_mae < PERSISTENCE_MACRO_MAE
):
    print("PASS - LSTM beats persistence on both micro and macro MAE.")

elif micro_mae < PERSISTENCE_MICRO_MAE:
    print(
        "PARTIAL PASS - LSTM beats persistence on micro MAE "
        "but not macro MAE."
    )

else:
    print(
        "FAIL - LSTM does not beat the persistence baseline."
    )

# ============================================================
# SAVE RESULTS
# ============================================================

metadata.to_csv(
    "lstm_test_sample_results.csv",
    index=False
)

ward_results.to_csv(
    "lstm_test_by_ward.csv"
)

horizon_df.to_csv(
    "lstm_test_by_horizon.csv",
    index=False
)

np.save(
    "lstm_test_predictions_raw.npy",
    pred_raw
)

summary = pd.DataFrame([{
    "persistence_micro_mae": PERSISTENCE_MICRO_MAE,
    "lstm_micro_mae": micro_mae,
    "micro_improvement_pct": micro_improvement,
    "persistence_macro_mae": PERSISTENCE_MACRO_MAE,
    "lstm_macro_mae": macro_mae,
    "macro_improvement_pct": macro_improvement
}])

summary.to_csv(
    "lstm_vs_persistence_summary.csv",
    index=False
)

print("\nSaved:")
print("lstm_test_sample_results.csv")
print("lstm_test_by_ward.csv")
print("lstm_test_by_horizon.csv")
print("lstm_test_predictions_raw.npy")
print("lstm_vs_persistence_summary.csv")
