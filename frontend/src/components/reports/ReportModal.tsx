import React, { useState, useEffect, useCallback } from 'react';
import {
  FileText,
  Download,
  Code,
  Copy,
  Check,
  ExternalLink,
  Loader2,
  AlertTriangle,
  FileCheck,
} from 'lucide-react';
import { Modal } from '../common/Modal';
import { generateReport, exportReportArtifact } from '../../api/reports';
import { InvestigationResponse, ReportGenerateResponse } from '../../types';
import { downloadFile } from './download';

export interface ReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  scenarioId: string;
  investigation?: InvestigationResponse | null;
  onReportGenerated?: (report: ReportGenerateResponse) => void;
}

export const ReportModal: React.FC<ReportModalProps> = ({
  isOpen,
  onClose,
  scenarioId,
  investigation,
  onReportGenerated,
}) => {
  const [reportTitle, setReportTitle] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isLoadingPreview, setIsLoadingPreview] = useState(false);
  const [generatedReport, setGeneratedReport] = useState<ReportGenerateResponse | null>(null);
  const [activeTab, setActiveTab] = useState<'html' | 'json'>('html');
  const [htmlContent, setHtmlContent] = useState<string>('');
  const [jsonContent, setJsonContent] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // Initialize title when modal opens
  useEffect(() => {
    if (isOpen) {
      if (investigation?.title) {
        setReportTitle(`Incident Report: ${investigation.title}`);
      } else {
        setReportTitle(`Incident Investigation Report — ${scenarioId}`);
      }
      setError(null);
    }
  }, [isOpen, investigation, scenarioId]);

  const loadReportArtifacts = useCallback(async (reportId: string) => {
    setIsLoadingPreview(true);
    try {
      const [html, json] = await Promise.all([
        exportReportArtifact(reportId, 'html'),
        exportReportArtifact(reportId, 'json'),
      ]);
      setHtmlContent(html);
      setJsonContent(json);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch report preview artifacts.');
    } finally {
      setIsLoadingPreview(false);
    }
  }, []);

  const handleGenerate = async () => {
    setIsGenerating(true);
    setError(null);
    try {
      const payload = {
        scenario_id: scenarioId,
        investigation_id: investigation?.id,
        title: reportTitle.trim() || undefined,
        verified_facts: investigation?.verified_facts || [],
        hypotheses: investigation?.hypotheses || [],
        action_items: investigation?.action_items || [],
      };

      const response = await generateReport(payload);
      setGeneratedReport(response);
      if (onReportGenerated) {
        onReportGenerated(response);
      }
      await loadReportArtifacts(response.report_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate incident report.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDownloadHtml = () => {
    if (!generatedReport || !htmlContent) return;
    const filename = `${generatedReport.report_id}.html`;
    downloadFile(htmlContent, filename, 'text/html; charset=utf-8');
  };

  const handleDownloadJson = () => {
    if (!generatedReport || !jsonContent) return;
    const filename = `${generatedReport.report_id}.json`;
    downloadFile(jsonContent, filename, 'application/json');
  };

  const handleCopyJson = async () => {
    if (!jsonContent) return;
    try {
      await navigator.clipboard.writeText(jsonContent);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback
      setCopied(false);
    }
  };

  const handleOpenHtmlInNewTab = () => {
    if (!htmlContent) return;
    const blob = new Blob([htmlContent], { type: 'text/html; charset=utf-8' });
    const url = URL.createObjectURL(blob);
    window.open(url, '_blank');
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Incident Investigation Report Generator"
      description="Generate reproducible, immutable JSON and safe standalone HTML reports containing concrete validation findings, impact radius, and lineage."
      maxWidth="max-w-5xl"
      dialogId="report-export-modal"
    >
      <div className="space-y-6">
        {/* Error Notification */}
        {error && (
          <div
            role="alert"
            className="p-4 bg-rose-950/60 border border-rose-800/80 rounded-lg flex items-start space-x-3 text-rose-200 text-sm"
          >
            <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="font-semibold text-rose-300">Report Action Failed</p>
              <p className="text-xs text-rose-300/90 mt-0.5">{error}</p>
            </div>
          </div>
        )}

        {/* Configuration or Generator Header */}
        {!generatedReport ? (
          <div className="space-y-4 bg-slate-950/60 p-5 rounded-xl border border-slate-800">
            <div>
              <label
                htmlFor="report-title-input"
                className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1"
              >
                Report Title
              </label>
              <input
                id="report-title-input"
                type="text"
                value={reportTitle}
                onChange={(e) => setReportTitle(e.target.value)}
                placeholder="e.g. Incident Report: Monday Morning Revenue Anomaly"
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-lux-500 focus:border-transparent"
              />
            </div>

            {investigation && (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 text-xs">
                <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                  <span className="text-slate-400 block">Verified Facts</span>
                  <span className="text-sm font-semibold text-emerald-400">
                    {investigation.verified_facts.length} items
                  </span>
                </div>
                <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                  <span className="text-slate-400 block">Working Hypotheses</span>
                  <span className="text-sm font-semibold text-amber-400">
                    {investigation.hypotheses.length} items
                  </span>
                </div>
                <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                  <span className="text-slate-400 block">Remediation Actions</span>
                  <span className="text-sm font-semibold text-lux-300">
                    {investigation.action_items.length} items
                  </span>
                </div>
              </div>
            )}

            <div className="pt-2 flex justify-end">
              <button
                type="button"
                onClick={handleGenerate}
                disabled={isGenerating || !reportTitle.trim()}
                data-testid="generate-report-btn"
                className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-lg bg-lux-600 hover:bg-lux-500 disabled:bg-slate-800 disabled:text-slate-500 text-white font-medium text-sm transition-colors shadow-lg shadow-lux-900/30"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Compiling Report Artifacts...</span>
                  </>
                ) : (
                  <>
                    <FileCheck className="w-4 h-4" />
                    <span>Generate Incident Report</span>
                  </>
                )}
              </button>
            </div>
          </div>
        ) : (
          /* Report Generated Success Banner & Export Controls */
          <div className="space-y-4">
            <div className="bg-slate-950/80 p-4 rounded-xl border border-lux-800/60 flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <div className="flex items-center space-x-2">
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-emerald-950 border border-emerald-800 text-emerald-300">
                    GENERATED
                  </span>
                  <span className="text-xs font-mono text-lux-300" data-testid="generated-report-id">
                    {generatedReport.report_id}
                  </span>
                </div>
                <h3 className="text-base font-bold text-white mt-1">{reportTitle}</h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Generated at {new Date(generatedReport.generated_at).toLocaleString()}
                </p>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  onClick={handleDownloadHtml}
                  disabled={!htmlContent || isLoadingPreview}
                  data-testid="download-html-btn"
                  className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-lux-600 hover:bg-lux-500 text-white text-xs font-medium transition-colors shadow-sm"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download HTML</span>
                </button>

                <button
                  type="button"
                  onClick={handleDownloadJson}
                  disabled={!jsonContent || isLoadingPreview}
                  data-testid="download-json-btn"
                  className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-medium transition-colors"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download JSON</span>
                </button>

                <button
                  type="button"
                  onClick={() => setGeneratedReport(null)}
                  className="text-xs text-slate-400 hover:text-slate-200 underline ml-2"
                >
                  Regenerate
                </button>
              </div>
            </div>

            {/* In-App Tabbed Preview */}
            <div className="border border-slate-800 rounded-xl overflow-hidden bg-slate-900">
              {/* Tab navigation */}
              <div className="flex items-center justify-between px-4 py-2.5 bg-slate-950 border-b border-slate-800">
                <div className="flex items-center space-x-2">
                  <button
                    type="button"
                    onClick={() => setActiveTab('html')}
                    className={`inline-flex items-center space-x-1.5 px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                      activeTab === 'html'
                        ? 'bg-lux-900/80 text-lux-200 border border-lux-700/60'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                    }`}
                  >
                    <FileText className="w-3.5 h-3.5" />
                    <span>HTML Preview</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setActiveTab('json')}
                    className={`inline-flex items-center space-x-1.5 px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                      activeTab === 'json'
                        ? 'bg-lux-900/80 text-lux-200 border border-lux-700/60'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                    }`}
                  >
                    <Code className="w-3.5 h-3.5" />
                    <span>JSON Artifact</span>
                  </button>
                </div>

                {/* Sub-actions per tab */}
                <div className="flex items-center space-x-2">
                  {activeTab === 'html' ? (
                    <button
                      type="button"
                      onClick={handleOpenHtmlInNewTab}
                      disabled={!htmlContent}
                      title="Open full report in a new browser tab"
                      className="inline-flex items-center space-x-1 text-xs text-slate-400 hover:text-lux-300 transition-colors"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                      <span>Open in New Tab</span>
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={handleCopyJson}
                      disabled={!jsonContent}
                      className="inline-flex items-center space-x-1 text-xs text-slate-400 hover:text-lux-300 transition-colors"
                    >
                      {copied ? (
                        <>
                          <Check className="w-3.5 h-3.5 text-emerald-400" />
                          <span className="text-emerald-400">Copied!</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3.5 h-3.5" />
                          <span>Copy JSON</span>
                        </>
                      )}
                    </button>
                  )}
                </div>
              </div>

              {/* Preview Body */}
              <div className="p-4">
                {isLoadingPreview ? (
                  <div className="flex flex-col items-center justify-center py-16 space-y-3">
                    <Loader2 className="w-6 h-6 animate-spin text-lux-400" />
                    <p className="text-xs text-slate-400">Loading artifact content...</p>
                  </div>
                ) : activeTab === 'html' ? (
                  <div className="space-y-2">
                    <iframe
                      title="Sanitized HTML Incident Report Preview"
                      srcDoc={htmlContent}
                      data-testid="html-report-preview-frame"
                      className="w-full h-[520px] rounded-lg border border-slate-700 bg-white"
                      sandbox="allow-same-origin"
                    />
                    <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1">
                      <span>Preview rendered in secure sandboxed container with CSP enforcement.</span>
                      <a
                        href={generatedReport.html_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-lux-400 hover:underline inline-flex items-center gap-1"
                      >
                        Direct URL: {generatedReport.html_url}
                      </a>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <pre
                      data-testid="json-report-preview"
                      className="text-xs font-mono p-4 bg-slate-950 text-slate-200 border border-slate-800 rounded-lg overflow-auto max-h-[520px] whitespace-pre"
                    >
                      {(() => {
                        try {
                          return JSON.stringify(JSON.parse(jsonContent), null, 2);
                        } catch {
                          return jsonContent;
                        }
                      })()}
                    </pre>
                    <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1">
                      <span>Immutable incident record formatted as structured JSON.</span>
                      <a
                        href={generatedReport.json_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-lux-400 hover:underline inline-flex items-center gap-1"
                      >
                        Direct URL: {generatedReport.json_url}
                      </a>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
};
