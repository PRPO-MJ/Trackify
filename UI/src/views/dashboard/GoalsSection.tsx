// VIEW: Pure presentational component for goals section
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { GoalCardView } from '@/views/goals/GoalCardView';
import { Goal } from '@/types/goal';
import { Plus, Target, Flame, CheckCircle2 } from 'lucide-react';

interface GoalsSectionProps {
  title: string;
  description: string;
  goals: Goal[];
  variant: 'active' | 'completed';
  onCreateClick?: () => void;
  showCreateButton?: boolean;
  currency?: string;
}

export function GoalsSection({ 
  title, 
  description, 
  goals, 
  variant,
  onCreateClick,
  showCreateButton = false,
  currency,
}: GoalsSectionProps) {
  const isActive = variant === 'active';

  return (
    <div className={isActive ? 'mb-8' : ''}>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${isActive ? 'bg-warning/20' : 'bg-success/20'}`}>
            {isActive ? (
              <Flame className="h-4 w-4 text-warning" />
            ) : (
              <CheckCircle2 className="h-4 w-4 text-success" />
            )}
          </div>
          <div>
            <h2 className="text-xl font-semibold">{title}</h2>
            <p className="text-sm text-muted-foreground">{description}</p>
          </div>
        </div>
        {showCreateButton && onCreateClick && (
          <Button onClick={onCreateClick}>
            <Plus className="h-4 w-4 mr-2" />
            New Goal
          </Button>
        )}
      </div>

      {goals.length === 0 && isActive ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Target className="h-12 w-12 text-muted-foreground/50 mb-4" />
            <h3 className="font-medium text-muted-foreground mb-2">No active goals</h3>
            <p className="text-sm text-muted-foreground/70 text-center max-w-sm mb-4">
              Create a new goal to start tracking your hours
            </p>
            {onCreateClick && (
              <Button onClick={onCreateClick}>
                <Plus className="h-4 w-4 mr-2" />
                Create Goal
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {goals.map((goal, index) => (
            <GoalCardView key={goal.id} goal={goal} index={index} currency={currency} />
          ))}
        </div>
      )}
    </div>
  );
}
