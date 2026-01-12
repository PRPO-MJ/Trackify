/**
 * Entries Service API Client
 */

import { API_ENDPOINTS, getAuthHeaders } from '@/lib/api-config';
import { WorkEntry } from '@/types/goal';

export interface CreateEntryRequest {
  goal_id: string;
  date: string;
  startTime: string;
  endTime: string;
  description: string;
}

// Backend response type
interface BackendTimeEntryResponse {
  entry_id: string;
  owner_user_id: string;
  related_goal_id: string | null;
  work_date: string | null;
  start_time: string | null;
  end_time: string | null;
  minutes: number | null;
  description: string | null;
  created_at: string;
  updated_at: string;
}

// Transform backend response to frontend WorkEntry model
function transformEntryResponse(backendEntry: BackendTimeEntryResponse): WorkEntry {
  return {
    id: backendEntry.entry_id,
    date: backendEntry.work_date || backendEntry.created_at.split('T')[0], // Use work date, fallback to creation date
    startTime: backendEntry.start_time || '',
    endTime: backendEntry.end_time || '',
    minutes: Number(backendEntry.minutes) || 0,
    description: backendEntry.description || ''
  };
}

export interface EntryListResponse {
  entries: WorkEntry[];
  total: number;
  skip: number;
  limit: number;
}

interface BackendEntryListResponse {
  entries: BackendTimeEntryResponse[];
  total: number;
  page: number;
  page_size: number;
}

export class EntriesAPI {
  /**
   * Fetch all time entries
   */
  static async listEntries(
    skip: number = 0,
    limit: number = 50,
    token?: string,
    sortBy: 'minutes' | 'work_date' | 'start_time' = 'work_date',
    sortOrder: 'asc' | 'desc' = 'desc'
  ): Promise<EntryListResponse> {
    const page = Math.floor(skip / limit) + 1;
    const url = new URL(API_ENDPOINTS.entries.list);
    url.searchParams.append('page', page.toString());
    url.searchParams.append('page_size', limit.toString());
    url.searchParams.append('sort_by', sortBy);
    url.searchParams.append('sort_order', sortOrder);

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: getAuthHeaders(token),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch entries: ${response.statusText}`);
    }

    const backendData: BackendEntryListResponse = await response.json();
    
    return {
      entries: backendData.entries.map(transformEntryResponse),
      total: backendData.total,
      skip: (backendData.page - 1) * backendData.page_size,
      limit: backendData.page_size
    };
  }

  /**
   * Fetch entries for a specific goal
   */
  static async listGoalEntries(
    goalId: string,
    skip: number = 0,
    limit: number = 50,
    token?: string,
    sortBy: 'minutes' | 'work_date' | 'start_time' | 'end_time' | 'created_at' | 'updated_at' = 'work_date',
    sortOrder: 'asc' | 'desc' = 'desc'
  ): Promise<EntryListResponse> {
    const page = Math.floor(skip / limit) + 1;
    const url = new URL(API_ENDPOINTS.entries.list);
    url.searchParams.append('page', page.toString());
    url.searchParams.append('page_size', limit.toString());
    url.searchParams.append('goal_id', goalId);
    url.searchParams.append('sort_by', sortBy);
    url.searchParams.append('sort_order', sortOrder);

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: getAuthHeaders(token),
    });

    if (!response.ok) {
      let errorDetail = response.statusText;
      try {
        const errorData = await response.json();
        errorDetail = errorData.detail || errorDetail;
        console.error('Entries API error:', errorData);
      } catch {
        // Couldn't parse error response
      }
      throw new Error(`Failed to fetch goal entries: ${errorDetail}`);
    }

    const backendData: BackendEntryListResponse = await response.json();
    
    return {
      entries: backendData.entries.map(transformEntryResponse),
      total: backendData.total,
      skip: (backendData.page - 1) * backendData.page_size,
      limit: backendData.page_size
    };
  }

  /**
   * Fetch a specific entry by ID
   */
  static async getEntry(id: string, token?: string): Promise<WorkEntry> {
    const response = await fetch(API_ENDPOINTS.entries.detail(id), {
      method: 'GET',
      headers: getAuthHeaders(token),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch entry: ${response.statusText}`);
    }

    const backendEntry: BackendTimeEntryResponse = await response.json();
    return transformEntryResponse(backendEntry);
  }

  /**
   * Create a new time entry
   */
  static async createEntry(data: CreateEntryRequest, token?: string): Promise<WorkEntry> {
    // Transform frontend request to backend format
    const backendData = {
      related_goal_id: data.goal_id,
      work_date: data.date,
      start_time: data.startTime,
      end_time: data.endTime,
      description: data.description
    };

    console.log('[EntriesAPI] Creating entry with data:', data);
    console.log('[EntriesAPI] Sending to backend:', {
      url: API_ENDPOINTS.entries.create,
      method: 'POST',
      headers: getAuthHeaders(token),
      body: backendData
    });

    const response = await fetch(API_ENDPOINTS.entries.create, {
      method: 'POST',
      headers: getAuthHeaders(token),
      body: JSON.stringify(backendData),
    });

    console.log('[EntriesAPI] Response status:', response.status, response.statusText);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('[EntriesAPI] Error response:', errorText);
      throw new Error(`Failed to create entry: ${response.statusText} - ${errorText}`);
    }

    const backendEntry: BackendTimeEntryResponse = await response.json();
    console.log('[EntriesAPI] Created entry:', backendEntry);
    return transformEntryResponse(backendEntry);
  }

  /**
   * Update an existing entry
   */
  static async updateEntry(id: string, data: Partial<WorkEntry>, token?: string): Promise<WorkEntry> {
    // Transform frontend data to backend format
    const backendData: any = {};
    if (data.startTime !== undefined) backendData.start_time = data.startTime;
    if (data.endTime !== undefined) backendData.end_time = data.endTime;
    if (data.minutes !== undefined) backendData.minutes = data.minutes;
    if (data.description !== undefined) backendData.description = data.description;

    const response = await fetch(API_ENDPOINTS.entries.update(id), {
      method: 'PUT',
      headers: getAuthHeaders(token),
      body: JSON.stringify(backendData),
    });

    if (!response.ok) {
      throw new Error(`Failed to update entry: ${response.statusText}`);
    }

    const backendEntry: BackendTimeEntryResponse = await response.json();
    return transformEntryResponse(backendEntry);
  }

  /**
   * Delete an entry
   */
  static async deleteEntry(id: string, token?: string): Promise<void> {
    const response = await fetch(API_ENDPOINTS.entries.delete(id), {
      method: 'DELETE',
      headers: getAuthHeaders(token),
    });

    if (!response.ok) {
      throw new Error(`Failed to delete entry: ${response.statusText}`);
    }
  }
}
