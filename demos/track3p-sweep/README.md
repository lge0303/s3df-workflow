# Track3P Multipacting Sweep — End-to-End Demo

## One Command, Full Pipeline

```bash
conda activate workflow-s3df
export ANTHROPIC_API_KEY="$ANTHROPIC_AUTH_TOKEN"
cd /sdf/group/rfar/lge/sdf/workflow/demos/track3p-sweep

./run-demo.sh "Sweep gradient from 10 to 50 MV/m in Track3P for pillbox cavity"
```

## What Happens

| Step | Action | Output |
|------|--------|--------|
| 1 | AI generates Maestro YAML from your description | `generated-workflow.yaml` |
| 2 | Submits Omega3P → Track3P pipeline to S3DF Slurm | Slurm jobs on milano |
| 3 | Monitors job progress until completion | Status updates every 30s |
| 4 | Generates multipacting analysis plots | `results/*.png` |
| 5 | Displays summary with key physics results | Text + file listing |

## End-to-End Flow

```
"Sweep gradient..."  →  AI Agent  →  YAML  →  Maestro  →  Slurm  →  Results  →  Plots
     (English)          (Claude)    (spec)   (submit)   (compute)  (physics)   (PNG)
```

## Output Files

After the demo completes:

```
demos/track3p-sweep/
├── run-demo.sh                 # The demo script
├── generated-workflow.yaml     # AI-generated Maestro spec
├── results/
│   ├── multipacting_map.png    # Impact energy vs field level
│   ├── enhancement_counter.png # EC vs field level (threshold at 1.0)
│   └── summary.txt             # Text summary with particle counts
└── README.md                   # This file
```

## Customizing the Prompt

You can change what the AI generates:

```bash
# Different field range
./run-demo.sh "Sweep gradient from 5 to 30 MV/m in Track3P for pillbox cavity"

# Different focus
./run-demo.sh "Run Omega3P sweep over FE orders 1, 2, 3 for convergence study"

# Merlin distributed workflow
./run-demo.sh "Large parameter sweep with 50 geometries using Merlin with fault tolerance"
```

## For Presentations

The script produces colored terminal output suitable for screen-sharing:
- Blue headers for each step
- Green for success messages
- Yellow for step separators
- Auto-displays results at the end

## Prerequisites

```bash
conda activate workflow-s3df
export ANTHROPIC_API_KEY="$ANTHROPIC_AUTH_TOKEN"  # Only works in Claude Code session
export TMPDIR=/sdf/group/rfar/lge/sdf/workflow/.tmp
```

## Timing

| Step | Duration |
|------|----------|
| AI generation | ~5 seconds |
| Omega3P solve | ~2 minutes |
| Track3P solve | ~2 minutes |
| Plot generation | ~2 seconds |
| **Total** | **~5 minutes** |
