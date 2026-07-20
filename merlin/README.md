# Merlin Workflows for ACE3P on S3DF

Distributed workflow execution with fault tolerance using [Merlin](https://github.com/LLNL/merlin).

## Prerequisites

1. Redis server running (message broker)
2. Merlin installed: `pip install merlin`
3. `app.yaml` configured (see below)

## Redis Setup on S3DF

### Option A: Interactive session (evaluation)

```bash
salloc -A rfar -N 1 -t 02:00:00
redis-server --daemonize yes --port 6379
redis-cli ping  # Should respond PONG
```

### Option B: Podman container (persistent)

```bash
podman run -d --name redis-workflow -p 6379:6379 redis:7-alpine
```

## Quick Start

```bash
conda activate workflow-s3df
cd /sdf/group/rfar/lge/sdf/workflow/merlin

# Verify broker connectivity
merlin info

# Run simple example
cd examples
merlin run simple-sweep.yaml
merlin run-workers simple-sweep.yaml

# Run fault tolerance demo
merlin run fault-tolerance.yaml
merlin run-workers fault-tolerance.yaml
```

## Workflow Specs

| File | Description |
|------|-------------|
| `examples/simple-sweep.yaml` | 5-task distributed sweep with aggregation |
| `examples/fault-tolerance.yaml` | Retry + checkpoint/restart demonstration |
| `ace3p-sweep.yaml` | 100-point Omega3P LHS parameter sweep |

## Key Concepts

- **Redis broker**: persistent message queue holding tasks between coordinator and workers
- **task_queue**: assigns steps to named worker pools
- **Workers**: `merlin run-workers` pulls tasks from Redis and executes them
- **$(MERLIN_RETRY)**: exit code for automatic retry (transient failures)
- **$(MERLIN_RESTART)**: exit code triggering checkpoint restart
- **$(MERLIN_HARD_FAIL)**: abort task and all dependents
- **merlin.samples**: programmatic parameter generation from scripts
- **Concurrency**: `--concurrency N` runs N tasks per worker simultaneously

## Multi-Allocation Execution

Merlin campaigns can span multiple Slurm jobs:

```bash
# Job 1: push tasks to Redis
merlin run ace3p-sweep.yaml

# Job 1: start workers (runs until allocation ends)
merlin run-workers ace3p-sweep.yaml

# Job 2 (later): remaining tasks picked up automatically
merlin run-workers ace3p-sweep.yaml
```

## Scripts

- `scripts/generate_params.py` — Latin Hypercube Sampling for parameter space
- `scripts/generate_input.py` — Template substitution for ACE3P input files
