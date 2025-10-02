"""
Prompt sampling for OpenEvolve
"""

import logging
import random
from typing import Any, Dict, List, Optional, Union

from openevolve.config import PromptConfig
from openevolve.prompt.templates import TemplateManager
from openevolve.utils.metrics_utils import (
    format_feature_coordinates,
    get_fitness_score,
)

logger = logging.getLogger(__name__)


class PromptSampler:
    """Generates prompts for code evolution"""

    def __init__(self, config: PromptConfig):
        self.config = config
        self.template_manager = TemplateManager(custom_template_dir=config.template_dir)

        # Store custom template mappings
        self.system_template_override = None
        self.user_template_override = None

        # Only log once to reduce duplication
        if not hasattr(logger, "_prompt_sampler_logged"):
            logger.info("Initialized prompt sampler")
            logger._prompt_sampler_logged = True

    def set_templates(
        self, system_template: Optional[str] = None, user_template: Optional[str] = None
    ) -> None:
        """
        Set custom templates to use for this sampler

        Args:
            system_template: Template name for system message
            user_template: Template name for user message
        """
        self.system_template_override = system_template
        self.user_template_override = user_template
        logger.info(
            f"Set custom templates: system={system_template}, user={user_template}"
        )

    def build_prompt(
        self,
        current_program: str = "",
        parent_program: str = "",
        program_metrics: Dict[str, float] = {},
        top_programs: List[Dict[str, Any]] = [],
        inspirations: List[Dict[str, Any]] = [],  # Add inspirations parameter
        language: str = "python",
        evolution_round: int = 0,
        diff_based_evolution: bool = True,
        template_key: Optional[str] = None,
        program_artifacts: Optional[Dict[str, Union[str, bytes]]] = None,
        feature_dimensions: Optional[List[str]] = None,
        # 新增：直接传入父程序的指标以避免依赖 previous_programs
        parent_metrics: Dict[str, float] = {},
        # 新增：当前程序的解释（来自 metadata.explanation 或外部）
        current_explanation: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, str]:
        """
        构建 LLM 的 prompt，按照新的信息架构组织内容

        新的信息架构遵循"代码—度量—证据—解释—差异"的阅读路径：

        A. 顶部区块（精简）：
           - Current Program: 当前程序代码块
           - Current Metrics: 纯指标展示（条目形式）
           - Parent vs Current: 指标差异对比（↑/↓/≈）
           - Current Artifacts: 当前程序的执行证据（可选）

        B. 程序族历史区块：
           每个程序包含 6 个子块：
           - Program Header: 程序名、得分、类型
           - Code Snippet: 完整代码
           - Metrics: 完整指标（条目形式）
           - Artifacts: 执行证据（若启用）
           - Parent Diff: 与父程序的对比
           - Model Explanation: 模型生成的解释

        Args:
            current_program: 当前程序代码
            parent_program: 父程序代码（用于对比）
            program_metrics: 当前程序的指标字典
            top_programs: 顶级表现程序列表（按适应度排序）
            inspirations: 灵感程序列表（多样性/创意示例）
            language: 编程语言
            evolution_round: 当前进化轮次
            diff_based_evolution: 是否使用基于差异的进化（True）或完全重写（False）
            template_key: 可选的模板键覆盖
            program_artifacts: 程序评估的可选 artifacts
            feature_dimensions: 特征维度列表
            **kwargs: 用于替换用户 prompt 中的额外键

        Returns:
            包含 'system' 和 'user' 键的字典
        """
        # Select template based on evolution mode (with overrides)
        if template_key:
            # Use explicitly provided template key
            user_template_key = template_key
        elif self.user_template_override:
            # Use the override set with set_templates
            user_template_key = self.user_template_override
        else:
            # Default behavior: diff-based vs full rewrite
            user_template_key = (
                "diff_user" if diff_based_evolution else "full_rewrite_user"
            )

        # Get the template
        user_template = self.template_manager.get_template(user_template_key)

        # Use system template override if set
        if self.system_template_override:
            system_message = self.template_manager.get_template(
                self.system_template_override
            )
        else:
            system_message = self.config.system_message
            # If system_message is a template name rather than content, get the template
            if system_message in self.template_manager.templates:
                system_message = self.template_manager.get_template(system_message)

        # 按照新的信息架构重构 prompt 构建流程

        # A. 顶部区块（更精简）
        # 1. Current Program 代码块（必须）
        current_program_section = f"```{language}\n{current_program}\n```"

        # 1.1 当前程序解释（可选）
        # 说明：按需求在顶部区块呈现当前程序的解释，来源由调用方传入
        current_explanation_section = ""
        if current_explanation:
            current_explanation_section = (
                f"\n**Why this program:** {current_explanation}\n"
            )

        # 2. Current Metrics（只展示metrics_str，不再放"improvement areas"）
        current_metrics_str = self._format_metrics(program_metrics)

        # 3. Parent vs Current (metrics diff)（若可得；紧邻 Current Metrics）
        # 说明：不依赖 previous_programs，直接使用传入的 parent_metrics 进行对比。
        parent_vs_current_section = ""
        effective_parent_metrics: Dict[str, float] = parent_metrics or {}
        if effective_parent_metrics:
            parent_vs_current_section = self._calculate_metrics_diff(
                program_metrics, effective_parent_metrics
            )

        # 3.1 Parent Program（代码内容展示；应用户要求在顶部呈现）
        parent_program_section = ""
        if parent_program:
            parent_program_section = f"```{language}\n{parent_program}\n```"

        # 4. Current Artifacts：仅当开启 artifacts 且存在与"当前程序"对应的 artifacts
        current_artifacts_section = ""
        if self.config.include_artifacts and program_artifacts:
            current_artifacts_section = self._render_artifacts(program_artifacts)

        # B. 程序族历史区块（Program Evolution History）
        evolution_history = self._format_evolution_history_new(
            top_programs, inspirations, language, feature_dimensions
        )

        # Apply stochastic template variations if enabled
        if self.config.use_template_stochasticity:
            user_template = self._apply_template_variations(user_template)

        # Calculate fitness and feature coordinates for backward compatibility
        feature_dimensions = feature_dimensions or []
        fitness_score = get_fitness_score(program_metrics, feature_dimensions)
        feature_coords = format_feature_coordinates(program_metrics, feature_dimensions)

        # Format the final user message using new architecture
        user_message = user_template.format(
            # 新的信息架构变量
            current_program=current_program_section,
            current_explanation_section=current_explanation_section,
            parent_program_section=parent_program_section,
            current_metrics=current_metrics_str,
            parent_vs_current_section=parent_vs_current_section,
            current_artifacts_section=current_artifacts_section,
            evolution_history=evolution_history,
            language=language,
            # 保持向后兼容的变量
            metrics=current_metrics_str,
            fitness_score=f"{fitness_score:.4f}",
            feature_coords=feature_coords,
            feature_dimensions=", ".join(feature_dimensions)
            if feature_dimensions
            else "None",
            improvement_areas="",  # 不再使用，但保持兼容性
            artifacts=current_artifacts_section,
            **kwargs,
        )

        return {
            "system": system_message,
            "user": user_message,
        }

    def _format_metrics(self, metrics: Dict[str, float]) -> str:
        """
        格式化指标为条目形式，用于新的信息架构

        按照新架构要求，指标必须以条目形式展示，避免"简写一行串"丢失信息。
        例如：
        - runs_successfully: 1.0000
        - value_score: 0.9579
        - distance_score: 0.7841
        - combined_score: 1.2437

        Args:
            metrics: 指标字典，键为指标名，值为指标值

        Returns:
            格式化的指标字符串，每行一个指标
        """
        # Use safe formatting to handle mixed numeric and string values
        formatted_parts = []
        for name, value in metrics.items():
            if isinstance(value, (int, float)):
                try:
                    formatted_parts.append(f"- {name}: {value:.4f}")
                except (ValueError, TypeError):
                    formatted_parts.append(f"- {name}: {value}")
            else:
                formatted_parts.append(f"- {name}: {value}")
        return "\n".join(formatted_parts)

    def _identify_improvement_areas(
        self,
        current_program: str,
        parent_program: str,
        metrics: Dict[str, float],
        feature_dimensions: Optional[List[str]] = None,
    ) -> str:
        """Identify improvement areas with proper fitness/feature separation"""

        improvement_areas = []
        feature_dimensions = feature_dimensions or []

        # Calculate fitness (excluding feature dimensions)
        current_fitness = get_fitness_score(metrics, feature_dimensions)

        # Track fitness changes is no longer based on previous programs

        # Note feature exploration (not good/bad, just informational)
        if feature_dimensions:
            feature_coords = format_feature_coordinates(metrics, feature_dimensions)
            if feature_coords != "No feature coordinates":
                msg = self.template_manager.get_fragment(
                    "exploring_region", features=feature_coords
                )
                improvement_areas.append(msg)

        # Code length check (configurable threshold)
        threshold = (
            self.config.suggest_simplification_after_chars
            or self.config.code_length_threshold
        )
        if threshold and len(current_program) > threshold:
            msg = self.template_manager.get_fragment(
                "code_too_long", threshold=threshold
            )
            improvement_areas.append(msg)

        # Default guidance if nothing specific
        if not improvement_areas:
            improvement_areas.append(
                self.template_manager.get_fragment("no_specific_guidance")
            )

        return "\n".join(f"- {area}" for area in improvement_areas)

    def _format_evolution_history(
        self,
        top_programs: List[Dict[str, Any]],
        inspirations: List[Dict[str, Any]],
        language: str,
        feature_dimensions: Optional[List[str]] = None,
    ) -> str:
        """Format the evolution history for the prompt"""
        # Get templates
        history_template = self.template_manager.get_template("evolution_history")
        previous_attempt_template = self.template_manager.get_template(
            "previous_attempt"
        )
        top_program_template = self.template_manager.get_template("top_program")

        # Previous attempts section removed; keep empty for template compatibility
        previous_attempts_str = ""

        # Format top programs
        top_programs_str = ""
        selected_top = top_programs[
            : min(self.config.num_top_programs, len(top_programs))
        ]

        for i, program in enumerate(selected_top):
            # Use the full program code
            program_code = program.get("code", "")

            # Calculate fitness score (prefers combined_score, excludes feature dimensions)
            score = get_fitness_score(
                program.get("metrics", {}), feature_dimensions or []
            )

            # Extract key features (this could be more sophisticated)
            key_features = program.get("key_features", [])
            if not key_features:
                key_features = []
                for name, value in program.get("metrics", {}).items():
                    if isinstance(value, (int, float)):
                        try:
                            key_features.append(
                                f"Performs well on {name} ({value:.4f})"
                            )
                        except (ValueError, TypeError):
                            key_features.append(f"Performs well on {name} ({value})")
                    else:
                        key_features.append(f"Performs well on {name} ({value})")

            key_features_str = ", ".join(key_features)

            top_programs_str += (
                top_program_template.format(
                    program_number=i + 1,
                    score=f"{score:.4f}",
                    language=language,
                    program_snippet=program_code,
                    key_features=key_features_str,
                )
                + "\n\n"
            )

        # Format diverse programs using num_diverse_programs config
        diverse_programs_str = ""
        if (
            self.config.num_diverse_programs > 0
            and len(top_programs) > self.config.num_top_programs
        ):
            # Skip the top programs we already included
            remaining_programs = top_programs[self.config.num_top_programs :]

            # Sample diverse programs from the remaining
            num_diverse = min(self.config.num_diverse_programs, len(remaining_programs))
            if num_diverse > 0:
                # Use random sampling to get diverse programs
                diverse_programs = random.sample(remaining_programs, num_diverse)

                diverse_programs_str += "\n\n## Diverse Programs\n\n"

                for i, program in enumerate(diverse_programs):
                    # Use the full program code
                    program_code = program.get("code", "")

                    # Calculate fitness score (prefers combined_score, excludes feature dimensions)
                    score = get_fitness_score(
                        program.get("metrics", {}), feature_dimensions or []
                    )

                    # Extract key features
                    key_features = program.get("key_features", [])
                    if not key_features:
                        key_features = [
                            f"Alternative approach to {name}"
                            for name in list(program.get("metrics", {}).keys())[
                                :2
                            ]  # Just first 2 metrics
                        ]

                    key_features_str = ", ".join(key_features)

                    diverse_programs_str += (
                        top_program_template.format(
                            program_number=f"D{i + 1}",
                            score=f"{score:.4f}",
                            language=language,
                            program_snippet=program_code,
                            key_features=key_features_str,
                        )
                        + "\n\n"
                    )

        # Combine top and diverse programs
        combined_programs_str = top_programs_str + diverse_programs_str

        # Format inspirations section
        inspirations_section_str = self._format_inspirations_section(
            inspirations, language, feature_dimensions
        )

        # Combine into full history
        return history_template.format(
            previous_attempts=previous_attempts_str.strip(),
            top_programs=combined_programs_str.strip(),
            inspirations_section=inspirations_section_str,
        )

    def _format_evolution_history_new(
        self,
        top_programs: List[Dict[str, Any]],
        inspirations: List[Dict[str, Any]],
        language: str,
        feature_dimensions: Optional[List[str]] = None,
    ) -> str:
        """
        按照新的信息架构格式化进化历史，每个程序包含完整的 6 个子块

        Args:
            top_programs: 顶级表现程序列表
            inspirations: 灵感程序列表
            language: 编程语言
            feature_dimensions: 特征维度列表

        Returns:
            格式化的进化历史字符串
        """
        history_sections = []

        # 格式化顶级程序
        if top_programs:
            history_sections.append("## Top Performing Programs\n")

            selected_top = top_programs[
                : min(self.config.num_top_programs, len(top_programs))
            ]

            for i, program in enumerate(selected_top):
                program_block = self._format_program_block(
                    program,
                    i + 1,
                    language,
                    feature_dimensions,
                    self.config.include_artifacts,
                    None,  # 顶级程序不需要父程序对比
                )
                history_sections.append(program_block)
                history_sections.append("")  # 空行分隔

        # 格式化灵感程序
        if inspirations:
            history_sections.append("## Inspiration Programs\n")
            history_sections.append(
                "These programs represent diverse approaches and creative solutions:\n"
            )

            for i, program in enumerate(inspirations):
                program_block = self._format_program_block(
                    program,
                    f"Inspiration {i + 1}",
                    language,
                    feature_dimensions,
                    self.config.include_artifacts,
                    None,  # 灵感程序不需要父程序对比
                )
                history_sections.append(program_block)
                history_sections.append("")  # 空行分隔

        return "\n".join(history_sections).strip()

    def _calculate_metrics_diff(
        self,
        current_metrics: Dict[str, float],
        parent_metrics: Dict[str, float],
        threshold: float = 1e-6,
    ) -> str:
        """
        计算当前程序与父程序的指标差异，使用符号显示变化方向

        Args:
            current_metrics: 当前程序的指标
            parent_metrics: 父程序的指标
            threshold: 判断变化是否显著的阈值

        Returns:
            格式化的指标差异字符串
        """
        if not parent_metrics:
            return "No parent metrics available for comparison"

        diff_lines = []

        for metric_name in current_metrics:
            current_value = current_metrics.get(metric_name, 0)
            parent_value = parent_metrics.get(metric_name, 0)

            # 只比较数值类型的指标
            if not isinstance(current_value, (int, float)) or not isinstance(
                parent_value, (int, float)
            ):
                continue

            diff = current_value - parent_value

            # 确定变化符号
            if abs(diff) < threshold:
                symbol = "≈"
                change_desc = f"({current_value:.4f})"
            elif diff > 0:
                symbol = "↑"
                change_desc = f"({parent_value:.4f} → {current_value:.4f}, +{diff:.4f})"
            else:
                symbol = "↓"
                change_desc = f"({parent_value:.4f} → {current_value:.4f}, {diff:.4f})"

            diff_lines.append(f"- {metric_name}: {symbol} {change_desc}")

        return "\n".join(diff_lines) if diff_lines else "No numeric metrics to compare"

    def _generate_code_diff_summary(
        self, current_code: str, parent_code: str, metadata: Dict[str, Any]
    ) -> str:
        """
        生成代码差异摘要，优先使用 metadata.changes，否则生成轻量启发式摘要

        Args:
            current_code: 当前程序代码
            parent_code: 父程序代码
            metadata: 程序元数据

        Returns:
            代码差异摘要字符串
        """
        # 优先使用 metadata 中的 changes 信息
        if metadata and "changes" in metadata:
            changes = metadata["changes"]
            if isinstance(changes, str) and changes.strip():
                return changes
            elif isinstance(changes, list):
                return "; ".join(str(change) for change in changes if change)

        # 如果没有 metadata.changes，生成轻量启发式摘要
        if not parent_code:
            return "Initial program creation"

        # 简单的启发式分析
        current_lines = current_code.split("\n")
        parent_lines = parent_code.split("\n")

        summary_parts = []

        # 行数变化
        line_diff = len(current_lines) - len(parent_lines)
        if line_diff > 0:
            summary_parts.append(f"Added {line_diff} lines")
        elif line_diff < 0:
            summary_parts.append(f"Removed {abs(line_diff)} lines")

        # 检查是否有新的导入
        current_imports = [
            line.strip()
            for line in current_lines
            if line.strip().startswith(("import ", "from "))
        ]
        parent_imports = [
            line.strip()
            for line in parent_lines
            if line.strip().startswith(("import ", "from "))
        ]

        new_imports = set(current_imports) - set(parent_imports)
        if new_imports:
            summary_parts.append(f"Added {len(new_imports)} new imports")

        # 检查函数定义变化（简单启发式）
        current_funcs = [
            line.strip() for line in current_lines if line.strip().startswith("def ")
        ]
        parent_funcs = [
            line.strip() for line in parent_lines if line.strip().startswith("def ")
        ]

        if len(current_funcs) != len(parent_funcs):
            func_diff = len(current_funcs) - len(parent_funcs)
            if func_diff > 0:
                summary_parts.append(f"Added {func_diff} functions")
            else:
                summary_parts.append(f"Removed {abs(func_diff)} functions")

        return "; ".join(summary_parts) if summary_parts else "Minor code modifications"

    def _format_program_block(
        self,
        program: Dict[str, Any],
        program_number: Union[int, str],
        language: str,
        feature_dimensions: Optional[List[str]] = None,
        include_artifacts: bool = False,
        parent_program: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        格式化单个程序块，包含完整的 6 个子块信息

        Args:
            program: 程序字典
            program_number: 程序编号
            language: 编程语言
            feature_dimensions: 特征维度列表
            include_artifacts: 是否包含 artifacts
            parent_program: 父程序（用于对比）

        Returns:
            格式化的程序块字符串
        """
        program_code = program.get("code", "")
        program_metrics = program.get("metrics", {})
        program_metadata = program.get("metadata", {})

        # 1. Program Header - 程序名与得分
        fitness_score = get_fitness_score(program_metrics, feature_dimensions or [])
        program_type = self._determine_program_type(program, feature_dimensions or [])

        header = f"### Program {program_number} (Score: {fitness_score:.4f}, Type: {program_type})"

        # 2. Code Snippet
        code_section = f"```{language}\n{program_code}\n```"

        # 3. Metrics - 完整的 metrics_str 条目形式
        metrics_lines = []
        for name, value in program_metrics.items():
            if isinstance(value, (int, float)):
                try:
                    metrics_lines.append(f"- {name}: {value:.4f}")
                except (ValueError, TypeError):
                    metrics_lines.append(f"- {name}: {value}")
            else:
                metrics_lines.append(f"- {name}: {value}")
        metrics_section = (
            "\n".join(metrics_lines) if metrics_lines else "No metrics available"
        )

        # 4. Artifacts（若启用）
        artifacts_section = ""
        if include_artifacts and "artifacts" in program:
            artifacts_section = "\n\n**Execution Artifacts:**\n"
            artifacts_section += self._render_artifacts(program["artifacts"])

        # 5. Parent Diff（与 parent 的代码&指标对比）
        parent_diff_section = ""
        if parent_program:
            parent_metrics = parent_program.get("metrics", {})
            parent_code = parent_program.get("code", "")

            # Metrics diff
            metrics_diff = self._calculate_metrics_diff(program_metrics, parent_metrics)

            # Code diff summary
            code_diff = self._generate_code_diff_summary(
                program_code, parent_code, program_metadata
            )

            parent_diff_section = "\n\n**Changes from Parent:**\n"
            parent_diff_section += f"Metrics Changes:\n{metrics_diff}\n"
            parent_diff_section += f"Code Changes: {code_diff}"

        # 6. Model Explanation（生成解释）
        explanation_section = ""
        explanation = program_metadata.get("explanation", "")
        if explanation:
            explanation_section = f"\n\n**Why this change:** {explanation}"

        # 组合所有部分
        sections = [
            header,
            code_section,
            f"\n**Metrics:**\n{metrics_section}",
            artifacts_section,
            parent_diff_section,
            explanation_section,
        ]

        return "\n".join(section for section in sections if section)

    def _format_inspirations_section(
        self,
        inspirations: List[Dict[str, Any]],
        language: str,
        feature_dimensions: Optional[List[str]] = None,
    ) -> str:
        """
        Format the inspirations section for the prompt

        Args:
            inspirations: List of inspiration programs
            language: Programming language

        Returns:
            Formatted inspirations section string
        """
        if not inspirations:
            return ""

        # Get templates
        inspirations_section_template = self.template_manager.get_template(
            "inspirations_section"
        )
        inspiration_program_template = self.template_manager.get_template(
            "inspiration_program"
        )

        inspiration_programs_str = ""

        for i, program in enumerate(inspirations):
            # Use the full program code
            program_code = program.get("code", "")

            # Calculate fitness score (prefers combined_score, excludes feature dimensions)
            score = get_fitness_score(
                program.get("metrics", {}), feature_dimensions or []
            )

            # Determine program type based on metadata and score
            program_type = self._determine_program_type(
                program, feature_dimensions or []
            )

            # Extract unique features (emphasizing diversity rather than just performance)
            unique_features = self._extract_unique_features(program)

            inspiration_programs_str += (
                inspiration_program_template.format(
                    program_number=i + 1,
                    score=f"{score:.4f}",
                    program_type=program_type,
                    language=language,
                    program_snippet=program_code,
                    unique_features=unique_features,
                )
                + "\n\n"
            )

        return inspirations_section_template.format(
            inspiration_programs=inspiration_programs_str.strip()
        )

    def _determine_program_type(
        self, program: Dict[str, Any], feature_dimensions: Optional[List[str]] = None
    ) -> str:
        """
        Determine the type/category of an inspiration program

        Args:
            program: Program dictionary

        Returns:
            String describing the program type
        """
        metadata = program.get("metadata", {})
        score = get_fitness_score(program.get("metrics", {}), feature_dimensions or [])

        # Check metadata for explicit type markers
        if metadata.get("diverse", False):
            return "Diverse"
        if metadata.get("migrant", False):
            return "Migrant"
        if metadata.get("random", False):
            return "Random"

        # Classify based on score ranges
        if score >= 0.8:
            return "High-Performer"
        elif score >= 0.6:
            return "Alternative"
        elif score >= 0.4:
            return "Experimental"
        else:
            return "Exploratory"

    def _extract_unique_features(self, program: Dict[str, Any]) -> str:
        """
        Extract unique features of an inspiration program

        Args:
            program: Program dictionary

        Returns:
            String describing unique aspects of the program
        """
        features = []

        # Extract from metadata if available
        metadata = program.get("metadata", {})
        if "changes" in metadata:
            changes = metadata["changes"]
            if (
                isinstance(changes, str)
                and self.config.include_changes_under_chars
                and len(changes) < self.config.include_changes_under_chars
            ):
                features.append(f"Modification: {changes}")

        # Analyze metrics for standout characteristics
        metrics = program.get("metrics", {})
        for metric_name, value in metrics.items():
            if isinstance(value, (int, float)):
                if value >= 0.9:
                    features.append(f"Excellent {metric_name} ({value:.3f})")
                elif value <= 0.3:
                    features.append(f"Alternative {metric_name} approach")

        # Code-based features (simple heuristics)
        code = program.get("code", "")
        if code:
            code_lower = code.lower()
            if "class" in code_lower and "def __init__" in code_lower:
                features.append("Object-oriented approach")
            if "numpy" in code_lower or "np." in code_lower:
                features.append("NumPy-based implementation")
            if "for" in code_lower and "while" in code_lower:
                features.append("Mixed iteration strategies")
            if (
                self.config.concise_implementation_max_lines
                and len(code.split("\n"))
                <= self.config.concise_implementation_max_lines
            ):
                features.append("Concise implementation")
            elif (
                self.config.comprehensive_implementation_min_lines
                and len(code.split("\n"))
                >= self.config.comprehensive_implementation_min_lines
            ):
                features.append("Comprehensive implementation")

        # Default if no specific features found
        if not features:
            program_type = self._determine_program_type(program)
            features.append(f"{program_type} approach to the problem")

        # Use num_top_programs as limit for features (similar to how we limit programs)
        feature_limit = self.config.num_top_programs
        return ", ".join(features[:feature_limit])

    def _apply_template_variations(self, template: str) -> str:
        """Apply stochastic variations to the template"""
        result = template

        # Apply variations defined in the config
        for key, variations in self.config.template_variations.items():
            if variations and f"{{{key}}}" in result:
                chosen_variation = random.choice(variations)
                result = result.replace(f"{{{key}}}", chosen_variation)

        return result

    def _render_artifacts(self, artifacts: Dict[str, Union[str, bytes]]) -> str:
        """
        Render artifacts for prompt inclusion

        Args:
            artifacts: Dictionary of artifact name to content

        Returns:
            Formatted string for prompt inclusion (empty string if no artifacts)
        """
        if not artifacts:
            return ""

        sections = []

        # Process all artifacts using .items()
        for key, value in artifacts.items():
            content = self._safe_decode_artifact(value)
            # Truncate if too long
            if len(content) > self.config.max_artifact_bytes:
                content = (
                    content[: self.config.max_artifact_bytes] + "\n... (truncated)"
                )

            sections.append(f"### {key}\n```\n{content}\n```")

        if sections:
            return "## Last Execution Output\n\n" + "\n\n".join(sections)
        else:
            return ""

    def _safe_decode_artifact(self, value: Union[str, bytes]) -> str:
        """
        Safely decode an artifact value to string

        Args:
            value: Artifact value (string or bytes)

        Returns:
            String representation of the value
        """
        if isinstance(value, str):
            # Apply security filter if enabled
            if self.config.artifact_security_filter:
                return self._apply_security_filter(value)
            return value
        elif isinstance(value, bytes):
            try:
                decoded = value.decode("utf-8", errors="replace")
                if self.config.artifact_security_filter:
                    return self._apply_security_filter(decoded)
                return decoded
            except Exception:
                return f"<binary data: {len(value)} bytes>"
        else:
            return str(value)

    def _apply_security_filter(self, text: str) -> str:
        """
        Apply security filtering to artifact text

        Args:
            text: Input text

        Returns:
            Filtered text with potential secrets/sensitive info removed
        """
        import re

        # Remove ANSI escape sequences
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        filtered = ansi_escape.sub("", text)

        # Basic patterns for common secrets (can be expanded)
        secret_patterns = [
            (r"[A-Za-z0-9]{32,}", "<REDACTED_TOKEN>"),  # Long alphanumeric tokens
            (r"sk-[A-Za-z0-9]{48}", "<REDACTED_API_KEY>"),  # OpenAI-style API keys
            (r"password[=:]\s*[^\s]+", "password=<REDACTED>"),  # Password assignments
            (r"token[=:]\s*[^\s]+", "token=<REDACTED>"),  # Token assignments
        ]

        for pattern, replacement in secret_patterns:
            filtered = re.sub(pattern, replacement, filtered, flags=re.IGNORECASE)

        return filtered
