import React from 'react';
import {
  X,
  Target,
  ArrowRight,
  Database,
  Terminal,
  CheckCircle2,
  AlertOctagon,
  AlertTriangle,
  Flame,
  Layers,
  TrendingUp,
  LayoutDashboard,
  Cpu,
  CornerDownRight,
  Focus,
} from 'lucide-react';
import clsx from 'clsx';
import {
  BlastRadiusReport,
  LineageNodeDetail,
} from '../../types';

export interface NodeDetailsPanelProps {
  nodeDetail: LineageNodeDetail | null;
  blastRadius: BlastRadiusReport | null;
  isLoading?: boolean;
  onClose: () => void;
  onSelectNode: (nodeId: string) => void;
  onFocusNode?: (nodeId: string) => void;
}

const TYPE_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  SOURCE_DATASET: Database,
  TRANSFORMATION: Cpu,
  DERIVED_DATASET: Layers,
  METRIC: TrendingUp,
  REPORT: LayoutDashboard,
};

export const NodeDetailsPanel: React.FC<NodeDetailsPanelProps> = ({
  nodeDetail,
  blastRadius,
  isLoading = false,
  onClose,
  onSelectNode,
  onFocusNode,
}) => {
  if (!nodeDetail) {
    return null;
  }

  const TypeIcon = TYPE_ICONS[nodeDetail.type] || Layers;
  const isImpactRoot = blastRadius?.root_node_id === nodeDetail.id;

  return (
    <aside
      data-testid="node-details-panel"
      aria-label={`Node details for ${nodeDetail.name}`}
      className="w-96 flex-shrink-0 bg-slate-900 border-l border-slate-800 flex flex-col h-full shadow-2xl z-20 overflow-hidden"
    >
      {/* Header */}
      <div className="p-4 border-b border-slate-800 flex items-start justify-between bg-slate-900/90 backdrop-blur sticky top-0 z-10">
        <div className="flex items-start space-x-3 pr-2">
          <div className="w-9 h-9 rounded-lg bg-lux-900/60 border border-lux-700/50 flex items-center justify-center text-lux-300 flex-shrink-0">
            <TypeIcon className="w-5 h-5" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 uppercase tracking-wider">
                {nodeDetail.type}
              </span>
              {nodeDetail.dataset_id && (
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-blue-950/70 border border-blue-800/60 text-blue-300">
                  {nodeDetail.dataset_id}
                </span>
              )}
            </div>
            <h2
              className="text-sm font-bold text-white truncate mt-1"
              title={nodeDetail.name}
            >
              {nodeDetail.name}
            </h2>
            <div className="text-[11px] font-mono text-slate-400 truncate flex items-center space-x-1.5">
              <span>ID: {nodeDetail.id}</span>
              {isLoading && (
                <span className="w-2 h-2 rounded-full border border-lux-400 border-t-transparent animate-spin inline-block" />
              )}
            </div>
          </div>
        </div>

        <button
          type="button"
          onClick={onClose}
          aria-label="Close inspector panel"
          className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Content Scroll */}
      <div className="flex-1 overflow-y-auto p-4 space-y-5 text-xs text-slate-300">
        {/* Dual Dimension Status Cards (ADR-006) */}
        <section aria-label="Health Dimensions">
          <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-2">
            Dual Status Dimensions (ADR-006)
          </h3>
          <div className="grid grid-cols-2 gap-2">
            {/* Compute Status */}
            <div className="p-2.5 rounded-lg bg-slate-800/80 border border-slate-700/80 space-y-1">
              <span className="text-[10px] uppercase font-semibold text-slate-400 flex items-center space-x-1">
                <Terminal className="w-3 h-3 text-slate-400" />
                <span>Compute</span>
              </span>
              <div className="flex items-center space-x-1.5 pt-0.5">
                <span
                  className={clsx(
                    'w-2 h-2 rounded-full',
                    nodeDetail.execution_status === 'COMPLETED_SUCCESS' ||
                      nodeDetail.execution_status === 'SUCCESS'
                      ? 'bg-emerald-400 shadow-sm shadow-emerald-500/50'
                      : 'bg-rose-400 shadow-sm shadow-rose-500/50'
                  )}
                />
                <span className="font-mono text-[11px] font-semibold text-slate-200 truncate">
                  {nodeDetail.execution_status || 'COMPLETED_SUCCESS'}
                </span>
              </div>
            </div>

            {/* Quality Health */}
            <div className="p-2.5 rounded-lg bg-slate-800/80 border border-slate-700/80 space-y-1">
              <span className="text-[10px] uppercase font-semibold text-slate-400 flex items-center space-x-1">
                <CheckCircle2 className="w-3 h-3 text-slate-400" />
                <span>Quality</span>
              </span>
              <div className="flex items-center space-x-1.5 pt-0.5">
                {nodeDetail.quality_health === 'CORRUPTED' ||
                nodeDetail.quality_health === 'FAILED' ? (
                  <>
                    <AlertOctagon className="w-3.5 h-3.5 text-rose-400 animate-pulse" />
                    <span className="font-semibold text-rose-300">CORRUPTED</span>
                  </>
                ) : nodeDetail.quality_health === 'DEGRADED' ||
                  nodeDetail.quality_health === 'WARNING' ? (
                  <>
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                    <span className="font-semibold text-amber-300">DEGRADED</span>
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    <span className="font-semibold text-emerald-300">HEALTHY</span>
                  </>
                )}
              </div>
            </div>
          </div>
        </section>

        {/* Metadata info */}
        {(nodeDetail.owner || nodeDetail.description) && (
          <section aria-label="Asset Metadata" className="space-y-1.5">
            <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Metadata & Ownership
            </h3>
            {nodeDetail.owner && (
              <div className="flex items-center justify-between py-1 border-b border-slate-800">
                <span className="text-slate-400">Owner:</span>
                <span className="font-medium text-slate-200">{nodeDetail.owner}</span>
              </div>
            )}
            {nodeDetail.description && (
              <p className="text-slate-400 text-[11px] leading-relaxed pt-1">
                {nodeDetail.description}
              </p>
            )}
          </section>
        )}

        {/* Downstream Blast Radius Summary */}
        {blastRadius && (
          <section
            data-testid="blast-radius-summary"
            aria-label="Downstream Blast Radius"
            className="space-y-2.5 p-3 rounded-xl bg-slate-950/70 border border-lux-700/40"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-1.5">
                <Target className="w-4 h-4 text-lux-400" />
                <h3 className="text-xs font-bold text-white tracking-wide">
                  Downstream Blast Radius
                </h3>
              </div>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-950 text-rose-300 border border-rose-800">
                {blastRadius.total_affected_assets} Assets Affected
              </span>
            </div>

            {isImpactRoot && (
              <div className="flex items-center space-x-2 text-[11px] text-rose-300 bg-rose-950/40 border border-rose-800/60 rounded px-2.5 py-1.5 font-medium">
                <Flame className="w-4 h-4 text-rose-400 flex-shrink-0" />
                <span>This node is the root failure origin for this blast radius.</span>
              </div>
            )}

            {/* Impact Tier Breakdown */}
            <div className="grid grid-cols-3 gap-1.5 text-center pt-1">
              <div className="p-1.5 rounded bg-rose-950/50 border border-rose-900/60">
                <div className="text-base font-bold text-rose-400 font-mono">
                  {blastRadius.impact_summary.confirmed_failed}
                </div>
                <div className="text-[9px] uppercase font-semibold text-rose-300">
                  Confirmed
                </div>
              </div>
              <div className="p-1.5 rounded bg-amber-950/50 border border-amber-900/60">
                <div className="text-base font-bold text-amber-400 font-mono">
                  {blastRadius.impact_summary.directly_affected}
                </div>
                <div className="text-[9px] uppercase font-semibold text-amber-300">
                  Direct
                </div>
              </div>
              <div className="p-1.5 rounded bg-lux-950/50 border border-lux-900/60">
                <div className="text-base font-bold text-lux-400 font-mono">
                  {blastRadius.impact_summary.potentially_affected}
                </div>
                <div className="text-[9px] uppercase font-semibold text-lux-300">
                  Potential
                </div>
              </div>
            </div>

            {/* Affected Asset List & Paths */}
            <div className="space-y-2 pt-2 border-t border-slate-800/80">
              <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">
                Impacted Assets & Chains
              </span>
              <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                {blastRadius.affected_assets.map((asset) => {
                  const AssetIcon = TYPE_ICONS[asset.type] || Layers;
                  const isCurrent = asset.node_id === nodeDetail.id;

                  return (
                    <div
                      key={asset.node_id}
                      data-testid={`affected-asset-${asset.node_id}`}
                      className={clsx(
                        'p-2 rounded-lg border text-left transition-colors',
                        isCurrent
                          ? 'bg-lux-950/70 border-lux-500/80'
                          : 'bg-slate-900/90 border-slate-800 hover:border-slate-700'
                      )}
                    >
                      <div className="flex items-center justify-between gap-1">
                        <button
                          type="button"
                          onClick={() => onSelectNode(asset.node_id)}
                          className="flex items-center space-x-1.5 text-left font-semibold text-white hover:text-lux-300 transition-colors truncate"
                        >
                          <AssetIcon className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                          <span className="truncate">{asset.name}</span>
                        </button>

                        <span
                          className={clsx(
                            'text-[9px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider border flex-shrink-0',
                            asset.impact_status === 'CONFIRMED_FAILED' &&
                              'bg-rose-950 text-rose-300 border-rose-800',
                            asset.impact_status === 'DIRECTLY_AFFECTED' &&
                              'bg-amber-950 text-amber-300 border-amber-800',
                            asset.impact_status === 'POTENTIALLY_AFFECTED' &&
                              'bg-lux-950 text-lux-300 border-lux-800'
                          )}
                        >
                          {asset.impact_status === 'CONFIRMED_FAILED'
                            ? 'Failed'
                            : asset.impact_status === 'DIRECTLY_AFFECTED'
                            ? 'Direct'
                            : 'Potential'}
                        </span>
                      </div>

                      {/* Distance & Path Breadcrumb */}
                      <div className="mt-1 flex items-center space-x-2 text-[10px] text-slate-400 font-mono">
                        <span>Distance: {asset.distance} hops</span>
                      </div>

                      {/* Explanation or path */}
                      {asset.explanation && (
                        <div className="mt-1 text-[10px] text-slate-400 flex items-start space-x-1">
                          <CornerDownRight className="w-3 h-3 text-lux-400 flex-shrink-0 mt-0.5" />
                          <span className="leading-tight">{asset.explanation}</span>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </section>
        )}

        {/* Upstream Predecessors */}
        <section aria-label="Upstream Dependencies" className="space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Immediate Upstream Predecessors ({nodeDetail.direct_upstream_count})
            </h3>
            <span className="text-[10px] text-slate-500 font-mono">
              Total Ancestors: {nodeDetail.total_ancestors_count}
            </span>
          </div>

          {nodeDetail.upstream_nodes.length === 0 ? (
            <div className="p-3 rounded-lg bg-slate-950/40 border border-slate-800 text-slate-500 text-center text-xs">
              Root node — no upstream dependencies.
            </div>
          ) : (
            <div className="space-y-1">
              {nodeDetail.upstream_nodes.map((u) => (
                <button
                  key={u.id}
                  type="button"
                  onClick={() => onSelectNode(u.id)}
                  className="w-full flex items-center justify-between p-2 rounded-lg bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 text-left transition-colors group"
                >
                  <div className="flex items-center space-x-2 truncate">
                    <span className="text-[10px] font-mono px-1 rounded bg-slate-900 text-slate-400 border border-slate-700">
                      {u.type}
                    </span>
                    <span className="text-white group-hover:text-lux-300 font-medium truncate">
                      {u.name}
                    </span>
                  </div>
                  <ArrowRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-lux-300 flex-shrink-0" />
                </button>
              ))}
            </div>
          )}
        </section>

        {/* Downstream Consumers */}
        <section aria-label="Downstream Consumers" className="space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Immediate Downstream Consumers ({nodeDetail.direct_downstream_count})
            </h3>
            <span className="text-[10px] text-slate-500 font-mono">
              Total Descendants: {nodeDetail.total_descendants_count}
            </span>
          </div>

          {nodeDetail.downstream_nodes.length === 0 ? (
            <div className="p-3 rounded-lg bg-slate-950/40 border border-slate-800 text-slate-500 text-center text-xs">
              Leaf asset — no downstream consumers.
            </div>
          ) : (
            <div className="space-y-1">
              {nodeDetail.downstream_nodes.map((d) => (
                <button
                  key={d.id}
                  type="button"
                  onClick={() => onSelectNode(d.id)}
                  className="w-full flex items-center justify-between p-2 rounded-lg bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 text-left transition-colors group"
                >
                  <div className="flex items-center space-x-2 truncate">
                    <span className="text-[10px] font-mono px-1 rounded bg-slate-900 text-slate-400 border border-slate-700">
                      {d.type}
                    </span>
                    <span className="text-white group-hover:text-lux-300 font-medium truncate">
                      {d.name}
                    </span>
                  </div>
                  <ArrowRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-lux-300 flex-shrink-0" />
                </button>
              ))}
            </div>
          )}
        </section>
      </div>

      {/* Footer Actions */}
      <div className="p-3 border-t border-slate-800 bg-slate-900/90 flex items-center justify-between gap-2">
        {onFocusNode && (
          <button
            type="button"
            onClick={() => onFocusNode(nodeDetail.id)}
            className="flex-1 flex items-center justify-center space-x-1.5 py-2 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-colors"
          >
            <Focus className="w-3.5 h-3.5" />
            <span>Center Node</span>
          </button>
        )}
        <button
          type="button"
          onClick={onClose}
          className="py-2 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 transition-colors"
        >
          Close
        </button>
      </div>
    </aside>
  );
};
