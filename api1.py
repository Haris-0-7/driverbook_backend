from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import uvicorn

app = FastAPI(title="Fleet Fuel CSV API")

# -----------------------------
# CORS setup
# -----------------------------
origins = [
    "http://localhost:5173","https://driverbook.netlify.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# CSV folder
# -----------------------------
DATA_FOLDER = "./data/"

@app.get("/")
def health_check():
    return {"message": "API is working 🚀"}

@app.get("/latest-record")
def get_latest_record(vehicleId: str = Query(..., description="Vehicle ID to fetch latest record")):
    try:
        CSV_FILE = f"{DATA_FOLDER}{vehicleId}.csv"

        # Read CSV
        df = pd.read_csv(CSV_FILE)

        # Replace NaN / inf / -inf with None (JSON compliant)
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.where(pd.notnull(df), None)

        # Ensure timestamp column exists
        if "timestamp" not in df.columns:
            return JSONResponse(
                content={"error": "'timestamp' column not found in CSV"},
                status_code=400
            )

        # Sort by timestamp to find latest row
        df_sorted = df.sort_values("timestamp")

        # Get latest row
        latest_row = df_sorted.iloc[-1].to_dict()

        # Single line JSON-safe conversion
        safe_latest = {}
        for k, v in latest_row.items():
            if pd.isna(v):
                safe_latest[k] = None
            elif isinstance(v, (int, float, np.integer, np.floating)):
                if np.isinf(v):
                    safe_latest[k] = None
                else:
                    safe_latest[k] = float(v)
            else:
                safe_latest[k] = v
        latest_row = safe_latest

        # Get all historical fuelLevel_pct as list
        if "fuelLevel_pct" in df_sorted.columns:
            latest_row["fuelLevel_pct"] = [
                float(x) if pd.notnull(x) else None for x in df_sorted["fuelLevel_pct"]
            ]

        return JSONResponse(content=latest_row)

    except FileNotFoundError:
        return JSONResponse(
            content={"error": f"CSV file for vehicleId {vehicleId} not found"},
            status_code=404
        )
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


# -----------------------------
# Return all rows for vehicle CSV using query param
# -----------------------------
@app.get("/all-records")
def get_all_records(vehicleId: str = Query(..., description="Vehicle ID to fetch all records")):
    try:
        CSV_FILE = f"{DATA_FOLDER}{vehicleId}.csv"

        # Read CSV
        df = pd.read_csv(CSV_FILE)

        # JSON-safe conversion row by row
        records = []
        for _, row in df.iterrows():
            safe_row = {}
            for col, val in row.items():
                if pd.isna(val):
                    safe_row[col] = None
                elif isinstance(val, (int, float, np.integer, np.floating)):
                    if np.isinf(val):
                        safe_row[col] = None
                    else:
                        safe_row[col] = float(val)
                else:
                    safe_row[col] = val
            records.append(safe_row)

        return JSONResponse(content=records)

    except FileNotFoundError:
        return JSONResponse(
            content={"error": f"CSV file for vehicleId {vehicleId} not found"},
            status_code=404
        )
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)