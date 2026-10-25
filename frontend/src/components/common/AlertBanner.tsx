import React from 'react';
import { AlertTriangle, CheckCircle2, Info, X } from 'lucide-react';

export type AlertType = 'error' | 'warning' | 'success' | 'info';

interface AlertBannerProps {
  type: AlertType;
  message: string;
  details?: string;
  onClose?: () => void;
  className?: string;
}

export const AlertBanner: React.FC<AlertBannerProps> = ({
  type,
  message,
  details,
  onClose,
  className = '',
}) => {
  const getStyles = () => {
    switch (type) {
      case 'error':
        return {
          container: 'bg-rose-950/40 border-rose-600/40 text-rose-200',
          icon: <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />,
          title: 'text-rose-300',
        };
      case 'warning':
        return {
          container: 'bg-amber-950/40 border-amber-600/40 text-amber-200',
          icon: <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />,
          title: 'text-amber-300',
        };
      case 'success':
        return {
          container: 'bg-emerald-950/40 border-emerald-600/40 text-emerald-200',
          icon: <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />,
          title: 'text-emerald-300',
        };
      case 'info':
      default:
        return {
          container: 'bg-lux-950/40 border-lux-600/40 text-lux-200',
          icon: <Info className="w-5 h-5 text-lux-400 shrink-0 mt-0.5" />,
          title: 'text-lux-300',
        };
    }
  };

  const style = getStyles();

  return (
    <div
      role="alert"
      className={`flex items-start justify-between p-5 sm:p-6 border rounded-2xl backdrop-blur-xl text-sm shadow-lg ${style.container} ${className}`}
    >
      <div className="flex items-start space-x-3.5">
        {style.icon}
        <div className="space-y-1">
          <p className={`font-bold ${style.title}`}>{message}</p>
          {details && <p className="text-xs opacity-90 mt-1 font-mono break-all leading-relaxed">{details}</p>}
        </div>
      </div>
      {onClose && (
        <button
          type="button"
          onClick={onClose}
          aria-label="Dismiss alert"
          className="ml-4 p-1.5 rounded-lg hover:bg-slate-800/60 text-slate-400 hover:text-white transition-colors cursor-pointer"
        >
          <X className="w-4.5 h-4.5" />
        </button>
      )}
    </div>
  );
};

