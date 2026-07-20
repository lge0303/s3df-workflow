# Scientific Workflow Automation for S3DF

Evaluation and enablement of scientific workflow automation technologies for SLAC's S3DF computing environment, including workflow orchestration, AI-assisted workflow generation, and workflow monitoring interfaces.

## Overview

This project evaluates and deploys HPC workflow tools on S3DF using the ACE3P parallel electromagnetic simulation suite as the demonstration application. It builds on the [ACE3P Dashboard](https://github.com/lge0303/ace3p-dashboard) prototype.

### Tools Evaluated

| Tool | Purpose | Level |
|------|---------|-------|
| [Maestro](https://github.com/LLNL/maestrowf) | DAG-based workflow orchestration (YAML) | Dependencies |
| [Merlin](https://github.com/LLNL/merlin) | Distributed coordination via message broker | Scale + Fault tolerance |
| [AiiDA](https://www.aiida.net/) | Provenance tracking and reproducibility | Provenance |

### Additional Components

- **AI-Assisted Workflow Generation** — Natural language → valid workflow specs
- **Dashboard Monitoring** — Real-time workflow status visualization

## Project Structure

```
.
├── docs/                    # Documentation and work plan
├── maestro/                 # Maestro workflow specifications
├── merlin/                  # Merlin specs and broker config
├── aiida/                   # AiiDA profiles and plugins
├── ai-assist/               # LLM-based workflow generator
├── dashboard-integration/   # Monitoring UI extensions
└── environment.yml          # Conda environment
```

## Quick Start

```bash
# Create conda environment
conda env create -f environment.yml
conda activate workflow-s3df

# Test Maestro
cd maestro/examples
maestro run hello-world.yaml

# Test Merlin (requires Redis)
cd merlin/examples
merlin run simple-sweep.yaml
merlin run-workers simple-sweep.yaml
```

## Context

Based on the NERSC "Automating HPC Research Workflows on Perlmutter" training (May 2026), which presents a progressive capability model from simple parallelism (GNU Parallel) through provenance-tracked reproducibility (AiiDA). This project adapts those patterns for S3DF infrastructure.

## Related

- [ACE3P Dashboard](https://github.com/lge0303/ace3p-dashboard) — Web UI for ACE3P input generation and workflow documentation
- [NERSC Workflow Tutorial](https://github.com/NERSC/workflow-automation-tutorial) — Reference training materials
