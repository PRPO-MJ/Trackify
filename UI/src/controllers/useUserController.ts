// CONTROLLER: User state and actions
import { useState, useCallback, useEffect } from 'react';
import { User } from '@/types/goal';
import { UserAPI } from '@/lib/user-api';
import { useAuth } from '@/context/AuthContext';

export function useUserController() {
  const { token } = useAuth();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch user profile on mount or when token changes
  useEffect(() => {
    const fetchUser = async () => {
      if (!token) {
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        setError(null);
        const userData = await UserAPI.getProfile(token);
        setUser(userData);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to load user';
        setError(errorMessage);
        console.error('Failed to fetch user:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchUser();
  }, [token]);

  const updateUser = useCallback(
    async (data: Partial<User>) => {
      if (!token) {
        setError('Not authenticated');
        return null;
      }

      try {
        setError(null);
        const updated = await UserAPI.updateProfile(data, token);
        setUser(updated);
        return updated;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to update user';
        setError(errorMessage);
        console.error('Failed to update user:', err);
        return null;
      }
    },
    [token]
  );

  const firstName = user?.name.split(' ')[0] || '';

  return {
    user,
    firstName,
    updateUser,
    isLoading,
    error,
  };
}
