import api from '@/lib/api';

export interface AgendaEvent {
    id: string;
    expediente_id: string;
    descripcion: string;
    tipo_plazo: string;
    fecha_inicio?: string;
    fecha_vencimiento: string;
    hora_vencimiento?: string;
    status: string;
    prioridad: string;
    base_legal?: string;
    usuario_responsable_id?: string;
    // Extra fields from join
    numero_causa?: string;
    numero_interno?: string;
    ramo?: string;
}

export interface AgendaFilterParams {
    desde?: string;
    hasta?: string;
    status?: string;
    prioridad?: string;
}

export const agendaService = {
    /**
     * Get deadlines as agenda events within a date range.
     * Uses the existing deadlines endpoint.
     */
    async getEvents(params: AgendaFilterParams = {}): Promise<AgendaEvent[]> {
        const { data } = await api.get<AgendaEvent[]>('/deadlines', { params });
        return data;
    },

    /**
     * Get upcoming deadlines for calendar view.
     * Uses the dashboard upcoming-deadlines endpoint.
     */
    async getUpcoming(limit = 30): Promise<AgendaEvent[]> {
        const { data } = await api.get<AgendaEvent[]>('/dashboard/upcoming-deadlines', {
            params: { limit, include_overdue: true }
        });
        return data;
    },

    /**
     * Update a deadline status (e.g., mark as completed).
     */
    async updateStatus(deadlineId: string, status: string): Promise<void> {
        await api.patch(`/deadlines/${deadlineId}`, { status });
    },
};
