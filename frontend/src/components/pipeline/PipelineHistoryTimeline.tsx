import React, { useState } from 'react';
import {
  Clock,
  Terminal,
  CheckCircle2,
  AlertOctagon,
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  Database,
  Calendar,
  Layers,
  Activity,
} from 'lucide-react';
import { PipelineRun, PipelineStepLog } from '../../types';

interface PipelineHistoryTimelineProps {
  runs: PipelineRun[];
  isLoading?: boolean;
  selectedRunId?: string | null;
  onSelectRun?: (runId: string) => void;
}

function formatDuration(ms: number): string {
  if (ms <= 0) return '0s';
  const totalSeconds = Math.floor(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  if (minutes === 0) return `${seconds}s`;
  return `${minutes}m ${seconds.toString().padStart(2, '0')}s`;
}

function formatDateTime(isoString: string): string {
  try {
    const d = new Date(isoString);
    return d.toISOString().replace('T', ' ').substring(0, 19) + ' UTC';
  } catch {
    return isoString;
  }
}

export const PipelineHistoryTimeline: React.FC<PipelineHistoryTimelineProps> = ({
  runs,
  isLoading = false,
  selectedRunId,
  onSelectRun,
}) => {
  const [expandedRunIds, setExpandedRunIds] = useState<Record<string, boolean>>({
    // Expand the latest run by default if available
    ...(runs.length > 0 ? { [runs[0].id]: true } : {}),
  });

  const toggleRunExpand = (runId: string) => {
    setExpandedRunIds((prev) => ({
      ...prev,
      [runId]: !prev[runId],
    }));
  };

  if (isLoading) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center space-y-3">
        <Activity className="w-8 h-8 text-lux-400 animate-spin mx-auto" />
        <p className="text-sm text-slate-400">Loading historical pipeline executions...</p>
      </div>
    );
  }

  if (runs.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center space-y-2">
        <Layers className="w-8 h-8 text-slate-600 mx-auto" />
        <h3 className="text-sm font-semibold text-slate-300">No Pipeline Runs Found</h3>
        <p className="text-xs text-slate-500">
          No execution runs have been logged for this scenario yet.
        </p>
      </div>
    );
  }

  const maxDuration = Math.max(...runs.map((r) => r.duration_ms || 1));
  const successComputeCount = runs.filter(
    (r) => r.execution_status === 'COMPLETED_SUCCESS' || r.execution_status === 'SUCCESS'
  ).length;
  const corruptedQualityCount = runs.filter(
    (r) => r.quality_health === 'CORRUPTED' || r.quality_health === 'DEGRADED'
  ).length;
  const healthyQualityCount = runs.filter((r) => r.quality_health === 'HEALTHY').length;

  return (
    <div className="space-y-6" data-testid="pipeline-history-timeline">
      {/* High-level Summary Metrics Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Historical Runs</span>
            <Layers className="w-4 h-4 text-slate-500" />
          </div>
          <div className="text-2xl font-bold text-white mt-2">{runs.length}</div>
          <div className="text-xs text-slate-500 mt-1">Logged pipeline executions</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Compute Success</span>
            <Terminal className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400 mt-2">
            {Math.round((successComputeCount / runs.length) * 100)}%
          </div>
          <div className="text-xs text-slate-500 mt-1">{successComputeCount} of {runs.length} exited 0</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Healthy Data Runs</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-white mt-2">{healthyQualityCount}</div>
          <div className="text-xs text-slate-500 mt-1">Passing all validations</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Corrupted Data Runs</span>
            <AlertOctagon className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-bold text-rose-400 mt-2">{corruptedQualityCount}</div>
          <div className="text-xs text-rose-500/80 mt-1">Critical anomalies detected</div>
        </div>
      </div>

      {/* Execution Runs Timeline */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/90">
          <div>
            <h3 className="text-base font-semibold text-white flex items-center gap-2">
              <Clock className="w-4 h-4 text-lux-400" />
              <span>Execution Timeline & Dual-Dimension History</span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Chronological log of batch ETL runs comparing compute exit codes against data quality health
            </p>
          </div>
          <span className="text-xs font-mono px-2.5 py-1 bg-slate-800 text-slate-400 rounded border border-slate-700">
            {runs.length} runs
          </span>
        </div>

        <div className="divide-y divide-slate-800/80">
          {runs.map((run, idx) => {
            const isExpanded = Boolean(expandedRunIds[run.id]);
            const isSelected = selectedRunId === run.id;
            const durationPct = Math.min(100, Math.round((run.duration_ms / maxDuration) * 100));

            const isSuccess =
              run.execution_status === 'COMPLETED_SUCCESS' || run.execution_status === 'SUCCESS';
            const isCorrupted = run.quality_health === 'CORRUPTED';
            const isWarning = run.quality_health === 'WARNING' || run.quality_health === 'DEGRADED';
            const isHealthy = run.quality_health === 'HEALTHY';

            return (
              <div
                key={run.id}
                className={`transition-colors ${
                  isSelected ? 'bg-lux-950/20' : 'hover:bg-slate-800/30'
                }`}
                data-testid={`pipeline-run-item-${run.id}`}
              >
                {/* Run Header / Summary Row */}
                <div className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="space-y-2 flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2.5">
                      <span className="font-mono text-sm font-semibold text-white">
                        {run.id}
                      </span>
                      <span className="text-xs font-mono text-slate-400 bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
                        {run.pipeline_name}
                      </span>
                      {idx === 0 && (
                        <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-lux-700 text-white">
                          Latest Run
                        </span>
                      )}
                    </div>

                    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-400">
                      <span className="flex items-center gap-1.5">
                        <Calendar className="w-3.5 h-3.5 text-slate-500" />
                        <span>Started: {formatDateTime(run.start_time)}</span>
                      </span>
                      <span className="flex items-center gap-1.5">
                        <Clock className="w-3.5 h-3.5 text-slate-500" />
                        <span>Duration: {formatDuration(run.duration_ms)}</span>
                      </span>
                      <span className="flex items-center gap-1.5">
                        <Database className="w-3.5 h-3.5 text-slate-500" />
                        <span>{run.records_ingested.toLocaleString()} in → {run.records_written.toLocaleString()} written</span>
                      </span>
                    </div>

                    {/* Proportional Duration Bar */}
                    <div className="pt-1 max-w-md">
                      <div className="flex items-center justify-between text-[11px] text-slate-500 mb-1">
                        <span>Execution Duration</span>
                        <span className="font-mono">{formatDuration(run.duration_ms)} ({run.duration_ms.toLocaleString()} ms)</span>
                      </div>
                      <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all ${
                            isCorrupted ? 'bg-gradient-to-r from-lux-600 to-rose-500' : 'bg-lux-500'
                          }`}
                          style={{ width: `${Math.max(durationPct, 8)}%` }}
                        />
                      </div>
                    </div>
                  </div>

                  {/* Dual-Dimension Status Badges & Controls */}
                  <div className="flex flex-row md:flex-col items-center md:items-end justify-between gap-3 shrink-0">
                    <div className="flex items-center gap-2">
                      {/* Compute Status Badge */}
                      <span
                        className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold border ${
                          isSuccess
                            ? 'bg-emerald-950/60 text-emerald-300 border-emerald-500/40'
                            : 'bg-rose-950/60 text-rose-300 border-rose-500/40'
                        }`}
                        title={`Compute: ${run.execution_status}`}
                        data-testid={`badge-compute-${run.id}`}
                      >
                        <Terminal className="w-3 h-3 mr-1 text-emerald-400" />
                        <span>{run.execution_status}</span>
                      </span>

                      {/* Quality Health Badge */}
                      <span
                        className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-bold border ${
                          isHealthy
                            ? 'bg-emerald-950/60 text-emerald-300 border-emerald-500/40'
                            : isCorrupted
                            ? 'bg-rose-950/90 text-rose-300 border-rose-500/60 shadow-sm shadow-rose-900/30'
                            : isWarning
                            ? 'bg-amber-950/60 text-amber-300 border-amber-500/40'
                            : 'bg-slate-800 text-slate-300 border-slate-700'
                        }`}
                        title={`Quality Health: ${run.quality_health}`}
                        data-testid={`badge-quality-${run.id}`}
                      >
                        {isHealthy ? (
                          <CheckCircle2 className="w-3 h-3 mr-1 text-emerald-400" />
                        ) : isCorrupted ? (
                          <AlertOctagon className="w-3 h-3 mr-1 text-rose-400" />
                        ) : (
                          <AlertTriangle className="w-3 h-3 mr-1 text-amber-400" />
                        )}
                        <span>{run.quality_health}</span>
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      {onSelectRun && (
                        <button
                          type="button"
                          onClick={() => onSelectRun(run.id)}
                          className="text-xs text-lux-400 hover:text-lux-300 font-medium transition-colors"
                        >
                          Select
                        </button>
                      )}
                      <button
                        type="button"
                        onClick={() => toggleRunExpand(run.id)}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 text-xs font-medium transition-colors focus:outline-none focus:ring-1 focus:ring-lux-500"
                        aria-expanded={isExpanded}
                        aria-label={`Toggle step logs for ${run.id}`}
                      >
                        <span>{isExpanded ? 'Hide Steps' : 'View Steps'}</span>
                        {isExpanded ? (
                          <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                        ) : (
                          <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
                        )}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Collapsible Step Logs Table */}
                {isExpanded && (
                  <div className="bg-slate-950/70 border-t border-slate-800/80 px-5 py-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <Terminal className="w-3.5 h-3.5 text-lux-400" />
                        <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
                          Pipeline Step Logs & Execution Trace
                        </h4>
                      </div>
                      <span className="text-[11px] text-slate-500 font-mono">
                        {run.run_log?.length || 0} steps executed
                      </span>
                    </div>

                    {(!run.run_log || run.run_log.length === 0) ? (
                      <p className="text-xs text-slate-500 italic py-2">
                        No individual step logs recorded for this execution run.
                      </p>
                    ) : (
                      <div className="overflow-x-auto border border-slate-800 rounded-lg">
                        <table className="w-full text-left text-xs">
                          <thead className="bg-slate-900/90 text-slate-400 font-medium border-b border-slate-800">
                            <tr>
                              <th className="py-2.5 px-3">#</th>
                              <th className="py-2.5 px-3">Step Identifier</th>
                              <th className="py-2.5 px-3">Status</th>
                              <th className="py-2.5 px-3">Records Processed</th>
                              <th className="py-2.5 px-3">Step Duration</th>
                              <th className="py-2.5 px-3">Duration Share</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-800/60 font-mono">
                            {run.run_log.map((step: PipelineStepLog, stepIdx: number) => {
                              const stepDurationPct =
                                run.duration_ms > 0
                                  ? Math.round((step.duration_ms / run.duration_ms) * 100)
                                  : 0;

                              return (
                                <tr key={stepIdx} className="hover:bg-slate-900/50">
                                  <td className="py-2 px-3 text-slate-500">{stepIdx + 1}</td>
                                  <td className="py-2 px-3 font-semibold text-slate-200">
                                    {step.step}
                                  </td>
                                  <td className="py-2 px-3">
                                    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[11px] font-semibold bg-emerald-950/60 text-emerald-300 border border-emerald-500/30">
                                      <CheckCircle2 className="w-2.5 h-2.5 text-emerald-400" />
                                      {step.status}
                                    </span>
                                  </td>
                                  <td className="py-2 px-3 text-slate-300">
                                    {step.records.toLocaleString()} rows
                                  </td>
                                  <td className="py-2 px-3 text-slate-300">
                                    {formatDuration(step.duration_ms)} ({step.duration_ms.toLocaleString()} ms)
                                  </td>
                                  <td className="py-2 px-3 min-w-[120px]">
                                    <div className="flex items-center gap-2">
                                      <div className="w-16 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                                        <div
                                          className="h-full bg-lux-500 rounded-full"
                                          style={{ width: `${Math.max(stepDurationPct, 4)}%` }}
                                        />
                                      </div>
                                      <span className="text-[11px] text-slate-500">
                                        {stepDurationPct}%
                                      </span>
                                    </div>
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
