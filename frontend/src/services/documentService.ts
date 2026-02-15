import api from '@/lib/api';

export interface Document {
    id: string;
    expediente_id: string;
    nombre_archivo: string;
    tipo_archivo: string;
    tamano_bytes: number;
    storage_path: string;
    descripcion?: string;
    categoria: string;
    created_at: string;
    subido_por_id: string;
    download_url?: string;
}

export interface UploadDocumentDto {
    expediente_id: string;
    file: File;
    descripcion?: string;
    categoria?: string;
}

export const documentService = {
    async getByCaseId(caseId: string): Promise<Document[]> {
        const { data } = await api.get<{ items: Document[] }>('/documents/', {
            params: { expediente_id: caseId }
        });
        return data.items;
    },

    async upload(doc: UploadDocumentDto): Promise<Document> {
        const formData = new FormData();
        formData.append('expediente_id', doc.expediente_id);
        formData.append('file', doc.file);
        if (doc.descripcion) formData.append('descripcion', doc.descripcion);
        if (doc.categoria) formData.append('categoria', doc.categoria);

        const { data } = await api.post<Document>('/documents/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return data;
    },

    async getDownloadUrl(id: string): Promise<string> {
        const { data } = await api.get<{ url: string }>(`/documents/${id}/download`);
        return data.url;
    },

    async delete(id: string): Promise<void> {
        await api.delete(`/documents/${id}`);
    }
};
