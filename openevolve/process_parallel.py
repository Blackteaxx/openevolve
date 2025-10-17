"""
Process-based parallel controller for true parallelism
"""

import asyncio
import logging
import multiprocessing as mp
import time
from concurrent.futures import Future, ProcessPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from openevolve.config import Config
from openevolve.database import Program, ProgramDatabase
from openevolve.utils.metrics_utils import safe_numeric_average
from openevolve.experience_kb_service import ExperienceKBService, KBUpdateResult

logger = logging.getLogger(__name__)


@dataclass
class SerializableResult:
    """Result that can be pickled and sent between processes"""

    child_program_dict: Optional[Dict[str, Any]] = None
    parent_id: Optional[str] = None
    iteration_time: float = 0.0
    prompt: Optional[Dict[str, str]] = None
    llm_response: Optional[str] = None
    artifacts: Optional[Dict[str, Any]] = None
    iteration: int = 0
    error: Optional[str] = None
    # Explanation prompt/response for logging
    explanation_prompt: Optional[Dict[str, str]] = None
    explanation_response: Optional[str] = None
    # Experience KB prompt/response for logging
    experience_kb_prompt: Optional[Dict[str, str]] = None
    experience_kb_response: Optional[str] = None
    experience_kb_summary: Optional[str] = None


def _worker_init(
    config_dict: dict, evaluation_file: str, parent_env: dict = None
) -> None:
    """Initialize worker process with necessary components"""
    import os

    # Set environment from parent process
    if parent_env:
        os.environ.update(parent_env)

    global _worker_config
    global _worker_evaluation_file
    global _worker_evaluator
    global _worker_llm_ensemble
    global _worker_prompt_sampler
    global _worker_explanation_service
    global _worker_experience_kb_service

    # Store config for later use
    # Reconstruct Config object from nested dictionaries
    from openevolve.config import (
        Config,
        DatabaseConfig,
        EvaluatorConfig,
        LLMConfig,
        LLMModelConfig,
        PromptConfig,
        ExplanationConfig,
        ExperienceKBConfig,
    )

    # Reconstruct model objects
    models = [LLMModelConfig(**m) for m in config_dict["llm"]["models"]]
    evaluator_models = [
        LLMModelConfig(**m) for m in config_dict["llm"]["evaluator_models"]
    ]

    # Create LLM config with models
    llm_dict = config_dict["llm"].copy()
    llm_dict["models"] = models
    llm_dict["evaluator_models"] = evaluator_models
    llm_config = LLMConfig(**llm_dict)

    # Create other configs
    prompt_config = PromptConfig(**config_dict["prompt"])
    database_config = DatabaseConfig(**config_dict["database"])
    evaluator_config = EvaluatorConfig(**config_dict["evaluator"])
    # Explanation config (optional) with dedicated LLM reconstruction
    explanation_config = None
    if "explanation" in config_dict and isinstance(config_dict["explanation"], dict):
        exp_dict = dict(config_dict["explanation"])  # shallow copy
        if "llm" in exp_dict and isinstance(exp_dict["llm"], dict):
            exp_llm_dict = dict(exp_dict["llm"])  # shallow copy
            # Reconstruct nested model configs for explanation LLM
            if "models" in exp_llm_dict and isinstance(exp_llm_dict["models"], list):
                exp_llm_dict["models"] = [
                    LLMModelConfig(**m) for m in exp_llm_dict["models"]
                ]
            if "evaluator_models" in exp_llm_dict and isinstance(
                exp_llm_dict["evaluator_models"], list
            ):
                exp_llm_dict["evaluator_models"] = [
                    LLMModelConfig(**m) for m in exp_llm_dict["evaluator_models"]
                ]
            exp_dict["llm"] = LLMConfig(**exp_llm_dict)
        explanation_config = ExplanationConfig(**exp_dict)

    # Experience KB config (optional) with dedicated LLM reconstruction
    experience_kb_config = None
    if "experience_kb" in config_dict and isinstance(config_dict["experience_kb"], dict):
        kb_dict = dict(config_dict["experience_kb"])  # shallow copy
        if "llm" in kb_dict and isinstance(kb_dict["llm"], dict):
            kb_llm_dict = dict(kb_dict["llm"])  # shallow copy
            if "models" in kb_llm_dict and isinstance(kb_llm_dict["models"], list):
                kb_llm_dict["models"] = [LLMModelConfig(**m) for m in kb_llm_dict["models"]]
            if "evaluator_models" in kb_llm_dict and isinstance(kb_llm_dict["evaluator_models"], list):
                kb_llm_dict["evaluator_models"] = [LLMModelConfig(**m) for m in kb_llm_dict["evaluator_models"]]
            kb_dict["llm"] = LLMConfig(**kb_llm_dict)
        experience_kb_config = ExperienceKBConfig(**kb_dict)

    _worker_config = Config(
        llm=llm_config,
        prompt=prompt_config,
        database=database_config,
        evaluator=evaluator_config,
        explanation=explanation_config if explanation_config else None,
        experience_kb=experience_kb_config if experience_kb_config else ExperienceKBConfig(),
        **{
            k: v
            for k, v in config_dict.items()
            if k not in ["llm", "prompt", "database", "evaluator", "explanation", "experience_kb"]
        },
    )
    _worker_evaluation_file = evaluation_file

    # These will be lazily initialized on first use
    _worker_evaluator = None
    _worker_llm_ensemble = None
    _worker_prompt_sampler = None
    _worker_explanation_service = None
    _worker_experience_kb_service = None


def _lazy_init_worker_components():
    """Lazily initialize expensive components on first use"""
    global _worker_evaluator
    global _worker_llm_ensemble
    global _worker_prompt_sampler
    global _worker_explanation_service
    global _worker_experience_kb_service

    if _worker_llm_ensemble is None:
        from openevolve.llm.ensemble import LLMEnsemble

        _worker_llm_ensemble = LLMEnsemble(_worker_config.llm.models)

    if _worker_prompt_sampler is None:
        from openevolve.prompt.sampler import PromptSampler

        _worker_prompt_sampler = PromptSampler(_worker_config.prompt)

    if _worker_evaluator is None:
        from openevolve.evaluator import Evaluator
        from openevolve.llm.ensemble import LLMEnsemble
        from openevolve.prompt.sampler import PromptSampler

        # Create evaluator-specific components
        evaluator_llm = LLMEnsemble(_worker_config.llm.evaluator_models)
        evaluator_prompt = PromptSampler(_worker_config.prompt)
        evaluator_prompt.set_templates("evaluator_system_message")

        _worker_evaluator = Evaluator(
            _worker_config.evaluator,
            _worker_evaluation_file,
            evaluator_llm,
            evaluator_prompt,
            database=None,  # No shared database in worker
        )

    # Initialize explanation service if enabled and not yet created
    if _worker_explanation_service is None:
        explanation_cfg = getattr(_worker_config, "explanation", None)
        if explanation_cfg and getattr(explanation_cfg, "enabled", False):
            from openevolve.explanation_service import ExplanationService
            from openevolve.llm.ensemble import LLMEnsemble

            # Choose ensemble role (evolution or evaluator),
            # but prefer dedicated explanation LLM config if provided.
            role = getattr(explanation_cfg, "ensemble_role", "evolution")
            if getattr(explanation_cfg, "llm", None):
                exp_llm_cfg = explanation_cfg.llm
                if role == "evaluator" and getattr(
                    exp_llm_cfg, "evaluator_models", None
                ):
                    explanation_llm = LLMEnsemble(exp_llm_cfg.evaluator_models)
                else:
                    explanation_llm = LLMEnsemble(exp_llm_cfg.models)
            else:
                if role == "evaluator":
                    explanation_llm = LLMEnsemble(_worker_config.llm.evaluator_models)
                else:
                    explanation_llm = _worker_llm_ensemble or LLMEnsemble(
                        _worker_config.llm.models
                    )

            # Reuse TemplateManager from prompt sampler
            template_manager = _worker_prompt_sampler.template_manager
            _worker_explanation_service = ExplanationService(
                template_manager=template_manager,
                llm_ensemble=explanation_llm,
                config=explanation_cfg,
            )

    # Initialize Experience KB service if enabled
    if _worker_experience_kb_service is None:
        kb_cfg = getattr(_worker_config, "experience_kb", None)
        if kb_cfg and getattr(kb_cfg, "enabled", False):
            try:
                # Reuse TemplateManager from prompt sampler
                template_manager = _worker_prompt_sampler.template_manager
                # Prefer dedicated KB LLM if provided, else None (service tolerates None)
                from openevolve.llm.ensemble import LLMEnsemble
                kb_llm = None
                if getattr(kb_cfg, "llm", None) and getattr(kb_cfg.llm, "models", None):
                    kb_llm = LLMEnsemble(kb_cfg.llm.models)

                # Resolve output dir for worker
                output_dir = None
                try:
                    # Will be set later via set_output_dir from db_snapshot
                    output_dir = None
                except Exception:
                    output_dir = None

                _worker_experience_kb_service = ExperienceKBService(
                    template_manager=template_manager,
                    config=kb_cfg,
                    llm_ensemble=kb_llm,
                    output_dir=output_dir,
                )
            except Exception as e:
                # If KB service init fails, log and continue without it
                logger.error(f"Failed to initialize ExperienceKBService: {e}")
                _worker_experience_kb_service = None


def _run_iteration_worker(
    iteration: int,
    db_snapshot: Dict[str, Any],
    parent_id: str,
    inspiration_ids: List[str],
) -> SerializableResult:
    """Run a single iteration in a worker process"""
    try:
        # Lazy initialization
        _lazy_init_worker_components()

        # Reconstruct programs from snapshot
        programs = {
            pid: Program(**prog_dict)
            for pid, prog_dict in db_snapshot["programs"].items()
        }

        parent = programs[parent_id]
        inspirations = [programs[pid] for pid in inspiration_ids if pid in programs]

        # Get parent artifacts if available
        parent_artifacts = db_snapshot["artifacts"].get(parent_id)

        # Get parent program of current program
        grand_parent_id = parent.parent_id
        grand_parent = None
        if grand_parent_id and grand_parent_id in programs:
            grand_parent = programs[grand_parent_id]

        # Get island-specific programs for context
        parent_island = parent.metadata.get("island", db_snapshot["current_island"])
        island_programs = [
            programs[pid]
            for pid in db_snapshot["islands"][parent_island]
            if pid in programs
        ]

        # Sort by metrics for top programs
        island_programs.sort(
            key=lambda p: p.metrics.get(
                "combined_score", safe_numeric_average(p.metrics)
            ),
            reverse=True,
        )

        # Use config values for limits instead of hardcoding
        programs_for_prompt = island_programs[
            : _worker_config.prompt.num_top_programs  # 2025.9.29: revise from num_top_programs + num_diverse_programs to num_top_programs
        ]

        # Build prompt
        # KB: Prepare experience KB summary if enabled
        experience_kb_summary = ""
        kb_cfg = getattr(_worker_config, "experience_kb", None)
        if kb_cfg and getattr(kb_cfg, "enabled", False) and getattr(kb_cfg, "include_in_prompt", True):
            try:
                # Update storage dir to worker snapshot output_dir if provided
                if _worker_experience_kb_service and db_snapshot.get("output_dir"):
                    _worker_experience_kb_service.set_output_dir(db_snapshot.get("output_dir"))
                if _worker_experience_kb_service:
                    experience_kb_summary = _worker_experience_kb_service.get_summary(
                        max_bytes=getattr(kb_cfg, "max_kb_bytes", None)
                    )
            except Exception:
                experience_kb_summary = ""
        prompt = _worker_prompt_sampler.build_prompt(
            current_program=parent.code,
            program_metrics=parent.metrics,
            current_explanation=parent.metadata.get("explanation"),
            parent_program=grand_parent.code if grand_parent else None,
            parent_metrics=grand_parent.metrics if grand_parent else None,
            top_programs=[p.to_dict() for p in programs_for_prompt],
            inspirations=[p.to_dict() for p in inspirations],
            language=_worker_config.language,
            evolution_round=iteration,
            diff_based_evolution=_worker_config.diff_based_evolution,
            program_artifacts=parent_artifacts,
            feature_dimensions=db_snapshot.get("feature_dimensions", []),
            experience_kb_summary=experience_kb_summary,
            # 传递自定义的 KB 区块模板键（若配置存在则使用）
            experience_kb_section_key=getattr(kb_cfg, "section_template_key", None),
        )

        iteration_start = time.time()

        # Generate code modification (sync wrapper for async)
        try:
            llm_response = asyncio.run(
                _worker_llm_ensemble.generate_with_context(
                    system_message=prompt["system"],
                    messages=[{"role": "user", "content": prompt["user"]}],
                )
            )
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return SerializableResult(
                error=f"LLM generation failed: {str(e)}", iteration=iteration
            )

        # Check for None response
        if llm_response is None:
            return SerializableResult(
                error="LLM returned None response", iteration=iteration
            )

        # Parse response based on evolution mode
        # Add a configurable switch to control whether explanation is extracted/used.
        explanation_text = None
        use_explanation = getattr(_worker_config, "use_explanation", None)
        if _worker_config.diff_based_evolution:
            from openevolve.utils.code_utils import (
                apply_diff,
                apply_validated_diff_blocks,
                extract_diffs,
                format_diff_summary,
                extract_explanation,
                validate_diff_blocks,
                format_diff_blocks_string,
            )

            # Extract diff blocks and validate them against the parent program
            raw_diff_blocks = extract_diffs(llm_response)
            diff_blocks = validate_diff_blocks(parent.code, raw_diff_blocks)

            if not diff_blocks:
                return SerializableResult(
                    error="No valid diffs found in response", iteration=iteration
                )

            child_code = apply_validated_diff_blocks(parent.code, diff_blocks)
            if child_code == parent.code:
                return SerializableResult(
                    error="Generated code is identical to parent code",
                    iteration=iteration,
                )
            changes_summary = format_diff_summary(diff_blocks)
            # Controlled explanation extraction (disabled by default in diff-based mode)
            if use_explanation:
                explanation_text = extract_explanation(llm_response)
        else:
            from openevolve.utils.code_utils import (
                parse_full_rewrite,
                extract_explanation,
            )

            new_code = parse_full_rewrite(llm_response, _worker_config.language)
            if not new_code:
                return SerializableResult(
                    error="No valid code found in response", iteration=iteration
                )

            child_code = new_code
            changes_summary = "Full rewrite"
            # Controlled explanation extraction (enabled by default in full rewrite mode)
            if use_explanation:
                explanation_text = extract_explanation(llm_response)

        # Check code length
        if len(child_code) > _worker_config.max_code_length:
            return SerializableResult(
                error=f"Generated code exceeds maximum length ({len(child_code)} > {_worker_config.max_code_length})",
                iteration=iteration,
            )

        # Evaluate the child program
        # This stage will be very time-consuming in Code Optimization Task
        import uuid

        child_id = str(uuid.uuid4())
        child_metrics = asyncio.run(
            _worker_evaluator.evaluate_program(child_code, child_id)
        )

        # Get artifacts
        artifacts = _worker_evaluator.get_pending_artifacts(child_id)

        # Initialize optional explanation text
        explanation_text = None

        # Optionally build and generate explanation via ExplanationService
        explanation_prompt = None
        explanation_response = None
        if use_explanation and _worker_explanation_service is not None:
            try:
                # Get diff_blocks if available (for diff-based evolution)
                diff_blocks_str = None
                if _worker_config.diff_based_evolution and "diff_blocks" in locals():
                    diff_blocks_str = format_diff_blocks_string(diff_blocks)

                explanation_prompt = _worker_explanation_service.build_prompt(
                    metrics=child_metrics,
                    artifacts=artifacts,
                    changes_summary=changes_summary,
                    current_code=child_code,
                    parent_code=parent.code,
                    language=_worker_config.language,
                    iteration=iteration,
                    # Prefer concise task description if provided; fallback to system_message
                    task_description=(
                        getattr(_worker_config.prompt, "task_description", None)
                        or _worker_config.prompt.system_message
                    ),
                    parent_metrics=parent.metrics,
                    diff_blocks=diff_blocks_str,
                )
                explanation_response = asyncio.run(
                    _worker_explanation_service.generate(explanation_prompt)
                )
                # Prefer service-generated explanation when available
                if explanation_response:
                    explanation_text = explanation_response
            except Exception as ex:
                logger.warning(f"ExplanationService generation failed: {ex}")

        # Optionally compute and record Experience KB update
        experience_kb_prompt = None
        experience_kb_response = None
        kb_update_result: Optional[KBUpdateResult] = None
        if _worker_experience_kb_service is not None:
            try:
                parent_score = parent.metrics.get("combined_score")
                child_score = child_metrics.get("combined_score")
                # Basic policy: record all changes if record_failures, else only improvements
                record = True
                kb_cfg = getattr(_worker_config, "experience_kb", None)
                if kb_cfg:
                    if not kb_cfg.record_failures:
                        try:
                            record = (
                                isinstance(parent_score, (int, float))
                                and isinstance(child_score, (int, float))
                                and float(child_score) - float(parent_score)
                                >= float(getattr(kb_cfg, "min_improvement", 0.0))
                            )
                        except Exception:
                            record = False
                if record:
                    # Prepare diff blocks string if available
                    diff_blocks_str = None
                    if _worker_config.diff_based_evolution and "diff_blocks" in locals():
                        diff_blocks_str = format_diff_blocks_string(diff_blocks)

                    experience_kb_prompt = _worker_experience_kb_service.build_update_prompt(
                        metrics=child_metrics,
                        artifacts=artifacts,
                        changes_summary=changes_summary,
                        current_code=child_code,
                        parent_code=parent.code,
                        language=_worker_config.language,
                        iteration=iteration,
                        task_description=(
                            getattr(_worker_config.prompt, "task_description", None)
                            or _worker_config.prompt.system_message
                        ),
                        parent_metrics=parent.metrics,
                        diff_blocks=diff_blocks_str,
                        explanation=explanation_text,
                    )
                    kb_update_result = asyncio.run(
                        _worker_experience_kb_service.generate(experience_kb_prompt)
                    )
                    experience_kb_response = kb_update_result.response
            except Exception as ex:
                logger.warning(f"ExperienceKBService update failed: {ex}")

        # Create child program
        metadata = {
            "changes": changes_summary,
            "parent_metrics": parent.metrics,
            "island": parent_island,
            "diff_blocks": format_diff_blocks_string(diff_blocks)
            if _worker_config.diff_based_evolution
            else None,
        }
        if use_explanation and explanation_text:
            metadata["explanation"] = explanation_text

        child_program = Program(
            id=child_id,
            code=child_code,
            language=_worker_config.language,
            parent_id=parent.id,
            generation=parent.generation + 1,
            metrics=child_metrics,
            iteration_found=iteration,
            metadata=metadata,
        )

        iteration_time = time.time() - iteration_start

        return SerializableResult(
            child_program_dict=child_program.to_dict(),
            parent_id=parent.id,
            iteration_time=iteration_time,
            prompt=prompt,
            llm_response=llm_response,
            artifacts=artifacts,
            iteration=iteration,
            explanation_prompt=explanation_prompt,
            explanation_response=explanation_response,
            experience_kb_prompt=experience_kb_prompt,
            experience_kb_response=experience_kb_response,
            experience_kb_summary=(kb_update_result.summary if kb_update_result else experience_kb_summary),
        )

    except Exception as e:
        logger.exception(f"Error in worker iteration {iteration}")
        return SerializableResult(error=str(e), iteration=iteration)


class ProcessParallelController:
    """Controller for process-based parallel evolution"""

    def __init__(
        self,
        config: Config,
        evaluation_file: str,
        database: ProgramDatabase,
        evolution_tracer=None,
        output_dir: str = None,
    ):
        self.config = config
        self.evaluation_file = evaluation_file
        self.database = database
        self.evolution_tracer = evolution_tracer
        self.output_dir = output_dir

        self.executor: Optional[ProcessPoolExecutor] = None
        self.shutdown_event = mp.Event()
        self.early_stopping_triggered = False

        # Number of worker processes
        self.num_workers = config.evaluator.parallel_evaluations

        # Worker-to-island pinning for true island isolation
        self.num_islands = config.database.num_islands
        self.worker_island_map = {}

        # Distribute workers across islands using modulo
        for worker_id in range(self.num_workers):
            island_id = worker_id % self.num_islands
            self.worker_island_map[worker_id] = island_id

        logger.info(
            f"Initialized process parallel controller with {self.num_workers} workers"
        )
        logger.info(f"Worker-to-island mapping: {self.worker_island_map}")

    def _serialize_config(self, config: Config) -> dict:
        """Serialize config object to a dictionary that can be pickled"""
        # Manual serialization to handle nested objects properly
        return {
            "llm": {
                "models": [asdict(m) for m in config.llm.models],
                "evaluator_models": [asdict(m) for m in config.llm.evaluator_models],
                "api_base": config.llm.api_base,
                "api_key": config.llm.api_key,
                "temperature": config.llm.temperature,
                "top_p": config.llm.top_p,
                "max_tokens": config.llm.max_tokens,
                "timeout": config.llm.timeout,
                "retries": config.llm.retries,
                "retry_delay": config.llm.retry_delay,
            },
            "prompt": asdict(config.prompt),
            "database": asdict(config.database),
            "evaluator": asdict(config.evaluator),
            "explanation": {
                "enabled": config.explanation.enabled,
                "template_key": config.explanation.template_key,
                "system_message_key": config.explanation.system_message_key,
                "include_code": config.explanation.include_code,
                "max_artifacts_bytes": config.explanation.max_artifacts_bytes,
                "ensemble_role": config.explanation.ensemble_role,
                "llm": {
                    "models": [asdict(m) for m in config.explanation.llm.models],
                    "evaluator_models": [
                        asdict(m) for m in config.explanation.llm.evaluator_models
                    ],
                    "api_base": config.explanation.llm.api_base,
                    "api_key": config.explanation.llm.api_key,
                    "temperature": config.explanation.llm.temperature,
                    "top_p": config.explanation.llm.top_p,
                    "max_tokens": config.explanation.llm.max_tokens,
                    "timeout": config.explanation.llm.timeout,
                    "retries": config.explanation.llm.retries,
                    "retry_delay": config.explanation.llm.retry_delay,
                }
                if config.explanation.llm
                else None,
            },
            "experience_kb": {
                "enabled": config.experience_kb.enabled,
                "include_in_prompt": config.experience_kb.include_in_prompt,
                "section_template_key": getattr(
                    config.experience_kb, "section_template_key", "experience_kb_section"
                ),
                "update_template_key": config.experience_kb.update_template_key,
                "update_system_message_key": config.experience_kb.update_system_message_key,
                "storage_dir": config.experience_kb.storage_dir,
                "max_kb_bytes": config.experience_kb.max_kb_bytes,
                "min_improvement": config.experience_kb.min_improvement,
                "record_failures": config.experience_kb.record_failures,
                "llm": (
                    {
                        "models": [asdict(m) for m in getattr(config.experience_kb.llm, "models", [])],
                        "evaluator_models": [
                            asdict(m)
                            for m in getattr(config.experience_kb.llm, "evaluator_models", [])
                        ],
                        "api_base": getattr(config.experience_kb.llm, "api_base", None),
                        "api_key": getattr(config.experience_kb.llm, "api_key", None),
                        "temperature": getattr(config.experience_kb.llm, "temperature", None),
                        "top_p": getattr(config.experience_kb.llm, "top_p", None),
                        "max_tokens": getattr(config.experience_kb.llm, "max_tokens", None),
                        "timeout": getattr(config.experience_kb.llm, "timeout", None),
                        "retries": getattr(config.experience_kb.llm, "retries", None),
                        "retry_delay": getattr(config.experience_kb.llm, "retry_delay", None),
                    }
                    if getattr(config.experience_kb, "llm", None) is not None
                    else None
                ),
            },
            "max_iterations": config.max_iterations,
            "checkpoint_interval": config.checkpoint_interval,
            "log_level": config.log_level,
            "log_dir": config.log_dir,
            "random_seed": config.random_seed,
            "diff_based_evolution": config.diff_based_evolution,
            "max_code_length": config.max_code_length,
            "language": config.language,
            # Custom flags
            "use_explanation": config.use_explanation,
        }

    def start(self) -> None:
        """Start the process pool"""
        # Convert config to dict for pickling
        # We need to be careful with nested dataclasses
        config_dict = self._serialize_config(self.config)

        # Pass current environment to worker processes
        import os

        current_env = dict(os.environ)

        # Create process pool with initializer
        self.executor = ProcessPoolExecutor(
            max_workers=self.num_workers,
            initializer=_worker_init,
            initargs=(config_dict, self.evaluation_file, current_env),
        )

        logger.info(f"Started process pool with {self.num_workers} processes")

    def stop(self) -> None:
        """Stop the process pool"""
        self.shutdown_event.set()

        if self.executor:
            # 2025.9.20: Force to shutdown all the process
            self.executor.shutdown(wait=False)  # Do not wait for all tasks to complete
            self.executor = None

        logger.info("Stopped process pool")

    def request_shutdown(self) -> None:
        """Request graceful shutdown"""
        logger.info("Graceful shutdown requested...")
        self.shutdown_event.set()

    def _create_database_snapshot(self) -> Dict[str, Any]:
        """Create a serializable snapshot of the database state"""
        # Only include necessary data for workers
        snapshot = {
            "programs": {
                pid: prog.to_dict() for pid, prog in self.database.programs.items()
            },
            "islands": [list(island) for island in self.database.islands],
            "current_island": self.database.current_island,
            "feature_dimensions": self.database.config.feature_dimensions,
            "artifacts": {},  # Will be populated selectively
            "output_dir": self.output_dir,  # Add output directory for worker processes
        }

        # Include artifacts for programs that might be selected
        # IMPORTANT: This limits artifacts (execution outputs/errors) to first 100 programs only.
        # This does NOT affect program code - all programs are fully serialized above.
        # With max_artifact_bytes=20KB and population_size=1000, artifacts could be 20MB total,
        # which would significantly slow worker process initialization. The limit of 100 keeps
        # artifact data under 2MB while still providing execution context for recent programs.
        # Workers can still evolve properly as they have access to ALL program code.
        for pid in list(self.database.programs.keys())[:100]:
            artifacts = self.database.get_artifacts(pid)
            if artifacts:
                snapshot["artifacts"][pid] = artifacts

        return snapshot

    async def run_evolution(
        self,
        start_iteration: int,
        max_iterations: int,
        target_score: Optional[float] = None,
        checkpoint_callback=None,
    ):
        """Run evolution with process-based parallelism"""
        if not self.executor:
            raise RuntimeError("Process pool not started")

        total_iterations = start_iteration + max_iterations

        logger.info(
            f"Starting process-based evolution from iteration {start_iteration} "
            f"for {max_iterations} iterations (total: {total_iterations})"
        )

        # Track pending futures by island to maintain distribution
        pending_futures: Dict[int, Future] = {}
        island_pending: Dict[int, List[int]] = {i: [] for i in range(self.num_islands)}
        batch_size = min(self.num_workers * 2, max_iterations)

        # Submit initial batch - distribute across islands
        batch_per_island = (
            max(1, batch_size // self.num_islands) if batch_size > 0 else 0
        )
        current_iteration = start_iteration

        # Round-robin distribution across islands
        for island_id in range(self.num_islands):
            for _ in range(batch_per_island):
                if current_iteration < total_iterations:
                    # Note: Submit iteration to process pool, which starts mission
                    # This will block if process pool is full, but that's fine
                    # as we're distributing evenly across islands
                    future = self._submit_iteration(current_iteration, island_id)
                    if future:
                        pending_futures[current_iteration] = future
                        island_pending[island_id].append(current_iteration)
                    current_iteration += 1

        next_iteration = current_iteration
        completed_iterations = 0

        # Island management
        programs_per_island = max(
            1, max_iterations // (self.config.database.num_islands * 10)
        )
        current_island_counter = 0

        # Early stopping tracking
        early_stopping_enabled = self.config.early_stopping_patience is not None
        if early_stopping_enabled:
            best_score = float("-inf")
            iterations_without_improvement = 0
            logger.info(
                f"Early stopping enabled: patience={self.config.early_stopping_patience}, "
                f"threshold={self.config.convergence_threshold}, "
                f"metric={self.config.early_stopping_metric}"
            )
        else:
            logger.info("Early stopping disabled")

        # Process results as they complete
        while (
            pending_futures
            and completed_iterations < max_iterations
            and not self.shutdown_event.is_set()
        ):
            # Find completed futures. Process one per iteration.
            completed_iteration = None
            for iteration, future in list(pending_futures.items()):
                if future.done():
                    completed_iteration = iteration
                    break

            if completed_iteration is None:
                await asyncio.sleep(0.01)
                continue

            # Process completed result
            future = pending_futures.pop(completed_iteration)

            try:
                # Use evaluator timeout + buffer to gracefully handle stuck processes
                timeout_seconds = self.config.evaluator.timeout + 30
                result = future.result(timeout=timeout_seconds)

                if result.error:
                    logger.warning(
                        f"Iteration {completed_iteration} error: {result.error}"
                    )
                elif result.child_program_dict:
                    # Reconstruct program from dict
                    child_program = Program(**result.child_program_dict)

                    # Add to database (will auto-inherit parent's island)
                    # No need to specify target_island - database will handle parent island inheritance
                    self.database.add(child_program, iteration=completed_iteration)

                    # Store artifacts
                    if result.artifacts:
                        self.database.store_artifacts(
                            child_program.id, result.artifacts
                        )

                    # Log evolution trace
                    if self.evolution_tracer:
                        # Retrieve parent program for trace logging
                        parent_program = (
                            self.database.get(result.parent_id)
                            if result.parent_id
                            else None
                        )
                        if parent_program:
                            # Determine island ID
                            island_id = child_program.metadata.get(
                                "island", self.database.current_island
                            )

                            self.evolution_tracer.log_trace(
                                iteration=completed_iteration,
                                parent_program=parent_program,
                                child_program=child_program,
                                prompt=result.prompt,
                                llm_response=result.llm_response,
                                artifacts=result.artifacts,
                                island_id=island_id,
                                metadata={
                                    "iteration_time": result.iteration_time,
                                    "changes": child_program.metadata.get(
                                        "changes", ""
                                    ),
                                },
                            )

                    # Log prompts
                    if result.prompt:
                        self.database.log_prompt(
                            template_key=(
                                "full_rewrite_user"
                                if not self.config.diff_based_evolution
                                else "diff_user"
                            ),
                            program_id=child_program.id,
                            prompt=result.prompt,
                            responses=[result.llm_response]
                            if result.llm_response
                            else [],
                        )

                    # Log explanation prompt/response if present
                    if (
                        getattr(self.config, "use_explanation", False)
                        and result.explanation_prompt
                    ):
                        try:
                            self.database.log_prompt(
                                template_key=self.config.explanation.template_key,
                                program_id=child_program.id,
                                prompt=result.explanation_prompt,
                                responses=[result.explanation_response]
                                if result.explanation_response
                                else [],
                            )
                        except Exception as ex:
                            logger.warning(
                                f"Failed to log explanation prompt/response: {ex}"
                            )

                    # Log Experience KB update prompt/response if present
                    if result.experience_kb_prompt:
                        try:
                            kb_template_key = (
                                self.config.experience_kb.update_template_key
                                if self.config.experience_kb
                                else "experience_kb_update"
                            )
                            self.database.log_prompt(
                                template_key=kb_template_key,
                                program_id=child_program.id,
                                prompt=result.experience_kb_prompt,
                                responses=[result.experience_kb_response]
                                if result.experience_kb_response
                                else [],
                            )
                        except Exception as ex:
                            logger.warning(
                                f"Failed to log Experience KB prompt/response: {ex}"
                            )

                    # Island management
                    if (
                        completed_iteration > start_iteration
                        and current_island_counter >= programs_per_island
                    ):
                        self.database.next_island()
                        current_island_counter = 0
                        logger.debug(
                            f"Switched to island {self.database.current_island}"
                        )

                    current_island_counter += 1
                    self.database.increment_island_generation()

                    # Check migration
                    if self.database.should_migrate():
                        logger.info(
                            f"Performing migration at iteration {completed_iteration}"
                        )
                        self.database.migrate_programs()
                        self.database.log_island_status()

                    # Log progress
                    logger.info(
                        f"Iteration {completed_iteration}: "
                        f"Program {child_program.id} "
                        f"(parent: {result.parent_id}) "
                        f"completed in {result.iteration_time:.2f}s"
                    )

                    if child_program.metrics:
                        metrics_str = ", ".join(
                            [
                                f"{k}={v:.4f}"
                                if isinstance(v, (int, float))
                                else f"{k}={v}"
                                for k, v in child_program.metrics.items()
                            ]
                        )
                        logger.info(f"Metrics: {metrics_str}")

                        # Check if this is the first program without combined_score
                        if not hasattr(self, "_warned_about_combined_score"):
                            self._warned_about_combined_score = False

                        if (
                            "combined_score" not in child_program.metrics
                            and not self._warned_about_combined_score
                        ):
                            avg_score = safe_numeric_average(child_program.metrics)
                            logger.warning(
                                f"⚠️  No 'combined_score' metric found in evaluation results. "
                                f"Using average of all numeric metrics ({avg_score:.4f}) for evolution guidance. "
                                f"For better evolution results, please modify your evaluator to return a 'combined_score' "
                                f"metric that properly weights different aspects of program performance."
                            )
                            self._warned_about_combined_score = True

                    # Check for new best
                    if self.database.best_program_id == child_program.id:
                        logger.info(
                            f"🌟 New best solution found at iteration {completed_iteration}: "
                            f"{child_program.id}"
                        )

                    # Checkpoint callback
                    # Don't checkpoint at iteration 0 (that's just the initial program)
                    if (
                        completed_iteration > 0
                        and completed_iteration % self.config.checkpoint_interval == 0
                    ):
                        logger.info(
                            f"Checkpoint interval reached at iteration {completed_iteration}"
                        )
                        self.database.log_island_status()
                        if checkpoint_callback:
                            checkpoint_callback(completed_iteration)

                    # Check target score
                    if target_score is not None and child_program.metrics:
                        numeric_metrics = [
                            v
                            for v in child_program.metrics.values()
                            if isinstance(v, (int, float))
                        ]
                        if numeric_metrics:
                            avg_score = sum(numeric_metrics) / len(numeric_metrics)
                            if avg_score >= target_score:
                                logger.info(
                                    f"Target score {target_score} reached at iteration {completed_iteration}"
                                )
                                break

                    # Check early stopping
                    if early_stopping_enabled and child_program.metrics:
                        # Get the metric to track for early stopping
                        current_score = None
                        if self.config.early_stopping_metric in child_program.metrics:
                            current_score = child_program.metrics[
                                self.config.early_stopping_metric
                            ]
                        elif self.config.early_stopping_metric == "combined_score":
                            # Default metric not found, use safe average (standard pattern)
                            current_score = safe_numeric_average(child_program.metrics)
                        else:
                            # User specified a custom metric that doesn't exist
                            logger.warning(
                                f"Early stopping metric '{self.config.early_stopping_metric}' not found, using safe numeric average"
                            )
                            current_score = safe_numeric_average(child_program.metrics)

                        if current_score is not None and isinstance(
                            current_score, (int, float)
                        ):
                            # Check for improvement
                            improvement = current_score - best_score
                            if improvement >= self.config.convergence_threshold:
                                best_score = current_score
                                iterations_without_improvement = 0
                                logger.debug(
                                    f"New best score: {best_score:.4f} (improvement: {improvement:+.4f})"
                                )
                            else:
                                iterations_without_improvement += 1
                                logger.debug(
                                    f"No improvement: {iterations_without_improvement}/{self.config.early_stopping_patience}"
                                )

                            # Check if we should stop
                            if (
                                iterations_without_improvement
                                >= self.config.early_stopping_patience
                            ):
                                self.early_stopping_triggered = True
                                logger.info(
                                    f"🛑 Early stopping triggered at iteration {completed_iteration}: "
                                    f"No improvement for {iterations_without_improvement} iterations "
                                    f"(best score: {best_score:.4f})"
                                )
                                break

            except FutureTimeoutError:
                logger.error(
                    f"⏰ Iteration {completed_iteration} timed out after {timeout_seconds}s "
                    f"(evaluator timeout: {self.config.evaluator.timeout}s + 30s buffer). "
                    f"Canceling future and continuing with next iteration."
                )
                # Cancel the future to clean up the process
                future.cancel()
            except Exception as e:
                logger.error(
                    f"Error processing result from iteration {completed_iteration}: {e}"
                )

            completed_iterations += 1

            # Remove completed iteration from island tracking
            for island_id, iteration_list in island_pending.items():
                if completed_iteration in iteration_list:
                    iteration_list.remove(completed_iteration)
                    break

            # Submit next iterations maintaining island balance
            for island_id in range(self.num_islands):
                if (
                    len(island_pending[island_id]) < batch_per_island
                    and next_iteration < total_iterations
                    and not self.shutdown_event.is_set()
                ):
                    future = self._submit_iteration(next_iteration, island_id)
                    if future:
                        pending_futures[next_iteration] = future
                        island_pending[island_id].append(next_iteration)
                        next_iteration += 1
                        break  # Only submit one iteration per completion to maintain balance

        # Handle shutdown
        if self.shutdown_event.is_set():
            logger.info("Shutdown requested, canceling remaining evaluations...")
            for future in pending_futures.values():
                future.cancel()

        # Log completion reason
        if self.early_stopping_triggered:
            logger.info(
                "✅ Evolution completed - Early stopping triggered due to convergence"
            )
        elif self.shutdown_event.is_set():
            logger.info("✅ Evolution completed - Shutdown requested")
        else:
            logger.info("✅ Evolution completed - Maximum iterations reached")

        return self.database.get_best_program()

    def _submit_iteration(
        self, iteration: int, island_id: Optional[int] = None
    ) -> Optional[Future]:
        """Submit an iteration to the process pool, optionally pinned to a specific island"""
        try:
            # Use specified island or current island
            target_island = (
                island_id if island_id is not None else self.database.current_island
            )

            # Use thread-safe sampling that doesn't modify shared state
            # This fixes the race condition from GitHub issue #246
            parent, inspirations = self.database.sample_from_island(
                island_id=target_island,
                num_inspirations=self.config.prompt.num_diverse_programs,  # 2025.9.29: revise from num_top_programs to num_diverse_programs
            )

            # Create database snapshot
            db_snapshot = self._create_database_snapshot()
            db_snapshot["sampling_island"] = (
                target_island  # Mark which island this is for
            )

            # Submit to process pool
            future = self.executor.submit(
                _run_iteration_worker,
                iteration,
                db_snapshot,
                parent.id,
                [insp.id for insp in inspirations],
            )

            return future

        except Exception as e:
            logger.error(f"Error submitting iteration {iteration}: {e}")
            return None
