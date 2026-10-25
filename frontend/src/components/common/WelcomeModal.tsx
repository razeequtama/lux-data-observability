import React from 'react';
import { X, Sparkles, ShieldCheck, Compass, Database, Upload } from 'lucide-react';
import { Language, translations } from '../../i18n/translations';
import { LanguageToggle } from './LanguageToggle';

export interface WelcomeModalProps {
  isOpen: boolean;
  onClose: () => void;
  language: Language;
  onLanguageChange: (lang: Language) => void;
}

export const WelcomeModal: React.FC<WelcomeModalProps> = ({
  isOpen,
  onClose,
  language,
  onLanguageChange,
}) => {
  if (!isOpen) return null;

  const t = translations[language];

  return (
    <div
      className="fixed inset-0 z-50 overflow-hidden bg-slate-950/85 backdrop-blur-md flex items-center justify-center p-4 sm:p-6 lg:p-8"
      role="dialog"
      aria-modal="true"
      aria-labelledby="welcome-modal-title"
      data-testid="welcome-modal"
    >
      {/* Centered Modal Card with Fixed Top and Bottom */}
      <div
        className="w-full max-w-3xl bg-[#0d0f1b]/95 border border-white/[0.1] border-t-purple-400/40 rounded-3xl shadow-2xl flex flex-col overflow-hidden max-h-[88vh] sm:max-h-[82vh] transition-all animate-in fade-in zoom-in-95 duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        {/* FIXED TOP HEADER (Unscrollable) */}
        <div className="shrink-0 p-5 sm:p-6 lg:p-7 border-b border-white/[0.08] bg-[#090a14]/90 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center space-x-4">
            {/* Logo with Ambient Purple Glow */}
            <div className="relative group shrink-0">
              <div
                className="absolute -inset-2 bg-gradient-to-r from-purple-600/40 via-lux-500/30 to-indigo-600/30 rounded-2xl blur-lg pointer-events-none"
                aria-hidden="true"
              />
              <img
                src="/logo_and_title.svg"
                alt="Lux Logo"
                className="h-12 sm:h-14 lg:h-16 w-auto object-contain relative z-10 filter drop-shadow-[0_0_16px_rgba(168,85,247,0.65)]"
              />
            </div>

            <div className="space-y-0.5">
              <div className="flex items-center space-x-2">
                <h2
                  id="welcome-modal-title"
                  className="text-base sm:text-lg font-black text-white tracking-tight"
                >
                  {t.welcome.title}
                </h2>
                <span className="px-2.5 py-0.5 rounded-md text-[10px] font-sans font-bold bg-lux-950 text-purple-200 border border-lux-600/50 tracking-wider">
                  v1.0.0
                </span>
              </div>
              <p className="text-xs text-purple-300 font-medium line-clamp-1">
                {t.welcome.subtitle}
              </p>
            </div>
          </div>

          {/* Right side of fixed header: Language Toggle & Quick Close */}
          <div className="flex items-center justify-between sm:justify-end space-x-3 shrink-0">
            <LanguageToggle
              language={language}
              onLanguageChange={onLanguageChange}
              size="sm"
            />
            <button
              type="button"
              onClick={onClose}
              data-testid="welcome-close-icon"
              aria-label="Close Welcome Dialog"
              className="p-1.5 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800/80 transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* SCROLLABLE INFORMATION SECTION */}
        <div
          className="flex-1 overflow-y-auto p-5 sm:p-7 lg:p-8 space-y-7 text-slate-300 text-xs sm:text-sm leading-relaxed"
          data-testid="welcome-info-section"
        >
          {/* Section 1: What is Lux? */}
          <div className="space-y-3.5">
            <div className="flex items-center space-x-2 text-white">
              <div className="p-1.5 rounded-lg bg-lux-950 border border-lux-600/40 text-lux-400">
                <ShieldCheck className="w-4 h-4" />
              </div>
              <h3 className="text-sm sm:text-base font-bold tracking-tight">
                {t.welcome.whatIsHeading}
              </h3>
            </div>
            <p className="text-slate-300 text-xs sm:text-sm leading-relaxed">
              {t.welcome.whatIsDescription}
            </p>

            {/* Core Capability Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
              {t.welcome.whatIsPoints.map((point, index) => (
                <div
                  key={index}
                  className="bg-slate-950/70 border border-white/[0.08] hover:border-purple-400/40 rounded-2xl p-3.5 space-y-1 transition-colors shadow-sm"
                >
                  <div className="flex items-center space-x-2">
                    <Sparkles className="w-3.5 h-3.5 text-purple-400 shrink-0" />
                    <h4 className="text-xs font-bold text-white tracking-tight">
                      {point.title}
                    </h4>
                  </div>
                  <p className="text-[11px] sm:text-xs text-slate-400 leading-normal pl-5.5">
                    {point.desc}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Dataset Choices: Reserved Scenario OR Add Your Own */}
          <div className="space-y-3.5 border-t border-white/[0.08] pt-6" data-testid="welcome-dataset-options">
            <div className="flex items-center space-x-2 text-white">
              <div className="p-1.5 rounded-lg bg-lux-950 border border-lux-600/40 text-lux-400">
                <Database className="w-4 h-4" />
              </div>
              <h3 className="text-sm sm:text-base font-bold tracking-tight">
                {t.welcome.datasetOptionsHeading}
              </h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 pt-1">
              {/* Option A: Reserved Monday Revenue Mystery Dataset */}
              <div className="bg-gradient-to-b from-lux-950/70 to-slate-950/80 border border-purple-500/30 hover:border-purple-400/60 rounded-2xl p-4 space-y-2 transition-all shadow-md">
                <div className="flex items-center space-x-2.5">
                  <span className="p-1.5 rounded-lg bg-lux-900/80 text-purple-300 border border-purple-500/40">
                    <Database className="w-4 h-4" />
                  </span>
                  <h4 className="text-xs sm:text-sm font-bold text-white tracking-tight">
                    {t.welcome.reservedOptionTitle}
                  </h4>
                </div>
                <p className="text-[11px] sm:text-xs text-slate-300 leading-relaxed pl-1">
                  {t.welcome.reservedOptionDesc}
                </p>
              </div>

              {/* Option B: Add Your Own Custom Dataset */}
              <div className="bg-gradient-to-b from-indigo-950/50 to-slate-950/80 border border-indigo-500/30 hover:border-indigo-400/60 rounded-2xl p-4 space-y-2 transition-all shadow-md">
                <div className="flex items-center space-x-2.5">
                  <span className="p-1.5 rounded-lg bg-indigo-900/80 text-indigo-300 border border-indigo-500/40">
                    <Upload className="w-4 h-4" />
                  </span>
                  <h4 className="text-xs sm:text-sm font-bold text-white tracking-tight">
                    {t.welcome.customOptionTitle}
                  </h4>
                </div>
                <p className="text-[11px] sm:text-xs text-slate-300 leading-relaxed pl-1">
                  {t.welcome.customOptionDesc}
                </p>
              </div>
            </div>
          </div>

          {/* Section 2: How It Works */}
          <div className="space-y-3.5 border-t border-white/[0.08] pt-6">
            <div className="flex items-center space-x-2 text-white">
              <div className="p-1.5 rounded-lg bg-lux-950 border border-lux-600/40 text-lux-400">
                <Compass className="w-4 h-4" />
              </div>
              <h3 className="text-sm sm:text-base font-bold tracking-tight">
                {t.welcome.howWorksHeading}
              </h3>
            </div>
            <p className="text-slate-400 text-xs">
              {t.welcome.howWorksDescription}
            </p>

            {/* Step-by-step Guided Journey */}
            <div className="space-y-2.5">
              {t.welcome.steps.map((item, idx) => (
                <div
                  key={idx}
                  className="flex items-start space-x-3.5 bg-slate-950/60 border border-white/[0.06] rounded-2xl p-3.5"
                >
                  <span className="shrink-0 px-2 py-0.5 rounded-lg font-sans text-[11px] font-bold bg-lux-950 text-purple-300 border border-lux-600/40 mt-0.5">
                    {item.step}
                  </span>
                  <div className="space-y-0.5">
                    <h4 className="text-xs sm:text-sm font-bold text-white tracking-tight">
                      {item.title}
                    </h4>
                    <p className="text-[11px] sm:text-xs text-slate-400 leading-normal">
                      {item.desc}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* FIXED BOTTOM FOOTER (Unscrollable) */}
        <div className="shrink-0 p-4 sm:p-5 border-t border-white/[0.08] bg-[#090a14]/95 flex items-center justify-center">
          <button
            type="button"
            data-testid="welcome-close-btn"
            onClick={onClose}
            className="flex items-center justify-center space-x-2 px-8 py-3.5 bg-gradient-to-r from-lux-700 via-lux-600 to-indigo-600 hover:from-lux-600 hover:to-indigo-500 active:scale-95 text-white rounded-2xl text-xs sm:text-sm font-bold shadow-[0_0_24px_rgba(124,58,237,0.5)] ring-1 ring-purple-400/50 transition-all cursor-pointer whitespace-nowrap min-w-[160px]"
          >
            <span>{t.welcome.cta}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
