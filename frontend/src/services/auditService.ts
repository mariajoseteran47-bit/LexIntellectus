import api from '@/lib/api';

export interface AuditLogEntry {
    id: string;
    user_id: string | null;
    accion: string;
    entidad: string;
    entidad_id: string | null;
    datos_antes?: Record<string, any> | null;
    datos_despues?: Record<string, any> | null;
    detalles?: Record<string, any> | null; // Computed from datos_despues or datos_antes
    ip_address?: string | null;
    created_at: string | null;
}

export interface AuditLogListResponse {
    items: AuditLogEntry[];
    total: number;
    page: number;
    size: number;
}

export interface AuditFilterParams {
    page?: number;
    size?: number;
    accion?: string;
    entidad?: string;
    user_id?: string;
    start_date?: string;
    end_date?: string;
}

export const auditService = {
    async getAll(params: AuditFilterParams = {}): Promise<AuditLogListResponse> {
        const { data } = await api.get<AuditLogListResponse>('/audit/logs', { params });
        // Enrich items with a computed 'detalles' field for the UI
        data.items = data.items.map(item => ({
            ...item,
            detalles: item.datos_despues || item.datos_antes || null,
        }));
        return data;
    },

    async getByModule(module: string, page = 1, size = 20): Promise<AuditLogListResponse> {
        const { data } = await api.get<AuditLogListResponse>('/audit/logs', {
            params: { entidad: module, page, size }
        });
        return data;
    },
};
