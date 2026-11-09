'use client';

import { useState, useEffect } from 'react';

interface ClientProfileData {
    id: string;
    nombre: string;
    apellido: string;
    email: string;
    telefono: string;
    tipo_persona: string;
    cedula_identidad: string;
    ruc: string;
    razon_social: string;
    nombre_comercial: string;
    direccion_domicilio: string;
    ciudad: string;
    departamento: string;
    pais: string;
    segmento: string;
    kyc_verificado: boolean;
    dias_credito: number;
}

export default function PortalProfilePage() {
    const [profile, setProfile] = useState<ClientProfileData | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [savedMsg, setSavedMsg] = useState('');

    const getAuthHeaders = () => {
        const token = localStorage.getItem('access_token');
        const userStr = localStorage.getItem('user');
        const user = userStr ? JSON.parse(userStr) : {};
        return {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
            'X-Tenant-ID': user.tenant_id || ''
        };
    };

    useEffect(() => {
        const fetchProfile = async () => {
            try {
                const res = await fetch('/api/v1/portal/profile', {
                    headers: getAuthHeaders()
                });
                if (res.ok) {
                    const data = await res.json();
                    setProfile(data);
                }
            } catch (err) {
                console.error('Error loading profile:', err);
            } finally {
                setLoading(false);
            }
        };
        fetchProfile();
    }, []);

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!profile) return;
        setSaving(true);
        setSavedMsg('');
        try {
            const res = await fetch('/api/v1/portal/profile', {
                method: 'PATCH',
                headers: getAuthHeaders(),
                body: JSON.stringify({
                    nombre: profile.nombre,
                    apellido: profile.apellido,
                    telefono: profile.telefono,
                    direccion_domicilio: profile.direccion_domicilio,
                    ciudad: profile.ciudad,
                    departamento: profile.departamento,
                    razon_social: profile.razon_social,
                    nombre_comercial: profile.nombre_comercial
                })
            });
            if (res.ok) {
                const updated = await res.json();
                setProfile(updated);
                setSavedMsg('Sus datos han sido actualizados exitosamente.');
                setTimeout(() => setSavedMsg(''), 4000);
            }
        } catch (err) {
            console.error('Error updating profile:', err);
        } finally {
            setSaving(false);
        }
    };

    if (loading || !profile) {
        return (
            <div className="flex items-center justify-center min-h-[60vh]">
                <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-amber-500"></div>
            </div>
        );
    }

    return (
        <div className="max-w-4xl space-y-8">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-extrabold text-white tracking-tight">Mi Perfil Legal y Facturación</h1>
                    <p className="text-slate-400 text-sm mt-1">
                        Mantenga actualizados sus datos de contacto, domicilio legal e información tributaria.
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    <span className={`px-3 py-1 rounded-full text-xs font-bold border ${
                        profile.kyc_verificado
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                            : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                    }`}>
                        {profile.kyc_verificado ? '✓ KYC Verificado (Ley 977)' : 'KYC en Proceso'}
                    </span>
                </div>
            </div>

            {savedMsg && (
                <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-sm font-semibold">
                    {savedMsg}
                </div>
            )}

            <form onSubmit={handleSave} className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 lg:p-8 space-y-6 shadow-xl">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                        <label className="block text-xs font-semibold text-slate-400 uppercase mb-1.5">Nombre</label>
                        <input
                            type="text"
                            value={profile.nombre}
                            onChange={(e) => setProfile({ ...profile, nombre: e.target.value })}
                            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-semibold text-slate-400 uppercase mb-1.5">Apellido</label>
                        <input
                            type="text"
                            value={profile.apellido}
                            onChange={(e) => setProfile({ ...profile, apellido: e.target.value })}
                            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-semibold text-slate-400 uppercase mb-1.5">Correo Electrónico (Solo lectura)</label>
                        <input
                            type="email"
                            disabled
                            value={profile.email}
                            className="w-full bg-slate-950/50 border border-slate-800/60 rounded-xl px-4 py-2.5 text-sm text-slate-500 cursor-not-allowed"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-semibold text-slate-400 uppercase mb-1.5">Teléfono de Contacto</label>
                        <input
                            type="text"
                            value={profile.telefono}
                            onChange={(e) => setProfile({ ...profile, telefono: e.target.value })}
                            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-semibold text-slate-400 uppercase mb-1.5">Razón Social / Empresa</label>
                        <input
                            type="text"
                            value={profile.razon_social || ''}
                            onChange={(e) => setProfile({ ...profile, razon_social: e.target.value })}
                            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-semibold text-slate-400 uppercase mb-1.5">Nombre Comercial</label>
                        <input
                            type="text"
                            value={profile.nombre_comercial || ''}
                            onChange={(e) => setProfile({ ...profile, nombre_comercial: e.target.value })}
                            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white"
                        />
                    </div>
                    <div className="md:col-span-2">
                        <label className="block text-xs font-semibold text-slate-400 uppercase mb-1.5">Dirección de Domicilio Legal (Cifrado Ley 787)</label>
                        <input
                            type="text"
                            value={profile.direccion_domicilio || ''}
                            onChange={(e) => setProfile({ ...profile, direccion_domicilio: e.target.value })}
                            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-semibold text-slate-400 uppercase mb-1.5">Ciudad / Municipio</label>
                        <input
                            type="text"
                            value={profile.ciudad || ''}
                            onChange={(e) => setProfile({ ...profile, ciudad: e.target.value })}
                            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-semibold text-slate-400 uppercase mb-1.5">Departamento</label>
                        <input
                            type="text"
                            value={profile.departamento || ''}
                            onChange={(e) => setProfile({ ...profile, departamento: e.target.value })}
                            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white"
                        />
                    </div>
                </div>

                <div className="flex justify-end pt-4 border-t border-slate-800">
                    <button
                        type="submit"
                        disabled={saving}
                        className="px-6 py-3 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold shadow-lg transition-all"
                    >
                        {saving ? 'Guardando cambios...' : 'Guardar Cambios de Perfil'}
                    </button>
                </div>
            </form>
        </div>
    );
}
