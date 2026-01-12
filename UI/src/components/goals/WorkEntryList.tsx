import { WorkEntry } from '@/types/goal';
import { format } from 'date-fns';
import { Clock, FileText } from 'lucide-react';
import { getCurrencySymbol } from '@/lib/utils';

interface WorkEntryListProps {
  entries: WorkEntry[];
  hourlyRate: number;
  currency?: string;
}

export function WorkEntryList({ entries, hourlyRate, currency }: WorkEntryListProps) {
  // Don't re-sort - entries are already sorted by the backend
  const currencySymbol = getCurrencySymbol(currency);

  if (entries.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <FileText className="h-12 w-12 text-muted-foreground/50 mb-4" />
        <h3 className="font-medium text-muted-foreground">No work entries yet</h3>
        <p className="text-sm text-muted-foreground/70 mt-1">
          Start logging your hours to track progress
        </p>
      </div>
    );
  }

  // Helper to format minutes into Xh Ym
  const formatHours = (minutes: number) => {
    if (!minutes || minutes <= 0) return '0h 0m';
    const hrs = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hrs}h ${mins}m`;
  };

  return (
    <div className="space-y-3">
      {entries.map((entry, index) => {
        const decimalHours = entry.minutes / 60; // For earnings calculation
        return (
          <div
            key={entry.id}
            className="flex items-start gap-4 p-4 rounded-lg border bg-card transition-all hover:border-foreground/20 animate-fade-in"
            style={{ animationDelay: `${index * 50}ms` }}
          >
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-secondary">
              <Clock className="h-4 w-4 text-muted-foreground" />
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="font-medium">{formatHours(entry.minutes)} logged</p>
                  <p className="text-sm text-muted-foreground mt-0.5">
                    {entry.description || 'No description'}
                  </p>
                </div>
                <div className="text-right shrink-0">
                  <p className="text-sm text-muted-foreground">
                    {format(new Date(entry.date), 'MMM d, yyyy')}
                  </p>
                  {hourlyRate > 0 && (
                    <p className="text-sm font-medium text-money mt-0.5">
                      +{currencySymbol} {(decimalHours * hourlyRate).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
