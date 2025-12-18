exp_roots=(
    "/data/CodeEfficiency/openevolve/examples/archive/Qwen3-32B@30-RepEval-baseline"
    "/data/CodeEfficiency/openevolve/examples/archive/Qwen3-32B@30-RepEval-baseline+KB+randomrules")

task="aizu_3612_roller-coaster"
metric="trimmed_mean_runtime"

labels=(
    "Qwen3-32B-Baseline"
    "Qwen3-32B-Baseline+KB+RandomRules"
)

python scripts/plot_task_latest_checkpoint.py \
    --exp-roots "${exp_roots[@]}" \
    --task "${task}" \
    --metric "${metric}" \
    --labels "${labels[@]}" \
    --output "${task}_latest_checkpoint.png" \
    --title "${task} Latest Checkpoint (${metric})"
