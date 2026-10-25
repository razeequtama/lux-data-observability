import React, { useState, useEffect, useCallback } from 'react';
import {
  Target,
  ShieldAlert,
  ArrowRight,
  RefreshCw,
  AlertTriangle,
  Layers,
  FileSpreadsheet,
  CheckCircle2,
} from 'lucide-react';
import { traceDownstreamImpact } from '../../api/lineage';
import { BlastRadiusReport, AssetImpactStatus, ValidationFindingItem } from '../../types';
import { AlertBanner } from '../common/AlertBanner';
import { LineageView } from '../lineage/LineageView';

export interface ImpactAnalysisViewProps {
  scenarioId: string;
  isScenarioLoaded: boolean;
  lastReloadKey?: number | string;
  initialTargetFinding?: ValidationFindingItem | null;
  initialTargetNodeId?: string | null;
  onNavigateToLineage?: (nodeId?: string) => void;
  onNavigateToValidations?: () => void;
}

const AVAILABLE_ROOT_TARGETS = [
  { id: 'src_orders', name: 'orders.csv (Source Dataset)', default: true },
  { id: 'src_order_items', name: 'order_items.csv (Source Dataset)', default: false },
  { id: 'src_products', name: 'products.csv (Source Dataset)', default: false },
  { id: 'src_inventory', name: 'inventory.csv (Source Dataset)', default: false },
  { id: 'tf_orders', name: 'transform_order_line_items (SQL Transform)', default: false },
  { id: 'dim_orders', name: 'dim_orders (Derived Table)', default: false },
  { id: 'fct_order_items', name: 'fct_order_items (Derived Table)', default: false },
];

function getStatusBadge(status: AssetImpactStatus) {
  switch (status) {
    case 'CONFIRMED_FAILED':
      return (
        <span className="inline-flex items-center space-x-1 px-3 py-1 rounded-md text-[11px] font-bold uppercase tracking-wider bg-rose-950/90 text-rose-300 border border-rose-600/70 shadow-[0_0_10px_rgba(244,63,94,0.3)]">
          <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
          <span>CONFIRMED FAILED</span>
        </span>
      );
    case 'DIRECTLY_AFFECTED':
      return (
        <span className="inline-flex items-center space-x-1 px-3 py-1 rounded-md text-[11px] font-bold uppercase tracking-wider bg-orange-950/90 text-orange-300 border border-orange-600/70 shadow-[0_0_10px_rgba(249,115,22,0.3)]">
          <ShieldAlert className="w-3.5 h-3.5 text-orange-400" />
          <span>DIRECT CONSUMER</span>
        </span>
      );
    case 'POTENTIALLY_AFFECTED':
      return (
        <span className="inline-flex items-center space-x-1 px-3 py-1 rounded-md text-[11px] font-bold uppercase tracking-wider bg-amber-950/80 text-amber-300 border border-amber-600/60 shadow-[0_0_10px_rgba(245,158,11,0.25)]">
          <Target className="w-3.5 h-3.5 text-amber-400" />
          <span>TRANSITIVE CONSUMER</span>
        </span>
      );
    case 'HEALTHY':
    default:
      return (
        <span className="inline-flex items-center space-x-1 px-3 py-1 rounded-md text-[11px] font-semibold uppercase tracking-wider bg-emerald-950/80 text-emerald-300 border border-emerald-600/50">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          <span>UNAFFECTED</span>
        </span>
      );
  }
}

export const ImpactAnalysisView: React.FC<ImpactAnalysisViewProps> = ({
  scenarioId,
  isScenarioLoaded,
  lastReloadKey,
  initialTargetFinding,
  initialTargetNodeId,
  onNavigateToLineage,
}) => {
  const [selectedTargetId, setSelectedTargetId] = useState<string>(
    initialTargetNodeId || (initialTargetFinding ? `src_${initialTargetFinding.dataset_id}` : 'src_orders')
  );
  const [blastRadius, setBlastRadius] = useState<BlastRadiusReport | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchBlastRadius = useCallback(
    async (targetId: string) => {
      if (!isScenarioLoaded) {
        setBlastRadius(null);
        setError(null);
        setIsLoading(false);
        return;
      }
      setIsLoading(true);
      setError(null);
      try {
        const report = await traceDownstreamImpact({
          scenario_id: scenarioId,
          target_type: 'NODE',
          target_id: targetId,
          include_transformations: true,
          include_root: true,
        });
        if (isScenarioLoaded) {
          setBlastRadius(report);
        }
      } catch (err) {
        if (isScenarioLoaded) {
          console.warn('Could not fetch blast radius:', err);
          setError(err instanceof Error ? err.message : 'Failed to trace blast radius.');
        }
      } finally {
        setIsLoading(false);
      }
    },
    [scenarioId, isScenarioLoaded]
  );

  useEffect(() => {
    let isCancelled = false;

    if (!isScenarioLoaded) {
      setBlastRadius(null);
      setError(null);
      setIsLoading(false);
      setSelectedTargetId('src_orders');
      return;
    }

    const runFetch = async (targetId: string) => {
      setIsLoading(true);
      setError(null);
      try {
        const report = await traceDownstreamImpact({
          scenario_id: scenarioId,
          target_type: 'NODE',
          target_id: targetId,
          include_transformations: true,
          include_root: true,
        });
        if (!isCancelled) {
          setBlastRadius(report);
        }
      } catch (err) {
        if (!isCancelled) {
          console.warn('Could not fetch blast radius:', err);
          setError(err instanceof Error ? err.message : 'Failed to trace blast radius.');
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    };

    if (initialTargetFinding) {
      const targetId = `src_${initialTargetFinding.dataset_id}`;
      setSelectedTargetId(targetId);
      runFetch(targetId);
    } else if (initialTargetNodeId) {
      setSelectedTargetId(initialTargetNodeId);
      runFetch(initialTargetNodeId);
    } else {
      runFetch(selectedTargetId);
    }

    return () => {
      isCancelled = true;
    };
  }, [
    scenarioId,
    initialTargetFinding,
    initialTargetNodeId,
    isScenarioLoaded,
    lastReloadKey,
    selectedTargetId,
  ]);

  const handleSelectTarget = (newTargetId: string) => {
    setSelectedTargetId(newTargetId);
  };

  if (!isScenarioLoaded) {
    return (
      <div className="space-y-6" data-testid="impact-analysis-view">
        {/* Action Header Banner */}
        <div className="relative overflow-hidden bg-[#0d0f1b]/90 backdrop-blur-xl border border-white/[0.08] border-t-purple-400/30 rounded-3xl p-6 sm:p-7 shadow-xl shadow-black/40 flex flex-col xl:flex-row xl:items-center justify-between gap-4">
          <div className="space-y-1.5 relative z-10">
            <div className="flex items-center space-x-3">
              <div className="p-2.5 rounded-2xl bg-lux-950/80 border border-lux-700/50 text-lux-400 shadow-[0_0_16px_rgba(168,85,247,0.35)]">
                <Target className="w-5 h-5" />
              </div>
              <h2 className="text-base sm:text-lg font-bold text-white tracking-tight">
                Downstream Impact & Blast Radius Analysis
              </h2>
              <span className="text-xs px-3.5 py-1 rounded-xl font-sans font-semibold bg-slate-900/90 text-purple-200 border border-white/[0.08] shadow-inner">
                scenario: {scenarioId}
              </span>
            </div>
            <p className="text-xs sm:text-sm text-slate-400">
              Traverses lineage dependencies to isolate affected downstream models, calculate blast radius, and protect executive assets.
            </p>
          </div>
        </div>

        {/* Empty State Banner when no scenario is loaded */}
        <div
          data-testid="impact-empty-state"
          className="relative overflow-hidden bg-[#0d0f1b]/60 backdrop-blur-xl border border-white/[0.07] border-t-purple-400/20 rounded-3xl p-16 text-center space-y-6 shadow-xl"
        >
          <div className="w-16 h-16 mx-auto rounded-3xl bg-lux-950/80 border border-lux-700/50 flex items-center justify-center text-lux-400 shadow-[0_0_24px_rgba(168,85,247,0.4)]">
            <Target className="w-8 h-8" />
          </div>
          <div className="max-w-md mx-auto space-y-2.5">
            <h3 className="text-lg font-bold text-white tracking-tight">
              No Scenario Loaded Yet
            </h3>
            <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
              Click &quot;Load Scenario&quot; in the top command bar to ingest datasets into the workspace before tracing downstream impact and blast radius.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="impact-analysis-view">
      {error && (
        <AlertBanner
          type="error"
          message="Downstream Impact Error"
          details={error}
          onClose={() => setError(null)}
        />
      )}

      {/* Action Header Banner */}
      <div className="relative overflow-hidden bg-[#0d0f1b]/90 backdrop-blur-xl border border-white/[0.08] border-t-purple-400/30 rounded-3xl p-6 sm:p-7 shadow-xl shadow-black/40 flex flex-col xl:flex-row xl:items-center justify-between gap-4">
        {/* Ambient Glow */}
        <div className="absolute top-0 right-0 w-80 h-full bg-gradient-to-l from-purple-600/15 via-indigo-600/10 to-transparent pointer-events-none" />

        <div className="space-y-1.5 relative z-10">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-2xl bg-lux-950/80 border border-lux-700/50 text-lux-400 shadow-[0_0_16px_rgba(168,85,247,0.35)]">
              <Target className="w-5 h-5" />
            </div>
            <h2 className="text-base sm:text-lg font-bold text-white tracking-tight">
              Downstream Impact & Blast Radius Analysis
            </h2>
            <span className="text-xs px-3.5 py-1 rounded-xl font-sans font-semibold bg-slate-900/90 text-purple-200 border border-white/[0.08] shadow-inner">
              scenario: {scenarioId}
            </span>
          </div>
          <p className="text-xs sm:text-sm text-slate-400">
            Traverses lineage dependencies to isolate affected downstream models, calculate blast radius, and protect executive assets.
          </p>
        </div>

        {/* Target Asset Picker & Actions */}
        <div className="flex flex-wrap items-center gap-3 relative z-10">
          <div className="flex items-center space-x-2 bg-slate-950/80 border border-white/[0.08] rounded-2xl px-4 py-2 shadow-inner">
            <span className="text-xs text-slate-400 font-medium">Trace Root:</span>
            <select
              data-testid="impact-target-select"
              aria-label="Select Root Asset for Impact Tracing"
              value={selectedTargetId}
              onChange={(e) => handleSelectTarget(e.target.value)}
              disabled={isLoading}
              className="bg-transparent text-slate-200 text-xs font-semibold focus:outline-none cursor-pointer"
            >
              {AVAILABLE_ROOT_TARGETS.map((t) => (
                <option key={t.id} value={t.id} className="bg-slate-950 text-slate-200">
                  {t.name}
                </option>
              ))}
            </select>
          </div>

          <button
            type="button"
            data-testid="retrace-impact-btn"
            onClick={() => fetchBlastRadius(selectedTargetId)}
            disabled={isLoading}
            className="flex items-center justify-center space-x-3 px-6 py-3 bg-gradient-to-r from-lux-700 via-lux-600 to-indigo-600 hover:from-lux-600 hover:to-indigo-500 disabled:opacity-50 text-white rounded-2xl text-xs sm:text-sm font-bold transition-all shadow-[0_0_20px_rgba(124,58,237,0.4)] ring-1 ring-purple-400/50 cursor-pointer"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            <span>{isLoading ? 'Tracing Paths...' : 'Re-calculate Blast Radius'}</span>
          </button>
        </div>
      </div>

      {/* Metric Cards Row */}
      {blastRadius && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4" data-testid="impact-summary-metrics">
          {/* Total Blast Radius */}
          <div className="bg-[#0d0f1b]/80 backdrop-blur-xl border border-white/[0.08] border-t-purple-400/40 rounded-2xl p-5 sm:p-6 shadow-xl shadow-black/40">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-xs font-semibold uppercase tracking-wider">Total Blast Radius</span>
              <Target className="w-4 h-4 text-purple-400" />
            </div>
            <div className="mt-2.5 flex items-baseline space-x-2">
              <span className="text-3xl font-black text-white tracking-tight">
                {blastRadius.total_affected_assets}
              </span>
              <span className="text-xs text-slate-400 font-mono">assets at risk</span>
            </div>
            <p className="mt-1.5 text-xs text-purple-300">
              Downstream transitive dependency tree
            </p>
          </div>

          {/* Confirmed Failed Root */}
          <div className="bg-[#0d0f1b]/80 backdrop-blur-xl border border-rose-500/30 border-t-rose-400/50 rounded-2xl p-5 sm:p-6 shadow-xl shadow-black/40">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-xs font-semibold uppercase tracking-wider text-rose-300">Root Cause</span>
              <AlertTriangle className="w-4 h-4 text-rose-400" />
            </div>
            <div className="mt-2.5 flex items-baseline space-x-2">
              <span className="text-3xl font-black text-rose-300 tracking-tight">
                {blastRadius.impact_summary.confirmed_failed}
              </span>
              <span className="text-xs text-rose-300/80 font-mono">originating defect</span>
            </div>
            <p className="mt-1.5 text-xs text-rose-300/90 font-mono truncate">
              {blastRadius.root_node_id}
            </p>
          </div>

          {/* Directly Affected */}
          <div className="bg-[#0d0f1b]/80 backdrop-blur-xl border border-orange-500/30 border-t-orange-400/50 rounded-2xl p-5 sm:p-6 shadow-xl shadow-black/40">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-xs font-semibold uppercase tracking-wider text-orange-300">Direct Consumers</span>
              <ShieldAlert className="w-4 h-4 text-orange-400" />
            </div>
            <div className="mt-2.5 flex items-baseline space-x-2">
              <span className="text-3xl font-black text-orange-300 tracking-tight">
                {blastRadius.impact_summary.directly_affected}
              </span>
              <span className="text-xs text-orange-300/80 font-mono">immediate models</span>
            </div>
            <p className="mt-1.5 text-xs text-orange-300/90">
              1 hop downstream from origin
            </p>
          </div>

          {/* Potentially Affected */}
          <div className="bg-[#0d0f1b]/80 backdrop-blur-xl border border-amber-500/30 border-t-amber-400/50 rounded-2xl p-5 sm:p-6 shadow-xl shadow-black/40">
            <div className="flex items-center justify-between text-slate-400">
              <span className="text-xs font-semibold uppercase tracking-wider text-amber-300">Transitive Impact</span>
              <Layers className="w-4 h-4 text-amber-400" />
            </div>
            <div className="mt-2.5 flex items-baseline space-x-2">
              <span className="text-3xl font-black text-amber-300 tracking-tight">
                {blastRadius.impact_summary.potentially_affected}
              </span>
              <span className="text-xs text-amber-300/80 font-mono">downstream assets</span>
            </div>
            <p className="mt-1.5 text-xs text-amber-300/90">
              Metrics, aggregates, and executive dashboards
            </p>
          </div>
        </div>
      )}

      {/* Main Impact View: List of Affected Consumers & Dependency Paths */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left: Blast Radius Table */}
        <div className="lg:col-span-5 bg-[#0d0f1b]/90 backdrop-blur-xl border border-white/[0.08] border-t-purple-400/30 rounded-3xl p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-white/[0.08] pb-4">
            <div className="flex items-center space-x-2.5">
              <Layers className="w-4.5 h-4.5 text-lux-400" />
              <h3 className="text-sm font-bold text-white tracking-tight">
                Affected Downstream Consumers ({blastRadius?.affected_assets.length || 0})
              </h3>
            </div>
            {onNavigateToLineage && (
              <button
                type="button"
                onClick={() => onNavigateToLineage(selectedTargetId)}
                className="text-xs text-purple-300 hover:text-white flex items-center space-x-1 cursor-pointer font-semibold transition-colors"
              >
                <span>Full DAG</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {isLoading ? (
            <div className="py-16 text-center text-slate-400 space-y-3">
              <div className="w-7 h-7 border-2 border-lux-500 border-t-transparent rounded-full animate-spin mx-auto" />
              <p className="text-xs">Traversing dependency graph...</p>
            </div>
          ) : !blastRadius || blastRadius.affected_assets.length === 0 ? (
            <div className="py-16 text-center text-slate-400 space-y-3">
              <FileSpreadsheet className="w-10 h-10 text-slate-600 mx-auto" />
              <p className="text-xs font-medium">No affected consumers found for this asset.</p>
            </div>
          ) : (
            <div className="space-y-3 max-h-[600px] overflow-y-auto pr-1">
              {blastRadius.affected_assets.map((asset) => (
                <div
                  key={asset.node_id}
                  data-testid={`affected-asset-${asset.node_id}`}
                  className="bg-slate-950/70 border border-white/[0.06] hover:border-purple-400/40 rounded-2xl p-4 transition-all space-y-2.5 group"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-white text-xs font-mono group-hover:text-purple-200 transition-colors">
                          {asset.name}
                        </span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-700/60 uppercase">
                          {asset.type.replace(/_/g, ' ')}
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-500 font-mono">
                        id: {asset.node_id}
                      </div>
                    </div>

                    <div>
                      {getStatusBadge(asset.impact_status)}
                    </div>
                  </div>

                  {/* Dependency Path Traversed */}
                  <div className="text-[11px] text-slate-400 font-mono bg-[#090b14] px-3 py-1.5 rounded-xl border border-white/[0.04] flex items-center space-x-1.5 overflow-x-auto">
                    <span className="text-slate-500 shrink-0">Path:</span>
                    <span className="text-purple-200 truncate font-semibold">
                      {asset.dependency_path_names.join(' → ')}
                    </span>
                  </div>

                  <p className="text-xs text-slate-400 leading-relaxed">
                    {asset.explanation}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right: Embedded Interactive Blast Radius DAG */}
        <div className="lg:col-span-7 bg-[#0d0f1b]/90 backdrop-blur-xl border border-white/[0.08] border-t-purple-400/30 rounded-3xl overflow-hidden shadow-xl min-h-[640px] flex flex-col">
          <div className="p-4 border-b border-white/[0.08] bg-[#0c0e1a]/95 flex items-center justify-between">
            <div className="flex items-center space-x-2.5">
              <div className="w-2.5 h-2.5 rounded-full bg-purple-400 shadow-[0_0_8px_rgba(168,85,247,0.8)]" />
              <span className="text-xs font-bold text-white tracking-wide">
                Blast Radius Visual Path for {selectedTargetId}
              </span>
            </div>
            <span className="text-xs text-slate-400 font-mono">
              Illuminated Blast Radius
            </span>
          </div>

          <div className="flex-1 w-full h-full min-h-[580px]">
            <LineageView
              scenarioId={scenarioId}
              isScenarioLoaded={isScenarioLoaded}
              initialSelectedNodeId={selectedTargetId}
              lastReloadKey={lastReloadKey}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
