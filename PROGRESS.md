# Workflow Automation Progress

**Project:** Scientific Workflow Automation for S3DF  
**Author:** Lixin Ge  
**Last Updated:** 2026-07-20  
**Work Plan:** [docs/workplan.md](docs/workplan.md)

---

## Phase Status Overview

| Phase | Description | Status | Target |
|-------|-------------|--------|--------|
| 1 | Environment Setup & Tool Installation | COMPLETE | Week 2 |
| 2 | Maestro — DAG Workflow Orchestration | IN PROGRESS | Week 4 |
| 3 | Merlin — Distributed Execution | IN PROGRESS | Week 6 |
| 4 | AiiDA — Provenance Tracking | IN PROGRESS | Week 8 |
| 5 | AI-Assisted Workflow Generation | IN PROGRESS | Week 10 |
| 6 | Dashboard Workflow Monitoring | IN PROGRESS | Week 12 |

---

## Phase 1: Environment Setup — COMPLETE

- [x] Conda environment `workflow-s3df` created and installed
- [x] Maestro 1.2.0, Merlin 1.13.0, AiiDA 2.8.0 all installed
- [x] redis-server installed (`conda install -c conda-forge redis-server`)
- [x] anthropic SDK installed for AI workflow generator
- [x] Directory structure created per workplan spec
- [x] S3DF-specific configs (Slurm account rfar, partitions, ACE3P paths)

**Env location:** `/sdf/home/l/lge/.conda/envs/workflow-s3df`

---

## Phase 2: Maestro — IN PROGRESS

### Completed
- [x] Hello-world workflow tested and passed (3-step DAG)
- [x] Parameter sweep tested and passed (6 combinations, fan-out/fan-in)
  - Fixed: Maestro requires equal-length param arrays (column-wise zip, not cross-product)
  - Output: `maestro/examples/parameter-sweep_20260720-145517/`
- [x] ACE3P workflow specs written (omega3p, track3p, multi-solver)

### Remaining
- [ ] Test `ace3p-omega3p.yaml` with real ACE3P solvers on Slurm
- [ ] Test `ace3p-multi-solver.yaml` (Omega3P → Track3P dependency chain)
- [ ] Verify Slurm batch submission (not just local execution)
- [ ] Document S3DF-specific Maestro usage guide

### Key Finding
Maestro `global.parameters` does NOT do cross-product. All parameter arrays must be the same length — it zips them column-wise. To get a cross-product of N×M, enumerate all N*M pairs explicitly.

---

## Phase 3: Merlin — IN PROGRESS

### Completed
- [x] Merlin config created (`~/.merlin/app.yaml` → local Redis)
- [x] Redis server installed and tested on login node
- [x] Simple sweep tested in `--local` mode (generate → 5 process → aggregate)
  - Output: `merlin/examples/merlin_output/simple-sweep_20260720-150241/`

### Remaining
- [ ] Test with Slurm workers (`merlin run` + `merlin run-workers`)
- [ ] Test fault-tolerance.yaml (retry behavior demo)
- [ ] Set up persistent Redis (Podman container or SPIN service)
- [ ] Test large-scale sweep (100+ tasks across multiple Slurm allocations)
- [ ] Document Redis deployment options for S3DF

### Infrastructure Note
For evaluation: `redis-server --daemonize yes --dir .tmp --port 6379` (ephemeral, login node).  
For production: need persistent Redis via Podman or SPIN allocation.

---

## Phase 4: AiiDA — IN PROGRESS

### Completed
- [x] Profile created with `verdi presto` (SQLite backend)
- [x] S3DF registered as AiiDA computer (local transport, Slurm scheduler)
- [x] ACE3P codes registered: omega3p@s3df, track3p@s3df, acdtool@s3df
- [x] ACE3P plugin code written (CalcJob classes for Omega3P, Track3P, Acdtool)

### Remaining
- [ ] Install RabbitMQ broker for async daemon operation
- [ ] Package aiida-ace3p as pip-installable plugin (setup.cfg + entry points)
- [ ] Test actual CalcJob submission through AiiDA
- [ ] Build WorkGraph pipeline (prepare_mesh → solve → postprocess)
- [ ] Demonstrate provenance: `verdi node graph generate`
- [ ] Test calculation caching

### Limitations (no broker)
Without RabbitMQ: no daemon, no async submission, no auto-retry. Calculations must be run with `verdi run` (blocking). This is fine for development but not for production workflows.

---

## Phase 5: AI Workflow Generation — IN PROGRESS

### Completed
- [x] Generator code written with Claude API integration
- [x] System prompt with ACE3P context and few-shot examples
- [x] YAML validation layer (checks structure, required fields)
- [x] CLI interface with --tool, --output, --model options
- [x] Anthropic SDK installed and import verified

### Remaining
- [ ] Set ANTHROPIC_API_KEY and run end-to-end test
- [ ] Validate with 10+ test scenarios
- [ ] Add /api/workflow/generate backend route to dashboard
- [ ] Connect dashboard UI to backend

### To Test
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
cd ai-assist/workflow-generator
python generator.py "Run Omega3P sweep over 3 frequencies"
python generator.py --tool merlin "Large parameter sweep with 100 cavity geometries"
```

---

## Phase 6: Dashboard Integration — IN PROGRESS

### Completed
- [x] WorkflowMonitor.tsx component (real-time DAG status, auto-refresh)
- [x] /workflow/status page route created
- [x] /workflow/generate page with AI generator UI
- [x] /api/workflow/status API route (reads Maestro output dirs + squeue)
- [x] Navigation updated with "Workflows" section
- [x] `next build` passes with all new routes

### Remaining
- [ ] Add /api/workflow/generate backend (calls Python generator)
- [ ] Deploy updated dashboard
- [ ] Test with live Maestro/Merlin workflows running
- [ ] Add historical run browser
- [ ] Push to GitHub

---

## Known Issues & Workarounds

| Issue | Workaround | Status |
|-------|-----------|--------|
| /lscratch 100% full | `export TMPDIR=/sdf/group/rfar/lge/sdf/workflow/.tmp` | Resolved (94% now) |
| No RabbitMQ on S3DF | AiiDA runs without broker (limited); Merlin uses Redis only | Acceptable for eval |
| ACE3P binary path | Corrected to `/sdf/group/rfar/lge/sdf/ace3p/bin/` | Fixed |
| Maestro cross-product | Enumerate all combinations explicitly in param arrays | Fixed |

---

## Quick Reference

| What | Where |
|------|-------|
| Workflow project | `/sdf/group/rfar/lge/sdf/workflow/` |
| Work plan | `docs/workplan.md` |
| Dashboard repo | `/sdf/group/rfar/lge/sdf/webdev/ace3p-dashboard/` |
| Conda env | `workflow-s3df` (`conda activate workflow-s3df`) |
| ACE3P binaries | `/sdf/group/rfar/lge/sdf/ace3p/bin/` |
| Merlin config | `~/.merlin/app.yaml` |
| AiiDA config | `~/.aiida/` (profile: presto) |
| Temp directory | `/sdf/group/rfar/lge/sdf/workflow/.tmp` |
| GitHub (workflow) | https://github.com/lge0303/s3df-workflow |
| GitHub (dashboard) | https://github.com/lge0303/ace3p-dashboard |

---

## Session Log

### 2026-07-20 (Session 2)
- Tested Maestro parameter sweep (fixed YAML, all 6 combos passed)
- Installed redis-server, configured Merlin, tested simple sweep (7 tasks passed)
- Set up AiiDA profile, registered S3DF computer and 3 ACE3P codes
- Installed anthropic SDK, verified generator logic
- Integrated WorkflowMonitor + AI Generator into dashboard (build passes)
- Committed to both repos

### 2026-07-20 (Session 1)
- Initial repo setup with work plan
- Created all workflow specs and directory structure
- Installed conda environment with Maestro, Merlin, AiiDA
- Tested Maestro hello-world (passed)
- Wrote ACE3P AiiDA plugin, AI generator, dashboard monitor code
