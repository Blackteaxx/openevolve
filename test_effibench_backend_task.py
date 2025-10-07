import os
import json
import time
import argparse
import logging
from typing import List, Dict, Any

from openevolve.effibench.run_tests import run_tests
from openevolve.effibench.backends.backend_utils import get_backend_url


def load_task_data(path: str) -> Dict[str, Any]:
    with open(path, "r") as f:
        data = json.load(f)
    return data


def main():
    parser = argparse.ArgumentParser(description="Run effibench run_tests against a dataset using configured backends")
    parser.add_argument("dataset", nargs="?", default="/data/CodeEfficiency/benchmark/EffiBench-X/data/dataset/atcoder_abc388c_various-kagamimochi.json",
                        help="Path to the task dataset JSON")
    parser.add_argument("--limit", type=int, default=10, help="Limit number of test cases for quick run")
    parser.add_argument("--poll", type=int, default=3, help="Polling interval seconds")
    parser.add_argument("--retries", type=int, default=2, help="Backend retries")
    parser.add_argument("--timeout", type=int, default=300, help="Overall eval timeout seconds")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    backend_env = os.getenv("BACKEND_BASE_URL")
    print(f"BACKEND_BASE_URL={backend_env}")

    data = load_task_data(args.dataset)
    lang = data.get("language", "python3")
    gt = data.get("generated_tests")
    test_cases = json.loads(gt) if isinstance(gt, str) else gt
    print(f"First test case: {test_cases[0]}")
    if args.limit:
        test_cases = test_cases[: args.limit]

    evaluator_code = data["evaluator"]
    test_runner_code = data.get("test_runner_code", {}).get(lang)

    # Minimal placeholder solution that prints a constant (not a correct solution)
    solution = "import sys\nprint(0)\n"

    try:
        print("Selected backend:", get_backend_url())
    except Exception as e:
        print("Error selecting backend:", type(e).__name__, str(e))

    try:
        t0 = time.time()
        results = run_tests(
            lang=lang,
            solution=solution,
            test_cases=test_cases,
            evaluator=evaluator_code,
            test_runner=test_runner_code,
            time_limit=10,
            memory_limit=1024,
            early_stop=False,
            raise_on_error=False,
            as_batch=True,
            backend_retries=args.retries,
            eval_timeout=args.timeout,
            polling_interval=args.poll,
        )
        elapsed = time.time() - t0
        print(f"Completed in {elapsed:.1f}s, got {len(results)} results")
        statuses = [r.get("status") if isinstance(r, dict) else None for r in results]
        print("Status counts:", {s: statuses.count(s) for s in set(statuses)})
        print("Sample statuses:", statuses[: min(10, len(statuses))])
    except Exception as e:
        import traceback
        print("RUN_TESTS_EXCEPTION:", type(e).__name__, str(e))
        traceback.print_exc()


if __name__ == "__main__":
    main()