"""Evaluator for algorithm efficiency and correctness (Sandbox-based)

2025.9.23: 重构说明（Sandbox集成版本）
- 评估目标：通用算法的正确率、时间效率、空间效率。
- 使用Sandbox进行安全的代码执行和内存限制。
- 评估器作为客户端，将评估任务打包后委托给Sandbox执行。
- 支持动态内存限制配置，提供更安全的代码执行环境。
- 保持与原有接口的兼容性，输出综合得分 combined_score。
"""

import copy
import logging
import math
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import scipy.stats as st

os.environ["OMP_NUM_THREADS"] = "1"

from openevolve.evaluation_result import EvaluationResult
from openevolve.sandbox import Sandbox

logger = logging.getLogger(__name__)

# Define the entry point function name, test cases and some consts
ENTRY_POINT = "addTwoNumbers"
TEST_CASES = [
    {"expected": [7, 0, 8], "input": [[2, 4, 3], [5, 6, 4]]},
    {"expected": [0], "input": [[0], [0]]},
    {
        "expected": [8, 9, 9, 9, 0, 0, 0, 1],
        "input": [[9, 9, 9, 9, 9, 9, 9], [9, 9, 9, 9]],
    },
    {
        "expected": [
            1,
            9,
            4,
            7,
            5,
            6,
            3,
            9,
            2,
            4,
            8,
            5,
            7,
            3,
            6,
            7,
            8,
            2,
            2,
            0,
            5,
            9,
            0,
            4,
            5,
            8,
            8,
            8,
            4,
            3,
            3,
            2,
            4,
            7,
            9,
            2,
            9,
            9,
            2,
            7,
            2,
            3,
            2,
            5,
            1,
            5,
            3,
            3,
            0,
            5,
            8,
        ],
        "input": [
            [
                1,
                9,
                4,
                7,
                5,
                6,
                3,
                9,
                2,
                4,
                8,
                5,
                7,
                3,
                6,
                7,
                8,
                2,
                2,
                0,
                5,
                9,
                0,
                4,
                5,
                8,
                8,
                8,
                4,
                3,
                3,
                2,
                4,
                7,
                9,
                2,
                9,
                9,
                2,
                7,
                2,
                3,
                2,
                5,
                1,
                5,
                3,
                3,
                0,
                5,
                8,
            ],
            [0],
        ],
    },
    {
        "expected": [
            5,
            5,
            9,
            6,
            8,
            3,
            2,
            7,
            1,
            4,
            9,
            5,
            9,
            7,
            5,
            0,
            6,
            2,
            6,
            7,
            7,
            8,
            0,
            0,
            3,
            3,
            2,
            9,
            5,
            3,
            5,
            2,
            8,
            5,
            2,
            8,
            7,
            4,
            3,
            3,
            3,
            5,
            9,
            5,
            1,
            8,
            9,
            1,
            5,
            4,
            8,
            5,
            8,
            8,
            7,
            2,
            0,
            4,
            8,
            4,
            8,
            9,
            6,
            1,
            9,
            7,
            0,
            5,
            7,
            5,
            7,
            5,
            4,
            5,
            5,
            8,
            9,
            3,
            9,
            7,
            6,
        ],
        "input": [
            [
                3,
                2,
                8,
                3,
                4,
                7,
                8,
                7,
                3,
                3,
                8,
                5,
                4,
                7,
                8,
                5,
                7,
                9,
                0,
                5,
                6,
                0,
                9,
                1,
                6,
                7,
                1,
                8,
                8,
                2,
                1,
                3,
                6,
                9,
                7,
                1,
                4,
                9,
                9,
                6,
                7,
                9,
                6,
                2,
                1,
                2,
                9,
                9,
                9,
                0,
                5,
                1,
                3,
                9,
                2,
                5,
            ],
            [
                2,
                3,
                1,
                3,
                4,
                6,
                3,
                9,
                7,
                0,
                1,
                0,
                5,
                0,
                7,
                4,
                8,
                2,
                5,
                2,
                1,
                8,
                1,
                8,
                6,
                5,
                0,
                1,
                7,
                0,
                4,
                9,
                1,
                6,
                4,
                6,
                3,
                5,
                3,
                6,
                5,
                5,
                2,
                3,
                0,
                6,
                0,
                2,
                5,
                3,
                3,
                4,
                5,
                9,
                4,
                7,
                9,
                3,
                8,
                4,
                8,
                9,
                6,
                1,
                9,
                7,
                0,
                5,
                7,
                5,
                7,
                5,
                4,
                5,
                5,
                8,
                9,
                3,
                9,
                7,
                6,
            ],
        ],
    },
    {
        "expected": [
            7,
            4,
            2,
            8,
            5,
            3,
            9,
            4,
            6,
            2,
            7,
            0,
            8,
            0,
            4,
            4,
            2,
            5,
            6,
            3,
            1,
            0,
            3,
            8,
            5,
            2,
            7,
            2,
            6,
            3,
            8,
            3,
            0,
            9,
            2,
            0,
            4,
            7,
            2,
            3,
            1,
            9,
            2,
            7,
            1,
            2,
            2,
            6,
            9,
            9,
            1,
            3,
            1,
            0,
            2,
            1,
            3,
            4,
            1,
            5,
            7,
            8,
            5,
            2,
            4,
            6,
            1,
            9,
            2,
            2,
            4,
            6,
            3,
            6,
            8,
            9,
            5,
            5,
            7,
            7,
            4,
            2,
            1,
            9,
        ],
        "input": [
            [1, 5, 9, 6, 7, 3, 9, 5],
            [
                6,
                9,
                2,
                1,
                8,
                9,
                9,
                8,
                5,
                2,
                7,
                0,
                8,
                0,
                4,
                4,
                2,
                5,
                6,
                3,
                1,
                0,
                3,
                8,
                5,
                2,
                7,
                2,
                6,
                3,
                8,
                3,
                0,
                9,
                2,
                0,
                4,
                7,
                2,
                3,
                1,
                9,
                2,
                7,
                1,
                2,
                2,
                6,
                9,
                9,
                1,
                3,
                1,
                0,
                2,
                1,
                3,
                4,
                1,
                5,
                7,
                8,
                5,
                2,
                4,
                6,
                1,
                9,
                2,
                2,
                4,
                6,
                3,
                6,
                8,
                9,
                5,
                5,
                7,
                7,
                4,
                2,
                1,
                9,
            ],
        ],
    },
    {
        "expected": [
            2,
            7,
            3,
            7,
            8,
            8,
            1,
            1,
            7,
            6,
            8,
            1,
            5,
            1,
            2,
            6,
            0,
            8,
            8,
            8,
            5,
            7,
            3,
            0,
            2,
            6,
            1,
            9,
            4,
            2,
            0,
            9,
            4,
            7,
            3,
            6,
            8,
            6,
            3,
            8,
            3,
            7,
            3,
            2,
            6,
            4,
            9,
            0,
            5,
            7,
            9,
            1,
            4,
            7,
            5,
            0,
            3,
            6,
            1,
            0,
            1,
            2,
            5,
            7,
            5,
            6,
            4,
            1,
            4,
            7,
            4,
            6,
            7,
        ],
        "input": [
            [
                9,
                5,
                5,
                6,
                8,
                8,
                1,
                1,
                7,
                6,
                8,
                1,
                5,
                1,
                2,
                6,
                0,
                8,
                8,
                8,
                5,
                7,
                3,
                0,
                2,
                6,
                1,
                9,
                4,
                2,
                0,
                9,
                4,
                7,
                3,
                6,
                8,
                6,
                3,
                8,
                3,
                7,
                3,
                2,
                6,
                4,
                9,
                0,
                5,
                7,
                9,
                1,
                4,
                7,
                5,
                0,
                3,
                6,
                1,
                0,
                1,
                2,
                5,
                7,
                5,
                6,
                4,
                1,
                4,
                7,
                4,
                6,
                7,
            ],
            [3, 1, 8],
        ],
    },
    {
        "expected": [
            0,
            7,
            3,
            1,
            3,
            7,
            2,
            7,
            9,
            0,
            6,
            2,
            9,
            7,
            0,
            6,
            8,
            8,
            8,
            8,
            2,
            5,
            4,
            9,
            7,
            5,
            2,
            1,
            0,
            8,
            7,
            3,
            2,
            8,
            7,
            1,
            1,
            9,
            5,
            0,
            7,
            9,
            4,
            3,
            6,
            2,
            8,
            6,
            5,
            3,
            0,
            5,
            3,
            3,
            7,
            4,
            1,
            5,
            4,
            8,
            1,
            2,
            4,
            5,
            2,
            3,
            1,
            4,
            6,
            2,
            6,
            6,
            7,
            1,
            1,
            9,
            2,
            1,
            8,
            3,
            0,
            7,
            6,
            7,
            3,
            4,
            2,
            7,
            9,
            5,
            8,
            5,
            9,
            9,
            5,
            5,
            7,
        ],
        "input": [
            [
                7,
                6,
                2,
                1,
                7,
                0,
                6,
                7,
                6,
                1,
                4,
                8,
                9,
                7,
                3,
                9,
                7,
                9,
                6,
                8,
                1,
                6,
                4,
                4,
                4,
                3,
                6,
                5,
                5,
                6,
                1,
                3,
                8,
                7,
                3,
                5,
                6,
                4,
                6,
                3,
                3,
                0,
                2,
                4,
                9,
                3,
                0,
                5,
                3,
                0,
                4,
                2,
                6,
                8,
                2,
                7,
                4,
                9,
                1,
                2,
                6,
                5,
                7,
                2,
                8,
                0,
                9,
                4,
                5,
                1,
                1,
                6,
                0,
                4,
                8,
                3,
                9,
                3,
            ],
            [
                3,
                0,
                1,
                0,
                6,
                6,
                6,
                9,
                2,
                9,
                1,
                4,
                9,
                9,
                6,
                6,
                0,
                9,
                1,
                0,
                1,
                9,
                9,
                4,
                3,
                2,
                6,
                5,
                4,
                1,
                6,
                0,
                4,
                0,
                4,
                6,
                4,
                4,
                9,
                6,
                3,
                9,
                2,
                9,
                6,
                8,
                7,
                1,
                2,
                3,
                6,
                2,
                7,
                4,
                4,
                7,
                6,
                5,
                2,
                6,
                5,
                6,
                6,
                2,
                4,
                2,
                2,
                9,
                0,
                1,
                5,
                0,
                7,
                7,
                2,
                5,
                3,
                7,
                7,
                3,
                0,
                7,
                6,
                7,
                3,
                4,
                2,
                7,
                9,
                5,
                8,
                5,
                9,
                9,
                5,
                5,
                7,
            ],
        ],
    },
]
CONVERT_OFFLINE = """def convert_offline(case):
    import lctk
    inputs, expected = case
    inputs = tuple([lctk.linkedList(inputs[0]), lctk.linkedList(inputs[1])])
    return inputs, expected"""
EVALUATE_OFFLINE = """def evaluate_offline(inputs, outputs, expected):
    import lctk
    outputs = lctk.linkedList2Arr(outputs)
    if outputs == expected:
        return True
    
    return False"""
EVAL_TIMEOUT_SEC = 10  # 评估超时时间（秒）
MAX_MEMORY_LIMIT_MB = 256  # 内存限制（MB）
T_REF = 10.0  # 参考时间（秒）
M_REF = 64.0  # 参考内存（MB）
EVAL_NUM = 30


def _sanitize_metrics_for_json(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Replace non-finite floats (inf, -inf, nan) with None for JSON compatibility."""
    sanitized: Dict[str, Any] = {}
    for k, v in metrics.items():
        if isinstance(v, float) and not math.isfinite(v):
            sanitized[k] = None
        else:
            sanitized[k] = v
    return sanitized


def format_test_cases_for_sandbox(test_cases):
    """
    将TEST_CASES格式转换为Sandbox要求的格式
    从 [{'input': [args], 'expected': result}]
    转换为 [{'input': [args], 'expected': result}] (保持不变，已经是正确格式)
    """
    return test_cases


def discover_reference_paths(program_path: str) -> List[str]:
    """
    2025.9.19: 自动发现参考解路径的辅助函数

    在 ref_solutions 目录中查找所有 .py 文件作为参考解。

    Args:
        program_path: 待评估程序的文件路径

    Returns:
        List[str]: 发现的参考解文件的绝对路径列表
    """
    reference_paths: List[str] = []
    try:
        # 寻找本文件所在目录
        dirpath = os.path.dirname(__file__)
        ref_solutions_dir = os.path.join(dirpath, "ref_solutions")
        if os.path.isdir(ref_solutions_dir):
            reference_paths = [
                os.path.join(ref_solutions_dir, f)
                for f in os.listdir(ref_solutions_dir)
                if f.endswith(".py")
            ]
    except Exception:
        # 失败则回退为空列表
        reference_paths = []
    return reference_paths


def create_sandbox_sample(
    solution_code: str, test_cases: list, entry_point: str, memory_limit_mb: int
) -> dict:
    """
    创建Sandbox执行所需的sample字典
    """
    # 定义胶水代码
    convert_offline_code = CONVERT_OFFLINE
    evaluate_offline_code = EVALUATE_OFFLINE

    sample = {
        "solution": solution_code,
        "timeout": EVAL_TIMEOUT_SEC,
        "test_cases": format_test_cases_for_sandbox(test_cases),
        "entry_point": entry_point,
        "convert_offline": convert_offline_code,
        "evaluate_offline": evaluate_offline_code,
        "maximum_memory_bytes": memory_limit_mb * 1024 * 1024,
        "solution_index": 0,
    }
    return sample


def analyze_runtimes(samples, confidence=0.95, trim_ratio=0.05):
    samples = np.array(samples)
    mean = samples.mean()
    std = samples.std(ddof=1)
    min_val = samples.min()
    max_val = samples.max()
    max_diff = max_val - min_val

    # 95% confidence interval for the mean
    ci_low, ci_high = st.t.interval(
        confidence, df=len(samples) - 1, loc=mean, scale=st.sem(samples)
    )

    # trimmed mean (去掉前后 5%)
    sorted_samples = np.sort(samples)
    n = len(samples)
    k = int(n * trim_ratio)
    trimmed = sorted_samples[k : n - k] if k > 0 else sorted_samples
    trimmed_mean = trimmed.mean()

    return {
        "n": len(samples),
        "mean": mean,
        "std": std,
        "min": min_val,
        "max": max_val,
        "max_diff": max_diff,
        "95%_CI": (ci_low, ci_high),
        "trimmed_mean": trimmed_mean,
    }


def _evaluate_single_reference(ref_path: str, index: int) -> Dict[str, Any]:
    """评估单个参考解并返回其性能指标（运行5次取平均值）。"""
    try:
        # 读取参考解代码
        solution_code = Path(ref_path).read_text()

        # 创建sandbox sample
        sample = create_sandbox_sample(
            solution_code=solution_code,
            test_cases=copy.deepcopy(TEST_CASES),
            entry_point=ENTRY_POINT,
            memory_limit_mb=MAX_MEMORY_LIMIT_MB,
        )

        # 运行5次测量取平均值
        runtimes = []
        all_passed = True
        final_status = "passed"
        final_passed = 0
        final_total = 0

        b_failures = []
        for run_idx in range(EVAL_NUM):
            # 使用Sandbox执行
            result_dict = Sandbox.run_sample(sample)

            # 解析结果
            status = result_dict.get("status", "failed")
            runtime = result_dict.get("runtime", float("inf"))
            passed = result_dict.get("passed", None)
            total = result_dict.get("total", None)

            if status == "passed":
                runtimes.append(runtime)
                final_passed = len(TEST_CASES)
                final_total = len(TEST_CASES)
            else:
                all_passed = False
                final_status = status
                final_passed = 0 if passed is None else passed
                final_total = len(TEST_CASES)

                # 捕获来自sandbox的详细错误信息
                error_info = {
                    "status": status,
                    "error": result_dict.get("error"),
                    "exception": result_dict.get("exception"),
                    "failures": result_dict.get(
                        "failures"
                    ),  # if the program does not pass all test cases, the 'failures' field will contain the details of the failed test cases.
                    "failed_test_case": result_dict.get(
                        "failed_test_case"
                    ),  # if the program throw exceptions, the 'failed_test_case' field will contain the details of the failed test case.
                    "failed_test_case_index": result_dict.get("failed_test_case_index"),
                }
                b_failures.append(
                    {k: v for k, v in error_info.items() if v is not None}
                )
                break  # 如果有一次失败，就不继续测试了

        # 计算平均运行时间、标准差与极差，并打印
        if runtimes:
            runtime_stats = analyze_runtimes(runtimes)
            avg_runtime = runtime_stats["trimmed_mean"]
            # Print runtime statistics
            print(
                f"Reference {index}: {ref_path} - Average runtime: {runtime_stats["mean"]:.8f} sec, Std Dev: {runtime_stats['std']:.8f} sec, Range: {runtime_stats['max_diff']:.8f} sec, 95% CI: {runtime_stats['95%_CI']}, Trimmed mean: {runtime_stats['trimmed_mean']:.8f}"
            )
        else:
            avg_runtime = float("inf")

        # 计算通过率（使用5次测试的最终结果）
        if final_status == "passed" and all_passed:
            b_passed = final_passed
            b_total = final_total
            b_pass_rate = 1.0
            b_duration = avg_runtime
            b_peak_mb = 0.0  # Sandbox不返回内存信息，设为0
            # b_failures is already empty
        else:
            b_passed = final_passed
            b_total = final_total
            b_pass_rate = b_passed / b_total if b_total > 0 else 0.0
            b_duration = avg_runtime
            b_peak_mb = float("inf")
            # 如果循环中没有捕获到详细错误，则添加通用错误信息
            if not b_failures:
                b_failures = [
                    {"error": "Sandbox execution failed", "status": final_status}
                ]

        result = {
            "path": ref_path,
            "pass_rate": b_pass_rate,
            "passed_cases": int(b_passed),
            "total_cases": int(b_total),
            "execution_time_sec": float(b_duration),
            "python_peak_memory_mb": float(b_peak_mb),
            "failures_sample": b_failures,
            "measurement_runs": len(runtimes) if runtimes else 1,  # 记录实际测量次数
            "sandbox_status": final_status,
            "failed_test_case_index": (
                b_failures[0].get("failed_test_case_index")
                if b_failures and isinstance(b_failures[0], dict)
                else None
            ),
        }
        if b_passed == b_total and b_total > 0:
            result["ref_time"] = float(b_duration)
            result["ref_mem"] = float(b_peak_mb)
        return result
    except Exception as be:
        logger.exception(
            f"Error evaluating reference {index}: {ref_path} - {type(be).__name__}: {str(be)}"
        )
        return {
            "path": ref_path,
            "error_type": type(be).__name__,
            "error_message": str(be),
        }


def evaluate(program_path: str) -> EvaluationResult:
    """
    2025.9.23: 综合评估算法的正确率、时间效率与空间效率（Sandbox版本）。

    约定：被评估程序需定义 class Solution，包含可调用的方法（如 solve 或 findMedianSortedArrays）。

    指标：
    - pass_rate: 通过的用例数 / 用例总数
    - execution_time_sec: 执行全部用例的总耗时
    - python_peak_memory_mb: 固定为0（由于使用Sandbox）
    - time_score, mem_score: 归一化时间/内存得分（优先相对参考基线，否则回退到常量基线）
    - combined_score: 0.5 * pass_rate + 0.5 * time_score
    """

    # 读取候选程序代码
    try:
        _ = Path(program_path).read_text()
    except Exception as e:
        logger.exception(
            f"Error reading program {program_path}: {type(e).__name__}: {str(e)}"
        )
        _metrics = {
            "pass_rate": 0.0,
            "execution_time_sec": 0.0,
            # "python_peak_memory_mb": 0.0,
            "combined_score": 0.0,
            "error": f"FileReadError: {e}",
        }
        return EvaluationResult(
            metrics=_sanitize_metrics_for_json(_metrics),
            artifacts={
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
        )

    try:
        # 使用已有的_evaluate_single_reference函数（包含5次测量逻辑）
        result = _evaluate_single_reference(program_path, 0)

        # 提取结果
        passed = result.get("passed_cases", 0)
        total = result.get("total_cases", len(TEST_CASES))
        duration_sec = result.get("execution_time_sec", float("inf"))
        peak_mb = result.get("python_peak_memory_mb", 0.0)
        failures = result.get(
            "failures_sample", []
        )  # Catch Exceptions and Failed Test Cases
        sandbox_status = result.get("sandbox_status")
        failed_test_case_index = result.get("failed_test_case_index")

    except Exception as e:
        logger.exception(
            f"Error evaluating program {program_path}: {type(e).__name__}: {str(e)}"
        )
        _metrics = {
            "pass_rate": 0.0,
            "execution_time_sec": float("inf"),
            # "python_peak_memory_mb": 0.0,
            "combined_score": 0.0,
            "error": f"EvaluationError: {e}",
        }
        return EvaluationResult(
            metrics=_sanitize_metrics_for_json(_metrics),
            artifacts={
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
        )

    pass_rate = float(passed) / float(total) if total > 0 else 0.0
    # 2025.9.19: If the program is incorrect, then set the time and mem to infinite
    if pass_rate != 1:
        duration_sec = float("inf")

    # 评估参考解，建立性能基线
    reference_paths = discover_reference_paths(program_path)
    baseline_details: List[Dict[str, Any]] = []
    ref_time_list: List[float] = []
    ref_mem_list: List[float] = []

    # 2025.9.26: 降低并行度以减少资源消耗，将max_workers从2改为1
    with ThreadPoolExecutor(max_workers=1) as executor:
        # 提交所有任务
        future_to_index = {
            executor.submit(_evaluate_single_reference, ref_path, i): (ref_path, i)
            for i, ref_path in enumerate(reference_paths)
        }

        # 收集结果
        for future in as_completed(future_to_index):
            ref_path, i = future_to_index[future]
            try:
                result = future.result()
                baseline_details.append(result)
                if "ref_time" in result and "ref_mem" in result:
                    ref_time_list.append(result["ref_time"])
                    ref_mem_list.append(result["ref_mem"])
            except Exception as exc:
                logging.warning(
                    f"Reference solution {ref_path} generated an exception: {exc}"
                )

    # 2025.9.19: Sort the baseline_details by the original order of reference_paths
    baseline_details.sort(key=lambda x: reference_paths.index(x["path"]))

    # 计算性能得分
    time_score = 0.0
    mem_score = 0.0

    # Calc the Normalized Score
    # 2025.9.19: Implement Beyond metric (Mercury) temporarily
    def clamp(value, min_val, max_val):
        return max(min(value, max_val), min_val)

    # 2025.9.22: Add check for all equal solutions in ref_time_list
    # and ref_mem_list
    if len(ref_time_list) > 0:
        time_range = max(ref_time_list) - min(ref_time_list)
        if time_range > 0:
            time_score = (
                max(ref_time_list)
                - clamp(duration_sec, min(ref_time_list), max(ref_time_list))
            ) / time_range
        else:
            time_score = 1.0 if duration_sec <= min(ref_time_list) else 0.0
    else:
        time_score = 1.0 / (1.0 + max(duration_sec, 0.0) / T_REF)

    # 内存得分固定为0（Sandbox版本不测量内存）
    mem_score = 0.0

    # 综合得分（调整权重，因为不再考虑内存）
    combined_score = 0.5 * pass_rate + 0.5 * time_score

    metrics = {
        "pass_rate": pass_rate,
        "passed_cases": int(passed),
        "total_cases": int(total),
        "execution_time_sec": float(duration_sec),
        # "python_peak_memory_mb": float(peak_mb),
        "time_score": float(time_score),
        # "mem_score": float(mem_score),
        "combined_score": float(combined_score),
        "baseline_count": len(reference_paths),
        "valid_baseline_count": len(ref_time_list),
    }

    metrics = _sanitize_metrics_for_json(metrics)

    artifacts = {
        "failures": failures,
        "sandbox_status": sandbox_status,
        "failed_test_case_index": failed_test_case_index,
        # "baseline_details": baseline_details, # disabled for too long info
        "notes": "Evaluator uses built-in test cases and compares against reference baselines when available.",
    }

    return EvaluationResult(metrics=metrics, artifacts=artifacts)


# Stage-based evaluation for cascade evaluation
def evaluate_stage1(program_path):
    """First stage evaluation with fewer trials"""
    return evaluate(program_path)


def evaluate_stage2(program_path):
    """Second stage evaluation with more thorough testing"""
    # Full evaluation as in the main evaluate function
    return evaluate(program_path)
