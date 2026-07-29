# Web-Based Visualization and GUI Tools on S3DF

## Summary of Available Tools

### ParaView 5.11.1 (Web-Capable)

**Location:** `/sdf/group/rfar/software/ParaView-5.11.1-MPI-Linux-Python3.9-x86_64/`

**Web applications included:**
- **ParaView Visualizer** — Full ParaView GUI in browser (3D rendering, filters, pipelines)
- **ParaView Glance** — Lightweight client-side viewer (no server needed for pre-exported files)
- **ParaView Lite** — Simplified web viewer
- **Divvy** — Data analysis and scatter plot tool

**Web support libraries:** wslink, VTK Web Core, WebGL Exporter

**How to run ParaView Web Visualizer:**
```bash
PVDIR=/sdf/group/rfar/software/ParaView-5.11.1-MPI-Linux-Python3.9-x86_64

# Start web visualizer serving ACE3P results
$PVDIR/bin/pvpython \
  $PVDIR/share/paraview-5.11/web/visualizer/server/pvw-visualizer.py \
  --data /path/to/your/results \
  --port 8080

# Access via browser (with SSH tunnel):
# ssh -L 8080:localhost:8080 user@s3df.slac.stanford.edu
# Then open: http://localhost:8080
```

**Can ParaView run on a web server?** Yes. ParaView 5.11 includes built-in web applications that serve a full visualization interface over HTTP/WebSocket. The `pvw-visualizer.py` script starts a web server that renders 3D data server-side and streams it to the browser. No ParaView installation is needed on the client.

### Cubit 16.12 (Mesh Generation)

**Location:** `/sdf/group/rfar/software/Cubit-16.12/`

**GUI access options:**
- **NoMachine** — Remote desktop session on S3DF (recommended)
- **X11 forwarding** — `ssh -X s3df` then run cubit
- **Batch mode** — Run `.jou` journal files without GUI:
  ```bash
  /sdf/group/rfar/software/Cubit-16.12/cubit -batch -nographics -input Pillbox.jou
  ```

**Example journal files:** `/sdf/group/rfar/software/cubit01.jou` through `cubit05.jou`

**Note:** Cubit does not have a native web interface. For web-based mesh viewing, export to VTK format and use ParaView Glance.

### ACE3P ParaView Macros

**Location:** `/sdf/group/rfar/lge/sdf/ace3p/paraview/macros/`

Python scripts for post-processing ACE3P outputs in ParaView:
- `resonant/` — Resonant particle visualization
- `trajectory/` — Particle trajectory animation
- `enhancement/` — Enhancement counter plotting
- `wakeplot/` — Wake field visualization
- `sparam/` — S-parameter analysis
- `nextmode/` — Mode analysis
- `symmetrize4/` — Symmetry operations

These can be loaded into ParaView (desktop or web) as Python macros.

---

## Architecture: End-to-End Web Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│  ACE3P Dashboard (Next.js) — all in browser                      │
│                                                                   │
│  /workflow/generate   → AI generates workflow YAML from text      │
│  /workflow/status     → Monitor Slurm jobs (auto-refresh)        │
│  /workflow/results    → View parameters, convergence plots       │
│  /workflow/visualize  → ParaView Web (iframe/embedded)           │
│  /mesh/view           → ParaView Glance for mesh inspection      │
└─────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
   AI Generator         Maestro/Slurm        ParaView Web
   (Claude API)         (S3DF compute)       (pvw-visualizer)
                              │
                              ▼
                     Post-Processing
                   (matplotlib → PNG)
```

---

## Post-Processing Pipeline (Currently Implemented)

The Maestro workflow specs now include automatic plot generation as a final step:

### FE Convergence Sweep → `plot_convergence.py`
- Convergence plot (frequency vs. FE order)
- Cost-accuracy tradeoff (DOFs vs. error)
- Summary text file

### Multi-Solver DAG → `plot_multipacting.py`
- Multipacting map (impact energy vs. field level)
- Enhancement counter bar chart
- Summary with threshold analysis

**Output:** PNG files in `<run_dir>/plots/` — directly servable by the dashboard.

### Usage in Maestro Workflow:
```yaml
  - name: plot
    description: Generate analysis plots (PNG)
    run:
      cmd: |
        python3 $(SPECROOT)/scripts/plot_convergence.py \
          $(solve.workspace) $(WORKSPACE)/plots
      depends: [solve_*]
```

---

## Feasibility Assessment

| Feature | Status | How |
|---------|--------|-----|
| Matplotlib plots in workflow | **Working** | Scripts tested with real data |
| Dashboard shows PNG results | **Ready** | Serve from workflow output dir |
| ParaView Web for 3D fields | **Available** | pvw-visualizer.py on port 8080 |
| ParaView Glance (lightweight) | **Available** | Static HTML, export VTK files |
| Cubit GUI in browser | **Needs NoMachine** | Not native web |
| ACE3P macros in web ParaView | **Feasible** | Load as Python plugins |

---

## Next Steps

1. **Done**: Matplotlib post-processing integrated into workflow specs
2. **Next**: Test ParaView Web Visualizer with Omega3P mode files
3. **Future**: Embed ParaView Web into dashboard as iframe
4. **Future**: Add route `/workflow/results/:runId` to serve PNG plots from output dirs
