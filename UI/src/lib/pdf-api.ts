/**
 * PDF Service API Client
 * Handles PDF generation and download functionality
 */

const PDF_SERVICE_URL = import.meta.env.VITE_PDF_SERVICE_URL || 'http://localhost:8010';

export const getAuthHeaders = (token?: string): HeadersInit => {
  const headers: HeadersInit = {};

  const authToken = token || localStorage.getItem('access_token');
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }

  return headers;
};

/**
 * Generate and download a PDF report for a specific goal
 * @param goalId - The UUID of the goal
 * @param token - Authentication token
 */
export const generateGoalPDF = async (goalId: string, token?: string): Promise<void> => {
  try {
    const response = await fetch(`${PDF_SERVICE_URL}/api/pdf/goal/${goalId}`, {
      method: 'GET',
      headers: getAuthHeaders(token),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Failed to generate PDF' }));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    // Get the blob from response
    const blob = await response.blob();
    
    // Extract filename from Content-Disposition header or use default
    const contentDisposition = response.headers.get('Content-Disposition');
    let filename = 'goal_report.pdf';
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="?(.+)"?/);
      if (filenameMatch) {
        filename = filenameMatch[1];
      }
    }

    // Create download link and trigger download
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    
    // Cleanup
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error('Error generating goal PDF:', error);
    throw error;
  }
};

/**
 * Generate and download a comprehensive report with all goals
 * @param token - Authentication token
 */
export const generateFullReport = async (token?: string): Promise<void> => {
  try {
    const response = await fetch(`${PDF_SERVICE_URL}/api/pdf/report`, {
      method: 'GET',
      headers: getAuthHeaders(token),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Failed to generate PDF' }));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    // Get the blob from response
    const blob = await response.blob();
    
    // Extract filename from Content-Disposition header or use default
    const contentDisposition = response.headers.get('Content-Disposition');
    let filename = 'trackify_report.pdf';
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="?(.+)"?/);
      if (filenameMatch) {
        filename = filenameMatch[1];
      }
    }

    // Create download link and trigger download
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    
    // Cleanup
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error('Error generating full report:', error);
    throw error;
  }
};
