"""
lstm_forecaster.py
------------------
Layer 4 — LSTM-based next-quarter revenue forecasting.

Pipeline:
    ticker → fetch_and_preprocess (yfinance)
           → normalize (MinMaxScaler)
           → create_sequences (sliding window)
           → FinancialDataset + DataLoader
           → train (LSTM training loop with early stopping + gradient clipping)
           → predict_next_quarter (inference + inverse transform)

Why LSTM over Transformer:
    Quarterly financial data gives ~20-40 data points per ticker.
    Transformers are data-hungry (attention learns O(n²) pair relationships).
    LSTM with proper regularisation (dropout, gradient clipping) generalises
    better in this small-data regime. A Transformer here would overfit severely.

Why gradient clipping:
    LSTM hidden states can accumulate large gradients over long sequences
    (the vanishing/exploding gradient problem). Clipping the global gradient
    norm prevents weight updates from destabilising training.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import yfinance as yf
from loguru import logger
from sklearn.preprocessing import MinMaxScaler
from torch.utils.data import DataLoader, Dataset


# ---------------------------------------------------------------------------
# Model  (✍️ write this yourself — must be able to explain every line)
# ---------------------------------------------------------------------------

class FinancialLSTM(nn.Module):
    """
    Stacked LSTM for one-step-ahead quarterly revenue forecasting.

    Input:  (batch, seq_len, input_size)  — sequence of quarterly financials
    Output: (batch, 1)                    — predicted next-quarter revenue (scaled)

    Why last-timestep output only:
        One-step-ahead forecasting, not sequence-to-sequence.
        The LSTM hidden state h_T at the final timestep encodes the full
        sequence history through the recurrent connections. Using h_T alone
        (not all hidden states) is sufficient and avoids aggregation choices.
    """

    def __init__(
        self,
        input_size: int,
        hidden_size: int,
        num_layers: int,
        dropout: float,
    ) -> None:
        super().__init__()

        # nn.LSTM's `dropout` applies between stacked layers, NOT after the
        # final layer. Single-layer LSTMs must pass dropout=0 here.
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0.0,
            batch_first=True,
        )

        # Separate dropout after the last LSTM layer (always applied)
        self.dropout = nn.Dropout(p=dropout)

        # Linear head: maps final hidden state → scalar revenue prediction
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, seq_len, input_size)
        lstm_out, _ = self.lstm(x)           # (batch, seq_len, hidden_size)
        last_hidden = lstm_out[:, -1, :]     # (batch, hidden_size)
        dropped = self.dropout(last_hidden)
        return self.fc(dropped)              # (batch, 1)


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------

class FinancialDataset(Dataset):
    """
    PyTorch Dataset wrapping (X, y) sequence arrays.

    X: (n_samples, seq_len, n_features)
    y: (n_samples, 1)
    """

    def __init__(self, X: np.ndarray, y: np.ndarray) -> None:
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.float32)

    def __len__(self) -> int:
        return len(self.X)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        return self.X[idx], self.y[idx]


# ---------------------------------------------------------------------------
# Data pipeline  (✍️ write this yourself)
# ---------------------------------------------------------------------------

def fetch_and_preprocess(
    ticker: str,
    features: List[str],
) -> pd.DataFrame:
    """
    Fetches quarterly financials from yfinance and returns a clean DataFrame.

    Args:
        ticker   : e.g. "AAPL", "MSFT"
        features : list of column names to extract

    Returns:
        DataFrame with columns = features, rows sorted ascending by date,
        no NaN rows.
    """
    t = yf.Ticker(ticker)
    qf = t.quarterly_financials  # columns=dates, index=metrics

    if qf is None or qf.empty:
        raise ValueError(f"yfinance returned no quarterly financials for ticker={ticker}")

    # Transpose → rows=dates, cols=metrics; sort chronologically
    df = qf.T.sort_index(ascending=True)

    # Keep only the configured features, drop unavailable ones with warning
    available = [f for f in features if f in df.columns]
    missing = set(features) - set(available)
    if missing:
        logger.warning(f"Features not available for {ticker}: {missing}")
    if not available:
        raise ValueError(f"None of the configured features are available for {ticker}")

    df = df[available].dropna()
    logger.info(f"Fetched {len(df)} quarters of data for {ticker} | features: {available}")
    return df


def normalize(df: pd.DataFrame) -> Tuple[np.ndarray, MinMaxScaler]:
    """
    Fits a MinMaxScaler on the full dataset and transforms.

    Returns:
        (scaled_array, scaler)

    The scaler is returned so it can be used to inverse-transform predictions.
    It is fit on ALL data (not just train) because we need consistent scaling
    for the final prediction step. For production, fit only on train split.
    """
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled = scaler.fit_transform(df.values.astype(np.float32))
    return scaled, scaler


def create_sequences(
    data: np.ndarray,
    seq_len: int,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Builds sliding-window sequences for LSTM training.

    For each window of `seq_len` timesteps, the target y is the
    Total Revenue (first feature, index 0) of the NEXT timestep.

    X shape: (n_samples, seq_len, n_features)
    y shape: (n_samples, 1)
    """
    X, y = [], []
    for i in range(len(data) - seq_len):
        X.append(data[i : i + seq_len])        # seq_len quarters as input
        y.append(data[i + seq_len, 0:1])       # next quarter's revenue (col 0)
    return np.array(X), np.array(y)


# ---------------------------------------------------------------------------
# Training loop  (✍️ write this yourself — must explain every decision)
# ---------------------------------------------------------------------------

def train(
    model: FinancialLSTM,
    train_loader: DataLoader,
    val_loader: DataLoader,
    config: Dict[str, Any],
    checkpoint_dir: str,
    ticker: str,
) -> Dict[str, List[float]]:
    """
    Full training loop with:
        - Adam optimiser
        - MSE loss
        - Gradient clipping (prevents exploding gradients in LSTM)
        - Checkpoint saving on val loss improvement
        - Early stopping (patience-based)

    Args:
        model          : FinancialLSTM instance
        train_loader   : DataLoader for training split
        val_loader     : DataLoader for validation split
        config         : full config dict (uses config["forecasting"])
        checkpoint_dir : directory to save best model checkpoint
        ticker         : used to name the checkpoint file

    Returns:
        {"train_losses": [...], "val_losses": [...]}
    """
    cfg = config["forecasting"]
    epochs = cfg["epochs"]
    lr = cfg["lr"]
    grad_clip = cfg["grad_clip"]
    patience = cfg["early_stopping_patience"]

    optimiser = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()

    Path(checkpoint_dir).mkdir(parents=True, exist_ok=True)
    checkpoint_path = Path(checkpoint_dir) / f"{ticker}_best.pt"

    train_losses, val_losses = [], []
    best_val_loss = float("inf")
    epochs_without_improvement = 0

    for epoch in range(1, epochs + 1):
        # --- Training ---
        model.train()
        epoch_train_loss = 0.0
        for X_batch, y_batch in train_loader:
            optimiser.zero_grad()
            preds = model(X_batch)
            loss = criterion(preds, y_batch)
            loss.backward()

            # Clip gradients: prevents exploding gradient problem in deep LSTMs.
            # max_norm=1.0 is a standard default for financial time series.
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=grad_clip)

            optimiser.step()
            epoch_train_loss += loss.item()

        avg_train_loss = epoch_train_loss / len(train_loader)
        train_losses.append(avg_train_loss)

        # --- Validation ---
        model.eval()
        epoch_val_loss = 0.0
        with torch.no_grad():
            for X_batch, y_batch in val_loader:
                preds = model(X_batch)
                loss = criterion(preds, y_batch)
                epoch_val_loss += loss.item()

        avg_val_loss = epoch_val_loss / len(val_loader)
        val_losses.append(avg_val_loss)

        if epoch % 10 == 0 or epoch == 1:
            logger.info(
                f"Epoch {epoch:03d}/{epochs} | "
                f"train_loss={avg_train_loss:.6f} | "
                f"val_loss={avg_val_loss:.6f}"
            )

        # --- Checkpoint on improvement ---
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            torch.save(model.state_dict(), checkpoint_path)
            epochs_without_improvement = 0
        else:
            epochs_without_improvement += 1

        # --- Early stopping ---
        if epochs_without_improvement >= patience:
            logger.info(f"Early stopping at epoch {epoch} (no improvement for {patience} epochs)")
            break

    # Reload best weights
    model.load_state_dict(torch.load(checkpoint_path, weights_only=True))
    logger.info(f"Best model loaded from {checkpoint_path} (best_val_loss={best_val_loss:.6f})")

    return {"train_losses": train_losses, "val_losses": val_losses}


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------

def predict_next_quarter(
    model: FinancialLSTM,
    last_sequence: np.ndarray,
    scaler: MinMaxScaler,
) -> Dict[str, Any]:
    """
    Predicts the next quarter's revenue using the last available sequence.

    Args:
        model         : trained FinancialLSTM (best checkpoint loaded)
        last_sequence : shape (seq_len, n_features) — the most recent window
        scaler        : the fitted MinMaxScaler (for inverse transform)

    Returns:
        {
            "predicted_revenue"  : float (original scale, USD),
            "last_actual_revenue": float (original scale, USD),
            "qoq_growth_pct"     : float (quarter-over-quarter growth %),
        }
    """
    model.eval()
    with torch.no_grad():
        x = torch.tensor(last_sequence, dtype=torch.float32).unsqueeze(0)  # (1, seq_len, features)
        scaled_pred = model(x).item()  # scalar in [0, 1]

    # Inverse-transform: reconstruct a full-width dummy row to use scaler.inverse_transform
    n_features = last_sequence.shape[1]
    dummy = np.zeros((1, n_features), dtype=np.float32)
    dummy[0, 0] = scaled_pred
    predicted_revenue = scaler.inverse_transform(dummy)[0, 0]

    # Last actual revenue (most recent quarter, revenue column)
    dummy_actual = np.zeros((1, n_features), dtype=np.float32)
    dummy_actual[0, 0] = last_sequence[-1, 0]  # last timestep, revenue col
    last_actual = scaler.inverse_transform(dummy_actual)[0, 0]

    qoq_pct = ((predicted_revenue - last_actual) / abs(last_actual)) * 100 if last_actual != 0 else 0.0

    return {
        "predicted_revenue": float(predicted_revenue),
        "last_actual_revenue": float(last_actual),
        "qoq_growth_pct": round(float(qoq_pct), 2),
    }


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def run_forecast(ticker: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Full forecasting pipeline for a given ticker.

    Returns:
        {
            "ticker"        : str,
            "n_quarters"    : int,
            "history"       : List[{"date": str, "revenue": float}],
            "train_losses"  : List[float],
            "val_losses"    : List[float],
            "prediction"    : {predicted_revenue, last_actual_revenue, qoq_growth_pct},
            "features_used" : List[str],
        }
    """
    cfg = config["forecasting"]
    features: List[str] = cfg["features"]
    seq_len: int = cfg["seq_len"]

    # 1. Fetch & preprocess
    df = fetch_and_preprocess(ticker, features)

    if len(df) < seq_len + 2:
        raise ValueError(
            f"Insufficient data for {ticker}: need ≥{seq_len + 2} quarters, got {len(df)}. "
            "Try a larger ticker with more earnings history."
        )

    # Save revenue history for chart display (before scaling)
    history = [
        {"date": str(idx.date()), "revenue": float(row["Total Revenue"])}
        for idx, row in df.iterrows()
        if "Total Revenue" in df.columns
    ]

    # 2. Normalise
    scaled, scaler = normalize(df)

    # 3. Sequences
    X, y = create_sequences(scaled, seq_len)

    # 4. Train/val split (no shuffle — time series!)
    split = int(len(X) * cfg["train_val_split"])
    if split == 0:
        split = 1  # at minimum 1 training sample

    X_train, X_val = X[:split], X[split:]
    y_train, y_val = y[:split], y[split:]

    # If val set is empty (very little data), reuse train as val
    if len(X_val) == 0:
        X_val, y_val = X_train, y_train
        logger.warning("Val set empty — reusing train set for validation (data is very limited)")

    train_ds = FinancialDataset(X_train, y_train)
    val_ds = FinancialDataset(X_val, y_val)

    batch_size = min(cfg["batch_size"], len(train_ds))
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=False)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    # 5. Model
    n_features = scaled.shape[1]
    model = FinancialLSTM(
        input_size=n_features,
        hidden_size=cfg["hidden_size"],
        num_layers=cfg["num_layers"],
        dropout=cfg["dropout"],
    )

    # 6. Train
    checkpoint_dir = cfg.get("checkpoint_dir", "./checkpoints")
    history_losses = train(model, train_loader, val_loader, config, checkpoint_dir, ticker)

    # 7. Predict using the last seq_len quarters
    last_sequence = scaled[-seq_len:]
    prediction = predict_next_quarter(model, last_sequence, scaler)

    return {
        "ticker": ticker,
        "n_quarters": len(df),
        "history": history,
        "train_losses": history_losses["train_losses"],
        "val_losses": history_losses["val_losses"],
        "prediction": prediction,
        "features_used": features,
    }
