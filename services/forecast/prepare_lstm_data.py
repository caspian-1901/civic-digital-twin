import pandas as pd
import numpy as np
import pickle
from sklearn.preprocessing import StandardScaler

WARD_FILE = "ward_hourly_observed.csv"
SPLIT_FILE = "persistence_baseline_final_samples.csv"

INPUT_HOURS = 24
OUTPUT_HOURS = 48

# ============================================================
# LOAD DATA
# ============================================================

ward = pd.read_csv(WARD_FILE)
splits = pd.read_csv(SPLIT_FILE)

ward["datetime_utc"] = pd.to_datetime(
    ward["datetime_utc"],
    utc=True,
    errors="coerce"
)

ward["pm25"] = pd.to_numeric(
    ward["pm25"],
    errors="coerce"
)

for col in [
    "input_start",
    "input_end",
    "forecast_start",
    "forecast_end"
]:
    splits[col] = pd.to_datetime(
        splits[col],
        utc=True,
        errors="coerce"
    )

ward = ward.sort_values(
    ["ward_name", "datetime_utc"]
).reset_index(drop=True)

# ============================================================
# FAST LOOKUP
# ============================================================

lookup = {
    (row.ward_name, row.datetime_utc): row.pm25
    for row in ward.itertuples()
}

# ============================================================
# BUILD ARRAYS FROM THE EXACT FROZEN SPLITS
# ============================================================

def build_split(split_name):

    part = (
        splits[splits["split"] == split_name]
        .copy()
        .reset_index(drop=True)
    )

    X = []
    y = []
    metadata = []

    for row in part.itertuples():

        input_times = pd.date_range(
            start=row.input_start,
            periods=INPUT_HOURS,
            freq="h"
        )

        target_times = pd.date_range(
            start=row.forecast_start,
            periods=OUTPUT_HOURS,
            freq="h"
        )

        input_values = [
            lookup.get((row.ward_name, t), np.nan)
            for t in input_times
        ]

        target_values = [
            lookup.get((row.ward_name, t), np.nan)
            for t in target_times
        ]

        if np.isnan(input_values).any():
            raise ValueError(
                f"Missing input values for {row.ward_name} "
                f"starting {row.input_start}"
            )

        if np.isnan(target_values).any():
            raise ValueError(
                f"Missing target values for {row.ward_name} "
                f"starting {row.forecast_start}"
            )

        X.append(input_values)
        y.append(target_values)

        metadata.append({
            "ward_name": row.ward_name,
            "input_start": row.input_start,
            "forecast_start": row.forecast_start,
            "split": split_name
        })

    return (
        np.array(X, dtype=np.float32),
        np.array(y, dtype=np.float32),
        pd.DataFrame(metadata)
    )

X_train_raw, y_train_raw, meta_train = build_split("train")
X_val_raw, y_val_raw, meta_val = build_split("validation")
X_test_raw, y_test_raw, meta_test = build_split("test")

# ============================================================
# FIT SCALER ON TRAINING DATA ONLY
#
# Important:
# scaler sees ONLY training PM2.5 values.
# ============================================================

scaler = StandardScaler()

train_values_for_scaler = np.concatenate([
    X_train_raw.reshape(-1),
    y_train_raw.reshape(-1)
]).reshape(-1, 1)

scaler.fit(train_values_for_scaler)

# ============================================================
# SCALE INPUTS AND TARGETS
# ============================================================

def scale_array(arr):
    original_shape = arr.shape

    scaled = scaler.transform(
        arr.reshape(-1, 1)
    )

    return scaled.reshape(original_shape).astype(np.float32)

X_train = scale_array(X_train_raw)
y_train = scale_array(y_train_raw)

X_val = scale_array(X_val_raw)
y_val = scale_array(y_val_raw)

X_test = scale_array(X_test_raw)
y_test = scale_array(y_test_raw)

# LSTM expects:
# samples x timesteps x features
X_train = X_train[..., np.newaxis]
X_val = X_val[..., np.newaxis]
X_test = X_test[..., np.newaxis]

# ============================================================
# VALIDATION
# ============================================================

print("=" * 75)
print("LSTM PREPROCESSING")
print("=" * 75)

print("\nRAW SHAPES")
print("X_train_raw:", X_train_raw.shape)
print("y_train_raw:", y_train_raw.shape)
print("X_val_raw:  ", X_val_raw.shape)
print("y_val_raw:  ", y_val_raw.shape)
print("X_test_raw: ", X_test_raw.shape)
print("y_test_raw: ", y_test_raw.shape)

print("\nLSTM SHAPES")
print("X_train:", X_train.shape)
print("y_train:", y_train.shape)
print("X_val:  ", X_val.shape)
print("y_val:  ", y_val.shape)
print("X_test: ", X_test.shape)
print("y_test: ", y_test.shape)

print("\nSCALER")
print("Mean:", scaler.mean_[0])
print("Scale:", scaler.scale_[0])

print("\nTRAIN SCALED INPUT SUMMARY")
print("Mean:", float(X_train.mean()))
print("Std: ", float(X_train.std()))

print("\nVALIDATION / TEST RANGE")
print("Validation min/max:", float(X_val.min()), float(X_val.max()))
print("Test min/max:", float(X_test.min()), float(X_test.max()))

# ============================================================
# CHECK COUNTS AGAINST FROZEN SPLIT FILE
# ============================================================

expected_train = (splits["split"] == "train").sum()
expected_val = (splits["split"] == "validation").sum()
expected_test = (splits["split"] == "test").sum()

assert len(X_train) == expected_train
assert len(X_val) == expected_val
assert len(X_test) == expected_test

assert X_train.shape[1:] == (24, 1)
assert X_val.shape[1:] == (24, 1)
assert X_test.shape[1:] == (24, 1)

assert y_train.shape[1] == 48
assert y_val.shape[1] == 48
assert y_test.shape[1] == 48

print("\nCOUNT / SHAPE CHECK: PASS")

# ============================================================
# SAVE ARRAYS
# ============================================================

np.save("X_train.npy", X_train)
np.save("y_train.npy", y_train)

np.save("X_val.npy", X_val)
np.save("y_val.npy", y_val)

np.save("X_test.npy", X_test)
np.save("y_test.npy", y_test)

np.save("X_train_raw.npy", X_train_raw)
np.save("y_train_raw.npy", y_train_raw)

np.save("X_val_raw.npy", X_val_raw)
np.save("y_val_raw.npy", y_val_raw)

np.save("X_test_raw.npy", X_test_raw)
np.save("y_test_raw.npy", y_test_raw)

meta_train.to_csv("lstm_train_metadata.csv", index=False)
meta_val.to_csv("lstm_validation_metadata.csv", index=False)
meta_test.to_csv("lstm_test_metadata.csv", index=False)

with open("pm25_scaler.pkl", "wb") as f:
    pickle.dump(scaler, f)

print("\nSaved:")
print("X_train.npy / y_train.npy")
print("X_val.npy / y_val.npy")
print("X_test.npy / y_test.npy")
print("raw arrays")
print("LSTM metadata files")
print("pm25_scaler.pkl")

print("\nPREPROCESSING RESULT: PASS")
