import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ScenarioSwitcher } from '../../src/components/scenario/ScenarioSwitcher';
import { ScenarioSummary } from '../../src/types';

describe('ScenarioSwitcher Component', () => {
  const mockScenarios: ScenarioSummary[] = [
    {
      id: 'monday_revenue_mystery',
      name: 'Monday Revenue Mystery',
      category: 'e-commerce',
      is_bundled: true,
      active_fixture_version: 'defective',
      dataset_count: 4,
      rule_count: 12,
    },
    {
      id: 'customer_churn_gap',
      name: 'Customer Churn Gap',
      category: 'telecom',
      is_bundled: true,
      active_fixture_version: 'defective',
      dataset_count: 2,
      rule_count: 6,
    },
  ];

  it('renders scenario selector options and active scenario', () => {
    render(
      <ScenarioSwitcher
        scenarios={mockScenarios}
        activeScenarioId="monday_revenue_mystery"
        activeFixtureVersion="defective"
        isLoading={false}
        onSelectScenario={vi.fn()}
        onSelectFixtureVersion={vi.fn()}
        onLoadScenario={vi.fn()}
      />
    );

    const select = screen.getByTestId('scenario-select') as HTMLSelectElement;
    expect(select).toBeInTheDocument();
    expect(select.value).toBe('monday_revenue_mystery');
    expect(screen.getByText('Monday Revenue Mystery')).toBeInTheDocument();
    expect(screen.getByText('Customer Churn Gap')).toBeInTheDocument();
  });

  it('calls onSelectScenario when a different scenario is chosen', () => {
    const handleSelectScenario = vi.fn();
    render(
      <ScenarioSwitcher
        scenarios={mockScenarios}
        activeScenarioId="monday_revenue_mystery"
        activeFixtureVersion="defective"
        isLoading={false}
        onSelectScenario={handleSelectScenario}
        onSelectFixtureVersion={vi.fn()}
        onLoadScenario={vi.fn()}
      />
    );

    const select = screen.getByTestId('scenario-select');
    fireEvent.change(select, { target: { value: 'customer_churn_gap' } });
    expect(handleSelectScenario).toHaveBeenCalledWith('customer_churn_gap');
  });

  it('toggles fixture version between defective and corrected', () => {
    const handleSelectFixtureVersion = vi.fn();
    render(
      <ScenarioSwitcher
        scenarios={mockScenarios}
        activeScenarioId="monday_revenue_mystery"
        activeFixtureVersion="defective"
        isLoading={false}
        onSelectScenario={vi.fn()}
        onSelectFixtureVersion={handleSelectFixtureVersion}
        onLoadScenario={vi.fn()}
      />
    );

    const defectiveBtn = screen.getByTestId('fixture-defective-btn');
    const correctedBtn = screen.getByTestId('fixture-corrected-btn');

    expect(defectiveBtn).toHaveAttribute('aria-pressed', 'true');
    expect(correctedBtn).toHaveAttribute('aria-pressed', 'false');

    fireEvent.click(correctedBtn);
    expect(handleSelectFixtureVersion).toHaveBeenCalledWith('corrected');
  });

  it('calls onLoadScenario when "Load Scenario" button is clicked', () => {
    const handleLoadScenario = vi.fn();
    render(
      <ScenarioSwitcher
        scenarios={mockScenarios}
        activeScenarioId="monday_revenue_mystery"
        activeFixtureVersion="defective"
        isLoading={false}
        onSelectScenario={vi.fn()}
        onSelectFixtureVersion={vi.fn()}
        onLoadScenario={handleLoadScenario}
      />
    );

    const loadBtn = screen.getByTestId('load-scenario-btn');
    fireEvent.click(loadBtn);

    expect(handleLoadScenario).toHaveBeenCalledWith('monday_revenue_mystery', 'defective');
  });

  it('disables controls while loading', () => {
    render(
      <ScenarioSwitcher
        scenarios={mockScenarios}
        activeScenarioId="monday_revenue_mystery"
        activeFixtureVersion="defective"
        isLoading={true}
        onSelectScenario={vi.fn()}
        onSelectFixtureVersion={vi.fn()}
        onLoadScenario={vi.fn()}
      />
    );

    expect(screen.getByTestId('scenario-select')).toBeDisabled();
    expect(screen.getByTestId('fixture-defective-btn')).toBeDisabled();
    expect(screen.getByTestId('fixture-corrected-btn')).toBeDisabled();
    expect(screen.getByTestId('load-scenario-btn')).toBeDisabled();
    expect(screen.getByText('Loading Fixtures...')).toBeInTheDocument();
  });

  it('renders "Unload Scenario" button and calls onUnloadScenario when clicked', () => {
    const handleUnloadScenario = vi.fn();
    render(
      <ScenarioSwitcher
        scenarios={mockScenarios}
        activeScenarioId="monday_revenue_mystery"
        activeFixtureVersion="defective"
        isLoading={false}
        isUnloading={false}
        onSelectScenario={vi.fn()}
        onSelectFixtureVersion={vi.fn()}
        onLoadScenario={vi.fn()}
        onUnloadScenario={handleUnloadScenario}
      />
    );

    const unloadBtn = screen.getByTestId('unload-scenario-btn');
    expect(unloadBtn).toBeInTheDocument();
    expect(screen.getByText('Unload Scenario')).toBeInTheDocument();

    fireEvent.click(unloadBtn);
    expect(handleUnloadScenario).toHaveBeenCalledWith('monday_revenue_mystery');
  });

  it('disables controls while unloading', () => {
    render(
      <ScenarioSwitcher
        scenarios={mockScenarios}
        activeScenarioId="monday_revenue_mystery"
        activeFixtureVersion="defective"
        isLoading={false}
        isUnloading={true}
        onSelectScenario={vi.fn()}
        onSelectFixtureVersion={vi.fn()}
        onLoadScenario={vi.fn()}
        onUnloadScenario={vi.fn()}
      />
    );

    expect(screen.getByTestId('scenario-select')).toBeDisabled();
    expect(screen.getByTestId('load-scenario-btn')).toBeDisabled();
    expect(screen.getByTestId('unload-scenario-btn')).toBeDisabled();
    expect(screen.getByText('Unloading...')).toBeInTheDocument();
  });
});


