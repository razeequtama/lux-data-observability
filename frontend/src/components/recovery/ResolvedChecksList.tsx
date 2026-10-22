import React, { useState } from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Database,
  Check,
} from 'lucide-react';
import { ResolvedFindingItem } from '../../types';

export interface ResolvedChecksListProps {
  items: ResolvedFindingItem[];
}

export const ResolvedChecksList: React.FC<ResolvedChecksListProps> = ({ items }) => {
  const [filter, setFilter] = useState<'ALL' | 'RESOLVED' | 'UNRESOLVED'>('ALL');

  const resolvedCount = items.filter((item) => item.status === 'RESOLVED').length;
  const unresolvedCount = items.filter((item) => item.status !== 'RESOLVED').length;

  const filteredItems = items.filter((item) => {
    if (filter === 'RESOLVED') return item.status === 'RESOLVED';
    if (filter === 'UNRESOLVED') return item.status !== 'RESOLVED';
    return true;
  });

  const getSeverityBadge = (severity?: string | null) => {
    switch (severity?.toUpperCase()) {
      case 'CRITICAL':
        return 'bg-rose-500/15 text-rose-400 border-rose-500/30';
      case 'HIGH':
        return 'bg-orange-500/15 text-orange-400 border-orange-500/30';
      case 'MEDIUM':
        return 'bg-amber-500/15 text-amber-400 border-amber-500/30';
      default:
        return 'bg-slate-500/15 text-slate-400 border-slate-500/30';
    }
  };

  return (
    <div
      role="region"
      aria-label="Resolved Quality Checks Checklist"
      data-testid="resolved-checks-list"
      className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden shadow-sm"
    >
      {/* Header and Filter Controls */}
      <div className="p-5 border-b border-slate-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h3 className="text-base font-bold text-white tracking-tight">
              Quality Rule Resolution Checklist
            </h3>
            <span
              data-testid="resolution-count-badge"
              className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30"
            >
              {resolvedCount} of {items.length} Resolved ({items.length > 0 ? Math.round((resolvedCount / items.length) * 100) : 100}%)
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Verification status comparing baseline defective outcomes against clean fixture evaluation.
          </p>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center space-x-1.5 bg-slate-950/80 p-1 rounded-lg border border-slate-800 text-xs">
          <button
            type="button"
            onClick={() => setFilter('ALL')}
            className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
              filter === 'ALL'
                ? 'bg-lux-700 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
            data-testid="filter-all-btn"
          >
            All ({items.length})
          </button>
          <button
            type="button"
            onClick={() => setFilter('RESOLVED')}
            className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
              filter === 'RESOLVED'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-emerald-300'
            }`}
            data-testid="filter-resolved-btn"
          >
            Resolved ({resolvedCount})
          </button>
          <button
            type="button"
            onClick={() => setFilter('UNRESOLVED')}
            className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
              filter === 'UNRESOLVED'
                ? 'bg-rose-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-rose-300'
            }`}
            data-testid="filter-unresolved-btn"
          >
            Unresolved ({unresolvedCount})
          </button>
        </div>
      </div>

      {/* Checklist Table */}
      <div className="divide-y divide-slate-800/80 overflow-x-auto">
        {filteredItems.length === 0 ? (
          <div className="p-8 text-center text-slate-400 text-sm">
            No quality checks match the selected filter.
          </div>
        ) : (
          filteredItems.map((item) => {
            const isResolved = item.status === 'RESOLVED';

            return (
              <div
                key={item.rule_id}
                data-testid={`resolved-item-${item.rule_id}`}
                className="p-4 hover:bg-slate-800/40 transition-colors flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                {/* Left: Resolution Status Icon + Rule Details */}
                <div className="flex items-start space-x-3.5 min-w-0">
                  <div
                    className={`p-2 rounded-lg shrink-0 mt-0.5 ${
                      isResolved
                        ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                        : 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                    }`}
                  >
                    {isResolved ? (
                      <CheckCircle2 className="w-5 h-5" />
                    ) : (
                      <AlertTriangle className="w-5 h-5" />
                    )}
                  </div>

                  <div className="space-y-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-mono text-xs font-bold text-lux-300">
                        {item.rule_id}
                      </span>
                      <h4 className="text-sm font-semibold text-white truncate">
                        {item.rule_name}
                      </h4>
                      {item.severity && (
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider border ${getSeverityBadge(
                            item.severity
                          )}`}
                        >
                          {item.severity}
                        </span>
                      )}
                      {item.category && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-300 border border-slate-700">
                          {item.category}
                        </span>
                      )}
                    </div>

                    <div className="flex items-center space-x-3 text-xs text-slate-400">
                      {item.dataset_id && (
                        <span className="flex items-center space-x-1 font-mono text-slate-300">
                          <Database className="w-3 h-3 text-slate-500" />
                          <span>{item.dataset_id}</span>
                        </span>
                      )}
                      {item.message && (
                        <span className="truncate max-w-lg text-slate-300 text-xs">
                          {item.message}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Right: State Transition & Status Chip */}
                <div className="flex items-center space-x-4 shrink-0 pl-11 md:pl-0">
                  <div className="flex items-center space-x-2 text-xs font-mono">
                    <span className="px-2 py-0.5 rounded bg-rose-500/15 text-rose-400 border border-rose-500/30">
                      {item.previous_status || 'FAILED'}
                    </span>
                    <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
                    <span
                      className={`px-2 py-0.5 rounded border ${
                        item.current_status === 'PASSED'
                          ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                          : 'bg-rose-500/15 text-rose-400 border-rose-500/30'
                      }`}
                    >
                      {item.current_status || (isResolved ? 'PASSED' : 'FAILED')}
                    </span>
                  </div>

                  <span
                    data-testid={`status-badge-${item.rule_id}`}
                    className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold border space-x-1 ${
                      isResolved
                        ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                        : 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                    }`}
                  >
                    {isResolved && <Check className="w-3 h-3" />}
                    <span>{item.status}</span>
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

