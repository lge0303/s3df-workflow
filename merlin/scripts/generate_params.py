#!/usr/bin/env python3
"""
Generate parameter samples for ACE3P sweep using Latin Hypercube Sampling.

Produces an .npy file with columns: cavity_radius, iris_radius, fe_order, freq_shift
"""

import argparse
import numpy as np
from pathlib import Path


def latin_hypercube(n_samples: int, n_dims: int, seed: int = 42) -> np.ndarray:
    """Generate Latin Hypercube samples in [0, 1]^n_dims."""
    rng = np.random.default_rng(seed)
    samples = np.zeros((n_samples, n_dims))
    for dim in range(n_dims):
        perm = rng.permutation(n_samples)
        samples[:, dim] = (perm + rng.uniform(size=n_samples)) / n_samples
    return samples


def scale_parameters(unit_samples: np.ndarray) -> np.ndarray:
    """Scale [0,1] samples to physical parameter ranges."""
    bounds = {
        "cavity_radius": (0.080, 0.120),   # meters
        "iris_radius": (0.025, 0.045),      # meters
        "fe_order": (1, 3),                 # integer (rounded)
        "freq_shift": (0.8e9, 3.5e9),      # Hz
    }

    scaled = np.zeros_like(unit_samples)
    for i, (lo, hi) in enumerate(bounds.values()):
        scaled[:, i] = lo + unit_samples[:, i] * (hi - lo)

    # Round fe_order to integer
    scaled[:, 2] = np.round(scaled[:, 2]).astype(int)

    return scaled


def main():
    parser = argparse.ArgumentParser(description="Generate LHS parameter samples")
    parser.add_argument("--n", type=int, default=100, help="Number of samples")
    parser.add_argument("--method", choices=["lhs", "random", "grid"], default="lhs")
    parser.add_argument("--output", type=str, required=True, help="Output .npy file")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    if args.method == "lhs":
        unit_samples = latin_hypercube(args.n, 4, seed=args.seed)
    elif args.method == "random":
        rng = np.random.default_rng(args.seed)
        unit_samples = rng.uniform(size=(args.n, 4))
    elif args.method == "grid":
        n_per_dim = int(np.ceil(args.n ** 0.25))
        axes = [np.linspace(0, 1, n_per_dim) for _ in range(4)]
        grid = np.array(np.meshgrid(*axes)).T.reshape(-1, 4)
        unit_samples = grid[:args.n]

    scaled = scale_parameters(unit_samples)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(output_path, scaled)

    print(f"Generated {len(scaled)} parameter samples → {output_path}")
    print(f"  cavity_radius: [{scaled[:,0].min():.4f}, {scaled[:,0].max():.4f}] m")
    print(f"  iris_radius:   [{scaled[:,1].min():.4f}, {scaled[:,1].max():.4f}] m")
    print(f"  fe_order:      [{scaled[:,2].min():.0f}, {scaled[:,2].max():.0f}]")
    print(f"  freq_shift:    [{scaled[:,3].min():.2e}, {scaled[:,3].max():.2e}] Hz")


if __name__ == "__main__":
    main()
