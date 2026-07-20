# AI-Assisted Workflow Generator

Generate valid Maestro/Merlin YAML workflow specs from natural language descriptions using Claude.

## Setup

```bash
conda activate workflow-s3df
export ANTHROPIC_API_KEY="your-key-here"
```

## Usage

```bash
# Generate Maestro workflow (default)
python generator.py "Run Omega3P sweep over 3 frequencies on 2 nodes"

# Generate Merlin workflow (distributed)
python generator.py --tool merlin "Large parameter sweep with 100 cavity geometries"

# Save to file
python generator.py --output sweep.yaml "Compare FE orders 1, 2, 3 for convergence"
```

## Examples

```bash
# Mesh convergence study
python generator.py "Run Omega3P for coarse, medium, and fine mesh and compare eigenfrequencies"

# Multipacting threshold scan
python generator.py "Sweep gradient from 10 to 50 MV/m in Track3P to find multipacting onset"

# Multi-solver pipeline
python generator.py "Run Omega3P then Track3P using the mode fields, sweep over 3 gradients"

# Large distributed sweep
python generator.py --tool merlin "Latin hypercube sampling of 200 cavity geometries with fault tolerance"
```

## How It Works

1. User provides natural language description
2. Claude generates YAML using ACE3P-specific system prompt with few-shot examples
3. Generated YAML is validated for correct structure
4. Output can be directly used with `maestro run` or `merlin run`

## Integration with Dashboard

This generator is also available through the ACE3P dashboard web interface at `/workflow/generate`.
