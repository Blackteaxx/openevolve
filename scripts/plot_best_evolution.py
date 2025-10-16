"""
Plot the evolution of best programs across multiple experimental settings.

Usage:
    python scripts/plot_best_evolution.py \
        --dirs DIR1 DIR2 ... \
        --labels "Setting A" "Setting B" ... \
        --metric combined_score \
        --output artifacts/multi_best_evolution.png \
        [--title "Best Program Evolution"]

Inputs:
- Each DIR should point to a directory containing program JSON files.
  Typical paths:
    - .../openevolve_output/checkpoints/checkpoint_XX/programs
    - Or any folder with multiple `*.json` program entries.

Sorting:
- Primary: `iteration_found` (ascending)
- Fallback: `timestamp` (ascending), then file modification time
- Final tie-breaker: stable sort by `id` (ascending)

Line Chart:
- X-axis: iteration_found when available, else sequential index
- Y-axis: chosen metric (default: combined_score)
- Series: one per input directory

"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional


def _safe_float(x: object) -> Optional[float]:
    """Convert value to float; return None on failure or non-numeric strings like 'Infinity'."""
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str):
        if x.lower() in {"inf", "+inf", "infinity", "+infinity"}:
            return float("inf")
        if x.lower() in {"-inf", "-infinity"}:
            return float("-inf")
        try:
            return float(x)
        except ValueError:
            return None
    return None


def load_programs_from_dir(dir_path: Path) -> List[Dict]:
    """Load all program JSON files from a directory.

    If the directory contains a `programs` subdirectory, use that.
    Otherwise, read `*.json` files directly from the given directory.
    """
    p = Path(dir_path)
    if not p.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")

    programs_dir = p / "programs"
    scan_dir = programs_dir if programs_dir.exists() else p

    items: List[Dict] = []
    for jf in sorted(scan_dir.glob("*.json")):
        # Skip summary info files if present
        if jf.name.endswith("best_program_info.json"):
            continue
        try:
            with open(jf, "r") as f:
                data = json.load(f)
                # Attach path for mtime fallback
                data["_file_path"] = str(jf)
                items.append(data)
        except Exception:
            # Skip unreadable / malformed files
            continue

    return items


def sort_programs(programs: List[Dict]) -> List[Dict]:
    """Sort programs by iteration_found (primary), then timestamp, then file mtime, then id.

    - If `iteration_found` is missing, we sort that entry by timestamp/mtime and place it
      after entries with iteration_found using a two-level tuple key.
    """

    def sort_key(prog: Dict) -> Tuple[int, float, float, str]:
        iteration = prog.get("iteration_found")
        # Some older schemas may use 'iteration'
        if iteration is None:
            iteration = prog.get("iteration")

        # Timestamp fallback chain: timestamp -> saved_at -> file mtime -> 0
        ts = _safe_float(prog.get("timestamp"))
        if ts is None:
            ts = _safe_float(prog.get("saved_at"))
        if ts is None:
            try:
                ts = float(os.path.getmtime(prog.get("_file_path", "")))
            except Exception:
                ts = 0.0

        # mtime for tie-breaking after timestamp
        try:
            mtime = float(os.path.getmtime(prog.get("_file_path", "")))
        except Exception:
            mtime = ts

        # Place entries with iteration first (flag=0), otherwise after (flag=1)
        flag = 0 if isinstance(iteration, (int, float)) else 1
        iter_value = float(iteration) if isinstance(iteration, (int, float)) else ts
        prog_id = str(prog.get("id", ""))
        return (flag, iter_value, ts if ts is not None else 0.0, prog_id)

    return sorted(programs, key=sort_key)


def build_best_series(programs: List[Dict], metric: str) -> Tuple[List[float], List[float]]:
    """Build X (iteration) and Y (best-so-far metric) series.

    - For `trimmed_mean_runtime`, smaller is better; for others, higher is better.
    - X-axis uses `iteration_found` when present; else sequential index starting from 1.
    """
    higher_better = metric not in {"trimmed_mean_runtime"}

    xs: List[float] = []
    ys: List[float] = []
    best: Optional[float] = None

    for idx, prog in enumerate(programs, start=1):
        # X value
        iteration = prog.get("iteration_found")
        if iteration is None:
            iteration = prog.get("iteration")
        x = float(iteration) if isinstance(iteration, (int, float)) else float(idx)

        # Y value
        metrics = prog.get("metrics", {})
        val = _safe_float(metrics.get(metric))
        if val is None:
            # If value is missing or non-numeric, skip update
            xs.append(x)
            ys.append(best if best is not None else float("nan"))
            continue

        if best is None:
            best = val
        else:
            if higher_better:
                if val > best:
                    best = val
            else:
                if val < best:
                    best = val

        xs.append(x)
        ys.append(best)

    return xs, ys


def derive_labels(dirs: List[str], labels: Optional[List[str]]) -> List[str]:
    if labels and len(labels) == len(dirs):
        return labels
    return [Path(d).name for d in dirs]


def main():
    parser = argparse.ArgumentParser(description="Plot best-so-far evolution across experiments")
    parser.add_argument("--dirs", nargs="+", required=True, help="List of program directories")
    parser.add_argument("--labels", nargs="*", help="Labels for each directory (same length as --dirs)")
    parser.add_argument("--metric", default="combined_score",
                        choices=["combined_score", "time_score", "pass_rate", "trimmed_mean_runtime"],
                        help="Metric to plot (default: combined_score)")
    parser.add_argument("--output", default="artifacts/multi_best_evolution.png",
                        help="Output image path (default: artifacts/multi_best_evolution.png)")
    parser.add_argument("--title", default=None, help="Optional plot title")

    args = parser.parse_args()

    # Lazy import matplotlib after args parsing
    try:
        import matplotlib.pyplot as plt
    except Exception as e:
        raise RuntimeError(
            "matplotlib is required to generate plots. Please install it (e.g., pip install matplotlib)."
        ) from e

    labels = derive_labels(args.dirs, args.labels)

    series: List[Tuple[List[float], List[float]]] = []
    for d in args.dirs:
        programs = load_programs_from_dir(Path(d))
        if not programs:
            # Still add an empty series to keep legend alignment
            series.append(([], []))
            continue
        sorted_programs = sort_programs(programs)
        xs, ys = build_best_series(sorted_programs, args.metric)
        series.append((xs, ys))

    # Prepare output directory
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Plot
    plt.figure(figsize=(10, 6))
    for (xs, ys), label in zip(series, labels):
        if xs and ys:
            plt.plot(xs, ys, label=label)
        else:
            # Plot an empty placeholder for consistency
            plt.plot([], [], label=label)

    plt.xlabel("Iteration Found")
    ylabel = {
        "combined_score": "Combined Score",
        "time_score": "Time Score",
        "pass_rate": "Pass Rate",
        "trimmed_mean_runtime": "Trimmed Mean Runtime (lower is better)",
    }[args.metric]
    plt.ylabel(ylabel)

    title = args.title or f"Best Program Evolution ({args.metric})"
    plt.title(title)
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.3)

    plt.tight_layout()
    plt.savefig(out_path)
    print(f"Saved plot to: {out_path}")


if __name__ == "__main__":
    main()