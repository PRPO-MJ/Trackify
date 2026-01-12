/**
 * Authentication Context
 * Manages authentication state and token storage
 */

import React, { createContext, useContext, useCallback, useEffect, useState } from 'react';

interface AuthContextType {
  token: string | null;
  isAuthenticated: boolean;
  user_id: string | null;
  setToken: (token: string) => void;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setTokenState] = useState<string | null>(() => {
    return localStorage.getItem('access_token');
  });
  const [user_id, setUserId] = useState<string | null>(() => {
    return localStorage.getItem('user_id');
  });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setIsLoading(false);
  }, []);

  const setToken = useCallback((newToken: string) => {
    setTokenState(newToken);
    localStorage.setItem('access_token', newToken);
  }, []);

  const logout = useCallback(() => {
    setTokenState(null);
    setUserId(null);
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_id');
  }, []);

  const value: AuthContextType = {
    token,
    isAuthenticated: !!token,
    user_id,
    setToken,
    logout,
    isLoading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
