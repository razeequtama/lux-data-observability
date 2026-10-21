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
      className="flex flex-wrap items-center gap-3 bg-slate-900 border border-slate-800 rounded-lg p-2.5"
      data-testid="scenario-switcher"
    >
      {/* Scenario Selector Dropdown */}
      <div className="flex items-center space-x-2">
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
          className="bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded-md px-2.5 py-1.5 focus:border-lux-500 focus:outline-none focus:ring-1 focus:ring-lux-500 cursor-pointer disabled:opacity-50"
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
      <div className="flex items-center space-x-1.5 bg-slate-800/80 border border-slate-700/80 rounded-md p-0.5">
        <button
          type="button"
          data-testid="fixture-defective-btn"
          aria-pressed={activeFixtureVersion === 'defective'}
          onClick={() => onSelectFixtureVersion('defective')}
          disabled={isBusy}
          className={`flex items-center space-x-1 px-2 py-1 rounded text-xs font-medium transition-colors ${
            activeFixtureVersion === 'defective'
              ? 'bg-rose-950/80 text-rose-300 border border-rose-700/60 shadow-sm'
              : 'text-slate-400 hover:text-slate-200'
          }`}
          title="Corrupted fixture with introduced quality defects"
        >
          <AlertCircle className="w-3 h-3 text-rose-400" />
          <span>Defective</span>
        </button>

        <button
          type="button"
          data-testid="fixture-corrected-btn"
          aria-pressed={activeFixtureVersion === 'corrected'}
          onClick={() => onSelectFixtureVersion('corrected')}
          disabled={isBusy}
          className={`flex items-center space-x-1 px-2 py-1 rounded text-xs font-medium transition-colors ${
            activeFixtureVersion === 'corrected'
              ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-700/60 shadow-sm'
              : 'text-slate-400 hover:text-slate-200'
          }`}
          title="Clean recovered fixture with defects resolved"
        >
          <CheckCircle2 className="w-3 h-3 text-emerald-400" />
          <span>Corrected</span>
        </button>
      </div>

      {/* Trigger Load Scenario Button */}
      <button
        type="button"
        data-testid="load-scenario-btn"
        onClick={() => onLoadScenario(activeScenario?.id || activeScenarioId, activeFixtureVersion)}
        disabled={isBusy}
        className="flex items-center space-x-1.5 px-3 py-1.5 bg-lux-700 hover:bg-lux-600 active:bg-lux-800 disabled:opacity-50 text-white rounded-md text-xs font-semibold shadow-sm shadow-lux-700/30 transition-colors cursor-pointer"
      >
        <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
        <span>{isLoading ? 'Loading Fixtures...' : 'Load Scenario'}</span>
      </button>

      {/* Trigger Unload Scenario Button */}
      {onUnloadScenario && (
        <button
          type="button"
          data-testid="unload-scenario-btn"
          onClick={() => onUnloadScenario(activeScenario?.id || activeScenarioId)}
          disabled={isBusy}
          className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-800 hover:bg-rose-950/60 active:bg-rose-900/80 text-slate-300 hover:text-rose-200 border border-slate-700 hover:border-rose-700/60 disabled:opacity-50 rounded-md text-xs font-semibold transition-colors cursor-pointer"
          title="Unload scenario datasets and reset workspace"
        >
          <FolderX className={`w-3.5 h-3.5 text-rose-400 ${isUnloading ? 'animate-pulse' : ''}`} />
          <span>{isUnloading ? 'Unloading...' : 'Unload Scenario'}</span>
        </button>
      )}

      {/* Dataset / Rule Counts pill */}
      {activeScenario && (
        <div className="hidden lg:flex items-center space-x-2 text-[11px] text-slate-400 pl-1 border-l border-slate-800">
          <span>{activeScenario.dataset_count} datasets</span>
          <span>•</span>
          <span>{activeScenario.rule_count} rules</span>
        </div>
      )}
    </div>
  );
};


