#!/usr/bin/env python3
"""Generate convergence plots from Omega3P FE order sweep results."""

import sys
import os
import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def parse_omega3p_output(outfile):
    """Extract frequencies, Q-factors, and DOFs from Omega3P output."""
    freqs = []
    qfactors = []
    dofs = None

    with open(outfile) as f:
        for line in f:
            m = re.search(r'Frequency\s*:\s*([\d.eE+\-]+)', line)
            if m and 'Shift' not in line:
                freqs.append(float(m.group(1)))
            m = re.search(r'QualityFactor\s*:\s*([\d.eE+\-]+)', line)
            if m:
                qfactors.append(float(m.group(1)))
            m = re.search(r'Total Number of DOFs:\s*(\d+)', line)
            if m:
                dofs = int(m.group(1))

    return freqs, qfactors, dofs


def main():
    if len(sys.argv) < 3:
        print("Usage: plot_convergence.py <workspace_dir> <output_dir>")
        print("  workspace_dir: directory containing FE_ORDER.*/solve_*.out files")
        print("  output_dir: where to save PNG plots")
        sys.exit(1)

    workspace = sys.argv[1]
    output_dir = sys.argv[2]
    os.makedirs(output_dir, exist_ok=True)

    orders = []
    mode1_freqs = []
    mode2_freqs = []
    dofs_list = []
    q_factors = []

    for entry in sorted(os.listdir(workspace)):
        if not entry.startswith('FE_ORDER.'):
            continue
        order = int(entry.split('.')[1])
        step_dir = os.path.join(workspace, entry)

        outfiles = [f for f in os.listdir(step_dir) if f.endswith('.out')]
        if not outfiles:
            continue

        outfile = os.path.join(step_dir, outfiles[0])
        freqs, qf, dofs = parse_omega3p_output(outfile)

        if len(freqs) >= 1:
            orders.append(order)
            mode1_freqs.append(freqs[0] / 1e9)
            if len(freqs) >= 2:
                mode2_freqs.append(freqs[1] / 1e9)
            dofs_list.append(dofs or 0)
            if qf:
                q_factors.append(qf[0])

    if not orders:
        print("ERROR: No results found in", workspace)
        sys.exit(1)

    reference = 1.3138129364

    # Plot 1: Convergence
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5))

    ax1.plot(orders, mode1_freqs, 'bo-', markersize=8, linewidth=2, label='Mode 1 (TM$_{010}$)')
    if mode2_freqs:
        ax1.plot(orders, mode2_freqs, 'gs-', markersize=7, linewidth=2, label='Mode 2')
    ax1.axhline(y=reference, color='r', linestyle='--', linewidth=1.5,
                label=f'Reference ({reference:.4f} GHz)')
    ax1.set_xlabel('Finite Element Order', fontsize=12)
    ax1.set_ylabel('Eigenfrequency (GHz)', fontsize=12)
    ax1.set_title('FE Order Convergence — Omega3P on S3DF', fontsize=11)
    ax1.set_xticks(orders)
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3)

    errors = [abs(f - reference) / reference * 100 for f in mode1_freqs]
    ax2.semilogy(orders, errors, 'rs-', markersize=8, linewidth=2)
    ax2.set_xlabel('Finite Element Order', fontsize=12)
    ax2.set_ylabel('Relative Error (%)', fontsize=12)
    ax2.set_title('Convergence Rate', fontsize=11)
    ax2.set_xticks(orders)
    ax2.grid(True, alpha=0.3)

    for order, dof, err in zip(orders, dofs_list, errors):
        if dof:
            ax2.annotate(f'{dof:,} DOFs', (order, err),
                         textcoords="offset points", xytext=(10, 5),
                         fontsize=9, color='gray')

    plt.tight_layout()
    outpath = os.path.join(output_dir, 'convergence.png')
    plt.savefig(outpath, dpi=150, bbox_inches='tight')
    print(f"Saved: {outpath}")

    # Plot 2: DOFs vs Error (cost-accuracy tradeoff)
    if dofs_list:
        fig2, ax3 = plt.subplots(figsize=(6, 4))
        ax3.loglog(dofs_list, errors, 'bo-', markersize=8, linewidth=2)
        for order, dof, err in zip(orders, dofs_list, errors):
            ax3.annotate(f'p={order}', (dof, err),
                         textcoords="offset points", xytext=(5, 5), fontsize=10)
        ax3.set_xlabel('Degrees of Freedom', fontsize=12)
        ax3.set_ylabel('Relative Error (%)', fontsize=12)
        ax3.set_title('Cost-Accuracy Tradeoff', fontsize=11)
        ax3.grid(True, alpha=0.3)
        plt.tight_layout()
        outpath2 = os.path.join(output_dir, 'cost_accuracy.png')
        plt.savefig(outpath2, dpi=150, bbox_inches='tight')
        print(f"Saved: {outpath2}")

    # Summary text
    summary_path = os.path.join(output_dir, 'summary.txt')
    with open(summary_path, 'w') as f:
        f.write("=== FE Order Convergence Summary ===\n\n")
        f.write(f"{'Order':<8}{'Freq (GHz)':<18}{'Error (%)':<14}{'DOFs':<12}\n")
        f.write("-" * 50 + "\n")
        for order, freq, err, dof in zip(orders, mode1_freqs, errors, dofs_list):
            f.write(f"{order:<8}{freq:<18.10f}{err:<14.6f}{dof:<12,}\n")
        f.write(f"\nReference: {reference} GHz\n")
    print(f"Saved: {summary_path}")


if __name__ == '__main__':
    main()
