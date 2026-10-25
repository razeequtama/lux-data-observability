import React from 'react';
import { Database, RefreshCw, AlertCircle, CheckCircle2, FolderX } from 'lucide-react';
import { FixtureVersion, ScenarioSummary } from '../../types';

interface ScenarioSwitcherProps {
  scenarios: ScenarioSummary[];
  activeScenarioId: string;
  activeFixtureVersion: FixtureVersion;
  isLoading: boolean;
  isUnloading?: boolean;
  onSelectScenario: (scenarioId: string) => void;
  onSelectFixtureVersion: (version: FixtureVersion) => void;
  onLoadScenario: (scenarioId: string, version: FixtureVersion) => void;
  onUnloadScenario?: (scenarioId: string) => void;
}

export const ScenarioSwitcher: React.FC<ScenarioSwitcherProps> = ({
  scenarios,
  activeScenarioId,
  activeFixtureVersion,
  isLoading,
  isUnloading = false,
  onSelectScenario,
  onSelectFixtureVersion,
  onLoadScenario,
  onUnloadScenario,
}) => {
  const activeScenario = scenarios.find((s) => s.id === activeScenarioId) || scenarios[0];
  const isBusy = isLoading || isUnloading;

  return (
    <div
      className="flex flex-wrap items-center gap-3 bg-slate-900/70 backdrop-blur-md border border-white/[0.08] border-t-purple-400/20 rounded-2xl p-2.5 sm:p-3 shadow-inner"
      data-testid="scenario-switcher"
    >
      {/* Scenario Selector Dropdown */}
      <div className="flex items-center space-x-2.5">
        <Database className="w-4 h-4 text-lux-400 shrink-0" />
        <label htmlFor="scenario-select" className="text-xs text-slate-400 font-medium sr-only">
          Select Scenario
        </label>
        <select
          id="scenario-select"
          data-testid="scenario-select"
          aria-label="Select Scenario"
          value={activeScenarioId}
          onChange={(e) => onSelectScenario(e.target.value)}
          disabled={isBusy}
          className="bg-slate-950/80 border border-white/[0.08] text-slate-200 text-xs rounded-xl px-4 py-2.5 focus:border-lux-500 focus:outline-none focus:ring-1 focus:ring-lux-500 cursor-pointer disabled:opacity-50 transition-colors shadow-inner font-medium"
        >
          {scenarios.length === 0 ? (
            <option value="monday_revenue_mystery">Monday Revenue Mystery</option>
          ) : (
            scenarios.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))
          )}
        </select>
      </div>

      {/* Fixture Version Switcher */}
      <div className="flex items-center space-x-1.5 bg-slate-950/70 border border-white/[0.08] rounded-xl p-1 shadow-inner">
        <button
          type="button"
          data-testid="fixture-defective-btn"
          aria-pressed={activeFixtureVersion === 'defective'}
          onClick={() => onSelectFixtureVersion('defective')}
          disabled={isBusy}
          className={`flex items-center space-x-1.5 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
            activeFixtureVersion === 'defective'
              ? 'bg-rose-950/80 text-rose-200 border border-rose-500/60 shadow-[0_0_12px_rgba(244,63,94,0.35)]'
              : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]'
          }`}
          title="Corrupted fixture with introduced quality defects"
        >
          <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
          <span>Defective</span>
        </button>

        <button
          type="button"
          data-testid="fixture-corrected-btn"
          aria-pressed={activeFixtureVersion === 'corrected'}
          onClick={() => onSelectFixtureVersion('corrected')}
          disabled={isBusy}
          className={`flex items-center space-x-1.5 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
            activeFixtureVersion === 'corrected'
              ? 'bg-emerald-950/80 text-emerald-200 border border-emerald-500/60 shadow-[0_0_12px_rgba(16,185,129,0.35)]'
              : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]'
          }`}
          title="Clean recovered fixture with defects resolved"
        >
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          <span>Corrected</span>
        </button>
      </div>

      {/* Trigger Load Scenario Button */}
      <button
        type="button"
        data-testid="load-scenario-btn"
        onClick={() => onLoadScenario(activeScenario?.id || activeScenarioId, activeFixtureVersion)}
        disabled={isBusy}
        className="flex items-center justify-center space-x-3 px-7 py-3 min-w-[155px] bg-gradient-to-r from-lux-700 via-lux-600 to-purple-600 hover:from-lux-600 hover:to-purple-500 active:from-lux-800 active:to-purple-700 disabled:opacity-50 text-white rounded-xl text-xs sm:text-sm font-bold shadow-[0_0_20px_rgba(124,58,237,0.4)] ring-1 ring-purple-400/50 transition-all cursor-pointer whitespace-nowrap"
      >
        <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
        <span>{isLoading ? 'Loading Fixtures...' : 'Load Scenario'}</span>
      </button>

      {/* Trigger Unload Scenario Button */}
      {onUnloadScenario && (
        <button
          type="button"
          data-testid="unload-scenario-btn"
          onClick={() => onUnloadScenario(activeScenario?.id || activeScenarioId)}
          disabled={isBusy}
          className="flex items-center justify-center space-x-3 px-7 py-3 min-w-[160px] bg-slate-900/80 hover:bg-rose-950/60 active:bg-rose-900/80 text-slate-300 hover:text-rose-200 border border-white/[0.08] hover:border-rose-500/50 disabled:opacity-50 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer shadow-sm whitespace-nowrap"
          title="Unload scenario datasets and reset workspace"
        >
          <FolderX className={`w-4 h-4 text-rose-400 ${isUnloading ? 'animate-pulse' : ''}`} />
          <span>{isUnloading ? 'Unloading...' : 'Unload Scenario'}</span>
        </button>
      )}

      {/* Dataset / Rule Counts pill */}
      {activeScenario && (
        <div className="hidden lg:flex items-center space-x-2 text-[11px] text-slate-400 pl-3 border-l border-white/[0.08]">
          <span>{activeScenario.dataset_count} datasets</span>
          <span className="text-slate-600">|</span>
          <span>{activeScenario.rule_count} rules</span>
        </div>
      )}
    </div>
  );
};


