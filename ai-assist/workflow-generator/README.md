# AI-Assisted Workflow Generator

Generate valid Maestro/Merlin YAML workflow specs from natural language descriptions using Claude.

## Setup

```bash
conda activate workflow-s3df
export ANTHROPIC_API_KEY="$ANTHROPIC_AUTH_TOKEN"
```

**Note:** On S3DF, `$ANTHROPIC_AUTH_TOKEN` is available in Claude Code sessions. The generator uses model `us.anthropic.claude-sonnet-4-6`.

## Usage

```bash
# Generate Maestro workflow (default)
python generator.py "Run Omega3P sweep over 3 frequencies"

# Generate Merlin workflow (distributed with fault tolerance)
python generator.py --tool merlin "Sweep iris radius 30-32mm in 0.5mm steps"

# Save to file
python generator.py -o sweep.yaml "Compare FE orders 1, 2, 3 for convergence"

# Use a different model
python generator.py --model us.anthropic.claude-opus-4-6-v1 "Complex multi-solver pipeline"
```

## Examples

```bash
# Mesh convergence study
python generator.py "Run Omega3P for coarse, medium, and fine mesh and compare eigenfrequencies"

# Multipacting threshold scan
python generator.py "Sweep gradient from 10 to 50 MV/m in Track3P to find multipacting onset"

# Multi-solver pipeline
python generator.py "Run Omega3P then Track3P using the mode fields, sweep over 3 gradients"

# Large distributed sweep with Merlin
python generator.py --tool merlin "Latin hypercube sampling of 200 cavity geometries with fault tolerance"

# Small geometry variation
python generator.py --tool merlin "Run Omega3P sweep varying iris radius from 30mm to 32mm in 0.5mm steps"
```

## How It Works

1. User provides natural language description of simulation campaign
2. Claude generates YAML using ACE3P-specific system prompt with few-shot examples
3. Generated YAML is validated for correct structure (description + study blocks required)
4. Output can be directly used with `maestro run` or `merlin run`

## Validated Test Results (2026-07-28)

| Prompt | Tool | Result |
|--------|------|--------|
| "Run Omega3P sweep over 3 frequencies" | Maestro | PASSED — meshconvert → solve → postprocess → collect |
| "Sweep iris radius 30-32mm in 0.5mm steps" | Merlin | PASSED — 4 worker pools, retry logic, fan-in aggregation |

## Integration with Dashboard

This generator is also available through the ACE3P dashboard web interface at `/workflow/generate`.
