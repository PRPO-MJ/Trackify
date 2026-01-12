/**
 * Goals Service API Client
 */

import { API_ENDPOINTS, getAuthHeaders } from '@/lib/api-config';
import { Goal } from '@/types/goal';

export interface CreateGoalRequest {
  name: string;
  description: string;
  targetHours: number;
  hourlyRate: number;
  endDate: string;
}

// Backend response type
interface BackendGoalResponse {
  goal_id: string;
  owner_user_id: string;
  title: string;
  target_hours: number | null;
  start_date: string | null;
  end_date: string | null;
  hourly_rate: number | null;
  description: string | null;
  created_at: string;
  updated_at: string;
}

// Transform backend response to frontend Goal model
function transformGoalResponse(backendGoal: BackendGoalResponse): Goal {
  return {
    id: backendGoal.goal_id,
    name: backendGoal.title,
    description: backendGoal.description || '',
    targetHours: backendGoal.target_hours || 0,
    completedHours: 0, // Will be updated from entries
    hourlyRate: backendGoal.hourly_rate || 0,
    currency: 'USD',
    startDate: backendGoal.start_date || '',
    endDate: backendGoal.end_date || '',
    workEntries: [],
    emailSettings: {
      enabled: false,
      recipients: [],
      subject: '',
      body: '',
      dayOfMonth: 1
    },
    createdAt: backendGoal.created_at,
    updatedAt: backendGoal.updated_at
  };
}

export interface GoalListResponse {
  goals: Goal[];
  total: number;
  skip: number;
  limit: number;
}

interface BackendGoalListResponse {
  goals: BackendGoalResponse[];
  total: number;
  page: number;
  page_size: number;
}

export class GoalsAPI {
  /**
   * Fetch all goals for current user
   */
  static async listGoals(skip: number = 0, limit: number = 50, token?: string): Promise<GoalListResponse> {
    const page = Math.floor(skip / limit) + 1;
    const url = new URL(API_ENDPOINTS.goals.list);
    url.searchParams.append('page', page.toString());
    url.searchParams.append('page_size', limit.toString());

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: getAuthHeaders(token),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch goals: ${response.statusText}`);
    }

    const backendData: BackendGoalListResponse = await response.json();
    
    return {
      goals: backendData.goals.map(transformGoalResponse),
      total: backendData.total,
      skip: (backendData.page - 1) * backendData.page_size,
      limit: backendData.page_size
    };
  }

  /**
   * Fetch a specific goal by ID
   */
  static async getGoal(id: string, token?: string): Promise<Goal> {
    const response = await fetch(API_ENDPOINTS.goals.detail(id), {
      method: 'GET',
      headers: getAuthHeaders(token),
    });

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Goal not found');
      }
      throw new Error(`Failed to fetch goal: ${response.statusText}`);
    }

    const backendGoal: BackendGoalResponse = await response.json();
    return transformGoalResponse(backendGoal);
  }

  /**
   * Create a new goal
   */
  static async createGoal(data: CreateGoalRequest, token?: string): Promise<Goal> {
    // Transform frontend request to backend format
    const backendData = {
      title: data.name,
      description: data.description,
      target_hours: data.targetHours,
      hourly_rate: data.hourlyRate,
      end_date: data.endDate,
      start_date: new Date().toISOString().split('T')[0]
    };

    console.log('[GoalsAPI] Creating goal:', {
      url: API_ENDPOINTS.goals.create,
      method: 'POST',
      headers: getAuthHeaders(token),
      body: backendData
    });

    const response = await fetch(API_ENDPOINTS.goals.create, {
      method: 'POST',
      headers: getAuthHeaders(token),
      body: JSON.stringify(backendData),
    });

    console.log('[GoalsAPI] Response status:', response.status, response.statusText);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('[GoalsAPI] Error response:', errorText);
      throw new Error(`Failed to create goal: ${response.statusText} - ${errorText}`);
    }

    const backendGoal: BackendGoalResponse = await response.json();
    console.log('[GoalsAPI] Created goal:', backendGoal);
    return transformGoalResponse(backendGoal);
  }

  /**
   * Update an existing goal
   */
  static async updateGoal(id: string, data: Partial<Goal>, token?: string): Promise<Goal> {
    // Transform frontend data to backend format
    const backendData: any = {};
    if (data.name !== undefined) backendData.title = data.name;
    if (data.description !== undefined) backendData.description = data.description;
    if (data.targetHours !== undefined) backendData.target_hours = data.targetHours;
    if (data.hourlyRate !== undefined) backendData.hourly_rate = data.hourlyRate;
    if (data.startDate !== undefined) backendData.start_date = data.startDate;
    if (data.endDate !== undefined) backendData.end_date = data.endDate;

    const response = await fetch(API_ENDPOINTS.goals.update(id), {
      method: 'PUT',
      headers: getAuthHeaders(token),
      body: JSON.stringify(backendData),
    });

    if (!response.ok) {
      throw new Error(`Failed to update goal: ${response.statusText}`);
    }

    const backendGoal: BackendGoalResponse = await response.json();
    return transformGoalResponse(backendGoal);
  }

  /**
   * Delete a goal
   */
  static async deleteGoal(id: string, token?: string): Promise<void> {
    const response = await fetch(API_ENDPOINTS.goals.delete(id), {
      method: 'DELETE',
      headers: getAuthHeaders(token),
    });

    if (!response.ok) {
      throw new Error(`Failed to delete goal: ${response.statusText}`);
    }
  }
}
