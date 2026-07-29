#!/usr/bin/env python3
"""Generate multipacting analysis plots from Track3P results."""

import sys
import os
import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def parse_resonant_particles(filepath):
    """Parse Track3P resonantparticles output file."""
    field_levels = []
    energies = []

    with open(filepath) as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 6 and parts[0] != 'Field_Level':
                try:
                    fl = float(parts[0])
                    energy = float(parts[5])
                    field_levels.append(fl / 1e6)  # Convert to MV/m
                    energies.append(energy)
                except ValueError:
                    continue

    return field_levels, energies


def parse_enhancement_counter(filepath):
    """Parse Track3P enhancementCounter output file."""
    field_levels = []
    enhancements = []

    with open(filepath) as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 4 and parts[0] != 'fieldlevel':
                try:
                    fl = float(parts[0])
                    ec = float(parts[2])
                    field_levels.append(fl / 1e6)
                    enhancements.append(ec)
                except ValueError:
                    continue

    return field_levels, enhancements


def main():
    if len(sys.argv) < 3:
        print("Usage: plot_multipacting.py <track3p_results_dir> <output_dir>")
        print("  track3p_results_dir: directory containing OUTPUT/resonantparticles")
        print("  output_dir: where to save PNG plots")
        sys.exit(1)

    results_dir = sys.argv[1]
    output_dir = sys.argv[2]
    os.makedirs(output_dir, exist_ok=True)

    # Look for results in track3p_results/OUTPUT/
    output_subdir = os.path.join(results_dir, 'track3p_results', 'OUTPUT')
    if not os.path.isdir(output_subdir):
        output_subdir = os.path.join(results_dir, 'OUTPUT')
    if not os.path.isdir(output_subdir):
        print(f"ERROR: No OUTPUT directory found in {results_dir}")
        sys.exit(1)

    # Plot 1: Resonant particles impact energy vs field level
    res_file = os.path.join(output_subdir, 'resonantparticles')
    if os.path.exists(res_file):
        field_levels, energies = parse_resonant_particles(res_file)

        if field_levels:
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.scatter(field_levels, energies, c='red', s=15, alpha=0.6, edgecolors='none')
            ax.set_xlabel('Field Level (MV/m)', fontsize=12)
            ax.set_ylabel('Impact Energy (eV)', fontsize=12)
            ax.set_title('Multipacting Map — Impact Energy vs. Field Level\n(Track3P, CW23 Pillbox on S3DF)', fontsize=11)
            ax.grid(True, alpha=0.3)

            unique_levels = sorted(set(field_levels))
            counts = [field_levels.count(fl) for fl in unique_levels]
            ax2 = ax.twinx()
            ax2.bar(unique_levels, counts, width=0.3, alpha=0.2, color='blue', label='Particle count')
            ax2.set_ylabel('Resonant Particle Count', fontsize=10, color='blue')
            ax2.tick_params(axis='y', labelcolor='blue')

            plt.tight_layout()
            outpath = os.path.join(output_dir, 'multipacting_map.png')
            plt.savefig(outpath, dpi=150, bbox_inches='tight')
            print(f"Saved: {outpath}")
            plt.close()

    # Plot 2: Enhancement counter vs field level
    ec_file = os.path.join(output_subdir, 'enhancementCounter')
    if os.path.exists(ec_file):
        field_levels, enhancements = parse_enhancement_counter(ec_file)

        if field_levels:
            fig, ax = plt.subplots(figsize=(7, 4.5))

            unique_levels = sorted(set(field_levels))
            max_ec = [max(e for f, e in zip(field_levels, enhancements) if f == fl)
                      for fl in unique_levels]

            ax.bar(unique_levels, max_ec, width=0.3, color='#2196F3', edgecolor='black', alpha=0.8)
            ax.axhline(y=1.0, color='red', linestyle='--', linewidth=1.5, label='EC = 1 (threshold)')
            ax.set_xlabel('Field Level (MV/m)', fontsize=12)
            ax.set_ylabel('Max Enhancement Counter', fontsize=12)
            ax.set_title('Enhancement Counter vs. Field Level\n(Multipacting Susceptibility)', fontsize=11)
            ax.legend(fontsize=10)
            ax.grid(True, alpha=0.3, axis='y')

            plt.tight_layout()
            outpath = os.path.join(output_dir, 'enhancement_counter.png')
            plt.savefig(outpath, dpi=150, bbox_inches='tight')
            print(f"Saved: {outpath}")
            plt.close()

    # Summary
    summary_path = os.path.join(output_dir, 'summary.txt')
    with open(summary_path, 'w') as f:
        f.write("=== Track3P Multipacting Analysis Summary ===\n\n")
        if os.path.exists(res_file):
            field_levels, energies = parse_resonant_particles(res_file)
            unique_levels = sorted(set(field_levels))
            f.write(f"Field levels scanned: {len(unique_levels)}\n")
            for fl in unique_levels:
                count = field_levels.count(fl)
                f.write(f"  {fl:.1f} MV/m: {count} resonant particles\n")
            f.write(f"\nTotal resonant particles: {len(field_levels)}\n")
            if energies:
                f.write(f"Energy range: {min(energies):.1f} - {max(energies):.1f} eV\n")
        if os.path.exists(ec_file):
            field_levels_ec, enhancements = parse_enhancement_counter(ec_file)
            f.write(f"\nEnhancement counter max: {max(enhancements):.4f}\n")
            if max(enhancements) > 1.0:
                f.write("WARNING: EC > 1 detected — multipacting is sustained!\n")
            else:
                f.write("EC < 1 at all levels — multipacting decays\n")
    print(f"Saved: {summary_path}")


if __name__ == '__main__':
    main()
