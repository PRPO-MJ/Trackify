// VIEW: Pure presentational component for goal card
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Goal } from '@/types/goal';
import { Clock, DollarSign, ArrowRight, Calendar } from 'lucide-react';
import { differenceInDays } from 'date-fns';
import { getCurrencySymbol } from '@/lib/utils';

interface GoalCardViewProps {
  goal: Goal;
  index: number;
  currency?: string;
}

export function GoalCardView({ goal, index, currency }: GoalCardViewProps) {
  const progressPercent = Math.min((goal.completedHours / goal.targetHours) * 100, 100);
  const isCompleted = progressPercent >= 100;
  const daysRemaining = differenceInDays(new Date(goal.endDate), new Date());
  const earnedAmount = goal.completedHours * goal.hourlyRate;
  const currencySymbol = getCurrencySymbol(currency);
  
  const progressVariant = isCompleted 
    ? 'success' as const
    : progressPercent > 75 
      ? 'info' as const
      : progressPercent > 50 
        ? 'progress' as const
        : progressPercent > 25 
          ? 'warning' as const
          : 'purple' as const;

  return (
    <Link to={`/goal/${goal.id}`}>
      <Card 
        className="group relative overflow-hidden border transition-all duration-300 hover:border-foreground/20 hover:shadow-lg animate-slide-up"
        style={{ animationDelay: `${index * 100}ms` }}
      >
        <CardHeader className="pb-3">
          <div className="space-y-1">
            <h3 className="font-semibold leading-none tracking-tight group-hover:text-foreground/80 transition-colors">
              {goal.name}
            </h3>
            <p className="text-sm text-muted-foreground line-clamp-1">
              {goal.description}
            </p>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Progress</span>
              <span className="font-medium">{progressPercent.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}%</span>
            </div>
            <Progress value={progressPercent} variant={progressVariant} className="h-2" />
          </div>

          <div className="grid grid-cols-3 gap-4 pt-2">
            <div className="space-y-1">
              <div className="flex items-center gap-1 text-muted-foreground">
                <Clock className="h-3.5 w-3.5" />
                <span className="text-xs">Hours</span>
              </div>
              <p className="text-sm font-medium">
                {goal.completedHours.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} / {goal.targetHours.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} h
              </p>
            </div>

            {goal.hourlyRate > 0 && (
              <div className="space-y-1">
                <div className="flex items-center gap-1 text-muted-foreground">
                  <DollarSign className="h-3.5 w-3.5" />
                  <span className="text-xs">Earned</span>
                </div>
                <p className="text-sm font-medium text-money">
                  {currencySymbol} {earnedAmount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </p>
              </div>
            )}

            <div className="space-y-1">
              <div className="flex items-center gap-1 text-muted-foreground">
                <Calendar className="h-3.5 w-3.5" />
                <span className="text-xs">Deadline</span>
              </div>
              <p className={`text-sm font-medium ${daysRemaining < 7 && !isCompleted ? 'text-warning' : ''}`}>
                {daysRemaining > 0 ? `${daysRemaining}d left` : 'Ended'}
              </p>
            </div>
          </div>

          <div className="flex items-center justify-end pt-2 text-sm text-muted-foreground group-hover:text-foreground transition-colors">
            View details
            <ArrowRight className="ml-1 h-4 w-4 transition-transform group-hover:translate-x-1" />
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
