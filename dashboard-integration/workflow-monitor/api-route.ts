/**
 * API route for workflow status monitoring.
 *
 * Reads Maestro output directories and Slurm job status to provide
 * real-time workflow state to the dashboard frontend.
 *
 * Next.js App Router: app/api/workflow/status/route.ts
 */

import { NextResponse } from "next/server";
import { execSync } from "child_process";
import { readdirSync, readFileSync, existsSync } from "fs";
import { join } from "path";

const WORKFLOW_DIR = "/sdf/group/rfar/lge/sdf/workflow";
const MAESTRO_OUTPUT_BASE = join(WORKFLOW_DIR, "maestro");

interface StepStatus {
  name: string;
  status: "pending" | "running" | "finished" | "failed" | "cancelled";
  startTime?: string;
  endTime?: string;
  slurmJobId?: string;
  depends?: string[];
}

interface WorkflowRun {
  id: string;
  name: string;
  specFile: string;
  startTime: string;
  status: "running" | "finished" | "failed";
  steps: StepStatus[];
}

export async function GET() {
  try {
    const runs = getMaestroRuns();
    return NextResponse.json({ runs });
  } catch (error) {
    return NextResponse.json({ runs: [], error: String(error) }, { status: 500 });
  }
}

function getMaestroRuns(): WorkflowRun[] {
  const runs: WorkflowRun[] = [];

  // Scan for Maestro timestamped output directories
  if (!existsSync(MAESTRO_OUTPUT_BASE)) return runs;

  const entries = readdirSync(MAESTRO_OUTPUT_BASE, { withFileTypes: true });
  const outputDirs = entries
    .filter((e) => e.isDirectory() && /^\d{8}-\d{6}/.test(e.name))
    .map((e) => e.name)
    .sort()
    .reverse()
    .slice(0, 10); // Last 10 runs

  for (const dir of outputDirs) {
    const runPath = join(MAESTRO_OUTPUT_BASE, dir);
    const run = parseMaestroRun(runPath, dir);
    if (run) runs.push(run);
  }

  return runs;
}

function parseMaestroRun(runPath: string, dirName: string): WorkflowRun | null {
  // Read maestro status if available
  const statusPath = join(runPath, "status.csv");
  const steps: StepStatus[] = [];

  if (existsSync(statusPath)) {
    const statusContent = readFileSync(statusPath, "utf-8");
    for (const line of statusContent.split("\n").slice(1)) {
      if (!line.trim()) continue;
      const [name, status, jobId] = line.split(",");
      steps.push({
        name: name.trim(),
        status: mapMaestroStatus(status.trim()),
        slurmJobId: jobId?.trim() || undefined,
      });
    }
  } else {
    // Infer from directory structure
    const stepDirs = readdirSync(runPath, { withFileTypes: true })
      .filter((e) => e.isDirectory() && !e.name.startsWith("."))
      .map((e) => e.name);

    for (const stepName of stepDirs) {
      const stepPath = join(runPath, stepName);
      steps.push({
        name: stepName,
        status: inferStepStatus(stepPath),
      });
    }
  }

  // Enrich with Slurm status for running jobs
  for (const step of steps) {
    if (step.status === "running" && step.slurmJobId) {
      try {
        const squeueOutput = execSync(
          `squeue -j ${step.slurmJobId} --noheader -o "%T" 2>/dev/null`,
          { encoding: "utf-8", timeout: 5000 }
        ).trim();
        if (!squeueOutput) step.status = "finished";
      } catch {
        // Job no longer in queue - likely finished
      }
    }
  }

  const overallStatus = steps.some((s) => s.status === "failed")
    ? "failed"
    : steps.some((s) => s.status === "running" || s.status === "pending")
    ? "running"
    : "finished";

  return {
    id: dirName,
    name: dirName.replace(/^\d{8}-\d{6}_/, ""),
    specFile: `maestro/${dirName}`,
    startTime: formatTimestamp(dirName),
    status: overallStatus,
    steps,
  };
}

function mapMaestroStatus(status: string): StepStatus["status"] {
  const map: Record<string, StepStatus["status"]> = {
    PENDING: "pending",
    RUNNING: "running",
    FINISHED: "finished",
    FAILED: "failed",
    CANCELLED: "cancelled",
  };
  return map[status.toUpperCase()] || "pending";
}

function inferStepStatus(stepPath: string): StepStatus["status"] {
  if (existsSync(join(stepPath, "FINISHED"))) return "finished";
  if (existsSync(join(stepPath, "FAILED"))) return "failed";
  if (existsSync(join(stepPath, "*.slurm.sh"))) return "running";
  return "pending";
}

function formatTimestamp(dirName: string): string {
  const match = dirName.match(/^(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})/);
  if (!match) return dirName;
  return `${match[1]}-${match[2]}-${match[3]} ${match[4]}:${match[5]}:${match[6]}`;
}
