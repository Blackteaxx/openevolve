#!/usr/bin/env python3
"""
Example:
    python scripts/cluster_programs.py \
        --programs-dir /data/CodeEfficiency/openevolve/examples/archive/effibench_code_optimization_Qwen3-32B-Pass-Threshold-NoRepEval/aizu_3612_roller-coaster/openevolve_output/checkpoints/checkpoint_100/programs \
        --model-path /data/model/BAAI/bge-m3 \
        --output-dir programs_analysis \
        --device cuda \
        --batch-size 16 \
        --top-k 5

"""



import os
import sys
import json
import math
import glob
import argparse
import logging
from typing import List, Dict, Any, Tuple

import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except Exception as e:
    raise RuntimeError(
        "sentence-transformers is required. Install with: pip install sentence-transformers"
    ) from e

try:
    from sklearn.cluster import DBSCAN
except Exception as e:
    raise RuntimeError(
        "scikit-learn is required. Install with: pip install scikit-learn"
    ) from e


def find_code_field(d: Dict[str, Any]) -> str | None:
    """Best-effort extraction of code text from a program JSON object."""
    candidates = [
        "program",
        "code",
        "content",
        "text",
        "program_code",
        "source_code",
        "body",
    ]
    for key in candidates:
        v = d.get(key)
        if isinstance(v, str) and v.strip():
            return v
    # Some files may store under nested structures
    for key in d:
        v = d[key]
        if isinstance(v, dict):
            nested = find_code_field(v)
            if nested:
                return nested
    return None


def load_program_texts(programs_dir: str) -> Tuple[List[str], List[str]]:
    """
    Load all program JSON files under programs_dir and extract code text.
    Returns:
        paths: list of file paths
        texts: list of code strings corresponding to paths
    """
    # Consider both JSON and plain code files
    files = sorted(glob.glob(os.path.join(programs_dir, "*")))
    paths: List[str] = []
    texts: List[str] = []

    for fp in files:
        if os.path.isdir(fp):
            continue
        ext = os.path.splitext(fp)[1].lower()
        try:
            if ext == ".json":
                with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                    data = json.load(f)
                code = find_code_field(data)
                if code is None:
                    logging.warning(f"No code field found in {fp}; skipping JSON.")
                    continue
            else:
                # Treat as plain text code (e.g., .py, .txt, no extension)
                with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                    code = f.read()
                if not isinstance(code, str) or not code.strip():
                    logging.warning(f"Empty or invalid text in {fp}; skipping.")
                    continue
            paths.append(fp)
            texts.append(code)
        except Exception as e:
            logging.warning(f"Failed to read {fp}: {type(e).__name__}: {e}")
            continue

    return paths, texts


def auto_k(n: int) -> int:
    """Heuristic for cluster count based on dataset size."""
    if n <= 2:
        return n
    # sqrt heuristic capped to a reasonable range
    k = int(round(math.sqrt(n)))
    return max(2, min(50, k))


def build_neighbors(embeddings: np.ndarray, top_k: int = 5) -> List[List[Tuple[int, float]]]:
    """Compute top-k cosine neighbors for each item (excluding self)."""
    # embeddings expected normalized; cosine = dot product
    sim = embeddings @ embeddings.T  # shape (N, N)
    n = sim.shape[0]
    neighbors: List[List[Tuple[int, float]]] = []
    for i in range(n):
        # Exclude self
        sims_i = sim[i].copy()
        sims_i[i] = -np.inf
        # 处理小样本场景：最多只能选 n-1 个非自身邻居
        effective_k = min(top_k, n - 1)
        if effective_k <= 0:
            neighbors.append([])
            continue
        # 使用 argsort，避免当 effective_k >= len(sims_i) 时 argpartition 越界
        idxs = np.argsort(-sims_i)[:effective_k]
        neighbors.append([(int(j), float(sims_i[j])) for j in idxs])
    return neighbors


def infer_eps_from_dist(dist: np.ndarray) -> float:
    """Infer a reasonable DBSCAN eps from a precomputed distance matrix.

    Heuristic: use the median of nearest-neighbor distances across all points.
    This scales with dataset density without requiring manual tuning.
    """
    n = dist.shape[0]
    # Ensure diagonal is not chosen
    nearest = []
    for i in range(n):
        row = dist[i].copy()
        row[i] = np.inf
        nearest.append(float(np.min(row)))
    # Median nearest neighbor distance
    base = float(np.median(nearest))
    # Slightly inflate to allow local connectivity
    return max(1e-8, base * 1.05)


def main():
    parser = argparse.ArgumentParser(
        description="Cluster and similarity analysis for EffiBench checkpoint programs using bge-m3 embeddings"
    )
    parser.add_argument(
        "--programs-dir",
        required=True,
        help="Path to the programs directory (e.g., .../checkpoints/checkpoint_100/programs)",
    )
    parser.add_argument(
        "--model-path",
        default="/data/model/BAAI/bge-m3",
        help="Local path to HuggingFace embedding model (default: /data/model/BAAI/bge-m3)",
    )
    parser.add_argument(
        "--output-dir",
        default="programs_analysis",
        help="Directory to write analysis outputs (JSON/CSV/Numpy)",
    )
    parser.add_argument(
        "--device",
        default=None,
        help="Device for embedding model, e.g. 'cuda' or 'cpu' (default: auto)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
        help="Batch size for embedding encoding",
    )
    # Density clustering parameters
    parser.add_argument(
        "--eps",
        type=float,
        default=None,
        help="DBSCAN eps (distance threshold). If not set, inferred from data",
    )
    parser.add_argument(
        "--min-samples",
        type=int,
        default=3,
        help="DBSCAN min_samples (minimum points to form a core point)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Top-K neighbors to compute for similarity report",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for clustering",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    programs_dir = args.programs_dir
    if not os.path.isdir(programs_dir):
        logging.error(f"Programs dir not found: {programs_dir}")
        sys.exit(1)

    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    logging.info(f"Loading program JSONs from: {programs_dir}")
    paths, texts = load_program_texts(programs_dir)
    n = len(texts)
    if n == 0:
        logging.error("No programs with valid code found. Aborting.")
        sys.exit(2)
    logging.info(f"Found {n} programs")

    # Load embedding model
    logging.info(f"Loading embedding model from: {args.model_path}")
    model = SentenceTransformer(args.model_path, device=args.device)

    # Compute embeddings (normalized for cosine)
    logging.info("Encoding embeddings...")
    embeddings = model.encode(
        texts,
        batch_size=args.batch_size,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    # Similarity and distance matrices
    logging.info("Computing cosine similarity matrix")
    sim = embeddings @ embeddings.T  # cosine similarity
    # 数值稳定性：极少数情况下点积可能因浮点误差略微超过 1 或小于 -1
    sim = np.clip(sim, -1.0, 1.0)
    dist = 1.0 - sim                 # convert to distance, [0, 2]
    # 保证非负，避免 sklearn 对预计算距离的非负校验报错
    np.fill_diagonal(dist, 0.0)
    np.clip(dist, 0.0, None, out=dist)

    # Density clustering (DBSCAN) on precomputed distance matrix
    eps = float(args.eps) if args.eps is not None else infer_eps_from_dist(dist)
    min_samples = int(args.min_samples)
    logging.info(f"Clustering with DBSCAN: eps={eps:.6f}, min_samples={min_samples}")
    db = DBSCAN(eps=eps, min_samples=min_samples, metric="precomputed")
    labels = db.fit_predict(dist)

    # Nearest neighbors
    logging.info(f"Computing top-{args.top_k} neighbors per program")
    neighbors = build_neighbors(embeddings, top_k=args.top_k)

    # Persist outputs
    np.save(os.path.join(output_dir, "embeddings.npy"), embeddings)

    index = [
        {"id": i, "path": paths[i]} for i in range(n)
    ]
    with open(os.path.join(output_dir, "index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    # Build clusters mapping (DBSCAN uses -1 for noise)
    clusters: Dict[int, List[int]] = {}
    for i, lbl in enumerate(labels):
        clusters.setdefault(int(lbl), []).append(i)
    # Report estimated cluster count (excluding noise)
    unique_labels = set(int(l) for l in labels.tolist())
    n_clusters = len([l for l in unique_labels if l != -1])
    with open(os.path.join(output_dir, "clusters.json"), "w", encoding="utf-8") as f:
        json.dump({
            "algorithm": "dbscan",
            "eps": eps,
            "min_samples": min_samples,
            "k": int(n_clusters),
            "labels": labels.tolist(),
            "clusters": clusters
        }, f, ensure_ascii=False, indent=2)

    neighbors_out: List[Dict[str, Any]] = []
    for i, nbrs in enumerate(neighbors):
        neighbors_out.append({
            "id": i,
            "path": paths[i],
            "neighbors": [{"id": j, "path": paths[j], "score": s} for j, s in nbrs],
        })
    with open(os.path.join(output_dir, "neighbors.json"), "w", encoding="utf-8") as f:
        json.dump(neighbors_out, f, ensure_ascii=False, indent=2)

    logging.info("Analysis completed.")
    logging.info(f"Outputs written to: {output_dir}")
    logging.info("Files: embeddings.npy, index.json, clusters.json, neighbors.json")


if __name__ == "__main__":
    main()