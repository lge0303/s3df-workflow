"use client";

import { useState, useEffect } from "react";

interface WorkflowStep {
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
  steps: WorkflowStep[];
}

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-gray-200 text-gray-700",
  running: "bg-blue-100 text-blue-800 animate-pulse",
  finished: "bg-green-100 text-green-800",
  failed: "bg-red-100 text-red-800",
  cancelled: "bg-yellow-100 text-yellow-800",
};

const STATUS_ICONS: Record<string, string> = {
  pending: "○",
  running: "◷",
  finished: "✓",
  failed: "✗",
  cancelled: "■",
};

export default function WorkflowMonitor() {
  const [runs, setRuns] = useState<WorkflowRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<WorkflowRun | null>(null);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    fetchWorkflowStatus();
    if (autoRefresh) {
      const interval = setInterval(fetchWorkflowStatus, 5000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  async function fetchWorkflowStatus() {
    try {
      const response = await fetch("/api/workflow/status");
      if (response.ok) {
        const data = await response.json();
        setRuns(data.runs);
        if (data.runs.length > 0 && !selectedRun) {
          setSelectedRun(data.runs[0]);
        }
      }
    } catch {
      // API not available yet - show demo data
      setRuns(DEMO_RUNS);
      if (!selectedRun) setSelectedRun(DEMO_RUNS[0]);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return <div className="p-8 text-gray-500">Loading workflow status...</div>;
  }

  return (
    <div className="p-8 max-w-6xl">
      <header className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Workflow Monitor
          </h1>
          <p className="text-gray-500 mt-1">
            Real-time status of Maestro/Merlin workflows on S3DF
          </p>
        </div>
        <label className="flex items-center gap-2 text-sm text-gray-600">
          <input
            type="checkbox"
            checked={autoRefresh}
            onChange={(e) => setAutoRefresh(e.target.checked)}
            className="rounded"
          />
          Auto-refresh (5s)
        </label>
      </header>

      {/* Run list */}
      <div className="grid grid-cols-4 gap-6">
        <div className="col-span-1 space-y-2">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">
            Recent Runs
          </h2>
          {runs.map((run) => (
            <button
              key={run.id}
              onClick={() => setSelectedRun(run)}
              className={`w-full text-left p-3 rounded-lg border transition-colors ${
                selectedRun?.id === run.id
                  ? "border-blue-500 bg-blue-50"
                  : "border-gray-200 hover:border-gray-300"
              }`}
            >
              <p className="text-sm font-medium truncate">{run.name}</p>
              <p className="text-xs text-gray-500 mt-1">{run.startTime}</p>
              <span
                className={`inline-block mt-1 px-2 py-0.5 rounded text-xs font-medium ${STATUS_COLORS[run.status]}`}
              >
                {run.status}
              </span>
            </button>
          ))}
        </div>

        {/* DAG visualization */}
        <div className="col-span-3">
          {selectedRun && (
            <div>
              <h2 className="text-sm font-semibold text-gray-700 mb-3">
                {selectedRun.name}
                <span className="font-normal text-gray-500 ml-2">
                  {selectedRun.specFile}
                </span>
              </h2>
              <div className="space-y-3">
                {selectedRun.steps.map((step, idx) => (
                  <div
                    key={step.name}
                    className="flex items-center gap-4"
                  >
                    {/* Connection line */}
                    {idx > 0 && (
                      <div className="w-6 flex justify-center -mt-3">
                        <div className="w-0.5 h-3 bg-gray-300" />
                      </div>
                    )}
                    {/* Step card */}
                    <div
                      className={`flex-1 p-4 rounded-lg border ${
                        step.status === "running"
                          ? "border-blue-300 shadow-sm"
                          : "border-gray-200"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span
                            className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${STATUS_COLORS[step.status]}`}
                          >
                            {STATUS_ICONS[step.status]}
                          </span>
                          <div>
                            <p className="font-medium text-gray-900">
                              {step.name}
                            </p>
                            {step.depends && step.depends.length > 0 && (
                              <p className="text-xs text-gray-500">
                                depends: {step.depends.join(", ")}
                              </p>
                            )}
                          </div>
                        </div>
                        <div className="text-right text-xs text-gray-500">
                          {step.slurmJobId && (
                            <p>Job ID: {step.slurmJobId}</p>
                          )}
                          {step.startTime && <p>Started: {step.startTime}</p>}
                          {step.endTime && <p>Ended: {step.endTime}</p>}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Demo data for development when API is not available
const DEMO_RUNS: WorkflowRun[] = [
  {
    id: "run-001",
    name: "ace3p-omega3p-pipeline",
    specFile: "maestro/ace3p-omega3p.yaml",
    startTime: "2026-07-20 10:30:00",
    status: "running",
    steps: [
      {
        name: "mesh-convert",
        status: "finished",
        startTime: "10:30:05",
        endTime: "10:32:18",
        slurmJobId: "4521033",
      },
      {
        name: "omega3p-solve",
        status: "running",
        startTime: "10:32:25",
        slurmJobId: "4521034",
        depends: ["mesh-convert"],
      },
      {
        name: "postprocess",
        status: "pending",
        depends: ["omega3p-solve"],
      },
    ],
  },
  {
    id: "run-002",
    name: "omega3p-sweep-FE_ORDER",
    specFile: "maestro/ace3p-omega3p-sweep.yaml",
    startTime: "2026-07-20 09:15:00",
    status: "finished",
    steps: [
      {
        name: "prepare-input (x9)",
        status: "finished",
        startTime: "09:15:02",
        endTime: "09:15:10",
      },
      {
        name: "omega3p-solve (x9)",
        status: "finished",
        startTime: "09:15:15",
        endTime: "09:45:30",
        slurmJobId: "4520901-4520909",
        depends: ["prepare-input"],
      },
      {
        name: "extract-results (x9)",
        status: "finished",
        startTime: "09:45:35",
        endTime: "09:45:50",
        depends: ["omega3p-solve"],
      },
      {
        name: "aggregate",
        status: "finished",
        startTime: "09:45:55",
        endTime: "09:46:01",
        depends: ["extract-results_*"],
      },
    ],
  },
  {
    id: "run-003",
    name: "track3p-gradient-sweep",
    specFile: "maestro/ace3p-multi-solver.yaml",
    startTime: "2026-07-19 16:00:00",
    status: "failed",
    steps: [
      {
        name: "omega3p-solve",
        status: "finished",
        startTime: "16:00:05",
        endTime: "16:25:30",
        slurmJobId: "4519882",
      },
      {
        name: "track3p-solve",
        status: "failed",
        startTime: "16:25:35",
        endTime: "16:26:02",
        slurmJobId: "4519883",
        depends: ["omega3p-solve"],
      },
      {
        name: "track3p-analysis",
        status: "cancelled",
        depends: ["track3p-solve"],
      },
    ],
  },
];
