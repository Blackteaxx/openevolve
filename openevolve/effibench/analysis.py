import numpy as np
import scipy.stats as st
from typing import List, Dict

def analyze_runtimes(samples: List[float], confidence: float = 0.95, trim_ratio: float = 0.05) -> Dict[str, float]:
    """
    Analyzes a list of runtimes to provide robust statistical measures.

    This function calculates various statistical measures including mean, standard deviation,
    min, max, max difference, 95% confidence interval for the mean, and a trimmed mean.
    The trimmed mean removes a specified ratio of the smallest and largest values before
    calculating the mean, making it robust to outliers.

    Args:
        samples: A list of floats representing the runtimes of multiple executions.
        confidence: The confidence level for the confidence interval (e.g., 0.95 for 95%).
        trim_ratio: The fraction of observations to be trimmed from each end of the
                    sorted list of runtimes before the trimmed mean is computed. The value
                    should be between 0 and 0.5.

    Returns:
        A dictionary containing various statistical measures of the runtimes.
        Returns default values if the list is empty or contains insufficient data after trimming.
    """
    if not samples:
        return {
            "n": 0,
            "mean": float('inf'),
            "std": float('inf'),
            "min": float('inf'),
            "max": float('inf'),
            "max_diff": float('inf'),
            "95%_CI": (float('inf'), float('inf')),
            "trimmed_mean": float('inf'),
        }

    samples_np = np.array(samples)

    mean = samples_np.mean()
    std = samples_np.std(ddof=1) if len(samples_np) > 1 else 0.0
    min_val = samples_np.min()
    max_val = samples_np.max()
    max_diff = max_val - min_val

    # Confidence Interval
    ci_low, ci_high = float('inf'), float('inf')
    if len(samples_np) > 1:
        ci_low, ci_high = st.t.interval(
            confidence, df=len(samples_np) - 1, loc=mean, scale=st.sem(samples_np)
        )

    # Trimmed mean 
    sorted_samples = np.sort(samples_np)
    n = len(samples_np)
    k = int(n * trim_ratio)

    trimmed = sorted_samples[k : n - k] if k > 0 and (n - 2 * k) > 0 else sorted_samples
    trimmed_mean = trimmed.mean() if len(trimmed) > 0 else float('inf')

    return {
        "n": len(samples_np),
        "mean": mean,
        "std": std,
        "min": min_val,
        "max": max_val,
        "max_diff": max_diff,
        "95%_CI": (ci_low, ci_high),
        "trimmed_mean": trimmed_mean,
    }