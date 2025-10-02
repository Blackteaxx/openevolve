#!/usr/bin/env python3
"""
测试新的信息架构是否正常工作
"""

from openevolve.config import PromptConfig
from openevolve.prompt.sampler import PromptSampler

def test_new_architecture():
    """测试新的信息架构"""
    
    # 创建配置
    config = PromptConfig()
    config.include_artifacts = True
    
    # 创建 sampler
    sampler = PromptSampler(config)
    
    # 准备测试数据
    current_program = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
    
    parent_program = """
def fibonacci(n):
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fibonacci(n-1) + fibonacci(n-2)
"""
    
    current_metrics = {
        "runs_successfully": 1.0,
        "value_score": 0.9579,
        "distance_score": 0.7841,
        "combined_score": 1.2437
    }
    
    parent_metrics = {
        "runs_successfully": 1.0,
        "value_score": 0.8234,
        "distance_score": 0.7841,
        "combined_score": 1.1234
    }
    
    
    top_programs = [
        {
            "code": current_program,
            "metrics": current_metrics,
            "metadata": {
                "explanation": "Simplified condition logic for better readability"
            }
        }
    ]
    
    program_artifacts = {
        "stdout": "Test output",
        "stderr": "",
        "execution_time": "0.001s"
    }
    
    # 构建 prompt
    prompt = sampler.build_prompt(
        current_program=current_program,
        parent_program=parent_program,
        program_metrics=current_metrics,
        parent_metrics=parent_metrics,  
        top_programs=top_programs,
        language="python",
        program_artifacts=program_artifacts,
        feature_dimensions=["value_score", "distance_score"]
    )
    
    print("=== 新信息架构测试结果 ===")
    print("\n--- System Message ---")
    print(prompt["system"][:200] + "..." if len(prompt["system"]) > 200 else prompt["system"])
    
    print("\n--- User Message (前 1000 字符) ---")
    print(prompt["user"])
    
    # 验证关键元素是否存在
    user_msg = prompt["user"]
    
    checks = [
        ("Current Program", "## Current Program" in user_msg),
        ("Current Metrics", "## Current Metrics" in user_msg),
        ("Parent vs Current", "## Parent vs Current" in user_msg),
        ("Current Artifacts", "## Current Artifacts" in user_msg),
        ("Metrics diff symbols", any(symbol in user_msg for symbol in ["↑", "↓", "≈"])),
        ("Program Evolution History", "# Program Evolution History" in user_msg),
        ("Top Performing Programs", "## Top Performing Programs" in user_msg),
    ]
    
    print("\n--- 架构元素检查 ---")
    for check_name, result in checks:
        status = "✓" if result else "✗"
        print(f"{status} {check_name}")
    
    return all(result for _, result in checks)

if __name__ == "__main__":
    success = test_new_architecture()
    print(f"\n测试结果: {'成功' if success else '失败'}")