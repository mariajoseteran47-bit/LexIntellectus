import api from '@/lib/api';
import { Expediente, ExpedienteListResponse, ParteProcesal } from '@/types/case';

export interface CaseFilterParams {
    page?: number;
    size?: number;
    search?: string;
    ramo?: string;
    estado_id?: string;
}

export const caseService = {
    // List cases with pagination and filters
    async getAll(params: CaseFilterParams = {}): Promise<ExpedienteListResponse> {
        const { data } = await api.get<ExpedienteListResponse>('/cases/', { params });
        return data;
    },

    // Get single case by ID
    async getById(id: string): Promise<Expediente> {
        const { data } = await api.get<Expediente>(`/cases/${id}`);
        return data;
    },

    // Create new case
    async create(caseData: Partial<Expediente>): Promise<Expediente> {
        const { data } = await api.post<Expediente>('/cases/', caseData);
        return data;
    },

    // Update case
    async update(id: string, caseData: Partial<Expediente>): Promise<Expediente> {
        const { data } = await api.patch<Expediente>(`/cases/${id}`, caseData);
        return data;
    },

    // Add party to case
    async addParty(caseId: string, partyData: Partial<ParteProcesal>): Promise<ParteProcesal> {
        const { data } = await api.post<ParteProcesal>(`/cases/${caseId}/partes`, partyData);
        return data;
    }
};
