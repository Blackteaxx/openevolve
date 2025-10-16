python scripts/plot_best_evolution.py \
    --dirs "/data/CodeEfficiency/openevolve/examples/archive/effibench_code_optimization_Qwen3-32B-Pass-Threshold-Enhanced-NoRepEval-1/codechef_STKSTR_streak-star/openevolve_output/checkpoints/checkpoint_100/programs" "/data/CodeEfficiency/openevolve/examples/archive/effibench_code_optimization_Qwen3-32B-Pass-Threshold-EnhancedExplanation-NoRepEval/codechef_STKSTR_streak-star/openevolve_output/checkpoints/checkpoint_100/programs" "/data/CodeEfficiency/openevolve/examples/archive/effibench_code_optimization_Qwen3-32B-Pass-Threshold-Enhanced-NoRepEval/codechef_STKSTR_streak-star/openevolve_output/checkpoints/checkpoint_100/programs" \
    --labels "Qwen3-32B-NoRepEval-1 STKSTR" "Qwen3-32B-Explanation-NoRepEval STKSTR" "Qwen3-32B-NoRepEval STKSTR" \
    --metric combined_score \
    --output multi_best_evolution.png \
    --title "Best Program Evolution (combined_score)"