"""
Evaluator for algorithm efficiency and correctness (refactored)

2025.9.19: 重构说明
- 将原本针对函数最小化的评估器重写为针对通用算法评估：正确率、时间效率、空间效率。
- 通过 AST 动态解析 test() 函数，将其中的每条 assert 作为独立用例执行并统计通过率。
- 使用 time.perf_counter() 测量总执行时间，使用 tracemalloc 测量 Python 内存峰值。
- 给出综合得分 combined_score（正确率优先，其次时间与内存），便于在进化过程中进行优化。
"""

# 2025.9.19: 删除了无用的 cgi.test / numpy / signal 引用，新增 ast、tracemalloc 等
import ast
import importlib.util
import time
from tomllib import load
import traceback
import tracemalloc
import os
import glob  # 2025.9.19: 引入文件系统与模式匹配，用于自动发现参考解
import logging
from typing import Any, Dict, List, Optional

from openevolve.evaluation_result import EvaluationResult

logger = logging.getLogger(__name__)

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


# deprecated
# Unused in code optimization evaluation
def safe_float(value):
    """Convert a value to float safely"""
    try:
        return float(value)
    except (TypeError, ValueError):
        print(f"Warning: Could not convert {value} of type {type(value)} to float")
        return 0.0


def _extract_test_function(tree: ast.AST) -> Optional[ast.FunctionDef]:
    """
    2025.9.19: 从 AST 中提取名为 test 的函数定义。
    """
    for node in getattr(tree, "body", []):
        if isinstance(node, ast.FunctionDef) and node.name == "test":
            return node
    return None


def discover_reference_paths(program_path: str) -> List[str]:
    """
    2025.9.19: 自动发现参考解路径的辅助函数
    
    在给定程序文件的同目录下，根据预定义的命名模式搜索参考解文件。
    支持的模式包括：*_ref.py, *_reference.py, *.reference.py, reference*.py, baseline*.py
    
    Args:
        program_path: 待评估程序的文件路径
        
    Returns:
        List[str]: 发现的参考解文件的绝对路径列表（去重且排除自身）
    """
    reference_paths: List[str] = []
    try:
        dirpath = os.path.dirname(os.path.abspath(program_path))
        patterns = [
            "*_ref.py",
            "*_reference.py",
            "*.reference.py",
            "reference*.py",
            "baseline*.py",
        ]
        seen = set()
        for pat in patterns:
            for p in glob.glob(os.path.join(dirpath, pat)):
                ap = os.path.abspath(p)
                if ap != os.path.abspath(program_path) and ap not in seen:
                    reference_paths.append(ap)
                    seen.add(ap)
    except Exception:
        # 失败则回退为空列表
        reference_paths = []
    
    return reference_paths


# 顶部新增：从 evaluate 中抽取的一次性执行函数，便于扩展与复用（2025.9.19）
def run_once_with_metrics(module, test_fn, source_code, program_path):
    """
    2025.9.19: 从 evaluate 中抽取，便于复用/扩展。
    执行 test() 函数体内的语句：
    - 普通语句按顺序 exec
    - assert 语句单独 eval 并统计通过/失败
    同时测量执行总时长与 Python 层峰值内存。

    Returns:
        passed_asserts, total_asserts, duration_sec, peak_mb, failures, non_assert_errors
    """
    env: Dict[str, Any] = {}
    g = module.__dict__  # 使用已加载模块的全局，以便访问 Solution 等定义

    total_asserts = 0
    passed_asserts = 0
    failures: List[Dict[str, Any]] = []
    non_assert_errors: List[Dict[str, Any]] = []

    start = time.perf_counter()
    tracemalloc.start()
    try:
        # 顺序执行 test() 函数体中的语句；遇到 assert 时单独评估表达式
        for idx, stmt in enumerate(test_fn.body):
            if isinstance(stmt, ast.Assert):
                total_asserts += 1
                try:
                    expr_code = compile(
                        ast.Expression(stmt.test), filename=program_path, mode="eval"
                    )
                    ok = eval(expr_code, g, env)
                    if ok:
                        passed_asserts += 1
                    else:
                        # 断言为 False，不抛异常，记录失败
                        try:
                            src = ast.get_source_segment(source_code, stmt)  # type: ignore[arg-type]
                        except Exception:
                            # Py<3.8 或特殊情况 fallback
                            try:
                                src = ast.unparse(stmt)
                            except Exception:
                                src = "<assert>"
                        failures.append(
                            {
                                "index": total_asserts,
                                "source": src,
                                "message": "assert evaluated to False",
                            }
                        )
                except Exception as e:
                    try:
                        src = ast.get_source_segment(source_code, stmt)  # type: ignore[arg-type]
                    except Exception:
                        try:
                            src = ast.unparse(stmt)
                        except Exception:
                            src = "<assert>"
                    failures.append(
                        {
                            "index": total_asserts,
                            "source": src,
                            "exception": type(e).__name__,
                            "error_message": str(e),
                            "traceback": traceback.format_exc(),
                        }
                    )
            else:
                # 执行前置或中间语句（例如 solution = Solution() 等）
                try:
                    code_obj = compile(
                        ast.Module(body=[stmt], type_ignores=[]),
                        filename=program_path,
                        mode="exec",
                    )
                    exec(code_obj, g, env)
                except Exception as e:
                    try:
                        src = ast.get_source_segment(source_code, stmt)  # type: ignore[arg-type]
                    except Exception:
                        try:
                            src = ast.unparse(stmt)
                        except Exception:
                            src = "<stmt>"
                    non_assert_errors.append(
                        {
                            "index": idx,
                            "stmt": src,
                            "exception": type(e).__name__,
                            "error_message": str(e),
                            "traceback": traceback.format_exc(),
                        }
                    )
        current, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    duration_sec = time.perf_counter() - start
    peak_mb = float(peak) / (1024.0 * 1024.0)
    return (
        passed_asserts,
        total_asserts,
        duration_sec,
        peak_mb,
        failures,
        non_assert_errors,
    )


def evaluate(program_path: str) -> EvaluationResult:
    """
    2025.9.19: 综合评估算法的正确率、时间效率与空间效率。

    约定：
    - 被评估的程序文件应定义可执行的环境（如 Solution 类等）以及一个 test() 函数。
    - 我们不直接调用 test()，而是解析其函数体，将每条 assert 当作独立用例来执行，统计通过率。

    指标：
    - pass_rate: 通过的断言数 / 断言总数
    - execution_time_sec: 执行 test 函数体（含前置语句与全部断言）的总耗时
    - python_peak_memory_mb: 执行期间 tracemalloc 观测到的 Python 内存峰值（MB）
    - combined_score: 综合得分（正确率优先，其次时间、内存）

    评分：
    - time_score = 1 / (1 + execution_time_sec / T_REF)
    - mem_score  = 1 / (1 + python_peak_memory_mb / M_REF)
    - combined_score = 0.7 * pass_rate + 0.2 * time_score + 0.1 * mem_score
      （可按需要调整权重与参考值）
    """
    # 参考参数（可视项目规模调整）
    T_REF = 10  # 参考时间（秒），越快越接近 1
    M_REF = 64.0  # 参考内存（MB），越省越接近 1

    try:
        # 1) 读取源代码并加载模块（用于获得全局环境，如 Solution 类等）
        with open(program_path, "r", encoding="utf-8") as f:
            source_code = f.read()

        spec = importlib.util.spec_from_file_location(
            "program_under_test", program_path
        )
        if spec is None or spec.loader is None:
            raise ImportError("Failed to create module spec for program")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # 2) 解析 AST，找到 test() 函数
        try:
            tree = ast.parse(source_code, filename=program_path)
        except SyntaxError as syn_err:
            return EvaluationResult(
                metrics={
                    "pass_rate": 0.0,
                    "execution_time_sec": 0.0,
                    "python_peak_memory_mb": 0.0,
                    "combined_score": 0.0,
                    "error": f"SyntaxError: {syn_err}",
                },
                artifacts={
                    "error_type": "SyntaxError",
                    "error_message": str(syn_err),
                    "full_traceback": traceback.format_exc(),
                },
            )

        test_fn = _extract_test_function(tree)
        if test_fn is None:
            return EvaluationResult(
                metrics={
                    "pass_rate": 0.0,
                    "execution_time_sec": 0.0,
                    "python_peak_memory_mb": 0.0,
                    "combined_score": 0.0,
                    "error": "Missing 'test' function",
                },
                artifacts={
                    "error_type": "MissingFunction",
                    "error_message": "Program is missing required 'test' function",
                    "suggestion": "Please provide a test() function that sets up environment and contains assert statements.",
                },
            )

        # 2025.9.19: 使用封装的函数发现参考解路径
        EVAL_TIMEOUT_SEC = 20  # 评估每个程序的一次执行超时时间（秒）
        reference_paths = discover_reference_paths(program_path)

        baseline_details: List[Dict[str, Any]] = []
        baseline_time_list: List[float] = []
        baseline_mem_list: List[float] = []

        # 3) 定义一次评估执行（含前置语句与断言逐条执行）
        # 2025.9.19: 已抽取为顶层函数 run_once_with_metrics(module, test_fn, source_code, program_path)
        
        # 4) 执行一次（可按需扩展为多次重复取平均）
        def _do_run():
            return run_once_with_metrics(module, test_fn, source_code, program_path)

        try:
            # 2025.9.19: 使用 run_with_timeout 包裹，避免无限阻塞
            passed, total, duration_sec, peak_mb, failures, non_assert_errors = run_with_timeout(
                _do_run, timeout_seconds=EVAL_TIMEOUT_SEC
            )
        except TimeoutError as e:
            return EvaluationResult(
                metrics={
                    "pass_rate": 0.0,
                    "execution_time_sec": float("inf"),
                    "python_peak_memory_mb": float("nan"),
                    "combined_score": 0.0,
                    "error": str(e),
                },
                artifacts={
                    "error_type": "Timeout",
                    "error_message": str(e),
                },
            )

        if total == 0:
            # 未发现断言，无法计算通过率
            return EvaluationResult(
                metrics={
                    "pass_rate": 0.0,
                    "execution_time_sec": duration_sec,
                    "python_peak_memory_mb": peak_mb,
                    "combined_score": 0.0,
                    "error": "No asserts found in test()",
                },
                artifacts={
                    "error_type": "NoAsserts",
                    "error_message": "No assert statements found inside test() function",
                    "advice": "Please add assert cases to test() to measure correctness.",
                },
            )

        # 2025.9.19: 评估参考解，建立性能基线（如存在）
        for ref_path in reference_paths[:3]:  # 限制最多 3 个参考解，避免开销过大
            try:
                with open(ref_path, "r", encoding="utf-8") as rf:
                    _ = rf.read()  # 目前不需要内容，仅验证可读性
                ref_spec = importlib.util.spec_from_file_location("program_reference", ref_path)
                if ref_spec is None or ref_spec.loader is None:
                    raise ImportError("Failed to create module spec for reference")
                ref_module = importlib.util.module_from_spec(ref_spec)
                ref_spec.loader.exec_module(ref_module)

                def _do_run_baseline():
                    # 注意：沿用候选程序的 test() AST，使输入一致，仅更换执行环境（globals）
                    return run_once_with_metrics(ref_module, test_fn, source_code, program_path)

                try:
                    (
                        b_passed,
                        b_total,
                        b_duration,
                        b_peak_mb,
                        b_failures,
                        b_non_assert_errors,
                    ) = run_with_timeout(_do_run_baseline, timeout_seconds=EVAL_TIMEOUT_SEC)
                except TimeoutError as te:
                    baseline_details.append(
                        {
                            "path": ref_path,
                            "error_type": "Timeout",
                            "error_message": str(te),
                        }
                    )
                    continue

                b_pass_rate = float(b_passed) / float(b_total) if b_total > 0 else 0.0
                baseline_time_list.append(float(b_duration))
                baseline_mem_list.append(float(b_peak_mb))
                baseline_details.append(
                    {
                        "path": ref_path,
                        "pass_rate": b_pass_rate,
                        "passed_asserts": int(b_passed),
                        "total_asserts": int(b_total),
                        "execution_time_sec": float(b_duration),
                        "python_peak_memory_mb": float(b_peak_mb),
                        "failures_sample": b_failures[:5],
                        "non_assert_errors": b_non_assert_errors,
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

        baseline_time_mean = (
            sum(baseline_time_list) / len(baseline_time_list) if baseline_time_list else None
        )
        baseline_mem_mean = (
            sum(baseline_mem_list) / len(baseline_mem_list) if baseline_mem_list else None
        )

        pass_rate = float(passed) / float(total)
        # 2025.9.19: 优先使用"相对参考解"的归一化得分；否则回退到固定参考常数
        if baseline_time_mean is not None and baseline_time_mean > 0.0:
            time_ratio = max(duration_sec, 0.0) / max(baseline_time_mean, 1e-9)
            time_score = 1.0 / (1.0 + time_ratio)
        else:
            time_score = 1.0 / (1.0 + max(duration_sec, 0.0) / T_REF)

        if baseline_mem_mean is not None and baseline_mem_mean > 0.0:
            mem_ratio = max(peak_mb, 0.0) / max(baseline_mem_mean, 1e-9)
            mem_score = 1.0 / (1.0 + mem_ratio)
        else:
            mem_score = 1.0 / (1.0 + max(peak_mb, 0.0) / M_REF)

        combined_score = 0.7 * pass_rate + 0.2 * time_score + 0.1 * mem_score

        metrics = {
            "pass_rate": pass_rate,
            "passed_asserts": int(passed),
            "total_asserts": int(total),
            "execution_time_sec": float(duration_sec),
            "avg_assert_time_ms": float(1000.0 * duration_sec / total)
            if total > 0
            else None,
            "python_peak_memory_mb": float(peak_mb),
            "time_score": float(time_score),
            "mem_score": float(mem_score),
            "combined_score": float(combined_score),
            # 2025.9.19: 基线汇总（若存在）
            "baseline_count": len(baseline_time_list),
            "baseline_time_mean_sec": float(baseline_time_mean)
            if baseline_time_mean is not None
            else None,
            "baseline_mem_mean_mb": float(baseline_mem_mean)
            if baseline_mem_mean is not None
            else None,
        }

        artifacts = {
            "failures": failures[:10],
            "non_assert_errors": non_assert_errors,
            "notes": "This evaluator parses test() and evaluates each assert independently to compute pass rate, timing, and memory.",
            # 2025.9.19: 记录用于归一化的参考信息
            "reference_paths": reference_paths[:3],
            "baseline_details": baseline_details,
            "normalization": "time_score/mem_score prefer relative-to-baseline (candidate/baseline) when baseline exists; otherwise fall back to absolute refs.",
        }

        return EvaluationResult(metrics=metrics, artifacts=artifacts)

    except Exception as e:
        # 顶层兜底
        return EvaluationResult(
            metrics={
                "pass_rate": 0.0,
                "execution_time_sec": 0.0,
                "python_peak_memory_mb": 0.0,
                "combined_score": 0.0,
                "error": str(e),
            },
            artifacts={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "full_traceback": traceback.format_exc(),
            },
        )


# Stage-based evaluation for cascade evaluation
def evaluate_stage1(program_path):
    """First stage evaluation with fewer trials"""
    return evaluate(program_path)


def evaluate_stage2(program_path):
    """Second stage evaluation with more thorough testing"""
    # Full evaluation as in the main evaluate function
    return evaluate(program_path)
