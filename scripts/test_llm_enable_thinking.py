#!/usr/bin/env python3
import asyncio
import logging
from types import SimpleNamespace
from openevolve.llm.openai import OpenAILLM

"""
Minimal real-call test for enable_thinking injection.
- Uses your provided llm config (api_base points to local OpenAI-compatible server)
- No monkey patching; makes actual requests
- DEBUG logging enabled to show API parameters (including extra_body)
"""

logging.basicConfig(level=logging.DEBUG, format="[%(levelname)s] %(message)s")

cfg = SimpleNamespace(
    name="Qwen3-32B",
    system_message="You are a helpful assistant.",
    temperature=0.7,
    top_p=0.8,
    max_tokens=8000,
    timeout=120,
    retries=0,
    retry_delay=0.1,
    api_base="http://127.0.0.1:8080/v1",
    api_key="code-efficiency",
    random_seed=None,
    reasoning_effort=None,
)

llm = OpenAILLM(model_cfg=cfg)

async def main():
    try:
        print("\nCase 1: enable_thinking=True with extra_body top_k=20")
        r1 = await llm.generate_with_context(
            system_message="sys",
            messages=[{"role": "user", "content": "hello"}],
            enable_thinking=True,
            extra_body={"top_k": 20},
        )
        print("Response1:\n", r1)
    except Exception as e:
        print("Case 1 error:", e)

    try:
        print("\nCase 2: enable_thinking=False no extra_body")
        r2 = await llm.generate_with_context(
            system_message="sys",
            messages=[{"role": "user", "content": "hello"}],
            enable_thinking=False,
        )
        print("Response2:\n", r2)
    except Exception as e:
        print("Case 2 error:", e)

    try:
        print("\nCase 3: no enable_thinking, extra_body passthrough top_k=10")
        r3 = await llm.generate_with_context(
            system_message="sys",
            messages=[{"role": "user", "content": "hello"}],
            extra_body={"top_k": 10},
        )
        print("Response3:\n", r3)
    except Exception as e:
        print("Case 3 error:", e)

if __name__ == "__main__":
    asyncio.run(main())