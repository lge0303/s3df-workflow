# Scientific Workflow Automation for S3DF

## Work Plan: Evaluation and Enablement of Workflow Technologies

**Author:** Lixin Ge  
**Date:** July 2026  
**Duration:** 3 months (July – October 2026)  
**Location:** `/sdf/group/rfar/lge/sdf/workflow/`

---

## 1. Motivation and Background

SLAC's S3DF computing environment serves a diverse set of scientific computing workloads, including the ACE3P parallel electromagnetic simulation suite. Currently, researchers manage multi-step simulation pipelines (geometry → meshing → solving → post-processing → visualization) using ad-hoc bash scripts and manual Slurm job submission. This approach breaks down at scale:

- Parameter sweeps generate combinatorial explosions that exceed manual management
- Multi-step pipelines with dependencies are fragile when encoded in bash
- Failed tasks require manual identification and resubmission
- Reproducing past results requires reconstructing which inputs and code versions were used
- New users face a steep learning curve for complex workflows

A prototype **ACE3P Workflow Dashboard** (Next.js web application, [github.com/lge0303/ace3p-dashboard](https://github.com/lge0303/ace3p-dashboard)) has already been developed, demonstrating how workflow documentation, input file generation, and monitoring can be integrated into an accessible web interface. This plan extends that foundation with production-grade workflow orchestration.

### Reference Material

This plan draws from the NERSC "Automating HPC Research Workflows on Perlmutter" training (May 28, 2026, by Bill Arndt), which presents a progressive capability model:

| Level | Tool | Capability Added |
|-------|------|-----------------|
| 3 | **Maestro** | DAG-based dependency management, YAML-declared workflows |
| 4 | **Merlin** | Distributed coordination via message broker, fault tolerance at scale |
| 5 | **AiiDA** | Comprehensive automatic provenance tracking |

---

## 2. Objectives

1. **Evaluate** Maestro, Merlin, and AiiDA for suitability on S3DF infrastructure
2. **Enable** these tools with S3DF-specific configuration (Slurm accounts, partitions, storage)
3. **Demonstrate** each tool using real ACE3P simulation workflows as the example application
4. **Integrate** AI-assisted workflow generation into the existing dashboard
5. **Extend** the dashboard with live workflow monitoring capabilities

---

## 3. Technical Plan

### Phase 1: Environment Setup & Tool Installation (Weeks 1–2)

#### 3.1.1 Conda Environment

Create a shared environment with all workflow tools:

```yaml
# environment.yml
name: workflow-s3df
channels:
  - conda-forge
dependencies:
  - python=3.11
  - pip
  - redis
  - pip:
    - maestrowf
    - merlin
    - aiida-core
    - aiida-workgraph
    - pyyaml
    - numpy
```

#### 3.1.2 S3DF Configuration

| Parameter | S3DF Value |
|-----------|-----------|
| Slurm account | `rfar` |
| Partition | `shared` / `roma` / `milano` |
| ACE3P binaries | `/sdf/group/rfar/lge/sdf/ace3p/build/bin/` |
| Working storage | `/sdf/group/rfar/lge/sdf/workflow/` |
| Scratch | `/sdf/scratch/rfar/lge/` |

#### 3.1.3 Directory Structure

```
/sdf/group/rfar/lge/sdf/workflow/
├── environment.yml
├── docs/
│   └── workplan.md              (this document)
├── maestro/
│   ├── ace3p-omega3p.yaml       # Omega3P pipeline spec
│   ├── ace3p-track3p.yaml       # Track3P pipeline spec
│   ├── ace3p-multi-solver.yaml  # Cross-solver DAG
│   └── examples/                # Simple test workflows
├── merlin/
│   ├── app.yaml                 # Redis broker configuration
│   ├── ace3p-sweep.yaml         # Large parameter sweep
│   └── examples/
├── aiida/
│   ├── setup-profile.sh
│   └── ace3p-plugin/            # Custom AiiDA CalcJob for ACE3P
├── ai-assist/
│   └── workflow-generator/      # LLM-based YAML spec generator
└── dashboard-integration/
    └── workflow-monitor/        # Real-time job status components
```

---

### Phase 2: Maestro — DAG Workflow Orchestration (Weeks 2–4)

#### 3.2.1 Why Maestro

Maestro (developed at LLNL) provides:
- Declarative YAML workflow specification
- DAG-based dependency resolution
- Built-in parameter sweep expansion (`global.parameters`)
- Native Slurm integration (auto-generates `sbatch` scripts)
- Fan-out/fan-in patterns for parallel parameter studies

#### 3.2.2 ACE3P Pipeline as Maestro Spec

Encode the existing 6-step Omega3P workflow:

```yaml
description:
  name: ace3p-omega3p-pipeline
  description: |
    Complete Omega3P eigenmode simulation pipeline on S3DF.
    Steps: mesh-convert → solve → post-process

env:
  variables:
    ACE3P_BIN: /sdf/group/rfar/lge/sdf/ace3p/build/bin
    MESH_FILE: pillbox4.gen
    INPUT_FILE: pillbox.omega3p
    RFPOST_FILE: pillbox.rfpost

batch:
  type: slurm
  host: s3df
  bank: rfar

study:
  - name: mesh-convert
    description: Convert Genesis mesh to NetCDF format
    run:
      cmd: |
        #SBATCH --constraint=cpu
        srun -n 1 $(ACE3P_BIN)/acdtool meshconvert $(MESH_FILE)
      nodes: 1
      procs: 1
      walltime: "00:10:00"

  - name: omega3p-solve
    description: Eigenmode computation
    run:
      cmd: |
        #SBATCH --constraint=cpu
        srun -n $(PROCS) $(ACE3P_BIN)/omega3p $(INPUT_FILE)
      depends: [mesh-convert]
      nodes: 1
      procs: 128
      walltime: "00:30:00"

  - name: postprocess
    description: Extract RF parameters (R/Q, Q-factor)
    run:
      cmd: |
        srun -n 1 $(ACE3P_BIN)/acdtool postprocess rf $(RFPOST_FILE)
      depends: [omega3p-solve]
      nodes: 1
      procs: 1
      walltime: "00:10:00"
```

#### 3.2.3 Parameter Sweeps

```yaml
global.parameters:
  FE_ORDER:
    values: [1, 2, 3]
    label: FE_ORDER.%%
  FREQ_SHIFT:
    values: [1.0e9, 2.0e9, 3.0e9]
    label: FREQ_SHIFT.%%
```

This produces 9 independent pipeline executions with automatic directory organization.

#### 3.2.4 Multi-Solver DAG

Demonstrate Omega3P → Track3P dependency (Track3P uses mode fields from Omega3P):

```
mesh-convert → omega3p-solve → track3p-solve → impact-analysis
                             └→ postprocess
```

#### 3.2.5 Deliverable

- Working Maestro specs for 3 ACE3P pipelines
- Documentation: S3DF-specific Maestro usage guide
- Verification: `maestro run ace3p-omega3p.yaml` completes full pipeline

---

### Phase 3: Merlin — Distributed Execution & Fault Tolerance (Weeks 4–6)

#### 3.3.1 Why Merlin

Merlin (developed at LLNL) adds over Maestro:
- Persistent message broker (Redis) preserves workflow state
- Workers across separate Slurm jobs, nodes, and time
- Automatic retry (`$(MERLIN_RETRY)`) and checkpoint/restart (`$(MERLIN_RESTART)`)
- Scales to millions of tasks
- Campaign can span multiple Slurm allocations

#### 3.3.2 Redis Infrastructure on S3DF

| Option | Approach | Pros | Cons |
|--------|----------|------|------|
| A (preferred) | Redis container via Podman | Persistent, isolated | Requires container setup |
| B (evaluation) | Redis on compute node | Quick to test | Ephemeral, port conflicts |
| C (production) | Redis on SPIN | Highly available | Requires SPIN allocation |

#### 3.3.3 Large-Scale Parameter Sweep

Convert the Omega3P sweep to Merlin with programmatic parameter generation:

```yaml
merlin:
  resources:
    workers:
      simworkers:
        args: --concurrency 4 --prefetch-multiplier 1 -O fair
        steps: [omega3p-solve]

  samples:
    generate:
      cmd: python generate_params.py --n 100 --method lhs
    file: params.npy
    column_labels: [cavity_radius, iris_radius, fe_order]

study:
  - name: omega3p-solve
    description: Run eigenmode solver with sampled parameters
    run:
      cmd: |
        python prepare_input.py --radius $(cavity_radius) --iris $(iris_radius) --order $(fe_order)
        srun -n 64 $(ACE3P_BIN)/omega3p generated.omega3p
      task_queue: simworkers
      nodes: 1
      procs: 64
      walltime: "00:20:00"
      retry_delay: 10
      max_retries: 3
```

#### 3.3.4 Fault Tolerance Demonstration

- Inject synthetic failures to demonstrate retry behavior
- Implement checkpoint/restart for long Track3P multipacting simulations
- Show campaign resumption after Slurm allocation expires

#### 3.3.5 Deliverable

- Working Merlin specs with 100+ task sweep on S3DF
- Redis deployment documentation
- Fault tolerance demonstration with metrics

---

### Phase 4: AiiDA — Provenance Tracking (Weeks 6–8)

#### 3.4.1 Why AiiDA

AiiDA adds over Merlin:
- Automatic, comprehensive provenance recording of every calculation
- Searchable graph database linking inputs → calculations → outputs
- Exportable archives for publication-grade reproducibility
- Cache identical calculations (avoid redundant compute)
- Team coordination with shared computation history

#### 3.4.2 S3DF Profile Setup

```bash
verdi presto  # Quick SQLite setup for development
verdi computer setup  # Register S3DF Slurm
verdi code create core.code.installed  # Register ACE3P binaries
```

#### 3.4.3 ACE3P AiiDA Plugin (`aiida-ace3p`)

Custom CalcJob classes:

| Class | Input | Output |
|-------|-------|--------|
| `Omega3pCalculation` | `.omega3p` config, mesh file | Eigenvalues, mode files |
| `Track3pCalculation` | `.track3p` config, mode files | Impact data, trajectories |
| `AcdtoolCalculation` | Mesh file, operation type | Converted mesh, RF parameters |

Each automatically records:
- All input parameters and files
- Code version and executable path
- Compute resources used
- All output data and files
- Wall time and exit status

#### 3.4.4 WorkGraph Pipeline

```python
from aiida_workgraph import WorkGraph, task

@task.calcfunction
def prepare_mesh(geometry, mesh_params):
    # Returns AiiDA SinglefileData with .ncdf mesh
    ...

@task.calcfunction  
def run_omega3p(mesh, solver_params):
    # Returns eigenvalues and mode files
    ...

@task.calcfunction
def postprocess(mode_files, rfpost_params):
    # Returns R/Q, Q-factor results
    ...

wg = WorkGraph("ace3p-omega3p")
prep = wg.add_task(prepare_mesh, geometry=geo, mesh_params=params)
solve = wg.add_task(run_omega3p, mesh=prep.outputs.result)
post = wg.add_task(postprocess, mode_files=solve.outputs.modes)
wg.submit()
```

#### 3.4.5 Deliverable

- Working AiiDA profile on S3DF with registered computer and codes
- `aiida-ace3p` plugin with 3 CalcJob classes
- Provenance demonstration: trace any result back to inputs
- Provenance graph export (PNG visualization)

---

### Phase 5: AI-Assisted Workflow Generation (Weeks 8–10)

#### 3.5.1 Concept

Leverage LLMs to lower the barrier to workflow adoption:
- User describes simulation campaign in natural language
- System generates valid Maestro YAML or Merlin spec
- Validates against ACE3P parameter constraints
- Offers preview and download

#### 3.5.2 Implementation

```python
# workflow-generator CLI
from anthropic import Anthropic

def generate_workflow(description: str, tool: str = "maestro") -> str:
    """
    Given natural language, produce a valid workflow spec.
    Uses few-shot examples from our Phase 2-3 specs.
    """
    client = Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6-20250514",
        system=SYSTEM_PROMPT_WITH_EXAMPLES,
        messages=[{"role": "user", "content": description}]
    )
    return validate_and_return(response.content[0].text)
```

#### 3.5.3 Dashboard Integration

Add to existing ACE3P dashboard:
- New route: `/workflow/generate`
- Text area for natural language input
- Generated YAML preview with syntax highlighting
- Validation feedback and download button

#### 3.5.4 Deliverable

- Python CLI tool: `workflow-gen "Run Omega3P sweep over 5 frequencies"`
- Dashboard page with interactive generation
- Test suite with 10+ validated generation scenarios

---

### Phase 6: Dashboard Workflow Monitoring (Weeks 10–12)

#### 3.6.1 Live Monitoring Component

Extend the existing ACE3P dashboard with real-time workflow status:

```typescript
// WorkflowMonitor.tsx - new component
interface WorkflowStep {
  name: string;
  status: 'pending' | 'running' | 'finished' | 'failed';
  startTime?: string;
  endTime?: string;
  slurmJobId?: string;
}
```

Features:
- Visual DAG with color-coded step status
- Auto-refresh via polling (Maestro status directory or `squeue`)
- Click-through to Slurm job logs
- Historical run browser

#### 3.6.2 End-to-End User Flow

```
Dashboard Form → Generate Input Files → Generate Workflow Spec → Submit → Monitor
     ↑                                                                      ↓
     └──────────────────── Results + Provenance ←───────────────────────────┘
```

#### 3.6.3 Deliverable

- New dashboard route: `/workflow/status`
- `WorkflowMonitor.tsx` component with DAG visualization
- Integration with Maestro output directories
- End-to-end demo: form → submit → monitor → results

---

## 4. Deliverables Summary

| Week | Phase | Milestone | Verification |
|------|-------|-----------|-------------|
| 2 | Setup | Environment ready | All tools importable, Slurm test job succeeds |
| 4 | Maestro | Pipeline automated | `maestro run` completes 3-step Omega3P pipeline |
| 6 | Merlin | Distributed sweep | 100 tasks processed across 2 Slurm allocations |
| 8 | AiiDA | Provenance working | `verdi node graph generate` renders full DAG |
| 10 | AI | Workflow generator | Natural language → valid YAML (10 test cases) |
| 12 | Dashboard | Monitoring live | Real-time status updates during active workflow |

---

## 5. Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Redis not available on S3DF | Use compute-node Redis for evaluation; request SPIN for production |
| AiiDA PostgreSQL dependency | Use SQLite for prototype; PostgreSQL for Phase 2 deployment |
| S3DF Slurm differs from Perlmutter | Test each tool's Slurm integration in Week 1; adapt batch configs |
| LLM generates invalid YAML | Validation layer + constrained output schema + test suite |
| Tool version conflicts | Isolated conda env; pin versions in environment.yml |

---

## 6. Success Criteria

1. A researcher can define and execute an ACE3P parameter sweep using Maestro YAML without writing bash scripts
2. A 100-task campaign runs unattended with automatic retry of failures (Merlin)
3. Any simulation result can be traced back to its exact inputs and code version (AiiDA)
4. A non-expert can generate a valid workflow spec from a natural language description
5. The dashboard shows real-time workflow progress without SSH/terminal access

---

## 7. Relationship to Existing Work

The prototype ACE3P dashboard (`/sdf/group/rfar/lge/sdf/webdev/ace3p-dashboard`) provides:
- Input file generators for all 5 ACE3P solver modules
- Workflow documentation with step-by-step tutorials
- Slurm script generation for Perlmutter

This plan **extends** the dashboard by adding:
- Backend workflow orchestration (Maestro/Merlin)
- Provenance database (AiiDA)
- AI-powered workflow generation
- Live monitoring interface

The dashboard serves as the user-facing layer; the workflow tools provide the backend automation engine.
