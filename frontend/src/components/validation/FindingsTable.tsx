import React, { useState, useMemo } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Search,
  Filter,
  Eye,
  Target,
  ArrowUpDown,
  RotateCcw,
} from 'lucide-react';
import {
  RuleCategory,
  RuleSeverity,
  RuleStatus,
  ValidationFindingItem,
} from '../../types';

interface FindingsTableProps {
  findings: ValidationFindingItem[];
  isLoading?: boolean;
  selectedFindingId?: string | null;
  onSelectFinding: (finding: ValidationFindingItem) => void;
  onTraceImpact?: (finding: ValidationFindingItem) => void;
  availableDatasets?: string[];
  initialSeverityFilter?: RuleSeverity | 'ALL';
}

function getSeverityBadge(severity: RuleSeverity) {
  switch (severity) {
    case 'CRITICAL':
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider bg-rose-950/90 text-rose-300 border border-rose-700/60 shadow-sm">
          CRITICAL
        </span>
      );
    case 'HIGH':
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider bg-orange-950/80 text-orange-300 border border-orange-700/60 shadow-sm">
          HIGH
        </span>
      );
    case 'MEDIUM':
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold uppercase tracking-wider bg-amber-950/80 text-amber-300 border border-amber-700/60">
          MEDIUM
        </span>
      );
    case 'LOW':
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium uppercase tracking-wider bg-blue-950/70 text-blue-300 border border-blue-700/50">
          LOW
        </span>
      );
    case 'INFO':
    default:
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium uppercase tracking-wider bg-slate-800 text-slate-300 border border-slate-700">
          INFO
        </span>
      );
  }
}

function getStatusBadge(status: RuleStatus) {
  switch (status) {
    case 'PASSED':
      return (
        <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-status-healthy/15 text-status-healthy border border-status-healthy/30">
          <CheckCircle2 className="w-3 h-3" />
          <span>PASSED</span>
        </span>
      );
    case 'FAILED':
      return (
        <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-status-corrupted/15 text-status-corrupted border border-status-corrupted/30">
          <XCircle className="w-3 h-3" />
          <span>FAILED</span>
        </span>
      );
    case 'WARNING':
      return (
        <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-status-warning/15 text-status-warning border border-status-warning/30">
          <AlertTriangle className="w-3 h-3" />
          <span>WARNING</span>
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold bg-slate-800 text-slate-400 border border-slate-700">
          {status}
        </span>
      );
  }
}

function formatCategory(category: RuleCategory): string {
  return category.replace(/_/g, ' ');
}

export const FindingsTable: React.FC<FindingsTableProps> = ({
  findings,
  isLoading = false,
  selectedFindingId,
  onSelectFinding,
  onTraceImpact,
  availableDatasets,
  initialSeverityFilter = 'ALL',
}) => {
  const [severityFilter, setSeverityFilter] = useState<RuleSeverity | 'ALL'>(initialSeverityFilter);
  const [statusFilter, setStatusFilter] = useState<RuleStatus | 'ALL'>('ALL');
  const [datasetFilter, setDatasetFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [sortField, setSortField] = useState<'severity' | 'status' | 'dataset' | 'records'>('severity');
  const [sortAsc, setSortAsc] = useState<boolean>(false);

  // Distinct datasets for filtering
  const datasetOptions = useMemo(() => {
    if (availableDatasets && availableDatasets.length > 0) {
      return availableDatasets;
    }
    const unique = new Set<string>();
    findings.forEach((f) => unique.add(f.dataset_id));
    return Array.from(unique).sort();
  }, [availableDatasets, findings]);

  // Filtering findings
  const filteredFindings = useMemo(() => {
    return findings.filter((finding) => {
      // Severity filter
      if (severityFilter !== 'ALL' && finding.severity !== severityFilter) {
        return false;
      }
      // Status filter
      if (statusFilter !== 'ALL' && finding.status !== statusFilter) {
        return false;
      }
      // Dataset filter
      if (datasetFilter !== 'ALL' && finding.dataset_id !== datasetFilter) {
        return false;
      }
      // Search query filter
      if (searchQuery.trim() !== '') {
        const q = searchQuery.toLowerCase();
        const matchesId = finding.rule_id.toLowerCase().includes(q);
        const matchesName = finding.rule_name.toLowerCase().includes(q);
        const matchesDataset = finding.dataset_id.toLowerCase().includes(q);
        const matchesMessage = finding.message.toLowerCase().includes(q);
        const matchesCategory = finding.rule_category.toLowerCase().includes(q);
        if (!matchesId && !matchesName && !matchesDataset && !matchesMessage && !matchesCategory) {
          return false;
        }
      }
      return true;
    });
  }, [findings, severityFilter, statusFilter, datasetFilter, searchQuery]);

  // Sorting
  const sortedFindings = useMemo(() => {
    const list = [...filteredFindings];
    const severityWeight: Record<RuleSeverity, number> = {
      CRITICAL: 4,
      HIGH: 3,
      MEDIUM: 2,
      LOW: 1,
      INFO: 0,
    };
    const statusWeight: Record<string, number> = {
      FAILED: 3,
      WARNING: 2,
      ERROR: 3,
      SKIPPED: 1,
      PASSED: 0,
    };

    list.sort((a, b) => {
      let comparison = 0;
      switch (sortField) {
        case 'severity':
          comparison = (severityWeight[a.severity] ?? 0) - (severityWeight[b.severity] ?? 0);
          break;
        case 'status':
          comparison = (statusWeight[a.status] ?? 0) - (statusWeight[b.status] ?? 0);
          break;
        case 'dataset':
          comparison = a.dataset_id.localeCompare(b.dataset_id);
          break;
        case 'records':
          comparison = a.affected_record_count - b.affected_record_count;
          break;
        default:
          comparison = 0;
      }
      return sortAsc ? comparison : -comparison;
    });
    return list;
  }, [filteredFindings, sortField, sortAsc]);

  const handleSort = (field: 'severity' | 'status' | 'dataset' | 'records') => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  const handleResetFilters = () => {
    setSeverityFilter('ALL');
    setStatusFilter('ALL');
    setDatasetFilter('ALL');
    setSearchQuery('');
  };

  const hasActiveFilters =
    severityFilter !== 'ALL' ||
    statusFilter !== 'ALL' ||
    datasetFilter !== 'ALL' ||
    searchQuery.trim() !== '';

  return (
    <div
      className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm"
      data-testid="findings-table-container"
    >
      {/* Filters & Search Toolbar */}
      <div className="p-4 border-b border-slate-800 bg-slate-900/90 space-y-3">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          {/* Search Bar */}
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              role="searchbox"
              data-testid="filter-search"
              aria-label="Search findings by rule or dataset"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by rule ID, name, dataset, or issue..."
              className="w-full pl-9 pr-4 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-lux-500 focus:border-lux-500 transition-colors"
            />
          </div>

          {/* Filter Dropdowns */}
          <div className="flex flex-wrap items-center gap-2 text-xs">
            {/* Severity Filter */}
            <div className="flex items-center space-x-1.5">
              <label htmlFor="filter-severity" className="text-slate-400 font-medium">
                Severity:
              </label>
              <select
                id="filter-severity"
                data-testid="filter-severity"
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value as RuleSeverity | 'ALL')}
                className="bg-slate-950 border border-slate-700 text-slate-200 rounded-lg px-2.5 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-lux-500"
              >
                <option value="ALL">All Severities</option>
                <option value="CRITICAL">CRITICAL</option>
                <option value="HIGH">HIGH</option>
                <option value="MEDIUM">MEDIUM</option>
                <option value="LOW">LOW</option>
                <option value="INFO">INFO</option>
              </select>
            </div>

            {/* Status Filter */}
            <div className="flex items-center space-x-1.5">
              <label htmlFor="filter-status" className="text-slate-400 font-medium">
                Status:
              </label>
              <select
                id="filter-status"
                data-testid="filter-status"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as RuleStatus | 'ALL')}
                className="bg-slate-950 border border-slate-700 text-slate-200 rounded-lg px-2.5 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-lux-500"
              >
                <option value="ALL">All Statuses</option>
                <option value="FAILED">FAILED</option>
                <option value="WARNING">WARNING</option>
                <option value="PASSED">PASSED</option>
              </select>
            </div>

            {/* Dataset Filter */}
            <div className="flex items-center space-x-1.5">
              <label htmlFor="filter-dataset" className="text-slate-400 font-medium">
                Dataset:
              </label>
              <select
                id="filter-dataset"
                data-testid="filter-dataset"
                value={datasetFilter}
                onChange={(e) => setDatasetFilter(e.target.value)}
                className="bg-slate-950 border border-slate-700 text-slate-200 rounded-lg px-2.5 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-lux-500"
              >
                <option value="ALL">All Datasets</option>
                {datasetOptions.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
            </div>

            {/* Reset Filter Button */}
            {hasActiveFilters && (
              <button
                type="button"
                onClick={handleResetFilters}
                data-testid="reset-filters-btn"
                className="flex items-center space-x-1 px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700 transition-colors"
                title="Reset all filters"
              >
                <RotateCcw className="w-3 h-3" />
                <span>Reset</span>
              </button>
            )}
          </div>
        </div>

        {/* Active Filter Counter / Info */}
        <div className="flex items-center justify-between text-xs text-slate-400 pt-1">
          <div className="flex items-center space-x-2">
            <Filter className="w-3.5 h-3.5 text-lux-400" />
            <span>
              Showing <strong className="text-slate-200">{sortedFindings.length}</strong> of{' '}
              <strong className="text-slate-200">{findings.length}</strong> findings
            </span>
          </div>
          {severityFilter === 'CRITICAL' && (
            <span className="text-rose-400 font-medium">
              Filtered for critical integrity blockers
            </span>
          )}
        </div>
      </div>

      {/* Findings Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse" data-testid="findings-table">
          <thead className="bg-slate-950/60 border-b border-slate-800 text-slate-400">
            <tr>
              <th
                className="py-3 px-4 font-semibold cursor-pointer hover:text-white"
                onClick={() => handleSort('status')}
              >
                <div className="flex items-center space-x-1">
                  <span>Status</span>
                  <ArrowUpDown className="w-3 h-3 text-slate-400" />
                </div>
              </th>
              <th
                className="py-3 px-4 font-semibold cursor-pointer hover:text-white"
                onClick={() => handleSort('severity')}
              >
                <div className="flex items-center space-x-1">
                  <span>Severity</span>
                  <ArrowUpDown className="w-3 h-3 text-slate-400" />
                </div>
              </th>
              <th className="py-3 px-4 font-semibold">Rule & Issue Diagnostics</th>
              <th
                className="py-3 px-4 font-semibold cursor-pointer hover:text-white"
                onClick={() => handleSort('dataset')}
              >
                <div className="flex items-center space-x-1">
                  <span>Target Dataset</span>
                  <ArrowUpDown className="w-3 h-3 text-slate-400" />
                </div>
              </th>
              <th
                className="py-3 px-4 font-semibold text-right cursor-pointer hover:text-white"
                onClick={() => handleSort('records')}
              >
                <div className="flex items-center justify-end space-x-1">
                  <span>Affected Records</span>
                  <ArrowUpDown className="w-3 h-3 text-slate-400" />
                </div>
              </th>
              <th className="py-3 px-4 font-semibold text-right">Duration</th>
              <th className="py-3 px-4 font-semibold text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/80">
            {isLoading ? (
              <tr>
                <td colSpan={7} className="py-12 text-center text-slate-400">
                  <div className="inline-flex items-center space-x-2">
                    <div className="w-4 h-4 border-2 border-lux-500 border-t-transparent rounded-full animate-spin" />
                    <span>Evaluating validation checks...</span>
                  </div>
                </td>
              </tr>
            ) : sortedFindings.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-12 text-center text-slate-400 space-y-2">
                  <div className="w-10 h-10 mx-auto rounded-full bg-slate-800/80 flex items-center justify-center text-slate-400">
                    <CheckCircle2 className="w-5 h-5 text-status-healthy" />
                  </div>
                  <p className="text-sm font-semibold text-slate-300">No findings match active filters</p>
                  <p className="text-xs text-slate-400">
                    Try adjusting or resetting your search, severity, or dataset filters.
                  </p>
                  {hasActiveFilters && (
                    <button
                      type="button"
                      onClick={handleResetFilters}
                      className="mt-2 inline-flex items-center space-x-1 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-lux-300 rounded-lg text-xs font-semibold"
                    >
                      <span>Clear all filters</span>
                    </button>
                  )}
                </td>
              </tr>
            ) : (
              sortedFindings.map((finding) => {
                const isSelected = selectedFindingId === finding.id;
                const violationRatio =
                  finding.total_record_count > 0
                    ? ((finding.affected_record_count / finding.total_record_count) * 100).toFixed(1)
                    : '0';

                return (
                  <tr
                    key={finding.id}
                    data-testid={`finding-row-${finding.rule_id}`}
                    onClick={() => onSelectFinding(finding)}
                    className={`transition-colors cursor-pointer group ${
                      isSelected
                        ? 'bg-lux-950/40 border-l-2 border-l-lux-500'
                        : 'hover:bg-slate-800/50'
                    }`}
                  >
                    {/* Status */}
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      {getStatusBadge(finding.status)}
                    </td>

                    {/* Severity */}
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      {getSeverityBadge(finding.severity)}
                    </td>

                    {/* Rule Info & Diagnostics */}
                    <td className="py-3.5 px-4 max-w-md">
                      <div className="space-y-1">
                        <div className="flex items-center space-x-2">
                          <code className="font-mono font-bold text-lux-300 text-[11px] bg-slate-950 px-1.5 py-0.5 rounded border border-slate-800">
                            {finding.rule_id}
                          </code>
                          <span className="font-semibold text-white group-hover:text-lux-200 transition-colors">
                            {finding.rule_name}
                          </span>
                          <span className="text-[10px] uppercase font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 border border-slate-700/60">
                            {formatCategory(finding.rule_category)}
                          </span>
                        </div>
                        <p className="text-xs text-slate-400 line-clamp-1">
                          {finding.message}
                        </p>
                      </div>
                    </td>

                    {/* Dataset */}
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <span className="font-mono text-slate-200 bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700 text-xs">
                        {finding.dataset_id}
                      </span>
                    </td>

                    {/* Violations / Total */}
                    <td className="py-3.5 px-4 text-right whitespace-nowrap">
                      <div className="space-y-0.5">
                        <div className="font-mono font-bold text-slate-200">
                          <span
                            className={
                              finding.affected_record_count > 0
                                ? finding.severity === 'CRITICAL'
                                  ? 'text-rose-400'
                                  : 'text-amber-400'
                                : 'text-slate-400'
                            }
                          >
                            {finding.affected_record_count.toLocaleString()}
                          </span>
                          <span className="text-slate-400 font-normal">
                            {' '}/ {finding.total_record_count.toLocaleString()}
                          </span>
                        </div>
                        {finding.affected_record_count > 0 && (
                          <div className="text-[10px] text-slate-400 font-mono">
                            {violationRatio}% affected
                          </div>
                        )}
                      </div>
                    </td>

                    {/* Execution Duration */}
                    <td className="py-3.5 px-4 text-right whitespace-nowrap font-mono text-slate-400">
                      {finding.execution_duration_ms} ms
                    </td>

                    {/* Actions */}
                    <td className="py-3.5 px-4 text-right whitespace-nowrap">
                      <div className="flex items-center justify-end space-x-1.5">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            onSelectFinding(finding);
                          }}
                          aria-label={`View evidence for ${finding.rule_id}`}
                          data-testid={`view-evidence-btn-${finding.rule_id}`}
                          className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition-colors"
                          title="Inspect sample records and evidence"
                        >
                          <Eye className="w-3.5 h-3.5" />
                        </button>
                        {onTraceImpact && (
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              onTraceImpact(finding);
                            }}
                            aria-label={`Trace impact for ${finding.rule_id}`}
                            data-testid={`trace-impact-btn-${finding.rule_id}`}
                            className="flex items-center space-x-1 px-2.5 py-1.5 rounded-lg bg-lux-900/60 hover:bg-lux-800/80 text-lux-300 border border-lux-700/50 hover:border-lux-600 transition-colors text-[11px] font-semibold"
                            title="Trace downstream blast radius in lineage DAG"
                          >
                            <Target className="w-3.5 h-3.5 text-lux-400" />
                            <span className="hidden sm:inline">Trace Impact</span>
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

