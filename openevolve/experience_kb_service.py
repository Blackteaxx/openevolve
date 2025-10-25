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
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union, Tuple

import json
import random
from pathlib import Path

from openevolve.utils.code_utils import (
    extract_diffs,
    validate_diff_blocks,
    apply_validated_diff_blocks,
    format_diff_blocks_string,
)

from openevolve.config import ExperienceKBConfig, LLMConfig
from openevolve.llm.ensemble import LLMEnsemble


@dataclass
class KBUpdateResult:
    summary: Optional[str] = None
    rules_json: Optional[str] = None
    prompt: Optional[Dict[str, str]] = None
    response: Optional[str] = None
    critical_prompt: Optional[Dict[str, str]] = None
    critical_response: Optional[str] = None


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
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initialized ExperienceKBService")

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
                initial_content = self._get_initial_markdown()
                with open(self.experience_md_path, "w", encoding="utf-8") as f:
                    f.write(initial_content)
                self.logger.info(
                    f"Created experience markdown at {self.experience_md_path}"
                )
        except Exception as e:
            # Swallow IO errors in worker context to avoid crashing
            self.logger.warning(f"Failed to initialize experience markdown: {e}")
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
                initial_content = self._get_initial_markdown()
                with open(self.experience_md_path, "w", encoding="utf-8") as f:
                    f.write(initial_content)
                self.logger.info(
                    f"Created experience markdown at {self.experience_md_path}"
                )

            self.logger.info(
                f"ExperienceKB storage directory set to {self.storage_dir}"
            )
        except Exception as e:
            # Keep previous paths if unable to update
            self.logger.warning(f"Failed to set output dir: {e}")
            pass

    # --- Markdown storage helpers ---
    def _get_initial_markdown(self) -> str:
        """Resolve initial KB markdown from config, templates, or bundled fallback."""
        # 1) Explicit path provided by config (supports .md)
        try:
            template_path = getattr(self.config, "initial_markdown_template_path", None)
            if template_path:
                p = Path(template_path)
                if p.exists():
                    return p.read_text(encoding="utf-8")
                else:
                    self.logger.warning(
                        f"Initial KB template path not found: {template_path}"
                    )
        except Exception as e:
            self.logger.warning(f"Failed reading initial KB template path: {e}")

        # 4) Minimal default header
        return (
            "# Experience Knowledge Base\n\n"
            "## I. Algorithmic & Data Structure Principles\n\n"
            "## II. Memory & Locality Optimizations\n\n"
            "## III. Language-Specific Idioms\n\n"
            "## IV. I/O & System Call Efficiency"
        )

    def _read_markdown(self) -> str:
        try:
            if not os.path.exists(self.experience_md_path):
                self.logger.debug("experience.md not found; returning empty content")
                return ""
            with open(self.experience_md_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.logger.debug(
                    f"Read experience.md with {len(content.encode('utf-8'))} bytes"
                )
                return content
        except Exception as e:
            self.logger.warning(f"Failed reading experience.md: {e}")
            return ""

    def _write_markdown(self, content: str) -> None:
        try:
            with open(self.experience_md_path, "w", encoding="utf-8") as f:
                f.write(content or "")
            self.logger.info(
                f"Updated experience.md with {len((content or '').encode('utf-8'))} bytes"
            )
        except Exception as e:
            # Swallow IO errors in worker context
            self.logger.warning(f"Failed writing experience.md: {e}")
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
        # Choose summary mode: full or random_rules
        mode = getattr(self.config, "summary_mode", "full")
        if mode == "random_rules":
            try:
                max_k = getattr(self.config, "random_rules_max_k", 5)
                if not isinstance(max_k, int) or max_k < 0:
                    max_k = 5
                k = random.randint(0, max_k)
                self.logger.info(f"KB random summary: k={k} max_k={max_k}")
                content = self._select_random_rules(content, k)
            except Exception as e:
                self.logger.warning(f"KB random summary failed: {e}; falling back to full content.")
        encoded = content.encode("utf-8")
        if len(encoded) > max_bytes:
            return encoded[:max_bytes].decode("utf-8", errors="ignore")
        return content

    def _select_random_rules(self, content: str, k: int) -> str:
        """Select k random rules from the markdown, preserving H1/H2 headings."""
        try:
            lines = content.splitlines()
            h1: Optional[str] = None
            sections: List[Dict[str, Any]] = []
            current_section: Optional[Dict[str, Any]] = None
            current_rule_start: Optional[int] = None

            def finalize_rule(end_idx: int) -> None:
                nonlocal current_rule_start, current_section
                if current_rule_start is not None and current_section is not None:
                    current_section["rules"].append((current_rule_start, end_idx))
                    current_rule_start = None

            for i, line in enumerate(lines):
                # H1 heading
                if line.startswith("# ") and not line.startswith("## "):
                    if h1 is None:
                        h1 = line
                    finalize_rule(i)
                    continue
                # H2 heading
                if line.startswith("## ") and not line.startswith("### "):
                    finalize_rule(i)
                    current_section = {"title": line, "rules": []}
                    sections.append(current_section)
                    continue
                # Rule block starts at H3 with "Rule ID:"
                if line.startswith("### ") and "Rule ID:" in line:
                    finalize_rule(i)
                    if current_section is None:
                        current_section = {"title": "## Rules", "rules": []}
                        sections.append(current_section)
                    current_rule_start = i
                    continue
            # finalize last rule at EOF
            finalize_rule(len(lines))

            # Flatten rule refs
            rule_refs: List[Tuple[int, int]] = []  # (section_index, rule_index)
            for si, sec in enumerate(sections):
                for ri, _ in enumerate(sec["rules"]):
                    rule_refs.append((si, ri))

            # If k<=0 or no rules, return only headers
            if k <= 0 or not rule_refs:
                out_lines: List[str] = []
                if h1:
                    out_lines.append(h1)
                for sec in sections:
                    out_lines.append(sec["title"])
                return "\n\n".join(out_lines).strip()

            # Bound k by available rules
            if k > len(rule_refs):
                k = len(rule_refs)
            chosen_indices = set(random.sample(range(len(rule_refs)), k))

            # Reconstruct content
            out_lines: List[str] = []
            if h1:
                out_lines.append(h1)
            for si, sec in enumerate(sections):
                out_lines.append(sec["title"])
                # Keep original order of rules in section
                for idx, (sidx, ridx) in enumerate(rule_refs):
                    if sidx == si and idx in chosen_indices:
                        start, end = sec["rules"][ridx]
                        out_lines.extend(lines[start:end])
            return "\n".join(out_lines).strip()
        except Exception as e:
            self.logger.warning(f"_select_random_rules failed: {e}")
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
            f"```{language_safe}\n{current_code or ''}\n```"
            if current_code
            else "(no current code)"
        )
        parent_code_section = (
            f"```{language_safe}\n{parent_code or ''}\n```"
            if parent_code
            else "(no parent code)"
        )

        # Existing KB content (entire markdown)
        existing_kb_md = self._read_markdown()
        existing_kb_section = (
            existing_kb_md if existing_kb_md else "(no existing KB content yet)"
        )

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

    def _build_critical_agent_prompt(
        self,
        *,
        iteration: int,
        language: str,
        metrics: str,
        changes_summary: str,
        artifacts: str,
        current_code_section: str,
        parent_code_section: str,
        task_description: str,
        parent_metrics: str,
        diff_blocks: str,
        explanation: str,
        existing_kb_markdown: str,
        proposed_diff: str,
    ) -> Dict[str, str]:
        """Build the critical agent prompt using explicit fields and templates."""
        try:
            system_msg = self.template_manager.get_template(
                getattr(
                    self.config,
                    "critical_agent_system_message_key",
                    "critical_agent_system_message",
                )
            )
        except Exception:
            system_msg = "You are the Principal Engineer and chair of the Code Standards Committee."
        try:
            user_template = self.template_manager.get_template(
                getattr(self.config, "critical_agent_template_key", "critical_agent")
            )
        except Exception:
            user_template = (
                "Evaluate the proposed diff strictly and return a JSON decision with keys 'decision' and 'reasoning'.\n\n"
                "Context: {task_description}, Iteration: {iteration} | Language: {language}\n\n"
                "Existing Experience KB (Markdown)\n{existing_kb_markdown}\n\n"
                "Proposed Diff:\n{proposed_diff}"
            )
        try:
            user_msg = user_template.format(
                task_description=task_description or "(no task description)",
                iteration=iteration if iteration is not None else -1,
                language=language or "python",
                current_code_section=current_code_section or "(no current code)",
                parent_code_section=parent_code_section or "(no parent code)",
                metrics=metrics or "(no metrics)",
                parent_metrics=parent_metrics or "(no parent metrics)",
                changes_summary=changes_summary or "(no changes summary)",
                diff_blocks=diff_blocks or "(no diff blocks)",
                artifacts=artifacts or "(no artifacts)",
                explanation=explanation or "(no explanation)",
                existing_kb_markdown=existing_kb_markdown
                or "(no existing KB content yet)",
                proposed_diff=proposed_diff or "",
            )
        except Exception as e:
            self.logger.warning(f"Failed formatting critical agent prompt: {e}")
            user_msg = (
                f"Existing KB:\n{existing_kb_markdown}\n\nProposed Diff:\n{proposed_diff}"
                if proposed_diff
                else "No diff"
            )
        return {"system": system_msg, "user": user_msg}

    def _extract_json_decision(self, text: str) -> Optional[Dict[str, str]]:
        """Extract JSON object with keys decision and reasoning from critical agent output."""
        if not text:
            return None
        try:
            import re, json as _json

            # Find a ```json code block first
            m = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
            if m:
                obj = _json.loads(m.group(1))
                return {
                    "decision": obj.get("decision"),
                    "reasoning": obj.get("reasoning"),
                }
            # Fallback: find first {...}
            m2 = re.search(r"(\{.*?\})", text, re.DOTALL)
            if m2:
                obj = _json.loads(m2.group(1))
                return {
                    "decision": obj.get("decision"),
                    "reasoning": obj.get("reasoning"),
                }
        except Exception as e:
            self.logger.warning(f"Failed to parse critical agent JSON: {e}")
        return None

    async def generate(
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
        """Generate KB update diff, validate, critical-review, and apply to markdown with retries (no ctx)."""
        # Early exit if no LLM
        if not self.llm:
            self.logger.info(
                "LLM ensemble not configured; skipping KB update generation"
            )
            return KBUpdateResult(
                summary=self.get_summary(self.config.max_kb_bytes),
                rules_json=None,
                prompt=None,
                response=None,
                critical_prompt=None,
                critical_response=None,
            )

        attempts = max(1, getattr(self.config, "max_update_attempts", 1))
        last_diff: Optional[str] = None
        last_update_prompt: Optional[Dict[str, str]] = None
        last_critical_prompt: Optional[Dict[str, str]] = None
        last_critical_response: Optional[str] = None

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

        # Prepare formatted fields
        metrics_str = self._format_metrics(metrics or {})
        parent_metrics_str = self._format_parent_metrics(parent_metrics or {})
        language_safe = language or "python"
        current_code_section = (
            f"```{language_safe}\n{current_code or ''}\n```"
            if current_code
            else "(no current code)"
        )
        parent_code_section = (
            f"```{language_safe}\n{parent_code or ''}\n```"
            if parent_code
            else "(no parent code)"
        )
        existing_kb_md = self._read_markdown()
        existing_kb_section = (
            existing_kb_md if existing_kb_md else "(no existing KB content yet)"
        )
        explanation_section = f"{explanation}" if explanation else "(no explanation)"

        artifacts_str = ""
        if artifacts:
            try:
                items = []
                for k, v in artifacts.items():
                    items.append(f"- {k}: {self._safe_decode_artifact(v)}")
                artifacts_str = "\n".join(items)
            except Exception:
                artifacts_str = json.dumps(artifacts, ensure_ascii=False)
        diff_blocks_str = diff_blocks or "(no diff blocks)"

        for attempt in range(1, attempts + 1):
            self.logger.info(f"KB update attempt {attempt}/{attempts}")

            # Build update prompt directly from raw fields
            try:
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
            except Exception as e:
                self.logger.warning(f"Failed formatting update prompt: {e}")
                user_msg = "Format error while building update prompt."

            update_prompt = {"system": system_msg, "user": user_msg}
            last_update_prompt = update_prompt

            # 1) Generate proposed diff
            diff_response = None
            try:
                diff_response = await self.llm.generate_with_context(
                    system_message=system_msg,
                    messages=[{"role": "user", "content": user_msg}],
                )
            except Exception as e:
                self.logger.warning(f"LLM generate failed: {e}")
                diff_response = None

            if not diff_response:
                explanation_section = "Generation returned empty response; produce valid SEARCH/REPLACE diff blocks only."
                continue

            self.logger.debug(f"Proposed diff length: {len(diff_response)} characters")
            last_diff = diff_response

            # 2) Parse and validate diff against existing KB using shared utils
            # kb_text = self._read_markdown()
            kb_text = existing_kb_md
            diff_blocks_list = extract_diffs(diff_response)
            valid_blocks = validate_diff_blocks(kb_text, diff_blocks_list)
            if self.config.require_all_matches and len(valid_blocks) != len(
                diff_blocks_list
            ):
                explanation_section = (
                    "Invalid diff: some SEARCH blocks not found; ensure exact matches."
                )
                self.logger.info(
                    f"Diff invalid; valid_blocks={len(valid_blocks)}/{len(diff_blocks_list)}; retrying"
                )
                continue
            if not valid_blocks:
                explanation_section = "Diff contained no valid blocks; ensure SEARCH matches existing content."
                self.logger.info("Diff validation found 0 valid blocks; retrying")
                continue

            # 3) Critical agent review based on valid blocks
            proposed_diff_str = format_diff_blocks_string(valid_blocks)
            critical_prompt = self._build_critical_agent_prompt(
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
                proposed_diff=proposed_diff_str,
            )
            last_critical_prompt = critical_prompt

            agent_output = None
            try:
                agent_output = await self.llm.generate_with_context(
                    system_message=critical_prompt.get("system", ""),
                    messages=[
                        {"role": "user", "content": critical_prompt.get("user", "")}
                    ],
                )
            except Exception as e:
                self.logger.warning(f"Critical agent call failed: {e}")
                agent_output = None
            
            # Track last critical agent raw response for logging purposes
            last_critical_response = agent_output

            decision_obj = self._extract_json_decision(agent_output or "")
            if not decision_obj:
                explanation_section = "Critical agent returned no valid JSON decision; restate diff using strict format."
                self.logger.info(
                    "Critical agent did not provide a valid decision; retrying"
                )
                continue

            decision = str(decision_obj.get("decision", "")).upper()
            reason = decision_obj.get("reasoning", "")
            self.logger.info(f"Critical agent decision: {decision}")

            if decision != "APPROVE":
                explanation_section = f"Critical agent REJECT: {reason}. Regenerate diff that is generalizable, correctly categorized, and strictly formatted."
                continue

            # 4) Apply diff blocks to KB using shared utils
            new_text = apply_validated_diff_blocks(kb_text, valid_blocks)
            if not new_text or new_text == kb_text:
                explanation_section = "Diff application resulted in no changes; ensure SEARCH matches existing block."
                self.logger.info("Diff application produced no changes; retrying")
                continue

            # Persist updated markdown content
            self._write_markdown(new_text)

            # Return updated summary and both prompts
            summary = self.get_summary(max_bytes=self.config.max_kb_bytes)
            return KBUpdateResult(
                summary=summary,
                rules_json=None,
                prompt=update_prompt,
                response=diff_response,
                critical_prompt=critical_prompt,
                critical_response=agent_output,
            )

        # Retries exhausted; return without applying changes
        self.logger.warning("KB update attempts exhausted without application")
        return KBUpdateResult(
            summary=self.get_summary(self.config.max_kb_bytes),
            rules_json=None,
            prompt=last_update_prompt,
            response=last_diff,
            critical_prompt=last_critical_prompt,
            critical_response=last_critical_response,
        )

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
        """Wrapper: call generate with raw fields (no prompt dict)."""
        return await self.generate(
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
