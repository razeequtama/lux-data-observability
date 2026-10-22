import React from 'react';
import {
  AlertOctagon,
  CheckCircle2,
  Clock,
  ArrowRight,
  Sparkles,
} from 'lucide-react';
import { RecoveryRunSummary } from '../../types';

export interface ComparisonMetricCardsProps {
  previousRun: RecoveryRunSummary;
  currentRun: RecoveryRunSummary;
}

export const ComparisonMetricCards: React.FC<ComparisonMetricCardsProps> = ({
  previousRun,
  currentRun,
}) => {
  const prevHealthColor =
    previousRun.quality_health === 'HEALTHY'
      ? 'text-emerald-400 bg-emerald-500/15 border-emerald-500/30'
      : previousRun.quality_health === 'DEGRADED'
      ? 'text-amber-400 bg-amber-500/15 border-amber-500/30'
      : 'text-rose-400 bg-rose-500/15 border-rose-500/30';

  const currHealthColor =
    currentRun.quality_health === 'HEALTHY'
      ? 'text-emerald-400 bg-emerald-500/15 border-emerald-500/30'
      : currentRun.quality_health === 'DEGRADED'
      ? 'text-amber-400 bg-amber-500/15 border-amber-500/30'
      : 'text-rose-400 bg-rose-500/15 border-rose-500/30';

  const durationDiff =
    previousRun.execution_duration_ms !== null &&
    previousRun.execution_duration_ms !== undefined &&
    currentRun.execution_duration_ms !== null &&
    currentRun.execution_duration_ms !== undefined
      ? currentRun.execution_duration_ms - previousRun.execution_duration_ms
      : null;

  return (
    <div
      role="region"
      aria-label="Before and After Run Comparison"
      data-testid="comparison-metric-cards"
      className="space-y-4"
    >
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 relative">
        {/* Central visual indicator on desktop */}
        <div className="hidden md:flex absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-10 w-10 h-10 rounded-full bg-slate-900 border border-slate-700 items-center justify-center text-slate-300 shadow-md">
          <ArrowRight className="w-5 h-5 text-lux-400" />
        </div>

        {/* 1. BEFORE: Defective Run */}
        <div
          data-testid="before-run-card"
          className="rounded-xl border border-rose-500/30 bg-slate-900/90 p-5 shadow-sm space-y-4 relative overflow-hidden"
        >
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-rose-500 to-rose-600/60" />

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <span className="text-xs font-semibold text-rose-400 uppercase tracking-wider flex items-center space-x-1.5">
                <AlertOctagon className="w-3.5 h-3.5" />
                <span>Before Recovery (Baseline)</span>
              </span>
              <h3 className="text-base font-bold text-white">
                Fixture: <span className="font-mono text-rose-300">{previousRun.fixture_version}</span>
              </h3>
            </div>
            <span
              data-testid="before-health-badge"
              className={`px-2.5 py-1 rounded-full text-xs font-semibold border ${prevHealthColor}`}
            >
              {previousRun.quality_health}
            </span>
          </div>

          <div className="grid grid-cols-3 gap-3 pt-2 border-t border-slate-800 text-center">
            <div className="bg-slate-950/60 rounded-lg p-2.5 border border-slate-800/80">
              <span className="text-[11px] text-slate-400 block font-medium">Failed Checks</span>
              <span
                data-testid="before-failed-count"
                className="text-xl font-bold font-mono text-rose-400"
              >
                {previousRun.failed_checks}
              </span>
            </div>
            <div className="bg-slate-950/60 rounded-lg p-2.5 border border-slate-800/80">
              <span className="text-[11px] text-slate-400 block font-medium">Passed Checks</span>
              <span className="text-xl font-bold font-mono text-slate-200">
                {previousRun.passed_checks ?? (previousRun.total_checks ? previousRun.total_checks - previousRun.failed_checks : '-')}
              </span>
            </div>
            <div className="bg-slate-950/60 rounded-lg p-2.5 border border-slate-800/80">
              <span className="text-[11px] text-slate-400 block font-medium">Duration</span>
              <span className="text-xl font-bold font-mono text-slate-200">
                {previousRun.execution_duration_ms !== null && previousRun.execution_duration_ms !== undefined
                  ? `${previousRun.execution_duration_ms}ms`
                  : '-'}
              </span>
            </div>
          </div>

          <div className="flex items-center justify-between text-xs text-slate-400 font-mono pt-1">
            <span className="truncate max-w-[200px]" title={previousRun.run_id}>
              Run: {previousRun.run_id}
            </span>
            {previousRun.executed_at && (
              <span className="flex items-center space-x-1">
                <Clock className="w-3 h-3 text-slate-500" />
                <span>{new Date(previousRun.executed_at).toLocaleTimeString()}</span>
              </span>
            )}
          </div>
        </div>

        {/* 2. AFTER: Corrected Run */}
        <div
          data-testid="after-run-card"
          className="rounded-xl border border-emerald-500/30 bg-slate-900/90 p-5 shadow-sm space-y-4 relative overflow-hidden"
        >
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-emerald-500 to-emerald-600/60" />

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider flex items-center space-x-1.5">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>After Recovery (Clean Fixtures)</span>
              </span>
              <h3 className="text-base font-bold text-white">
                Fixture: <span className="font-mono text-emerald-300">{currentRun.fixture_version}</span>
              </h3>
            </div>
            <span
              data-testid="after-health-badge"
              className={`px-2.5 py-1 rounded-full text-xs font-semibold border ${currHealthColor}`}
            >
              {currentRun.quality_health}
            </span>
          </div>

          <div className="grid grid-cols-3 gap-3 pt-2 border-t border-slate-800 text-center">
            <div className="bg-slate-950/60 rounded-lg p-2.5 border border-slate-800/80">
              <span className="text-[11px] text-slate-400 block font-medium">Failed Checks</span>
              <span
                data-testid="after-failed-count"
                className={`text-xl font-bold font-mono ${
                  currentRun.failed_checks === 0 ? 'text-emerald-400' : 'text-rose-400'
                }`}
              >
                {currentRun.failed_checks}
              </span>
            </div>
            <div className="bg-slate-950/60 rounded-lg p-2.5 border border-slate-800/80">
              <span className="text-[11px] text-slate-400 block font-medium">Passed Checks</span>
              <span className="text-xl font-bold font-mono text-emerald-400">
                {currentRun.passed_checks ?? (currentRun.total_checks ? currentRun.total_checks - currentRun.failed_checks : '-')}
              </span>
            </div>
            <div className="bg-slate-950/60 rounded-lg p-2.5 border border-slate-800/80">
              <span className="text-[11px] text-slate-400 block font-medium">Duration</span>
              <span className="text-xl font-bold font-mono text-slate-200">
                {currentRun.execution_duration_ms !== null && currentRun.execution_duration_ms !== undefined
                  ? `${currentRun.execution_duration_ms}ms`
                  : '-'}
              </span>
            </div>
          </div>

          <div className="flex items-center justify-between text-xs text-slate-400 font-mono pt-1">
            <span className="truncate max-w-[200px]" title={currentRun.run_id}>
              Run: {currentRun.run_id}
            </span>
            {currentRun.executed_at && (
              <span className="flex items-center space-x-1">
                <Clock className="w-3 h-3 text-slate-500" />
                <span>{new Date(currentRun.executed_at).toLocaleTimeString()}</span>
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Execution Performance & Resolution Delta Footer */}
      <div className="rounded-lg bg-slate-900/60 border border-slate-800 px-4 py-3 flex flex-col sm:flex-row items-start sm:items-center justify-between text-xs text-slate-300 gap-2">
        <div className="flex items-center space-x-2">
          <Sparkles className="w-4 h-4 text-lux-400 shrink-0" />
          <span>
            Resolution Delta:{' '}
            <strong className="text-emerald-400">
              {previousRun.failed_checks - currentRun.failed_checks} check(s) resolved
            </strong>{' '}
            ({previousRun.failed_checks} failed → {currentRun.failed_checks} failed)
          </span>
        </div>
        {durationDiff !== null && (
          <div className="flex items-center space-x-1.5 font-mono text-slate-400">
            <Clock className="w-3.5 h-3.5" />
            <span>
              Execution duration: {previousRun.execution_duration_ms}ms vs {currentRun.execution_duration_ms}ms{' '}
              ({durationDiff <= 0 ? `${Math.abs(durationDiff)}ms faster` : `+${durationDiff}ms`})
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

