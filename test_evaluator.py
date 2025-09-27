#!/usr/bin/env python3
"""
evaluator.py 测试脚本
测试evaluator的各项功能和性能
"""

import os
import sys
import tempfile
import time

sys.path.insert(0, "/data/CodeEfficiency/openevolve")

# 导入evaluator模块
sys.path.insert(
    0, "/data/CodeEfficiency/openevolve/examples/code_optimization_template"
)
from evaluator import evaluate
from openevolve.sandbox import Sandbox


def test_basic_functionality():
    """测试基本功能"""
    print("=== 测试基本功能 ===")

    # 创建一个简单的正确解决方案
    correct_solution = '''
# Definition for singly-linked list.
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

class Solution:
    def addTwoNumbers(self, l1, l2):
        """Add Two Numbers - 正确实现"""
        dummy = ListNode()
        curr = dummy
        carry = 0
        
        while l1 or l2 or carry:
            val1 = l1.val if l1 else 0
            val2 = l2.val if l2 else 0
            
            total = val1 + val2 + carry
            carry = total // 10
            curr.next = ListNode(total % 10)
            curr = curr.next
            
            if l1:
                l1 = l1.next
            if l2:
                l2 = l2.next
        
        return dummy.next
'''

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(correct_solution)
        solution_path = f.name

    try:
        print(f"✓ 创建测试解决方案: {solution_path}")

        # 测试评估
        result = evaluate(solution_path)
        print("✓ 评估完成")
        print(f"  - 结果: {result}")

        return result

    finally:
        os.unlink(solution_path)


def test_incorrect_solution():
    """测试错误解决方案"""
    print("\n=== 测试错误解决方案 ===")

    # 创建一个总是返回None的错误解决方案
    incorrect_solution = '''
# Definition for singly-linked list.
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

class Solution:
    def addTwoNumbers(self, l1, l2):
        """错误实现 - 总是返回None"""
        return None
'''

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(incorrect_solution)
        solution_path = f.name

    try:
        print(f"✓ 创建错误解决方案: {solution_path}")

        result = evaluate(solution_path)
        print("✓ 评估完成")
        print(f"  - 结果: {result}")

        return result

    finally:
        os.unlink(solution_path)


def test_timeout_solution():
    """测试超时解决方案"""
    print("\n=== 测试超时解决方案 ===")

    # 创建一个会超时的解决方案
    timeout_solution = '''
# Definition for singly-linked list.
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

class Solution:
    def addTwoNumbers(self, l1, l2):
        """超时实现 - 无限循环"""
        import time
        time.sleep(15)  # 超过timeout限制
        return ListNode(0)
'''

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(timeout_solution)
        solution_path = f.name

    try:
        print(f"✓ 创建超时解决方案: {solution_path}")

        start_time = time.time()
        result = evaluate(solution_path)
        end_time = time.time()

        print(f"✓ 评估完成 (耗时: {end_time - start_time:.2f}秒)")
        print(f"  - 结果: {result}")

        return result

    finally:
        os.unlink(solution_path)


def test_syntax_error_solution():
    """测试语法错误解决方案"""
    print("\n=== 测试语法错误解决方案 ===")

    # 创建一个有语法错误的解决方案
    syntax_error_solution = '''
# Definition for singly-linked list.
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

class Solution:
    def addTwoNumbers(self, l1, l2):
        """语法错误实现"""
        if l1 and l2  # 缺少冒号
            return ListNode(0)
        return None
    # 缺少缩进
print("syntax error")
'''

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(syntax_error_solution)
        solution_path = f.name

    try:
        print(f"✓ 创建语法错误解决方案: {solution_path}")

        result = evaluate(solution_path)
        print("✓ 评估完成")
        print(f"  - 结果: {result}")

        return result

    finally:
        os.unlink(solution_path)


def test_memory_limit_solution():
    """测试内存超限解决方案"""
    print("\n=== 测试内存超限解决方案 ===")

    # 创建一个会消耗大量内存的解决方案
    memory_limit_solution = '''
# Definition for singly-linked list.
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

class Solution:
    def addTwoNumbers(self, l1, l2):
        """消耗大量内存的解决方案"""
        # 创建大量内存占用
        big_list = []
        for i in range(1000000):  # 创建100万个列表
            big_list.append([0] * 1000)  # 每个列表包含1000个元素
        
        # 简单的正确实现
        dummy = ListNode()
        curr = dummy
        carry = 0
        
        while l1 or l2 or carry:
            val1 = l1.val if l1 else 0
            val2 = l2.val if l2 else 0
            
            total = val1 + val2 + carry
            carry = total // 10
            curr.next = ListNode(total % 10)
            curr = curr.next
            
            if l1:
                l1 = l1.next
            if l2:
                l2 = l2.next
        
        return dummy.next
'''

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(memory_limit_solution)
        solution_path = f.name

    try:
        print(f"✓ 创建内存超限解决方案: {solution_path}")

        result = evaluate(solution_path)
        print("✓ 评估完成")
        print(f"  - 结果: {result}")

        return result

    finally:
        os.unlink(solution_path)


def test_performance_comparison():
    """测试性能对比"""
    print("\n=== 测试性能对比 ===")

    # 高效解决方案
    efficient_solution = '''
# Definition for singly-linked list.
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

class Solution:
    def addTwoNumbers(self, l1, l2):
        """高效实现"""
        dummy = ListNode()
        curr = dummy
        carry = 0
        
        while l1 or l2 or carry:
            val1 = l1.val if l1 else 0
            val2 = l2.val if l2 else 0
            
            total = val1 + val2 + carry
            carry = total // 10
            curr.next = ListNode(total % 10)
            curr = curr.next
            
            if l1:
                l1 = l1.next
            if l2:
                l2 = l2.next
        
        return dummy.next
'''

    # 低效解决方案 - 使用更多不必要的操作来放大性能差异
    inefficient_solution = '''
# Definition for singly-linked list.
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

class Solution:
    def addTwoNumbers(self, l1, l2):
        """低效实现 - 使用字符串转换和多次计算"""
        # 低效：将链表转换为字符串再转回数字
        def list_to_string(node):
            result = ""
            while node:
                result = str(node.val) + result  # 低效的字符串拼接
                node = node.next
            return result if result else "0"
        
        # 低效：多次转换
        num1_str = list_to_string(l1)
        num2_str = list_to_string(l2)
        
        # 转换为整数并相加
        num1 = int(num1_str)
        num2 = int(num2_str)
        total = num1 + num2
        
        # 转换回链表
        total_str = str(total)
        dummy = ListNode()
        curr = dummy
        
        for digit in reversed(total_str):
            curr.next = ListNode(int(digit))
            curr = curr.next
        
        return dummy.next
'''

    solutions = [
        ("高效解决方案", efficient_solution),
        ("低效解决方案", inefficient_solution),
    ]

    results = []

    for name, solution in solutions:
        print(f"\n--- 测试 {name} ---")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(solution)
            solution_path = f.name

        try:
            result = evaluate(solution_path)
            results.append((name, result))

            print(f"  - 结果: {result}")

        finally:
            os.unlink(solution_path)

    # 性能对比
    if len(results) == 2:
        print("\n--- 性能对比 ---")
        efficient_result = results[0][1]
        inefficient_result = results[1][1]

        print(f"高效解决方案结果: {efficient_result}")
        print(f"低效解决方案结果: {inefficient_result}")

    return results


def test_sandbox_integration():
    """测试与Sandbox的集成"""
    print("\n=== 测试Sandbox集成 ===")

    # 测试Sandbox直接调用
    sample = {
        "solution": """
# Definition for singly-linked list.
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

class Solution:
    def addTwoNumbers(self, l1, l2):
        # 简单逻辑：只处理单个数字
        if l1 and l2:
            return ListNode((l1.val + l2.val) % 10)
        return ListNode(0)
""",
        "timeout": 10,
        "test_cases": [
            {"input": [[2, 4, 3], [5, 6, 4]], "expected": [7, 0, 8]},
            {"input": [[0], [0]], "expected": [0]},
        ],
        "entry_point": "addTwoNumbers",
        "convert_offline": "def convert_offline(case): import lctk; inputs, expected = case; inputs = tuple([lctk.linkedList(inputs[0]), lctk.linkedList(inputs[1])]); return inputs, expected",
        "evaluate_offline": "def evaluate_offline(inputs, outputs, expected): import lctk; outputs = lctk.linkedList2Arr(outputs); return outputs == expected",
        "maximum_memory_bytes": 128 * 1024 * 1024,
        "solution_index": 0,
    }

    print("测试Sandbox.run_sample...")
    result = Sandbox.run_sample(sample)
    print(f"✓ Sandbox执行结果: {result}")

    return result


def main():
    """主测试函数"""
    print("开始evaluator.py全面测试...\n")

    try:
        # # 基本功能测试
        basic_result = test_basic_functionality()

        # # 错误情况测试
        # incorrect_result = test_incorrect_solution()

        # # 超时测试
        # timeout_result = test_timeout_solution()

        # # 语法错误测试
        # syntax_error_result = test_syntax_error_solution()

        # # 内存超限测试
        # memory_limit_result = test_memory_limit_solution()

        # 性能对比测试
        performance_results = test_performance_comparison()

        # # Sandbox集成测试
        # sandbox_result = test_sandbox_integration()

        # # 总结
        # print("\n" + "=" * 50)
        # print("测试总结")
        # print("=" * 50)
        # print(f"✓ 基本功能测试: {basic_result}")
        # print(f"✓ 错误解决方案测试: {incorrect_result}")
        # print(f"✓ 超时测试: {timeout_result}")
        # print(f"✓ 语法错误测试: {syntax_error_result}")
        # print(f"✓ 内存超限测试: {memory_limit_result}")
        # print(f"✓ Sandbox集成测试: {sandbox_result}")

        if performance_results:
            print("\n性能测试结果:")
            for name, result in performance_results:
                print(f"  - {name}: {result}")

        print("\n🎉 所有测试完成!")

    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
