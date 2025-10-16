"""
Experience Knowledge Base (KB) service for capturing and injecting learnings.

Refactor notes:
- Storage uses a single Markdown file (experience.md) containing high-level
  recommendations and lessons; legacy events storage has been removed.
- Interface aligns with ExplanationService by accepting a pre-built prompt dict in
  generate(prompt), while keeping build_update_prompt for constructing prompts.
- The entire Markdown content is included in update prompts so the model can revise
  and return the complete updated Markdown document each time.
"""

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

import json

from openevolve.config import ExperienceKBConfig, LLMConfig
from openevolve.llm.ensemble import LLMEnsemble


@dataclass
class KBUpdateResult:
    summary: Optional[str] = None
    rules_json: Optional[str] = None
    prompt: Optional[Dict[str, str]] = None
    response: Optional[str] = None


class ExperienceKBService:
    """Manages KB storage, summary generation, and update prompts"""

    def __init__(
        self,
        template_manager,
        config: ExperienceKBConfig,
        llm_ensemble: Optional[LLMEnsemble] = None,
        output_dir: Optional[str] = None,
    ) -> None:
        self.template_manager = template_manager
        self.config = config or ExperienceKBConfig()

        # Resolve storage path
        base_dir = output_dir or os.getcwd()
        storage_dir = self.config.storage_dir or os.path.join(base_dir, "experience_kb")
        os.makedirs(storage_dir, exist_ok=True)
        self.storage_dir = storage_dir
        # Primary Markdown storage
        self.experience_md_path = os.path.join(self.storage_dir, "experience.md")
        # Ensure markdown file exists
        try:
            if not os.path.exists(self.experience_md_path):
                with open(self.experience_md_path, "w", encoding="utf-8") as f:
                    f.write("# Experience Knowledge Base\n\n")
        except Exception:
            # Swallow IO errors in worker context to avoid crashing
            pass

        # Resolve LLM ensemble
        if llm_ensemble is not None:
            self.llm = llm_ensemble
        elif getattr(self.config, "llm", None):
            cfg: LLMConfig = self.config.llm
            # Prefer explanation-like config: use explicit models list
            self.llm = LLMEnsemble(cfg.models)
        else:
            self.llm = None

    def set_output_dir(self, base_dir: Optional[str]) -> None:
        """Update storage directory based on a new base output directory"""
        if not base_dir:
            return
        storage_dir = self.config.storage_dir or os.path.join(base_dir, "experience_kb")
        try:
            os.makedirs(storage_dir, exist_ok=True)
            self.storage_dir = storage_dir
            self.experience_md_path = os.path.join(self.storage_dir, "experience.md")
            if not os.path.exists(self.experience_md_path):
                with open(self.experience_md_path, "w", encoding="utf-8") as f:
                    f.write("# Experience Knowledge Base\n\n")
        except Exception:
            # Keep previous paths if unable to update
            pass

    # --- Markdown storage helpers ---
    def _read_markdown(self) -> str:
        try:
            if not os.path.exists(self.experience_md_path):
                return ""
            with open(self.experience_md_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""

    def _write_markdown(self, content: str) -> None:
        try:
            with open(self.experience_md_path, "w", encoding="utf-8") as f:
                f.write(content or "")
        except Exception:
            # Swallow IO errors in worker context
            pass

    def _safe_decode_artifact(self, value: Union[str, bytes]) -> str:
        if isinstance(value, bytes):
            try:
                return value.decode("utf-8", errors="replace")
            except Exception:
                return "[binary artifact]"
        return str(value)

    def _format_metrics(self, metrics: Dict[str, Any]) -> str:
        lines: List[str] = []
        for k, v in (metrics or {}).items():
            if isinstance(v, (int, float)):
                try:
                    lines.append(f"- {k}: {v:.4f}")
                except Exception:
                    lines.append(f"- {k}: {v}")
            else:
                lines.append(f"- {k}: {v}")
        return "\n".join(lines) if lines else "(no metrics)"

    def _format_parent_metrics(self, parent_metrics: Optional[Dict[str, Any]]) -> str:
        lines: List[str] = []
        for k, v in (parent_metrics or {}).items():
            if isinstance(v, (int, float)):
                try:
                    lines.append(f"- {k}: {v:.4f}")
                except Exception:
                    lines.append(f"- {k}: {v}")
            else:
                lines.append(f"- {k}: {v}")
        return "\n".join(lines) if lines else "(no parent metrics)"

    def get_summary(self, max_bytes: Optional[int] = None) -> str:
        """Return the markdown KB content (trimmed) for prompt injection."""
        max_bytes = max_bytes or self.config.max_kb_bytes
        content = self._read_markdown()
        if not content:
            return ""
        encoded = content.encode("utf-8")
        if len(encoded) > max_bytes:
            return encoded[:max_bytes].decode("utf-8", errors="ignore")
        return content

    def build_update_prompt(
        self,
        metrics: Dict[str, Any],
        artifacts: Optional[Dict[str, Union[str, bytes]]] = None,
        changes_summary: Optional[str] = None,
        current_code: Optional[str] = None,
        parent_code: Optional[str] = None,
        language: Optional[str] = None,
        iteration: Optional[int] = None,
        task_description: Optional[str] = None,
        parent_metrics: Optional[Dict[str, Any]] = None,
        diff_blocks: Optional[str] = None,
        explanation: Optional[str] = None,
    ) -> Dict[str, str]:
        # Load system and user templates with graceful fallbacks
        try:
            system_msg = self.template_manager.get_template(
                self.config.update_system_message_key
            )
        except Exception:
            system_msg = (
                "You maintain an evolving Experience Knowledge Base in Markdown. "
                "On each update, produce a complete revised Markdown document."
            )
        try:
            user_template = self.template_manager.get_template(
                self.config.update_template_key
            )
        except Exception:
            user_template = (
                "Update the following Experience KB (Markdown) based on the provided context. "
                "Return only the full updated Markdown document, without any JSON or extra commentary."
            )

        # Align with ExplanationService prompt structure (L88-L99)
        metrics_str = self._format_metrics(metrics or {})
        parent_metrics_str = self._format_parent_metrics(parent_metrics or {})

        # Artifacts section
        artifacts_str = ""
        if artifacts:
            try:
                items = []
                for k, v in artifacts.items():
                    items.append(f"- {k}: {self._safe_decode_artifact(v)}")
                artifacts_str = "\n".join(items)
            except Exception:
                artifacts_str = json.dumps(artifacts, ensure_ascii=False)

        # Code sections
        language_safe = language or "python"
        current_code_section = (
            f"```{language_safe}\n{current_code or ''}\n```" if current_code else "(no current code)"
        )
        parent_code_section = (
            f"```{language_safe}\n{parent_code or ''}\n```" if parent_code else "(no parent code)"
        )

        # Existing KB content (entire markdown)
        existing_kb_md = self._read_markdown()
        existing_kb_section = existing_kb_md if existing_kb_md else "(no existing KB content yet)"

        # Optional explanation section
        explanation_section = f"{explanation}" if explanation else "(no explanation)"

        # Optional diff blocks
        diff_blocks_str = diff_blocks or "(no diff blocks)"

        # Directly format the user template with placeholders, similar to ExplanationService
        user_msg = user_template.format(
            iteration=iteration if iteration is not None else -1,
            language=language_safe,
            metrics=metrics_str,
            changes_summary=changes_summary or "(no changes summary)",
            artifacts=artifacts_str or "(no artifacts)",
            current_code_section=current_code_section,
            parent_code_section=parent_code_section,
            task_description=task_description or "(no task description)",
            parent_metrics=parent_metrics_str,
            diff_blocks=diff_blocks_str,
            explanation=explanation_section,
            existing_kb_markdown=existing_kb_section,
        )

        return {"system": system_msg, "user": user_msg}

    async def generate(self, prompt: Dict[str, str]) -> KBUpdateResult:
        """Generate updated KB content given a pre-built prompt and persist to Markdown.

        Args:
            prompt: Dict with keys {"system", "user"}

        Returns:
            KBUpdateResult with summary (trimmed markdown), full response, and prompt.
        """
        response = None
        if self.llm:
            try:
                response = await self.llm.generate_with_context(
                    system_message=prompt.get("system", ""),
                    messages=[{"role": "user", "content": prompt.get("user", "")}],
                )
            except Exception:
                response = None

        # Persist updated markdown content (replace entire file)
        if response:
            self._write_markdown(response)

        # Return updated summary (the markdown content trimmed)
        summary = self.get_summary(max_bytes=self.config.max_kb_bytes)
        return KBUpdateResult(summary=summary, rules_json=None, prompt=prompt, response=response)

    async def generate_update(
        self,
        metrics: Dict[str, Any],
        artifacts: Optional[Dict[str, Union[str, bytes]]] = None,
        changes_summary: Optional[str] = None,
        current_code: Optional[str] = None,
        parent_code: Optional[str] = None,
        language: Optional[str] = None,
        iteration: Optional[int] = None,
        task_description: Optional[str] = None,
        parent_metrics: Optional[Dict[str, Any]] = None,
        diff_blocks: Optional[str] = None,
        explanation: Optional[str] = None,
    ) -> KBUpdateResult:
        """Backward-compatible wrapper: build prompt then call generate(prompt)."""
        prompt = self.build_update_prompt(
            metrics=metrics,
            artifacts=artifacts,
            changes_summary=changes_summary,
            current_code=current_code,
            parent_code=parent_code,
            language=language,
            iteration=iteration,
            task_description=task_description,
            parent_metrics=parent_metrics,
            diff_blocks=diff_blocks,
            explanation=explanation,
        )
        return await self.generate(prompt)