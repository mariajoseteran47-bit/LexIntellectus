'use client';

import { useState, useEffect } from 'react';
import {
    Users, Search, Plus, Mail, Phone, MoreVertical, Shield,
    Building2, User as UserIcon, FileText, ChevronDown, ChevronUp,
    Briefcase, MapPin, Hash, Calendar, AlertTriangle, CheckCircle2, X
} from 'lucide-react';
import { userService, User, CreateUserDto } from '@/services/userService';
import api from '@/lib/api';

interface ClientProfile {
    id: string;
    user_id: string;
    tipo_persona: 'natural' | 'juridica';
    cedula_identidad?: string;
    ruc?: string;
    razon_social?: string;
    nombre_comercial?: string;
    tipo_sociedad?: string;
    actividad_economica?: string;
    direccion_domicilio?: string;
    ciudad?: string;
    departamento?: string;
    calificacion_riesgo: string;
    segmento: string;
    kyc_verificado: boolean;
    representantes: Representative[];
}

interface Representative {
    id: string;
    nombre_completo: string;
    tipo_poder: string;
    cargo?: string;
    numero_escritura?: string;
    fecha_otorgamiento: string;
    fecha_vencimiento?: string;
    notario_autorizante?: string;
    vigente: boolean;
}

type ModalStep = 'user' | 'profile' | 'representative';

const tipoSociedadLabels: Record<string, string> = {
    sociedad_anonima: 'Sociedad Anónima',
    sociedad_colectiva: 'Sociedad Colectiva',
    sociedad_responsabilidad_limitada: 'S.R.L.',
    cooperativa: 'Cooperativa',
    fundacion: 'Fundación',
    asociacion: 'Asociación',
    empresa_individual: 'Empresa Individual',
    sucursal_extranjera: 'Sucursal Extranjera',
    otro: 'Otro',
};

const tipoPoderLabels: Record<string, string> = {
    generalisimo: 'Generalísimo',
    general_administracion: 'General de Administración',
    especial: 'Especial',
    judicial: 'Judicial',
};

const riskColors: Record<string, string> = {
    bajo: 'text-green-600 bg-green-50',
    medio: 'text-amber-600 bg-amber-50',
    alto: 'text-red-600 bg-red-50',
};

export default function ClientsPage() {
    const [clients, setClients] = useState<User[]>([]);
    const [profiles, setProfiles] = useState<Record<string, ClientProfile>>({});
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [filterType, setFilterType] = useState<string>('all');
    const [showModal, setShowModal] = useState(false);
    const [modalStep, setModalStep] = useState<ModalStep>('user');
    const [saving, setSaving] = useState(false);
    const [expandedClient, setExpandedClient] = useState<string | null>(null);
    const [newUserId, setNewUserId] = useState<string | null>(null);

    // Form states
    const [formData, setFormData] = useState<CreateUserDto>({
        nombre: '', apellido: '', email: '', telefono: '',
        password: 'ClientPassword123!', tipo_usuario: 'cliente', tipo_vinculo: 'cliente'
    });
    const [profileForm, setProfileForm] = useState({
        tipo_persona: 'natural' as 'natural' | 'juridica',
        cedula_identidad: '', ruc: '', razon_social: '', nombre_comercial: '',
        tipo_sociedad: '', actividad_economica: '', direccion_domicilio: '',
        ciudad: '', departamento: '', segmento: 'individual',
        calificacion_riesgo: 'bajo', referido_por: '',
    });
    const [repForm, setRepForm] = useState({
        nombre_completo: '', cedula_identidad: '', telefono: '', email: '',
        cargo: '', tipo_poder: 'generalisimo', numero_escritura: '',
        fecha_otorgamiento: '', notario_autorizante: '', alcance_facultades: '',
    });

    useEffect(() => { fetchClients(); }, []);

    const fetchClients = async () => {
        try {
            const data = await userService.getAll(1, 100, '', 'cliente');
            setClients(data.items);
            // Fetch profiles for each client
            try {
                const { data: profileData } = await api.get('/clients/profiles?size=100');
                const map: Record<string, ClientProfile> = {};
                (profileData.items || []).forEach((p: ClientProfile) => { map[p.user_id] = p; });
                setProfiles(map);
            } catch { /* profiles may not exist yet */ }
        } catch (error) {
            console.error('Failed to fetch clients', error);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateUser = async (e: React.FormEvent) => {
        e.preventDefault();
        setSaving(true);
        try {
            const { data: newUser } = await api.post('/users', formData);
            setNewUserId(newUser.id);
            setModalStep('profile');
        } catch (error: any) {
            alert(error.response?.data?.detail || error.response?.data?.error?.message || 'Error al crear el cliente.');
        } finally {
            setSaving(false);
        }
    };

    const handleCreateProfile = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newUserId) return;
        setSaving(true);
        try {
            const payload = { ...profileForm, user_id: newUserId };
            const { data: profile } = await api.post('/clients/profiles', payload);
            if (profileForm.tipo_persona === 'juridica') {
                setNewUserId(profile.id); // reuse for rep step
                setModalStep('representative');
            } else {
                closeAndRefresh();
            }
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Error al crear perfil.');
        } finally {
            setSaving(false);
        }
    };

    const handleAddRepresentative = async (e: React.FormEvent) => {
        e.preventDefault();
        setSaving(true);
        try {
            await api.post(`/clients/profiles/${newUserId}/representatives`, repForm);
            closeAndRefresh();
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Error al agregar representante.');
        } finally {
            setSaving(false);
        }
    };

    const closeAndRefresh = () => {
        setShowModal(false);
        setModalStep('user');
        setNewUserId(null);
        setFormData({ nombre: '', apellido: '', email: '', telefono: '', password: 'ClientPassword123!', tipo_usuario: 'cliente', tipo_vinculo: 'cliente' });
        setProfileForm({ tipo_persona: 'natural', cedula_identidad: '', ruc: '', razon_social: '', nombre_comercial: '', tipo_sociedad: '', actividad_economica: '', direccion_domicilio: '', ciudad: '', departamento: '', segmento: 'individual', calificacion_riesgo: 'bajo', referido_por: '' });
        setRepForm({ nombre_completo: '', cedula_identidad: '', telefono: '', email: '', cargo: '', tipo_poder: 'generalisimo', numero_escritura: '', fecha_otorgamiento: '', notario_autorizante: '', alcance_facultades: '' });
        fetchClients();
    };

    const filteredClients = clients.filter(c => {
        const matchSearch = c.nombre.toLowerCase().includes(searchTerm.toLowerCase()) ||
            c.apellido.toLowerCase().includes(searchTerm.toLowerCase()) ||
            c.email.toLowerCase().includes(searchTerm.toLowerCase());
        if (filterType === 'all') return matchSearch;
        const profile = profiles[c.id];
        if (filterType === 'natural') return matchSearch && (!profile || profile.tipo_persona === 'natural');
        if (filterType === 'juridica') return matchSearch && profile?.tipo_persona === 'juridica';
        return matchSearch;
    });

    if (loading) {
        return <div className="p-8 text-center text-surface-500">Cargando directorio de clientes...</div>;
    }

    const stepTitles: Record<ModalStep, string> = {
        user: '1. Datos de Acceso',
        profile: '2. Perfil Legal',
        representative: '3. Representante Legal',
    };

    return (
        <div className="space-y-6 animate-fade-in">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="flex flex-col gap-1">
                    <h1 className="text-2xl font-bold text-surface-900 flex items-center gap-3">
                        <Users className="w-8 h-8 text-primary-500" />
                        Directorio de Clientes
                    </h1>
                    <p className="text-surface-500">Gestiona clientes naturales y jurídicos con sus representantes legales.</p>
                </div>
                <button onClick={() => setShowModal(true)} className="btn btn-primary flex items-center gap-2">
                    <Plus className="w-4 h-4" /> Nuevo Cliente
                </button>
            </div>

            {/* Filters */}
            <div className="card p-4">
                <div className="flex flex-col md:flex-row gap-3">
                    <div className="relative flex-1 max-w-md">
                        <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-surface-400" />
                        <input type="text" placeholder="Buscar por nombre, apellido o email..." className="input w-full pl-9 h-10 text-sm"
                            value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} />
                    </div>
                    <div className="flex gap-2">
                        {[
                            { key: 'all', label: 'Todos', icon: Users },
                            { key: 'natural', label: 'Naturales', icon: UserIcon },
                            { key: 'juridica', label: 'Jurídicas', icon: Building2 },
                        ].map(f => (
                            <button key={f.key} onClick={() => setFilterType(f.key)}
                                className={`px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-all ${filterType === f.key ? 'bg-primary-600 text-white' : 'bg-surface-100 text-surface-600 hover:bg-surface-200'}`}>
                                <f.icon className="w-3.5 h-3.5" /> {f.label}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* Client List */}
            {filteredClients.length === 0 ? (
                <div className="card p-12 text-center space-y-4">
                    <div className="w-16 h-16 bg-surface-100 rounded-full flex items-center justify-center mx-auto">
                        <Users className="w-8 h-8 text-surface-400" />
                    </div>
                    <p className="text-surface-500 font-medium">No se encontraron clientes registrados.</p>
                    <button className="btn btn-sm btn-outline" onClick={() => { setSearchTerm(''); setFilterType('all'); }}>Limpiar filtros</button>
                </div>
            ) : (
                <div className="space-y-3">
                    {filteredClients.map((client) => {
                        const profile = profiles[client.id];
                        const isExpanded = expandedClient === client.id;
                        const isJuridica = profile?.tipo_persona === 'juridica';

                        return (
                            <div key={client.id} className="card overflow-hidden hover:shadow-judicial transition-all">
                                {/* Main Row */}
                                <div className="p-5 flex items-center justify-between cursor-pointer" onClick={() => setExpandedClient(isExpanded ? null : client.id)}>
                                    <div className="flex items-center gap-4">
                                        <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-lg font-bold ${isJuridica ? 'bg-violet-50 text-violet-600' : 'bg-primary-50 text-primary-600'}`}>
                                            {isJuridica ? <Building2 className="w-6 h-6" /> : <>{client.nombre[0]}{client.apellido[0]}</>}
                                        </div>
                                        <div>
                                            <h3 className="font-bold text-surface-900 text-lg flex items-center gap-2">
                                                {isJuridica && profile?.razon_social ? profile.razon_social : `${client.nombre} ${client.apellido}`}
                                                {isJuridica && (
                                                    <span className="text-[10px] font-bold uppercase tracking-wider text-violet-600 bg-violet-50 px-2 py-0.5 rounded">Jurídica</span>
                                                )}
                                            </h3>
                                            <div className="flex items-center gap-4 mt-1 text-sm text-surface-500">
                                                <span className="flex items-center gap-1"><Mail className="w-3.5 h-3.5" /> {client.email}</span>
                                                {client.telefono && <span className="flex items-center gap-1"><Phone className="w-3.5 h-3.5" /> {client.telefono}</span>}
                                                {profile?.ruc && <span className="flex items-center gap-1"><Hash className="w-3.5 h-3.5" /> RUC: {profile.ruc}</span>}
                                            </div>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        {profile && (
                                            <span className={`inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${riskColors[profile.calificacion_riesgo] || 'text-surface-600 bg-surface-100'}`}>
                                                {profile.calificacion_riesgo === 'alto' ? <AlertTriangle className="w-3 h-3" /> : <Shield className="w-3 h-3" />}
                                                Riesgo {profile.calificacion_riesgo}
                                            </span>
                                        )}
                                        {!profile && (
                                            <span className="text-[10px] font-bold uppercase tracking-wider text-amber-600 bg-amber-50 px-2 py-0.5 rounded">Sin perfil</span>
                                        )}
                                        {isExpanded ? <ChevronUp className="w-5 h-5 text-surface-400" /> : <ChevronDown className="w-5 h-5 text-surface-400" />}
                                    </div>
                                </div>

                                {/* Expanded Detail */}
                                {isExpanded && (
                                    <div className="border-t border-surface-100 bg-surface-50/50 p-5 space-y-4 animate-fade-in">
                                        {profile ? (
                                            <>
                                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                                    <InfoField label="Tipo" value={profile.tipo_persona === 'juridica' ? 'Persona Jurídica' : 'Persona Natural'} />
                                                    <InfoField label="Cédula" value={profile.cedula_identidad} />
                                                    <InfoField label="Segmento" value={profile.segmento?.replace('_', ' ')} />
                                                    <InfoField label="KYC" value={profile.kyc_verificado ? '✅ Verificado' : '⏳ Pendiente'} />
                                                    {isJuridica && <>
                                                        <InfoField label="Tipo Sociedad" value={tipoSociedadLabels[profile.tipo_sociedad || ''] || profile.tipo_sociedad} />
                                                        <InfoField label="Nombre Comercial" value={profile.nombre_comercial} />
                                                        <InfoField label="Actividad" value={profile.actividad_economica} />
                                                    </>}
                                                    {profile.direccion_domicilio && <InfoField label="Domicilio" value={`${profile.direccion_domicilio}${profile.ciudad ? `, ${profile.ciudad}` : ''}`} />}
                                                </div>

                                                {/* Representatives */}
                                                {isJuridica && profile.representantes && profile.representantes.length > 0 && (
                                                    <div className="mt-4">
                                                        <h4 className="text-sm font-bold text-surface-700 mb-3 flex items-center gap-2">
                                                            <Briefcase className="w-4 h-4 text-primary-500" /> Representantes Legales / Apoderados
                                                        </h4>
                                                        <div className="space-y-2">
                                                            {profile.representantes.map(rep => (
                                                                <div key={rep.id} className="p-3 bg-white rounded-lg border border-surface-200 flex items-center justify-between">
                                                                    <div>
                                                                        <p className="font-semibold text-surface-800">{rep.nombre_completo}</p>
                                                                        <p className="text-xs text-surface-500 mt-0.5">
                                                                            {tipoPoderLabels[rep.tipo_poder] || rep.tipo_poder}
                                                                            {rep.cargo && ` · ${rep.cargo}`}
                                                                            {rep.numero_escritura && ` · Escritura N° ${rep.numero_escritura}`}
                                                                        </p>
                                                                    </div>
                                                                    <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded ${rep.vigente ? 'text-green-600 bg-green-50' : 'text-red-600 bg-red-50'}`}>
                                                                        {rep.vigente ? 'Vigente' : 'Revocado'}
                                                                    </span>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}
                                                {isJuridica && (!profile.representantes || profile.representantes.length === 0) && (
                                                    <p className="text-sm text-amber-600 bg-amber-50 p-3 rounded-lg flex items-center gap-2">
                                                        <AlertTriangle className="w-4 h-4" /> Esta persona jurídica no tiene representantes legales registrados.
                                                    </p>
                                                )}
                                            </>
                                        ) : (
                                            <p className="text-sm text-surface-500 italic">Este cliente no tiene perfil extendido. Puede agregarlo desde la edición del cliente.</p>
                                        )}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}

            {/* Multi-Step Modal */}
            {showModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-surface-900/50 backdrop-blur-sm animate-fade-in">
                    <div className="bg-white rounded-2xl shadow-judicial-lg w-full max-w-2xl overflow-hidden animate-slide-up max-h-[90vh] flex flex-col">
                        {/* Modal Header */}
                        <div className="p-5 border-b border-surface-200 bg-surface-50 flex justify-between items-center flex-shrink-0">
                            <div>
                                <h2 className="text-lg font-bold text-surface-900 flex items-center gap-2">
                                    <Users className="w-5 h-5 text-primary-500" /> Nuevo Cliente
                                </h2>
                                <div className="flex items-center gap-2 mt-2">
                                    {(['user', 'profile', 'representative'] as ModalStep[]).map((step, i) => (
                                        <div key={step} className="flex items-center gap-1">
                                            <div className={`w-6 h-6 rounded-full text-[10px] font-bold flex items-center justify-center ${modalStep === step ? 'bg-primary-600 text-white' : i < ['user', 'profile', 'representative'].indexOf(modalStep) ? 'bg-green-500 text-white' : 'bg-surface-200 text-surface-500'}`}>
                                                {i + 1}
                                            </div>
                                            <span className={`text-[10px] font-medium ${modalStep === step ? 'text-primary-700' : 'text-surface-400'}`}>{stepTitles[step]}</span>
                                            {i < 2 && <div className="w-4 h-px bg-surface-300 mx-1" />}
                                        </div>
                                    ))}
                                </div>
                            </div>
                            <button onClick={closeAndRefresh} className="text-surface-400 hover:text-surface-600 transition-colors text-2xl">&times;</button>
                        </div>

                        {/* Modal Body */}
                        <div className="p-6 overflow-y-auto flex-1">
                            {/* Step 1: User */}
                            {modalStep === 'user' && (
                                <form onSubmit={handleCreateUser} className="space-y-4">
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="space-y-1">
                                            <label className="text-xs font-bold text-surface-500 uppercase tracking-wider">Nombre</label>
                                            <input type="text" required className="input w-full" placeholder="Juan"
                                                value={formData.nombre} onChange={e => setFormData({ ...formData, nombre: e.target.value })} />
                                        </div>
                                        <div className="space-y-1">
                                            <label className="text-xs font-bold text-surface-500 uppercase tracking-wider">Apellido</label>
                                            <input type="text" required className="input w-full" placeholder="Pérez"
                                                value={formData.apellido} onChange={e => setFormData({ ...formData, apellido: e.target.value })} />
                                        </div>
                                    </div>
                                    <div className="space-y-1">
                                        <label className="text-xs font-bold text-surface-500 uppercase tracking-wider">Email</label>
                                        <input type="email" required className="input w-full" placeholder="correo@ejemplo.com"
                                            value={formData.email} onChange={e => setFormData({ ...formData, email: e.target.value })} />
                                    </div>
                                    <div className="space-y-1">
                                        <label className="text-xs font-bold text-surface-500 uppercase tracking-wider">Teléfono</label>
                                        <input type="tel" className="input w-full" placeholder="+505 8888 8888"
                                            value={formData.telefono} onChange={e => setFormData({ ...formData, telefono: e.target.value })} />
                                    </div>
                                    <div className="pt-4 flex justify-end">
                                        <button type="submit" disabled={saving} className="btn btn-primary">
                                            {saving ? 'Guardando...' : 'Siguiente →'}
                                        </button>
                                    </div>
                                </form>
                            )}

                            {/* Step 2: Profile */}
                            {modalStep === 'profile' && (
                                <form onSubmit={handleCreateProfile} className="space-y-4">
                                    {/* Tipo persona toggle */}
                                    <div className="flex gap-3">
                                        {[
                                            { key: 'natural' as const, label: 'Persona Natural', icon: UserIcon, desc: 'Individuo' },
                                            { key: 'juridica' as const, label: 'Persona Jurídica', icon: Building2, desc: 'Empresa / Sociedad' },
                                        ].map(opt => (
                                            <button key={opt.key} type="button"
                                                onClick={() => setProfileForm({ ...profileForm, tipo_persona: opt.key })}
                                                className={`flex-1 p-4 rounded-xl border-2 text-left transition-all ${profileForm.tipo_persona === opt.key ? 'border-primary-500 bg-primary-50' : 'border-surface-200 hover:border-surface-300'}`}>
                                                <opt.icon className={`w-6 h-6 mb-2 ${profileForm.tipo_persona === opt.key ? 'text-primary-600' : 'text-surface-400'}`} />
                                                <p className="font-bold text-sm text-surface-800">{opt.label}</p>
                                                <p className="text-xs text-surface-500">{opt.desc}</p>
                                            </button>
                                        ))}
                                    </div>

                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="space-y-1">
                                            <label className="text-xs font-bold text-surface-500 uppercase tracking-wider">Cédula de Identidad</label>
                                            <input type="text" className="input w-full" placeholder="001-010190-0001A"
                                                value={profileForm.cedula_identidad} onChange={e => setProfileForm({ ...profileForm, cedula_identidad: e.target.value })} />
                                        </div>
                                        <div className="space-y-1">
                                            <label className="text-xs font-bold text-surface-500 uppercase tracking-wider">RUC</label>
                                            <input type="text" className="input w-full" placeholder="J0310000012345"
                                                value={profileForm.ruc} onChange={e => setProfileForm({ ...profileForm, ruc: e.target.value })} />
                                        </div>
                                    </div>

                                    {/* Juridica-specific fields */}
                                    {profileForm.tipo_persona === 'juridica' && (
                                        <div className="space-y-4 p-4 bg-violet-50/50 rounded-xl border border-violet-100">
                                            <h3 className="text-sm font-bold text-violet-700 flex items-center gap-2"><Building2 className="w-4 h-4" /> Datos de la Sociedad</h3>
                                            <div className="grid grid-cols-2 gap-4">
                                                <div className="space-y-1">
                                                    <label className="text-xs font-bold text-surface-500 uppercase tracking-wider">Razón Social</label>
                                                    <input type="text" className="input w-full" placeholder="Grupo Pérez S.A."
                                                        value={profileForm.razon_social} onChange={e => setProfileForm({ ...profileForm, razon_social: e.target.value })} />
                                                </div>
                                                <div className="space-y-1">
                                                    <label className="text-xs font-bold text-surface-500 uppercase tracking-wider">Nombre Comercial</label>
                                                    <input type="text" className="input w-full" placeholder="GrupoPérez"
                                                        value={profileForm.nombre_comercial} onChange={e => setProfileForm({ ...profileForm, nombre_comercial: e.target.value })} />
                                                </div>
                                                <div className="space-y-1">
                                                    <label className="text-xs font-bold text-surface-500 uppercase tracking-wider">Tipo de Sociedad</label>
                                                    <select className="input w-full" value={profileForm.tipo_sociedad}
                                                        onChange={e => setProfileForm({ ...profileForm, tipo_sociedad: e.target.value })}>
                                                        <option value="">Seleccionar...</option>
                                                        {Object.entries(tipoSociedadLabels).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                                                    </select>
                                                </div>
                                                <div className="space-y-1">
                                                    <label className="text-xs font-bold text-surface-500 uppercase tracking-wider">Actividad Económica</label>
                                                    <input type="text" className="input w-full" placeholder="Comercio mayorista"
                                                        value={profileForm.actividad_economica} onChange={e => setProfileForm({ ...profileForm, actividad_economica: e.target.value })} />
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="space-y-1">
                                            <label className="text-xs font-bold text-surface-500 uppercase tracking-wider">Dirección</label>
                                            <input type="text" className="input w-full" placeholder="Km 4.5 Carretera Norte"
                                                value={profileForm.direccion_domicilio} onChange={e => setProfileForm({ ...profileForm, direccion_domicilio: e.target.value })} />
                                        </div>
                                        <div className="space-y-1">
                                            <label className="text-xs font-bold text-surface-500 uppercase tracking-wider">Ciudad</label>
                                            <input type="text" className="input w-full" placeholder="Managua"
                                                value={profileForm.ciudad} onChange={e => setProfileForm({ ...profileForm, ciudad: e.target.value })} />
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="space-y-1">
                                            <label className="text-xs font-bold text-surface-500 uppercase tracking-wider">Segmento</label>
                                            <select className="input w-full" value={profileForm.segmento}
                                                onChange={e => setProfileForm({ ...profileForm, segmento: e.target.value })}>
                                                <option value="individual">Individual</option>
                                                <option value="pyme">PYME</option>
                                                <option value="corporativo">Corporativo</option>
                                                <option value="gobierno">Gobierno</option>
                                                <option value="ong">ONG</option>
                                            </select>
                                        </div>
                                        <div className="space-y-1">
                                            <label className="text-xs font-bold text-surface-500 uppercase tracking-wider">Riesgo</label>
                                            <select className="input w-full" value={profileForm.calificacion_riesgo}
                                                onChange={e => setProfileForm({ ...profileForm, calificacion_riesgo: e.target.value })}>
                                                <option value="bajo">Bajo</option>
                                                <option value="medio">Medio</option>
                                                <option value="alto">Alto</option>
                                            </select>
                                        </div>
                                    </div>

                                    <div className="pt-4 flex justify-end gap-3">
                                        <button type="button" onClick={closeAndRefresh} className="btn btn-ghost">Omitir</button>
                                        <button type="submit" disabled={saving} className="btn btn-primary">
                                            {saving ? 'Guardando...' : profileForm.tipo_persona === 'juridica' ? 'Siguiente → Apoderado' : 'Guardar Cliente'}
                                        </button>
                                    </div>
                                </form>
                            )}

                            {/* Step 3: Representative */}
                            {modalStep === 'representative' && (
                                <form onSubmit={handleAddRepresentative} className="space-y-4">
                                    <div className="p-3 bg-violet-50 rounded-lg border border-violet-100 text-sm text-violet-700 flex items-center gap-2">
                                        <Briefcase className="w-4 h-4" /> Registre el Apoderado General o Representante Legal de la sociedad.
                                    </div>

                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="space-y-1">
                                            <label className="text-xs font-bold text-surface-500 uppercase tracking-wider">Nombre Completo</label>
                                            <input type="text" required className="input w-full" placeholder="Roberto Martínez López"
                                                value={repForm.nombre_completo} onChange={e => setRepForm({ ...repForm, nombre_completo: e.target.value })} />
                                        </div>
                                        <div className="space-y-1">
                                            <label className="text-xs font-bold text-surface-500 uppercase tracking-wider">Cargo</label>
                                            <input type="text" className="input w-full" placeholder="Gerente General"
                                                value={repForm.cargo} onChange={e => setRepForm({ ...repForm, cargo: e.target.value })} />
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="space-y-1">
                                            <label className="text-xs font-bold text-surface-500 uppercase tracking-wider">Cédula</label>
                                            <input type="text" className="input w-full" placeholder="001-010190-0001A"
                                                value={repForm.cedula_identidad} onChange={e => setRepForm({ ...repForm, cedula_identidad: e.target.value })} />
                                        </div>
                                        <div className="space-y-1">
                                            <label className="text-xs font-bold text-surface-500 uppercase tracking-wider">Tipo de Poder</label>
                                            <select className="input w-full" value={repForm.tipo_poder}
                                                onChange={e => setRepForm({ ...repForm, tipo_poder: e.target.value })}>
                                                {Object.entries(tipoPoderLabels).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                                            </select>
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="space-y-1">
                                            <label className="text-xs font-bold text-surface-500 uppercase tracking-wider">N° de Escritura del Poder</label>
                                            <input type="text" className="input w-full" placeholder="15"
                                                value={repForm.numero_escritura} onChange={e => setRepForm({ ...repForm, numero_escritura: e.target.value })} />
                                        </div>
                                        <div className="space-y-1">
                                            <label className="text-xs font-bold text-surface-500 uppercase tracking-wider">Fecha de Otorgamiento</label>
                                            <input type="date" required className="input w-full"
                                                value={repForm.fecha_otorgamiento} onChange={e => setRepForm({ ...repForm, fecha_otorgamiento: e.target.value })} />
                                        </div>
                                    </div>

                                    <div className="space-y-1">
                                        <label className="text-xs font-bold text-surface-500 uppercase tracking-wider">Notario Autorizante</label>
                                        <input type="text" className="input w-full" placeholder="Lic. Ana María González"
                                            value={repForm.notario_autorizante} onChange={e => setRepForm({ ...repForm, notario_autorizante: e.target.value })} />
                                    </div>

                                    <div className="space-y-1">
                                        <label className="text-xs font-bold text-surface-500 uppercase tracking-wider">Alcance de Facultades</label>
                                        <textarea className="input w-full h-20 resize-none" placeholder="Facultado para representar a la sociedad en todos los actos de administración..."
                                            value={repForm.alcance_facultades} onChange={e => setRepForm({ ...repForm, alcance_facultades: e.target.value })} />
                                    </div>

                                    <div className="pt-4 flex justify-end gap-3">
                                        <button type="button" onClick={closeAndRefresh} className="btn btn-ghost">Omitir</button>
                                        <button type="submit" disabled={saving} className="btn btn-primary flex items-center gap-2">
                                            {saving ? 'Guardando...' : <><CheckCircle2 className="w-4 h-4" /> Finalizar Registro</>}
                                        </button>
                                    </div>
                                </form>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

function InfoField({ label, value }: { label: string; value?: string | null }) {
    return (
        <div>
            <p className="text-[10px] font-bold text-surface-400 uppercase tracking-wider">{label}</p>
            <p className="text-sm text-surface-700 mt-0.5">{value || '—'}</p>
        </div>
    );
}
