import api from '@/lib/api';

export interface User {
    id: string;
    email: string;
    nombre: string;
    apellido: string;
    telefono?: string;
    tipo_usuario: 'admin_sistema' | 'admin_despacho' | 'abogado' | 'notario' | 'secretaria' | 'contador' | 'gestor' | 'cliente';
    tipo_vinculo: 'indefinido' | 'determinado' | 'servicios' | 'socio' | 'pasantia';
    is_active: boolean;
    tenant_id: string;
    sede_id?: string;
    created_at: string;
}

export interface UserListResponse {
    items: User[];
    total: number;
    page: number;
    size: number;
}

export interface CreateUserDto {
    email: string;
    password: string;
    nombre: string;
    apellido: string;
    telefono?: string;
    tipo_usuario: string;
    tipo_vinculo: string;
    sede_id?: string;
}

export const userService = {
    async getAll(page = 1, size = 20, search = '', role = ''): Promise<UserListResponse> {
        const params: any = { page, size };
        if (search) params.search = search;
        if (role) params.role = role;
        const { data } = await api.get<UserListResponse>('/users', { params });
        return data;
    },

    async create(userData: CreateUserDto): Promise<User> {
        const { data } = await api.post<User>('/users', userData);
        return data;
    },

    async update(id: string, userData: Partial<CreateUserDto>): Promise<User> {
        const { data } = await api.patch<User>(`/users/${id}`, userData);
        return data;
    },

    async delete(id: string): Promise<void> {
        // API doesn't have delete yet based on review, but for completeness or future
        // await api.delete(`/users/${id}`);
    }
};
