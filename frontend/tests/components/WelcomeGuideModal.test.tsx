import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { WelcomeModal } from '../../src/components/common/WelcomeModal';
import { GuideModal } from '../../src/components/common/GuideModal';
import { LanguageToggle } from '../../src/components/common/LanguageToggle';
import { ScenarioSwitcher } from '../../src/components/scenario/ScenarioSwitcher';
import { ScenarioSummary } from '../../src/types';

describe('LanguageToggle Component', () => {
  it('renders English and Indonesian toggle with flag SVGs', () => {
    const handleLanguageChange = vi.fn();
    render(
      <LanguageToggle
        language="en"
        onLanguageChange={handleLanguageChange}
      />
    );

    expect(screen.getByTestId('language-toggle')).toBeInTheDocument();
    expect(screen.getByLabelText('English flag')).toBeInTheDocument();
    expect(screen.getByText('EN')).toBeInTheDocument();
    expect(screen.getByLabelText('Indonesian flag')).toBeInTheDocument();
    expect(screen.getByText('ID')).toBeInTheDocument();

    const idBtn = screen.getByTestId('lang-id-btn');
    fireEvent.click(idBtn);
    expect(handleLanguageChange).toHaveBeenCalledWith('id');
  });

  it('allows switching from Indonesian back to English', () => {
    const handleLanguageChange = vi.fn();
    render(
      <LanguageToggle
        language="id"
        onLanguageChange={handleLanguageChange}
      />
    );

    const enBtn = screen.getByTestId('lang-en-btn');
    fireEvent.click(enBtn);
    expect(handleLanguageChange).toHaveBeenCalledWith('en');
  });
});

describe('WelcomeModal Component', () => {
  it('renders welcome modal centered with logo, title, dataset choices, and "Have fun" button without rocket emoji', () => {
    const handleClose = vi.fn();
    const handleLanguageChange = vi.fn();

    render(
      <WelcomeModal
        isOpen={true}
        onClose={handleClose}
        language="en"
        onLanguageChange={handleLanguageChange}
      />
    );

    expect(screen.getByTestId('welcome-modal')).toBeInTheDocument();
    expect(screen.getByText('Welcome to Lux')).toBeInTheDocument();
    expect(screen.getByText('What is Lux?')).toBeInTheDocument();
    expect(screen.getByText('How It Works')).toBeInTheDocument();

    // Verify dataset choices (Reserved scenario vs Custom upload)
    expect(screen.getByTestId('welcome-dataset-options')).toBeInTheDocument();
    expect(screen.getAllByText(/Monday Revenue Mystery/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/Add Your Own Custom Dataset/i)).toBeInTheDocument();

    const closeBtn = screen.getByTestId('welcome-close-btn');
    expect(closeBtn).toBeInTheDocument();
    expect(closeBtn).toHaveTextContent('Have fun');
    expect(closeBtn.textContent).not.toContain('🚀');

    fireEvent.click(closeBtn);
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it('translates content to Indonesian when language is id', () => {
    render(
      <WelcomeModal
        isOpen={true}
        onClose={vi.fn()}
        language="id"
        onLanguageChange={vi.fn()}
      />
    );

    expect(screen.getByText('Selamat Datang di Lux')).toBeInTheDocument();
    expect(screen.getByText('Apa itu Lux?')).toBeInTheDocument();
    expect(screen.getByText('Cara Kerja Platform')).toBeInTheDocument();
    expect(screen.getByText(/Tambahkan Dataset Anda Sendiri/i)).toBeInTheDocument();
    expect(screen.getByTestId('welcome-close-btn')).toHaveTextContent('Selamat Menjelajah');
    expect(screen.getByTestId('welcome-close-btn').textContent).not.toContain('🚀');
  });

  it('does not render when isOpen is false', () => {
    render(
      <WelcomeModal
        isOpen={false}
        onClose={vi.fn()}
        language="en"
        onLanguageChange={vi.fn()}
      />
    );

    expect(screen.queryByTestId('welcome-modal')).not.toBeInTheDocument();
  });
});

describe('GuideModal Component', () => {
  it('renders guide modal with "How this works" heading at top, dataset choices in Step 1, and "Close guide" button at bottom', () => {
    const handleClose = vi.fn();

    render(
      <GuideModal
        isOpen={true}
        onClose={handleClose}
        language="en"
        onLanguageChange={vi.fn()}
      />
    );

    expect(screen.getByTestId('guide-modal')).toBeInTheDocument();
    expect(screen.getByText('How this works')).toBeInTheDocument();
    expect(screen.getByText(/Step 1: Choose Your Dataset/i)).toBeInTheDocument();
    expect(screen.getByText('Step 2: Run Validations')).toBeInTheDocument();
    expect(screen.getByText('Step 3: Explore Lineage DAG')).toBeInTheDocument();
    expect(screen.getByText('Step 4: Analyze Blast Radius')).toBeInTheDocument();
    expect(screen.getByText('Step 5: Monitor Pipeline Observability')).toBeInTheDocument();
    expect(screen.getByText('Step 6: Review Incident Investigation')).toBeInTheDocument();
    expect(screen.getByText('Step 7: Verify Recovery')).toBeInTheDocument();

    const closeBtn = screen.getByTestId('guide-close-btn');
    expect(closeBtn).toBeInTheDocument();
    expect(closeBtn).toHaveTextContent('Close guide');
    expect(closeBtn.textContent).not.toContain('🚀');

    fireEvent.click(closeBtn);
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it('renders Indonesian guide when language is id', () => {
    render(
      <GuideModal
        isOpen={true}
        onClose={vi.fn()}
        language="id"
        onLanguageChange={vi.fn()}
      />
    );

    expect(screen.getByText(/Langkah 1: Pilih Sumber Dataset/i)).toBeInTheDocument();
    expect(screen.getByTestId('guide-close-btn')).toHaveTextContent('Tutup Panduan');
    expect(screen.getByTestId('guide-close-btn').textContent).not.toContain('🚀');
  });

  it('does not render when isOpen is false', () => {
    render(
      <GuideModal
        isOpen={false}
        onClose={vi.fn()}
        language="en"
        onLanguageChange={vi.fn()}
      />
    );

    expect(screen.queryByTestId('guide-modal')).not.toBeInTheDocument();
  });
});

describe('ScenarioSwitcher Component - Removal of dataset & rule counts', () => {
  const mockScenarios: ScenarioSummary[] = [
    {
      id: 'monday_revenue_mystery',
      name: 'Monday Revenue Mystery',
      category: 'e-commerce',
      is_bundled: true,
      active_fixture_version: 'defective',
      dataset_count: 4,
      rule_count: 8,
    },
  ];

  it('does NOT render "4 datasets | 8 rules" in scenario switcher tools', () => {
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

    expect(screen.queryByText(/4 datasets/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/8 rules/i)).not.toBeInTheDocument();
  });
});
