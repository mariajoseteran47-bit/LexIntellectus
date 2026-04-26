import api from '@/lib/api';
import { Expediente, ExpedienteListResponse, ParteProcesal, CaseStatus, WorkflowStage } from '@/types/case';

export interface CaseFilterParams {
    page?: number;
    size?: number;
    search?: string;
    ramo?: string;
    tipo_servicio?: string;
    estado_id?: string;
}

export const caseService = {
    // List cases with pagination and filters
    async getAll(params: CaseFilterParams = {}): Promise<ExpedienteListResponse> {
        const { data } = await api.get<ExpedienteListResponse>('/cases', { params });
        return data;
    },

    // Get single case by ID
    async getById(id: string): Promise<Expediente> {
        const { data } = await api.get<Expediente>(`/cases/${id}`);
        return data;
    },

    // Create new case
    async create(caseData: Partial<Expediente>): Promise<Expediente> {
        const { data } = await api.post<Expediente>('/cases', caseData);
        return data;
    },

    // Update case
    async update(id: string, caseData: Partial<Expediente>): Promise<Expediente> {
        const { data } = await api.patch<Expediente>(`/cases/${id}`, caseData);
        return data;
    },

    // Change case status
    async changeStatus(id: string, estadoId: string): Promise<Expediente> {
        const { data } = await api.patch<Expediente>(`/cases/${id}/status`, { estado_id: estadoId });
        return data;
    },

    // Get configured statuses
    async getStatuses(): Promise<CaseStatus[]> {
        const { data } = await api.get<CaseStatus[]>('/cases/config/statuses');
        return data;
    },

    // Change case workflow stage
    async changeStage(id: string, etapaId: string): Promise<any> {
        const { data } = await api.patch(`/cases/${id}/stage`, { etapa_id: etapaId });
        return data;
    },

    // Get workflow stages by ramo, tipo_servicio, or process type
    async getStages(params: { ramo?: string; tipo_servicio?: string; tipo_proceso?: string }): Promise<WorkflowStage[]> {
        const { data } = await api.get<WorkflowStage[]>('/cases/workflow/stages', { params });
        return data;
    },

    // Add party to case
    async addParty(caseId: string, partyData: Partial<ParteProcesal>): Promise<ParteProcesal> {
        const { data } = await api.post<ParteProcesal>(`/cases/${caseId}/partes`, partyData);
        return data;
    }
};
