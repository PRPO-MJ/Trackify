// PAGE: Composes Views with Controller (MVC Pattern)
import { useEffect } from 'react';
import { CreateGoalDialog } from '@/components/goals/CreateGoalDialog';
import { useGoalsController } from '@/controllers/useGoalsController';
import { useUserController } from '@/controllers/useUserController';
import { WelcomeHeader } from '@/views/dashboard/WelcomeHeader';
import { StatsGrid } from '@/views/dashboard/StatsGrid';
import { GoalsSection } from '@/views/dashboard/GoalsSection';

export default function Dashboard() {
  // Controllers handle all state and logic
  const { 
    activeGoals, 
    completedGoals, 
    statistics,
    createDialogOpen,
    createGoal,
    setCreateDialogOpen,
    openCreateDialog,
    refetchGoals,
  } = useGoalsController();

  const { firstName, user } = useUserController();

  // Refetch goals when dashboard becomes visible (user navigates back)
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        refetchGoals();
      }
    };

    // Refetch on window focus (when user comes back to the tab/window)
    const handleFocus = () => {
      refetchGoals();
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('focus', handleFocus);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('focus', handleFocus);
    };
  }, [refetchGoals]);

  return (
    <div className="container py-8">
      {/* Views are pure presentational components */}
      <WelcomeHeader firstName={firstName} />

      <StatsGrid 
        totalHours={statistics.totalHours}
        totalTarget={statistics.totalTarget}
        totalEarned={statistics.totalEarned}
        activeCount={statistics.activeCount}
        completedCount={statistics.completedCount}
        currency={user?.currency}
      />

      <GoalsSection
        title="Active Goals"
        description={`${activeGoals.length} goal${activeGoals.length !== 1 ? 's' : ''} in progress`}
        goals={activeGoals}
        variant="active"
        showCreateButton
        onCreateClick={openCreateDialog}
        currency={user?.currency}
      />

      {completedGoals.length > 0 && (
        <GoalsSection
          title="Completed Goals"
          description={`${completedGoals.length} goal${completedGoals.length !== 1 ? 's' : ''} achieved`}
          goals={completedGoals}
          variant="completed"
          currency={user?.currency}
        />
      )}

      <CreateGoalDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
        onSubmit={createGoal}
      />
    </div>
  );
}
