from pathlib import Path
import pickle

import numpy as np
import pandas as pd
import tensorflow as tf
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware


BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "final_lstm_model.keras"
SCALER_PATH = BASE_DIR / "final_pm25_scaler.pkl"
DATA_PATH = BASE_DIR / "ward_hourly_observed.csv"


# BMC administrative ward IDs from the validated ward GeoJSON.
WARD_ID_TO_NAME = {
    1: "A",
    2: "B",
    3: "C",
    4: "D",
    5: "E",
    6: "F/S",
    7: "G/S",
    8: "F/N",
    9: "G/N",
    10: "N",
    11: "R/C",
    12: "S",
    13: "T",
    14: "K/W",
    15: "R/N",
    16: "M/E",
    17: "M/W",
    18: "H/E",
    19: "K/E",
    20: "P/S",
    21: "P/N",
    22: "R/S",
    23: "H/W",
    24: "L",
}


app = FastAPI(
    title="Civic Digital Twin Forecast Service",
    version="1.0.0",
)

# Required by CONTRACTS.md
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Load model and scaler once when the service starts.
model = tf.keras.models.load_model(MODEL_PATH)

with open(SCALER_PATH, "rb") as f:
    scaler = pickle.load(f)


# Load and prepare ward-hourly observations.
observations = pd.read_csv(DATA_PATH)
observations["datetime_utc"] = pd.to_datetime(
    observations["datetime_utc"],
    utc=True,
)
observations = observations.sort_values(
    ["ward_name", "datetime_utc"]
).reset_index(drop=True)


def latest_contiguous_24_hours(ward_name: str) -> pd.DataFrame:
    """
    Return the most recent 24 consecutive hourly PM2.5 observations
    for the requested ward.
    """
    ward_df = observations[
        observations["ward_name"] == ward_name
    ].copy()

    if ward_df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No observed PM2.5 data available for ward {ward_name}",
        )

    ward_df = ward_df.sort_values("datetime_utc").reset_index(drop=True)

    # A new run starts whenever the gap is not exactly one hour.
    gaps = ward_df["datetime_utc"].diff()
    run_id = gaps.ne(pd.Timedelta(hours=1)).cumsum()
    ward_df["run_id"] = run_id

    runs = ward_df.groupby("run_id", sort=False)

    valid_runs = [
        run.copy()
        for _, run in runs
        if len(run) >= 24
    ]

    if not valid_runs:
        raise HTTPException(
            status_code=422,
            detail=f"Ward {ward_name} has no continuous 24-hour input sequence",
        )

    latest_run = max(
        valid_runs,
        key=lambda x: x["datetime_utc"].max(),
    )

    return latest_run.tail(24).copy()


@app.get("/forecast")
def get_forecast(
    ward_id: int = Query(..., ge=1, le=24),
    hours: int = Query(48, ge=1, le=48),
):
    if ward_id not in WARD_ID_TO_NAME:
        raise HTTPException(
            status_code=400,
            detail="Invalid ward_id",
        )

    ward_name = WARD_ID_TO_NAME[ward_id]

    latest_24 = latest_contiguous_24_hours(ward_name)

    input_values = latest_24["pm25"].to_numpy(
        dtype=np.float32
    ).reshape(-1, 1)

    if len(input_values) != 24:
        raise HTTPException(
            status_code=500,
            detail="Forecast input must contain exactly 24 hourly observations",
        )

    scaled_input = scaler.transform(input_values)

    model_input = scaled_input.reshape(1, 24, 1)

    scaled_prediction = model.predict(
        model_input,
        verbose=0,
    )[0]

    prediction = scaler.inverse_transform(
        scaled_prediction.reshape(-1, 1)
    ).reshape(-1)

    # PM2.5 cannot be negative.
    prediction = np.maximum(prediction, 0)

    last_observed = latest_24["datetime_utc"].iloc[-1]

    result = []

    for hour in range(1, hours + 1):
        forecast_ts = last_observed + pd.Timedelta(hours=hour)

        result.append(
            {
                "ts": forecast_ts.isoformat(),
                "value": round(float(prediction[hour - 1]), 2),
            }
        )

    return result
