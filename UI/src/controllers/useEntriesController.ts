// CONTROLLER: Time Entries state and actions
import { useState, useCallback, useEffect } from 'react';
import { WorkEntry } from '@/types/goal';
import { EntriesAPI, CreateEntryRequest, EntryListResponse } from '@/lib/entries-api';
import { useAuth } from '@/context/AuthContext';

export interface CreateEntryData extends CreateEntryRequest {}

export function useEntriesController(goalId?: string) {
  const { token } = useAuth();
  const [entries, setEntries] = useState<WorkEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch entries on mount or when token/goalId changes
  useEffect(() => {
    const fetchEntries = async () => {
      if (!token) {
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        setError(null);
        const data: EntryListResponse = goalId
          ? await EntriesAPI.listGoalEntries(goalId, 0, 100, token)
          : await EntriesAPI.listEntries(0, 100, token);
        setEntries(data.entries || []);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to load entries';
        setError(errorMessage);
        console.error('Failed to fetch entries:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchEntries();
  }, [token, goalId]);

  // Actions
  const createEntry = useCallback(
    async (data: CreateEntryData) => {
      if (!token) {
        setError('Not authenticated');
        return null;
      }

      try {
        setError(null);
        const newEntry = await EntriesAPI.createEntry(data, token);
        setEntries((prev) => [newEntry, ...prev]);
        return newEntry;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to create entry';
        setError(errorMessage);
        console.error('Failed to create entry:', err);
        return null;
      }
    },
    [token]
  );

  const updateEntry = useCallback(
    async (id: string, data: Partial<WorkEntry>) => {
      if (!token) {
        setError('Not authenticated');
        return null;
      }

      try {
        setError(null);
        const updated = await EntriesAPI.updateEntry(id, data, token);
        setEntries((prev) => prev.map((e) => (e.id === id ? updated : e)));
        return updated;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to update entry';
        setError(errorMessage);
        console.error('Failed to update entry:', err);
        return null;
      }
    },
    [token]
  );

  const deleteEntry = useCallback(
    async (id: string) => {
      if (!token) {
        setError('Not authenticated');
        return false;
      }

      try {
        setError(null);
        await EntriesAPI.deleteEntry(id, token);
        setEntries((prev) => prev.filter((e) => e.id !== id));
        return true;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to delete entry';
        setError(errorMessage);
        console.error('Failed to delete entry:', err);
        return false;
      }
    },
    [token]
  );

  return {
    entries,
    createEntry,
    updateEntry,
    deleteEntry,
    isLoading,
    error,
  };
}
