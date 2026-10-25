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
    fetchLatestRun(scenarioId);
  }, [fetchLatestRun, scenarioId, fixtureVersion, lastReloadKey]);

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
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <div className="p-1.5 rounded-lg bg-lux-950/80 border border-lux-700/40 text-lux-400">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <h2 className="text-base font-bold text-white tracking-tight">
              Deterministic Quality Engine
            </h2>
            <span className="text-xs px-2 py-0.5 rounded-full font-mono bg-slate-800 text-slate-300 border border-slate-700">
              Scenario: {scenarioId}
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Executes structural, uniqueness, referential integrity, range, and temporal rules against datasets.
          </p>
        </div>

        <div className="flex items-center space-x-2.5 w-full sm:w-auto">
          {currentRun && (
            <button
              type="button"
              onClick={() => fetchLatestRun(scenarioId)}
              disabled={isLoadingRun || isRunningValidation}
              data-testid="refresh-run-btn"
              aria-label="Refresh run findings"
              className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
              title="Refresh findings"
            >
              <RotateCw className={`w-4 h-4 ${isLoadingRun ? 'animate-spin' : ''}`} />
            </button>
          )}

          <button
            type="button"
            onClick={handleExecuteValidationRun}
            disabled={isRunningValidation || isLoadingRun}
            data-testid="execute-validations-btn"
            className="flex-1 sm:flex-initial flex items-center justify-center space-x-2 px-4 py-2 bg-lux-700 hover:bg-lux-600 disabled:opacity-50 text-white rounded-lg text-xs font-bold transition-all shadow-sm cursor-pointer"
          >
            {isRunningValidation ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Evaluating Rules...</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>{currentRun ? 'Re-run Quality Validations' : 'Execute Quality Validations'}</span>
              </>
            )}
          </button>
        </div>
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
          className="bg-slate-900/60 border border-slate-800 rounded-xl p-12 text-center space-y-4"
        >
          <div className="w-12 h-12 mx-auto rounded-full bg-lux-950 border border-lux-700/50 flex items-center justify-center text-lux-400">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div className="max-w-md mx-auto space-y-2">
            <h3 className="text-base font-bold text-white">
              {availableDatasets && availableDatasets.length === 0
                ? 'No Scenario Loaded Yet'
                : 'No Validation Runs Executed Yet'}
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              {availableDatasets && availableDatasets.length === 0
                ? 'Click "Load Scenario" in the top bar to ingest datasets into the workspace before executing validations.'
                : `Click "Execute Quality Validations" to evaluate deterministic rules against the active scenario datasets (${availableDatasets?.length || 4} files) and inspect structured row findings.`}
            </p>
          </div>
          {(!availableDatasets || availableDatasets.length > 0) && (
            <button
              type="button"
              onClick={handleExecuteValidationRun}
              data-testid="empty-state-run-btn"
              className="inline-flex items-center space-x-2 px-4 py-2 bg-lux-700 hover:bg-lux-600 text-white rounded-lg text-xs font-bold transition-colors cursor-pointer"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
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
