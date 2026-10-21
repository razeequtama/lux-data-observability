import React from 'react';
import {
  AlertOctagon,
  Terminal,
  ShieldAlert,
  ArrowRight,
} from 'lucide-react';
import { PipelineRun } from '../../types';

interface DualStatusCalloutProps {
  run?: PipelineRun | null;
  onTraceImpact?: () => void;
  onViewLogs?: () => void;
}

export const DualStatusCallout: React.FC<DualStatusCalloutProps> = ({
  run,
  onTraceImpact,
  onViewLogs,
}) => {
  if (!run) return null;

  const isSuccessCompute =
    run.execution_status === 'COMPLETED_SUCCESS' || run.execution_status === 'SUCCESS';
  const isCorruptedQuality =
    run.quality_health === 'CORRUPTED' || run.quality_health === 'DEGRADED';

  // Only show this prominent callout if there is a divergence between compute and quality
  if (!isSuccessCompute || !isCorruptedQuality) {
    return null;
  }

  return (
    <div
      role="region"
      aria-label="Compute vs Quality Discrepancy Alert"
      className="bg-gradient-to-r from-slate-900 via-rose-950/20 to-slate-900 border-2 border-rose-500/40 rounded-xl p-5 shadow-lg shadow-rose-950/20 relative overflow-hidden"
    >
      {/* Background accent glow */}
      <div className="absolute -top-12 -right-12 w-48 h-48 bg-rose-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 relative z-10">
        <div className="space-y-2 max-w-3xl">
          <div className="flex flex-wrap items-center gap-2.5">
            <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold bg-rose-500/20 border border-rose-500/40 text-rose-300">
              <ShieldAlert className="w-3.5 h-3.5 mr-1.5 text-rose-400" />
              ADR-006 Dual-Dimension Anomaly
            </span>
            <span className="text-xs text-slate-400">
              Run ID: <span className="font-mono text-slate-200">{run.id}</span>
            </span>
          </div>

          <h2 className="text-lg sm:text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <AlertOctagon className="w-5 h-5 text-rose-400 shrink-0" />
            <span>Execution Succeeded (Exit 0) but Data Quality is Corrupted</span>
          </h2>

          <p className="text-sm text-slate-300 leading-relaxed">
            The ETL orchestration job terminated cleanly with exit code 0, yet validation engines
            detected critical data anomalies. Traditional orchestrator monitoring remained green
            while corrupted revenue metrics and inventory figures propagated downstream.
          </p>

          <div className="flex flex-wrap items-center gap-4 pt-1 text-xs text-slate-400">
            <span className="flex items-center text-slate-300">
              <span className="w-1.5 h-1.5 rounded-full bg-rose-400 mr-1.5" />
              15 Duplicate Orders Ingested
            </span>
            <span className="flex items-center text-slate-300">
              <span className="w-1.5 h-1.5 rounded-full bg-rose-400 mr-1.5" />
              24 Orphaned Line Items
            </span>
            <span className="flex items-center text-slate-300">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mr-1.5" />
              5.99h Ingestion Gap in Sunday Partition
            </span>
          </div>
        </div>

        {/* Status badges & Quick Actions */}
        <div className="flex flex-col sm:flex-row lg:flex-col items-start sm:items-center lg:items-end gap-3 shrink-0">
          <div className="flex items-center gap-2">
            {/* Compute Status */}
            <div
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-950/60 border border-emerald-500/40 text-emerald-300 text-xs font-medium"
              title="Compute Execution: Exit Code 0"
            >
              <Terminal className="w-3.5 h-3.5 text-emerald-400" />
              <span>Compute: {run.execution_status} (Exit 0)</span>
            </div>

            {/* Quality Status */}
            <div
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-950/80 border border-rose-500/60 text-rose-300 text-xs font-semibold animate-pulse"
              title="Data Quality Health: Corrupted"
            >
              <AlertOctagon className="w-3.5 h-3.5 text-rose-400" />
              <span>Quality: {run.quality_health}</span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {onViewLogs && (
              <button
                type="button"
                onClick={onViewLogs}
                className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-colors flex items-center gap-1.5 focus:outline-none focus:ring-2 focus:ring-lux-500"
              >
                <Terminal className="w-3.5 h-3.5 text-slate-400" />
                <span>View Step Logs</span>
              </button>
            )}
            {onTraceImpact && (
              <button
                type="button"
                onClick={onTraceImpact}
                className="px-3 py-1.5 rounded-lg bg-lux-700 hover:bg-lux-600 text-white text-xs font-medium shadow-sm transition-colors flex items-center gap-1.5 focus:outline-none focus:ring-2 focus:ring-lux-400"
              >
                <span>Trace Blast Radius</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
