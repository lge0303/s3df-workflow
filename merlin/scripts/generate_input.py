#!/usr/bin/env python3
"""
Generate an Omega3P input file from a template with given parameters.
Substitutes placeholders in the template with actual parameter values.
"""

import argparse
from pathlib import Path


def generate_input(
    cavity_radius: float,
    iris_radius: float,
    fe_order: int,
    freq_shift: float,
    template_path: str,
    output_path: str,
):
    """Generate .omega3p input file from template."""
    template = Path(template_path).read_text()

    content = template.replace("@FE_ORDER@", str(int(fe_order)))
    content = content.replace("@FREQ_SHIFT@", f"{freq_shift:.6e}")

    # If template has geometry placeholders
    content = content.replace("@CAVITY_RADIUS@", f"{cavity_radius:.6f}")
    content = content.replace("@IRIS_RADIUS@", f"{iris_radius:.6f}")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(content)
    print(f"Generated: {output_path}")
    print(f"  FE_ORDER={int(fe_order)}, FREQ_SHIFT={freq_shift:.2e}")


def main():
    parser = argparse.ArgumentParser(description="Generate ACE3P input from template")
    parser.add_argument("--cavity-radius", type=float, required=True)
    parser.add_argument("--iris-radius", type=float, required=True)
    parser.add_argument("--fe-order", type=float, required=True)
    parser.add_argument("--freq-shift", type=float, required=True)
    parser.add_argument("--template", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    args = parser.parse_args()

    generate_input(
        cavity_radius=args.cavity_radius,
        iris_radius=args.iris_radius,
        fe_order=args.fe_order,
        freq_shift=args.freq_shift,
        template_path=args.template,
        output_path=args.output,
    )


if __name__ == "__main__":
    main()
