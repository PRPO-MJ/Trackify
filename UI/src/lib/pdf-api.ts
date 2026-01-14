
import { API_ENDPOINTS, API_PDF_URL, getAuthHeaders } from './api-config';

/**
 * Generate and download a PDF report for a specific goal
 * @param goalId - The UUID of the goal
 * @param token - Authentication token
 */
export async function generateGoalPDF(goalId: string, token?: string): Promise<void> {
  const response = await fetch(API_ENDPOINTS.pdf.goalReport(goalId), {
    method: 'GET',
    headers: getAuthHeaders(token),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to generate PDF' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  const blob = await response.blob();
  const contentDisposition = response.headers.get('Content-Disposition');
  let filename = 'goal_report.pdf';
  if (contentDisposition) {
    const match = contentDisposition.match(/filename="?(.+)"?/);
    if (match) filename = match[1];
  }

  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}

/**
 * Generate and download a comprehensive report with all goals
 * @param token - Authentication token
 */
export async function generateFullReport(token?: string): Promise<void> {
  const response = await fetch(API_ENDPOINTS.pdf.fullReport, {
    method: 'GET',
    headers: getAuthHeaders(token),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to generate PDF' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  const blob = await response.blob();
  const contentDisposition = response.headers.get('Content-Disposition');
  let filename = 'trackify_report.pdf';
  if (contentDisposition) {
    const match = contentDisposition.match(/filename="?(.+)"?/);
    if (match) filename = match[1];
  }

  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}

// For object-style usage
export const PDFAPI = {
  generateGoalPDF,
  generateFullReport,
};
