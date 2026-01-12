// VIEW: Pure presentational component for stats grid
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Clock, DollarSign, CheckCircle2, Flame } from 'lucide-react';
import { getCurrencySymbol } from '@/lib/utils';

interface StatsGridProps {
  totalHours: number;
  totalTarget: number;
  totalEarned: number;
  activeCount: number;
  completedCount: number;
  currency?: string;
}

export function StatsGrid({ 
  totalHours, 
  totalTarget, 
  totalEarned, 
  activeCount, 
  completedCount,
  currency
}: StatsGridProps) {
  const currencySymbol = getCurrencySymbol(currency);
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-8">
      <Card className="animate-slide-up border-l-4 border-l-info" style={{ animationDelay: '0ms' }}>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Total Hours
          </CardTitle>
          <Clock className="h-4 w-4 text-info" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{totalHours.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} h</div>
          <p className="text-xs text-muted-foreground mt-1">
            total hours logged
          </p>
        </CardContent>
      </Card>

      <Card className="animate-slide-up border-l-4 border-l-money" style={{ animationDelay: '50ms' }}>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Total Earned
          </CardTitle>
          <DollarSign className="h-4 w-4 text-money" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-money">
            {currencySymbol}{totalEarned.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            from billable goals
          </p>
        </CardContent>
      </Card>

      <Card className="animate-slide-up border-l-4 border-l-warning" style={{ animationDelay: '100ms' }}>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Active Goals
          </CardTitle>
          <Flame className="h-4 w-4 text-warning" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{activeCount}</div>
          <p className="text-xs text-muted-foreground mt-1">
            in progress
          </p>
        </CardContent>
      </Card>

      <Card className="animate-slide-up border-l-4 border-l-success" style={{ animationDelay: '150ms' }}>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Completed
          </CardTitle>
          <CheckCircle2 className="h-4 w-4 text-success" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{completedCount}</div>
          <p className="text-xs text-muted-foreground mt-1">
            goals achieved
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
