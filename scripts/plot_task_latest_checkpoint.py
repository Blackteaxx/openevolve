#!/usr/bin/env python3
"""
Plot best-so-far evolution per setting using latest checkpoint's programs for a specific task.
Reuses functions from scripts/plot_best_evolution.py.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path
import importlib.util
from typing import Optional, List, Tuple


def _load_plot_best_module():
    """Dynamically load functions from scripts/plot_best_evolution.py."""
    module_path = Path(__file__).parent / "plot_best_evolution.py"
    if not module_path.exists():
        raise FileNotFoundError(f"Required module not found: {module_path}")
    spec = importlib.util.spec_from_file_location("plot_best_evolution", str(module_path))
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod


def find_task_dir(exp_root: Path, task: str) -> Optional[Path]:
    """Locate the task directory under an experiment root.

    Strategy:
    - Search for exact directory name match at any depth
    - Fallback to substring match, prefer shortest path
    """
    exp_root = Path(exp_root)
    if not exp_root.exists():
        return None

    exact: List[Path] = []
    for p in exp_root.rglob("*"):
        if p.is_dir() and p.name == task:
            exact.append(p)
    if exact:
        exact.sort(key=lambda x: len(x.parts))
        return exact[0]

    substr: List[Path] = []
    for p in exp_root.rglob("*"):
        if p.is_dir() and task in p.name:
            substr.append(p)
    if substr:
        substr.sort(key=lambda x: len(x.parts))
        return substr[0]
    return None


def find_latest_checkpoint_dir(task_dir: Path) -> Optional[Path]:
    """Find the latest checkpoint directory under the task's checkpoints path.

    Prefer the highest numeric suffix in names like 'checkpoint_50'. If no numeric
    suffix is present, fall back to latest modification time.
    """
    base = Path(task_dir) / "openevolve_output" / "checkpoints"
    if not base.exists():
        return None

    candidates: List[Tuple[Optional[int], float, Path]] = []
    for p in base.iterdir():
        if p.is_dir() and p.name.startswith("checkpoint"):
            m = re.search(r"(\d+)$", p.name)
            num = int(m.group(1)) if m else None
            try:
                mtime = p.stat().st_mtime
            except Exception:
                mtime = 0.0
            candidates.append((num, mtime, p))

    if not candidates:
        return None

    numerics = [(n, mt, p) for (n, mt, p) in candidates if n is not None]
    non_numerics = [(n, mt, p) for (n, mt, p) in candidates if n is None]

    if numerics:
        numerics.sort(key=lambda t: t[0])  # ascending by checkpoint number
        return numerics[-1][2]

    non_numerics.sort(key=lambda t: t[1])  # ascending by mtime
    return non_numerics[-1][2] if non_numerics else None


def derive_labels(roots: List[str], labels: Optional[List[str]]) -> List[str]:
    if labels and len(labels) == len(roots):
        return labels
    return [Path(r).name for r in roots]


def main():
    parser = argparse.ArgumentParser(
        description="Plot using latest checkpoint programs for a task across settings",
    )
    parser.add_argument("--exp-roots", nargs="+", required=True, help="Experiment root directories")
    parser.add_argument("--task", required=True, help="Task directory name or substring")
    parser.add_argument("--labels", nargs="*", help="Labels for each exp root (same length as --exp-roots)")
    parser.add_argument(
        "--metric",
        default="combined_score",
        choices=["combined_score", "time_score", "pass_rate", "trimmed_mean_runtime"],
        help="Metric to plot (default: combined_score)",
    )
    parser.add_argument(
        "--output",
        default="artifacts/task_latest_checkpoint.png",
        help="Output image path (default: artifacts/task_latest_checkpoint.png)",
    )
    parser.add_argument("--title", default=None, help="Optional plot title")
    parser.add_argument("--x-min", type=float, default=0.0, help="Left bound for X axis (default: 0)")

    args = parser.parse_args()

    # Import matplotlib lazily after args parsing
    try:
        import matplotlib.pyplot as plt
    except Exception as e:
        raise RuntimeError(
            "matplotlib is required to generate plots. Please install it (e.g., pip install matplotlib)."
        ) from e

    # Load plotting helpers from plot_best_evolution.py
    mod = _load_plot_best_module()
    load_programs_from_dir = getattr(mod, "load_programs_from_dir")
    sort_programs = getattr(mod, "sort_programs")
    build_best_series = getattr(mod, "build_best_series")

    labels = derive_labels(args.exp_roots, args.labels)

    series: List[Tuple[List[float], List[float]]] = []
    resolved_paths: List[Optional[Path]] = []

    for root in args.exp_roots:
        task_dir = find_task_dir(Path(root), args.task)
        if not task_dir:
            series.append(([], []))
            resolved_paths.append(None)
            continue

        cp_dir = find_latest_checkpoint_dir(task_dir)
        if not cp_dir:
            series.append(([], []))
            resolved_paths.append(task_dir)
            continue

        programs_dir = cp_dir / "programs"
        try:
            programs = load_programs_from_dir(programs_dir)
        except Exception:
            # Fallback to reading JSONs directly under the checkpoint dir
            try:
                programs = load_programs_from_dir(cp_dir)
            except Exception:
                programs = []

        if not programs:
            series.append(([], []))
            resolved_paths.append(cp_dir)
            continue

        sorted_programs = sort_programs(programs)
        xs, ys = build_best_series(sorted_programs, args.metric)
        series.append((xs, ys))
        resolved_paths.append(programs_dir)

    # Prepare output directory
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Plot
    plt.figure(figsize=(10, 6))
    for (xs, ys), label in zip(series, labels):
        if xs and ys:
            plt.plot(xs, ys, label=label)
        else:
            # Placeholder to keep legend alignment even if not found
            plt.plot([None], [None], label=f"{label} (not found)")

    plt.xlabel("Iteration Found")
    ylabel = {
        "combined_score": "Combined Score",
        "time_score": "Time Score",
        "pass_rate": "Pass Rate",
        "trimmed_mean_runtime": "Trimmed Mean Runtime (lower is better)",
    }[args.metric]
    plt.ylabel(ylabel)

    title = args.title or f"Task '{args.task}' Latest Checkpoint Programs ({args.metric})"
    plt.title(title)
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.3)
    plt.xlim(left=args.x_min)

    plt.tight_layout()
    plt.savefig(out_path)
    print(f"Saved plot to: {out_path}")


if __name__ == "__main__":
    main()