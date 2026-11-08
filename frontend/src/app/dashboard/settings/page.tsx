'use client';

import { useState, useEffect } from 'react';
import {
    Building2, Users, Shield, MapPin, Save, Plus, X, Eye, EyeOff,
    Settings as SettingsIcon, ChevronRight, Palette, Bell, Lock,
    Key, Webhook, Copy, Check, Trash2, Send, Activity, RefreshCw
} from 'lucide-react';
import { useToast } from '@/components/ui/ToastProvider';
import {
    settingsService,
    ApiKeyItem,
    WebhookSubscriptionItem,
    WebhookDeliveryLogItem
} from '@/services/settingsService';
import MfaModal from '@/components/auth/MfaModal';

interface TenantData {
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

const DEFAULT_SCOPES = [
    'read:invoices',
    'write:invoices',
    'read:payments',
    'write:payments',
    'read:clients',
    'read:matters',
    'read:time_entries',
];

const DEFAULT_WEBHOOK_EVENTS = [
    'matter.created',
    'matter.status_changed',
    'matter.stage_changed',
    'matter.closed',
    'invoice.created',
    'invoice.paid',
    'invoice.overdue',
    'document.uploaded',
    'document.approved',
    'deadline.approaching',
    'deadline.expired',
    'client.created',
    'payment.received',
    'conflict.detected',
];

export default function SettingsPage() {
    const [activeSection, setActiveSection] = useState('despacho');
    const [tenantData, setTenantData] = useState<TenantData | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [user, setUser] = useState<any>(null);

    // Password change state
    const [showPasswordForm, setShowPasswordForm] = useState(false);
    const [passwordData, setPasswordData] = useState({ current: '', new_password: '', confirm: '' });
    const [showPasswords, setShowPasswords] = useState({ current: false, new_password: false, confirm: false });
    const [showMfaModal, setShowMfaModal] = useState(false);

    // Sprint 6: Public API Keys & Webhooks state
    const [apiKeys, setApiKeys] = useState<ApiKeyItem[]>([]);
    const [webhooks, setWebhooks] = useState<WebhookSubscriptionItem[]>([]);
    const [loadingIntegrations, setLoadingIntegrations] = useState(false);
    const [newlyCreatedKey, setNewlyCreatedKey] = useState<string | null>(null);
    const [copiedText, setCopiedText] = useState<string | null>(null);

    const [showNewKeyForm, setShowNewKeyForm] = useState(false);
    const [newKeyForm, setNewKeyForm] = useState({
        nombre: '',
        plataforma: 'quickbooks',
        scopes: ['read:invoices', 'write:invoices', 'read:clients', 'read:payments', 'write:payments'],
        rate_limit_per_minute: 60,
    });

    const [showNewWebhookForm, setShowNewWebhookForm] = useState(false);
    const [newWebhookForm, setNewWebhookForm] = useState({
        nombre: '',
        url: '',
        events: ['invoice.created', 'invoice.paid', 'payment.received'],
    });
    const [selectedWebhookLogs, setSelectedWebhookLogs] = useState<{
        webhookId: string;
        logs: WebhookDeliveryLogItem[];
    } | null>(null);

    const toast = useToast();

    useEffect(() => {
        const stored = localStorage.getItem('user');
        if (stored) setUser(JSON.parse(stored));
        fetchTenantData();
    }, []);

    useEffect(() => {
        if (activeSection === 'integraciones') {
            fetchIntegrationsData();
        }
    }, [activeSection]);

    const fetchTenantData = async () => {
        try {
            const data = await settingsService.getTenant();
            setTenantData(data as any);
        } catch (e) {
            console.error('Error fetching tenant', e);
        } finally {
            setLoading(false);
        }
    };

    const fetchIntegrationsData = async () => {
        setLoadingIntegrations(true);
        try {
            const [keysData, hooksData] = await Promise.all([
                settingsService.listApiKeys(),
                settingsService.listWebhooks(),
            ]);
            setApiKeys(keysData);
            setWebhooks(hooksData);
        } catch (e) {
            console.error('Error loading integrations', e);
        } finally {
            setLoadingIntegrations(false);
        }
    };

    const copyToClipboard = (text: string, label: string) => {
        navigator.clipboard.writeText(text);
        setCopiedText(text);
        toast.success('Copiado', `${label} copiado al portapapeles`);
        setTimeout(() => setCopiedText(null), 2000);
    };

    const handleCreateApiKey = async () => {
        if (!newKeyForm.nombre.trim()) {
            toast.error('Nombre requerido', 'Ingresa un nombre descriptivo para la API Key.');
            return;
        }
        if (newKeyForm.scopes.length === 0) {
            toast.error('Permisos requeridos', 'Selecciona al menos un scope.');
            return;
        }
        setSaving(true);
        try {
            const created = await settingsService.createApiKey(newKeyForm);
            setNewlyCreatedKey(created.raw_key || null);
            setApiKeys(prev => [created, ...prev]);
            setShowNewKeyForm(false);
            setNewKeyForm({
                nombre: '',
                plataforma: 'quickbooks',
                scopes: ['read:invoices', 'write:invoices', 'read:clients', 'read:payments', 'write:payments'],
                rate_limit_per_minute: 60,
            });
            toast.success('API Key generada', 'Copia tu clave secreta ahora; no se volverá a mostrar.');
        } catch (e: any) {
            toast.error('Error', e?.response?.data?.detail || 'No se pudo crear la API Key.');
        } finally {
            setSaving(false);
        }
    };

    const handleRevokeApiKey = async (keyId: string) => {
        try {
            await settingsService.revokeApiKey(keyId);
            setApiKeys(prev => prev.map(k => k.id === keyId ? { ...k, activo: false } : k));
            toast.success('API Key revocada', 'El acceso externo con esta clave ha sido desactivado.');
        } catch (e) {
            toast.error('Error', 'No se pudo revocar la API Key.');
        }
    };

    const handleCreateWebhook = async () => {
        if (!newWebhookForm.nombre.trim() || !newWebhookForm.url.trim()) {
            toast.error('Campos incompletos', 'Ingresa un nombre y URL de destino válida.');
            return;
        }
        if (newWebhookForm.events.length === 0) {
            toast.error('Eventos requeridos', 'Selecciona al menos un evento para suscribir.');
            return;
        }
        setSaving(true);
        try {
            const created = await settingsService.createWebhook(newWebhookForm);
            setWebhooks(prev => [created, ...prev]);
            setShowNewWebhookForm(false);
            setNewWebhookForm({
                nombre: '',
                url: '',
                events: ['invoice.created', 'invoice.paid', 'payment.received'],
            });
            toast.success('Webhook registrado', 'El endpoint recibirá eventos firmados con HMAC-SHA256.');
        } catch (e: any) {
            toast.error('Error', e?.response?.data?.detail || 'No se pudo registrar el webhook.');
        } finally {
            setSaving(false);
        }
    };

    const handleTestWebhook = async (webhookId: string) => {
        try {
            const log = await settingsService.testWebhook(webhookId);
            if (log.success) {
                toast.success('Ping exitoso', `Respuesta HTTP ${log.response_status} recibida.`);
            } else {
                toast.info('Ping enviado', `Intento registrado (Estado HTTP: ${log.response_status || 'Sin conexión'}).`);
            }
            const logs = await settingsService.getWebhookLogs(webhookId);
            setSelectedWebhookLogs({ webhookId, logs });
        } catch (e) {
            toast.error('Error', 'No se pudo enviar el evento de prueba.');
        }
    };

    const handleViewWebhookLogs = async (webhookId: string) => {
        try {
            const logs = await settingsService.getWebhookLogs(webhookId);
            setSelectedWebhookLogs({ webhookId, logs });
        } catch (e) {
            toast.error('Error', 'No se pudieron cargar los logs de entrega.');
        }
    };

    const handleDeleteWebhook = async (webhookId: string) => {
        try {
            await settingsService.deleteWebhook(webhookId);
            setWebhooks(prev => prev.filter(w => w.id !== webhookId));
            if (selectedWebhookLogs?.webhookId === webhookId) {
                setSelectedWebhookLogs(null);
            }
            toast.success('Webhook eliminado');
        } catch (e) {
            toast.error('Error', 'No se pudo eliminar el webhook.');
        }
    };

    const handleSaveTenant = async () => {
        if (!tenantData) return;
        setSaving(true);
        try {
            await settingsService.updateTenant({
                nombre: tenantData.nombre,
                email: tenantData.email,
                telefono: tenantData.telefono,
                direccion: tenantData.direccion,
            });
            toast.success('Datos guardados', 'La información del despacho se actualizó correctamente.');
        } catch (e) {
            toast.error('Error', 'No se pudieron guardar los cambios.');
        } finally {
            setSaving(false);
        }
    };

    const handleSaveProfile = async () => {
        if (!user) return;
        setSaving(true);
        try {
            await settingsService.updateProfile({
                nombre: user.nombre,
                apellido: user.apellido,
            });
            localStorage.setItem('user', JSON.stringify(user));
            toast.success('Perfil actualizado', 'Sus datos de perfil se guardaron correctamente.');
        } catch (e: any) {
            localStorage.setItem('user', JSON.stringify(user));
            toast.success('Perfil actualizado localmente', 'Los cambios se guardaron en su sesión.');
        } finally {
            setSaving(false);
        }
    };

    const handleChangePassword = async () => {
        if (passwordData.new_password !== passwordData.confirm) {
            toast.error('Las contraseñas no coinciden');
            return;
        }
        if (passwordData.new_password.length < 6) {
            toast.error('La contraseña debe tener al menos 6 caracteres');
            return;
        }
        setSaving(true);
        try {
            await settingsService.changePassword(passwordData.current, passwordData.new_password);
            toast.success('Contraseña actualizada', 'Su contraseña se cambió correctamente.');
            setShowPasswordForm(false);
            setPasswordData({ current: '', new_password: '', confirm: '' });
        } catch (e: any) {
            const detail = e?.response?.data?.detail || 'Contraseña actual incorrecta o error del servidor.';
            toast.error('Error', detail);
        } finally {
            setSaving(false);
        }
    };

    const sections = [
        { id: 'despacho', label: 'Datos del Despacho', icon: Building2, desc: 'Información general del bufete' },
        { id: 'perfil', label: 'Mi Perfil', icon: Users, desc: 'Datos personales y credenciales' },
        { id: 'seguridad', label: 'Seguridad', icon: Lock, desc: 'Contraseña, 2FA y sesiones' },
        { id: 'integraciones', label: 'Integraciones y API', icon: Webhook, desc: 'API Keys, ERPs y Webhooks' },
        { id: 'notificaciones', label: 'Notificaciones', icon: Bell, desc: 'Preferencias de alertas' },
        { id: 'apariencia', label: 'Apariencia', icon: Palette, desc: 'Tema y personalización' },
    ];

    const InputField = ({ label, value, onChange, placeholder, type = 'text', disabled = false }: any) => (
        <div>
            <label className="block text-sm font-medium text-surface-700 mb-1.5">{label}</label>
            <input
                type={type}
                value={value || ''}
                onChange={(e) => onChange(e.target.value)}
                placeholder={placeholder}
                disabled={disabled}
                className="w-full px-4 py-2.5 rounded-lg border border-surface-300 bg-white text-surface-800 placeholder:text-surface-400 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 disabled:bg-surface-50 disabled:text-surface-400"
            />
        </div>
    );

    const toggleScope = (scope: string) => {
        setNewKeyForm(prev => ({
            ...prev,
            scopes: prev.scopes.includes(scope)
                ? prev.scopes.filter(s => s !== scope)
                : [...prev.scopes, scope],
        }));
    };

    const toggleWebhookEvent = (ev: string) => {
        setNewWebhookForm(prev => ({
            ...prev,
            events: prev.events.includes(ev)
                ? prev.events.filter(e => e !== ev)
                : [...prev.events, ev],
        }));
    };

    return (
        <div className="animate-fade-in space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold text-surface-900 flex items-center gap-3">
                    <SettingsIcon className="w-6 h-6 text-primary-500" />
                    Configuración
                </h1>
                <p className="text-surface-500 text-sm mt-1">
                    Administra la configuración de tu despacho, perfil, seguridad e integraciones contables
                </p>
            </div>

            {/* Settings Layout */}
            <div className="flex flex-col lg:flex-row gap-6">
                {/* Sidebar Navigation */}
                <div className="lg:w-72 flex-shrink-0">
                    <div className="card overflow-hidden">
                        <nav className="divide-y divide-surface-100">
                            {sections.map((section) => (
                                <button
                                    key={section.id}
                                    onClick={() => setActiveSection(section.id)}
                                    className={`w-full flex items-center gap-3 px-5 py-4 text-left transition-all duration-200 ${
                                        activeSection === section.id
                                            ? 'bg-primary-50 text-primary-700 border-l-[3px] border-primary-500'
                                            : 'hover:bg-surface-50 text-surface-600'
                                    }`}
                                >
                                    <section.icon className={`w-5 h-5 flex-shrink-0 ${
                                        activeSection === section.id ? 'text-primary-500' : 'text-surface-400'
                                    }`} />
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm font-medium">{section.label}</p>
                                        <p className="text-xs text-surface-400 mt-0.5">{section.desc}</p>
                                    </div>
                                    <ChevronRight className={`w-4 h-4 flex-shrink-0 ${
                                        activeSection === section.id ? 'text-primary-400' : 'text-surface-300'
                                    }`} />
                                </button>
                            ))}
                        </nav>
                    </div>
                </div>

                {/* Content Area */}
                <div className="flex-1 min-w-0">
                    {/* Despacho Section */}
                    {activeSection === 'despacho' && (
                        <div className="card p-8 space-y-6">
                            <div className="flex items-center justify-between border-b border-surface-100 pb-4">
                                <div>
                                    <h2 className="text-lg font-bold text-surface-900">Datos del Despacho</h2>
                                    <p className="text-sm text-surface-500">Información general de tu bufete jurídico</p>
                                </div>
                                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center text-white text-lg font-bold shadow-lg">
                                    {tenantData?.nombre?.charAt(0) || 'D'}
                                </div>
                            </div>

                            {loading ? (
                                <div className="py-12 text-center text-surface-500">Cargando datos...</div>
                            ) : (
                                <>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                                        <InputField
                                            label="Nombre del Despacho"
                                            value={tenantData?.nombre}
                                            onChange={(v: string) => setTenantData(prev => prev ? { ...prev, nombre: v } : prev)}
                                            placeholder="Bufete Jurídico ABC"
                                        />
                                        <InputField
                                            label="RUC"
                                            value={tenantData?.ruc}
                                            onChange={(v: string) => setTenantData(prev => prev ? { ...prev, ruc: v } : prev)}
                                            placeholder="J0310000012345"
                                        />
                                        <InputField
                                            label="Email Corporativo"
                                            value={tenantData?.email}
                                            onChange={(v: string) => setTenantData(prev => prev ? { ...prev, email: v } : prev)}
                                            placeholder="contacto@bufete.com.ni"
                                            type="email"
                                        />
                                        <InputField
                                            label="Teléfono"
                                            value={tenantData?.telefono}
                                            onChange={(v: string) => setTenantData(prev => prev ? { ...prev, telefono: v } : prev)}
                                            placeholder="+505 2222-3333"
                                        />
                                    </div>
                                    <InputField
                                        label="Dirección"
                                        value={tenantData?.direccion}
                                        onChange={(v: string) => setTenantData(prev => prev ? { ...prev, direccion: v } : prev)}
                                        placeholder="Km 4.5 Carretera a Masaya, Managua"
                                    />

                                    <div className="flex justify-end pt-4 border-t border-surface-100">
                                        <button
                                            onClick={handleSaveTenant}
                                            disabled={saving}
                                            className="btn-primary flex items-center gap-2"
                                        >
                                            <Save className="w-4 h-4" />
                                            {saving ? 'Guardando...' : 'Guardar Cambios'}
                                        </button>
                                    </div>
                                </>
                            )}
                        </div>
                    )}

                    {/* Profile Section */}
                    {activeSection === 'perfil' && (
                        <div className="card p-8 space-y-6">
                            <div className="flex items-center justify-between border-b border-surface-100 pb-4">
                                <div>
                                    <h2 className="text-lg font-bold text-surface-900">Mi Perfil</h2>
                                    <p className="text-sm text-surface-500">Actualiza tus datos personales</p>
                                </div>
                                <div className="w-14 h-14 rounded-full bg-gradient-to-br from-primary-500 to-accent-400 flex items-center justify-center text-white text-lg font-bold shadow-lg">
                                    {user?.nombre?.charAt(0)}{user?.apellido?.charAt(0)}
                                </div>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                                <InputField
                                    label="Nombre"
                                    value={user?.nombre}
                                    onChange={(v: string) => setUser((prev: any) => prev ? { ...prev, nombre: v } : prev)}
                                />
                                <InputField
                                    label="Apellido"
                                    value={user?.apellido}
                                    onChange={(v: string) => setUser((prev: any) => prev ? { ...prev, apellido: v } : prev)}
                                />
                                <InputField
                                    label="Email"
                                    value={user?.email}
                                    disabled
                                />
                                <div>
                                    <label className="block text-sm font-medium text-surface-700 mb-1.5">Rol</label>
                                    <div className="px-4 py-2.5 rounded-lg border border-surface-200 bg-surface-50 text-surface-600 text-sm capitalize">
                                        {user?.tipo_usuario?.replace('_', ' ') || '—'}
                                    </div>
                                </div>
                            </div>

                            <div className="flex justify-end pt-4 border-t border-surface-100">
                                <button onClick={handleSaveProfile} disabled={saving} className="btn-primary flex items-center gap-2">
                                    <Save className="w-4 h-4" />
                                    {saving ? 'Guardando...' : 'Guardar Perfil'}
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Security Section */}
                    {activeSection === 'seguridad' && (
                        <div className="space-y-6">
                            <div className="card p-8 space-y-6">
                                <div className="border-b border-surface-100 pb-4">
                                    <h2 className="text-lg font-bold text-surface-900">Seguridad de la Cuenta</h2>
                                    <p className="text-sm text-surface-500">Gestiona tu contraseña y sesiones activas</p>
                                </div>

                                {/* Change Password */}
                                <div className="p-5 rounded-xl border border-surface-200 bg-surface-50/50 space-y-4">
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <h3 className="font-semibold text-surface-800">Cambiar Contraseña</h3>
                                            <p className="text-xs text-surface-500 mt-0.5">Se recomienda cambiarla cada 90 días</p>
                                        </div>
                                        {!showPasswordForm && (
                                            <button onClick={() => setShowPasswordForm(true)} className="btn-outline text-sm py-1.5 px-4">
                                                Cambiar
                                            </button>
                                        )}
                                    </div>

                                    {showPasswordForm && (
                                        <div className="space-y-4 pt-2">
                                            {(['current', 'new_password', 'confirm'] as const).map((field) => (
                                                <div key={field} className="relative">
                                                    <label className="block text-sm font-medium text-surface-700 mb-1.5">
                                                        {field === 'current' ? 'Contraseña Actual' :
                                                         field === 'new_password' ? 'Nueva Contraseña' : 'Confirmar Nueva Contraseña'}
                                                    </label>
                                                    <div className="relative">
                                                        <input
                                                            type={showPasswords[field] ? 'text' : 'password'}
                                                            value={passwordData[field]}
                                                            onChange={(e) => setPasswordData(prev => ({ ...prev, [field]: e.target.value }))}
                                                            className="w-full px-4 py-2.5 pr-10 rounded-lg border border-surface-300 bg-white focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
                                                        />
                                                        <button
                                                            onClick={() => setShowPasswords(prev => ({ ...prev, [field]: !prev[field] }))}
                                                            className="absolute right-3 top-1/2 -translate-y-1/2 text-surface-400 hover:text-surface-600"
                                                        >
                                                            {showPasswords[field] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                                        </button>
                                                    </div>
                                                </div>
                                            ))}
                                            <div className="flex gap-3 justify-end">
                                                <button
                                                    onClick={() => { setShowPasswordForm(false); setPasswordData({ current: '', new_password: '', confirm: '' }); }}
                                                    className="px-4 py-2 text-sm text-surface-600 hover:text-surface-800"
                                                >
                                                    Cancelar
                                                </button>
                                                <button
                                                    onClick={handleChangePassword}
                                                    disabled={saving}
                                                    className="btn-primary text-sm py-2"
                                                >
                                                    {saving ? 'Guardando...' : 'Guardar Contraseña'}
                                                </button>
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* Active Sessions */}
                                <div className="p-5 rounded-xl border border-surface-200 bg-surface-50/50">
                                    <h3 className="font-semibold text-surface-800 mb-3">Sesiones Activas</h3>
                                    <div className="space-y-3">
                                        <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-surface-200">
                                            <div className="flex items-center gap-3">
                                                <div className="w-8 h-8 rounded-lg bg-green-50 flex items-center justify-center">
                                                    <div className="w-2 h-2 rounded-full bg-green-500" />
                                                </div>
                                                <div>
                                                    <p className="text-sm font-medium text-surface-800">Sesión Actual</p>
                                                    <p className="text-xs text-surface-500">Navegador Web · Managua, NI</p>
                                                </div>
                                            </div>
                                            <span className="badge bg-green-100 text-green-700">Activa</span>
                                        </div>
                                    </div>
                                </div>

                                {/* MFA Section */}
                                <div className="p-5 rounded-xl border border-surface-200 bg-surface-50/50">
                                    <h3 className="font-semibold text-surface-800 mb-3">Autenticación de Dos Factores (MFA)</h3>
                                    <div className="space-y-4">
                                        <div className="flex items-center justify-between">
                                            <div>
                                                <p className="text-sm text-surface-600">
                                                    Protege tu cuenta con un paso adicional de seguridad.
                                                </p>
                                                {user?.mfa_enabled ? (
                                                    <span className="inline-flex mt-2 items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                                        Activado
                                                    </span>
                                                ) : (
                                                    <span className="inline-flex mt-2 items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-surface-200 text-surface-800">
                                                        Desactivado
                                                    </span>
                                                )}
                                            </div>
                                            <button 
                                                onClick={() => setShowMfaModal(true)}
                                                className={`btn text-sm py-1.5 px-4 ${user?.mfa_enabled ? 'btn-outline border-red-200 text-red-600 hover:bg-red-50' : 'btn-primary'}`}
                                            >
                                                {user?.mfa_enabled ? 'Desactivar MFA' : 'Configurar MFA'}
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Sprint 6: Integraciones & API Pública Section */}
                    {activeSection === 'integraciones' && (
                        <div className="space-y-6">
                            {/* ERP Connectors Banner */}
                            <div className="card p-6">
                                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-surface-100 pb-4 mb-4">
                                    <div>
                                        <h2 className="text-lg font-bold text-surface-900 flex items-center gap-2">
                                            <Key className="w-5 h-5 text-primary-500" />
                                            API Pública (`/api/v1/public/*`) & Conectores Contables
                                        </h2>
                                        <p className="text-sm text-surface-500">
                                            Sincroniza facturas, retenciones DGI/ALMA, pagos, clientes y tiempos con sistemas ERP externos
                                        </p>
                                    </div>
                                    <button
                                        onClick={fetchIntegrationsData}
                                        className="btn-outline text-xs py-1.5 px-3 flex items-center gap-1.5 self-start"
                                    >
                                        <RefreshCw className={`w-3.5 h-3.5 ${loadingIntegrations ? 'animate-spin' : ''}`} />
                                        Actualizar
                                    </button>
                                </div>

                                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
                                    {[
                                        { id: 'quickbooks', name: 'QuickBooks Online', desc: 'Facturas, Pagos y Clientes' },
                                        { id: 'xero', name: 'Xero Accounting', desc: 'Sincronización Contable' },
                                        { id: 'alegra', name: 'Alegra LATAM', desc: 'Facturación DGI / ALMA' },
                                        { id: 'sap', name: 'SAP Business One', desc: 'ERP Bidireccional' },
                                    ].map(erp => (
                                        <div key={erp.id} className="p-3.5 rounded-xl border border-surface-200 bg-surface-50/60">
                                            <p className="text-xs font-bold text-surface-800">{erp.name}</p>
                                            <p className="text-[11px] text-surface-500 mt-0.5">{erp.desc}</p>
                                        </div>
                                    ))}
                                </div>

                                {/* Newly Created Key Alert */}
                                {newlyCreatedKey && (
                                    <div className="mb-6 p-4 rounded-xl border-2 border-amber-300 bg-amber-50 space-y-2">
                                        <div className="flex items-center justify-between">
                                            <p className="text-sm font-bold text-amber-900">
                                                🔐 Guarda tu nueva API Key ahora (solo se muestra una vez)
                                            </p>
                                            <button
                                                onClick={() => setNewlyCreatedKey(null)}
                                                className="text-amber-700 hover:text-amber-900"
                                            >
                                                <X className="w-4 h-4" />
                                            </button>
                                        </div>
                                        <div className="flex items-center gap-2 bg-white p-2.5 rounded-lg border border-amber-200 font-mono text-xs text-surface-800 break-all">
                                            <span className="flex-1">{newlyCreatedKey}</span>
                                            <button
                                                onClick={() => copyToClipboard(newlyCreatedKey, 'API Key')}
                                                className="btn-primary py-1 px-2.5 text-xs flex items-center gap-1"
                                            >
                                                {copiedText === newlyCreatedKey ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                                                Copiar
                                            </button>
                                        </div>
                                        <p className="text-xs text-amber-700">
                                            Envía esta clave en el header HTTP <code className="font-mono bg-amber-100 px-1 rounded">X-API-Key</code>.
                                        </p>
                                    </div>
                                )}

                                {/* API Keys Header & Form */}
                                <div className="flex items-center justify-between mb-4">
                                    <h3 className="text-sm font-bold text-surface-800">Claves de API Activas</h3>
                                    {!showNewKeyForm && (
                                        <button
                                            onClick={() => setShowNewKeyForm(true)}
                                            className="btn-primary text-xs py-2 px-3.5 flex items-center gap-1.5"
                                        >
                                            <Plus className="w-4 h-4" />
                                            Generar API Key
                                        </button>
                                    )}
                                </div>

                                {showNewKeyForm && (
                                    <div className="mb-6 p-5 rounded-xl border border-primary-200 bg-primary-50/30 space-y-4">
                                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                            <InputField
                                                label="Nombre de la Integración"
                                                value={newKeyForm.nombre}
                                                onChange={(v: string) => setNewKeyForm(prev => ({ ...prev, nombre: v }))}
                                                placeholder="Ej: Conector Alegra Contabilidad"
                                            />
                                            <div>
                                                <label className="block text-sm font-medium text-surface-700 mb-1.5">Plataforma ERP</label>
                                                <select
                                                    value={newKeyForm.plataforma}
                                                    onChange={(e) => setNewKeyForm(prev => ({ ...prev, plataforma: e.target.value }))}
                                                    className="w-full px-3.5 py-2.5 rounded-lg border border-surface-300 bg-white text-sm text-surface-800"
                                                >
                                                    <option value="quickbooks">QuickBooks Online</option>
                                                    <option value="xero">Xero</option>
                                                    <option value="alegra">Alegra LATAM</option>
                                                    <option value="sap">SAP Business One</option>
                                                    <option value="custom">Personalizado / Otro</option>
                                                </select>
                                            </div>
                                            <InputField
                                                label="Rate Limit (req / min)"
                                                type="number"
                                                value={newKeyForm.rate_limit_per_minute}
                                                onChange={(v: string) => setNewKeyForm(prev => ({ ...prev, rate_limit_per_minute: Number(v) || 60 }))}
                                            />
                                        </div>

                                        <div>
                                            <label className="block text-xs font-semibold text-surface-700 mb-2">
                                                Alcances de Permisos (Scopes)
                                            </label>
                                            <div className="flex flex-wrap gap-2">
                                                {DEFAULT_SCOPES.map(scope => {
                                                    const active = newKeyForm.scopes.includes(scope);
                                                    return (
                                                        <button
                                                            key={scope}
                                                            type="button"
                                                            onClick={() => toggleScope(scope)}
                                                            className={`px-3 py-1.5 rounded-lg text-xs font-mono border transition-all ${
                                                                active
                                                                    ? 'bg-primary-600 text-white border-primary-600'
                                                                    : 'bg-white text-surface-600 border-surface-300 hover:border-primary-400'
                                                            }`}
                                                        >
                                                            {scope}
                                                        </button>
                                                    );
                                                })}
                                            </div>
                                        </div>

                                        <div className="flex justify-end gap-2 pt-2">
                                            <button
                                                onClick={() => setShowNewKeyForm(false)}
                                                className="px-4 py-2 text-xs text-surface-600 hover:text-surface-800"
                                            >
                                                Cancelar
                                            </button>
                                            <button
                                                onClick={handleCreateApiKey}
                                                disabled={saving}
                                                className="btn-primary text-xs py-2 px-4"
                                            >
                                                {saving ? 'Generando...' : 'Crear API Key'}
                                            </button>
                                        </div>
                                    </div>
                                )}

                                {/* API Keys List */}
                                <div className="space-y-3">
                                    {apiKeys.length === 0 ? (
                                        <p className="text-sm text-surface-400 py-6 text-center border border-dashed border-surface-200 rounded-xl">
                                            No hay claves de API generadas todavía.
                                        </p>
                                    ) : (
                                        apiKeys.map(k => (
                                            <div
                                                key={k.id}
                                                className="flex flex-col md:flex-row md:items-center justify-between gap-3 p-4 rounded-xl border border-surface-200 bg-white"
                                            >
                                                <div className="space-y-1">
                                                    <div className="flex items-center gap-2">
                                                        <span className="font-semibold text-sm text-surface-900">{k.nombre}</span>
                                                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold uppercase bg-surface-100 text-surface-700">
                                                            {k.plataforma}
                                                        </span>
                                                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                                                            k.activo ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                                                        }`}>
                                                            {k.activo ? 'Activa' : 'Revocada'}
                                                        </span>
                                                    </div>
                                                    <p className="text-xs font-mono text-surface-500">
                                                        Prefijo: <span className="text-surface-700">{k.key_prefix}...</span> · Límite: {k.rate_limit_per_minute}/min
                                                    </p>
                                                    <div className="flex flex-wrap gap-1 pt-1">
                                                        {(k.scopes || []).map(sc => (
                                                            <span key={sc} className="px-2 py-0.5 rounded bg-surface-100 text-surface-600 font-mono text-[10px]">
                                                                {sc}
                                                            </span>
                                                        ))}
                                                    </div>
                                                </div>
                                                {k.activo && (
                                                    <button
                                                        onClick={() => handleRevokeApiKey(k.id)}
                                                        className="btn-outline border-red-200 text-red-600 hover:bg-red-50 text-xs py-1.5 px-3 flex items-center gap-1.5 self-start md:self-center"
                                                    >
                                                        <Trash2 className="w-3.5 h-3.5" />
                                                        Revocar
                                                    </button>
                                                )}
                                            </div>
                                        ))
                                    )}
                                </div>
                            </div>

                            {/* Webhooks Card */}
                            <div className="card p-6 space-y-5">
                                <div className="flex items-center justify-between border-b border-surface-100 pb-4">
                                    <div>
                                        <h2 className="text-lg font-bold text-surface-900 flex items-center gap-2">
                                            <Webhook className="w-5 h-5 text-primary-500" />
                                            Suscripciones de Webhooks (Tiempo Real)
                                        </h2>
                                        <p className="text-sm text-surface-500">
                                            Notificaciones HTTP POST firmadas con <code className="font-mono text-xs">X-LexIntellectus-Signature</code> (HMAC-SHA256)
                                        </p>
                                    </div>
                                    {!showNewWebhookForm && (
                                        <button
                                            onClick={() => setShowNewWebhookForm(true)}
                                            className="btn-primary text-xs py-2 px-3.5 flex items-center gap-1.5"
                                        >
                                            <Plus className="w-4 h-4" />
                                            Nuevo Webhook
                                        </button>
                                    )}
                                </div>

                                {showNewWebhookForm && (
                                    <div className="p-5 rounded-xl border border-primary-200 bg-primary-50/30 space-y-4">
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                            <InputField
                                                label="Nombre del Endpoint"
                                                value={newWebhookForm.nombre}
                                                onChange={(v: string) => setNewWebhookForm(prev => ({ ...prev, nombre: v }))}
                                                placeholder="Ej: Listener Contable QuickBooks"
                                            />
                                            <InputField
                                                label="URL de Destino (HTTPS)"
                                                value={newWebhookForm.url}
                                                onChange={(v: string) => setNewWebhookForm(prev => ({ ...prev, url: v }))}
                                                placeholder="https://erp.midominio.com/webhooks/lexintellectus"
                                            />
                                        </div>

                                        <div>
                                            <label className="block text-xs font-semibold text-surface-700 mb-2">
                                                Eventos Suscritos (14 eventos disponibles)
                                            </label>
                                            <div className="flex flex-wrap gap-1.5">
                                                {DEFAULT_WEBHOOK_EVENTS.map(ev => {
                                                    const active = newWebhookForm.events.includes(ev);
                                                    return (
                                                        <button
                                                            key={ev}
                                                            type="button"
                                                            onClick={() => toggleWebhookEvent(ev)}
                                                            className={`px-2.5 py-1 rounded-lg text-xs font-mono border transition-all ${
                                                                active
                                                                    ? 'bg-primary-600 text-white border-primary-600'
                                                                    : 'bg-white text-surface-600 border-surface-300 hover:border-primary-400'
                                                            }`}
                                                        >
                                                            {ev}
                                                        </button>
                                                    );
                                                })}
                                            </div>
                                        </div>

                                        <div className="flex justify-end gap-2 pt-2">
                                            <button
                                                onClick={() => setShowNewWebhookForm(false)}
                                                className="px-4 py-2 text-xs text-surface-600 hover:text-surface-800"
                                            >
                                                Cancelar
                                            </button>
                                            <button
                                                onClick={handleCreateWebhook}
                                                disabled={saving}
                                                className="btn-primary text-xs py-2 px-4"
                                            >
                                                {saving ? 'Guardando...' : 'Registrar Webhook'}
                                            </button>
                                        </div>
                                    </div>
                                )}

                                <div className="space-y-3">
                                    {webhooks.length === 0 ? (
                                        <p className="text-sm text-surface-400 py-6 text-center border border-dashed border-surface-200 rounded-xl">
                                            No hay endpoints de webhook registrados.
                                        </p>
                                    ) : (
                                        webhooks.map(wh => (
                                            <div key={wh.id} className="p-4 rounded-xl border border-surface-200 bg-white space-y-3">
                                                <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
                                                    <div>
                                                        <div className="flex items-center gap-2">
                                                            <span className="font-semibold text-sm text-surface-900">{wh.nombre}</span>
                                                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                                                                wh.activo ? 'bg-green-100 text-green-700' : 'bg-surface-200 text-surface-600'
                                                            }`}>
                                                                {wh.activo ? 'Activo' : 'Pausado'}
                                                            </span>
                                                        </div>
                                                        <p className="text-xs font-mono text-primary-600 break-all mt-0.5">{wh.url}</p>
                                                    </div>

                                                    <div className="flex items-center gap-2">
                                                        <button
                                                            onClick={() => handleTestWebhook(wh.id)}
                                                            className="btn-outline text-xs py-1.5 px-3 flex items-center gap-1"
                                                        >
                                                            <Send className="w-3.5 h-3.5" />
                                                            Probar Ping
                                                        </button>
                                                        <button
                                                            onClick={() => handleViewWebhookLogs(wh.id)}
                                                            className="btn-outline text-xs py-1.5 px-3 flex items-center gap-1"
                                                        >
                                                            <Activity className="w-3.5 h-3.5" />
                                                            Logs
                                                        </button>
                                                        <button
                                                            onClick={() => handleDeleteWebhook(wh.id)}
                                                            className="p-1.5 text-red-500 hover:bg-red-50 rounded-lg"
                                                            title="Eliminar Webhook"
                                                        >
                                                            <Trash2 className="w-4 h-4" />
                                                        </button>
                                                    </div>
                                                </div>

                                                <div className="flex items-center justify-between bg-surface-50 px-3 py-2 rounded-lg text-xs">
                                                    <span className="font-mono text-surface-600 truncate">
                                                        Secret HMAC: <strong>{wh.secret}</strong>
                                                    </span>
                                                    <button
                                                        onClick={() => copyToClipboard(wh.secret, 'Signing Secret')}
                                                        className="text-primary-600 hover:underline flex items-center gap-1 ml-2 flex-shrink-0"
                                                    >
                                                        <Copy className="w-3.5 h-3.5" />
                                                        Copiar Secret
                                                    </button>
                                                </div>

                                                <div className="flex flex-wrap gap-1">
                                                    {(wh.events || []).map(ev => (
                                                        <span key={ev} className="px-2 py-0.5 rounded bg-primary-50 text-primary-700 font-mono text-[10px]">
                                                            {ev}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        ))
                                    )}
                                </div>

                                {/* Delivery Logs Viewer */}
                                {selectedWebhookLogs && (
                                    <div className="mt-4 p-4 rounded-xl border border-surface-200 bg-surface-50 space-y-3">
                                        <div className="flex items-center justify-between">
                                            <h4 className="text-xs font-bold uppercase tracking-wider text-surface-700">
                                                Historial de Entregas Recientes
                                            </h4>
                                            <button
                                                onClick={() => setSelectedWebhookLogs(null)}
                                                className="text-xs text-surface-500 hover:text-surface-800"
                                            >
                                                Cerrar
                                            </button>
                                        </div>
                                        {selectedWebhookLogs.logs.length === 0 ? (
                                            <p className="text-xs text-surface-500">Sin entregas registradas.</p>
                                        ) : (
                                            <div className="space-y-2 max-h-60 overflow-y-auto">
                                                {selectedWebhookLogs.logs.map(log => (
                                                    <div key={log.id} className="p-2.5 rounded-lg bg-white border border-surface-200 flex items-center justify-between text-xs">
                                                        <div>
                                                            <span className="font-mono font-semibold text-surface-800">{log.event_type}</span>
                                                            <span className="text-surface-400 ml-2">
                                                                Intentos: {log.attempt_count}
                                                            </span>
                                                        </div>
                                                        <div className="flex items-center gap-2">
                                                            <span className={`px-2 py-0.5 rounded font-mono text-[10px] ${
                                                                log.success ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-800'
                                                            }`}>
                                                                HTTP {log.response_status ?? 0}
                                                            </span>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Notifications Section */}
                    {activeSection === 'notificaciones' && (
                        <div className="card p-8 space-y-6">
                            <div className="border-b border-surface-100 pb-4">
                                <h2 className="text-lg font-bold text-surface-900">Preferencias de Notificaciones</h2>
                                <p className="text-sm text-surface-500">Configura cómo y cuándo recibir alertas</p>
                            </div>

                            {[
                                { label: 'Plazos fatales (72h antes)', desc: 'Alerta cuando un plazo vence en 3 días', defaultOn: true },
                                { label: 'Plazos fatales (24h antes)', desc: 'Alerta urgente, vence mañana', defaultOn: true },
                                { label: 'Nuevos documentos', desc: 'Cuando se sube un documento a sus expedientes', defaultOn: false },
                                { label: 'Asignación de expedientes', desc: 'Cuando le asignan un nuevo caso', defaultOn: true },
                                { label: 'Resumen diario por email', desc: 'Resumen de actividad enviado cada mañana', defaultOn: false },
                            ].map((item, i) => (
                                <div key={i} className="flex items-center justify-between py-3 border-b border-surface-50 last:border-0">
                                    <div>
                                        <p className="text-sm font-medium text-surface-800">{item.label}</p>
                                        <p className="text-xs text-surface-500 mt-0.5">{item.desc}</p>
                                    </div>
                                    <label className="relative inline-flex items-center cursor-pointer">
                                        <input type="checkbox" defaultChecked={item.defaultOn} className="sr-only peer" />
                                        <div className="w-10 h-5 bg-surface-300 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-primary-500" />
                                    </label>
                                </div>
                            ))}

                            <div className="flex justify-end pt-4">
                                <button onClick={() => toast.success('Preferencias guardadas')} className="btn-primary flex items-center gap-2">
                                    <Save className="w-4 h-4" />
                                    Guardar Preferencias
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Appearance Section */}
                    {activeSection === 'apariencia' && (
                        <div className="card p-8 space-y-6">
                            <div className="border-b border-surface-100 pb-4">
                                <h2 className="text-lg font-bold text-surface-900">Apariencia</h2>
                                <p className="text-sm text-surface-500">Personaliza la interfaz del sistema</p>
                            </div>

                            <div>
                                <h3 className="text-sm font-semibold text-surface-800 mb-3">Tema de Color</h3>
                                <div className="grid grid-cols-3 gap-4">
                                    {[
                                        { name: 'Clásico (Azul)', colors: ['#1E3A5F', '#D4AF37', '#F8FAFC'], active: true },
                                        { name: 'Oscuro', colors: ['#1a1a2e', '#e94560', '#16213e'], active: false },
                                        { name: 'Profesional', colors: ['#2d3436', '#00b894', '#dfe6e9'], active: false },
                                    ].map((theme) => (
                                        <button
                                            key={theme.name}
                                            className={`p-4 rounded-xl border-2 text-center transition-all ${
                                                theme.active ? 'border-primary-500 ring-2 ring-primary-500/20' : 'border-surface-200 hover:border-surface-300'
                                            }`}
                                        >
                                            <div className="flex gap-1.5 justify-center mb-2">
                                                {theme.colors.map((c, ci) => (
                                                    <div key={ci} className="w-6 h-6 rounded-full border border-surface-200" style={{ backgroundColor: c }} />
                                                ))}
                                            </div>
                                            <p className="text-xs font-medium text-surface-700">{theme.name}</p>
                                            {theme.active && <p className="text-[10px] text-primary-500 mt-1">Activo</p>}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm text-amber-800">
                                <p className="font-medium">🎨 Temas adicionales próximamente</p>
                                <p className="text-xs text-amber-600 mt-1">Los temas Oscuro y Profesional estarán disponibles en la próxima versión.</p>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* 2FA Modal */}
            <MfaModal
                isOpen={showMfaModal}
                onClose={() => setShowMfaModal(false)}
                isCurrentlyEnabled={!!user?.mfa_enabled}
                onSuccess={(newStatus) => {
                    setUser((prev: any) => ({ ...prev, mfa_enabled: newStatus }));
                    localStorage.setItem('user', JSON.stringify({ ...user, mfa_enabled: newStatus }));
                }}
            />
        </div>
    );
}
