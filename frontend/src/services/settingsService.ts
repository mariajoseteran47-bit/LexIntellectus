import api from '@/lib/api';

export interface TenantInfo {
    id: string;
    nombre: string;
    razon_social?: string;
    ruc?: string;
    email?: string;
    telefono?: string;
    direccion?: string;
    ciudad?: string;
    departamento?: string;
    config_json?: Record<string, any>;
}

export interface TenantUpdateDto {
    nombre?: string;
    ruc?: string;
    email?: string;
    telefono?: string;
    direccion?: string;
}

export interface ProfileUpdateDto {
    nombre?: string;
    apellido?: string;
}

export const settingsService = {
    // ── Tenant Management ──────────────────────────

    async getTenant(): Promise<TenantInfo> {
        const { data } = await api.get<TenantInfo>('/tenants/current');
        return data;
    },

    async updateTenant(updates: TenantUpdateDto): Promise<TenantInfo> {
        const { data } = await api.patch<TenantInfo>('/tenants/current', updates);
        return data;
    },

    // ── User Profile ───────────────────────────────

    async updateProfile(updates: ProfileUpdateDto): Promise<any> {
        // Try to get user ID from localStorage
        const stored = localStorage.getItem('user');
        if (!stored) throw new Error('No user session');
        const user = JSON.parse(stored);
        const { data } = await api.patch(`/users/${user.id}`, updates);
        return data;
    },

    // ── Security / Password ────────────────────────

    async changePassword(currentPassword: string, newPassword: string): Promise<void> {
        await api.post('/auth/change-password', {
            current_password: currentPassword,
            new_password: newPassword,
        });
    },
};
