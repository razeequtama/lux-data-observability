import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import App from '../src/App';

describe('Lux App Shell Component', () => {
  it('renders the Lux header with logo and branding', () => {
    render(<App />);

    expect(screen.getByText('Lux')).toBeInTheDocument();
    expect(screen.getByText('Data Observability Platform')).toBeInTheDocument();
    expect(screen.getByTestId('lux-logo')).toBeInTheDocument();
  });

  it('renders the active signature scenario badge', () => {
    render(<App />);

    const scenarioBadge = screen.getByTestId('active-scenario');
    expect(scenarioBadge).toBeInTheDocument();
    expect(scenarioBadge).toHaveTextContent('Monday Revenue Mystery');
  });

  it('renders dual-dimension health indicators separating compute and quality', () => {
    render(<App />);

    const indicator = screen.getByTestId('dual-health-indicator');
    expect(indicator).toBeInTheDocument();
    expect(indicator).toHaveTextContent('Compute:');
    expect(indicator).toHaveTextContent('SUCCESS');
    expect(indicator).toHaveTextContent('Quality:');
    expect(indicator).toHaveTextContent('CORRUPTED');
  });

  it('renders all semantic navigation tabs with accessible ARIA roles', () => {
    render(<App />);

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

  it('defaults to the Validations tab and displays the Validations panel', () => {
    render(<App />);

    const validationsTab = screen.getByRole('tab', { name: /validations/i });
    expect(validationsTab).toHaveAttribute('aria-selected', 'true');

    expect(screen.getByRole('heading', { level: 1, name: /validations/i })).toBeInTheDocument();
    expect(screen.getByText(/deterministic quality rule evaluation/i)).toBeInTheDocument();
  });

  it('switches tabs and updates active panel upon tab click', () => {
    render(<App />);

    const lineageTab = screen.getByRole('tab', { name: /lineage/i });
    expect(lineageTab).toHaveAttribute('aria-selected', 'false');

    fireEvent.click(lineageTab);

    expect(lineageTab).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByRole('heading', { level: 1, name: /lineage/i })).toBeInTheDocument();
    expect(screen.getByText(/interactive directed acyclic graph/i)).toBeInTheDocument();

    // Switch to Recovery tab
    const recoveryTab = screen.getByRole('tab', { name: /recovery/i });
    fireEvent.click(recoveryTab);

    expect(recoveryTab).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByRole('heading', { level: 1, name: /recovery/i })).toBeInTheDocument();
    expect(screen.getByText(/before vs after verification/i)).toBeInTheDocument();
  });
});

