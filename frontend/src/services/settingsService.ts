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

export interface ApiKeyItem {
    id: string;
    tenant_id: string;
    nombre: string;
    plataforma: string;
    key_prefix: string;
    scopes: string[];
    rate_limit_per_minute: number;
    activo: boolean;
    last_used_at?: string;
    expires_at?: string;
    created_at?: string;
    raw_key?: string;
}

export interface WebhookSubscriptionItem {
    id: string;
    tenant_id: string;
    nombre: string;
    url: string;
    events: string[];
    secret: string;
    activo: boolean;
    failure_count: number;
    last_triggered_at?: string;
    created_at?: string;
}

export interface WebhookDeliveryLogItem {
    id: string;
    subscription_id: string;
    event_type: string;
    payload: Record<string, any>;
    signature?: string;
    response_status?: number;
    response_body?: string;
    attempt_count: number;
    success: boolean;
    delivered_at?: string;
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

    // ── MFA ────────────────────────────────────────

    async setupMfa(): Promise<{ secret: string; qr_uri: string }> {
        const { data } = await api.get('/auth/mfa/setup');
        return data;
    },

    async verifyMfa(code: string): Promise<{ message: string }> {
        const { data } = await api.post('/auth/mfa/verify', { code });
        return data;
    },

    async disableMfa(code: string): Promise<{ message: string }> {
        const { data } = await api.post('/auth/mfa/disable', { code });
        return data;
    },

    // ── Public API Keys & Webhooks (Sprint 6) ──────

    async getIntegrationsCatalog(): Promise<{
        scopes: string[];
        webhook_events: string[];
        platforms: { id: string; name: string; category: string }[];
    }> {
        const { data } = await api.get('/integrations/catalog');
        return data;
    },

    async listApiKeys(): Promise<ApiKeyItem[]> {
        const { data } = await api.get<ApiKeyItem[]>('/integrations/api-keys');
        return data;
    },

    async createApiKey(payload: {
        nombre: string;
        plataforma: string;
        scopes: string[];
        rate_limit_per_minute?: number;
    }): Promise<ApiKeyItem> {
        const { data } = await api.post<ApiKeyItem>('/integrations/api-keys', payload);
        return data;
    },

    async revokeApiKey(keyId: string): Promise<void> {
        await api.delete(`/integrations/api-keys/${keyId}`);
    },

    async listWebhooks(): Promise<WebhookSubscriptionItem[]> {
        const { data } = await api.get<WebhookSubscriptionItem[]>('/integrations/webhooks');
        return data;
    },

    async createWebhook(payload: {
        nombre: string;
        url: string;
        events: string[];
    }): Promise<WebhookSubscriptionItem> {
        const { data } = await api.post<WebhookSubscriptionItem>('/integrations/webhooks', payload);
        return data;
    },

    async toggleWebhook(webhookId: string, activo: boolean): Promise<WebhookSubscriptionItem> {
        const { data } = await api.patch<WebhookSubscriptionItem>(`/integrations/webhooks/${webhookId}`, { activo });
        return data;
    },

    async deleteWebhook(webhookId: string): Promise<void> {
        await api.delete(`/integrations/webhooks/${webhookId}`);
    },

    async testWebhook(webhookId: string): Promise<WebhookDeliveryLogItem> {
        const { data } = await api.post<WebhookDeliveryLogItem>(`/integrations/webhooks/${webhookId}/test`);
        return data;
    },

    async getWebhookLogs(webhookId: string): Promise<WebhookDeliveryLogItem[]> {
        const { data } = await api.get<WebhookDeliveryLogItem[]>(`/integrations/webhooks/${webhookId}/logs`);
        return data;
    },
};
