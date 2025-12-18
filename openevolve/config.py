"""
Configuration handling for OpenEvolve
"""

import os
from dataclasses import dataclass, field
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import yaml


@dataclass
class LLMModelConfig:
    """Configuration for a single LLM model"""

    # API configuration
    api_base: str = None
    api_key: Optional[str] = None
    name: str = None

    # Custom LLM client
    init_client: Optional[Callable] = None

    # Weight for model in ensemble
    weight: float = 1.0

    # Generation parameters
    system_message: Optional[str] = None
    temperature: float = None
    top_p: float = None
    max_tokens: int = None

    # Request parameters
    timeout: int = None
    retries: int = None
    retry_delay: int = None

    # Reproducibility
    random_seed: Optional[int] = None

    # Reasoning parameters
    reasoning_effort: Optional[str] = None
    enable_thinking: Optional[bool] = None


@dataclass
class LLMConfig(LLMModelConfig):
    """Configuration for LLM models"""

    # API configuration
    api_base: str = "https://api.openai.com/v1"

    # Generation parameters
    system_message: Optional[str] = "system_message"
    temperature: float = 0.7
    top_p: float = 0.95
    max_tokens: int = 4096

    # Request parameters
    timeout: int = 60
    retries: int = 3
    retry_delay: int = 5

    # n-model configuration for evolution LLM ensemble
    models: List[LLMModelConfig] = field(default_factory=list)

    # n-model configuration for evaluator LLM ensemble
    evaluator_models: List[LLMModelConfig] = field(default_factory=lambda: [])

    # Backwardes compatibility with primary_model(_weight) options
    primary_model: str = None
    primary_model_weight: float = None
    secondary_model: str = None
    secondary_model_weight: float = None

    # Reasoning parameters (inherited from LLMModelConfig but can be overridden)
    reasoning_effort: Optional[str] = None
    enable_thinking: Optional[bool] = None

    def __post_init__(self):
        """Post-initialization to set up model configurations"""
        # Handle backward compatibility for primary_model(_weight) and secondary_model(_weight).
        if self.primary_model:
            # Create primary model
            primary_model = LLMModelConfig(
                name=self.primary_model, weight=self.primary_model_weight or 1.0
            )
            self.models.append(primary_model)

        if self.secondary_model:
            # Create secondary model (only if weight > 0)
            if self.secondary_model_weight is None or self.secondary_model_weight > 0:
                secondary_model = LLMModelConfig(
                    name=self.secondary_model,
                    weight=(
                        self.secondary_model_weight
                        if self.secondary_model_weight is not None
                        else 0.2
                    ),
                )
                self.models.append(secondary_model)

        # Only validate if this looks like a user config (has some model info)
        # Don't validate during internal/default initialization
        if (
            self.primary_model
            or self.secondary_model
            or self.primary_model_weight
            or self.secondary_model_weight
        ) and not self.models:
            raise ValueError(
                "No LLM models configured. Please specify 'models' array or "
                "'primary_model' in your configuration."
            )

        # If no evaluator models are defined, use the same models as for evolution
        if not self.evaluator_models:
            self.evaluator_models = self.models.copy()

        # Update models with shared configuration values
        shared_config = {
            "api_base": self.api_base,
            "api_key": self.api_key,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
            "retries": self.retries,
            "retry_delay": self.retry_delay,
            "random_seed": self.random_seed,
            "reasoning_effort": self.reasoning_effort,
            "enable_thinking": getattr(self, "enable_thinking", None),
        }
        self.update_model_params(shared_config)

    def update_model_params(
        self, args: Dict[str, Any], overwrite: bool = False
    ) -> None:
        """Update model parameters for all models"""
        for model in self.models + self.evaluator_models:
            for key, value in args.items():
                if overwrite or getattr(model, key, None) is None:
                    setattr(model, key, value)

    def rebuild_models(self) -> None:
        """Rebuild the models list after primary_model/secondary_model field changes"""
        # Clear existing models lists
        self.models = []
        self.evaluator_models = []

        # Re-run model generation logic from __post_init__
        if self.primary_model:
            # Create primary model
            primary_model = LLMModelConfig(
                name=self.primary_model, weight=self.primary_model_weight or 1.0
            )
            self.models.append(primary_model)

        if self.secondary_model:
            # Create secondary model (only if weight > 0)
            if self.secondary_model_weight is None or self.secondary_model_weight > 0:
                secondary_model = LLMModelConfig(
                    name=self.secondary_model,
                    weight=(
                        self.secondary_model_weight
                        if self.secondary_model_weight is not None
                        else 0.2
                    ),
                )
                self.models.append(secondary_model)

        # If no evaluator models are defined, use the same models as for evolution
        if not self.evaluator_models:
            self.evaluator_models = self.models.copy()

        # Update models with shared configuration values
        shared_config = {
            "api_base": self.api_base,
            "api_key": self.api_key,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
            "retries": self.retries,
            "retry_delay": self.retry_delay,
            "random_seed": self.random_seed,
            "reasoning_effort": self.reasoning_effort,
            "enable_thinking": getattr(self, "enable_thinking", None),
        }
        self.update_model_params(shared_config)


@dataclass
class PromptConfig:
    """Configuration for prompt generation"""

    template_dir: Optional[str] = None
    system_message: str = "system_message"
    evaluator_system_message: str = "evaluator_system_message"
    # Short task description used by Explanation/KB services instead of full system message
    task_description: Optional[str] = None

    # Number of examples to include in the prompt
    num_top_programs: int = 3
    num_diverse_programs: int = 2

    # Template stochasticity
    use_template_stochasticity: bool = True
    template_variations: Dict[str, List[str]] = field(default_factory=dict)

    # Meta-prompting
    use_meta_prompting: bool = False
    meta_prompt_weight: float = 0.1

    # Artifact rendering
    include_artifacts: bool = True
    max_artifact_bytes: int = 20 * 1024  # 20KB in prompt
    artifact_security_filter: bool = True

    # Explanation injection controls
    include_current_explanation_in_prompt: bool = True
    include_explanations_in_history: bool = True

    # Feature extraction and program labeling
    suggest_simplification_after_chars: Optional[int] = (
        500  # Suggest simplifying if program exceeds this many characters
    )
    include_changes_under_chars: Optional[int] = (
        100  # Include change descriptions in features if under this length
    )
    concise_implementation_max_lines: Optional[int] = (
        10  # Label as "concise" if program has this many lines or fewer
    )
    comprehensive_implementation_min_lines: Optional[int] = (
        50  # Label as "comprehensive" if program has this many lines or more
    )

    # Backward compatibility - deprecated
    code_length_threshold: Optional[int] = (
        None  # Deprecated: use suggest_simplification_after_chars
    )


@dataclass
class ExplanationConfig:
    """Configuration for post-evaluation explanation generation"""

    enabled: bool = False
    template_key: str = "explanation"
    system_message_key: str = "system_message"
    include_code: bool = False
    max_artifacts_bytes: int = 10 * 1024
    ensemble_role: str = "evolution"  # "evolution" or "evaluator"
    # Optional dedicated LLM configuration for explanation
    # If provided, overrides selection from evolution/evaluator ensembles
    llm: Optional[LLMConfig] = None


@dataclass
class ExperienceKBConfig:
    """Configuration for Experience Knowledge Base (KB) feature"""

    # Feature toggles
    enabled: bool = False
    include_in_prompt: bool = True

    # Prompt templates/keys
    # Key for the KB section template stored in .txt files
    section_template_key: str = "experience_kb_section"
    # Template keys used when generating KB updates
    update_template_key: str = "experience_kb_update"
    update_system_message_key: str = "experience_kb_system_message"
    # Critical agent templates
    critical_agent_template_key: str = "critical_agent"
    critical_agent_system_message_key: str = "critical_agent_system_message"

    # Storage and limits
    storage_dir: Optional[str] = None  # Defaults to <output_dir>/experience_kb
    max_kb_bytes: int = 64 * 1024  # Max bytes of KB summary injected into prompt

    # Summary controls
    # full: inject entire markdown (trimmed by max_kb_bytes)
    # random_rules: inject H1/H2 headers plus k random Rule blocks
    summary_mode: str = "full"  # Options: "full", "random_rules"
    random_rules_max_k: int = 5  # Randomly choose k in [0, max_k]

    # Initial markdown creation via template
    initial_markdown_template_path: Optional[str] = None

    # Update policy
    min_improvement: float = (
        0.01  # Trigger KB update when combined_score improves by this delta
    )
    record_failures: bool = False  # Record negative learnings when score drops

    # Diff application and retry
    max_update_attempts: int = 3
    require_all_matches: bool = False

    # Optional dedicated LLM configuration for KB updates
    llm: Optional[LLMConfig] = None


@dataclass
class DatabaseConfig:
    """Configuration for the program database"""

    # General settings
    db_path: Optional[str] = None  # Path to store database on disk
    in_memory: bool = True

    # Prompt and response logging to programs/<id>.json
    log_prompts: bool = True

    # Evolutionary parameters
    population_size: int = 1000
    archive_size: int = 100
    num_islands: int = 5

    # Selection parameters
    elite_selection_ratio: float = 0.1
    exploration_ratio: float = 0.2
    exploitation_ratio: float = 0.7
    diversity_metric: str = "edit_distance"  # Options: "edit_distance", "feature_based"

    # If true, sampling from island picks the best-fitness parent deterministically
    island_pick_best_parent: bool = False

    # Feature map dimensions for MAP-Elites
    # Default to complexity and diversity for better exploration
    # CRITICAL: For custom dimensions, evaluators must return RAW VALUES, not bin indices
    # Built-in: "complexity", "diversity", "score" (always available)
    # Custom: Any metric from your evaluator (must be continuous values)
    feature_dimensions: List[str] = field(
        default_factory=lambda: ["complexity", "diversity"],
        metadata={
            "help": "List of feature dimensions for MAP-Elites grid. "
            "Built-in dimensions: 'complexity', 'diversity', 'score'. "
            "Custom dimensions: Must match metric names from evaluator. "
            "IMPORTANT: Evaluators must return raw continuous values for custom dimensions, "
            "NOT pre-computed bin indices. OpenEvolve handles all scaling and binning internally."
        },
    )
    feature_bins: Union[int, Dict[str, int]] = (
        10  # Can be int (all dims) or dict (per-dim)
    )
    diversity_reference_size: int = (
        20  # Size of reference set for diversity calculation
    )

    # Migration parameters for island-based evolution
    migration_interval: int = 50  # Migrate every N generations
    migration_rate: float = 0.1  # Fraction of population to migrate

    # Random seed for reproducible sampling
    random_seed: Optional[int] = 42

    # Artifact storage
    artifacts_base_path: Optional[str] = None  # Defaults to db_path/artifacts
    artifact_size_threshold: int = 32 * 1024  # 32KB threshold
    cleanup_old_artifacts: bool = True
    artifact_retention_days: int = 30


@dataclass
class EvaluatorConfig:
    """Configuration for program evaluation"""

    # General settings
    timeout: int = 300  # Maximum evaluation time in seconds
    max_retries: int = 3

    # Resource limits for evaluation
    memory_limit_mb: Optional[int] = None
    cpu_limit: Optional[float] = None

    # Evaluation strategies
    cascade_evaluation: bool = True
    cascade_thresholds: List[float] = field(default_factory=lambda: [0.5, 0.75, 0.9])

    # Parallel evaluation
    parallel_evaluations: int = 1
    distributed: bool = False

    # LLM-based feedback
    use_llm_feedback: bool = False
    llm_feedback_weight: float = 0.1

    # Artifact handling
    enable_artifacts: bool = True
    max_artifact_storage: int = 100 * 1024 * 1024  # 100MB per program


@dataclass
class EvolutionTraceConfig:
    """Configuration for evolution trace logging"""

    enabled: bool = False
    format: str = "jsonl"  # Options: "jsonl", "json", "hdf5"
    include_code: bool = False
    include_prompts: bool = True
    output_path: Optional[str] = None
    buffer_size: int = 10
    compress: bool = False


@dataclass
class Config:
    """Master configuration for OpenEvolve"""

    # General settings
    max_iterations: int = 10000
    checkpoint_interval: int = 100
    log_level: str = "INFO"
    log_dir: Optional[str] = None
    random_seed: Optional[int] = 42
    language: str = None

    # Component configurations
    llm: LLMConfig = field(default_factory=LLMConfig)
    prompt: PromptConfig = field(default_factory=PromptConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    evaluator: EvaluatorConfig = field(default_factory=EvaluatorConfig)
    evolution_trace: EvolutionTraceConfig = field(default_factory=EvolutionTraceConfig)
    explanation: ExplanationConfig = field(default_factory=ExplanationConfig)
    experience_kb: ExperienceKBConfig = field(default_factory=ExperienceKBConfig)

    # Evolution settings
    diff_based_evolution: bool = True
    max_code_length: int = 10000
    # Control whether to extract/use explanation from LLM outputs.
    use_explanation: Optional[bool] = False

    # Early stopping settings
    early_stopping_patience: Optional[int] = None
    convergence_threshold: float = 0.001
    early_stopping_metric: str = "combined_score"

    @classmethod
    def from_yaml(cls, path: Union[str, Path]) -> "Config":
        """Load configuration from a YAML file"""
        with open(path, "r") as f:
            config_dict = yaml.safe_load(f)
        return cls.from_dict(config_dict)

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Config":
        """Create configuration from a dictionary"""
        # Handle nested configurations
        config = Config()

        # Update top-level fields
        for key, value in config_dict.items():
            if key not in [
                "llm",
                "prompt",
                "database",
                "evaluator",
                "evolution_trace",
                "explanation",
                "experience_kb",
            ] and hasattr(config, key):
                setattr(config, key, value)

        # Update nested configs
        if "llm" in config_dict:
            llm_dict = config_dict["llm"]
            if "models" in llm_dict:
                llm_dict["models"] = [LLMModelConfig(**m) for m in llm_dict["models"]]
            if "evaluator_models" in llm_dict:
                llm_dict["evaluator_models"] = [
                    LLMModelConfig(**m) for m in llm_dict["evaluator_models"]
                ]
            config.llm = LLMConfig(**llm_dict)
        if "prompt" in config_dict:
            config.prompt = PromptConfig(**config_dict["prompt"])
        if "database" in config_dict:
            config.database = DatabaseConfig(**config_dict["database"])

        # Ensure database inherits the random seed if not explicitly set
        if config.database.random_seed is None and config.random_seed is not None:
            config.database.random_seed = config.random_seed
        if "evaluator" in config_dict:
            config.evaluator = EvaluatorConfig(**config_dict["evaluator"])
        if "evolution_trace" in config_dict:
            config.evolution_trace = EvolutionTraceConfig(
                **config_dict["evolution_trace"]
            )
        if "explanation" in config_dict:
            exp_dict = (
                config_dict["explanation"]
                if isinstance(config_dict["explanation"], dict)
                else {}
            )
            # Rebuild nested LLM config for explanation if provided
            if (
                isinstance(exp_dict, dict)
                and "llm" in exp_dict
                and isinstance(exp_dict["llm"], dict)
            ):
                exp_llm_dict = dict(exp_dict["llm"])  # shallow copy
                if "models" in exp_llm_dict:
                    exp_llm_dict["models"] = [
                        LLMModelConfig(**m) for m in exp_llm_dict["models"]
                    ]
                if "evaluator_models" in exp_llm_dict:
                    exp_llm_dict["evaluator_models"] = [
                        LLMModelConfig(**m) for m in exp_llm_dict["evaluator_models"]
                    ]
                exp_dict["llm"] = LLMConfig(**exp_llm_dict)
            config.explanation = ExplanationConfig(**exp_dict)

        # Experience KB config
        if "experience_kb" in config_dict:
            kb_dict = (
                config_dict["experience_kb"]
                if isinstance(config_dict["experience_kb"], dict)
                else {}
            )
            if (
                isinstance(kb_dict, dict)
                and "llm" in kb_dict
                and isinstance(kb_dict["llm"], dict)
            ):
                kb_llm_dict = dict(kb_dict["llm"])  # shallow copy
                if "models" in kb_llm_dict:
                    kb_llm_dict["models"] = [
                        LLMModelConfig(**m) for m in kb_llm_dict["models"]
                    ]
                if "evaluator_models" in kb_llm_dict:
                    kb_llm_dict["evaluator_models"] = [
                        LLMModelConfig(**m) for m in kb_llm_dict["evaluator_models"]
                    ]
                kb_dict["llm"] = LLMConfig(**kb_llm_dict)
            config.experience_kb = ExperienceKBConfig(**kb_dict)

        # Backward compatibility: reflect use_explanation flag into explanation.enabled
        if getattr(config, "use_explanation", None) is not None:
            config.explanation.enabled = bool(config.use_explanation)

        return config

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary suitable for process workers and YAML"""
        return {
            # General settings
            "max_iterations": self.max_iterations,
            "checkpoint_interval": self.checkpoint_interval,
            "log_level": self.log_level,
            "log_dir": self.log_dir,
            "random_seed": self.random_seed,
            "language": self.language,
            # Component configurations (use full dataclass serialization for nested configs)
            "llm": {
                "models": [asdict(m) for m in self.llm.models],
                "evaluator_models": [asdict(m) for m in self.llm.evaluator_models],
                "api_base": self.llm.api_base,
                "api_key": self.llm.api_key,
                "temperature": self.llm.temperature,
                "top_p": self.llm.top_p,
                "max_tokens": self.llm.max_tokens,
                "timeout": self.llm.timeout,
                "retries": self.llm.retries,
                "retry_delay": self.llm.retry_delay,
                "reasoning_effort": getattr(self.llm, "reasoning_effort", None),
                "enable_thinking": getattr(self.llm, "enable_thinking", None),
            },
            "prompt": asdict(self.prompt),
            "database": asdict(self.database),
            "evaluator": asdict(self.evaluator),
            "evolution_trace": {
                "enabled": self.evolution_trace.enabled,
                "format": self.evolution_trace.format,
                "include_code": self.evolution_trace.include_code,
                "include_prompts": self.evolution_trace.include_prompts,
                "output_path": self.evolution_trace.output_path,
                "buffer_size": self.evolution_trace.buffer_size,
                "compress": self.evolution_trace.compress,
            },
            "explanation": {
                "enabled": self.explanation.enabled,
                "template_key": self.explanation.template_key,
                "system_message_key": self.explanation.system_message_key,
                "include_code": self.explanation.include_code,
                "max_artifacts_bytes": self.explanation.max_artifacts_bytes,
                "ensemble_role": self.explanation.ensemble_role,
                # Include dedicated LLM config for explanation, if present
                "llm": (
                    {
                        "models": [
                            asdict(m)
                            for m in getattr(self.explanation.llm, "models", [])
                        ],
                        "evaluator_models": [
                            asdict(m)
                            for m in getattr(
                                self.explanation.llm, "evaluator_models", []
                            )
                        ],
                        "api_base": getattr(self.explanation.llm, "api_base", None),
                        "api_key": getattr(self.explanation.llm, "api_key", None),
                        "temperature": getattr(
                            self.explanation.llm, "temperature", None
                        ),
                        "top_p": getattr(self.explanation.llm, "top_p", None),
                        "max_tokens": getattr(self.explanation.llm, "max_tokens", None),
                        "timeout": getattr(self.explanation.llm, "timeout", None),
                        "retries": getattr(self.explanation.llm, "retries", None),
                        "retry_delay": getattr(
                            self.explanation.llm, "retry_delay", None
                        ),
                        "reasoning_effort": getattr(
                            self.explanation.llm, "reasoning_effort", None
                        ),
                        "enable_thinking": getattr(
                            self.explanation.llm, "enable_thinking", None
                        ),
                    }
                    if getattr(self.explanation, "llm", None) is not None
                    else None
                ),
            },
            "experience_kb": {
                "enabled": self.experience_kb.enabled,
                "include_in_prompt": self.experience_kb.include_in_prompt,
                "section_template_key": self.experience_kb.section_template_key,
                "update_template_key": self.experience_kb.update_template_key,
                "update_system_message_key": self.experience_kb.update_system_message_key,
                "critical_agent_template_key": getattr(
                    self.experience_kb, "critical_agent_template_key", "critical_agent"
                ),
                "critical_agent_system_message_key": getattr(
                    self.experience_kb,
                    "critical_agent_system_message_key",
                    "critical_agent_system_message",
                ),
                "initial_markdown_template_path": self.experience_kb.initial_markdown_template_path,
                "storage_dir": self.experience_kb.storage_dir,
                "max_kb_bytes": self.experience_kb.max_kb_bytes,
                "summary_mode": getattr(self.experience_kb, "summary_mode", "full"),
                "random_rules_max_k": getattr(
                    self.experience_kb, "random_rules_max_k", 5
                ),
                "min_improvement": self.experience_kb.min_improvement,
                "record_failures": self.experience_kb.record_failures,
                "max_update_attempts": getattr(
                    self.experience_kb, "max_update_attempts", 3
                ),
                "require_all_matches": getattr(
                    self.experience_kb, "require_all_matches", False
                ),
                "llm": (
                    {
                        "models": [
                            asdict(m)
                            for m in getattr(self.experience_kb.llm, "models", [])
                        ],
                        "evaluator_models": [
                            asdict(m)
                            for m in getattr(
                                self.experience_kb.llm, "evaluator_models", []
                            )
                        ],
                        "api_base": getattr(self.experience_kb.llm, "api_base", None),
                        "api_key": getattr(self.experience_kb.llm, "api_key", None),
                        "temperature": getattr(
                            self.experience_kb.llm, "temperature", None
                        ),
                        "top_p": getattr(self.experience_kb.llm, "top_p", None),
                        "max_tokens": getattr(
                            self.experience_kb.llm, "max_tokens", None
                        ),
                        "timeout": getattr(self.experience_kb.llm, "timeout", None),
                        "retries": getattr(self.experience_kb.llm, "retries", None),
                        "retry_delay": getattr(
                            self.experience_kb.llm, "retry_delay", None
                        ),
                        "reasoning_effort": getattr(
                            self.experience_kb.llm, "reasoning_effort", None
                        ),
                        "enable_thinking": getattr(
                            self.experience_kb.llm, "enable_thinking", None
                        ),
                    }
                    if getattr(self.experience_kb, "llm", None) is not None
                    else None
                ),
            },
            # Evolution settings
            "diff_based_evolution": self.diff_based_evolution,
            "max_code_length": self.max_code_length,
            # Custom flags
            "use_explanation": self.use_explanation,
            # Early stopping settings
            "early_stopping_patience": self.early_stopping_patience,
            "convergence_threshold": self.convergence_threshold,
            "early_stopping_metric": self.early_stopping_metric,
        }

    def to_yaml(self, path: Union[str, Path]) -> None:
        """Save configuration to a YAML file"""
        with open(path, "w") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)


def load_config(config_path: Optional[Union[str, Path]] = None) -> Config:
    """Load configuration from a YAML file or use defaults"""
    if config_path and os.path.exists(config_path):
        config = Config.from_yaml(config_path)
    else:
        config = Config()

        # Use environment variables if available
        api_key = os.environ.get("OPENAI_API_KEY")
        api_base = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")

        config.llm.update_model_params({"api_key": api_key, "api_base": api_base})

    # Ensure we have at least one model when loading from YAML configs that may omit LLM block
    # This preserves tests that expect loaded configs to include at least one model
    if config_path and os.path.exists(config_path) and not config.llm.models:
        from .config import LLMModelConfig  # local import to avoid circular
        # Choose a sensible default name; allow environment override via PRIMARY_MODEL
        default_name = os.environ.get("OPENEVOLVE_DEFAULT_MODEL", "gpt-oss-120b")
        config.llm.models.append(LLMModelConfig(name=default_name, weight=1.0))
        if not config.llm.evaluator_models:
            config.llm.evaluator_models = config.llm.models.copy()

    # Make the system message available to the individual models, in case it is not provided from the prompt sampler
    # Note: Set system_message for all models' configs(LLMModelConfig) in config.llm
    # which contains system_message key
    config.llm.update_model_params({"system_message": config.prompt.system_message})

    return config
