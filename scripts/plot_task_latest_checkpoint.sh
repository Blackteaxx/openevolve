exp_roots=(
    "/data/CodeEfficiency/openevolve/examples/archive/effibench_code_optimization_Qwen3-32B-Pass-Threshold-Enhanced-NoRepEval-2"
    "/data/CodeEfficiency/openevolve/examples/archive/effibench_code_optimization_Qwen3-32B-Pass-Threshold-Enhanced-NoRepEval-2-2"
    "/data/CodeEfficiency/openevolve/examples/archive/effibench_code_optimization_Qwen3-32B-Pass-Threshold-EnhancedExplanation-NoRepEval-2"
    "/data/CodeEfficiency/openevolve/examples/archive/effibench_code_optimization_Qwen3-32B-Pass-Threshold-EnhancedExplanation-NoRepEval-2-2"
    "/data/CodeEfficiency/openevolve/examples/archive/effibench_code_optimization_Qwen3-32B-Pass-Threshold-EnhancedExplanation-KB-NoRepEval-2"
    "/data/CodeEfficiency/openevolve/examples/archive/effibench_code_optimization_Qwen3-32B-Pass-Threshold-KB-NoRepEval-2"
    "/data/CodeEfficiency/openevolve/examples/archive/effibench_code_optimization_Qwen3-32B-Pass-Threshold-KB-NoRepEval-3"
)

task="atcoder_abc390c_paint-to-make-a-rectangle"
metric="trimmed_mean_runtime"

labels=(
    "Qwen3-32B-NoRepEval-2"
    "Qwen3-32B-NoRepEval-2-2"
    "Qwen3-32B-Explanation-NoRepEval-2"
    "Qwen3-32B-Explanation-NoRepEval-2-2"
    "Qwen3-32B-Explanation-KB-NoRepEval-2"
    "Qwen3-32B-KB-NoRepEval-2"
    "Qwen3-32B-KB-NoRepEval-3"
)

python scripts/plot_task_latest_checkpoint.py \
    --exp-roots "${exp_roots[@]}" \
    --task "${task}" \
    --metric "${metric}" \
    --labels "${labels[@]}" \
    --output "${task}_latest_checkpoint.png" \
    --title "${task} Latest Checkpoint (${metric})"
