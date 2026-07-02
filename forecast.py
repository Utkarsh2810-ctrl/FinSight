"""
api/routes/forecast.py
----------------------
POST /api/forecast — trains LSTM and returns next-quarter revenue prediction.

Note on latency:
    LSTM training takes 5-60 seconds depending on the ticker's data volume
    and configured epochs. The route runs synchronously in a thread pool
    (via run_in_executor) so it doesn't block the FastAPI event loop.
"""

import asyncio
import sys
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from loguru import logger
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.forecasting.lstm_forecaster import run_forecast

router = APIRouter()
_executor = ThreadPoolExecutor(max_workers=2)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ForecastRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=10, description="e.g. AAPL, MSFT, GOOGL")


class PredictionResult(BaseModel):
    predicted_revenue: float
    last_actual_revenue: float
    qoq_growth_pct: float


class RevenuePoint(BaseModel):
    date: str
    revenue: float


class ForecastResponse(BaseModel):
    ticker: str
    n_quarters: int
    history: List[RevenuePoint]
    train_losses: List[float]
    val_losses: List[float]
    prediction: PredictionResult
    features_used: List[str]


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@router.post("/forecast", response_model=ForecastResponse)
async def forecast(body: ForecastRequest, request: Request):
    """
    Fetches quarterly financials for the given ticker, trains an LSTM,
    and predicts the next quarter's revenue.

    The training loop runs in a background thread to avoid blocking the
    async event loop (PyTorch training is CPU-bound, not I/O-bound).
    """
    ticker = body.ticker.strip().upper()
    config = request.app.state.config

    logger.info(f"Forecast requested for ticker={ticker}")

    loop = asyncio.get_event_loop()
    fn = partial(run_forecast, ticker, config)

    try:
        result = await loop.run_in_executor(_executor, fn)
    except ValueError as e:
        # Business logic errors (not enough data, bad ticker, etc.)
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Forecast failed for ticker={ticker}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Forecasting failed for {ticker}: {str(e)}"
        )

    logger.info(
        f"Forecast complete for {ticker} | "
        f"predicted_revenue={result['prediction']['predicted_revenue']:,.0f} | "
        f"qoq={result['prediction']['qoq_growth_pct']:+.2f}%"
    )

    return ForecastResponse(**result)
