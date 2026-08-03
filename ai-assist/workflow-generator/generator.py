#!/usr/bin/env python3
"""
AI-assisted workflow generator for ACE3P on S3DF.

Takes a natural language description of a simulation campaign
and generates a valid Maestro or Merlin YAML workflow spec.
"""

import argparse
import sys
from pathlib import Path

from anthropic import Anthropic

SYSTEM_PROMPT = """You are an expert in HPC workflow automation for the ACE3P electromagnetic simulation suite on SLAC's S3DF computing environment.

Your job is to generate valid Maestro or Merlin YAML workflow specifications from natural language descriptions.

## ACE3P Context

ACE3P solvers:
- omega3p: eigenmode solver (frequency, Q-factor, R/Q)
- s3p: S-parameter solver (frequency domain, multi-port)
- track3p: particle tracking (multipacting, dark current)
- t3p: time-domain wakefield solver
- tem3p: coupled thermal-structural solver
- acdtool: utility (meshconvert, postprocess rf)

Binary location: /sdf/group/rfar/lge/sdf/ace3p/build/bin/
Slurm account: rfar

## Typical ACE3P Pipeline

1. Mesh conversion: acdtool meshconvert file.gen → file.ncdf
2. Solver execution: omega3p/track3p/etc. with input file
3. Post-processing: acdtool postprocess rf file.rfpost

## Maestro YAML Structure

```yaml
description:
  name: workflow-name
  description: What it does

env:
  variables:
    KEY: value

batch:
  type: slurm
  host: s3df
  bank: rfar

global.parameters:  # For sweeps
  PARAM_NAME:
    values: [val1, val2, val3]
    label: PARAM_NAME.%%

study:
  - name: step-name
    description: What this step does
    run:
      cmd: |
        shell commands here
      depends: [previous-step]  # DAG dependencies
      nodes: 1
      procs: 128
      walltime: "00:30:00"
```

## Merlin Extensions (for large-scale/distributed)

Add these blocks for Merlin workflows:
- merlin.resources.workers: worker pool configuration
- merlin.samples: programmatic parameter generation
- task_queue: assign steps to worker pools
- retry_delay / max_retries: fault tolerance

## Rules

1. Always use valid YAML syntax
2. Quote walltime values (contains colons)
3. Use $(VARIABLE) for Maestro token substitution
4. Use depends: [step_*] for fan-in (wait for all expanded instances)
5. Set realistic walltime and resource estimates for ACE3P
6. Include error handling comments where appropriate
7. Output ONLY the YAML content, no explanations before or after
"""

EXAMPLES = """
## Example 1

User: "Run Omega3P for 3 different mesh densities and compare frequencies"

Output:
```yaml
description:
  name: omega3p-mesh-convergence
  description: Mesh convergence study comparing eigenfrequencies across 3 mesh densities

env:
  variables:
    ACE3P_BIN: /sdf/group/rfar/lge/sdf/ace3p/build/bin
    INPUT_FILE: cavity.omega3p

batch:
  type: slurm
  host: s3df
  bank: rfar

global.parameters:
  MESH:
    values: [cavity_coarse.ncdf, cavity_medium.ncdf, cavity_fine.ncdf]
    label: MESH.%%

study:
  - name: solve
    description: Run Omega3P with each mesh
    run:
      cmd: |
        ln -sf $(SPECROOT)/meshes/$(MESH) $(WORKSPACE)/
        cp $(SPECROOT)/$(INPUT_FILE) $(WORKSPACE)/
        cd $(WORKSPACE)
        sed -i "s/File:.*/File: .\\/$(MESH)/" $(INPUT_FILE)
        $(LAUNCHER) $(ACE3P_BIN)/omega3p $(INPUT_FILE)
      nodes: 1
      procs: 128
      walltime: "00:30:00"

  - name: compare
    description: Extract and compare frequencies across meshes
    run:
      cmd: |
        echo "Mesh Frequency Residual" > $(WORKSPACE)/convergence.txt
        for d in $(solve.workspace)/MESH.*/; do
          MESH=$(basename $d | sed 's/MESH.//')
          FREQ=$(grep "Frequency:" $d/*.out | head -1 | awk '{print $2}')
          RES=$(grep "Residual:" $d/*.out | head -1 | awk '{print $2}')
          echo "$MESH $FREQ $RES" >> $(WORKSPACE)/convergence.txt
        done
        column -t $(WORKSPACE)/convergence.txt
      depends: [solve_*]
```

## Example 2

User: "Sweep gradient from 10 to 50 MV/m in Track3P and find the multipacting threshold"

Output:
```yaml
description:
  name: track3p-gradient-sweep
  description: Gradient sweep to identify multipacting threshold

env:
  variables:
    ACE3P_BIN: /sdf/group/rfar/lge/sdf/ace3p/build/bin
    TEMPLATE: $(SPECROOT)/templates/cavity.track3p

batch:
  type: slurm
  host: s3df
  bank: rfar

global.parameters:
  GRADIENT:
    values: [1.0e7, 2.0e7, 3.0e7, 4.0e7, 5.0e7]
    label: GRAD.%%

study:
  - name: track
    description: Run Track3P at each gradient level
    run:
      cmd: |
        cd $(WORKSPACE)
        sed "s/@GRADIENT@/$(GRADIENT)/" $(TEMPLATE) > run.track3p
        ln -sf $(SPECROOT)/data/*.ncdf .
        ln -sf $(SPECROOT)/data/omega3p_results .
        $(LAUNCHER) $(ACE3P_BIN)/track3p run.track3p
      nodes: 1
      procs: 128
      walltime: "01:00:00"

  - name: analyze
    description: Identify multipacting threshold from impact growth
    run:
      cmd: |
        echo "Gradient Impacts Growth" > $(WORKSPACE)/threshold.txt
        for d in $(track.workspace)/GRAD.*/; do
          GRAD=$(basename $d | sed 's/GRAD.//')
          IMPACTS=$(grep -i "total.*impact" $d/*.out | awk '{print $NF}')
          echo "$GRAD $IMPACTS" >> $(WORKSPACE)/threshold.txt
        done
        echo "=== Multipacting Threshold Analysis ==="
        cat $(WORKSPACE)/threshold.txt
      depends: [track_*]
```
"""


def _detect_model() -> str:
    """Auto-detect which model ID to use based on available credentials."""
    import os
    if os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        return "us.anthropic.claude-sonnet-4-6"
    return "claude-sonnet-4-6-20250514"


def generate_workflow(description: str, tool: str = "maestro", model: str = "") -> str:
    """Generate a workflow YAML spec from natural language description."""
    if not model:
        model = _detect_model()
    client = Anthropic()

    tool_context = ""
    if tool == "merlin":
        tool_context = "\n\nIMPORTANT: Generate a MERLIN workflow (not Maestro). Include merlin.resources.workers, task_queue assignments, and retry/fault-tolerance settings."

    response = client.messages.create(
        model=model,
        max_tokens=16000,
        system=[
            {"type": "text", "text": SYSTEM_PROMPT + tool_context},
            {"type": "text", "text": EXAMPLES, "cache_control": {"type": "ephemeral"}},
        ],
        messages=[
            {"role": "user", "content": f"Generate a {tool} workflow YAML for: {description}"},
        ],
    )

    content = ""
    for block in response.content:
        if hasattr(block, "text"):
            content = block.text
            break

    # Extract YAML from markdown code blocks if present
    if "```yaml" in content:
        start = content.index("```yaml") + 7
        end = content.index("```", start)
        content = content[start:end].strip()
    elif "```" in content:
        start = content.index("```") + 3
        end = content.index("```", start)
        content = content[start:end].strip()

    return content


def validate_yaml(content: str) -> tuple[bool, str]:
    """Validate that the generated content is valid YAML."""
    import yaml
    try:
        doc = yaml.safe_load(content)
        if not isinstance(doc, dict):
            return False, "YAML did not parse as a dictionary"
        if "description" not in doc:
            return False, "Missing required 'description' block"
        if "study" not in doc:
            return False, "Missing required 'study' block"
        return True, "Valid"
    except yaml.YAMLError as e:
        return False, f"YAML parse error: {e}"


def main():
    parser = argparse.ArgumentParser(
        description="Generate ACE3P workflow specs from natural language",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "Run Omega3P sweep over 3 frequencies on 2 nodes"
  %(prog)s --tool merlin "Large parameter sweep with 100 cavity geometries"
  %(prog)s --output sweep.yaml "Compare FE orders 1, 2, 3 for convergence"
        """,
    )
    parser.add_argument("description", help="Natural language description of the workflow")
    parser.add_argument("--tool", choices=["maestro", "merlin"], default="maestro", help="Target workflow tool")
    parser.add_argument("--output", "-o", type=str, help="Output file (default: stdout)")
    parser.add_argument("--validate", action="store_true", default=True, help="Validate generated YAML")
    parser.add_argument("--model", default="", help="Claude model to use (auto-detects if not specified)")
    args = parser.parse_args()

    print(f"Generating {args.tool} workflow for: {args.description}", file=sys.stderr)
    print("---", file=sys.stderr)

    yaml_content = generate_workflow(args.description, tool=args.tool, model=args.model)

    if args.validate:
        valid, msg = validate_yaml(yaml_content)
        if not valid:
            print(f"WARNING: Generated YAML validation failed: {msg}", file=sys.stderr)
        else:
            print("Validation: PASSED", file=sys.stderr)

    if args.output:
        Path(args.output).write_text(yaml_content)
        print(f"Written to: {args.output}", file=sys.stderr)
    else:
        print(yaml_content)


if __name__ == "__main__":
    main()
