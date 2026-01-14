import { API_PDF_URL, getAuthHeaders } from './api-config';

export interface PDFGenerateResponse {
  filename: string;
  blob: Blob;
}

export const PDFAPI = {
  async generateGoalPDF(goalId: string, token?: string): Promise<PDFGenerateResponse> {
    const response = await fetch(`${API_PDF_URL}/pdf/goal/${goalId}`, {
      method: 'GET',
      headers: getAuthHeaders(token),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Failed to generate PDF' }));
      throw new Error(errorData.detail || `Failed to generate PDF: ${response.status}`);
    }

    const blob = await response.blob();
    const contentDisposition = response.headers.get('Content-Disposition');
    let filename = 'goal_report.pdf';
    if (contentDisposition) {
      const match = contentDisposition.match(/filename="?(.+)"?/);
      if (match) filename = match[1];
    }

    PDFAPI.downloadPDF({ filename, blob });

    return { filename, blob };
  },

 
  async generateFullReport(token?: string): Promise<PDFGenerateResponse> {
    const response = await fetch(`${API_PDF_URL}/pdf/full-report`, {
      method: 'GET',
      headers: getAuthHeaders(token),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Failed to generate PDF' }));
      throw new Error(errorData.detail || `Failed to generate PDF: ${response.status}`);
    }

    const blob = await response.blob();
    const contentDisposition = response.headers.get('Content-Disposition');
    let filename = 'trackify_report.pdf';
    if (contentDisposition) {
      const match = contentDisposition.match(/filename="?(.+)"?/);
      if (match) filename = match[1];
    }

    PDFAPI.downloadPDF({ filename, blob });

    return { filename, blob };
  },

  downloadPDF({ filename, blob }: PDFGenerateResponse) {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  },
};
