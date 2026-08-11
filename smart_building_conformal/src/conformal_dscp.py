"""Dual-Splitting Conformal Prediction (DSCP).

Reference
---------
Yu, Q., Cao, Z., Wang, R., Yang, Z., Deng, L., Hu, M., Luo, Y. and Zhou, X.
(2025). "Dual-splitting conformal prediction for multi-step time series
forecasting." *Applied Soft Computing*, 184(B), 113825.
DOI: 10.1016/j.asoc.2025.113825

Source used for this implementation
-----------------------------------
The Elsevier version is paywalled; this implementation was written against the
open-access author preprint, arXiv:2503.21251 (v1), retrieved 2026-08-10:
https://arxiv.org/abs/2503.21251 — https://arxiv.org/html/2503.21251v1

**No official author implementation could be located.** The paper gives no code
URL, and no repository matching the method or author list was found. Everything
below is therefore a from-the-paper implementation, not a port, and the mapping
between paper and code is documented explicitly so a reader can check it.

How the paper's method maps onto this code
------------------------------------------
The paper splits calibration error information along two axes, hence "dual".

*Vertical split* (:func:`_fit_clusters`)
    The *predicted* calibration sequences ``{K̂_i}`` are clustered with k-means;
    ``k`` is chosen by silhouette score over ``k = 2 .. max_clusters``. The paper
    scans from 1, but a silhouette score is undefined for a single cluster, so
    ``k = 1`` is handled as the explicit fallback when no split scores well.
    Clustering uses the *predictions*, never the ground truth — this is what
    makes test-time assignment possible without seeing the future.

*Horizontal split* (:func:`_merge_steps`, paper Algorithm 1)
    Within a cluster, the per-step signed-error sets of adjacent steps ``j`` and
    ``j+1`` are merged when a two-sample Kolmogorov-Smirnov test cannot
    distinguish them (``p > Θ``). Steps whose error distributions genuinely
    differ keep their own quantiles.

*Nonconformity score*
    ``ξ_{i,j} = K_{i,j} − K̂_{i,j}`` — the **signed** error, deliberately not the
    absolute error, so over- and under-prediction keep separate quantiles and the
    resulting interval may be asymmetric about the point forecast.

*Test-time assignment* (:func:`_assign_cluster`)
    For a test prediction ``K̂_τ`` the paper computes soft-DTW similarity to every
    calibration prediction, takes the ``s`` most similar, and assigns ``K̂_τ`` to
    the majority cluster among them. The paper fixes ``s`` as *the size of the
    smallest cluster*, which is what :func:`fit_dscp` uses when ``neighbours`` is
    left at ``None``; an explicit integer overrides it only for experiments that
    deliberately depart from the paper. Soft-DTW is implemented directly in NumPy
    rather than by adding a DTW dependency: :func:`soft_dtw` is the readable
    two-sequence form, and :func:`soft_dtw_to_bank` evaluates the same dynamic
    program against the whole calibration bank at once. They agree exactly; the
    banked form exists because the bank holds one row per calibration forecast
    origin — tens of thousands of them — and a per-row Python loop would make
    test-time assignment take hours for no numerical gain.

*Interval*
    ``[K̂_τ + Q_{α/2}(Ẽ_β), K̂_τ + Q_{1−α/2}(Ẽ_β)]`` where ``Ẽ_β`` is the merged
    error set for that step in that cluster.

Adaptation to ConfoSense's direct multi-horizon design (documented deviation)
----------------------------------------------------------------------------
The paper assumes one model emitting ``b`` steps at once. ConfoSense trains a
*separate direct model per horizon* (h = 1, 3, 6 ...). The sequence ``K̂_i`` is
therefore assembled across horizon models sharing a forecast origin:
``K̂_i = [ŷ_{t+h_1}, ..., ŷ_{t+h_b}]``. This preserves everything the method
relies on — a per-origin multi-step prediction vector, per-step error sets, and
step adjacency for the horizontal merge — while keeping ConfoSense's direct
forecasting design. It is a genuine deviation from the paper's setting and is
recorded as such in the limitations report.

Assumptions (from the paper; asserted nowhere in the tests)
-----------------------------------------------------------
Calibration and test samples within a cluster are exchangeable; error
distributions are stable inside a merged step window. Neither holds exactly for
non-stationary building data, so the tests below check *mechanics* — splitting,
ordering, shape, determinism — and never assert nominal coverage.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

DEFAULT_KS_THRESHOLD = 0.05


# --------------------------------------------------------------------------- #
# soft-DTW
# --------------------------------------------------------------------------- #
def _soft_min(a: float, b: float, c: float, gamma: float) -> float:
    if gamma <= 0:
        return min(a, b, c)
    v = np.array([a, b, c], dtype=float)
    vmin = v.min()
    return float(vmin - gamma * np.log(np.sum(np.exp(-(v - vmin) / gamma))))


def soft_dtw(x: np.ndarray, y: np.ndarray, gamma: float = 1.0) -> float:
    """Soft-DTW discrepancy between two 1-D sequences (Cuturi & Blondel, 2017).

    ``gamma -> 0`` recovers classical DTW. Implemented directly because the
    sequences compared here are only a few steps long, so pulling in a
    dedicated DTW library would not be justified.
    """
    x = np.asarray(x, dtype=float).ravel()
    y = np.asarray(y, dtype=float).ravel()
    n, m = len(x), len(y)
    D = np.full((n + 1, m + 1), np.inf)
    D[0, 0] = 0.0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = (x[i - 1] - y[j - 1]) ** 2
            D[i, j] = cost + _soft_min(D[i - 1, j], D[i, j - 1], D[i - 1, j - 1], gamma)
    return float(D[n, m])


def _soft_min_rows(a: np.ndarray, b: np.ndarray, c: np.ndarray,
                   gamma: float) -> np.ndarray:
    """``_soft_min`` applied across a whole bank of sequences at once."""
    if gamma <= 0:
        return np.minimum(np.minimum(a, b), c)
    stack = np.stack([a, b, c])
    vmin = stack.min(axis=0)
    finite = np.isfinite(vmin)
    out = np.array(vmin, dtype=float)
    if finite.any():
        shifted = np.exp(-(stack[:, finite] - vmin[finite]) / gamma)
        out[finite] = vmin[finite] - gamma * np.log(shifted.sum(axis=0))
    return out


def soft_dtw_to_bank(x: np.ndarray, bank: np.ndarray, gamma: float = 1.0) -> np.ndarray:
    """Soft-DTW from one sequence to every row of ``bank``, vectorised.

    Mathematically identical to calling :func:`soft_dtw` once per row, but the
    dynamic program is evaluated across the whole bank simultaneously. That
    matters: the calibration bank holds one row per forecast origin — tens of
    thousands of them — so the per-row Python loop turns test-time assignment
    into hours of work for no numerical benefit.
    """
    x = np.asarray(x, dtype=float).ravel()
    bank = np.atleast_2d(np.asarray(bank, dtype=float))
    n_seq, m = bank.shape
    n = len(x)

    prev = np.full((m + 1, n_seq), np.inf)
    prev[0] = 0.0
    for i in range(1, n + 1):
        cur = np.full((m + 1, n_seq), np.inf)
        for j in range(1, m + 1):
            cost = (x[i - 1] - bank[:, j - 1]) ** 2
            cur[j] = cost + _soft_min_rows(prev[j], cur[j - 1], prev[j - 1], gamma)
        prev = cur
    return prev[m]


# --------------------------------------------------------------------------- #
# Fitted calibrator
# --------------------------------------------------------------------------- #
@dataclass
class DSCPCalibrator:
    """Fitted DSCP state: clusters, merged per-step error sets, and metadata."""

    horizons: list[int]
    cluster_labels: np.ndarray                  # per calibration sample
    calib_predictions: np.ndarray               # (m, b) predicted sequences
    merged_errors: dict[int, list[np.ndarray]]  # cluster -> per-step error pool
    merge_map: dict[int, list[int]]             # cluster -> step -> group id
    n_clusters: int
    silhouette: float
    ks_threshold: float
    neighbours: int
    gamma: float
    metadata: dict = field(default_factory=dict)

    @property
    def n_steps(self) -> int:
        return len(self.horizons)

    def _assign_cluster(self, sequence: np.ndarray) -> int:
        """Majority cluster among the ``s`` most soft-DTW-similar calibration rows."""
        if self.n_clusters == 1:
            return 0
        dists = soft_dtw_to_bank(sequence, self.calib_predictions, self.gamma)
        s = min(self.neighbours, len(dists))
        nearest = np.argpartition(dists, s - 1)[:s]
        counts = np.bincount(self.cluster_labels[nearest], minlength=self.n_clusters)
        return int(np.argmax(counts))

    def _step_quantiles(self, level: float) -> np.ndarray:
        """``(n_clusters, n_steps, 2)`` signed error quantiles.

        Each merged error pool is fixed at fit time, so its quantiles do not
        depend on the test sample. Computing them once per cluster and step
        rather than once per test row is a pure restructuring — the numbers are
        identical — but it removes a quantile call over a large pool from the
        inner loop.
        """
        alpha = 1.0 - level
        q = np.empty((self.n_clusters, self.n_steps, 2), dtype=float)
        for c in range(self.n_clusters):
            for j in range(self.n_steps):
                pool = self.merged_errors[c][j]
                q[c, j, 0] = float(np.quantile(pool, alpha / 2.0))
                q[c, j, 1] = float(np.quantile(pool, 1.0 - alpha / 2.0))
        return q

    def assign(self, predictions: np.ndarray) -> np.ndarray:
        """Cluster index for every row of ``predictions``.

        Exposed separately because assignment depends only on the predicted
        sequence, not on the coverage level: a caller producing 90% and 95%
        bands from the same forecasts should pay the soft-DTW cost once and pass
        the result back through :meth:`predict_interval`.
        """
        predictions = np.atleast_2d(np.asarray(predictions, dtype=float))
        if self.n_clusters == 1:
            return np.zeros(len(predictions), dtype=int)
        return np.array([self._assign_cluster(seq) for seq in predictions], dtype=int)

    def predict_interval(self, predictions: np.ndarray, level: float,
                         assignments: np.ndarray | None = None) -> dict:
        """Intervals for test predictions shaped ``(n_test, n_steps)``.

        Returns per-step ``lower``/``upper`` arrays of the same shape, plus the
        cluster each test sample was assigned to. Pass ``assignments`` from a
        previous :meth:`assign` call to skip recomputing them.
        """
        predictions = np.atleast_2d(np.asarray(predictions, dtype=float))
        if predictions.shape[1] != self.n_steps:
            raise ValueError(
                f"expected {self.n_steps} steps per sequence, got {predictions.shape[1]}"
            )
        quantiles = self._step_quantiles(level)

        if assignments is None:
            assigned = self.assign(predictions)
        else:
            assigned = np.asarray(assignments, dtype=int)
            if len(assigned) != len(predictions):
                raise ValueError("assignments length does not match predictions")

        offsets = quantiles[assigned]                     # (n_test, n_steps, 2)
        lower = predictions + offsets[:, :, 0]
        upper = predictions + offsets[:, :, 1]

        # Signed quantiles are monotone by construction, but guard against a
        # degenerate single-element pool producing a zero-width inversion.
        upper = np.maximum(upper, lower)
        return {"lower": lower, "upper": upper, "point": predictions,
                "cluster": assigned}


# --------------------------------------------------------------------------- #
# Fitting
# --------------------------------------------------------------------------- #
def _fit_clusters(sequences: np.ndarray, max_clusters: int, seed: int,
                  silhouette_sample: int = 2000) -> tuple[np.ndarray, int, float]:
    """Vertical split: k-means over predicted sequences, k by silhouette.

    ``silhouette_score`` builds a full pairwise distance matrix, so its cost is
    quadratic in the number of calibration sequences — tens of thousands here,
    which would mean a 10^8-entry matrix for every candidate ``k``. It is
    therefore evaluated on a fixed-size random subsample drawn with the run's own
    seed. The clustering itself still uses every sequence; only the model-
    selection score is estimated, and it is estimated deterministically.
    """
    n = len(sequences)
    upper = min(max_clusters, n - 1)
    if n < 4 or upper < 2:
        return np.zeros(n, dtype=int), 1, float("nan")

    sample = min(silhouette_sample, n) if n > silhouette_sample else None
    best_labels, best_k, best_score = np.zeros(n, dtype=int), 1, -np.inf
    for k in range(2, upper + 1):
        km = KMeans(n_clusters=k, n_init=10, random_state=seed)
        labels = km.fit_predict(sequences)
        if len(np.unique(labels)) < 2:
            continue
        score = float(silhouette_score(sequences, labels,
                                       sample_size=sample, random_state=seed))
        if score > best_score:
            best_labels, best_k, best_score = labels, k, score

    # A poor silhouette means the sequences do not separate; fall back to the
    # single-cluster case, which reduces DSCP to per-step split conformal.
    if best_score <= 0.0:
        return np.zeros(n, dtype=int), 1, best_score
    return best_labels, best_k, best_score


def _merge_steps(step_errors: list[np.ndarray], threshold: float) -> tuple[list[np.ndarray], list[int]]:
    """Horizontal split (paper Algorithm 1): merge adjacent similar steps.

    Walks the steps in order, accumulating a run while consecutive error sets
    are statistically indistinguishable under a two-sample KS test, then assigns
    the pooled errors back to every step in that run.
    """
    b = len(step_errors)
    if b == 1:
        return [step_errors[0]], [0]

    groups: list[list[int]] = [[0]]
    for j in range(1, b):
        prev, cur = step_errors[j - 1], step_errors[j]
        if len(prev) >= 2 and len(cur) >= 2:
            p = float(stats.ks_2samp(prev, cur).pvalue)
        else:
            p = 1.0  # too few points to distinguish; keep them together
        if p > threshold:
            groups[-1].append(j)
        else:
            groups.append([j])

    merged: list[np.ndarray] = [np.empty(0)] * b
    group_of: list[int] = [0] * b
    for gid, members in enumerate(groups):
        pool = np.concatenate([step_errors[j] for j in members])
        for j in members:
            merged[j] = pool
            group_of[j] = gid
    return merged, group_of


def fit_dscp(
    calib_predictions: np.ndarray,
    calib_truth: np.ndarray,
    horizons: list[int],
    *,
    max_clusters: int = 6,
    ks_threshold: float = DEFAULT_KS_THRESHOLD,
    neighbours: int | None = None,
    gamma: float = 1.0,
    seed: int = 42,
) -> DSCPCalibrator:
    """Fit DSCP on calibration predictions and truths.

    Parameters
    ----------
    calib_predictions, calib_truth
        ``(m, b)`` arrays: one row per forecast origin, one column per horizon
        in ``horizons`` order. Only calibration data may be passed here.
    neighbours
        Number of soft-DTW neighbours used for test-time cluster assignment.
        ``None`` (the default) follows the paper, which sets it to the size of
        the smallest cluster; an integer overrides that.
    """
    P = np.atleast_2d(np.asarray(calib_predictions, dtype=float))
    Y = np.atleast_2d(np.asarray(calib_truth, dtype=float))
    if P.shape != Y.shape:
        raise ValueError(f"prediction/truth shape mismatch: {P.shape} vs {Y.shape}")
    if P.shape[1] != len(horizons):
        raise ValueError(f"expected {len(horizons)} columns, got {P.shape[1]}")
    if len(P) < 2:
        raise ValueError("DSCP needs at least two calibration sequences")

    errors = Y - P                                   # signed, paper eq. for xi
    labels, k, sil = _fit_clusters(P, max_clusters, seed)

    # Paper: s is the size of the smallest cluster. Deriving it here rather than
    # hard-coding a constant keeps the neighbourhood proportionate to how finely
    # the calibration set actually split.
    neighbours_auto = neighbours is None
    if neighbours is None:
        counts = np.bincount(labels, minlength=k)
        counts = counts[counts > 0]
        neighbours = int(counts.min()) if len(counts) else 1
    neighbours = max(1, int(neighbours))

    merged_errors, merge_map = {}, {}
    for c in range(k):
        rows = labels == c
        if not rows.any():
            rows = np.ones(len(P), dtype=bool)       # never leave a cluster empty
        step_errors = [errors[rows, j] for j in range(P.shape[1])]
        merged, group_of = _merge_steps(step_errors, ks_threshold)
        merged_errors[c] = merged
        merge_map[c] = group_of

    return DSCPCalibrator(
        horizons=list(horizons),
        cluster_labels=labels,
        calib_predictions=P,
        merged_errors=merged_errors,
        merge_map=merge_map,
        n_clusters=k,
        silhouette=sil,
        ks_threshold=ks_threshold,
        neighbours=neighbours,
        gamma=gamma,
        metadata={
            "n_calibration": int(len(P)),
            "reference": "Yu et al. 2025, Applied Soft Computing 184:113825",
            "implementation_source": "arXiv:2503.21251v1 (no official code found)",
            "nonconformity": "signed error y - yhat",
            "direct_horizon_adaptation": True,
            "neighbours_rule": ("smallest cluster size (paper)"
                                if neighbours_auto else "explicit override"),
            "neighbours_used": int(neighbours),
            "cluster_sizes": np.bincount(labels, minlength=k).tolist(),
        },
    )
