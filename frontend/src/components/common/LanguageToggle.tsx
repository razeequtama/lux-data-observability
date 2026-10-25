import React from 'react';
import { Language } from '../../i18n/translations';

export const EnglishFlag: React.FC<{ className?: string }> = ({ className = 'w-5 h-3.5' }) => (
  <svg
    viewBox="0 0 60 30"
    className={`rounded-[2px] shadow-sm inline-block shrink-0 ${className}`}
    aria-label="English flag"
    role="img"
  >
    <clipPath id="uk-clip">
      <path d="M0 0v30h60V0z" />
    </clipPath>
    <clipPath id="uk-diag">
      <path d="M30 15h30v15zv15H30zH0v-15zv-15h30z" />
    </clipPath>
    <g clipPath="url(#uk-clip)">
      <path d="M0 0v30h60V0z" fill="#012169" />
      <path d="M0 0l60 30M60 0L0 30" stroke="#fff" strokeWidth="6" />
      <path d="M0 0l60 30M60 0L0 30" clipPath="url(#uk-diag)" stroke="#C8102E" strokeWidth="4" />
      <path d="M30 0v30M0 15h60" stroke="#fff" strokeWidth="10" />
      <path d="M30 0v30M0 15h60" stroke="#C8102E" strokeWidth="6" />
    </g>
  </svg>
);

export const IndonesianFlag: React.FC<{ className?: string }> = ({ className = 'w-5 h-3.5' }) => (
  <svg
    viewBox="0 0 60 30"
    className={`rounded-[2px] border border-white/20 shadow-sm inline-block shrink-0 overflow-hidden ${className}`}
    aria-label="Indonesian flag"
    role="img"
  >
    <rect width="60" height="15" fill="#CE1126" />
    <rect y="15" width="60" height="15" fill="#FFFFFF" />
  </svg>
);

interface LanguageToggleProps {
  language: Language;
  onLanguageChange: (lang: Language) => void;
  className?: string;
  size?: 'sm' | 'md';
}

export const LanguageToggle: React.FC<LanguageToggleProps> = ({
  language,
  onLanguageChange,
  className = '',
  size = 'md',
}) => {
  const isSm = size === 'sm';

  return (
    <div
      className={`inline-flex items-center bg-slate-950/80 border border-white/[0.08] p-1 rounded-xl shadow-inner text-xs font-semibold ${className}`}
      data-testid="language-toggle"
      role="group"
      aria-label="Language selection"
    >
      {/* English Toggle Button with UK Flag */}
      <button
        type="button"
        data-testid="lang-en-btn"
        onClick={() => onLanguageChange('en')}
        className={`flex items-center space-x-2 ${
          isSm ? 'px-2.5 py-1 text-xs' : 'px-3 py-1.5 text-xs'
        } rounded-lg transition-all cursor-pointer ${
          language === 'en'
            ? 'bg-gradient-to-r from-lux-700 via-lux-600 to-indigo-600 text-white shadow-[0_0_12px_rgba(168,85,247,0.4)] border border-purple-400/50 font-bold'
            : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
        }`}
        title="English"
        aria-pressed={language === 'en'}
      >
        <EnglishFlag className={isSm ? 'w-4 h-3' : 'w-5 h-3.5'} />
        <span>EN</span>
      </button>

      {/* Indonesian Toggle Button with Indonesian Flag */}
      <button
        type="button"
        data-testid="lang-id-btn"
        onClick={() => onLanguageChange('id')}
        className={`flex items-center space-x-2 ${
          isSm ? 'px-2.5 py-1 text-xs' : 'px-3 py-1.5 text-xs'
        } rounded-lg transition-all cursor-pointer ${
          language === 'id'
            ? 'bg-gradient-to-r from-lux-700 via-lux-600 to-indigo-600 text-white shadow-[0_0_12px_rgba(168,85,247,0.4)] border border-purple-400/50 font-bold'
            : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
        }`}
        title="Bahasa Indonesia"
        aria-pressed={language === 'id'}
      >
        <IndonesianFlag className={isSm ? 'w-4 h-3' : 'w-5 h-3.5'} />
        <span>ID</span>
      </button>
    </div>
  );
};
