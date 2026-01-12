// CONTROLLER: Connects Model and View, handles state and actions
import { useState, useCallback, useMemo, useEffect } from 'react';
import { Goal } from '@/types/goal';
import { GoalsAPI, CreateGoalRequest, GoalListResponse } from '@/lib/goals-api';
import { EntriesAPI } from '@/lib/entries-api';
import { useAuth } from '@/context/AuthContext';

export interface CreateGoalData extends CreateGoalRequest {}

export function useGoalsController() {
  const { token } = useAuth();
  const [goals, setGoals] = useState<Goal[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);

  // Fetch goals function extracted for reuse
  const fetchGoals = useCallback(async () => {
    if (!token) {
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      const data: GoalListResponse = await GoalsAPI.listGoals(0, 100, token);
      
      // Fetch entries for each goal to calculate completed hours
      const goalsWithHours = await Promise.all(
        data.goals.map(async (goal) => {
          try {
            // Validate goal ID format
            if (!goal.id || goal.id.trim() === '') {
              console.warn(`Goal has invalid ID:`, goal);
              return { ...goal, completedHours: 0 };
            }

            // Fetch ALL entries to calculate accurate completed hours
            // Start with a reasonable page size, then fetch more if needed
            let allEntries: any[] = [];
            let currentSkip = 0;
            const pageSize = 100;
            let hasMore = true;

            while (hasMore) {
              const entriesData = await EntriesAPI.listGoalEntries(goal.id, currentSkip, pageSize, token, 'work_date', 'desc');
              allEntries = [...allEntries, ...entriesData.entries];
              
              // Check if there are more entries to fetch
              hasMore = allEntries.length < entriesData.total;
              currentSkip += pageSize;
              
              // Safety check to prevent infinite loops
              if (currentSkip > 100000) break;
            }

            const completedMinutes = allEntries.reduce((sum, entry) => sum + Number(entry.minutes || 0), 0);
            const completedHours = completedMinutes / 60;
            return { ...goal, completedHours: Number.isFinite(completedHours) ? completedHours : 0 };
          } catch (err) {
            console.error(`Failed to fetch entries for goal ${goal.id}:`, err);
            // Ensure completedHours is set to 0 on error
            return { ...goal, completedHours: 0 };
          }
        })
      );
      
      setGoals(goalsWithHours);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load goals';
      setError(errorMessage);
      console.error('Failed to fetch goals:', err);
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  // Fetch goals on mount or when token changes
  useEffect(() => {
    fetchGoals();
  }, [fetchGoals]);

  // Derived state
  const activeGoals = useMemo(
    () => goals.filter((g) => {
      const completed = Number(g.completedHours) || 0;
      const target = Number(g.targetHours) || 0;
      return completed < target;
    }),
    [goals]
  );

  const completedGoals = useMemo(
    () => goals.filter((g) => {
      const completed = Number(g.completedHours) || 0;
      const target = Number(g.targetHours) || 0;
      return completed >= target && target > 0;
    }),
    [goals]
  );

  const statistics = useMemo(
    () => ({
      totalHours: goals.reduce((sum, g) => sum + (Number(g.completedHours) || 0), 0),
      totalTarget: goals.reduce((sum, g) => sum + (Number(g.targetHours) || 0), 0),
      totalEarned: goals.reduce((sum, g) => {
        const hours = Number(g.completedHours) || 0;
        const rate = Number(g.hourlyRate) || 0;
        return sum + (hours * rate);
      }, 0),
      activeCount: activeGoals.length,
      completedCount: completedGoals.length,
    }),
    [goals, activeGoals.length, completedGoals.length]
  );

  // Actions
  const openCreateDialog = useCallback(() => {
    setCreateDialogOpen(true);
  }, []);

  const createGoal = useCallback(
    async (data: CreateGoalData) => {
      if (!token) {
        setError('Not authenticated');
        return null;
      }

      try {
        setError(null);
        const newGoal = await GoalsAPI.createGoal(data, token);
        setGoals((prev) => [newGoal, ...prev]);
        setCreateDialogOpen(false);
        return newGoal;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to create goal';
        setError(errorMessage);
        console.error('Failed to create goal:', err);
        return null;
      }
    },
    [token]
  );

  const updateGoal = useCallback(
    async (id: string, data: Partial<Goal>) => {
      if (!token) {
        setError('Not authenticated');
        return null;
      }

      try {
        setError(null);
        const updated = await GoalsAPI.updateGoal(id, data, token);
        setGoals((prev) => prev.map((g) => (g.id === id ? updated : g)));
        return updated;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to update goal';
        setError(errorMessage);
        console.error('Failed to update goal:', err);
        return null;
      }
    },
    [token]
  );

  const deleteGoal = useCallback(
    async (id: string) => {
      if (!token) {
        setError('Not authenticated');
        return false;
      }

      try {
        setError(null);
        await GoalsAPI.deleteGoal(id, token);
        setGoals((prev) => prev.filter((g) => g.id !== id));
        return true;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to delete goal';
        setError(errorMessage);
        console.error('Failed to delete goal:', err);
        return false;
      }
    },
    [token]
  );

  return {
    goals,
    activeGoals,
    completedGoals,
    statistics,
    createDialogOpen,
    setCreateDialogOpen,
    openCreateDialog,
    createGoal,
    updateGoal,
    deleteGoal,
    refetchGoals: fetchGoals,
    isLoading,
    error,
  };
}
