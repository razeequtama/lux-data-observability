import React, { useState, useEffect, useCallback } from 'react';
import {
  FileText,
  ShieldCheck,
  Lightbulb,
  CheckSquare,
  Square,
  Plus,
  Trash2,
  Save,
  Sparkles,
  AlertTriangle,
  Loader2,
  CheckCircle2,
  GitFork,
  ArrowRight,
} from 'lucide-react';
import {
  listInvestigations,
  createInvestigation,
  updateInvestigation,
  synthesizeInvestigation,
} from '../../api/investigations';
import { InvestigationResponse, InvestigationStatus } from '../../types';
import { ReportModal } from './ReportModal';

export interface InvestigationWorkspaceProps {
  scenarioId: string;
  onNavigateToLineage?: (nodeId?: string) => void;
  onNavigateToValidations?: () => void;
}

export const InvestigationWorkspace: React.FC<InvestigationWorkspaceProps> = ({
  scenarioId,
  onNavigateToLineage,
  onNavigateToValidations,
}) => {
  const [investigations, setInvestigations] = useState<InvestigationResponse[]>([]);
  const [activeInvestigation, setActiveInvestigation] = useState<InvestigationResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Form state
  const [title, setTitle] = useState('');
  const [status, setStatus] = useState<string>('INVESTIGATING');
  const [verifiedFacts, setVerifiedFacts] = useState<string[]>([]);
  const [hypotheses, setHypotheses] = useState<string[]>([]);
  const [actionItems, setActionItems] = useState<string[]>([]);

  // Input states for new items
  const [newFact, setNewFact] = useState('');
  const [newHypothesis, setNewHypothesis] = useState('');
  const [newActionItem, setNewActionItem] = useState('');

  // Report modal state
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);

  const fetchInvestigations = useCallback(
    async (preferSynthesizeIfEmpty = false) => {
      setIsLoading(true);
      setError(null);
      try {
        const list = await listInvestigations({ scenarioId });
        setInvestigations(list);
        if (list.length > 0) {
          const active = list[0];
          setActiveInvestigation(active);
          setTitle(active.title);
          setStatus(active.status);
          setVerifiedFacts(active.verified_facts || []);
          setHypotheses(active.hypotheses || []);
          setActionItems(active.action_items || []);
        } else if (preferSynthesizeIfEmpty) {
          // Auto-synthesize initial workspace if none exists
          const synthesized = await synthesizeInvestigation({ scenario_id: scenarioId });
          setInvestigations([synthesized]);
          setActiveInvestigation(synthesized);
          setTitle(synthesized.title);
          setStatus(synthesized.status);
          setVerifiedFacts(synthesized.verified_facts || []);
          setHypotheses(synthesized.hypotheses || []);
          setActionItems(synthesized.action_items || []);
        } else {
          setActiveInvestigation(null);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch investigations.');
      } finally {
        setIsLoading(false);
      }
    },
    [scenarioId]
  );

  useEffect(() => {
    fetchInvestigations(false);
  }, [fetchInvestigations]);

  const handleSynthesize = async () => {
    setIsSynthesizing(true);
    setError(null);
    try {
      const synthesized = await synthesizeInvestigation({ scenario_id: scenarioId });
      setInvestigations((prev) => [synthesized, ...prev]);
      setActiveInvestigation(synthesized);
      setTitle(synthesized.title);
      setStatus(synthesized.status);
      setVerifiedFacts(synthesized.verified_facts || []);
      setHypotheses(synthesized.hypotheses || []);
      setActionItems(synthesized.action_items || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to synthesize investigation.');
    } finally {
      setIsSynthesizing(false);
    }
  };

  const handleSelectInvestigation = (id: string) => {
    const inv = investigations.find((i) => i.id === id);
    if (inv) {
      setActiveInvestigation(inv);
      setTitle(inv.title);
      setStatus(inv.status);
      setVerifiedFacts(inv.verified_facts || []);
      setHypotheses(inv.hypotheses || []);
      setActionItems(inv.action_items || []);
      setSaveSuccess(false);
    }
  };

  const handleCreateNew = async () => {
    setIsSaving(true);
    try {
      const created = await createInvestigation({
        scenario_id: scenarioId,
        title: `Investigation: ${scenarioId.replace(/_/g, ' ')}`,
        status: 'INVESTIGATING',
        verified_facts: [],
        hypotheses: [],
        action_items: [],
      });
      setInvestigations((prev) => [created, ...prev]);
      setActiveInvestigation(created);
      setTitle(created.title);
      setStatus(created.status);
      setVerifiedFacts([]);
      setHypotheses([]);
      setActionItems([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create new investigation.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveChanges = async () => {
    if (!activeInvestigation) return;
    setIsSaving(true);
    setError(null);
    setSaveSuccess(false);
    try {
      const updated = await updateInvestigation(activeInvestigation.id, {
        title,
        status,
        verified_facts: verifiedFacts,
        hypotheses,
        action_items: actionItems,
      });
      setActiveInvestigation(updated);
      setInvestigations((prev) =>
        prev.map((inv) => (inv.id === updated.id ? updated : inv))
      );
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save changes.');
    } finally {
      setIsSaving(false);
    }
  };

  // Add Item Handlers
  const handleAddFact = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newFact.trim()) return;
    setVerifiedFacts((prev) => [...prev, newFact.trim()]);
    setNewFact('');
  };

  const handleRemoveFact = (index: number) => {
    setVerifiedFacts((prev) => prev.filter((_, i) => i !== index));
  };

  const handleAddHypothesis = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newHypothesis.trim()) return;
    setHypotheses((prev) => [...prev, newHypothesis.trim()]);
    setNewHypothesis('');
  };

  const handleRemoveHypothesis = (index: number) => {
    setHypotheses((prev) => prev.filter((_, i) => i !== index));
  };

  const handleAddActionItem = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newActionItem.trim()) return;
    setActionItems((prev) => [...prev, newActionItem.trim()]);
    setNewActionItem('');
  };

  const handleToggleActionItem = (index: number) => {
    setActionItems((prev) =>
      prev.map((item, i) => {
        if (i !== index) return item;
        if (item.startsWith('[x] ') || item.startsWith('[X] ')) {
          return item.substring(4);
        }
        return `[x] ${item}`;
      })
    );
  };

  const handleRemoveActionItem = (index: number) => {
    setActionItems((prev) => prev.filter((_, i) => i !== index));
  };

  // Status badge helper
  const getStatusBadge = (s: string) => {
    switch (s) {
      case 'RESOLVED':
      case 'RECOVERED':
        return 'bg-emerald-950/80 border-emerald-800 text-emerald-300';
      case 'INVESTIGATING':
        return 'bg-amber-950/80 border-amber-800 text-amber-300';
      case 'OPEN':
        return 'bg-purple-950/80 border-purple-800 text-purple-300';
      default:
        return 'bg-slate-800 border-slate-700 text-slate-300';
    }
  };

  const completedActionsCount = actionItems.filter(
    (item) => item.startsWith('[x] ') || item.startsWith('[X] ')
  ).length;

  return (
    <div className="space-y-6" data-testid="investigation-workspace">
      {/* Top Action & Navigation Toolbar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-lux-900/60 border border-lux-700/50 flex items-center justify-center text-lux-300">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-base font-bold text-white tracking-tight">
                Incident Investigation Workspace
              </h2>
              {activeInvestigation && (
                <span
                  className={`px-2 py-0.5 rounded text-[11px] font-semibold border ${getStatusBadge(
                    status
                  )}`}
                  data-testid="investigation-status-badge"
                >
                  {status}
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400">
              Enforcing rigorous separation between verified facts and working hypotheses.
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-2">
          {investigations.length > 1 && (
            <select
              value={activeInvestigation?.id || ''}
              onChange={(e) => handleSelectInvestigation(e.target.value)}
              className="px-2.5 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-lux-500"
              aria-label="Select investigation"
            >
              {investigations.map((inv) => (
                <option key={inv.id} value={inv.id}>
                  {inv.title} ({inv.status})
                </option>
              ))}
            </select>
          )}

          <button
            type="button"
            onClick={handleSynthesize}
            disabled={isSynthesizing}
            data-testid="synthesize-evidence-btn"
            title="Automatically assemble findings, pipeline logs, and lineage blast radius"
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-medium transition-colors"
          >
            {isSynthesizing ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Sparkles className="w-3.5 h-3.5 text-lux-400" />
            )}
            <span>Synthesize Evidence</span>
          </button>

          {activeInvestigation && (
            <>
              <button
                type="button"
                onClick={handleSaveChanges}
                disabled={isSaving}
                data-testid="save-investigation-btn"
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-lux-700 hover:bg-lux-600 text-white text-xs font-medium transition-colors"
              >
                {isSaving ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : saveSuccess ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                ) : (
                  <Save className="w-3.5 h-3.5" />
                )}
                <span>{saveSuccess ? 'Saved!' : 'Save'}</span>
              </button>

              <button
                type="button"
                onClick={() => setIsReportModalOpen(true)}
                data-testid="open-report-modal-btn"
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-lux-600 hover:bg-lux-500 text-white text-xs font-medium transition-colors shadow-sm"
              >
                <FileText className="w-3.5 h-3.5" />
                <span>Generate Report</span>
              </button>
            </>
          )}
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div
          role="alert"
          className="p-4 bg-rose-950/60 border border-rose-800 rounded-lg flex items-start space-x-3 text-rose-200 text-sm"
        >
          <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="font-semibold text-rose-300">Investigation Error</p>
            <p className="text-xs text-rose-300/90 mt-0.5">{error}</p>
          </div>
          <button
            type="button"
            onClick={() => fetchInvestigations(false)}
            className="text-xs text-rose-400 hover:text-white underline"
          >
            Retry
          </button>
        </div>
      )}

      {/* Empty State when no investigation exists */}
      {!isLoading && !activeInvestigation && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-10 text-center space-y-4">
          <div className="w-12 h-12 mx-auto rounded-full bg-lux-900/40 border border-lux-700/30 flex items-center justify-center text-lux-400">
            <FileText className="w-6 h-6" />
          </div>
          <div className="max-w-md mx-auto space-y-2">
            <h3 className="text-base font-bold text-white">No Active Investigation Found</h3>
            <p className="text-xs text-slate-400">
              There is currently no active investigation workspace for scenario{' '}
              <span className="font-mono text-lux-300 font-semibold">{scenarioId}</span>. Synthesize
              one from existing validation findings, ETL pipeline logs, and lineage DAG.
            </p>
          </div>
          <div className="pt-2 flex justify-center space-x-3">
            <button
              type="button"
              onClick={handleSynthesize}
              disabled={isSynthesizing}
              data-testid="synthesize-initial-btn"
              className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg bg-lux-600 hover:bg-lux-500 text-white text-xs font-semibold transition-colors"
            >
              <Sparkles className="w-4 h-4" />
              <span>Synthesize from Evidence</span>
            </button>
            <button
              type="button"
              onClick={handleCreateNew}
              disabled={isSaving}
              className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span>Blank Investigation</span>
            </button>
          </div>
        </div>
      )}

      {/* Active Investigation Body */}
      {activeInvestigation && (
        <div className="space-y-6">
          {/* Metadata & Title Card */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-center">
              <div className="md:col-span-3">
                <label
                  htmlFor="investigation-title-input"
                  className="block text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-1"
                >
                  Investigation Title
                </label>
                <input
                  id="investigation-title-input"
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:ring-1 focus:ring-lux-500"
                />
              </div>

              <div>
                <label
                  htmlFor="investigation-status-select"
                  className="block text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-1"
                >
                  Status
                </label>
                <select
                  id="investigation-status-select"
                  value={status}
                  onChange={(e) => setStatus(e.target.value as InvestigationStatus)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:ring-1 focus:ring-lux-500"
                >
                  <option value="OPEN">OPEN</option>
                  <option value="INVESTIGATING">INVESTIGATING</option>
                  <option value="RESOLVED">RESOLVED</option>
                  <option value="RECOVERED">RECOVERED</option>
                  <option value="CLOSED">CLOSED</option>
                </select>
              </div>
            </div>

            {/* Quick Metrics Bar */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 text-xs border-t border-slate-800/80">
              <div className="flex items-center space-x-2 text-slate-400">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span>
                  <strong className="text-white">{verifiedFacts.length}</strong> Verified Facts
                </span>
              </div>
              <div className="flex items-center space-x-2 text-slate-400">
                <Lightbulb className="w-4 h-4 text-amber-400" />
                <span>
                  <strong className="text-white">{hypotheses.length}</strong> Working Hypotheses
                </span>
              </div>
              <div className="flex items-center space-x-2 text-slate-400">
                <CheckSquare className="w-4 h-4 text-lux-400" />
                <span>
                  <strong className="text-white">
                    {completedActionsCount} / {actionItems.length}
                  </strong>{' '}
                  Action Items Completed
                </span>
              </div>
            </div>
          </div>

          {/* Three-Column Architectural Boundary Zone */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* 1. VERIFIED FACTS ZONE */}
            <section
              aria-label="Confirmed Observations (Verified Facts)"
              className="bg-slate-900 border border-emerald-900/40 rounded-xl p-5 flex flex-col justify-between space-y-4 shadow-sm"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                  <div className="flex items-center space-x-2">
                    <ShieldCheck className="w-4 h-4 text-emerald-400" />
                    <h3 className="text-xs font-bold uppercase tracking-wider text-emerald-300">
                      Confirmed Observations
                    </h3>
                  </div>
                  <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-950/80 text-emerald-300 border border-emerald-800">
                    FACTS
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  Concrete, verifiable findings from validation execution rules and ETL orchestration logs.
                </p>

                {/* Facts List */}
                <ul className="space-y-2 mt-2 max-h-[360px] overflow-y-auto pr-1">
                  {verifiedFacts.length === 0 ? (
                    <li className="text-xs text-slate-500 italic py-4 text-center">
                      No verified facts recorded.
                    </li>
                  ) : (
                    verifiedFacts.map((fact, idx) => (
                      <li
                        key={idx}
                        className="p-2.5 rounded-lg bg-slate-950/70 border border-emerald-950/60 flex items-start justify-between gap-2 group text-xs text-slate-200"
                      >
                        <span className="flex-1 leading-snug">{fact}</span>
                        <button
                          type="button"
                          onClick={() => handleRemoveFact(idx)}
                          aria-label={`Remove fact ${idx + 1}`}
                          className="text-slate-500 hover:text-rose-400 opacity-60 group-hover:opacity-100 transition-opacity p-0.5"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </li>
                    ))
                  )}
                </ul>
              </div>

              {/* Add Fact Form */}
              <form onSubmit={handleAddFact} className="pt-2 border-t border-slate-800/80 space-y-2">
                <div className="flex items-center space-x-2">
                  <input
                    type="text"
                    value={newFact}
                    onChange={(e) => setNewFact(e.target.value)}
                    placeholder="Add verified observation..."
                    className="flex-1 px-2.5 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                  />
                  <button
                    type="submit"
                    disabled={!newFact.trim()}
                    className="p-1.5 bg-emerald-700 hover:bg-emerald-600 disabled:bg-slate-800 disabled:text-slate-600 text-white rounded-lg transition-colors"
                    title="Add verified fact"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                </div>
              </form>
            </section>

            {/* 2. WORKING HYPOTHESES ZONE */}
            <section
              aria-label="Working Hypotheses (Root-Cause Theories)"
              className="bg-slate-900 border border-amber-900/40 rounded-xl p-5 flex flex-col justify-between space-y-4 shadow-sm"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                  <div className="flex items-center space-x-2">
                    <Lightbulb className="w-4 h-4 text-amber-400" />
                    <h3 className="text-xs font-bold uppercase tracking-wider text-amber-300">
                      Working Hypotheses
                    </h3>
                  </div>
                  <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-950/80 text-amber-300 border border-amber-800">
                    THEORIES
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  Plausible root causes and theories under active investigation. Distinct from ground truth facts.
                </p>

                {/* Hypotheses List */}
                <ul className="space-y-2 mt-2 max-h-[360px] overflow-y-auto pr-1">
                  {hypotheses.length === 0 ? (
                    <li className="text-xs text-slate-500 italic py-4 text-center">
                      No working hypotheses added yet.
                    </li>
                  ) : (
                    hypotheses.map((hypo, idx) => (
                      <li
                        key={idx}
                        className="p-2.5 rounded-lg bg-slate-950/70 border border-amber-950/60 flex items-start justify-between gap-2 group text-xs text-slate-200"
                      >
                        <span className="flex-1 leading-snug">{hypo}</span>
                        <button
                          type="button"
                          onClick={() => handleRemoveHypothesis(idx)}
                          aria-label={`Remove hypothesis ${idx + 1}`}
                          className="text-slate-500 hover:text-rose-400 opacity-60 group-hover:opacity-100 transition-opacity p-0.5"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </li>
                    ))
                  )}
                </ul>
              </div>

              {/* Add Hypothesis Form */}
              <form
                onSubmit={handleAddHypothesis}
                className="pt-2 border-t border-slate-800/80 space-y-2"
              >
                <div className="flex items-center space-x-2">
                  <input
                    type="text"
                    value={newHypothesis}
                    onChange={(e) => setNewHypothesis(e.target.value)}
                    placeholder="Add hypothesis theory..."
                    className="flex-1 px-2.5 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
                  />
                  <button
                    type="submit"
                    disabled={!newHypothesis.trim()}
                    className="p-1.5 bg-amber-700 hover:bg-amber-600 disabled:bg-slate-800 disabled:text-slate-600 text-white rounded-lg transition-colors"
                    title="Add hypothesis"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                </div>
              </form>
            </section>

            {/* 3. REMEDIATION ACTION ITEMS ZONE */}
            <section
              aria-label="Remediation Action Items (Resolution Checklist)"
              className="bg-slate-900 border border-lux-900/40 rounded-xl p-5 flex flex-col justify-between space-y-4 shadow-sm"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                  <div className="flex items-center space-x-2">
                    <CheckSquare className="w-4 h-4 text-lux-400" />
                    <h3 className="text-xs font-bold uppercase tracking-wider text-lux-300">
                      Remediation Checklist
                    </h3>
                  </div>
                  <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-lux-950/80 text-lux-300 border border-lux-800">
                    ACTIONS
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  Concrete remediation tasks and follow-up work needed to recover data health.
                </p>

                {/* Actions List */}
                <ul className="space-y-2 mt-2 max-h-[360px] overflow-y-auto pr-1">
                  {actionItems.length === 0 ? (
                    <li className="text-xs text-slate-500 italic py-4 text-center">
                      No remediation items defined.
                    </li>
                  ) : (
                    actionItems.map((action, idx) => {
                      const isChecked =
                        action.startsWith('[x] ') || action.startsWith('[X] ');
                      const displayText = isChecked ? action.substring(4) : action;

                      return (
                        <li
                          key={idx}
                          className="p-2.5 rounded-lg bg-slate-950/70 border border-lux-950/60 flex items-start justify-between gap-2 group text-xs text-slate-200"
                        >
                          <button
                            type="button"
                            onClick={() => handleToggleActionItem(idx)}
                            aria-label={`Toggle action ${idx + 1}`}
                            className="mt-0.5 text-slate-400 hover:text-lux-400 transition-colors"
                          >
                            {isChecked ? (
                              <CheckSquare className="w-4 h-4 text-emerald-400" />
                            ) : (
                              <Square className="w-4 h-4" />
                            )}
                          </button>
                          <span
                            className={`flex-1 leading-snug cursor-pointer ${
                              isChecked ? 'line-through text-slate-500' : 'text-slate-200'
                            }`}
                            onClick={() => handleToggleActionItem(idx)}
                          >
                            {displayText}
                          </span>
                          <button
                            type="button"
                            onClick={() => handleRemoveActionItem(idx)}
                            aria-label={`Remove action item ${idx + 1}`}
                            className="text-slate-500 hover:text-rose-400 opacity-60 group-hover:opacity-100 transition-opacity p-0.5"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </li>
                      );
                    })
                  )}
                </ul>
              </div>

              {/* Add Action Item Form */}
              <form
                onSubmit={handleAddActionItem}
                className="pt-2 border-t border-slate-800/80 space-y-2"
              >
                <div className="flex items-center space-x-2">
                  <input
                    type="text"
                    value={newActionItem}
                    onChange={(e) => setNewActionItem(e.target.value)}
                    placeholder="Add remediation step..."
                    className="flex-1 px-2.5 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-lux-500"
                  />
                  <button
                    type="submit"
                    disabled={!newActionItem.trim()}
                    className="p-1.5 bg-lux-700 hover:bg-lux-600 disabled:bg-slate-800 disabled:text-slate-600 text-white rounded-lg transition-colors"
                    title="Add action item"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                </div>
              </form>
            </section>
          </div>

          {/* Quick Cross-Workspace Jump Links */}
          <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl flex flex-wrap items-center justify-between gap-3 text-xs text-slate-400">
            <span>Explore connected evidence across other observability workspaces:</span>
            <div className="flex items-center space-x-3">
              {onNavigateToLineage && (
                <button
                  type="button"
                  onClick={() => onNavigateToLineage()}
                  className="inline-flex items-center space-x-1 text-lux-400 hover:text-lux-300 font-medium transition-colors"
                >
                  <GitFork className="w-3.5 h-3.5" />
                  <span>Inspect Lineage DAG</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
              )}
              {onNavigateToValidations && (
                <button
                  type="button"
                  onClick={() => onNavigateToValidations()}
                  className="inline-flex items-center space-x-1 text-lux-400 hover:text-lux-300 font-medium transition-colors"
                >
                  <ShieldCheck className="w-3.5 h-3.5" />
                  <span>Inspect Quality Findings</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Report Generator Modal */}
      <ReportModal
        isOpen={isReportModalOpen}
        onClose={() => setIsReportModalOpen(false)}
        scenarioId={scenarioId}
        investigation={activeInvestigation}
      />
    </div>
  );
};
