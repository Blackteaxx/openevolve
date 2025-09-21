"""
Evaluator for algorithm efficiency and correctness (refactored)

2025.9.19: 重构说明（当前实现）
- 评估目标：通用算法的正确率、时间效率、空间效率。
- 取消对 AST 解析与 test() 函数的依赖，改为使用评估器内部的内置测试用例。
- 约定被测程序提供 class Solution，并在其中实现入口方法（默认 ENTRY_POINT）。
- 使用 time.perf_counter() 测量总执行时间，使用 tracemalloc 测量 Python 内存峰值。
- 先尝试发现参考解作为性能基线，否则回退到固定参考常量；输出综合得分 combined_score（正确率优先，其次时间与内存）。
"""
# 2025.9.19: 删除了无用的 cgi.test / numpy / signal 引用，新增 ast、tracemalloc 等
import ast
import importlib.util
import time
import traceback
import tracemalloc
import os
import glob  # 2025.9.19: 引入文件系统与模式匹配，用于自动发现参考解
import sys
import logging
import copy
from typing import Any, Dict, List, Optional

from openevolve.evaluation_result import EvaluationResult

logger = logging.getLogger(__name__)

# Define the entry point function name, test cases and some consts
ENTRY_POINT = "exist"
TEST_CASES = [{'expected': True,
  'input': [[['A', 'B', 'C', 'E'], ['S', 'F', 'C', 'S'], ['A', 'D', 'E', 'E']],
            'ABCCED']},
 {'expected': True,
  'input': [[['A', 'B', 'C', 'E'], ['S', 'F', 'C', 'S'], ['A', 'D', 'E', 'E']],
            'SEE']},
 {'expected': False,
  'input': [[['A', 'B', 'C', 'E'], ['S', 'F', 'C', 'S'], ['A', 'D', 'E', 'E']],
            'ABCB']},
 {'expected': True, 'input': [[['D']], 'D']},
 {'expected': False, 'input': [[['J'], ['A']], 'ELIJ']},
 {'expected': False,
  'input': [[['X', 'B', 'G', 'T', 'C', 'F'],
             ['T', 'H', 'S', 'A', 'G', 'M'],
             ['B', 'R', 'S', 'K', 'E', 'O'],
             ['D', 'S', 'J', 'K', 'Y', 'Q'],
             ['V', 'H', 'H', 'K', 'C', 'M'],
             ['E', 'V', 'A', 'W', 'J', 'P']],
            'EQNRCAPOH']},
 {'expected': False,
  'input': [[['D', 'C', 'E', 'F'],
             ['A', 'R', 'L', 'Y'],
             ['O', 'G', 'B', 'V'],
             ['V', 'P', 'F', 'X'],
             ['Y', 'X', 'S', 'S']],
            'JPNKADNG']},
 {'expected': False,
  'input': [[['R', 'V', 'K', 'B', 'O', 'C'],
             ['S', 'T', 'G', 'I', 'X', 'G'],
             ['R', 'T', 'C', 'W', 'U', 'M']],
            'KAAEYPUE']}]
EVAL_TIMEOUT_SEC = 10 # 评估超时时间（秒）
T_REF = 10.0  # 参考时间（秒）
M_REF = 64.0  # 参考内存（MB）


def run_with_timeout(func, args=(), kwargs={}, timeout_seconds=10):
    """
    Run a function with a timeout using concurrent.futures

    Args:
        func: Function to run
        args: Arguments to pass to the function
        kwargs: Keyword arguments to pass to the function
        timeout_seconds: Timeout in seconds

    Returns:
        Result of the function or raises TimeoutError
        assume result is a int, represent test case pass ratio
    """
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=timeout_seconds)
        except concurrent.futures.TimeoutError:
            raise TimeoutError(f"Function timed out after {timeout_seconds} seconds")


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
            reference_paths = [os.path.join(ref_solutions_dir, f) for f in os.listdir(ref_solutions_dir) if f.endswith(".py")]
    except Exception:
        # 失败则回退为空列表
        reference_paths = []
    return reference_paths


def execute_and_measure(mod, test_cases, entry_point: str):
    """在给定模块上执行内置测试并测量时间/内存。返回 (passed, total, duration_sec, peak_mb, failures)。"""
    total = len(test_cases)
    # 1) 获取 Solution 类并实例化
    try:
        SolutionClass = getattr(mod, "Solution", None)
    except Exception as e:
        return (
            0,
            total,
            0.0,
            0.0,
            [
                {
                    "exception": type(e).__name__,
                    "error_message": str(e),
                    "where": "getattr(Solution)",
                }
            ],
        )
    if SolutionClass is None:
        return (
            0,
            total,
            0.0,
            0.0,
            [
                {
                    "error_type": "MissingClass",
                    "error_message": "Program missing class 'Solution'",
                }
            ],
        )
    try:
        sol = SolutionClass()
    except Exception as e:
        return (
            0,
            total,
            0.0,
            0.0,
            [
                {
                    "exception": type(e).__name__,
                    "error_message": str(e),
                    "where": "instantiate(Solution)",
                }
            ],
        )

    # 2) 选择入口方法
    method = getattr(sol, entry_point, None)
    if method is None:
        return (
            0,
            total,
            0.0,
            0.0,
            [
                {
                    "error_type": "MissingMethod",
                    "error_message": f"Solution missing entry point method '{entry_point}'",
                }
            ],
        )

    # 3) 执行测试用例并测量
    passed = 0
    failures = []
    start = time.perf_counter()
    tracemalloc.start()
    try:
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        with open(os.devnull, 'w') as devnull:
            sys.stdout = devnull
            sys.stderr = devnull
            try:
                for idx, case in enumerate(test_cases):
                    args = case["input"]
                    expected = case["expected"]
                    try:
                        result = method(*args)
                        ok = result == expected
                        if ok:
                            passed += 1
                        else:
                            failures.append(
                                {
                                    "index": idx,
                                    "input": case["input"],
                                    "expected": expected,
                                    "got": result,
                                    "method": entry_point,
                                }
                            )
                    except Exception as ex:
                        failures.append(
                            {
                                "index": idx,
                                "input": case["input"],
                                "expected": expected,
                                "exception": type(ex).__name__,
                                "error_message": str(ex),
                                "traceback": traceback.format_exc(),
                                "method": entry_point,
                            }
                        )
            finally:
                sys.stdout = original_stdout
                sys.stderr = original_stderr
        current, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    duration_sec = time.perf_counter() - start
    peak_mb = float(peak) / (1024.0 * 1024.0)
    return (passed, total, duration_sec, peak_mb, failures)

def evaluate(program_path: str) -> EvaluationResult:
    """
    2025.9.19: 综合评估算法的正确率、时间效率与空间效率。

    约定：被评估程序需定义 class Solution，包含可调用的方法（如 solve 或 findMedianSortedArrays）。

    指标：
    - pass_rate: 通过的用例数 / 用例总数
    - execution_time_sec: 执行全部用例的总耗时
    - python_peak_memory_mb: 执行期间 tracemalloc 观测到的 Python 内存峰值（MB）
    - time_score, mem_score: 归一化时间/内存得分（优先相对参考基线，否则回退到常量基线）
    - combined_score: 0.3 * pass_rate + 0.5 * time_score + 0.2 * mem_score
    """

    # 加载候选程序模块
    try:
        spec = importlib.util.spec_from_file_location("program_under_test", program_path)
        if spec is None or spec.loader is None:
            raise ImportError("Failed to create module spec for program")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception as e:
        return EvaluationResult(
            metrics={
                "pass_rate": 0.0,
                "execution_time_sec": 0.0,
                "python_peak_memory_mb": 0.0,
                "combined_score": 0.0,
                "error": f"ImportError: {e}",
            },
            artifacts={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "full_traceback": traceback.format_exc(),
            },
        )

    # 评估候选程序（带超时保护）
    try:
        passed, total, duration_sec, peak_mb, failures = run_with_timeout(
            lambda: execute_and_measure(module, copy.deepcopy(TEST_CASES), ENTRY_POINT), timeout_seconds=EVAL_TIMEOUT_SEC
        )
    except TimeoutError as te:
        return EvaluationResult(
            metrics={
                "pass_rate": 0.0,
                "execution_time_sec": float("inf"),
                "python_peak_memory_mb": float("inf"),
                "combined_score": 0.0,
                "error": str(te),
            },
            artifacts={
                "error_type": "Timeout",
                "error_message": str(te),
            },
        )

    pass_rate = float(passed) / float(total) if total > 0 else 0.0
    # 2025.9.19: If the program is incorrect, then set the time and mem to infinite
    if pass_rate != 1:
        duration_sec = float("inf")
        peak_mb = float("inf")

    # 评估参考解，建立性能基线
    reference_paths = discover_reference_paths(program_path)
    baseline_details: List[Dict[str, Any]] = []
    ref_time_list: List[float] = []
    ref_mem_list: List[float] = []

    for i, ref_path in enumerate(reference_paths):
        try:
            mod_name = f"program_reference_{i}"
            ref_spec = importlib.util.spec_from_file_location(mod_name, ref_path)
            if ref_spec is None or ref_spec.loader is None:
                raise ImportError("Failed to create module spec for reference")
            ref_module = importlib.util.module_from_spec(ref_spec)
            ref_spec.loader.exec_module(ref_module)

            b_passed, b_total, b_duration, b_peak_mb, b_failures = run_with_timeout(
                lambda: execute_and_measure(ref_module, copy.deepcopy(TEST_CASES), ENTRY_POINT), timeout_seconds=EVAL_TIMEOUT_SEC
            )
            b_pass_rate = float(b_passed) / float(b_total) if b_total > 0 else 0.0
            baseline_details.append(
                {
                    "path": ref_path,
                    "pass_rate": b_pass_rate,
                    "passed_cases": int(b_passed),
                    "total_cases": int(b_total),
                    "execution_time_sec": float(b_duration),
                    "python_peak_memory_mb": float(b_peak_mb),
                    "failures_sample": b_failures[:5],
                }
            )
            # 收集完全通过测试用例的参考解的时间和内存数据
            if b_passed == b_total and b_total > 0:
                ref_time_list.append(float(b_duration))
                ref_mem_list.append(float(b_peak_mb))
        except TimeoutError as te:
            baseline_details.append(
                {
                    "path": ref_path,
                    "error_type": "Timeout",
                    "error_message": str(te),
                }
            )
        except Exception as be:
            baseline_details.append(
                {
                    "path": ref_path,
                    "error_type": type(be).__name__,
                    "error_message": str(be),
                    "traceback": traceback.format_exc(),
                }
            )
        finally:
            if mod_name in sys.modules:
                del sys.modules[mod_name]

    # Calc the Normalized Score 
    # 2025.9.19: Implement Beyond metric (Mercury) temporarily
    def clamp(value, min_val, max_val):
        return max(min(value, max_val), min_val)
    
    if len(ref_time_list) > 0:
        time_score = (
            max(ref_time_list)
            - clamp(duration_sec, min(ref_time_list), max(ref_time_list))
        ) / (max(ref_time_list) - min(ref_time_list))
    else:
        time_score = 1.0 / (1.0 + max(duration_sec, 0.0) / T_REF)

    if len(ref_mem_list) > 0:
        mem_score = (
            max(ref_mem_list)
            - clamp(peak_mb, min(ref_mem_list), max(ref_mem_list))
        ) / (max(ref_mem_list) - min(ref_mem_list))
    else:
        mem_score = 1.0 / (1.0 + max(peak_mb, 0.0) / M_REF)

    combined_score = 0.3 * pass_rate + 0.5 * time_score + 0.2 * mem_score

    metrics = {
        "pass_rate": pass_rate,
        "passed_cases": int(passed),
        "total_cases": int(total),
        "execution_time_sec": float(duration_sec),
        "python_peak_memory_mb": float(peak_mb),
        "time_score": float(time_score),
        "mem_score": float(mem_score),
        "combined_score": float(combined_score),
        "baseline_count": len(reference_paths),
    }

    artifacts = {
        "failures": failures,
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
