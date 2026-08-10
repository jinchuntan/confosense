"""Attention-LSTM point forecaster (PyTorch).

The network takes a fixed-length window of the recent multivariate series,
projects it, passes it through a single LSTM layer, pools the hidden states with
a learned temporal attention, and regresses the target at ``origin + horizon``.
One model is trained per horizon. Feature and target standardisation statistics
are estimated on the training window only; early stopping uses a chronological
validation slice taken from the end of the training data.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import torch
from torch import nn


def set_determinism(seed: int) -> None:
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)


def build_channel_matrix(df: pd.DataFrame, cfg: dict) -> tuple[np.ndarray, list[str]]:
    """Stack the raw channels the LSTM sees at every timestep."""
    channels = ["target"] + [c for c in cfg.get("covariates", []) if c in df.columns]
    mat = df[channels].to_numpy(dtype=float)

    # Per-timestep cyclical calendar context.
    idx = df.index
    hod = idx.hour + idx.minute / 60.0
    extra = np.column_stack([
        np.sin(2 * np.pi * hod / 24), np.cos(2 * np.pi * hod / 24),
        np.sin(2 * np.pi * idx.dayofweek / 7), np.cos(2 * np.pi * idx.dayofweek / 7),
    ])
    mat = np.column_stack([mat, extra])
    names = channels + ["hour_sin", "hour_cos", "dow_sin", "dow_cos"]
    return mat, names


def build_sequences(
    channel_matrix: np.ndarray,
    target: np.ndarray,
    seq_len: int,
    horizon: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (X_seq, y, origin_positions) for every valid, gap-free window."""
    n = len(target)
    xs, ys, pos = [], [], []
    for i in range(seq_len - 1, n - horizon):
        window = channel_matrix[i - seq_len + 1: i + 1]
        y = target[i + horizon]
        if not np.isfinite(window).all() or not np.isfinite(y):
            continue
        xs.append(window)
        ys.append(y)
        pos.append(i)
    if not xs:
        return (np.empty((0, seq_len, channel_matrix.shape[1])),
                np.empty((0,)), np.empty((0,), dtype=int))
    return np.asarray(xs, dtype=np.float32), np.asarray(ys, dtype=np.float32), np.asarray(pos, dtype=int)


class AttentionLSTM(nn.Module):
    def __init__(self, n_features: int, hidden: int = 64, dropout: float = 0.2):
        super().__init__()
        self.input_proj = nn.Linear(n_features, hidden)
        self.lstm = nn.LSTM(hidden, hidden, num_layers=1, batch_first=True)
        self.attn = nn.Linear(hidden, 1)
        self.dropout = nn.Dropout(dropout)
        self.head = nn.Linear(hidden, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = torch.tanh(self.input_proj(x))
        out, _ = self.lstm(h)
        scores = self.attn(out).squeeze(-1)
        weights = torch.softmax(scores, dim=1).unsqueeze(-1)
        context = self.dropout((out * weights).sum(dim=1))
        return self.head(context).squeeze(-1)


def _standardise(train: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mean = train.reshape(-1, train.shape[-1]).mean(axis=0)
    std = train.reshape(-1, train.shape[-1]).std(axis=0)
    std[std == 0] = 1.0
    return mean, std


def train_predict(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    cfg: dict,
    seed: int,
) -> dict:
    """Train the Attention-LSTM and predict on the test sequences.

    A chronological tail of the training data is held out for early stopping.
    Returns the test predictions (original scale) and the training history.
    """
    set_determinism(seed)
    device = torch.device("cpu")

    n = len(X_train)
    val_frac = cfg.get("val_fraction", 0.2)
    n_val = max(1, int(round(n * val_frac)))
    tr_x, tr_y = X_train[: n - n_val], y_train[: n - n_val]
    va_x, va_y = X_train[n - n_val:], y_train[n - n_val:]

    x_mean, x_std = _standardise(tr_x)
    y_mean, y_std = float(tr_y.mean()), float(tr_y.std() or 1.0)

    def prep_x(a: np.ndarray) -> torch.Tensor:
        return torch.tensor((a - x_mean) / x_std, dtype=torch.float32, device=device)

    def prep_y(a: np.ndarray) -> torch.Tensor:
        return torch.tensor((a - y_mean) / y_std, dtype=torch.float32, device=device)

    tr_xt, tr_yt = prep_x(tr_x), prep_y(tr_y)
    va_xt, va_yt = prep_x(va_x), prep_y(va_y)

    model = AttentionLSTM(
        n_features=X_train.shape[-1],
        hidden=cfg.get("hidden_size", 64),
        dropout=cfg.get("dropout", 0.2),
    ).to(device)
    optim = torch.optim.Adam(model.parameters(), lr=cfg.get("learning_rate", 1e-3))
    loss_fn = nn.MSELoss()

    batch = cfg.get("batch_size", 256)
    max_epochs = cfg.get("max_epochs", 30)
    patience = cfg.get("patience", 5)
    generator = torch.Generator().manual_seed(seed)

    best_val = float("inf")
    best_state = None
    epochs_no_improve = 0
    history = []

    for epoch in range(max_epochs):
        model.train()
        perm = torch.randperm(len(tr_xt), generator=generator)
        epoch_loss = 0.0
        for start in range(0, len(perm), batch):
            idx = perm[start: start + batch]
            optim.zero_grad()
            pred = model(tr_xt[idx])
            loss = loss_fn(pred, tr_yt[idx])
            loss.backward()
            optim.step()
            epoch_loss += float(loss.detach()) * len(idx)
        epoch_loss /= len(tr_xt)

        model.eval()
        with torch.no_grad():
            val_pred = model(va_xt)
            val_mae = float(torch.mean(torch.abs(val_pred - va_yt))) * y_std
        history.append({"epoch": epoch, "train_mse": epoch_loss, "val_mae": val_mae})

        if val_mae < best_val - 1e-6:
            best_val = val_mae
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= patience:
                break

    if best_state is not None:
        model.load_state_dict(best_state)

    model.eval()
    with torch.no_grad():
        test_pred_std = model(prep_x(X_test)).cpu().numpy()
    test_pred = test_pred_std * y_std + y_mean

    return {
        "predictions": test_pred,
        "history": history,
        "best_val_mae": best_val,
        "best_epoch": int(np.argmin([h["val_mae"] for h in history])),
        "n_epochs_run": len(history),
    }
