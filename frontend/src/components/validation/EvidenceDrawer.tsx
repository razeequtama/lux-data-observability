import React, { useEffect, useRef } from 'react';
import {
  X,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  FileText,
  Target,
  Database,
  Layers,
  ArrowRight,
  Code2,
} from 'lucide-react';
import { ValidationFindingItem } from '../../types';

interface EvidenceDrawerProps {
  finding: ValidationFindingItem | null;
  isOpen: boolean;
  onClose: () => void;
  onTraceImpact?: (finding: ValidationFindingItem) => void;
}

export const EvidenceDrawer: React.FC<EvidenceDrawerProps> = ({
  finding,
  isOpen,
  onClose,
  onTraceImpact,
}) => {
  const drawerRef = useRef<HTMLDivElement>(null);
  const previouslyFocusedElementRef = useRef<HTMLElement | null>(null);

  // Accessible Keyboard Focus Trap and Escape Listener
  useEffect(() => {
    if (isOpen) {
      previouslyFocusedElementRef.current = document.activeElement as HTMLElement;

      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === 'Escape') {
          e.preventDefault();
          onClose();
          return;
        }

        if (e.key === 'Tab' && drawerRef.current) {
          const focusableSelectors =
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
          const focusableElements = drawerRef.current.querySelectorAll<HTMLElement>(focusableSelectors);
          if (focusableElements.length === 0) return;

          const firstElement = focusableElements[0];
          const lastElement = focusableElements[focusableElements.length - 1];

          if (e.shiftKey) {
            if (document.activeElement === firstElement) {
              e.preventDefault();
              lastElement.focus();
            }
          } else {
            if (document.activeElement === lastElement) {
              e.preventDefault();
              firstElement.focus();
            }
          }
        }
      };

      document.addEventListener('keydown', handleKeyDown);

      // Focus first focusable element inside drawer
      const timer = setTimeout(() => {
        if (drawerRef.current) {
          const focusable = drawerRef.current.querySelector<HTMLElement>(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
          );
          if (focusable) {
            focusable.focus();
          } else {
            drawerRef.current.focus();
          }
        }
      }, 50);

      return () => {
        document.removeEventListener('keydown', handleKeyDown);
        clearTimeout(timer);
        if (previouslyFocusedElementRef.current && typeof previouslyFocusedElementRef.current.focus === 'function') {
          previouslyFocusedElementRef.current.focus();
        }
      };
    }
  }, [isOpen, onClose]);

  if (!isOpen || !finding) {
    return null;
  }

  const { evidence } = finding;
  const sampleDuplicates = evidence.sample_duplicates || [];
  const sampleOrphanedKeys = evidence.sample_orphaned_keys || [];
  const sampleViolations = evidence.sample_violations || [];

  // Determine Observed vs Expected values
  let expectedSummary = 'No violations (100% compliance with quality rules)';
  let observedSummary = `${finding.affected_record_count} violating records detected`;

  if (finding.rule_category === 'UNIQUENESS') {
    expectedSummary = '0 duplicate records (Every key must be unique)';
    observedSummary = `${finding.affected_record_count} duplicate keys detected in dataset`;
  } else if (finding.rule_category === 'REFERENTIAL_INTEGRITY') {
    expectedSummary = 'All foreign keys exist in target dimension dataset';
    observedSummary = `${finding.affected_record_count} orphaned records referencing missing keys`;
  } else if (finding.rule_category === 'VALUE_RANGE') {
    expectedSummary = 'Values strictly within declared valid range (e.g. quantity >= 0)';
    observedSummary = `${finding.affected_record_count} values outside acceptable boundaries`;
  } else if (finding.rule_category === 'FRESHNESS' || finding.rule_category === 'TEMPORAL_ANOMALY') {
    const threshold = evidence.threshold_hours ?? 2.0;
    const maxGap = evidence.max_gap_hours ? Number(evidence.max_gap_hours).toFixed(2) : 'N/A';
    expectedSummary = `Maximum temporal sync gap <= ${threshold} hours`;
    observedSummary = `Observed temporal gap of ${maxGap} hours`;
  } else if (evidence.expected_value !== undefined && evidence.observed_value !== undefined) {
    expectedSummary = String(evidence.expected_value);
    observedSummary = String(evidence.observed_value);
  }

  return (
    <div
      className="fixed inset-0 z-50 overflow-hidden"
      role="dialog"
      aria-modal="true"
      aria-labelledby="evidence-drawer-title"
      aria-describedby="evidence-drawer-desc"
      data-testid="evidence-drawer"
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-950/70 backdrop-blur-sm transition-opacity"
        onClick={onClose}
        aria-hidden="true"
        data-testid="evidence-drawer-backdrop"
      />

      {/* Slide-over Drawer Panel */}
      <div className="fixed inset-y-0 right-0 max-w-2xl w-full flex pl-6 sm:pl-10">
        <div
          ref={drawerRef}
          tabIndex={-1}
          className="w-full bg-slate-900 border-l border-slate-800 shadow-2xl flex flex-col overflow-hidden focus:outline-none"
        >
          {/* Header */}
          <div className="p-6 border-b border-slate-800 bg-slate-950/60 flex items-start justify-between">
            <div className="space-y-1">
              <div className="flex items-center space-x-2">
                <code className="font-mono font-bold text-xs bg-lux-950/80 text-lux-300 px-2 py-0.5 rounded border border-lux-700/50">
                  {finding.rule_id}
                </code>
                <span
                  className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[11px] font-bold ${
                    finding.status === 'PASSED'
                      ? 'bg-status-healthy/15 text-status-healthy border border-status-healthy/30'
                      : finding.status === 'FAILED'
                        ? 'bg-status-corrupted/15 text-status-corrupted border border-status-corrupted/30'
                        : 'bg-status-warning/15 text-status-warning border border-status-warning/30'
                  }`}
                >
                  {finding.status === 'PASSED' && <CheckCircle2 className="w-3 h-3" />}
                  {finding.status === 'FAILED' && <XCircle className="w-3 h-3" />}
                  {finding.status === 'WARNING' && <AlertTriangle className="w-3 h-3" />}
                  <span>{finding.status}</span>
                </span>
                <span className="text-[11px] font-semibold px-2 py-0.5 rounded uppercase tracking-wider bg-slate-800 text-slate-300 border border-slate-700">
                  {finding.severity}
                </span>
              </div>
              <h2
                id="evidence-drawer-title"
                className="text-lg font-bold text-white tracking-tight pt-1"
              >
                {finding.rule_name}
              </h2>
              <p id="evidence-drawer-desc" className="text-xs text-slate-400">
                Data quality evidence, observed discrepancies, and affected record coordinates
              </p>
            </div>

            <button
              type="button"
              onClick={onClose}
              data-testid="close-evidence-drawer"
              aria-label="Close evidence drawer"
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Drawer Body Scrollable Content */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {/* Metadata Bar */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-950/50 p-4 rounded-xl border border-slate-800 text-xs">
              <div>
                <span className="text-slate-400 block text-[11px]">Dataset</span>
                <div className="flex items-center space-x-1.5 mt-0.5">
                  <Database className="w-3.5 h-3.5 text-lux-400" />
                  <span className="font-mono font-semibold text-slate-200">
                    {finding.dataset_id}
                  </span>
                </div>
              </div>
              <div>
                <span className="text-slate-400 block text-[11px]">Rule Category</span>
                <div className="flex items-center space-x-1.5 mt-0.5">
                  <Layers className="w-3.5 h-3.5 text-lux-400" />
                  <span className="font-medium text-slate-200">
                    {finding.rule_category.replace(/_/g, ' ')}
                  </span>
                </div>
              </div>
              <div>
                <span className="text-slate-400 block text-[11px]">Violations</span>
                <div className="mt-0.5 font-mono font-bold text-rose-400">
                  {finding.affected_record_count} / {finding.total_record_count} rows
                </div>
              </div>
              <div>
                <span className="text-slate-400 block text-[11px]">Evaluation Time</span>
                <div className="mt-0.5 font-mono text-slate-300">
                  {finding.execution_duration_ms} ms
                </div>
              </div>
            </div>

            {/* Diagnostic Message */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-1.5">
              <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center space-x-1.5">
                <FileText className="w-3.5 h-3.5 text-lux-400" />
                <span>Engine Diagnosis</span>
              </span>
              <p className="text-xs text-slate-200 leading-relaxed font-sans bg-slate-950 p-3 rounded-lg border border-slate-800">
                {finding.message}
              </p>
            </div>

            {/* Observed vs Expected Comparison Card */}
            <div
              className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3"
              data-testid="observed-vs-expected-card"
            >
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Observed vs Expected Expectations
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                {/* Expected */}
                <div className="bg-emerald-950/20 border border-emerald-900/40 rounded-lg p-3 space-y-1">
                  <span className="text-[11px] font-bold text-emerald-400 uppercase tracking-wider flex items-center space-x-1">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Expected Contract</span>
                  </span>
                  <p className="text-slate-200 font-medium pt-0.5 font-mono text-[11px]">
                    {expectedSummary}
                  </p>
                </div>

                {/* Observed */}
                <div className="bg-rose-950/20 border border-rose-900/40 rounded-lg p-3 space-y-1">
                  <span className="text-[11px] font-bold text-rose-400 uppercase tracking-wider flex items-center space-x-1">
                    <XCircle className="w-3.5 h-3.5" />
                    <span>Observed Reality</span>
                  </span>
                  <p className="text-slate-200 font-medium pt-0.5 font-mono text-[11px]">
                    {observedSummary}
                  </p>
                </div>
              </div>
            </div>

            {/* Sample Records & Violations Section */}
            <div className="space-y-3" data-testid="evidence-samples-section">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Sample Violating Records & Line Numbers
                </h3>
                {evidence.sample_duplicates_truncated && (
                  <span className="text-[11px] font-mono text-amber-400 bg-amber-950/50 px-2 py-0.5 rounded border border-amber-800/40">
                    Capped at 50 samples
                  </span>
                )}
              </div>

              {/* Duplicate Records Table (VAL-ORD-001) */}
              {sampleDuplicates.length > 0 && (
                <div className="border border-slate-800 rounded-xl overflow-hidden bg-slate-950">
                  <div className="p-3 bg-slate-900/90 border-b border-slate-800 text-xs font-semibold text-slate-300 flex items-center justify-between">
                    <span>Duplicate Key Occurrences</span>
                    <span className="text-slate-400 font-mono text-[11px]">
                      {sampleDuplicates.length} sample groups
                    </span>
                  </div>
                  <div className="overflow-x-auto max-h-60">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead className="bg-slate-900/40 border-b border-slate-800 text-slate-400 font-medium">
                        <tr>
                          <th className="py-2 px-3">Duplicate Key (order_id)</th>
                          <th className="py-2 px-3">Occurrences</th>
                          <th className="py-2 px-3">Line / Row Numbers</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                        {sampleDuplicates.map((dup, idx) => (
                          <tr key={idx} className="hover:bg-slate-900/40">
                            <td className="py-2 px-3 font-semibold text-lux-300">
                              {dup.order_id || String(Object.values(dup)[0])}
                            </td>
                            <td className="py-2 px-3 text-rose-400 font-bold">
                              {dup.occurrences}x
                            </td>
                            <td className="py-2 px-3 text-slate-300">
                              {dup.row_indices && Array.isArray(dup.row_indices)
                                ? dup.row_indices
                                    .map((i) => `#${Number(i) + 1}`) // 1-indexed for human readability
                                    .join(', ')
                                : 'N/A'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Broken Foreign Keys (VAL-ORD-002) */}
              {sampleOrphanedKeys.length > 0 && (
                <div className="border border-slate-800 rounded-xl overflow-hidden bg-slate-950 p-4 space-y-3">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-slate-300">
                      Sample Orphaned Foreign Keys (Missing in products.csv):
                    </span>
                    <span className="font-mono text-rose-400 font-bold">
                      {sampleOrphanedKeys.length} keys
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {sampleOrphanedKeys.map((key, idx) => (
                      <span
                        key={idx}
                        className="font-mono text-xs bg-rose-950/60 text-rose-300 border border-rose-800/50 px-2 py-0.5 rounded"
                      >
                        {key}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Sample Violations Rows */}
              {sampleViolations.length > 0 && (
                <div className="border border-slate-800 rounded-xl overflow-hidden bg-slate-950">
                  <div className="p-3 bg-slate-900/90 border-b border-slate-800 text-xs font-semibold text-slate-300 flex items-center justify-between">
                    <span>Violating Row Coordinates</span>
                    <span className="text-slate-400 font-mono text-[11px]">
                      {sampleViolations.length} records
                    </span>
                  </div>
                  <div className="overflow-x-auto max-h-60">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead className="bg-slate-900/40 border-b border-slate-800 text-slate-400 font-medium">
                        <tr>
                          <th className="py-2 px-3">Line / Row</th>
                          <th className="py-2 px-3">Violation Details</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                        {sampleViolations.map((v, idx) => (
                          <tr key={idx} className="hover:bg-slate-900/40">
                            <td className="py-2 px-3 text-lux-300 font-bold">
                              {v.row_index !== undefined ? `#${Number(v.row_index) + 1}` : `#${idx + 1}`}
                            </td>
                            <td className="py-2 px-3 text-slate-200">
                              {Object.entries(v)
                                .filter(([k]) => k !== 'row_index')
                                .map(([k, val]) => `${k}: ${val}`)
                                .join(' | ')}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Temporal Gaps / Freshness Evidence */}
              {evidence.max_gap_hours !== undefined && (
                <div className="border border-slate-800 rounded-xl p-4 bg-slate-950 space-y-2 text-xs">
                  <span className="font-semibold text-slate-300 block">
                    Observed Ingestion Temporal Gap:
                  </span>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 font-mono">
                    <div className="bg-slate-900 p-2 rounded border border-slate-800">
                      <span className="text-slate-400 block text-[10px]">Max Gap</span>
                      <span className="text-amber-400 font-bold">
                        {Number(evidence.max_gap_hours).toFixed(2)} hours
                      </span>
                    </div>
                    {evidence.gap_start && (
                      <div className="bg-slate-900 p-2 rounded border border-slate-800">
                        <span className="text-slate-400 block text-[10px]">Gap Window Start</span>
                        <span className="text-slate-200">
                          {String(evidence.gap_start)}
                        </span>
                      </div>
                    )}
                    {evidence.gap_end && (
                      <div className="bg-slate-900 p-2 rounded border border-slate-800">
                        <span className="text-slate-400 block text-[10px]">Gap Window End</span>
                        <span className="text-slate-200">
                          {String(evidence.gap_end)}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Fallback if no structured samples */}
              {sampleDuplicates.length === 0 &&
                sampleOrphanedKeys.length === 0 &&
                sampleViolations.length === 0 &&
                evidence.max_gap_hours === undefined && (
                  <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl text-center text-xs text-slate-400">
                    No individual row violations recorded. Check status: {finding.status}.
                  </div>
                )}
            </div>

            {/* Raw JSON Diagnostics Expandable Panel */}
            <details className="group border border-slate-800 rounded-xl bg-slate-950/60 overflow-hidden text-xs">
              <summary className="p-3 font-semibold text-slate-400 hover:text-slate-200 cursor-pointer flex items-center justify-between select-none">
                <span className="flex items-center space-x-1.5">
                  <Code2 className="w-3.5 h-3.5 text-lux-400" />
                  <span>Raw Evidence Diagnostics (JSON)</span>
                </span>
                <span className="text-[10px] text-slate-400 font-mono">Click to toggle</span>
              </summary>
              <div className="p-4 border-t border-slate-800 bg-slate-950">
                <pre
                  data-testid="raw-evidence-json"
                  className="font-mono text-[11px] text-slate-300 overflow-x-auto p-2 bg-slate-900 rounded-lg border border-slate-800/80 leading-relaxed max-h-60"
                >
                  {JSON.stringify(evidence, null, 2)}
                </pre>
              </div>
            </details>
          </div>

          {/* Drawer Footer Actions */}
          <div className="p-4 border-t border-slate-800 bg-slate-950/80 flex items-center justify-between gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-semibold transition-colors"
            >
              Close Drawer
            </button>

            {onTraceImpact && (
              <button
                type="button"
                onClick={() => {
                  onClose();
                  onTraceImpact(finding);
                }}
                data-testid="drawer-trace-impact-btn"
                className="flex items-center space-x-2 px-4 py-2 bg-lux-700 hover:bg-lux-600 text-white rounded-lg text-xs font-semibold transition-colors shadow-sm"
              >
                <Target className="w-4 h-4 text-lux-200" />
                <span>Trace Downstream Impact</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

