// API service for AgriGuard backend communication
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export interface ImageFormatInfo {
  format?: string;
  mode?: string;
  width?: number;
  height?: number;
}

export interface ImageValidationResult {
  hash: string;
  not_empty: boolean;
  format_valid: boolean;
  format_info?: ImageFormatInfo;
  not_corrupted: boolean;
  visual_corruption: boolean;
  errors: string[];
  warnings: string[];
}

export interface PipelineReport {
  image_path?: string | null;
  prediction?: string | null;
  prob_healthy?: number | null;
  prob_diseased?: number | null;
  severity?: string | null;
  recommendations?: string[];
  shap_heatmap?: string | null;
  summary?: string | null;
}

export interface PipelineResult {
  upload_id?: string | null;
  stored_image_path?: string | null;
  image_path?: string | null;
  pred_class?: string | null;
  prob_healthy?: number | null;
  prob_diseased?: number | null;
  severity?: string | null;
  recommendations?: string[];
  summary?: string | null;
  prompt?: string | null;
  report_path?: string | null;
  report?: PipelineReport | null;
  prediction_breakdown?: Record<string, unknown> | null;
  shap_heatmap_path?: string | null;
  shap_heatmap_base64?: string | null;
  shap_method?: string | null;
  shap_note?: string | null;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface ChatInitResponse {
  session_id: string;
  initial_message: string;
  status: string;
}

export interface ChatMessageResponse {
  response: string;
  session_id: string;
  message_count: number;
}

export interface ChatHistoryResponse {
  session_id: string;
  history: ChatMessage[];
}

class AgriGuardAPI {
  // Validate uploaded image for corruption and security
  async validateImage(file: File): Promise<ImageValidationResult> {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE_URL}/validate-image`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (error) {
      console.error('Error validating image:', error);
      throw new Error('Failed to validate image. Please try again.');
    }
  }
  async initializeChat(analysisContext: PipelineResult): Promise<ChatInitResponse> {
    const response = await fetch(`${API_BASE_URL}/chat/init`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ analysis_context: analysisContext })
    });

    if (!response.ok) {
      throw new Error(`Chat initialization failed: ${response.statusText}`);
    }

    return response.json();
  }

  async sendChatMessage(sessionId: string, message: string): Promise<ChatMessageResponse> {
    const response = await fetch(`${API_BASE_URL}/chat/${sessionId}/message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    });

    if (!response.ok) {
      throw new Error(`Failed to send message: ${response.statusText}`);
    }

    return response.json();
  }

  async getChatHistory(sessionId: string): Promise<ChatHistoryResponse> {
    const response = await fetch(`${API_BASE_URL}/chat/history`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId })
    });

    if (!response.ok) {
      throw new Error(`Failed to get chat history: ${response.statusText}`);
    }

    return response.json();
  }

  async clearChatSession(sessionId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/chat/${sessionId}`, {
      method: 'DELETE'
    });

    if (!response.ok) {
      throw new Error(`Failed to clear chat session: ${response.statusText}`);
    }
  }

  // Run the complete disease analysis pipeline powered by backend_main
  async analyzeImage(file: File): Promise<PipelineResult> {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE_URL}/analyze`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      return result.result as PipelineResult;
    } catch (error) {
      console.error('Error running pipeline:', error);
      throw new Error('Failed to analyze image. Please try again.');
    }
  }

  // Check if backend is available
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/health`, {
        method: 'GET',
        timeout: 5000,
      } as RequestInit);
      return response.ok;
    } catch (error) {
      console.warn('Backend health check failed:', error);
      return false;
    }
  }
}

// Export singleton instance
export const agriGuardAPI = new AgriGuardAPI();

// Helper function to format file size
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// Helper function to get file type
export const getFileType = (file: File): string => {
  return file.type.split('/')[1]?.toUpperCase() || 'Unknown';
};