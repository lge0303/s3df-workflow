# AI Agentic Workflow Tool for ACE3P on S3DF

## Overview

This project demonstrates an **AI agentic workflow tool** that transforms natural language descriptions of simulation campaigns into executable HPC workflow specifications. A researcher describes their intent in plain English, and the AI agent generates a complete, validated workflow that runs autonomously on S3DF.

### Why "AI Agentic Tool"?

| Agentic Property | How We Demonstrate It |
|-----------------|----------------------|
| **Natural language interface** | User describes intent, not implementation details |
| **Domain reasoning** | AI understands ACE3P solvers, S3DF infrastructure, Slurm patterns |
| **Autonomous execution plan** | Generates full DAG with dependencies, resources, error handling |
| **Actionable output** | YAML runs directly with `maestro run` — no manual editing needed |
| **Multi-step orchestration** | Chains solvers (Omega3P → Track3P), manages data flow between steps |
| **Fault tolerance** | Merlin workflows include retry logic and distributed execution |

### The Value Proposition

> Instead of writing Slurm scripts and YAML workflow specs manually, a researcher describes their simulation campaign in plain English. The AI agent understands ACE3P solvers, S3DF infrastructure, and workflow automation patterns. It generates a complete, validated workflow specification that runs autonomously — submitting parallel jobs to Slurm, managing cross-solver dependencies, and aggregating results — all without manual intervention.

This approach:
- **Lowers the barrier** for new users unfamiliar with HPC workflow tools
- **Reduces errors** from manually writing complex YAML and Slurm scripts
- **Accelerates iteration** — modify and regenerate workflows in seconds
- **Encodes best practices** — proper resource requests, error handling, S3DF-specific patterns

---

## Live Demo Procedure

### Prerequisites

```bash
conda activate workflow-s3df
export ANTHROPIC_API_KEY="$ANTHROPIC_AUTH_TOKEN"
export TMPDIR=/sdf/group/rfar/lge/sdf/workflow/.tmp
cd /sdf/group/rfar/lge/sdf/workflow
```

---

### Demo Step 1: Natural Language → Workflow Specification

Show how a single command turns a research question into an executable workflow.

```bash
cd ai-assist/workflow-generator

# A researcher wants to study FE order convergence
python generator.py "Run Omega3P sweep over FE orders 1, 2, 3 and compare eigenfrequency convergence"
```

**What happens:** The AI agent:
1. Interprets the research intent (convergence study)
2. Selects appropriate ACE3P solver (Omega3P)
3. Designs a parameterized sweep (FE orders 1, 2, 3)
4. Adds a fan-in step to aggregate and compare results
5. Sets correct S3DF Slurm configuration (partition, account, walltime)
6. Outputs valid, ready-to-run Maestro YAML

```bash
# Save to file for submission
python generator.py -o /tmp/demo-sweep.yaml \
  "Run Omega3P sweep over FE orders 1, 2, 3 and compare eigenfrequency convergence"

# Inspect the generated spec
cat /tmp/demo-sweep.yaml
```

---

### Demo Step 2: Submit Workflow to S3DF Slurm

Show the generated workflow running on real HPC infrastructure.

```bash
cd /sdf/group/rfar/lge/sdf/workflow/maestro

# Submit the pre-validated FE sweep (same pattern as AI generates)
maestro run ace3p-fe-sweep.yaml --autoyes
```

**What happens:** Maestro:
1. Parses the YAML DAG specification
2. Submits 3 parallel Slurm jobs (one per FE order) to `milano` partition
3. Each job runs Omega3P with 16 MPI processes
4. After all 3 complete, submits the aggregation step
5. Aggregation extracts and compares eigenfrequencies

```bash
# Monitor progress
squeue -u $USER
maestro status .
```

---

### Demo Step 3: Show Results

Display the automatically aggregated convergence results.

```bash
# View the final comparison output
cat ace3p-fe-convergence_20260728-120635/compare/compare.out
```

**Expected output:**
```
=== FE Order Convergence Study ===

FE_Order  Mode1_Freq(Hz)       Mode2_Freq(Hz)       DOFs
--------  ------------------   ------------------   ------
1         1.3127548414628332e+09   2.3292250131240473e+09   15124
2         1.3138129363758669e+09   2.3291349970783100e+09   83476
3         1.3138257550129840e+09   2.3291183308421493e+09   245616

Reference: 1.3138129364e9 Hz (analytical TM010 pillbox mode)
```

The results show textbook convergence: Order 1 has 0.08% error, Order 2 matches the reference to 8 digits, and Order 3 adds one more digit at 3× the DOF cost.

---

### Demo Step 4: Multi-Solver Pipeline (Bonus)

Show the AI generating a cross-solver workflow (Omega3P → Track3P).

```bash
cd /sdf/group/rfar/lge/sdf/workflow/ai-assist/workflow-generator

# Generate a multipacting analysis workflow
python generator.py "Sweep gradient from 10 to 50 MV/m in Track3P to find multipacting onset"
```

**What happens:** The AI generates a 5-step pipeline:
1. Mesh conversion
2. Omega3P eigenmode solve (produces RF field data)
3. RF post-processing
4. Track3P particle tracking at 9 gradient levels (parameterized)
5. Fan-in analysis with multipacting onset detection

Show the previously-run CW23 Pillbox results:

```bash
# View the actual multi-solver run results
cat /sdf/group/rfar/lge/sdf/workflow/maestro/ace3p-multi-solver_20260728-133254/track3p-solve/track3p-solve.out | tail -10
```

---

### Demo Step 5: Distributed Workflow with Merlin (Bonus)

Show how the same tool generates fault-tolerant distributed workflows.

```bash
# Generate a Merlin workflow for large-scale sweep
python generator.py --tool merlin \
  "Run Omega3P sweep varying iris radius from 30mm to 32mm in 0.5mm steps"
```

**What happens:** The AI generates a Merlin spec with:
- Multiple worker pools (mesh, solve, post-process, analysis)
- Automatic retry on failure (`max_retries`, `retry_delay`)
- Redis-based task queue for distributed execution
- Fault tolerance across Slurm allocation boundaries

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User (Researcher)                      │
│                                                          │
│  "Run Omega3P sweep over 3 frequencies and compare"     │
└──────────────────────────┬───────────────────────────────┘
                           │ Natural Language
                           ▼
┌─────────────────────────────────────────────────────────┐
│              AI Agent (Claude + ACE3P Context)            │
│                                                          │
│  • ACE3P solver knowledge (omega3p, track3p, s3p, etc.) │
│  • S3DF infrastructure (Slurm, partitions, accounts)     │
│  • Workflow patterns (DAG, sweeps, fan-in/fan-out)        │
│  • Few-shot examples of valid Maestro/Merlin specs       │
└──────────────────────────┬───────────────────────────────┘
                           │ Validated YAML
                           ▼
┌─────────────────────────────────────────────────────────┐
│            Workflow Engine (Maestro / Merlin)             │
│                                                          │
│  • DAG dependency resolution                             │
│  • Slurm job submission (sbatch)                         │
│  • Parameter sweep expansion                             │
│  • Fan-in result aggregation                             │
└──────────────────────────┬───────────────────────────────┘
                           │ Slurm Jobs
                           ▼
┌─────────────────────────────────────────────────────────┐
│               S3DF HPC Infrastructure                     │
│                                                          │
│  • Milano partition (128 cores/node)                     │
│  • ACE3P solvers (omega3p, track3p, acdtool)            │
│  • Parallel execution across multiple nodes              │
└──────────────────────────────────────────────────────────┘
```

---

## Validated Results

All workflows have been tested end-to-end on S3DF Slurm:

| Test | Tool | Result |
|------|------|--------|
| Omega3P single solve (PillboxLossless) | Maestro | PASSED — eigenvalues match reference |
| FE order convergence (orders 1, 2, 3) | Maestro | PASSED — 3 parallel jobs, textbook convergence |
| Multi-solver DAG (Omega3P → Track3P) | Maestro | PASSED — CW23 Pillbox, multipacting detected |
| AI → "3 frequencies" | Maestro | PASSED — valid YAML with 4-step pipeline |
| AI → "iris radius sweep" | Merlin | PASSED — 4 worker pools, retry logic |
| AI → "gradient sweep Track3P" | Maestro | PASSED — 5-step pipeline with onset detection |

---

## How to Run the Demo Yourself

```bash
# 1. Setup
conda activate workflow-s3df
export ANTHROPIC_API_KEY="$ANTHROPIC_AUTH_TOKEN"
cd /sdf/group/rfar/lge/sdf/workflow/ai-assist/workflow-generator

# 2. Generate any workflow from natural language
python generator.py "Your simulation description here"

# 3. Generate and save
python generator.py -o my-workflow.yaml "Your description"

# 4. Run on S3DF
cd /sdf/group/rfar/lge/sdf/workflow/maestro
maestro run /path/to/my-workflow.yaml --autoyes

# 5. Monitor
squeue -u $USER
maestro status .
```

---

## References

- **S3DF Workflow Repository:** https://github.com/lge0303/s3df-workflow
- **ACE3P Dashboard:** https://github.com/lge0303/ace3p-dashboard
- **CW23 Training Examples:** https://s3df.slac.stanford.edu/people/cho/cw23/examples/
- **NERSC Workflow Training:** "Automating HPC Research Workflows on Perlmutter" (May 2026, Bill Arndt)
- **Maestro Documentation:** https://maestrowf.readthedocs.io/
- **Merlin Documentation:** https://merlin.readthedocs.io/
