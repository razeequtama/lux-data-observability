import React, { useState } from 'react';
import {
  RefreshCw,
  Loader2,
  ShieldCheck,
  GitFork,
  ArrowRight,
  Database,
  History,
  FileCheck2,
} from 'lucide-react';
import { verifyRecovery } from '../../api/recovery';
import { RecoveryComparison } from '../../types';
import { DownstreamRecoveryBanner } from './DownstreamRecoveryBanner';
import { ComparisonMetricCards } from './ComparisonMetricCards';
import { ResolvedChecksList } from './ResolvedChecksList';
import { AlertBanner } from '../common/AlertBanner';

export interface RecoveryDiffViewProps {
  scenarioId: string;
  initialComparison?: RecoveryComparison | null;
  onNavigateToLineage?: () => void;
  onNavigateToValidations?: () => void;
  onRecoveryVerified?: (comparison: RecoveryComparison) => void;
}

export const RecoveryDiffView: React.FC<RecoveryDiffViewProps> = ({
  scenarioId,
  initialComparison = null,
  onNavigateToLineage,
  onNavigateToValidations,
  onRecoveryVerified,
}) => {
  const [comparison, setComparison] = useState<RecoveryComparison | null>(initialComparison);
  const [isVerifying, setIsVerifying] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [lastVerifiedAt, setLastVerifiedAt] = useState<Date | null>(null);

  const handleVerify = async () => {
    setIsVerifying(true);
    setError(null);

    try {
      const response = await verifyRecovery(scenarioId, 'corrected');
      setComparison(response.comparison);
      setLastVerifiedAt(new Date());
      if (onRecoveryVerified) {
        onRecoveryVerified(response.comparison);
      }
    } catch (err) {
      console.error('Recovery verification failed:', err);
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to execute recovery verification. Please ensure the backend is running.'
      );
    } finally {
      setIsVerifying(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="recovery-diff-view">
      {/* Top Action Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-lg font-bold text-white tracking-tight flex items-center space-x-2">
              <FileCheck2 className="w-5 h-5 text-lux-400" />
              <span>Recovery Verification & Diff Inspector</span>
            </h2>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
              {scenarioId}
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Swap to clean fixtures, re-execute deterministic quality rules, and verify downstream lineage trust.
          </p>
        </div>

        <div className="flex items-center space-x-3 w-full sm:w-auto justify-end">
          {comparison && (
            <button
              type="button"
              onClick={handleVerify}
              disabled={isVerifying}
              className="inline-flex items-center px-3.5 py-2 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors disabled:opacity-50 space-x-2"
              data-testid="reverify-recovery-btn"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isVerifying ? 'animate-spin text-lux-400' : ''}`} />
              <span>Re-verify Recovery</span>
            </button>
          )}

          {!comparison && (
            <button
              type="button"
              onClick={handleVerify}
              disabled={isVerifying}
              className="inline-flex items-center px-5 py-2.5 rounded-lg text-sm font-semibold bg-lux-700 hover:bg-lux-600 text-white shadow-md shadow-lux-900/30 transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none space-x-2"
              data-testid="verify-recovery-btn"
            >
              {isVerifying ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-white" />
                  <span>Verifying Recovery...</span>
                </>
              ) : (
                <>
                  <RefreshCw className="w-4 h-4" />
                  <span>Verify Recovery</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div data-testid="recovery-error-alert">
          <AlertBanner
            type="error"
            message="Recovery Verification Failed"
            details={error}
            onClose={() => setError(null)}
          />
        </div>
      )}

      {/* Loading State Banner */}
      {isVerifying && (
        <div
          data-testid="recovery-loading-indicator"
          className="rounded-xl border border-lux-700/40 bg-slate-900/80 p-8 text-center space-y-4"
        >
          <div className="w-12 h-12 mx-auto rounded-full bg-lux-900/60 border border-lux-700/40 flex items-center justify-center text-lux-400 animate-pulse">
            <Loader2 className="w-6 h-6 animate-spin" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-bold text-white">
              Executing Recovery Verification Workflow...
            </h3>
            <p className="text-xs text-slate-400 max-w-md mx-auto">
              Swapping scenario files to <code className="text-lux-300 font-mono">corrected/</code> fixtures, re-evaluating quality rules, recalculating blast radius, and assessing downstream Lineage DAG health.
            </p>
          </div>
        </div>
      )}

      {/* Initial Callout (Before verification has been triggered) */}
      {!comparison && !isVerifying && (
        <div
          data-testid="recovery-initial-callout"
          className="rounded-xl border border-slate-800 bg-slate-900/70 p-8 space-y-6"
        >
          <div className="flex items-start space-x-4">
            <div className="p-3 rounded-xl bg-lux-900/40 border border-lux-700/30 text-lux-400 shrink-0">
              <ShieldCheck className="w-8 h-8" />
            </div>
            <div className="space-y-2">
              <h3 className="text-lg font-bold text-white">
                Ready to Verify Scenario Recovery
              </h3>
              <p className="text-sm text-slate-300 leading-relaxed max-w-3xl">
                The incident investigation identified 4 data defects across raw source datasets: duplicate order identifiers in <code className="text-xs font-mono text-lux-300">orders.csv</code>, orphaned foreign keys in <code className="text-xs font-mono text-lux-300">order_items.csv</code>, negative quantities in <code className="text-xs font-mono text-lux-300">inventory.csv</code>, and an ingestion temporal gap.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t border-slate-800 text-xs">
            <div className="rounded-lg bg-slate-950/60 p-4 border border-slate-800 space-y-2">
              <div className="flex items-center space-x-2 text-lux-400 font-semibold">
                <Database className="w-4 h-4" />
                <span>1. Clean Fixture Swap</span>
              </div>
              <p className="text-slate-400 leading-normal">
                Replaces defective source tables with corrected, deduplicated, and reconciled datasets in-place.
              </p>
            </div>

            <div className="rounded-lg bg-slate-950/60 p-4 border border-slate-800 space-y-2">
              <div className="flex items-center space-x-2 text-lux-400 font-semibold">
                <RefreshCw className="w-4 h-4" />
                <span>2. Deterministic Re-Validation</span>
              </div>
              <p className="text-slate-400 leading-normal">
                Executes all validation rules against corrected files to prove 0 failed checks remain.
              </p>
            </div>

            <div className="rounded-lg bg-slate-950/60 p-4 border border-slate-800 space-y-2">
              <div className="flex items-center space-x-2 text-lux-400 font-semibold">
                <GitFork className="w-4 h-4" />
                <span>3. Downstream DAG Audit</span>
              </div>
              <p className="text-slate-400 leading-normal">
                Evaluates the entire 16-node Lineage DAG to ensure downstream executive dashboards return to HEALTHY status.
              </p>
            </div>
          </div>

          <div className="pt-2 flex items-center justify-start">
            <button
              type="button"
              onClick={handleVerify}
              disabled={isVerifying}
              className="inline-flex items-center px-6 py-3 rounded-lg text-sm font-semibold bg-lux-700 hover:bg-lux-600 text-white shadow-lg shadow-lux-900/30 transition-all hover:scale-[1.02] active:scale-[0.98] space-x-2.5"
              data-testid="verify-recovery-cta-btn"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Verify Recovery Now</span>
              <ArrowRight className="w-4 h-4 ml-1 opacity-70" />
            </button>
          </div>
        </div>
      )}

      {/* Comparison Results */}
      {comparison && (
        <div className="space-y-6" data-testid="recovery-comparison-results">
          {/* 1. Downstream Asset Recovery Banner */}
          <DownstreamRecoveryBanner
            status={comparison.downstream_recovery_status}
            onNavigateToLineage={onNavigateToLineage}
          />

          {/* 2. Before vs After Metric Cards */}
          <ComparisonMetricCards
            previousRun={comparison.previous_run}
            currentRun={comparison.current_run}
          />

          {/* 3. Resolved Quality Checks Checklist */}
          <ResolvedChecksList items={comparison.resolved_findings} />

          {/* 4. Quick Navigation Bar */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs">
            <div className="flex items-center space-x-2 text-slate-400">
              <History className="w-4 h-4 text-slate-500" />
              <span>
                Recovery verified at {lastVerifiedAt ? lastVerifiedAt.toLocaleTimeString() : 'recently'}. Scenario is running in clean corrected state.
              </span>
            </div>

            <div className="flex items-center space-x-3 shrink-0">
              {onNavigateToValidations && (
                <button
                  type="button"
                  onClick={onNavigateToValidations}
                  className="px-3.5 py-1.5 rounded-lg font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors inline-flex items-center space-x-1.5"
                  data-testid="navigate-validations-btn"
                >
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Inspect Validations</span>
                </button>
              )}
              {onNavigateToLineage && (
                <button
                  type="button"
                  onClick={onNavigateToLineage}
                  className="px-3.5 py-1.5 rounded-lg font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors inline-flex items-center space-x-1.5"
                  data-testid="navigate-lineage-btn"
                >
                  <GitFork className="w-3.5 h-3.5 text-lux-400" />
                  <span>Inspect Lineage DAG</span>
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

