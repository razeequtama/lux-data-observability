import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import App from '../src/App';
import * as scenariosApi from '../src/api/scenarios';
import * as datasetsApi from '../src/api/datasets';
import * as validationsApi from '../src/api/validations';
import * as lineageApi from '../src/api/lineage';
import * as pipelinesApi from '../src/api/pipelines';
import * as investigationsApi from '../src/api/investigations';

describe('Lux App Shell Component', () => {
  const mockScenarios = [
    {
      id: 'monday_revenue_mystery',
      name: 'Monday Revenue Mystery',
      description: 'Daily revenue spikes following overnight run',
      category: 'e-commerce',
      is_bundled: true,
      active_fixture_version: 'defective',
      dataset_count: 4,
      rule_count: 12,
    },
  ];

  const mockDatasets = [
    {
      id: 'orders',
      scenario_id: 'monday_revenue_mystery',
      name: 'orders.csv',
      format: 'csv',
      file_size_bytes: 104857,
      record_count: 1250,
      column_count: 5,
    },
    {
      id: 'order_items',
      scenario_id: 'monday_revenue_mystery',
      name: 'order_items.csv',
      format: 'csv',
      file_size_bytes: 284920,
      record_count: 3420,
      column_count: 6,
    },
  ];

  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(scenariosApi, 'listScenarios').mockResolvedValue(mockScenarios);
    vi.spyOn(datasetsApi, 'listDatasets').mockResolvedValue(mockDatasets);
    vi.spyOn(validationsApi, 'listValidationRuns').mockResolvedValue([]);
    vi.spyOn(validationsApi, 'listValidationFindings').mockResolvedValue({
      run_id: 'val_run_mock',
      total_findings: 0,
      items: [],
    });
    vi.spyOn(lineageApi, 'getLineageGraph').mockResolvedValue({
      scenario_id: 'monday_revenue_mystery',
      nodes: [
        {
          id: 'src_orders',
          name: 'orders.csv',
          type: 'SOURCE_DATASET',
          position: { x: 50, y: 100 },
          execution_status: 'COMPLETED_SUCCESS',
          quality_health: 'CORRUPTED',
          data: { label: 'orders.csv', type: 'SOURCE_DATASET' },
        },
      ],
      edges: [],
    });
    vi.spyOn(pipelinesApi, 'listPipelineRuns').mockResolvedValue([]);
    vi.spyOn(pipelinesApi, 'getPipelineFreshness').mockResolvedValue([]);
    vi.spyOn(investigationsApi, 'listInvestigations').mockResolvedValue([]);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  const renderApp = async () => {
    await act(async () => {
      render(<App />);
    });
  };

  it('renders the Lux header with logo and branding', async () => {
    await renderApp();

    expect(screen.getByText('Lux')).toBeInTheDocument();
    expect(screen.getByText('Data Observability Platform')).toBeInTheDocument();
    expect(screen.getByTestId('lux-logo')).toBeInTheDocument();
  });

  it('renders the active signature scenario badge', async () => {
    await renderApp();

    const scenarioBadge = screen.getByTestId('active-scenario');
    expect(scenarioBadge).toBeInTheDocument();
    expect(scenarioBadge).toHaveTextContent('Monday Revenue Mystery');
  });

  it('renders dual-dimension health indicators separating compute and quality', async () => {
    await renderApp();

    const indicator = screen.getByTestId('dual-health-indicator');
    expect(indicator).toBeInTheDocument();
    expect(indicator).toHaveTextContent('Compute:');
    expect(indicator).toHaveTextContent('SUCCESS');
    expect(indicator).toHaveTextContent('Quality:');
    expect(indicator).toHaveTextContent('CORRUPTED');
  });

  it('renders all semantic navigation tabs with accessible ARIA roles', async () => {
    await renderApp();

    const tabList = screen.getByRole('tablist', { name: /observability workspaces/i });
    expect(tabList).toBeInTheDocument();

    const expectedTabs = [
      'Validations',
      'Lineage',
      'Impact Analysis',
      'Pipelines',
      'Investigation',
      'Recovery',
    ];

    expectedTabs.forEach((tabName) => {
      const tab = screen.getByRole('tab', { name: new RegExp(tabName, 'i') });
      expect(tab).toBeInTheDocument();
    });
  });

  it('defaults to the Validations tab and displays the Validations panel', async () => {
    await renderApp();

    const validationsTab = screen.getByRole('tab', { name: /validations/i });
    expect(validationsTab).toHaveAttribute('aria-selected', 'true');

    expect(screen.getByRole('heading', { level: 1, name: /validations/i })).toBeInTheDocument();
    expect(screen.getByText(/deterministic quality rule evaluation/i)).toBeInTheDocument();
  });

  it('switches tabs and updates active panel upon tab click', async () => {
    await renderApp();

    const lineageTab = screen.getByRole('tab', { name: /lineage/i });
    expect(lineageTab).toHaveAttribute('aria-selected', 'false');

    fireEvent.click(lineageTab);

    expect(lineageTab).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByRole('heading', { level: 1, name: /lineage/i })).toBeInTheDocument();
    expect(screen.getByText(/interactive directed acyclic graph/i)).toBeInTheDocument();
    expect(await screen.findByTestId('lineage-dag-container')).toBeInTheDocument();

    // Switch to Recovery tab
    const recoveryTab = screen.getByRole('tab', { name: /recovery/i });
    fireEvent.click(recoveryTab);

    expect(recoveryTab).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByRole('heading', { level: 1, name: /recovery/i })).toBeInTheDocument();
    expect(screen.getByText(/before vs after verification/i)).toBeInTheDocument();

    // Switch to Pipelines tab
    const pipelinesTab = screen.getByRole('tab', { name: /pipelines/i });
    await act(async () => {
      fireEvent.click(pipelinesTab);
    });

    expect(pipelinesTab).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByRole('heading', { level: 1, name: /pipelines/i })).toBeInTheDocument();
    expect(await screen.findByTestId('pipeline-observability-view')).toBeInTheDocument();

    // Switch to Investigation tab
    const investigationTab = screen.getByRole('tab', { name: /investigation/i });
    await act(async () => {
      fireEvent.click(investigationTab);
    });

    expect(investigationTab).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByRole('heading', { level: 1, name: /investigation/i })).toBeInTheDocument();
    expect(await screen.findByTestId('investigation-workspace')).toBeInTheDocument();
  });

  it('loads and displays datasets with row counts and columns', async () => {
    await renderApp();

    expect(screen.getByText('orders.csv')).toBeInTheDocument();
    expect(screen.getByText('1,250')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.getByText('order_items.csv')).toBeInTheDocument();
    expect(screen.getByText('3,420')).toBeInTheDocument();
    expect(screen.getByText('6')).toBeInTheDocument();
  });

  it('triggers scenario loading when Load Scenario is clicked', async () => {
    const mockLoadResponse = {
      scenario_id: 'monday_revenue_mystery',
      active_fixture_version: 'defective',
      loaded_datasets: ['orders', 'order_items', 'products', 'inventory'],
      rules_registered: 12,
      lineage_nodes_loaded: 16,
      message: 'Scenario "Monday Revenue Mystery" loaded successfully with defective fixtures.',
    };
    vi.spyOn(scenariosApi, 'loadScenario').mockResolvedValueOnce(mockLoadResponse);

    await renderApp();

    const loadBtn = screen.getByTestId('load-scenario-btn');
    expect(loadBtn).toBeInTheDocument();

    await act(async () => {
      fireEvent.click(loadBtn);
    });

    await waitFor(() => {
      expect(scenariosApi.loadScenario).toHaveBeenCalledWith(
        'monday_revenue_mystery',
        'defective'
      );
      expect(screen.getByText('Scenario Loaded Successfully')).toBeInTheDocument();
    });
  });

  it('toggles dataset inspector visibility', async () => {
    await renderApp();

    expect(screen.getByTestId('dataset-inspector')).toBeInTheDocument();

    const toggleBtn = screen.getByTestId('toggle-dataset-inspector-btn');
    fireEvent.click(toggleBtn);

    expect(screen.queryByTestId('dataset-inspector')).not.toBeInTheDocument();

    fireEvent.click(toggleBtn);
    expect(screen.getByTestId('dataset-inspector')).toBeInTheDocument();
  });

  it('opens upload modal when header upload button is clicked', async () => {
    await renderApp();

    const uploadBtn = screen.getByTestId('header-upload-btn');
    fireEvent.click(uploadBtn);

    expect(screen.getByText('Upload Custom Dataset')).toBeInTheDocument();
    expect(screen.getByTestId('dropzone')).toBeInTheDocument();
  });
});
