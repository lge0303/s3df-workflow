# S3DF Workflow Automation — Progress Tracker

**Project**: Scientific Workflow Automation for S3DF  
**Repository**: https://github.com/lge0303/s3df-workflow  
**Started**: July 20, 2026  
**Timeline**: 3 months (July – October 2026)

---

## Current Status (as of July 20, 2026)

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1: Environment Setup | Complete | Conda env created, all tools installed |
| Phase 2: Maestro | In Progress | hello-world passed, sweep not yet tested |
| Phase 3: Merlin | Not Started | Needs Redis setup |
| Phase 4: AiiDA | Not Started | Needs profile setup |
| Phase 5: AI-Assist | Not Started | Needs ANTHROPIC_API_KEY |
| Phase 6: Dashboard Monitor | Not Started | Code written, needs integration |

---

## What's Been Accomplished

### Environment (Phase 1)

- Conda environment `workflow-s3df` created at `/sdf/home/l/lge/.conda/envs/workflow-s3df/`
- Installed and verified:
  - `maestrowf 1.2.0` — CLI: `maestro`
  - `merlin 1.13.0` — CLI: `merlin`
  - `aiida-core 2.8.0` — CLI: `verdi`
- Note: needed `setuptools<71` for Merlin's `pkg_resources` dependency

### Maestro (Phase 2)

- **hello-world test PASSED** on S3DF (July 20, 2026)
  - 3-step DAG: generate → process → summarize
  - All steps completed with status FINISHED
  - Output: `maestro/examples/output/`
  - Confirmed: DAG dependency enforcement works on S3DF local executor
- Workflow specs written:
  - `maestro/examples/hello-world.yaml` — minimal test (tested)
  - `maestro/examples/parameter-sweep.yaml` — fan-out/fan-in (not yet tested)
  - `maestro/ace3p-omega3p.yaml` — full Omega3P pipeline
  - `maestro/ace3p-omega3p-sweep.yaml` — FE order × frequency sweep (9 jobs)
  - `maestro/ace3p-multi-solver.yaml` — Omega3P → Track3P cross-solver DAG
  - `maestro/templates/omega3p.template` — parameterized input file

### Code Structure (all phases)

All code written and pushed to GitHub:
- `merlin/` — app.yaml, simple-sweep, fault-tolerance, ace3p large sweep, helper scripts
- `aiida/` — setup script, `aiida-ace3p` plugin (CalcJobs, parsers, WorkChain)
- `ai-assist/` — Claude-powered workflow generator (natural language → YAML)
- `dashboard-integration/` — WorkflowMonitor.tsx component + API route

---

## Next Steps (Pick Up Here)

### Step 1: Test Maestro parameter sweep

```bash
conda activate workflow-s3df
cd /sdf/group/rfar/lge/sdf/workflow/maestro/examples
maestro run parameter-sweep.yaml --autoyes
# Wait ~2 min, then check:
maestro status sweep-output/
```

### Step 2: Set up and test Merlin

```bash
cd /sdf/group/rfar/lge/sdf/workflow/merlin

# Create Merlin config
merlin config create

# Start Redis (use an interactive node)
salloc -A rfar -N 1 -t 01:00:00
redis-server --daemonize yes
redis-cli ping   # Should respond PONG

# Run simple sweep
cd examples
merlin run simple-sweep.yaml
merlin run-workers simple-sweep.yaml

# Verify results
ls merlin_output/
```

### Step 3: Set up AiiDA profile

```bash
cd /sdf/group/rfar/lge/sdf/workflow/aiida
bash setup-profile.sh
verdi status
verdi computer list
verdi code list
```

### Step 4: Test AI workflow generator

```bash
export ANTHROPIC_API_KEY="your-key-here"
cd /sdf/group/rfar/lge/sdf/workflow/ai-assist/workflow-generator
python generator.py "Run Omega3P sweep over 3 frequencies"
python generator.py --tool merlin "Large parameter sweep with 100 geometries"
python generator.py --output test.yaml "Compare FE orders 1, 2, 3 for convergence"
# Validate output:
cat test.yaml
```

### Step 5: Integrate monitoring into ACE3P dashboard

```bash
cd /sdf/group/rfar/lge/sdf/webdev/ace3p-dashboard

# Copy monitoring component
cp /sdf/group/rfar/lge/sdf/workflow/dashboard-integration/workflow-monitor/WorkflowMonitor.tsx src/components/

# Create page route
mkdir -p src/app/workflow/status
# Create page.tsx that imports WorkflowMonitor

# Create API route
mkdir -p src/app/api/workflow/status
# Copy api-route.ts → route.ts

# Add navigation link in src/components/Navigation.tsx
# Test: npm run dev -- -p 3000
```

---

## Known Issues

| Issue | Workaround |
|-------|-----------|
| `/lscratch` disk full (300G, other users) | Set `export TMPDIR=/sdf/group/rfar/lge/sdf/workflow/.tmp` |
| Merlin needs `setuptools<71` | Already pinned in env |
| Maestro asks for interactive confirm | Use `--autoyes` flag |
| `gh` CLI not authenticated on S3DF | Use `git push` with SSH directly |

---

## Key Paths

| Resource | Path |
|----------|------|
| Workflow project | `/sdf/group/rfar/lge/sdf/workflow/` |
| Work plan | `/sdf/group/rfar/lge/sdf/workflow/docs/workplan.md` |
| ACE3P dashboard | `/sdf/group/rfar/lge/sdf/webdev/ace3p-dashboard/` |
| ACE3P source | `/sdf/group/rfar/lge/sdf/ace3p/` |
| Conda environment | `workflow-s3df` |
| NERSC training PDF | `/sdf/group/rfar/lge/sdf/workflow/workflow-nersc-training.pdf` |
| GitHub repo | https://github.com/lge0303/s3df-workflow |
| Dashboard repo | https://github.com/lge0303/ace3p-dashboard |
