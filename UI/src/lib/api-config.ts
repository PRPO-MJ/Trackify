/**
 * API Client Configuration
 * Centralized API endpoint configuration
 */

const USER_SERVICE_URL = import.meta.env.VITE_USER_SERVICE_URL || 'http://localhost:8006';
const GOALS_SERVICE_URL = import.meta.env.VITE_GOALS_SERVICE_URL || 'http://localhost:8008';
const ENTRIES_SERVICE_URL = import.meta.env.VITE_ENTRIES_SERVICE_URL || 'http://localhost:8009';
const PDF_SERVICE_URL = import.meta.env.VITE_PDF_SERVICE_URL || 'http://localhost:8010';
const MAILER_SERVICE_URL = import.meta.env.VITE_MAILER_SERVICE_URL || 'http://localhost:8002';

export const API_USER_URL = USER_SERVICE_URL + '/api';
export const API_GOALS_URL = GOALS_SERVICE_URL + '/api';
export const API_ENTRIES_URL = ENTRIES_SERVICE_URL + '/api';
export const API_PDF_URL = PDF_SERVICE_URL + '/api';
export const API_MAILER_URL = MAILER_SERVICE_URL + '/api';

export const API_ENDPOINTS = {
  // User Service
  user: {
    profile: `${USER_SERVICE_URL}/api/users/me`,
    updateProfile: `${USER_SERVICE_URL}/api/users/me`,
    verify: `${USER_SERVICE_URL}/api/auth/verify`,
  },
  // Goals Service
  goals: {
    list: `${GOALS_SERVICE_URL}/api/goals`,
    create: `${GOALS_SERVICE_URL}/api/goals`,
    detail: (id: string) => `${GOALS_SERVICE_URL}/api/goals/${id}`,
    update: (id: string) => `${GOALS_SERVICE_URL}/api/goals/${id}`,
    delete: (id: string) => `${GOALS_SERVICE_URL}/api/goals/${id}`,
  },
  // Entries Service
  entries: {
    list: `${ENTRIES_SERVICE_URL}/api/entries`,
    create: `${ENTRIES_SERVICE_URL}/api/entries`,
    detail: (id: string) => `${ENTRIES_SERVICE_URL}/api/entries/${id}`,
    update: (id: string) => `${ENTRIES_SERVICE_URL}/api/entries/${id}`,
    delete: (id: string) => `${ENTRIES_SERVICE_URL}/api/entries/${id}`,
    byGoal: (goalId: string) => `${ENTRIES_SERVICE_URL}/api/goals/${goalId}/entries`,
  },
  // PDF Service
  pdf: {
    goalReport: (goalId: string) => `${PDF_SERVICE_URL}/api/pdf/goal/${goalId}`,
    fullReport: `${PDF_SERVICE_URL}/api/pdf/report`,
  },
  // Mailer Service
  mailer: {
    emailSettings: (goalId: string) => `${MAILER_SERVICE_URL}/api/mail/settings/${goalId}`,
    saveSettings: `${MAILER_SERVICE_URL}/api/mail/settings`,
    sendNow: `${MAILER_SERVICE_URL}/api/mail/send-now`,
  },
};

export const getAuthHeaders = (token?: string): HeadersInit => {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  const authToken = token || localStorage.getItem('access_token');
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
    console.log('[API Config] Auth token present:', authToken.substring(0, 20) + '...');
  } else {
    console.warn('[API Config] No auth token available!');
  }

  return headers;
};
