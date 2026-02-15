import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

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

export const aiService = {
    chat: async (data: ChatRequest) => {
        const response = await axios.post(`${API_URL}/ai/chat`, data);
        return response.data;
    },

    getHistory: async (sessionId: string) => {
        const response = await axios.get(`${API_URL}/ai/history/${sessionId}`);
        return response.data;
    },

    ingestDocument: async (file: File, sourceType: string = 'ley') => {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('source_type', sourceType);

        const response = await axios.post(`${API_URL}/ai/ingest`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    }
};
