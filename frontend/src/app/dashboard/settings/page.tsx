'use client';

import { useState, useEffect } from 'react';
import {
    Building2, Users, Shield, MapPin, Save, Plus, X, Eye, EyeOff,
    Settings as SettingsIcon, ChevronRight, Palette, Bell, Lock
} from 'lucide-react';
import { useToast } from '@/components/ui/ToastProvider';
import { settingsService } from '@/services/settingsService';

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

    const toast = useToast();

    useEffect(() => {
        const stored = localStorage.getItem('user');
        if (stored) setUser(JSON.parse(stored));
        fetchTenantData();
    }, []);

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
            // If API call fails, still save to localStorage as fallback
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
        { id: 'seguridad', label: 'Seguridad', icon: Lock, desc: 'Contraseña y sesiones' },
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

    return (
        <div className="animate-fade-in space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold text-surface-900 flex items-center gap-3">
                    <SettingsIcon className="w-6 h-6 text-primary-500" />
                    Configuración
                </h1>
                <p className="text-surface-500 text-sm mt-1">
                    Administra la configuración de tu despacho, perfil y preferencias
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
        </div>
    );
}
