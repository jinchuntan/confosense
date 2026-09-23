"""No-fit checks for the cross-fold matched interval adapter."""
from __future__ import annotations

import argparse
import copy
from pathlib import Path

from adapter import (
    REPO, SOURCE_HASH, authorized_bundle, data_api, digest, frozen,
    owner_references, select_owner, source_digest, bundle_paths,
)
from src.intervals005_common import Operations, frame, read, tree


def check_one(dataset: str, fold: int, seed: int) -> None:
    scope, _ = authorized_bundle(dataset, fold, seed)
    refs = owner_references(dataset, fold, seed, scope["horizons"])
    prepared = None
    parts = {}
    frequency = None
    with Operations(forbid=True):
        for horizon in scope["horizons"]:
            data, roles, prepared = data_api.load_data(refs[str(horizon)], prepared)
            frequency = data["freq"]
            parts[horizon] = {role: data_api.role_frame(data, roles[role])
                              for role in ("fit", "calibration", "test")}
            _, checks = data_api.historical_predictions(refs[str(horizon)], data, roles)
            if len(checks) != 2:
                raise ValueError("historical prediction parity not established")
        for role in ("fit", "calibration", "test"):
            joined = data_api.joint_join(
                {h: parts[h][role] for h in scope["horizons"]}, scope["horizons"],
                expected=data_api.expected_joint(dataset, fold, role), frequency=frequency)
            expected = frozen.scope_policy(dataset, fold)["joint_support"][role]
            if len(joined[scope["horizons"][0]]) != expected:
                raise ValueError("joint support count changed")
    print(f"PASS owner, predictions, and joint membership {dataset} f{fold} s{seed}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scope", choices=["pilot", "modern", "accepted", "all"], default="all")
    args = parser.parse_args()
    if source_digest() != SOURCE_HASH:
        raise ValueError("scientific source changed")
    candidates = {
        "pilot": ("pleia", 0, 42),
        "modern": ("bdg2", 1, 42),
        "accepted": ("bdg2", 2, 42),
    }
    for label, key in candidates.items():
        if args.scope in (label, "all"):
            check_one(*key) if label != "accepted" else check_accepted(*key)
    if args.scope == "all":
        check_rejections()


def check_rejections() -> None:
    from adapter import LEDGER
    ledger = frame(LEDGER)
    exact = select_owner(ledger, "pleia", 1, 0, 42)
    if "h1_f0_s42_xgboost" not in exact.model_owner_path:
        raise ValueError("wrong fold/seed/dataset owner selected")
    for key in (("pleia", 1, 0, 43), ("pleia", 1, 1, 42),
                ("pleia_energy", 1, 0, 42)):
        selected = select_owner(ledger, *key)
        if selected.model_owner_path == exact.model_owner_path:
            raise ValueError("owner key collapsed")
    duplicate = frame(LEDGER)
    duplicate = __import__("pandas").concat([duplicate, exact.to_frame().T], ignore_index=True)
    try:
        select_owner(duplicate, "pleia", 1, 0, 42)
    except ValueError:
        pass
    else:
        raise ValueError("ambiguous owner was accepted")
    refs = owner_references("pleia", 0, 42, [1])
    wrong = copy.deepcopy(refs["1"])
    wrong["owner_hashes"]["model.ubj"] = "0" * 64
    try:
        data_api.check_historical(wrong)
    except ValueError:
        pass
    else:
        raise ValueError("corrupt owner hash was accepted")
    for dataset, expected in (("pleia", "pleia_f2_s42_v1"),
                              ("pleia_energy", "pleia_energy_f2_s42_v2")):
        design, _ = bundle_paths(dataset, 2, 43)
        protocol = read(design / "frozen_protocol.json")
        alias = protocol["seasonal_alias_source"]
        if expected not in alias["root"] or "bdg2" in alias["root"]:
            raise ValueError("wrong seasonal source selected")
        for horizon, files in alias["files"].items():
            for name, expected_hash in files.items():
                if digest(REPO / alias["root"] / f"seasonal_h{horizon}" / name) != expected_hash:
                    raise ValueError("seasonal alias source hash mismatch")
    print("PASS wrong owner, corruption, ambiguity, and seasonal-alias rejection checks", flush=True)


def check_accepted(dataset: str, fold: int, seed: int) -> None:
    old = REPO / "smart_building_conformal/protocols/matched_intervals005/bdg2_f2_s42_v1/frozen_protocol.json"
    p = read(old)
    refs = owner_references(dataset, fold, seed, p["scope"]["horizons"])
    for horizon in p["scope"]["horizons"]:
        fresh, saved = refs[str(horizon)], p["references"][str(horizon)]
        if fresh["owner_hashes"] != saved["owner_hashes"] or fresh["source_hash"] != saved["source_hash"]:
            raise ValueError("new reference differs from accepted owner")
    run = REPO / "smart_building_conformal/outputs/matched_intervals005/bdg2_f2_s42_v1"
    with Operations(forbid=True):
        marker = read(run / "COMPLETE.json")
        actual = tree(run)
        actual.pop("COMPLETE.json")
        if actual != marker["files"]:
            raise ValueError("accepted artifact tree changed")
    print("PASS accepted-scope owner and saved-artifact zero-fit parity", flush=True)


if __name__ == "__main__":
    main()
