import os
import sys

# Add project root to Python path to allow direct execution
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import json
import math
from typing import Any, Dict

import yaml

# Since analysis and benchmark are now part of the openevolve project structure,
# we can import them directly if the task is run from the correct context.
# The openevolve runner should handle the python path.
from openevolve.effibench.benchmark import run_performance_benchmark
from openevolve.evaluation_result import EvaluationResult


def load_config(file_path: str) -> Dict[str, Any]:
    """Loads a YAML configuration file."""
    with open(file_path, "r") as f:
        return yaml.safe_load(f)


def load_problem_data(file_path: str) -> Dict[str, Any]:
    """Loads the problem data from a JSON file."""
    with open(file_path, "r") as f:
        return json.load(f)


def evaluate(program_path: str, num_runs_override: int | None = None) -> EvaluationResult:
    """
    Evaluates the given program using the performance benchmark.

    Args:
        program_path: The path to the program code to be evaluated.
        num_runs_override: If provided, overrides the number of runs from the config.

    Returns:
        An EvaluationResult object with performance metrics or error information.
    """
    print("evaluate: Starting evaluation.")
    # Read the program code from the given path
    with open(program_path, "r") as f:
        program = f.read()

    # Load configuration
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "problem_config.yaml")
    problem_config = load_config(config_path)

    # Load the task data
    task_data = load_problem_data(problem_config["task_data_path"])
    print("evaluate: Loaded config and task data.")

    # Extract necessary parameters from configs and data
    lang = problem_config["language"]
    test_cases = (
        json.loads(task_data["generated_tests"])
        if isinstance(task_data["generated_tests"], str)
        else task_data["generated_tests"]
    )
    evaluator_code = task_data["evaluator"]
    test_runner_code = task_data.get("test_runner_code", {}).get(lang)  # Optional

    time_limit = problem_config["time_limit"]
    memory_limit = problem_config["memory_limit"]
    # Use override if provided, otherwise use config value
    num_runs = num_runs_override if num_runs_override is not None else problem_config["num_runs"]
    trimming_fraction = problem_config["trimming_fraction"]
    max_workers = problem_config["max_workers"]

    print("evaluate: Calling run_performance_benchmark...")
    # Run the performance benchmark
    benchmark_results = run_performance_benchmark(
        lang=lang,
        solution=program,
        test_cases=test_cases,
        evaluator=evaluator_code,
        test_runner=test_runner_code,
        num_runs=num_runs,
        time_limit=time_limit,
        memory_limit=memory_limit,
        trim_ratio=trimming_fraction,
        max_workers=max_workers,
    )
    print("evaluate: run_performance_benchmark finished.")

    performance_metrics = benchmark_results["performance_analysis"]
    failed_test_details = benchmark_results["failed_test_details"]

    if failed_test_details:
        # If there are failed submissions, return an error result
        num_failed = len(failed_test_details)
        num_total = len(benchmark_results["first_run_details"])
        pass_rate = (num_total - num_failed) / num_total if num_total > 0 else 0
        time_score = 0.0
        combined_score = 0.6 * pass_rate + 0.4 * time_score

        # Extract details from the first failed test case for the main error message
        first_failure = failed_test_details[0]
        error_status = first_failure.get("status", "unknown")
        error_text = first_failure.get("text", "No additional error text.")

        error_artifacts = {
            "error_type": f"SolutionFailedTests (status: {error_status})",
            "error_message": f"Solution passed {pass_rate:.2%} of test cases. First failure: {error_text}",
            "suggestion": "Review the solution to ensure it correctly handles all test cases, including edge cases.",
            "failed_tests": failed_test_details,  # Include all failure details
        }

        print("evaluate: Returning error result.")
        # Return a failing result with a score of 0
        return EvaluationResult(
            metrics={
                "pass_rate": pass_rate,
                "trimmed_mean_runtime": float("inf"),
                "time_score": time_score,
                "combined_score": combined_score,
                "error": f"Solution failed in some test cases. Error: {error_text}",
            },
            artifacts=error_artifacts,
        )
    else:
        # All tests passed, return performance metrics
        pass_rate = 1.0
        trimmed_mean_runtime = performance_metrics["trimmed_mean"]

        # Calculate time_score using an exponential decay function
        alpha = 5  # A decay constant to adjust the score distribution
        time_score = math.exp(-alpha * trimmed_mean_runtime / time_limit)

        # Calculate combined_score
        combined_score = 0.6 * pass_rate + 0.4 * time_score

        print("evaluate: Returning success result.")
        return EvaluationResult(
            metrics={
                "pass_rate": pass_rate,
                "trimmed_mean_runtime": trimmed_mean_runtime,
                "time_score": time_score,
                "combined_score": combined_score,
            },
            artifacts={"details": "All test cases passed."},
        )


# Stage-based evaluation for cascade evaluation
def evaluate_stage1(program_path):
    """
    First stage evaluation with a single trial to check for basic correctness.
    The main framework will use the combined_score from this result
    to decide if it passes the threshold for the next stage.
    """
    # Run with just one trial to quickly check for pass/fail.
    return evaluate(program_path, num_runs_override=1)


def evaluate_stage2(program_path):
    """Second stage evaluation with more thorough testing"""
    # Full evaluation as in the main evaluate function
    return evaluate(program_path)


# Example of how to run this evaluator independently for testing
if __name__ == "__main__":
    # This part is for testing the evaluator script directly.
    # It requires the config files and the initial program to be in the same directory.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    initial_program_path = os.path.join(script_dir, "initial_program.py")
    print(f"Script directory: {script_dir}")
    print(f"Initial program path: {initial_program_path}")

    with open(initial_program_path, "r") as f:
        initial_program = f.read()

    results = evaluate(initial_program_path)
    print("Evaluation results:", results)
