import { API_MAILER_URL } from './api-config';

export interface EmailSettings {
  mail_id: string;
  related_goal_id: string;
  owner_user_id: string;
  recipient: string;
  enabled: boolean;
  sent_when: number;
  last_sent_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface EmailSettingsCreate {
  goal_id: string;
  recipient_email: string;
  enabled: boolean;
  send_day: number;
}

export interface EmailSettingsUpdate {
  recipient_email?: string;
  enabled?: boolean;
  send_day?: number;
}

export interface SendNowRequest {
  goal_id: string;
}

export interface SendMailResponse {
  mail_id: string;
  status: string;
  message: string;
  sent_at: string | null;
}

export const MailerAPI = {
  /**
   * Get email settings for a goal
   */
  async getEmailSettings(goalId: string, token: string): Promise<EmailSettings> {
    const response = await fetch(`${API_MAILER_URL}/mail/settings/${goalId}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Email settings not configured for this goal');
      }
      const error = await response.json().catch(() => ({ detail: 'Failed to fetch email settings' }));
      throw new Error(error.detail || 'Failed to fetch email settings');
    }

    return response.json();
  },

  /**
   * Create or update email settings for a goal
   */
  async saveEmailSettings(data: EmailSettingsCreate, token: string): Promise<EmailSettings> {
    const response = await fetch(`${API_MAILER_URL}/mail/settings`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to save email settings' }));
      throw new Error(error.detail || 'Failed to save email settings');
    }

    return response.json();
  },

  /**
   * Update email settings for a goal
   */
  async updateEmailSettings(goalId: string, data: EmailSettingsUpdate, token: string): Promise<EmailSettings> {
    const response = await fetch(`${API_MAILER_URL}/mail/settings/${goalId}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to update email settings' }));
      throw new Error(error.detail || 'Failed to update email settings');
    }

    return response.json();
  },

  /**
   * Delete email settings for a goal
   */
  async deleteEmailSettings(goalId: string, token: string): Promise<void> {
    const response = await fetch(`${API_MAILER_URL}/mail/settings/${goalId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok && response.status !== 404) {
      const error = await response.json().catch(() => ({ detail: 'Failed to delete email settings' }));
      throw new Error(error.detail || 'Failed to delete email settings');
    }
  },

  /**
   * Send monthly report email immediately
   */
  async sendNow(goalId: string, token: string): Promise<SendMailResponse> {
    const response = await fetch(`${API_MAILER_URL}/mail/send-now`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ goal_id: goalId }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to send email' }));
      throw new Error(error.detail || 'Failed to send email');
    }

    return response.json();
  },
};
