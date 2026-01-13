/**
 * API Client Configuration
 * Centralized API endpoint configuration
 * Points to API subdomain hosted on AWS EKS
 */

// Base API URL - points to K8s cluster via subdomain
const API_BASE = 'https://api.trackify.zusidelavi.com/api';

export const API_USER_URL = API_BASE;
export const API_GOALS_URL = API_BASE;
export const API_ENTRIES_URL = API_BASE;
export const API_PDF_URL = API_BASE;
export const API_MAILER_URL = API_BASE;

export const API_ENDPOINTS = {
  // User Service
  user: {
    profile: `${API_BASE}/users/me`,
    updateProfile: `${API_BASE}/users/me`,
    verify: `${API_BASE}/auth/verify`,
  },
  // Goals Service
  goals: {
    list: `${API_BASE}/goals`,
    create: `${API_BASE}/goals`,
    detail: (id: string) => `${API_BASE}/goals/${id}`,
    update: (id: string) => `${API_BASE}/goals/${id}`,
    delete: (id: string) => `${API_BASE}/goals/${id}`,
  },
  // Entries Service
  entries: {
    list: `${API_BASE}/entries`,
    create: `${API_BASE}/entries`,
    detail: (id: string) => `${API_BASE}/entries/${id}`,
    update: (id: string) => `${API_BASE}/entries/${id}`,
    delete: (id: string) => `${API_BASE}/entries/${id}`,
    byGoal: (goalId: string) => `${API_BASE}/goals/${goalId}/entries`,
  },
  // PDF Service
  pdf: {
    goalReport: (goalId: string) => `${API_BASE}/pdf/goal/${goalId}`,
    fullReport: `${API_BASE}/pdf/report`,
  },
  // Mailer Service
  mailer: {
    emailSettings: (goalId: string) => `${API_BASE}/mail/settings/${goalId}`,
    saveSettings: `${API_BASE}/mail/settings`,
  },
};
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
