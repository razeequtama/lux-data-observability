import React from 'react';
import { X, BookOpen, Lightbulb } from 'lucide-react';
import { Language, translations } from '../../i18n/translations';
import { LanguageToggle } from './LanguageToggle';

export interface GuideModalProps {
  isOpen: boolean;
  onClose: () => void;
  language: Language;
  onLanguageChange: (lang: Language) => void;
}

export const GuideModal: React.FC<GuideModalProps> = ({
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
      aria-labelledby="guide-modal-title"
      data-testid="guide-modal"
    >
      {/* Centered Modal Card with Fixed Top and Bottom */}
      <div
        className="w-full max-w-3xl bg-[#0d0f1b]/95 border border-white/[0.1] border-t-purple-400/40 rounded-3xl shadow-2xl flex flex-col overflow-hidden max-h-[88vh] sm:max-h-[82vh] transition-all animate-in fade-in zoom-in-95 duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        {/* FIXED TOP HEADING (Unscrollable) */}
        <div className="shrink-0 p-5 sm:p-6 lg:p-7 border-b border-white/[0.08] bg-[#090a14]/90 flex items-center justify-between gap-4">
          <div className="flex items-center space-x-3.5">
            <div className="p-2.5 rounded-2xl bg-lux-950 border border-lux-600/50 text-lux-400 shadow-[0_0_16px_rgba(168,85,247,0.35)] shrink-0">
              <BookOpen className="w-5 h-5 text-lux-400" />
            </div>
            <div>
              <h2
                id="guide-modal-title"
                className="text-base sm:text-lg lg:text-xl font-black text-white tracking-tight"
              >
                {t.guide.heading}
              </h2>
              <p className="text-xs text-purple-300 font-medium">
                {t.guide.subtitle}
              </p>
            </div>
          </div>

          {/* Right: Language toggle and close icon */}
          <div className="flex items-center space-x-3 shrink-0">
            <LanguageToggle
              language={language}
              onLanguageChange={onLanguageChange}
              size="sm"
            />
            <button
              type="button"
              onClick={onClose}
              data-testid="guide-close-icon"
              aria-label="Close Guide"
              className="p-1.5 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800/80 transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* SCROLLABLE INFORMATION SECTION (Explains only how the tool works) */}
        <div
          className="flex-1 overflow-y-auto p-5 sm:p-7 lg:p-8 space-y-4 text-slate-300 text-xs sm:text-sm leading-relaxed"
          data-testid="guide-info-section"
        >
          {t.guide.steps.map((s, index) => (
            <div
              key={index}
              className="bg-slate-950/70 border border-white/[0.08] hover:border-purple-400/40 rounded-2xl p-4 sm:p-5 space-y-2.5 transition-all shadow-sm"
            >
              <div className="flex items-center space-x-3">
                <span className="w-6 h-6 rounded-lg bg-lux-950 border border-lux-600/50 text-purple-300 text-xs font-mono font-bold flex items-center justify-center shrink-0">
                  {s.number}
                </span>
                <h3 className="text-xs sm:text-sm font-bold text-white tracking-tight">
                  {s.title}
                </h3>
              </div>

              <p className="text-slate-300 text-xs sm:text-sm leading-relaxed pl-9 whitespace-pre-line">
                {s.desc}
              </p>

              {s.actionTip && (
                <div className="ml-9 flex items-center space-x-2 px-3 py-2 rounded-xl bg-purple-950/30 border border-purple-500/20 text-purple-200 text-[11px]">
                  <Lightbulb className="w-3.5 h-3.5 text-purple-400 shrink-0" />
                  <span>{s.actionTip}</span>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* FIXED BOTTOM FOOTER (Unscrollable) */}
        <div className="shrink-0 p-4 sm:p-5 border-t border-white/[0.08] bg-[#090a14]/95 flex items-center justify-center">
          <button
            type="button"
            data-testid="guide-close-btn"
            onClick={onClose}
            className="flex items-center justify-center space-x-2 px-8 py-3.5 bg-slate-900 hover:bg-slate-800 text-slate-200 hover:text-white border border-white/[0.1] hover:border-purple-400/50 active:scale-95 rounded-2xl text-xs sm:text-sm font-bold shadow-lg transition-all cursor-pointer whitespace-nowrap min-w-[160px]"
          >
            <span>{t.guide.close}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
