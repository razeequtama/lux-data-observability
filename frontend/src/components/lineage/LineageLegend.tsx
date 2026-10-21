import React from 'react';
import {
  Database,
  Cpu,
  Layers,
  TrendingUp,
  LayoutDashboard,
  Terminal,
  CheckCircle2,
  AlertOctagon,
  Flame,
  AlertTriangle,
} from 'lucide-react';

export const LineageLegend: React.FC = () => {
  return (
    <div
      data-testid="lineage-legend"
      aria-label="Lineage DAG Legend"
      className="bg-slate-900/95 border border-slate-800 rounded-xl p-4 shadow-xl text-xs space-y-3.5 backdrop-blur-md"
    >
      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
        <span className="font-semibold text-slate-200 tracking-wide uppercase text-[11px]">
          Lineage DAG Legend
        </span>
        <span className="text-[10px] text-slate-400 font-mono">ADR-003 & ADR-006</span>
      </div>

      {/* Node Classification Types */}
      <div className="space-y-1.5">
        <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">
          Node Classifications
        </span>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2">
          <div className="flex items-center space-x-1.5 px-2 py-1 rounded bg-blue-950/40 border border-blue-900/50 text-blue-300">
            <Database className="w-3.5 h-3.5 text-blue-400" />
            <span className="text-[11px]">Source Dataset</span>
          </div>
          <div className="flex items-center space-x-1.5 px-2 py-1 rounded bg-amber-950/40 border border-amber-900/50 text-amber-300">
            <Cpu className="w-3.5 h-3.5 text-amber-400" />
            <span className="text-[11px]">Transformation</span>
          </div>
          <div className="flex items-center space-x-1.5 px-2 py-1 rounded bg-indigo-950/40 border border-indigo-900/50 text-indigo-300">
            <Layers className="w-3.5 h-3.5 text-indigo-400" />
            <span className="text-[11px]">Derived Table</span>
          </div>
          <div className="flex items-center space-x-1.5 px-2 py-1 rounded bg-emerald-950/40 border border-emerald-900/50 text-emerald-300">
            <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
            <span className="text-[11px]">Metric / KPI</span>
          </div>
          <div className="flex items-center space-x-1.5 px-2 py-1 rounded bg-fuchsia-950/40 border border-fuchsia-900/50 text-fuchsia-300">
            <LayoutDashboard className="w-3.5 h-3.5 text-fuchsia-400" />
            <span className="text-[11px]">Report / Alert</span>
          </div>
        </div>
      </div>

      {/* Dual Dimension Status & Blast Radius */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 border-t border-slate-800/80">
        {/* Dual Dimension */}
        <div className="space-y-1.5">
          <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">
            Dual Status Dimensions (ADR-006)
          </span>
          <div className="flex flex-wrap gap-1.5">
            <span className="inline-flex items-center space-x-1 px-1.5 py-0.5 rounded text-[10px] font-mono bg-emerald-950/80 text-emerald-400 border border-emerald-800">
              <Terminal className="w-3 h-3" />
              <span>Compute: Exit 0</span>
            </span>
            <span className="inline-flex items-center space-x-1 px-1.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-950/80 text-emerald-300 border border-emerald-800">
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
              <span>Quality: Healthy</span>
            </span>
            <span className="inline-flex items-center space-x-1 px-1.5 py-0.5 rounded text-[10px] font-semibold bg-rose-950/80 text-rose-300 border border-rose-800">
              <AlertOctagon className="w-3 h-3 text-rose-400" />
              <span>Quality: Corrupted</span>
            </span>
          </div>
        </div>

        {/* Blast Radius Tiers */}
        <div className="space-y-1.5">
          <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">
            Downstream Blast Radius (FR-04)
          </span>
          <div className="flex flex-wrap gap-1.5">
            <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-bold bg-rose-950 text-rose-200 border border-rose-500">
              <Flame className="w-3 h-3 text-rose-400" />
              <span>Confirmed Failed</span>
            </span>
            <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-950 text-amber-200 border border-amber-500">
              <AlertTriangle className="w-3 h-3 text-amber-400" />
              <span>Directly Affected</span>
            </span>
            <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-lux-950 text-lux-200 border border-lux-500 border-dashed">
              <AlertOctagon className="w-3 h-3 text-lux-400" />
              <span>Potentially Affected</span>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

