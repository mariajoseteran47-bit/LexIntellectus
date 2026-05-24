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

export interface ChatResponse {
    [key: string]: any; 
}

export const aiService = {
    chat: async (data: ChatRequest) => {
        const { message, mode, session_id, expediente_id } = data;
        const response = await api.post<ChatResponse>('/ai/chat', { message, mode, session_id, expediente_id });
        return response.data;
    },

    getHistory: async (sessionId: string) => {
        const response = await api.get(`/ai/history/${sessionId}`);
        return response.data;
    },

    getStats: async () => {
        const response = await api.get('/ai/stats');
        return response.data;
    },

    ingestDocument: async (file: File, sourceType: string = 'ley', titulo: string = '') => {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('source_type', sourceType);
        if (titulo) formData.append('titulo', titulo);

        const response = await api.post('/ai/ingest', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },

    getSuggestions: async (expedienteId: string) => {
        const response = await api.get(`/ai/suggestions/${expedienteId}`);
        return response.data;
    }
};
