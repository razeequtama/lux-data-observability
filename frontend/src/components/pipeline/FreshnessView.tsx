import React from 'react';
import {
  Clock,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  Calendar,
  AlertOctagon,
  Activity,
  Layers,
} from 'lucide-react';
import { FreshnessCheck } from '../../types';

interface FreshnessViewProps {
  freshnessChecks: FreshnessCheck[];
  isLoading?: boolean;
  onRefresh?: () => void;
}

function formatTimestamp(isoString?: string | null): string {
  if (!isoString) return 'None recorded';
  try {
    const d = new Date(isoString);
    return d.toISOString().replace('T', ' ').substring(0, 19) + ' UTC';
  } catch {
    return isoString;
  }
}

export const FreshnessView: React.FC<FreshnessViewProps> = ({
  freshnessChecks,
  isLoading = false,
  onRefresh,
}) => {
  if (isLoading) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center space-y-3">
        <Activity className="w-8 h-8 text-lux-400 animate-spin mx-auto" />
        <p className="text-sm text-slate-400">Loading dataset partition freshness checkpoints...</p>
      </div>
    );
  }

  if (freshnessChecks.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center space-y-2">
        <Layers className="w-8 h-8 text-slate-600 mx-auto" />
        <h3 className="text-sm font-semibold text-slate-300">No Freshness Checks Found</h3>
        <p className="text-xs text-slate-500">
          No partition freshness monitors configured for this scenario.
        </p>
      </div>
    );
  }

  const totalChecks = freshnessChecks.length;
  const staleChecks = freshnessChecks.filter((c) => c.status === 'STALE');
  const freshChecks = freshnessChecks.filter((c) => c.status === 'FRESH');
  const maxHoursBehind = Math.max(...freshnessChecks.map((c) => c.hours_behind || 0));

  return (
    <div className="space-y-6" data-testid="freshness-view">
      {/* Overview Metric Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Partitions Monitored</span>
            <Layers className="w-4 h-4 text-slate-500" />
          </div>
          <div className="text-2xl font-bold text-white mt-2">{totalChecks}</div>
          <div className="text-xs text-slate-500 mt-1">Configured dataset SLAs</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>SLA Compliant</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400 mt-2">{freshChecks.length}</div>
          <div className="text-xs text-slate-500 mt-1">Up to date partitions</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Stale / SLA Breached</span>
            <AlertTriangle className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-bold text-rose-400 mt-2">{staleChecks.length}</div>
          <div className="text-xs text-rose-500/80 mt-1">Partitions lagging behind SLA</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Max Lag Behind SLA</span>
            <Clock className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-amber-400 mt-2">
            {maxHoursBehind > 0 ? `${maxHoursBehind.toFixed(2)}h` : '0h'}
          </div>
          <div className="text-xs text-slate-500 mt-1">Greatest observed delay</div>
        </div>
      </div>

      {/* Freshness Partition Cards Grid */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-semibold text-white flex items-center gap-2">
              <Clock className="w-4 h-4 text-lux-400" />
              <span>Dataset Partition Freshness & SLA Status</span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Continuous monitoring comparing observed latest partition timestamps against scheduled SLA expectations
            </p>
          </div>
          {onRefresh && (
            <button
              type="button"
              onClick={onRefresh}
              className="text-xs text-lux-400 hover:text-lux-300 font-medium transition-colors"
            >
              Refresh Status
            </button>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {freshnessChecks.map((check) => {
            const isStale = check.status === 'STALE';
            const isFresh = check.status === 'FRESH';

            return (
              <div
                key={check.dataset_id}
                data-testid={`freshness-card-${check.dataset_id}`}
                className={`bg-slate-900 border rounded-xl p-5 transition-all shadow-sm ${
                  isStale
                    ? 'border-rose-500/50 bg-gradient-to-b from-slate-900 via-rose-950/10 to-slate-900 shadow-rose-950/20'
                    : isFresh
                    ? 'border-slate-800 hover:border-emerald-500/30'
                    : 'border-slate-800'
                }`}
              >
                {/* Card Header: Dataset Name + Status Badge */}
                <div className="flex items-start justify-between gap-3 mb-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <h4 className="text-base font-bold text-white font-mono">
                        {check.dataset_name}
                      </h4>
                      <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                        {check.dataset_id}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-slate-400">
                      <Clock className="w-3.5 h-3.5 text-slate-500" />
                      <span>Configured SLA: <strong className="text-slate-200">{check.sla_hours} hours</strong></span>
                    </div>
                  </div>

                  {/* Status Badge */}
                  <span
                    data-testid={`badge-freshness-${check.dataset_id}`}
                    className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-bold border ${
                      isFresh
                        ? 'bg-emerald-950/70 text-emerald-300 border-emerald-500/40'
                        : isStale
                        ? 'bg-rose-950/90 text-rose-300 border-rose-500/60 shadow-sm shadow-rose-950/40 animate-pulse'
                        : 'bg-slate-800 text-slate-400 border-slate-700'
                    }`}
                  >
                    {isFresh ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    ) : isStale ? (
                      <AlertOctagon className="w-3.5 h-3.5 text-rose-400" />
                    ) : (
                      <HelpCircle className="w-3.5 h-3.5 text-slate-400" />
                    )}
                    <span>{check.status}</span>
                  </span>
                </div>

                {/* Staleness / Lag Warning Box */}
                {isStale && (
                  <div className="mb-4 p-3 rounded-lg bg-rose-950/40 border border-rose-500/30 text-xs text-rose-200 space-y-1">
                    <div className="font-semibold flex items-center gap-1.5 text-rose-300">
                      <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
                      <span>SLA Breach: {check.hours_behind.toFixed(2)} hours behind schedule</span>
                    </div>
                    <p className="text-slate-300 leading-relaxed text-[11px]">
                      Partition timestamp gap detected. Incoming data halted at{' '}
                      <span className="font-mono font-medium text-white">
                        {formatTimestamp(check.observed_partition_timestamp)}
                      </span>
                      , leaving expected records past 18:00 UTC uningested.
                    </p>
                  </div>
                )}

                {/* Timestamp Details Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-3 border-t border-slate-800/80 text-xs">
                  <div className="space-y-1">
                    <span className="text-slate-500 flex items-center gap-1 text-[11px]">
                      <Calendar className="w-3 h-3 text-slate-600" />
                      Expected SLA Cutoff
                    </span>
                    <p className="font-mono text-slate-200 text-[11px] truncate" title={check.expected_partition_timestamp}>
                      {formatTimestamp(check.expected_partition_timestamp)}
                    </p>
                  </div>

                  <div className="space-y-1">
                    <span className="text-slate-500 flex items-center gap-1 text-[11px]">
                      <Clock className="w-3 h-3 text-slate-600" />
                      Observed Partition Max
                    </span>
                    <p
                      className={`font-mono text-[11px] truncate ${
                        isStale ? 'text-rose-300 font-semibold' : 'text-slate-200'
                      }`}
                      title={check.observed_partition_timestamp || 'None'}
                    >
                      {formatTimestamp(check.observed_partition_timestamp)}
                    </p>
                  </div>
                </div>

                {/* Footer Check Time */}
                {check.checked_at && (
                  <div className="mt-3 pt-2 text-[10px] text-slate-500 flex items-center justify-between border-t border-slate-800/40">
                    <span>Evaluated at: {formatTimestamp(check.checked_at)}</span>
                    <span className="font-mono text-slate-400">
                      Lag: {check.hours_behind.toFixed(2)}h
                    </span>
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
