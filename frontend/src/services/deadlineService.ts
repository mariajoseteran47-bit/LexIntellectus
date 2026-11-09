import api from '@/lib/api';

export interface Deadline {
    id: string;
    expediente_id: string;
    descripcion: string;
    tipo_plazo: 'procesal' | 'contractual' | 'administrativo' | 'registral' | 'notarial' | 'institucional';
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
    fecha_inicio?: string;
    fecha_vencimiento?: string;
    cantidad_dias?: number;
    municipio?: string;
    incluir_vacaciones_judiciales?: boolean;
    hora_vencimiento?: string;
    dias_tipo?: string;
    prioridad?: string;
    base_legal?: string;
}

export interface DeadlineCalculationRequest {
    fecha_inicio: string;
    cantidad_dias: number;
    dias_tipo: 'habiles' | 'calendario';
    municipio: string;
    incluir_vacaciones_judiciales: boolean;
}

export interface DeadlineCalculationResult {
    fecha_inicio: string;
    fecha_vencimiento: string;
    cantidad_dias: number;
    dias_tipo: string;
    municipio: string;
    incluir_vacaciones_judiciales: boolean;
    dias_computados: string[];
    dias_excluidos: { fecha: string; motivo: string }[];
    total_dias_calendario_transcurridos: number;
    base_legal_aplicada: string;
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
        const { data } = await api.post<Deadline>('/deadlines', deadline);
        return data;
    },

    async update(id: string, deadline: Partial<CreateDeadlineDto & { status: string }>): Promise<Deadline> {
        const { data } = await api.patch<Deadline>(`/deadlines/${id}`, deadline);
        return data;
    },

    async delete(id: string): Promise<void> {
        await api.delete(`/deadlines/${id}`);
    },

    async calculate(payload: DeadlineCalculationRequest): Promise<DeadlineCalculationResult> {
        const { data } = await api.post<DeadlineCalculationResult>('/deadlines/calculate', payload);
        return data;
    },

    async getHolidays(year: number, municipio: string = 'managua'): Promise<{ items: { fecha: string; motivo: string }[] }> {
        const { data } = await api.get('/deadlines/holidays', {
            params: { year, municipio }
        });
        return data;
    },

    getIcalUrl(): string {
        const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : '';
        return `/api/v1/deadlines/ical.ics?token=${token || ''}`;
    }
};
