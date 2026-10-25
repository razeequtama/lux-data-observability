import React from 'react';
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  ShieldCheck,
  Zap,
} from 'lucide-react';
import { ValidationRunResponse } from '../../types';

interface ValidationSummaryCardsProps {
  run: ValidationRunResponse | null;
  isLoading?: boolean;
}

export const ValidationSummaryCards: React.FC<ValidationSummaryCardsProps> = ({
  run,
  isLoading = false,
}) => {
  const totalChecks = run?.total_checks ?? 0;
  const passedChecks = run?.passed_checks ?? 0;
  const failedChecks = run?.failed_checks ?? 0;
  const warningChecks = run?.warning_checks ?? 0;
  const durationMs = run?.execution_duration_ms ?? 0;

  const passRate =
    totalChecks > 0 ? Math.round((passedChecks / totalChecks) * 100) : 0;

  return (
    <div
      className="space-y-3"
      data-testid="validation-summary-cards"
      aria-label="Validation Run Execution Metrics"
    >
      {/* Top Meta Bar */}
      {run && (
        <div className="flex flex-wrap items-center justify-between text-xs text-slate-400 px-1 gap-2">
          <div className="flex items-center space-x-2">
            <span className="font-semibold text-slate-300">Run ID:</span>
            <code className="font-mono bg-slate-800 text-lux-300 px-1.5 py-0.5 rounded border border-slate-700">
              {run.run_id}
            </code>
            <span className="text-slate-600">|</span>
            <span className="capitalize">
              Fixture: <strong className="text-slate-200">{run.fixture_version}</strong>
            </span>
          </div>
          <div className="flex items-center space-x-3">
            <span
              className={`inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider text-[11px] ${
                run.status === 'PASSED'
                  ? 'bg-status-healthy/15 text-status-healthy border border-status-healthy/30'
                  : run.status === 'FAILED'
                    ? 'bg-status-corrupted/15 text-status-corrupted border border-status-corrupted/30'
                    : 'bg-status-warning/15 text-status-warning border border-status-warning/30'
              }`}
            >
              {run.status === 'PASSED' && <CheckCircle2 className="w-3 h-3" />}
              {run.status === 'FAILED' && <XCircle className="w-3 h-3" />}
              {run.status === 'WARNING' && <AlertTriangle className="w-3 h-3" />}
              <span>{run.status}</span>
            </span>
            <span>
              Executed: {new Date(run.executed_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
            </span>
          </div>
        </div>
      )}

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3.5">
        {/* Total Checks */}
        <div
          data-testid="summary-total-checks"
          className="bg-[#0d0f1b]/80 backdrop-blur-xl border border-white/[0.07] border-t-purple-400/30 rounded-2xl p-4 shadow-xl shadow-black/40 relative overflow-hidden transition-all duration-200 hover:border-purple-400/40 hover:shadow-[0_0_20px_rgba(168,85,247,0.15)]"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400">Total Checks</span>
            <div className="p-1.5 rounded-lg bg-slate-900/80 text-lux-400 border border-white/[0.08] shadow-inner">
              <ShieldCheck className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-2xl font-black text-white tracking-tight">
              {isLoading ? '...' : totalChecks}
            </span>
            <span className="text-xs text-slate-400 font-mono">rules</span>
          </div>
          <div className="mt-1 text-[11px] text-slate-400">
            {totalChecks > 0 ? `${passRate}% pass rate` : 'No checks executed'}
          </div>
        </div>

        {/* Passed Checks */}
        <div
          data-testid="summary-passed-checks"
          className="bg-[#0d0f1b]/80 backdrop-blur-xl border border-emerald-500/20 border-t-emerald-400/40 rounded-2xl p-4 shadow-xl shadow-black/40 relative overflow-hidden transition-all duration-200 hover:border-emerald-400/50 hover:shadow-[0_0_20px_rgba(16,185,129,0.15)]"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-emerald-400">Passed</span>
            <div className="p-1.5 rounded-lg bg-emerald-950/60 text-status-healthy border border-emerald-700/50 shadow-[0_0_8px_rgba(16,185,129,0.25)]">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-2xl font-black text-status-healthy tracking-tight">
              {isLoading ? '...' : passedChecks}
            </span>
            <span className="text-xs text-slate-400 font-mono">clean</span>
          </div>
          <div className="mt-1 text-[11px] text-slate-400">
            Compliant with expectations
          </div>
        </div>

        {/* Failed Checks — The Beacon */}
        <div
          data-testid="summary-failed-checks"
          className="bg-rose-950/20 backdrop-blur-xl border border-rose-500/30 border-t-rose-400/60 rounded-2xl p-4 shadow-xl shadow-black/40 relative overflow-hidden transition-all duration-200 hover:border-rose-400/60 hover:shadow-[0_0_25px_rgba(244,63,94,0.25)] ring-1 ring-rose-500/20"
        >
          {/* Subtle Beacon flare */}
          <div className="absolute -top-10 -right-10 w-24 h-24 bg-rose-500/15 rounded-full blur-xl pointer-events-none" />

          <div className="flex items-center justify-between relative z-10">
            <span className="text-xs font-semibold text-rose-300">Failed</span>
            <div className="p-1.5 rounded-lg bg-rose-950/70 text-status-corrupted border border-rose-600/50 shadow-[0_0_12px_rgba(244,63,94,0.4)]">
              <XCircle className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline space-x-2 relative z-10">
            <span className="text-2xl font-black text-status-corrupted tracking-tight">
              {isLoading ? '...' : failedChecks}
            </span>
            <span className="text-xs text-slate-400 font-mono">violations</span>
          </div>
          <div className="mt-1 text-[11px] text-slate-400 relative z-10">
            Requires active investigation
          </div>
        </div>

        {/* Warnings */}
        <div
          data-testid="summary-warning-checks"
          className="bg-[#0d0f1b]/80 backdrop-blur-xl border border-amber-500/20 border-t-amber-400/40 rounded-2xl p-4 shadow-xl shadow-black/40 relative overflow-hidden transition-all duration-200 hover:border-amber-400/50 hover:shadow-[0_0_20px_rgba(245,158,11,0.15)]"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-amber-400">Warnings</span>
            <div className="p-1.5 rounded-lg bg-amber-950/60 text-status-warning border border-amber-700/50">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-2xl font-black text-status-warning tracking-tight">
              {isLoading ? '...' : warningChecks}
            </span>
            <span className="text-xs text-slate-400 font-mono">alerts</span>
          </div>
          <div className="mt-1 text-[11px] text-slate-400">
            Anomalies below threshold
          </div>
        </div>

        {/* Duration */}
        <div
          data-testid="summary-duration"
          className="bg-[#0d0f1b]/80 backdrop-blur-xl border border-white/[0.07] border-t-purple-400/30 rounded-2xl p-4 shadow-xl shadow-black/40 relative overflow-hidden col-span-2 sm:col-span-1 transition-all duration-200 hover:border-purple-400/40 hover:shadow-[0_0_20px_rgba(168,85,247,0.15)]"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400">Duration</span>
            <div className="p-1.5 rounded-lg bg-slate-900/80 text-slate-300 border border-white/[0.08] shadow-inner">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-2xl font-black text-slate-200 tracking-tight font-mono">
              {isLoading ? '...' : durationMs}
            </span>
            <span className="text-xs text-slate-400 font-mono">ms</span>
          </div>
          <div className="mt-1 text-[11px] text-slate-400 flex items-center space-x-1">
            <Zap className="w-3 h-3 text-lux-400" />
            <span>Deterministic engine</span>
          </div>
        </div>
      </div>
    </div>
  );
};

