import api from '@/lib/api';

export interface Deadline {
    id: string;
    expediente_id: string;
    descripcion: string;
    tipo_plazo: 'procesal' | 'contractual' | 'administrativo';
    fecha_inicio?: string;
    fecha_vencimiento: string;
    hora_vencimiento?: string;
    dias_tipo: 'habiles' | 'calendario';
    base_legal?: string;
    usuario_responsable_id?: string;
    status: 'pendiente' | 'cumplido' | 'vencido' | 'cancelado';
    prioridad: 'normal' | 'alta' | 'critica';
    created_at: string;
}

export interface CreateDeadlineDto {
    expediente_id: string;
    descripcion: string;
    tipo_plazo: string;
    fecha_vencimiento: string;
    hora_vencimiento?: string;
    dias_tipo?: string;
    prioridad?: string;
    base_legal?: string;
}

export const deadlineService = {
    async getByCaseId(caseId: string): Promise<Deadline[]> {
        const { data } = await api.get<{ items: Deadline[] }>('/deadlines', {
            params: { expediente_id: caseId, size: 100 }
        });
        return data.items;
    },

    async getAll(params: any = {}): Promise<Deadline[]> {
        const { data } = await api.get<{ items: Deadline[] }>('/deadlines', {
            params: { ...params, size: 100 }
        });
        return data.items;
    },

    async create(deadline: CreateDeadlineDto): Promise<Deadline> {
        const { data } = await api.post<Deadline>('/deadlines/', deadline);
        return data;
    },

    async update(id: string, deadline: Partial<CreateDeadlineDto>): Promise<Deadline> {
        const { data } = await api.patch<Deadline>(`/deadlines/${id}`, deadline);
        return data;
    },

    async delete(id: string): Promise<void> {
        await api.delete(`/deadlines/${id}`);
    }
};
