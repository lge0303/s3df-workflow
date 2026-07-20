# AiiDA for ACE3P Provenance Tracking on S3DF

Automatic provenance recording for ACE3P simulations using [AiiDA](https://www.aiida.net/).

## Setup

```bash
conda activate workflow-s3df

# Quick SQLite setup (development)
bash setup-profile.sh

# Verify
verdi status
verdi code list
```

## Plugin: aiida-ace3p

Custom CalcJob classes for ACE3P solvers:

| CalcJob | Description |
|---------|-------------|
| `Omega3pCalculation` | Eigenmode solver — generates input, parses eigenvalues |
| `Track3pCalculation` | Particle tracking — uses Omega3P mode fields as input |
| `AcdtoolCalculation` | Mesh conversion and post-processing utility |

### Install plugin

```bash
cd ace3p-plugin
pip install -e .
verdi plugin list aiida.calculations  # Should show ace3p.omega3p, etc.
```

## Usage Example

```python
from aiida import orm, load_profile
from aiida.engine import run

load_profile()

# Load registered code and prepare inputs
omega3p_code = orm.load_code("omega3p@s3df")
mesh = orm.SinglefileData("/path/to/pillbox4.ncdf")
params = orm.Dict({
    "fe_order": 2,
    "num_eigenvalues": 2,
    "freq_shift": 1.0e9,
    "boundaries": {"magnetic": "1, 2", "exterior": "6"},
})

# Run with automatic provenance
result = run(omega3p_code.get_builder(), mesh=mesh, parameters=params)
print(result["eigenvalues"].get_dict())
```

## Querying Provenance

```bash
# List all calculations
verdi process list -a

# Show details of a specific run
verdi process show <PK>

# Visualize provenance graph
verdi node graph generate <PK> --output-format png

# Export for publication
verdi archive create --all my_study.aiida
```

## WorkGraph Pipeline

The `Omega3pWorkflow` chains mesh-convert → solve → postprocess with full provenance:

```python
from aiida.plugins import WorkflowFactory

Omega3pWorkflow = WorkflowFactory("ace3p.omega3p_workflow")
builder = Omega3pWorkflow.get_builder()
builder.mesh_file = orm.SinglefileData("pillbox4.gen")
builder.solver_parameters = orm.Dict({...})
builder.omega3p_code = orm.load_code("omega3p@s3df")
builder.acdtool_code = orm.load_code("acdtool@s3df")

# Submit (async, daemon handles execution)
from aiida.engine import submit
node = submit(builder)
print(f"Submitted workflow PK={node.pk}")
```

## Production Upgrade Path

| Component | Development | Production |
|-----------|------------|------------|
| Database | SQLite (verdi presto) | PostgreSQL on S3DF services |
| Execution | `run()` synchronous | `submit()` + AiiDA daemon |
| Broker | None | RabbitMQ for async execution |
