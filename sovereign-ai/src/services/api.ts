export interface UploadResponse {
  file_id: string;
  filename: string;
  mime_type: string;
  size: number;
  total_pages: number;
  status: string;
  has_images: boolean;
  timings?: {
    save_s: number;
    extraction_s: number;
    chunking_s: number;
    total_s: number;
  };
}

export interface SourceCitation {
  page: number;
  name: string;
  type: string;
  excerpt: string;
  relevance: string;
}

export interface InferenceTimings {
  is_cached: boolean;
  routing: string;
  model: string;
  extraction_s: number;
  ocr_s: number;
  image_render_s: number;
  context_s: number;
  time_to_first_token_s: number | null;
  llm_generation_s: number;
  total_s: number;
}

export interface VerificationData {
  is_verified: boolean;
  grounded: boolean;
  leak_count: number;
  unsupported_numbers?: number[];
  verified_numbers?: number[];
  unsupported_claims?: string[];
  unrelated_workflow_detected?: boolean;
  missing_info_properly_stated?: boolean;
  verification_label?: string;
  notes?: string;
}

export interface GeneratedDocumentFile {
  format: 'pdf' | 'docx';
  filename: string;
  download_url: string;
  size_bytes: number;
  size_formatted: string;
}

export interface GeneratedDocumentInfo {
  id: string;
  title: string;
  subtitle?: string;
  formats: string[];
  page_count: number;
  created_at: string;
  files: {
    pdf?: GeneratedDocumentFile;
    docx?: GeneratedDocumentFile;
  };
}

export interface ChatResponse {
  answer: string;
  sources: SourceCitation[];
  model: string;
  timings?: InferenceTimings;
  verification?: VerificationData;
  generated_document?: GeneratedDocumentInfo;
}

export interface NoteResponse {
  file_id: string;
  filename: string;
  note_markdown: string;
  model: string;
}

export interface ModelRegistryRecord {
  purpose: string;
  configured_model: string;
  active_model: string;
  is_available: boolean;
  is_mandatory: boolean;
  role_title: string;
  description: string;
  vram_gb: number;
  last_synced: string;
}

export interface SystemStatusResponse {
  ollama: boolean;
  model: string;
  vision_model?: string;
  document_model?: string;
  reasoning_model?: string;
  coder_model?: string;
  model_available: boolean;
  available_models: string[];
  model_registry?: ModelRegistryRecord[];
  external_calls: number;
  inference: string;
  network: string;
  gpu?: {
    name: string;
    vram: string;
    status: string;
  };
  message: string;
}

export interface AuthStatusResponse {
  has_users: boolean;
}

export interface LoginResponse {
  success: boolean;
  token?: string;
  user?: {
    id: number;
    username: string;
    display_name: string;
    created_at?: string;
  };
  error?: string;
}

const API_BASE = '/api';

// --- AUTHENTICATION API (Argon2id Local Only) ---

export async function getAuthStatus(): Promise<AuthStatusResponse> {
  const res = await fetch(`${API_BASE}/auth/status`);
  if (!res.ok) {
    return { has_users: true };
  }
  return res.json();
}

export async function loginUser(username: string, password: string): Promise<LoginResponse> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Incorrect username or password.' }));
    return {
      success: false,
      error: errorData.detail || 'Incorrect username or password.',
    };
  }

  return res.json();
}

export async function registerLocalAccount(
  username: string,
  password: string,
  displayName?: string
): Promise<{ success: boolean; message?: string; error?: string }> {
  const res = await fetch(`${API_BASE}/auth/setup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      username,
      password,
      display_name: displayName,
    }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Failed to create local account.' }));
    return {
      success: false,
      error: errorData.detail || 'Failed to create local account.',
    };
  }

  return res.json();
}

export async function logoutUser(token?: string): Promise<void> {
  try {
    await fetch(`${API_BASE}/auth/logout`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
  } catch {
    // Ignore network error on logout
  }
}

// --- DOCUMENT & CHAT API ---

export async function uploadDocument(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || 'Failed to upload document');
  }

  return res.json();
}

export async function sendChatMessageStream(
  message: string,
  fileId?: string | null,
  history: { role: string; content: string }[] = [],
  callbacks?: {
    onStage?: (stage: string, step: number, sources?: SourceCitation[]) => void;
    onToken?: (token: string) => void;
    onDone?: (data: {
      model: string;
      sources: SourceCitation[];
      timings?: InferenceTimings;
      verification?: VerificationData;
      generated_document?: GeneratedDocumentInfo;
    }) => void;
    onError?: (error: string) => void;
  }
): Promise<void> {
  const res = await fetch(`${API_BASE}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      file_id: fileId || null,
      history,
    }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    const errMsg = errorData.detail || 'Local inference engine error';
    if (callbacks?.onError) callbacks.onError(errMsg);
    throw new Error(errMsg);
  }

  if (!res.body) {
    throw new Error('ReadableStream not supported on this browser.');
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith('data: ')) {
          const jsonStr = trimmed.slice(6);
          try {
            const data = JSON.parse(jsonStr);
            if (data.event === 'stage' && callbacks?.onStage) {
              callbacks.onStage(data.stage, data.step, data.sources);
            } else if (data.event === 'token' && callbacks?.onToken) {
              callbacks.onToken(data.token);
            } else if (data.event === 'done' && callbacks?.onDone) {
              callbacks.onDone({
                model: data.model,
                sources: data.sources || [],
                timings: data.timings,
                verification: data.verification,
                generated_document: data.generated_document,
              });
            } else if (data.event === 'error') {
              if (callbacks?.onError) callbacks.onError(data.error);
              throw new Error(data.error);
            }
          } catch (e: any) {
            if (e.message && e.message.includes('Local inference engine')) {
              throw e;
            }
            // ignore mid-stream partial JSON chunk parse issues
          }
        }
      }
    }
  } catch (err: any) {
    if (callbacks?.onError) callbacks.onError(err.message || 'Stream processing error');
    throw err;
  }
}

export async function sendChatMessage(
  message: string,
  fileId?: string | null,
  history: { role: string; content: string }[] = []
): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      file_id: fileId || null,
      history,
    }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || 'Inference engine error');
  }

  return res.json();
}

export async function generateEngineeringNote(fileId: string): Promise<NoteResponse> {
  const res = await fetch(`${API_BASE}/generate-note`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ file_id: fileId }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || 'Failed to generate engineering note');
  }

  return res.json();
}

export async function getSystemStatus(): Promise<SystemStatusResponse> {
  const res = await fetch(`${API_BASE}/system/status`);
  if (!res.ok) {
    return {
      ollama: false,
      model: 'qwen2.5vl:3b',
      model_available: false,
      available_models: [],
      external_calls: 0,
      inference: 'local',
      network: 'Backend unreachable',
      message: 'Local backend service unreachable. Ensure FastAPI is running on port 8000.',
    };
  }
  return res.json();
}

export async function loadSampleDocument(): Promise<UploadResponse> {
  const res = await fetch(`${API_BASE}/documents/sample`);
  if (!res.ok) {
    throw new Error('Sample document not found on backend server.');
  }

  const blob = await res.blob();
  const sampleFile = new File([blob], 'Heat_Exchanger_E204_Inspection_Report.pdf', {
    type: 'application/pdf',
  });

  return uploadDocument(sampleFile);
}

export async function generateDocumentDirect(payload: {
  prompt?: string;
  file_id?: string;
  title?: string;
  formats?: string[];
  structure?: any;
}): Promise<GeneratedDocumentInfo> {
  const res = await fetch(`${API_BASE}/documents/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || 'Failed to generate document');
  }

  return res.json();
}

