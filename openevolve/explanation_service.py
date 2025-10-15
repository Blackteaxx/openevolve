"""
Explanation generation service using templates and LLM ensemble.
"""

from typing import Any, Dict, Optional, Union

from openevolve.config import ExplanationConfig
from openevolve.prompt.templates import TemplateManager


class ExplanationService:
    """Service that builds an explanation prompt and generates a response."""

    def __init__(
        self,
        template_manager: TemplateManager,
        llm_ensemble,
        config: ExplanationConfig,
    ) -> None:
        self.template_manager = template_manager
        self.llm_ensemble = llm_ensemble
        self.config = config

    def build_prompt(
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
    ) -> Dict[str, str]:
        """Build explanation prompt using the configured template and inputs."""
        # System message
        system_message_key = self.config.system_message_key or "system_message"
        system_message = self.template_manager.get_template(system_message_key)

        # User template
        template_key = self.config.template_key or "explanation"
        user_template = self.template_manager.get_template(template_key)

        # Format metrics as bullet list
        metrics_lines = []
        for k, v in (metrics or {}).items():
            if isinstance(v, (int, float)):
                try:
                    metrics_lines.append(f"- {k}: {v:.4f}")
                except Exception:
                    metrics_lines.append(f"- {k}: {v}")
            else:
                metrics_lines.append(f"- {k}: {v}")
        metrics_str = "\n".join(metrics_lines) if metrics_lines else "(no metrics)"

        # Artifacts summary (truncate values to max_artifacts_bytes)
        artifacts_str = ""
        if artifacts:
            max_bytes = max(0, int(self.config.max_artifacts_bytes or 0))
            parts = []
            for key, value in artifacts.items():
                text = self._safe_decode_artifact(value)
                if max_bytes:
                    text = text[:max_bytes]
                parts.append(f"- {key}:\n{text}")
            artifacts_str = "\n".join(parts)
        else:
            artifacts_str = "(no artifacts)"

        # Code sections (optional)
        current_code_section = f"```{language}\n{current_code}\n```" if (self.config.include_code and current_code) else "(omitted)"
        parent_code_section = f"```{language}\n{parent_code}\n```" if (self.config.include_code and parent_code) else "(omitted)"

        # Format parent metrics as bullet list
        parent_metrics_lines = []
        for k, v in (parent_metrics or {}).items():
            if isinstance(v, (int, float)):
                try:
                    parent_metrics_lines.append(f"- {k}: {v:.4f}")
                except Exception:
                    parent_metrics_lines.append(f"- {k}: {v}")
            else:
                parent_metrics_lines.append(f"- {k}: {v}")
        parent_metrics_str = "\n".join(parent_metrics_lines) if parent_metrics_lines else "(no parent metrics)"

        user_message = user_template.format(
            iteration=iteration if iteration is not None else -1,
            language=language or "python",
            metrics=metrics_str,
            changes_summary=changes_summary or "(no changes summary)",
            artifacts=artifacts_str,
            current_code_section=current_code_section,
            parent_code_section=parent_code_section,
            task_description=task_description or "(no task description)",
            parent_metrics=parent_metrics_str,
            diff_blocks=diff_blocks or "(no diff blocks)",
        )

        return {"system": system_message, "user": user_message}

    async def generate(self, prompt: Dict[str, str]) -> Optional[str]:
        """Generate explanation text using the LLM ensemble."""
        try:
            response = await self.llm_ensemble.generate_with_context(
                system_message=prompt["system"],
                messages=[{"role": "user", "content": prompt["user"]}],
            )
            return response
        except Exception:
            return None

    def _safe_decode_artifact(self, value: Union[str, bytes]) -> str:
        if isinstance(value, bytes):
            try:
                return value.decode("utf-8", errors="replace")
            except Exception:
                return "[binary artifact]"
        return str(value)