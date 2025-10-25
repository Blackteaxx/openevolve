#!/usr/bin/env python3
import sys
import os

# Ensure repo root is on PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from pprint import pprint

from openevolve.config import Config
from openevolve.prompt.templates import TemplateManager
from openevolve.experience_kb_service import ExperienceKBService


def run(config_path: str) -> None:
    print(f"[load] {config_path}")
    cfg = Config.from_yaml(config_path)
    kb_cfg = cfg.experience_kb

    # Print raw experience_kb dict from yaml for debugging
    import yaml
    with open(config_path, 'r') as f:
        raw = yaml.safe_load(f)
    print("[yaml.experience_kb]")
    pprint(raw.get('experience_kb'))

    # Avoid initializing LLM clients for this smoke test
    kb_cfg.llm = None

    # Print parsed dataclass fields
    print("[parsed.experience_kb]")
    pprint({k: getattr(kb_cfg, k) for k in dir(kb_cfg) if not k.startswith('__') and not callable(getattr(kb_cfg, k))})

    # Initialize templates (respect custom template dir if provided)
    tm = TemplateManager(custom_template_dir=cfg.prompt.template_dir)

    # Use current working directory for KB storage to match repo layout
    svc = ExperienceKBService(
        template_manager=tm,
        config=kb_cfg,
        llm_ensemble=None,
        output_dir=os.getcwd(),
    )

    print(f"[summary_mode={getattr(kb_cfg, 'summary_mode', 'full')} max_k={getattr(kb_cfg, 'random_rules_max_k', None)}]")

    # Call twice to observe randomness
    s1 = svc.get_summary()
    print("\n----- SUMMARY (call 1) -----")
    print(s1)

    s2 = svc.get_summary()
    print("\n----- SUMMARY (call 2) -----")
    print(s2)


if __name__ == "__main__":
    # Default to KB example config; allow overriding via argv
    default_config = "examples/code_optimization_template_KB/config_template.yaml"
    config_path = sys.argv[1] if len(sys.argv) > 1 else default_config
    run(config_path)