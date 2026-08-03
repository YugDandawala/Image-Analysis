/**
 * API Client — Backend communication service.
 * Handles image upload, chat SSE streaming, and status polling.
 */

const API_BASE = 'http://localhost:8000/api';

/**
 * Upload an image to the backend.
 * @param {File} file - The image file to upload.
 * @param {string} prompt - Optional initial prompt.
 * @returns {Promise<{session_id: string, thumbnail_url: string, original_filename: string}>}
 */
export async function uploadImage(file, prompt = '') {
  const formData = new FormData();
  formData.append('file', file);
  if (prompt) {
    formData.append('prompt', prompt);
  }

  const response = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Upload failed');
  }

  return response.json();
}

/**
 * Send a chat message and receive streaming SSE response.
 * @param {string} sessionId - Active session ID.
 * @param {string} message - User's message.
 * @param {function} onStage - Callback for stage updates.
 * @param {function} onToken - Callback for response tokens.
 * @param {function} onDone - Callback when streaming is complete.
 * @param {function} onError - Callback for errors.
 */
export async function sendMessage(sessionId, message, { onStage, onToken, onDone, onError }) {
  try {
    const response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, message }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Chat request failed');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));

            switch (data.type) {
              case 'stage':
                onStage?.(data.stage);
                break;
              case 'token':
                onToken?.(data.content);
                break;
              case 'done':
                onDone?.(data.category);
                break;
              case 'result':
                // Pipeline metadata result event
                break;
              case 'error':
                onError?.(data.message);
                break;
            }
          } catch (e) {
            // Skip malformed SSE events
          }
        }
      }
    }
  } catch (err) {
    onError?.(err.message);
  }
}

/**
 * Get pipeline processing status for a session.
 * @param {string} sessionId
 * @returns {Promise<{current_stage: string, completed_stages: string[], is_complete: boolean}>}
 */
export async function getStatus(sessionId) {
  const response = await fetch(`${API_BASE}/chat/${sessionId}/status`);
  if (!response.ok) throw new Error('Status check failed');
  return response.json();
}

/**
 * Health check.
 * @returns {Promise<{status: string, pipeline_ready: boolean}>}
 */
export async function checkHealth() {
  const response = await fetch(`${API_BASE}/health`);
  if (!response.ok) throw new Error('Health check failed');
  return response.json();
}
