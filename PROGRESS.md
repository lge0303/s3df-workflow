# Workflow Automation Progress

## Completed (2026-07-20)

### 1. Maestro Parameter Sweep - PASSED
- Fixed parameter-sweep.yaml (Maestro requires equal-length param arrays for column-wise zip)
- Ran 6 combinations (3 sizes x 2 methods) with fan-in aggregation
- All steps FINISHED, results correct: linear=SIZE*1.5, quadratic=SIZE^2*0.01
- Output: `maestro/examples/parameter-sweep_20260720-145517/`

### 2. Merlin Simple Sweep - PASSED
- Installed redis-server into conda env (`conda install -c conda-forge redis-server`)
- Configured ~/.merlin/app.yaml for local Redis (no RabbitMQ needed)
- Started Redis with: `redis-server --daemonize yes --dir .tmp --port 6379`
- Ran simple-sweep.yaml with `--local` flag: generate → 5 process tasks → aggregate
- All 7 steps completed, results correct: PARAM^2 * e

### 3. AiiDA Profile Setup - PASSED
- `verdi presto` created SQLite-backed profile (no PostgreSQL needed)
- Registered S3DF Slurm computer with local transport
- Registered 3 ACE3P codes: omega3p@s3df, track3p@s3df, acdtool@s3df
- Note: broker (RabbitMQ) not available; daemon/async submission disabled
- Note: calc-job plugins use placeholder entry point; custom plugin needs pip install

### 4. AI Workflow Generator - VERIFIED (partial)
- Installed `anthropic` SDK into conda env
- Validated import path and YAML validation logic works
- Full generation test blocked on ANTHROPIC_API_KEY (not set in env)

### 5. Dashboard Integration - PASSED
- Copied WorkflowMonitor.tsx → ace3p-dashboard/src/components/
- Created /workflow/status page route
- Created /workflow/generate page with AI generator UI
- Created /api/workflow/status API route (reads Maestro output dirs)
- Added "Workflows" nav section with Monitor and AI Generator links
- `next build` succeeds with all new routes

## Infrastructure Notes

- Redis running on login node port 6379 (for this session only)
- TMPDIR set to /sdf/group/rfar/lge/sdf/workflow/.tmp (avoids /lscratch issues)
- /lscratch at 94% (was 100%, blocker may have cleared)
- Conda env: workflow-s3df at /sdf/home/l/lge/.conda/envs/workflow-s3df

## What's Next

1. **Full AI generator test** — Set ANTHROPIC_API_KEY and run:
   ```
   cd ai-assist/workflow-generator
   python generator.py "Run Omega3P sweep over 3 frequencies"
   ```

2. **Maestro ACE3P pipeline** — Test actual ACE3P solver integration:
   ```
   cd maestro
   maestro run ace3p-omega3p.yaml --autoyes
   ```

3. **Merlin with Slurm workers** — Submit distributed workers via Slurm:
   ```
   cd merlin/examples
   merlin run simple-sweep.yaml
   merlin run-workers simple-sweep.yaml
   ```

4. **AiiDA broker setup** — Install RabbitMQ for async daemon operation

5. **AiiDA plugin packaging** — Make aiida-ace3p pip-installable with entry points

6. **Dashboard deployment** — Push updated ace3p-dashboard to GitHub
