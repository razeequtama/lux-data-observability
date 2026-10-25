import React, { useState, useEffect, useCallback } from 'react';
import {
  Play,
  RotateCw,
  ShieldCheck,
} from 'lucide-react';
import {
  ValidationFindingItem,
  ValidationRunResponse,
} from '../../types';
import {
  executeValidationRun,
  listValidationRuns,
  listValidationFindings,
} from '../../api';
import { ValidationSummaryCards } from './ValidationSummaryCards';
import { FindingsTable } from './FindingsTable';
import { EvidenceDrawer } from './EvidenceDrawer';
import { AlertBanner } from '../common/AlertBanner';

interface ValidationViewProps {
  scenarioId: string;
  fixtureVersion?: string;
  lastReloadKey?: number | string;
  availableDatasets?: string[];
  onTraceImpact?: (finding: ValidationFindingItem) => void;
  onValidationRunComplete?: (run: ValidationRunResponse) => void;
}

export const ValidationView: React.FC<ValidationViewProps> = ({
  scenarioId,
  fixtureVersion,
  lastReloadKey,
  availableDatasets,
  onTraceImpact,
  onValidationRunComplete,
}) => {
  const [currentRun, setCurrentRun] = useState<ValidationRunResponse | null>(null);
  const [findings, setFindings] = useState<ValidationFindingItem[]>([]);
  const [selectedFinding, setSelectedFinding] = useState<ValidationFindingItem | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState<boolean>(false);
  const [isLoadingRun, setIsLoadingRun] = useState<boolean>(false);
  const [isRunningValidation, setIsRunningValidation] = useState<boolean>(false);
  const [isLoadingFindings, setIsLoadingFindings] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Load findings for a run
  const fetchFindingsForRun = useCallback(async (runId: string) => {
    setIsLoadingFindings(true);
    try {
      const res = await listValidationFindings(runId, { limit: 200 });
      setFindings(res.items);
    } catch (err) {
      console.warn('Could not load validation findings:', err);
      setErrorMessage(
        err instanceof Error ? err.message : 'Failed to retrieve validation findings.'
      );
    } finally {
      setIsLoadingFindings(false);
    }
  }, []);

  // Fetch latest existing run or prompt
  const fetchLatestRun = useCallback(
    async (targetScenarioId: string) => {
      setIsLoadingRun(true);
      setErrorMessage(null);
      try {
        const runs = await listValidationRuns(targetScenarioId, 1, 0);
        if (runs && runs.length > 0) {
          const latest = runs[0];
          setCurrentRun(latest);
          await fetchFindingsForRun(latest.run_id);
          if (onValidationRunComplete) {
            onValidationRunComplete(latest);
          }
        } else {
          setCurrentRun(null);
          setFindings([]);
        }
      } catch (err) {
        console.warn('Could not fetch latest validation run:', err);
      } finally {
        setIsLoadingRun(false);
      }
    },
    [fetchFindingsForRun, onValidationRunComplete]
  );

  // Trigger validation run
  const handleExecuteValidationRun = async () => {
    setIsRunningValidation(true);
    setErrorMessage(null);
    try {
      const run = await executeValidationRun(scenarioId);
      setCurrentRun(run);
      await fetchFindingsForRun(run.run_id);
      if (onValidationRunComplete) {
        onValidationRunComplete(run);
      }
    } catch (err) {
      setErrorMessage(
        err instanceof Error ? err.message : 'Validation run execution failed.'
      );
    } finally {
      setIsRunningValidation(false);
    }
  };

  useEffect(() => {
    if (availableDatasets && availableDatasets.length === 0) {
      setCurrentRun(null);
      setFindings([]);
      setSelectedFinding(null);
      setIsDrawerOpen(false);
      return;
    }
    fetchLatestRun(scenarioId);
  }, [fetchLatestRun, scenarioId, fixtureVersion, lastReloadKey, availableDatasets]);

  const handleSelectFinding = (finding: ValidationFindingItem) => {
    setSelectedFinding(finding);
    setIsDrawerOpen(true);
  };

  const handleCloseDrawer = () => {
    setIsDrawerOpen(false);
  };

  return (
    <div className="space-y-6" data-testid="validation-view">
      {/* Action Header Banner */}
      <div className="relative overflow-hidden bg-[#0d0f1b]/80 backdrop-blur-xl border border-white/[0.07] border-t-purple-400/30 rounded-3xl p-6 sm:p-7 shadow-xl shadow-black/40 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        {/* Subtle background flare */}
        <div className="absolute top-0 right-0 w-64 h-full bg-gradient-to-l from-purple-600/10 via-indigo-600/5 to-transparent pointer-events-none" />

        <div className="space-y-1.5 relative z-10">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-2xl bg-lux-950/80 border border-lux-700/50 text-lux-400 shadow-[0_0_14px_rgba(168,85,247,0.35)]">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h2 className="text-base sm:text-lg font-bold text-white tracking-tight">
              Deterministic Quality Engine
            </h2>
            <span className="text-xs px-3.5 py-1 rounded-xl font-sans font-semibold bg-slate-900/90 text-purple-200 border border-white/[0.08] shadow-inner">
              scenario: {scenarioId}
            </span>
          </div>
          <p className="text-xs sm:text-sm text-slate-400">
            Executes structural, uniqueness, referential integrity, range, and temporal rules against datasets.
          </p>
        </div>

        {currentRun && (
          <div className="flex items-center space-x-3 w-full sm:w-auto relative z-10">
            <button
              type="button"
              onClick={() => fetchLatestRun(scenarioId)}
              disabled={isLoadingRun || isRunningValidation}
              data-testid="refresh-run-btn"
              aria-label="Refresh run findings"
              className="p-3 rounded-2xl bg-slate-900/80 hover:bg-slate-800 text-slate-300 border border-white/[0.08] hover:border-purple-400/40 transition-all shadow-sm cursor-pointer"
              title="Refresh findings"
            >
              <RotateCw className={`w-4.5 h-4.5 ${isLoadingRun ? 'animate-spin' : ''}`} />
            </button>

            <button
              type="button"
              onClick={handleExecuteValidationRun}
              disabled={isRunningValidation || isLoadingRun}
              data-testid="re-run-validations-btn"
              className="flex-1 sm:flex-initial flex items-center justify-center space-x-2.5 px-7 py-3 bg-gradient-to-r from-lux-700 via-lux-600 to-indigo-600 hover:from-lux-600 hover:to-indigo-500 disabled:opacity-50 text-white rounded-2xl text-xs sm:text-sm font-bold transition-all shadow-[0_0_22px_rgba(124,58,237,0.4)] ring-1 ring-purple-400/50 cursor-pointer"
            >
              {isRunningValidation ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Evaluating Rules...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-current" />
                  <span>Re-run Quality Validations</span>
                </>
              )}
            </button>
          </div>
        )}
      </div>

      {/* Error Alert */}
      {errorMessage && (
        <AlertBanner
          type="error"
          message="Validation Error"
          details={errorMessage}
          onClose={() => setErrorMessage(null)}
        />
      )}

      {/* Empty State when no validation run has been executed */}
      {!currentRun && !isLoadingRun && !isRunningValidation ? (
        <div
          data-testid="no-runs-empty-state"
          className="relative overflow-hidden bg-[#0d0f1b]/60 backdrop-blur-xl border border-white/[0.07] border-t-purple-400/20 rounded-3xl p-16 text-center space-y-6 shadow-xl"
        >
          <div className="w-16 h-16 mx-auto rounded-3xl bg-lux-950/80 border border-lux-700/50 flex items-center justify-center text-lux-400 shadow-[0_0_24px_rgba(168,85,247,0.4)]">
            <ShieldCheck className="w-8 h-8" />
          </div>
          <div className="max-w-md mx-auto space-y-2.5">
            <h3 className="text-lg font-bold text-white tracking-tight">
              {availableDatasets && availableDatasets.length === 0
                ? 'No Scenario Loaded Yet'
                : 'No Validation Runs Executed Yet'}
            </h3>
            <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
              {availableDatasets && availableDatasets.length === 0
                ? 'Click "Load Scenario" in the top bar to ingest datasets into the workspace before executing validations.'
                : `Click "Execute Validations Now" to evaluate deterministic rules against the active scenario datasets (${availableDatasets?.length || 4} files) and inspect structured row findings.`}
            </p>
          </div>
          {(!availableDatasets || availableDatasets.length > 0) && (
            <button
              type="button"
              onClick={handleExecuteValidationRun}
              data-testid="execute-validations-btn"
              className="inline-flex items-center space-x-2.5 px-8 py-3.5 bg-gradient-to-r from-lux-700 via-lux-600 to-indigo-600 hover:from-lux-600 hover:to-indigo-500 text-white rounded-2xl text-xs sm:text-sm font-bold transition-all shadow-[0_0_24px_rgba(124,58,237,0.45)] ring-1 ring-purple-400/50 cursor-pointer"
            >
              <Play className="w-4 h-4 fill-current" />
              <span>Execute Validations Now</span>
            </button>
          )}
        </div>
      ) : (
        <>
          {/* Summary Cards */}
          <ValidationSummaryCards
            run={currentRun}
            isLoading={isRunningValidation || isLoadingRun}
          />

          {/* Granular Findings Table */}
          <section aria-label="Granular Validation Findings Table">
            <FindingsTable
              findings={findings}
              isLoading={isLoadingFindings || isRunningValidation}
              selectedFindingId={selectedFinding?.id}
              onSelectFinding={handleSelectFinding}
              onTraceImpact={onTraceImpact}
              availableDatasets={availableDatasets}
            />
          </section>
        </>
      )}

      {/* Slide-over Evidence Drawer */}
      <EvidenceDrawer
        finding={selectedFinding}
        isOpen={isDrawerOpen}
        onClose={handleCloseDrawer}
        onTraceImpact={onTraceImpact}
      />
    </div>
  );
};
