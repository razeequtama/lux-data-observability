import React, { memo } from 'react';
import { Handle, Position, NodeProps, Node } from '@xyflow/react';
import {
  Database,
  Cpu,
  Layers,
  TrendingUp,
  LayoutDashboard,
  Terminal,
  CheckCircle2,
  AlertOctagon,
  AlertTriangle,
  HelpCircle,
  Flame,
} from 'lucide-react';
import clsx from 'clsx';
import { AssetImpactStatus, LineageNodeType } from '../../types';

export interface CustomNodeData {
  id: string;
  label: string;
  name?: string;
  type: LineageNodeType | string;
  dataset_id?: string | null;
  execution_status?: string | null;
  quality_health?: string | null;
  owner?: string | null;
  description?: string | null;
  metadata?: Record<string, unknown>;
  impactStatus?: AssetImpactStatus | null;
  isHighlighted?: boolean;
  isDimmed?: boolean;
  isSelected?: boolean;
  distance?: number;
  [key: string]: unknown;
}

export type CustomNodeType = Node<CustomNodeData>;
export type CustomNodeProps = NodeProps<CustomNodeType>;

const TYPE_CONFIG: Record<
  string,
  {
    icon: React.ComponentType<{ className?: string }>;
    label: string;
    badgeStyle: string;
    borderStyle: string;
    accentBg: string;
  }
> = {
  SOURCE_DATASET: {
    icon: Database,
    label: 'SOURCE',
    badgeStyle: 'bg-blue-950/80 text-blue-300 border-blue-800/80',
    borderStyle: 'border-blue-500/30 hover:border-blue-400',
    accentBg: 'from-blue-950/30 to-slate-900/90',
  },
  TRANSFORMATION: {
    icon: Cpu,
    label: 'TRANSFORM',
    badgeStyle: 'bg-amber-950/80 text-amber-300 border-amber-800/80',
    borderStyle: 'border-amber-500/30 hover:border-amber-400',
    accentBg: 'from-amber-950/30 to-slate-900/90',
  },
  DERIVED_DATASET: {
    icon: Layers,
    label: 'DERIVED',
    badgeStyle: 'bg-indigo-950/80 text-indigo-300 border-indigo-800/80',
    borderStyle: 'border-indigo-500/30 hover:border-indigo-400',
    accentBg: 'from-indigo-950/30 to-slate-900/90',
  },
  METRIC: {
    icon: TrendingUp,
    label: 'METRIC',
    badgeStyle: 'bg-emerald-950/80 text-emerald-300 border-emerald-800/80',
    borderStyle: 'border-emerald-500/30 hover:border-emerald-400',
    accentBg: 'from-emerald-950/30 to-slate-900/90',
  },
  REPORT: {
    icon: LayoutDashboard,
    label: 'REPORT',
    badgeStyle: 'bg-fuchsia-950/80 text-fuchsia-300 border-fuchsia-800/80',
    borderStyle: 'border-fuchsia-500/30 hover:border-fuchsia-400',
    accentBg: 'from-fuchsia-950/30 to-slate-900/90',
  },
};

export const CustomNode = memo(({ id, data, selected }: CustomNodeProps) => {
  const nodeType = data.type || 'DERIVED_DATASET';
  const config = TYPE_CONFIG[nodeType] || TYPE_CONFIG.DERIVED_DATASET;
  const TypeIcon = config.icon;

  const isSelected = selected || data.isSelected;
  const isDimmed = data.isDimmed;
  const impactStatus = data.impactStatus;

  // Dual-dimension Compute Status chip
  const renderComputeStatus = () => {
    const status = data.execution_status || 'COMPLETED_SUCCESS';
    if (status === 'COMPLETED_SUCCESS' || status === 'SUCCESS') {
      return (
        <span
          className="inline-flex items-center space-x-1 px-1.5 py-0.5 rounded text-[10px] font-mono bg-emerald-950/80 text-emerald-400 border border-emerald-800/60"
          title="Compute Status: COMPLETED_SUCCESS (Exit code 0)"
        >
          <Terminal className="w-2.5 h-2.5 text-emerald-400" />
          <span>Exit 0</span>
        </span>
      );
    }
    if (status === 'FAILED') {
      return (
        <span
          className="inline-flex items-center space-x-1 px-1.5 py-0.5 rounded text-[10px] font-mono bg-rose-950/80 text-rose-400 border border-rose-800/60"
          title="Compute Status: FAILED"
        >
          <Terminal className="w-2.5 h-2.5 text-rose-400" />
          <span>Failed</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center space-x-1 px-1.5 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-400 border border-slate-700">
        <Terminal className="w-2.5 h-2.5" />
        <span>{status}</span>
      </span>
    );
  };

  // Dual-dimension Quality Health chip
  const renderQualityHealth = () => {
    const health = data.quality_health || 'HEALTHY';
    if (health === 'CORRUPTED' || health === 'FAILED') {
      return (
        <span
          className="inline-flex items-center space-x-1 px-1.5 py-0.5 rounded text-[10px] font-semibold bg-rose-950/90 text-rose-300 border border-rose-700/80 shadow-sm"
          title="Data Quality Health: CORRUPTED (Detected rule violations)"
        >
          <AlertOctagon className="w-2.5 h-2.5 text-rose-400" />
          <span>Corrupted</span>
        </span>
      );
    }
    if (health === 'DEGRADED' || health === 'WARNING') {
      return (
        <span
          className="inline-flex items-center space-x-1 px-1.5 py-0.5 rounded text-[10px] font-semibold bg-amber-950/90 text-amber-300 border border-amber-700/80"
          title="Data Quality Health: DEGRADED"
        >
          <AlertTriangle className="w-2.5 h-2.5 text-amber-400" />
          <span>Degraded</span>
        </span>
      );
    }
    if (health === 'HEALTHY' || health === 'PASSED') {
      return (
        <span
          className="inline-flex items-center space-x-1 px-1.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-950/80 text-emerald-300 border border-emerald-800/60"
          title="Data Quality Health: HEALTHY (Passed quality checks)"
        >
          <CheckCircle2 className="w-2.5 h-2.5 text-emerald-400" />
          <span>Healthy</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center space-x-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-slate-800 text-slate-400 border border-slate-700">
        <HelpCircle className="w-2.5 h-2.5" />
        <span>Unchecked</span>
      </span>
    );
  };

  // Blast Radius Impact Chip
  const renderImpactChip = () => {
    if (!impactStatus || impactStatus === 'HEALTHY') return null;

    if (impactStatus === 'CONFIRMED_FAILED') {
      return (
        <div className="flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-bold bg-rose-900/90 text-white border border-rose-500 shadow-sm animate-pulse">
          <Flame className="w-3 h-3 text-rose-300" />
          <span>Failure Origin</span>
        </div>
      );
    }
    if (impactStatus === 'DIRECTLY_AFFECTED') {
      return (
        <div className="flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-900/80 text-amber-200 border border-amber-500 shadow-sm">
          <AlertTriangle className="w-3 h-3 text-amber-300" />
          <span>Direct Consumer</span>
        </div>
      );
    }
    if (impactStatus === 'POTENTIALLY_AFFECTED') {
      return (
        <div className="flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-lux-900/80 text-lux-200 border border-lux-500 shadow-sm">
          <AlertOctagon className="w-3 h-3 text-lux-300" />
          <span>Blast Radius</span>
        </div>
      );
    }
    return null;
  };

  // Determine border & glow styling
  const getContainerClasses = () => {
    const base =
      'w-64 rounded-xl border bg-gradient-to-b p-3 text-slate-100 shadow-lg transition-all duration-200 text-left';

    if (impactStatus === 'CONFIRMED_FAILED') {
      return clsx(
        base,
        'border-rose-500 bg-slate-900/95 ring-2 ring-rose-500/80 shadow-rose-950/50'
      );
    }
    if (impactStatus === 'DIRECTLY_AFFECTED') {
      return clsx(
        base,
        'border-amber-500 bg-slate-900/95 ring-2 ring-amber-500/70 shadow-amber-950/40'
      );
    }
    if (impactStatus === 'POTENTIALLY_AFFECTED') {
      return clsx(
        base,
        'border-lux-500 bg-slate-900/95 ring-2 ring-lux-500/60 ring-dashed shadow-lux-950/30'
      );
    }
    if (isSelected) {
      return clsx(
        base,
        'border-lux-400 bg-slate-900 ring-2 ring-lux-400 shadow-xl shadow-lux-950/60'
      );
    }

    return clsx(
      base,
      config.borderStyle,
      config.accentBg,
      isDimmed ? 'opacity-30 hover:opacity-90' : 'opacity-100'
    );
  };

  const displayName = data.name || data.label || id;
  const engine = data.metadata?.engine ? String(data.metadata.engine) : null;

  return (
    <div
      data-testid={`lineage-node-${id}`}
      data-node-id={id}
      data-node-type={nodeType}
      data-impact-status={impactStatus || 'NONE'}
      className={getContainerClasses()}
    >
      {/* Left Input Handle */}
      <Handle
        type="target"
        position={Position.Left}
        id="in"
        className="!w-2.5 !h-2.5 !bg-lux-400 !border-2 !border-slate-900 !-left-1.5"
      />

      {/* Header: Asset Type & Optional Impact Badge */}
      <div className="flex items-center justify-between gap-1.5 pb-2 mb-2 border-b border-slate-800/80">
        <div className="flex items-center space-x-1.5">
          <div
            className={clsx(
              'w-6 h-6 rounded flex items-center justify-center border',
              config.badgeStyle
            )}
          >
            <TypeIcon className="w-3.5 h-3.5" />
          </div>
          <span
            className={clsx(
              'px-1.5 py-0.5 rounded text-[10px] font-semibold tracking-wider uppercase border',
              config.badgeStyle
            )}
          >
            {config.label}
          </span>
          {engine && (
            <span className="text-[10px] font-mono px-1 py-0.2 rounded bg-slate-800 text-slate-400 border border-slate-700">
              {engine}
            </span>
          )}
        </div>

        {renderImpactChip()}
      </div>

      {/* Node Title & Identity */}
      <div className="space-y-1">
        <div
          className="text-xs font-bold text-white tracking-tight truncate"
          title={displayName}
        >
          {displayName}
        </div>
        <div className="flex items-center justify-between text-[11px] text-slate-400">
          <span className="font-mono text-[10px] text-slate-500 truncate" title={id}>
            {id}
          </span>
          {data.dataset_id && (
            <span className="text-[10px] font-mono px-1 rounded bg-slate-800/90 text-slate-400">
              {data.dataset_id}
            </span>
          )}
        </div>
      </div>

      {/* Dual Dimension Status Chips (ADR-006) */}
      <div className="mt-2.5 pt-2 border-t border-slate-800/60 flex items-center justify-between gap-1">
        <div className="flex items-center space-x-1">{renderComputeStatus()}</div>
        <div className="flex items-center space-x-1">{renderQualityHealth()}</div>
      </div>

      {/* Right Output Handle */}
      <Handle
        type="source"
        position={Position.Right}
        id="out"
        className="!w-2.5 !h-2.5 !bg-lux-400 !border-2 !border-slate-900 !-right-1.5"
      />
    </div>
  );
});

CustomNode.displayName = 'CustomNode';
