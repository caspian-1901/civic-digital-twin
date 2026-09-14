import pandas as pd
import numpy as np

INPUT = "ward_hourly_observed.csv"

INPUT_HOURS = 24
OUTPUT_HOURS = 48
WINDOW = INPUT_HOURS + OUTPUT_HOURS

# ============================================================
# LOAD DATA
# ============================================================

df = pd.read_csv(INPUT)

df["datetime_utc"] = pd.to_datetime(
    df["datetime_utc"],
    utc=True,
    errors="coerce"
)

df["pm25"] = pd.to_numeric(
    df["pm25"],
    errors="coerce"
)

df = df.dropna(
    subset=["ward_name", "datetime_utc", "pm25"]
).copy()

df = df.sort_values(
    ["ward_name", "datetime_utc"]
).reset_index(drop=True)

all_samples = []

# ============================================================
# BUILD VALID 72-HOUR WINDOWS
# ============================================================

for ward, g in df.groupby("ward_name"):

    g = (
        g.sort_values("datetime_utc")
         .reset_index(drop=True)
    )

    times = g["datetime_utc"].tolist()
    values = g["pm25"].to_numpy()

    ward_samples = []

    for i in range(len(g) - WINDOW + 1):

        window_times = times[i:i + WINDOW]

        # Check exact hourly continuity
        continuous = all(
            window_times[j] - window_times[j - 1]
            == pd.Timedelta(hours=1)
            for j in range(1, WINDOW)
        )

        if not continuous:
            continue

        window_values = values[i:i + WINDOW]

        input_values = window_values[:INPUT_HOURS]
        target_values = window_values[INPUT_HOURS:]

        # Persistence baseline:
        # repeat final input value for all 48 forecast hours
        prediction = np.repeat(
            input_values[-1],
            OUTPUT_HOURS
        )

        mae = float(
            np.mean(
                np.abs(
                    target_values - prediction
                )
            )
        )

        ward_samples.append({
            "ward_name": ward,
            "input_start": window_times[0],
            "input_end": window_times[INPUT_HOURS - 1],
            "forecast_start": window_times[INPUT_HOURS],
            "forecast_end": window_times[-1],
            "last_input_pm25": input_values[-1],
            "target_mean_pm25": float(target_values.mean()),
            "mae": mae
        })

    ws = pd.DataFrame(ward_samples)

    if len(ws) == 0:
        print("WARNING: no valid samples for", ward)
        continue

    ws = (
        ws.sort_values("input_start")
          .reset_index(drop=True)
    )

    # ========================================================
    # PER-WARD CHRONOLOGICAL 70 / 15 / 15 SPLIT
    # ========================================================

    n = len(ws)

    train_end_idx = int(n * 0.70)
    val_end_idx = int(n * 0.85)

    train = ws.iloc[:train_end_idx].copy()
    validation = ws.iloc[
        train_end_idx:val_end_idx
    ].copy()
    test = ws.iloc[val_end_idx:].copy()

    # ========================================================
    # PREVENT RAW-HOUR OVERLAP BETWEEN SPLITS
    #
    # A validation sample is retained only if its input begins
    # AFTER the final hour touched by the training set.
    # Same logic for validation -> test.
    # ========================================================

    if len(train) > 0 and len(validation) > 0:

        last_train_hour = train["forecast_end"].max()

        validation = validation[
            validation["input_start"] > last_train_hour
        ].copy()

    if len(validation) > 0 and len(test) > 0:

        last_validation_hour = (
            validation["forecast_end"].max()
        )

        test = test[
            test["input_start"] > last_validation_hour
        ].copy()

    train["split"] = "train"
    validation["split"] = "validation"
    test["split"] = "test"

    combined = pd.concat(
        [train, validation, test],
        ignore_index=True
    )

    all_samples.append(combined)

# ============================================================
# COMBINE ALL WARDS
# ============================================================

samples = pd.concat(
    all_samples,
    ignore_index=True
)

samples = samples.sort_values(
    ["ward_name", "input_start"]
).reset_index(drop=True)

print("=" * 80)
print("FINAL PERSISTENCE BASELINE")
print("=" * 80)

print("\nTotal retained samples:", len(samples))
print("Wards:", samples["ward_name"].nunique())

# ============================================================
# SPLIT COUNTS
# ============================================================

print("\n" + "=" * 80)
print("SPLIT COUNTS")
print("=" * 80)

print(
    samples["split"]
    .value_counts()
    .reindex(["train", "validation", "test"])
    .to_string()
)

# ============================================================
# PER-WARD SPLIT COUNTS
# ============================================================

split_counts = (
    samples.groupby(
        ["ward_name", "split"]
    )
    .size()
    .unstack(fill_value=0)
)

for col in ["train", "validation", "test"]:
    if col not in split_counts.columns:
        split_counts[col] = 0

split_counts = split_counts[
    ["train", "validation", "test"]
]

print("\n" + "=" * 80)
print("SAMPLES PER WARD")
print("=" * 80)

print(split_counts.to_string())

# ============================================================
# DATE RANGES PER SPLIT
# ============================================================

print("\n" + "=" * 80)
print("DATE RANGES")
print("=" * 80)

for split in ["train", "validation", "test"]:

    part = samples[
        samples["split"] == split
    ]

    print(
        f"{split:10s}",
        "|",
        part["input_start"].min(),
        "to",
        part["forecast_end"].max(),
        "| samples:",
        len(part)
    )

# ============================================================
# OVERALL MAE
# ============================================================

overall = (
    samples.groupby("split")["mae"]
    .agg(["count", "mean", "median"])
    .reindex(["train", "validation", "test"])
)

print("\n" + "=" * 80)
print("OVERALL PERSISTENCE MAE")
print("=" * 80)

print(overall.to_string())

# ============================================================
# TEST MAE BY WARD
# ============================================================

test = samples[
    samples["split"] == "test"
].copy()

ward_test = (
    test.groupby("ward_name")["mae"]
    .agg(["count", "mean", "median"])
    .sort_values("mean")
)

print("\n" + "=" * 80)
print("TEST MAE BY WARD")
print("=" * 80)

print(ward_test.to_string())

# Equal weight to every ward
macro_test_mae = (
    ward_test["mean"].mean()
)

# Every sample receives equal weight
micro_test_mae = (
    test["mae"].mean()
)

print("\n" + "=" * 80)
print("FINAL TEST BENCHMARK")
print("=" * 80)

print(
    "Micro-average test MAE:",
    round(micro_test_mae, 4)
)

print(
    "Macro-average test MAE:",
    round(macro_test_mae, 4)
)

# ============================================================
# LEAKAGE SAFETY CHECK
# ============================================================

print("\n" + "=" * 80)
print("SPLIT OVERLAP SAFETY CHECK")
print("=" * 80)

problems = []

for ward, g in samples.groupby("ward_name"):

    tr = g[g["split"] == "train"]
    va = g[g["split"] == "validation"]
    te = g[g["split"] == "test"]

    train_val_ok = True
    val_test_ok = True

    if len(tr) and len(va):
        train_val_ok = (
            tr["forecast_end"].max()
            <
            va["input_start"].min()
        )

    if len(va) and len(te):
        val_test_ok = (
            va["forecast_end"].max()
            <
            te["input_start"].min()
        )

    if not train_val_ok or not val_test_ok:
        problems.append(ward)

if len(problems) == 0:
    print(
        "PASS - no underlying hours overlap "
        "across split boundaries"
    )
else:
    print(
        "FAIL - overlap detected in:",
        problems
    )

# ============================================================
# SAVE
# ============================================================

samples.to_csv(
    "persistence_baseline_final_samples.csv",
    index=False
)

ward_test.to_csv(
    "persistence_baseline_final_test_by_ward.csv"
)

overall.to_csv(
    "persistence_baseline_final_overall.csv"
)

split_counts.to_csv(
    "persistence_baseline_final_split_counts.csv"
)

print("\nSaved:")
print("persistence_baseline_final_samples.csv")
print("persistence_baseline_final_test_by_ward.csv")
print("persistence_baseline_final_overall.csv")
print("persistence_baseline_final_split_counts.csv")
