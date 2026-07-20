# Maestro Workflows for ACE3P on S3DF

DAG-based workflow orchestration using [Maestro](https://github.com/LLNL/maestrowf).

## Quick Start

```bash
conda activate workflow-s3df
pip install maestrowf

# Run hello-world locally
maestro run examples/hello-world.yaml

# Dry-run ACE3P pipeline (check generated scripts)
maestro run ace3p-omega3p.yaml --dry

# Run on S3DF Slurm
maestro run ace3p-omega3p.yaml

# Check status
maestro status <output_directory>
```

## Workflow Specs

| File | Description |
|------|-------------|
| `examples/hello-world.yaml` | Minimal 3-step test (no Slurm) |
| `examples/parameter-sweep.yaml` | Fan-out/fan-in with 6 parameter combos |
| `ace3p-omega3p.yaml` | Full Omega3P pipeline: mesh → solve → postprocess |
| `ace3p-omega3p-sweep.yaml` | Omega3P with FE order × frequency sweep (9 jobs) |
| `ace3p-multi-solver.yaml` | Omega3P → Track3P cross-solver DAG |

## Key Concepts

- **Steps** define units of work with shell commands
- **depends** declares DAG edges (step B waits for step A)
- **global.parameters** expands steps into parallel parameter combinations
- **batch** configures Slurm submission (account, partition, walltime)
- **$(WORKSPACE)** is each step's unique output directory
- **$(step.workspace)** references another step's output for data flow
- **_* wildcard** in depends does fan-in (wait for all expanded instances)

## S3DF Configuration

Modify the `batch` block for your S3DF allocation:

```yaml
batch:
  type: slurm
  host: s3df
  bank: rfar        # Your Slurm account
```

## Templates

The `templates/` directory contains parameterized ACE3P input files. Placeholders like `@FE_ORDER@` are substituted by Maestro during `prepare-input` steps using `sed`.
