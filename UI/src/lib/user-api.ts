/**
 * User Service API Client
 */

import { API_ENDPOINTS, getAuthHeaders } from '@/lib/api-config';
import { User } from '@/types/goal';

// Backend response type
interface BackendUserResponse {
  google_sub: string;
  google_email: string;
  full_name: string;
  address: string | null;
  country: string | null;
  phone: string | null;
  currency: string | null;
  timezone: string | null;
  created_at: string;
  updated_at: string;
}

// Transform backend response to frontend User model
function transformUserResponse(backendUser: BackendUserResponse): User {
  return {
    id: backendUser.google_sub,
    name: backendUser.full_name,
    email: backendUser.google_email,
    avatar: `https://api.dicebear.com/7.x/avataaars/svg?seed=${backendUser.full_name}`,
    timezone: backendUser.timezone || 'America/New_York',
    currency: backendUser.currency || 'USD',
    address: backendUser.address || '',
    country: backendUser.country || '',
    phone: backendUser.phone || ''
  };
}

export class UserAPI {
  /**
   * Fetch current user profile
   */
  static async getProfile(token?: string): Promise<User> {
    const response = await fetch(API_ENDPOINTS.user.profile, {
      method: 'GET',
      headers: getAuthHeaders(token),
    });

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('Unauthorized: Please login again');
      }
      throw new Error(`Failed to fetch user profile: ${response.statusText}`);
    }

    const backendUser: BackendUserResponse = await response.json();
    return transformUserResponse(backendUser);
  }

  /**
   * Update user profile
   */
  static async updateProfile(data: Partial<User>, token?: string): Promise<User> {
    // Transform frontend data to backend format
    const backendData: any = {};
    if (data.name !== undefined) {
      backendData.full_name = data.name;
    }
    if (data.address !== undefined) backendData.address = data.address;
    if (data.country !== undefined) backendData.country = data.country;
    if (data.phone !== undefined) backendData.phone = data.phone;
    if (data.currency !== undefined) backendData.currency = data.currency;
    if (data.timezone !== undefined) backendData.timezone = data.timezone;

    const response = await fetch(API_ENDPOINTS.user.updateProfile, {
      method: 'PUT',
      headers: getAuthHeaders(token),
      body: JSON.stringify(backendData),
    });

    if (!response.ok) {
      throw new Error(`Failed to update user profile: ${response.statusText}`);
    }

    const backendUser: BackendUserResponse = await response.json();
    return transformUserResponse(backendUser);
  }

  /**
   * Verify JWT token
   */
  static async verifyToken(token?: string): Promise<{ valid: boolean; user_id: string }> {
    const response = await fetch(API_ENDPOINTS.user.verify, {
      method: 'GET',
      headers: getAuthHeaders(token),
    });

    if (!response.ok) {
      throw new Error('Token verification failed');
    }

    return response.json();
  }
}
