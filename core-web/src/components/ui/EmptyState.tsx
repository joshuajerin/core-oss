import type { ReactNode } from 'react';

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex-1 flex items-center justify-center p-8">
      <div className="flex flex-col items-center gap-3 max-w-sm text-center">
        {icon && (
          <div className="w-12 h-12 rounded-xl bg-gray-100 flex items-center justify-center text-gray-400">
            {icon}
          </div>
        )}
        <p className="text-sm font-medium text-text-dark">{title}</p>
        {description && (
          <p className="text-xs text-text-secondary">{description}</p>
        )}
        {action && (
          <button
            onClick={action.onClick}
            className="mt-1 px-4 py-1.5 text-sm font-medium rounded-lg bg-brand-primary text-white hover:opacity-90 transition-opacity"
          >
            {action.label}
          </button>
        )}
      </div>
    </div>
  );
}
