# Dashboard Integration: Workflow Monitoring

Components and API routes to add workflow monitoring to the [ACE3P Dashboard](https://github.com/lge0303/ace3p-dashboard).

## Components

### WorkflowMonitor.tsx

Real-time workflow status display with:
- Run list (recent workflows)
- DAG visualization with step status (color-coded)
- Auto-refresh (5-second polling)
- Slurm job ID display
- Demo data for development when API unavailable

### api-route.ts

Next.js API route (`/api/workflow/status`) that:
- Scans Maestro output directories for workflow state
- Enriches with live Slurm status via `squeue`
- Returns structured JSON for the frontend

## Integration Steps

To add to the existing ACE3P dashboard:

1. Copy `WorkflowMonitor.tsx` to `src/components/`
2. Create `src/app/workflow/status/page.tsx`:
   ```tsx
   import WorkflowMonitor from "@/components/WorkflowMonitor";
   export default function WorkflowStatusPage() {
     return <WorkflowMonitor />;
   }
   ```
3. Create `src/app/api/workflow/status/route.ts` from `api-route.ts`
4. Add navigation link in `src/components/Navigation.tsx`

## End-to-End Flow

```
User fills form → Generates input files → Generates workflow YAML
                                              ↓
                                     maestro run spec.yaml
                                              ↓
                              /workflow/status shows live progress
                                              ↓
                                     Results available
```
