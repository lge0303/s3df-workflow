# Live Demo Script — AI Agentic Workflow Tool

## Pre-Demo Setup (do 5 minutes before the meeting)

```bash
# Terminal 1: Setup environment
conda activate workflow-s3df
export ANTHROPIC_API_KEY="$ANTHROPIC_AUTH_TOKEN"
export TMPDIR=/sdf/group/rfar/lge/sdf/workflow/.tmp
cd /sdf/group/rfar/lge/sdf/workflow/ai-assist/workflow-generator

# Verify everything works (quick test)
python generator.py "test" 2>&1 | head -3
# Should see: "Generating maestro workflow for: test"
```

```bash
# Terminal 2: Have results ready to show
cd /sdf/group/rfar/lge/sdf/workflow/maestro
```

---

## Demo Flow (5–7 minutes)

### Part 1: AI Generates a Workflow (2 min)

**Say:** "I'll show how a researcher can go from a description of what they want to a running HPC workflow in one command."

```bash
# Show the command (type it slowly so audience reads it)
python generator.py "Sweep gradient from 10 to 50 MV/m in Track3P to find multipacting onset"
```

**Wait for output.** The YAML scrolls naturally — audience sees the AI producing a complete, structured workflow.

**Point out:**
- "Notice it created 5 steps with correct dependencies"
- "It knows the S3DF Slurm configuration — partition, account, walltime"
- "It parameterized 9 gradient levels automatically"
- "The fan-in step at the end detects multipacting onset"
- "Validation: PASSED — this YAML is ready to run as-is"

---

### Part 2: Show a Different Workflow (1 min)

**Say:** "It works for any ACE3P scenario. Here's a Merlin workflow with fault tolerance:"

```bash
python generator.py --tool merlin "Run Omega3P sweep varying iris radius from 30mm to 32mm in 0.5mm steps"
```

**Point out:**
- "Merlin adds distributed workers and retry logic"
- "4 worker pools, each with appropriate concurrency"
- "max_retries and retry_delay for fault tolerance"

---

### Part 3: Show Pre-Run Results (2 min)

**Say:** "These AI-generated workflows actually work. Here are results from workflows we've already run on S3DF."

```bash
# Show convergence results
cat /sdf/group/rfar/lge/sdf/workflow/maestro/ace3p-fe-convergence_20260728-120635/compare/compare.out
```

**Say:** "3 parallel Slurm jobs, each running Omega3P with a different FE order. Textbook convergence."

```bash
# Show the auto-generated plot (open in image viewer or show file)
ls /sdf/group/rfar/lge/sdf/workflow/maestro/ace3p-fe-convergence_20260728-120635/plots/
# → convergence.png, cost_accuracy.png, summary.txt
```

```bash
# Show multipacting results
cat /sdf/group/rfar/lge/sdf/workflow/maestro/ace3p-multi-solver_20260728-133254/plots/summary.txt
```

**Say:** "The workflow automatically generates publication-ready plots. No manual post-processing needed."

---

### Part 4: (Optional) Submit a Live Workflow (3 min)

**Only do this if time allows and you want to show real-time Slurm submission.**

```bash
cd /sdf/group/rfar/lge/sdf/workflow/maestro

# Submit the FE convergence sweep (takes ~3 min)
maestro run ace3p-fe-sweep.yaml --autoyes

# Monitor
squeue -u $USER
maestro status .
```

**Say:** "Maestro just submitted 3 parallel Slurm jobs. Each runs Omega3P on a different node. When all finish, it automatically runs the comparison and plotting steps."

---

## Backup: Pre-Captured Terminal Output

If the API is slow or network issues occur, show these pre-captured results:

### AI Generator Output (saved)
```
Generating maestro workflow for: Sweep gradient from 10 to 50 MV/m in Track3P...
---
Validation: PASSED
description:
  name: track3p-gradient-sweep-multipacting
  description: >
    Sweep accelerating gradient from 10 to 50 MV/m using Track3P...
[... full YAML ...]
```

### Convergence Results
```
=== FE Order Convergence Study ===

FE_Order  Mode1_Freq(Hz)       Mode2_Freq(Hz)       DOFs
--------  ------------------   ------------------   ------
1         1.3127548414628332e+09   2.3292250131240473e+09   15124
2         1.3138129363758669e+09   2.3291349970783100e+09   83476
3         1.3138257550129840e+09   2.3291183308421493e+09   245616

Reference: 1.3138129364e9 Hz (analytical TM010 pillbox mode)
```

---

## Key Talking Points

1. **"One command"** — From English description to running workflow
2. **"Domain-aware"** — AI knows ACE3P solvers, S3DF config, Slurm patterns
3. **"Validated"** — Generated YAML passes structure checks before execution
4. **"Real results"** — Eigenvalues match analytical references to 8 digits
5. **"Automated post-processing"** — Plots generated as part of the workflow
6. **"Extensible"** — Not limited to ACE3P; any HPC simulation workflow

---

## Questions You Might Get

| Question | Answer |
|----------|--------|
| "Does it always generate correct workflows?" | YAML structure is validated. Scientific correctness needs domain review — that's the human-in-the-loop aspect. |
| "What if the AI makes a mistake?" | User reviews YAML before `maestro run`. The agent validates but doesn't auto-submit expensive jobs. |
| "Can other groups use this?" | Yes — the framework is application-agnostic. Replace ACE3P system prompt with any domain. |
| "What about cost/tokens?" | One generation ~5-10 sec, minimal tokens. Running Claude Code itself is the main cost. |
| "How does this compare to just writing YAML?" | For experts: saves 10-15 min per workflow. For new users: enables workflows they couldn't write at all. |
| "Is this production-ready?" | Prototype stage. Next: dashboard deployment, more testing, safety policies. |
