import api from '@/lib/api';

export type AIMode = 'consultor' | 'estratega' | 'redactor' | 'cartulario';

export interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    metadata?: any;
}

export interface ChatRequest {
    message: string;
    mode: AIMode;
    session_id?: string;
    expediente_id?: string;
}

// Assuming ChatResponse is the type of the data returned by the chat endpoint
// This type was not provided in the original document, but is implied by the change.
export interface ChatResponse {
    // Define the structure of your chat response here
    // For example:
    // response: string;
    // session_id: string;
    // messages: ChatMessage[];
    [key: string]: any; // Placeholder if the exact structure is unknown
}

export const aiService = {
    chat: async (data: ChatRequest) => {
        // The original `data` parameter contains `message`, `mode`, `session_id`, `expediente_id`.
        // The change implies these properties should be passed as the request body.
        // Also, the response data is destructured directly.
        const { message, mode, session_id, expediente_id } = data;
        const response = await api.post<ChatResponse>('/ai/chat', { message, mode, session_id, expediente_id });
        return response.data;
    },

    getHistory: async (sessionId: string) => {
        const response = await api.get(`/ai/history/${sessionId}`);
        return response.data;
    },

    ingestDocument: async (file: File, sourceType: string = 'ley') => {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('source_type', sourceType);

        const response = await api.post('/ai/ingest', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    }
};
