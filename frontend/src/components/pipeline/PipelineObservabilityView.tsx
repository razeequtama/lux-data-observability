import React, { useState, useEffect, useCallback } from 'react';
import {
  Clock,
  Layers,
  RefreshCw,
  AlertTriangle,
} from 'lucide-react';
import { listPipelineRuns, getPipelineFreshness } from '../../api';
import { PipelineRun, FreshnessCheck } from '../../types';
import { DualStatusCallout } from './DualStatusCallout';
import { PipelineHistoryTimeline } from './PipelineHistoryTimeline';
import { FreshnessView } from './FreshnessView';

interface PipelineObservabilityViewProps {
  scenarioId: string;
  onTraceImpact?: () => void;
}

export type PipelineViewSubTab = 'history' | 'freshness' | 'combined';

export const PipelineObservabilityView: React.FC<PipelineObservabilityViewProps> = ({
  scenarioId,
  onTraceImpact,
}) => {
  const [activeSubTab, setActiveSubTab] = useState<PipelineViewSubTab>('combined');
  const [runs, setRuns] = useState<PipelineRun[]>([]);
  const [freshnessChecks, setFreshnessChecks] = useState<FreshnessCheck[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [fetchedRuns, fetchedFreshness] = await Promise.all([
        listPipelineRuns({ scenarioId }),
        getPipelineFreshness({ scenarioId }),
      ]);
      setRuns(fetchedRuns);
      setFreshnessChecks(fetchedFreshness);
    } catch (err) {
      console.error('Failed to load pipeline observability data:', err);
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to retrieve pipeline runs and freshness status from server.'
      );
    } finally {
      setIsLoading(false);
    }
  }, [scenarioId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Find any run exhibiting the dual-dimension anomaly (compute SUCCESS but quality CORRUPTED)
  const anomalousRun = runs.find(
    (r) =>
      (r.execution_status === 'COMPLETED_SUCCESS' || r.execution_status === 'SUCCESS') &&
      (r.quality_health === 'CORRUPTED' || r.quality_health === 'DEGRADED')
  ) || runs[0];

  const stalePartitionsCount = freshnessChecks.filter((c) => c.status === 'STALE').length;

  return (
    <div className="space-y-6" data-testid="pipeline-observability-view">
      {/* Top Controls & Sub-Tab Navigation */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        {/* Sub-Navigation Tabs */}
        <div className="flex items-center gap-2 p-1 bg-slate-900 border border-slate-800 rounded-lg">
          <button
            type="button"
            onClick={() => setActiveSubTab('combined')}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
              activeSubTab === 'combined'
                ? 'bg-lux-700 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            All Observability
          </button>
          <button
            type="button"
            onClick={() => setActiveSubTab('history')}
            className={`px-3 py-1.5 rounded-md text-xs font-medium flex items-center gap-1.5 transition-all ${
              activeSubTab === 'history'
                ? 'bg-lux-700 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            <Clock className="w-3.5 h-3.5" />
            <span>Run History</span>
            <span className="px-1.5 py-0.2 bg-slate-800 text-[10px] rounded font-mono">
              {runs.length}
            </span>
          </button>
          <button
            type="button"
            onClick={() => setActiveSubTab('freshness')}
            className={`px-3 py-1.5 rounded-md text-xs font-medium flex items-center gap-1.5 transition-all ${
              activeSubTab === 'freshness'
                ? 'bg-lux-700 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Partition Freshness</span>
            {stalePartitionsCount > 0 && (
              <span className="px-1.5 py-0.2 bg-rose-500/20 text-rose-300 border border-rose-500/30 text-[10px] rounded font-mono font-semibold">
                {stalePartitionsCount} stale
              </span>
            )}
          </button>
        </div>

        {/* Refresh Action */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={fetchData}
            disabled={isLoading}
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 text-xs font-medium border border-slate-700 transition-colors focus:outline-none focus:ring-2 focus:ring-lux-500"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-lux-400' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 bg-rose-950/40 border border-rose-500/50 rounded-xl text-xs text-rose-200 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h4 className="font-semibold text-rose-300">Observability Sync Failed</h4>
            <p>{error}</p>
          </div>
        </div>
      )}

      {/* ADR-006 Dual-Dimension Anomaly Callout */}
      {anomalousRun && (
        <DualStatusCallout
          run={anomalousRun}
          onTraceImpact={onTraceImpact}
          onViewLogs={() => setActiveSubTab('history')}
        />
      )}

      {/* Sub-Views */}
      {(activeSubTab === 'combined' || activeSubTab === 'history') && (
        <section aria-label="Pipeline Run History">
          <PipelineHistoryTimeline
            runs={runs}
            isLoading={isLoading}
          />
        </section>
      )}

      {(activeSubTab === 'combined' || activeSubTab === 'freshness') && (
        <section aria-label="Dataset Partition Freshness">
          <FreshnessView
            freshnessChecks={freshnessChecks}
            isLoading={isLoading}
            onRefresh={fetchData}
          />
        </section>
      )}
    </div>
  );
};
