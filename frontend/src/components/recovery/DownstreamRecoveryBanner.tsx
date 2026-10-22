import React from 'react';
import { ShieldCheck, AlertTriangle, XCircle, GitFork, ArrowRight } from 'lucide-react';
import { DownstreamRecoveryStatus } from '../../types';

export interface DownstreamRecoveryBannerProps {
  status: DownstreamRecoveryStatus;
  onNavigateToLineage?: () => void;
}

export const DownstreamRecoveryBanner: React.FC<DownstreamRecoveryBannerProps> = ({
  status,
  onNavigateToLineage,
}) => {
  const isHealthy = status === 'ALL_ASSETS_HEALTHY';
  const isPartial = status === 'PARTIALLY_RECOVERED';

  if (isHealthy) {
    return (
      <div
        role="region"
        aria-label="Downstream Asset Recovery Status"
        data-testid="downstream-recovery-banner"
        className="rounded-xl border border-emerald-500/40 bg-gradient-to-r from-emerald-950/60 via-slate-900/80 to-emerald-950/40 p-6 shadow-lg shadow-emerald-950/20"
      >
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start space-x-4">
            <div className="p-3 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 shrink-0">
              <ShieldCheck className="w-8 h-8" />
            </div>
            <div className="space-y-1">
              <div className="flex items-center space-x-2">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 uppercase tracking-wide">
                  Recovery Verified
                </span>
                <span className="text-xs font-mono text-emerald-400/80">
                  DAG Status: ALL_ASSETS_HEALTHY
                </span>
              </div>
              <h2 className="text-lg font-bold text-white tracking-tight">
                Downstream Trust Restored: All Lineage Assets Healthy
              </h2>
              <p className="text-sm text-slate-300 max-w-3xl leading-relaxed">
                Re-validation with clean fixtures confirmed zero data quality failures. Downstream
                derived tables (<code className="text-xs font-mono text-emerald-300">dim_orders</code>, <code className="text-xs font-mono text-emerald-300">fct_order_items</code>, <code className="text-xs font-mono text-emerald-300">dim_inventory</code>, <code className="text-xs font-mono text-emerald-300">agg_daily_revenue</code>), business metrics, and the <strong className="text-white">Executive Monday Dashboard</strong> have all returned to verified <span className="text-emerald-400 font-semibold">HEALTHY</span> status.
              </p>
            </div>
          </div>

          {onNavigateToLineage && (
            <div className="shrink-0 pt-2 md:pt-0">
              <button
                type="button"
                onClick={onNavigateToLineage}
                className="inline-flex items-center px-4 py-2.5 rounded-lg text-sm font-semibold bg-emerald-600 hover:bg-emerald-500 text-white shadow-md shadow-emerald-900/30 transition-all hover:scale-[1.02] active:scale-[0.98] focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:ring-offset-2 focus:ring-offset-slate-900 space-x-2"
                data-testid="banner-navigate-lineage-btn"
              >
                <GitFork className="w-4 h-4" />
                <span>View Restored Lineage DAG</span>
                <ArrowRight className="w-4 h-4 ml-1 opacity-70" />
              </button>
            </div>
          )}
        </div>
      </div>
    );
  }

  if (isPartial) {
    return (
      <div
        role="region"
        aria-label="Downstream Asset Recovery Status"
        data-testid="downstream-recovery-banner"
        className="rounded-xl border border-amber-500/40 bg-gradient-to-r from-amber-950/60 via-slate-900/80 to-amber-950/40 p-6 shadow-lg shadow-amber-950/20"
      >
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start space-x-4">
            <div className="p-3 rounded-xl bg-amber-500/15 border border-amber-500/30 text-amber-400 shrink-0">
              <AlertTriangle className="w-8 h-8" />
            </div>
            <div className="space-y-1">
              <div className="flex items-center space-x-2">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30 uppercase tracking-wide">
                  Partial Recovery
                </span>
                <span className="text-xs font-mono text-amber-400/80">
                  DAG Status: PARTIALLY_RECOVERED
                </span>
              </div>
              <h2 className="text-lg font-bold text-white tracking-tight">
                Partial Recovery Detected: Unresolved Finding(s) Remain
              </h2>
              <p className="text-sm text-slate-300 max-w-3xl leading-relaxed">
                Some validation checks were resolved, but one or more rules still failed. Downstream
                assets traversing unresolved dependencies remain in an impacted or degraded state.
              </p>
            </div>
          </div>

          {onNavigateToLineage && (
            <div className="shrink-0 pt-2 md:pt-0">
              <button
                type="button"
                onClick={onNavigateToLineage}
                className="inline-flex items-center px-4 py-2.5 rounded-lg text-sm font-semibold bg-amber-600 hover:bg-amber-500 text-white shadow-md shadow-amber-900/30 transition-all hover:scale-[1.02] active:scale-[0.98] focus:outline-none focus:ring-2 focus:ring-amber-400 focus:ring-offset-2 focus:ring-offset-slate-900 space-x-2"
                data-testid="banner-navigate-lineage-btn"
              >
                <GitFork className="w-4 h-4" />
                <span>Inspect Lineage Impact</span>
              </button>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Default: RECOVERY_FAILED or unknown failure
  return (
    <div
      role="region"
      aria-label="Downstream Asset Recovery Status"
      data-testid="downstream-recovery-banner"
      className="rounded-xl border border-rose-500/40 bg-gradient-to-r from-rose-950/60 via-slate-900/80 to-rose-950/40 p-6 shadow-lg shadow-rose-950/20"
    >
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-start space-x-4">
          <div className="p-3 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-400 shrink-0">
            <XCircle className="w-8 h-8" />
          </div>
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/20 text-rose-300 border border-rose-500/30 uppercase tracking-wide">
                Recovery Incomplete
              </span>
              <span className="text-xs font-mono text-rose-400/80">
                DAG Status: RECOVERY_FAILED
              </span>
            </div>
            <h2 className="text-lg font-bold text-white tracking-tight">
              Recovery Incomplete: Checks Failing on New Fixture
            </h2>
            <p className="text-sm text-slate-300 max-w-3xl leading-relaxed">
              Target fixture re-execution failed to resolve the detected data quality defects. Downstream
              assets remain flagged as corrupted or degraded.
            </p>
          </div>
        </div>

        {onNavigateToLineage && (
          <div className="shrink-0 pt-2 md:pt-0">
            <button
              type="button"
              onClick={onNavigateToLineage}
              className="inline-flex items-center px-4 py-2.5 rounded-lg text-sm font-semibold bg-rose-600 hover:bg-rose-500 text-white shadow-md shadow-rose-900/30 transition-all hover:scale-[1.02] active:scale-[0.98] focus:outline-none focus:ring-2 focus:ring-rose-400 focus:ring-offset-2 focus:ring-offset-slate-900 space-x-2"
              data-testid="banner-navigate-lineage-btn"
            >
              <GitFork className="w-4 h-4" />
              <span>Inspect Corrupted Nodes</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

