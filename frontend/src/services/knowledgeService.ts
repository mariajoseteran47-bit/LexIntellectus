import api from '@/lib/api';

export interface LegalChunk {
    id: string;
    titulo: string;
    contenido: string;
    fuente: string;
    tipo_documento: string;
    tags?: string[];
    created_at: string;
}

export interface IngestionRequest {
    titulo: string;
    contenido: string;
    fuente: string;
    tipo_documento: string;
    tags?: string[];
}

export const knowledgeService = {
    /**
     * Search the legal knowledge base using AI.
     */
    async search(query: string, limit = 5): Promise<LegalChunk[]> {
        const { data } = await api.post<LegalChunk[]>('/ai/search', { query, limit });
        return data;
    },

    /**
     * Ingest a new legal document into the knowledge base.
     */
    async ingest(doc: IngestionRequest): Promise<{ message: string; chunk_count: number }> {
        const { data } = await api.post('/ai/ingest', doc);
        return data;
    },

    /**
     * List ingested documents.
     */
    async listDocuments(page = 1, size = 20): Promise<{ items: LegalChunk[]; total: number }> {
        const { data } = await api.get('/ai/documents', { params: { page, size } });
        return data;
    },
};
