'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
    ArrowLeft, Clock, Users, FileText, Activity, Plus, MoreVertical,
    Edit2, History, StickyNote, Scale, BookOpen, AlertCircle, CheckCircle,
    Send, Shield, Gavel, Calendar, MapPin, User, ChevronRight, Flag,
    MessageSquare, Target, Lightbulb, ListChecks
} from 'lucide-react';
import { caseService } from '@/services/caseService';
import { Expediente, TIPOS_SERVICIO } from '@/types/case';
import { useToast } from '@/components/ui/ToastProvider';
import DeadlineList from '@/components/deadlines/DeadlineList';
import DocumentList from '@/components/documents/DocumentList';
import CaseTheoryAnalysis from '@/components/cases/CaseTheoryAnalysis';
import CaseStatusToggle from '@/components/cases/CaseStatusToggle';
import CaseStageToggle from '@/components/cases/CaseStageToggle';
import WorkflowProgressBar from '@/components/cases/WorkflowProgressBar';
import DiscussionPanel from '@/components/cases/DiscussionPanel';
import ApprovalsPanel from '@/components/cases/ApprovalsPanel';
import TaskPanel from '@/components/cases/TaskPanel';
import api from '@/lib/api';

// === CONSTANTES POR MATERIA ===
const RAMO_LABELS: Record<string, string> = {
    civil: 'Civil', penal: 'Penal', familia: 'Familia', laboral: 'Laboral',
    mercantil: 'Mercantil', constitucional: 'Constitucional', sucesiones: 'Sucesiones',
    administrativo: 'Administrativo',
};

const RAMO_COLORS: Record<string, string> = {
    civil: 'bg-blue-100 text-blue-700',
    penal: 'bg-red-100 text-red-700',
    familia: 'bg-pink-100 text-pink-700',
    laboral: 'bg-amber-100 text-amber-700',
    mercantil: 'bg-emerald-100 text-emerald-700',
    constitucional: 'bg-purple-100 text-purple-700',
    sucesiones: 'bg-stone-100 text-stone-700',
    administrativo: 'bg-cyan-100 text-cyan-700',
};

const EVENT_TYPE_CONFIG: Record<string, { icon: string; color: string; label: string }> = {
    escrito_presentado: { icon: '✍️', color: 'bg-blue-500', label: 'Escrito Presentado' },
    escrito_contraparte: { icon: '📩', color: 'bg-orange-500', label: 'Escrito Contraparte' },
    providencia: { icon: '⚖️', color: 'bg-purple-500', label: 'Providencia' },
    auto: { icon: '📋', color: 'bg-indigo-500', label: 'Auto Judicial' },
    sentencia: { icon: '🏛️', color: 'bg-red-600', label: 'Sentencia' },
    audiencia: { icon: '🎤', color: 'bg-green-500', label: 'Audiencia' },
    notificacion_judicial: { icon: '📬', color: 'bg-yellow-500', label: 'Notificación' },
    recurso_interpuesto: { icon: '📤', color: 'bg-blue-600', label: 'Recurso Interpuesto' },
    recurso_contraparte: { icon: '📥', color: 'bg-orange-600', label: 'Recurso Contraparte' },
    incidente: { icon: '⚡', color: 'bg-amber-600', label: 'Incidente Procesal' },
    excepcion: { icon: '🛡️', color: 'bg-slate-500', label: 'Excepción' },
    medida_cautelar: { icon: '🔒', color: 'bg-red-500', label: 'Medida Cautelar' },
    diligencia: { icon: '🔍', color: 'bg-teal-500', label: 'Diligencia' },
    prueba_admitida: { icon: '✅', color: 'bg-green-600', label: 'Prueba Admitida' },
    prueba_evacuada: { icon: '📊', color: 'bg-emerald-600', label: 'Prueba Evacuada' },
    acuerdo: { icon: '🤝', color: 'bg-lime-500', label: 'Acuerdo' },
    peritaje: { icon: '🔬', color: 'bg-violet-500', label: 'Peritaje' },
    nota_interna: { icon: '📝', color: 'bg-gray-400', label: 'Nota Interna' },
    otro: { icon: '📌', color: 'bg-gray-500', label: 'Otro' },
};

const NOTE_TYPE_CONFIG: Record<string, { icon: string; label: string; color: string }> = {
    estrategia: { icon: '🎯', label: 'Estrategia', color: 'bg-blue-100 text-blue-700' },
    investigacion: { icon: '🔍', label: 'Investigación', color: 'bg-green-100 text-green-700' },
    recordatorio: { icon: '⏰', label: 'Recordatorio', color: 'bg-amber-100 text-amber-700' },
    reunion_cliente: { icon: '👤', label: 'Reunión Cliente', color: 'bg-purple-100 text-purple-700' },
    reunion_equipo: { icon: '👥', label: 'Reunión Equipo', color: 'bg-indigo-100 text-indigo-700' },
    observacion: { icon: '💬', label: 'Observación', color: 'bg-gray-100 text-gray-700' },
    contraargumento: { icon: '⚔️', label: 'Contraargumento', color: 'bg-red-100 text-red-700' },
    jurisprudencia: { icon: '📚', label: 'Jurisprudencia', color: 'bg-emerald-100 text-emerald-700' },
};

interface Actuacion {
    id: string; tipo: string; titulo: string; descripcion?: string;
    fecha_evento: string; resultado?: string; base_legal?: string;
    documento_ids: string[]; estado: string; registrado_por_id?: string;
    analisis_ia?: string; created_at: string;
}

interface Nota {
    id: string; tipo: string; contenido: string; es_privada: boolean;
    prioridad: string; autor_id: string; created_at: string;
}

export default function CaseDetailPage({ params }: { params: { id: string } }) {
    const [caseData, setCaseData] = useState<Expediente | null>(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('timeline');
    const [showActionMenu, setShowActionMenu] = useState(false);

    // Timeline data
    const [actuaciones, setActuaciones] = useState<Actuacion[]>([]);
    const [loadingTimeline, setLoadingTimeline] = useState(false);

    // Notes data
    const [notas, setNotas] = useState<Nota[]>([]);
    const [loadingNotas, setLoadingNotas] = useState(false);

    // Workflow stages
    const [stages, setStages] = useState<any[]>([]);
    const [loadingStages, setLoadingStages] = useState(false);

    // New actuacion form
    const [showNewActuacion, setShowNewActuacion] = useState(false);
    const [newActuacion, setNewActuacion] = useState({
        tipo: 'escrito_presentado', titulo: '', descripcion: '', base_legal: '',
        fecha_evento: new Date().toISOString().slice(0, 16), resultado: '',
    });

    // New note form
    const [showNewNota, setShowNewNota] = useState(false);
    const [newNota, setNewNota] = useState({ tipo: 'observacion', contenido: '', es_privada: false, prioridad: 'normal' });

    const toast = useToast();
    const router = useRouter();

    useEffect(() => {
        if (params.id) loadCase(params.id);
    }, [params.id]);

    useEffect(() => {
        if (caseData) {
            if (caseData.tipo_servicio && caseData.tipo_servicio !== 'litigio') {
                loadStages(undefined, caseData.tipo_servicio, caseData.tipo_proceso);
            } else if (caseData.ramo) {
                loadStages(caseData.ramo, undefined, caseData.tipo_proceso);
            }
        }
    }, [caseData?.ramo, caseData?.tipo_servicio, caseData?.tipo_proceso]);

    useEffect(() => {
        if (caseData) {
            if (activeTab === 'timeline') loadTimeline();
            if (activeTab === 'notas') loadNotas();
        }
    }, [activeTab, caseData]);

    const loadCase = async (id: string) => {
        setLoading(true);
        try {
            const data = await caseService.getById(id);
            setCaseData(data);
        } catch (error) {
            console.error('Failed to load case', error);
        } finally {
            setLoading(false);
        }
    };

    const loadTimeline = async () => {
        setLoadingTimeline(true);
        try {
            const { data } = await api.get(`/cases/${params.id}/actuaciones?size=100`);
            setActuaciones(data.items || []);
        } catch (e) { console.error(e); }
        finally { setLoadingTimeline(false); }
    };

    const loadStages = async (ramo?: string, tipo_servicio?: string, tipo_proceso?: string) => {
        setLoadingStages(true);
        try {
            const params = new URLSearchParams();
            if (ramo) params.append('ramo', ramo);
            if (tipo_servicio) params.append('tipo_servicio', tipo_servicio);
            if (tipo_proceso) params.append('tipo_proceso', tipo_proceso);
            const { data } = await api.get(`/cases/workflow/stages?${params.toString()}`);
            setStages(data || []);
        } catch (e) { console.error('Error loading stages', e); }
        finally { setLoadingStages(false); }
    };

    const loadNotas = async () => {
        setLoadingNotas(true);
        try {
            const { data } = await api.get(`/cases/${params.id}/notes`);
            setNotas(data || []);
        } catch (e) { console.error(e); }
        finally { setLoadingNotas(false); }
    };

    const handleCreateActuacion = async () => {
        try {
            await api.post(`/cases/${params.id}/actuaciones`, {
                ...newActuacion,
                fecha_evento: new Date(newActuacion.fecha_evento).toISOString(),
            });
            toast.success('Actuación registrada exitosamente');
            setShowNewActuacion(false);
            setNewActuacion({ tipo: 'escrito_presentado', titulo: '', descripcion: '', base_legal: '', fecha_evento: new Date().toISOString().slice(0, 16), resultado: '' });
            loadTimeline();
        } catch (e) { toast.error('Error al registrar actuación'); }
    };

    const handleCreateNota = async () => {
        try {
            await api.post(`/cases/${params.id}/notas`, newNota);
            toast.success('Nota creada exitosamente');
            setShowNewNota(false);
            setNewNota({ tipo: 'observacion', contenido: '', es_privada: false, prioridad: 'normal' });
            loadNotas();
        } catch (e) { toast.error('Error al crear nota'); }
    };

    if (loading) return <div className="p-8 text-center">Cargando expediente...</div>;
    if (!caseData) return <div className="p-8 text-center">Expediente no encontrado</div>;

    const svcConfig = TIPOS_SERVICIO.find(s => s.value === caseData.tipo_servicio);
    const ramoLabel = svcConfig ? svcConfig.label : (RAMO_LABELS[caseData.ramo || ''] || caseData.ramo || caseData.tipo_servicio);
    const ramoColor = svcConfig ? svcConfig.color : (RAMO_COLORS[caseData.ramo || ''] || 'bg-gray-100 text-gray-700');

    const tabs = [
        { id: 'timeline', label: 'Timeline', icon: History, count: actuaciones.length },
        { id: 'general', label: 'Información', icon: BookOpen },
        { id: 'partes', label: 'Partes', icon: Users, count: caseData.partes?.length || 0 },
        { id: 'tareas', label: 'Tareas', icon: ListChecks },
        { id: 'plazos', label: 'Plazos', icon: Clock },
        { id: 'documentos', label: 'Documentos', icon: FileText },
        { id: 'discusiones', label: 'Discusiones', icon: MessageSquare },
        { id: 'aprobaciones', label: 'Aprobaciones', icon: CheckCircle },
        { id: 'notas', label: 'Notas Internas', icon: StickyNote, count: notas.length },
        { id: 'teoria', label: 'Teoría del Caso', icon: Target },
        { id: 'ia', label: 'IA', icon: Lightbulb, badge: 'LAA' },
    ];

    return (
        <div className="pb-12 space-y-6">
            {/* === HEADER MEJORADO === */}
            <div className="flex flex-col gap-4">
                <Link href="/dashboard/cases" className="text-surface-500 hover:text-primary-600 flex items-center gap-2 w-fit">
                    <ArrowLeft className="w-4 h-4" /> Volver al listado
                </Link>

                <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
                    <div className="flex-1">
                        <div className="flex items-center gap-3 mb-1 flex-wrap">
                            <h1 className="text-2xl font-bold text-surface-900">{caseData.numero_interno || 'Sin Número'}</h1>
                            {/* Service type badge */}
                            <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${ramoColor}`}>
                                {svcConfig ? `${svcConfig.icon} ${ramoLabel}` : ramoLabel}
                            </span>
                            {/* Prioridad badge */}
                            <span className={`px-2 py-0.5 rounded text-xs font-medium uppercase ${
                                caseData.prioridad === 'urgente' ? 'bg-red-100 text-red-700 animate-pulse' :
                                caseData.prioridad === 'alta' ? 'bg-orange-100 text-orange-700' :
                                caseData.prioridad === 'normal' ? 'bg-blue-50 text-blue-600' :
                                'bg-surface-100 text-surface-500'
                            }`}>
                                <Flag className="w-3 h-3 inline mr-1" />{caseData.prioridad}
                            </span>
                            
                            {/* Etapa Procesal (INTELIGENCIA LEGAL) */}
                            <CaseStageToggle 
                                caseId={caseData.id}
                                ramo={caseData.ramo}
                                tipoServicio={caseData.tipo_servicio}
                                tipoProceso={caseData.tipo_proceso}
                                currentStageId={caseData.etapa_actual_id}
                                onStageChange={(newId) => {
                                    setCaseData({...caseData, etapa_actual_id: newId});
                                    loadTimeline();
                                }}
                            />

                            {/* Estado Procesal (GESTIÓN INTERNA) */}
                            <CaseStatusToggle 
                                caseId={caseData.id} 
                                currentStatusId={caseData.estado_id} 
                                onStatusChange={(newId) => {
                                    setCaseData({...caseData, estado_id: newId});
                                    loadTimeline(); // Refrescar timeline con el historial
                                }}
                            />
                        </div>
                        <h2 className="text-lg text-surface-700 font-medium">{caseData.resumen || 'Sin resumen'}</h2>
                        <div className="flex items-center gap-4 mt-2 text-sm text-surface-500 flex-wrap">
                            {caseData.numero_causa && (
                                <div className="flex items-center gap-1.5">
                                    <Gavel className="w-4 h-4" /> {caseData.numero_causa}
                                </div>
                            )}
                            {caseData.juzgado && (
                                <div className="flex items-center gap-1.5">
                                    <MapPin className="w-4 h-4" /> {caseData.juzgado}
                                </div>
                            )}
                            {caseData.materia_especifica && (
                                <div className="flex items-center gap-1.5">
                                    <Activity className="w-4 h-4" /> {caseData.materia_especifica}
                                </div>
                            )}
                            {caseData.fecha_apertura && (
                                <div className="flex items-center gap-1.5">
                                    <Calendar className="w-4 h-4" /> Desde {new Date(caseData.fecha_apertura).toLocaleDateString()}
                                </div>
                            )}
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <button onClick={() => router.push(`/dashboard/cases/${params.id}/edit`)}
                            className="btn btn-outline flex items-center gap-2">
                            <Edit2 className="w-4 h-4" /> Editar
                        </button>
                        <div className="relative">
                            <button onClick={() => setShowActionMenu(!showActionMenu)}
                                className="btn btn-primary flex items-center gap-2">
                                <Plus className="w-4 h-4" /> Nueva Actuación
                            </button>
                            {showActionMenu && (
                                <>
                                    <div className="fixed inset-0 z-10" onClick={() => setShowActionMenu(false)}></div>
                                    <div className="absolute right-0 mt-2 w-60 bg-white rounded-lg shadow-xl border border-surface-200 z-20 py-1 overflow-hidden animate-slide-up">
                                        <button onClick={() => { setActiveTab('timeline'); setShowNewActuacion(true); setShowActionMenu(false); }}
                                            className="w-full text-left px-4 py-2.5 text-sm text-surface-700 hover:bg-surface-50 flex items-center gap-2">
                                            <History className="w-4 h-4 text-blue-500" /> Registrar Actuación
                                        </button>
                                        <button onClick={() => { setActiveTab('notas'); setShowNewNota(true); setShowActionMenu(false); }}
                                            className="w-full text-left px-4 py-2.5 text-sm text-surface-700 hover:bg-surface-50 flex items-center gap-2">
                                            <MessageSquare className="w-4 h-4 text-amber-500" /> Nueva Discusión (Nota)
                                        </button>
                                        <button onClick={() => { setActiveTab('plazos'); setShowActionMenu(false); }}
                                            className="w-full text-left px-4 py-2.5 text-sm text-surface-700 hover:bg-surface-50 flex items-center gap-2">
                                            <Clock className="w-4 h-4 text-red-500" /> Registrar Plazo
                                        </button>
                                        <button onClick={() => { setActiveTab('documentos'); setShowActionMenu(false); }}
                                            className="w-full text-left px-4 py-2.5 text-sm text-surface-700 hover:bg-surface-50 flex items-center gap-2">
                                            <FileText className="w-4 h-4 text-green-500" /> Subir Documento
                                        </button>
                                        <button onClick={() => { setActiveTab('partes'); setShowActionMenu(false); }}
                                            className="w-full text-left px-4 py-2.5 text-sm text-surface-700 hover:bg-surface-50 flex items-center gap-2">
                                            <Users className="w-4 h-4 text-purple-500" /> Agregar Parte
                                        </button>
                                    </div>
                                </>
                            )}
                        </div>
                    </div>
                </div>
                
                {/* --- Barra de Progreso de Flujo Procesal (MEJORADA) --- */}
                {stages.length > 0 && (
                    <WorkflowProgressBar 
                        stages={stages} 
                        currentStageId={caseData.etapa_actual_id} 
                        tipoProceso={caseData.tipo_proceso} 
                    />
                )}
            </div>

            {/* === TABS === */}
            <div className="border-b border-surface-200 overflow-x-auto">
                <nav className="flex gap-1 min-w-max">
                    {tabs.map(tab => (
                        <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                            className={`pb-3 px-3 text-sm font-medium border-b-2 transition-colors flex items-center gap-1.5 whitespace-nowrap ${
                                activeTab === tab.id
                                    ? tab.id === 'ia' ? 'border-accent-400 text-accent-500' : 'border-primary-500 text-primary-600'
                                    : 'border-transparent text-surface-500 hover:text-surface-700'
                            }`}>
                            <tab.icon className="w-4 h-4" />
                            {tab.label}
                            {tab.count !== undefined && tab.count > 0 && (
                                <span className="ml-1 px-1.5 py-0.5 rounded-full bg-surface-100 text-xs">{tab.count}</span>
                            )}
                            {tab.badge && (
                                <span className="ml-1 badge bg-accent-400/10 text-accent-500 text-[10px]">{tab.badge}</span>
                            )}
                        </button>
                    ))}
                </nav>
            </div>

            {/* === TAB CONTENT === */}
            <div className="animate-fade-in">

                {/* ====== TIMELINE ====== */}
                {activeTab === 'timeline' && (
                    <div className="space-y-4">
                        <div className="flex justify-between items-center">
                            <h3 className="font-semibold text-surface-800">Actuaciones Procesales</h3>
                            <button onClick={() => setShowNewActuacion(true)} className="btn btn-sm btn-primary gap-1">
                                <Plus className="w-4 h-4" /> Nueva Actuación
                            </button>
                        </div>

                        {/* Form inline para nueva actuación */}
                        {showNewActuacion && (
                            <div className="card p-6 border-2 border-primary-200 bg-primary-50/30 space-y-4">
                                <h4 className="font-semibold text-surface-800 flex items-center gap-2">
                                    <Plus className="w-4 h-4 text-primary-500" /> Registrar Actuación Procesal
                                </h4>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-surface-700 mb-1">Tipo de Actuación *</label>
                                        <select value={newActuacion.tipo} onChange={e => setNewActuacion(p => ({...p, tipo: e.target.value}))}
                                            className="input w-full">
                                            {Object.entries(EVENT_TYPE_CONFIG).map(([key, cfg]) => (
                                                <option key={key} value={key}>{cfg.icon} {cfg.label}</option>
                                            ))}
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-surface-700 mb-1">Fecha y Hora *</label>
                                        <input type="datetime-local" value={newActuacion.fecha_evento}
                                            onChange={e => setNewActuacion(p => ({...p, fecha_evento: e.target.value}))}
                                            className="input w-full" />
                                    </div>
                                    <div className="md:col-span-2">
                                        <label className="block text-sm font-medium text-surface-700 mb-1">Título *</label>
                                        <input value={newActuacion.titulo} onChange={e => setNewActuacion(p => ({...p, titulo: e.target.value}))}
                                            className="input w-full" placeholder="Ej: Contestación de demanda presentada por contraparte" />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-surface-700 mb-1">Descripción</label>
                                        <textarea value={newActuacion.descripcion} onChange={e => setNewActuacion(p => ({...p, descripcion: e.target.value}))}
                                            className="input w-full" rows={3} placeholder="Detalle de la actuación..." />
                                    </div>
                                    <div className="space-y-4">
                                        <div>
                                            <label className="block text-sm font-medium text-surface-700 mb-1">Base Legal</label>
                                            <input value={newActuacion.base_legal} onChange={e => setNewActuacion(p => ({...p, base_legal: e.target.value}))}
                                                className="input w-full" placeholder="Ej: Art. 234 CPC" />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-surface-700 mb-1">Resultado</label>
                                            <input value={newActuacion.resultado} onChange={e => setNewActuacion(p => ({...p, resultado: e.target.value}))}
                                                className="input w-full" placeholder="Ej: Se admitió la demanda" />
                                        </div>
                                    </div>
                                </div>
                                <div className="flex justify-end gap-2 pt-2">
                                    <button onClick={() => setShowNewActuacion(false)} className="btn btn-outline">Cancelar</button>
                                    <button onClick={handleCreateActuacion} disabled={!newActuacion.titulo}
                                        className="btn btn-primary disabled:opacity-50 flex items-center gap-1">
                                        <Send className="w-4 h-4" /> Registrar
                                    </button>
                                </div>
                            </div>
                        )}

                        {/* Timeline visual */}
                        {loadingTimeline ? (
                            <div className="text-center py-8 text-surface-500">Cargando timeline...</div>
                        ) : actuaciones.length === 0 ? (
                            <div className="card p-12 text-center">
                                <History className="w-12 h-12 mx-auto text-surface-300 mb-3" />
                                <h4 className="font-medium text-surface-700 mb-1">Sin actuaciones registradas</h4>
                                <p className="text-sm text-surface-500 mb-4">
                                    Registre la primera actuación procesal para comenzar el timeline del caso.
                                </p>
                                <button onClick={() => setShowNewActuacion(true)} className="btn btn-primary btn-sm gap-1">
                                    <Plus className="w-4 h-4" /> Primera Actuación
                                </button>
                            </div>
                        ) : (
                            <div className="relative pl-8 border-l-2 border-surface-200 space-y-6">
                                {actuaciones.map((act) => {
                                    const config = EVENT_TYPE_CONFIG[act.tipo] || EVENT_TYPE_CONFIG.otro;
                                    return (
                                        <div key={act.id} className="relative group">
                                            {/* Dot */}
                                            <div className={`absolute -left-[25px] w-4 h-4 rounded-full ${config.color} ring-4 ring-white`} />
                                            {/* Card */}
                                            <div className="card p-4 hover:shadow-md transition-shadow">
                                                <div className="flex items-start justify-between gap-4">
                                                    <div className="flex-1 min-w-0">
                                                        <div className="flex items-center gap-2 mb-1 flex-wrap">
                                                            <span className="text-base">{config.icon}</span>
                                                            <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-surface-100 text-surface-600">
                                                                {config.label}
                                                            </span>
                                                            {act.base_legal && (
                                                                <span className="text-xs text-primary-600 font-mono">{act.base_legal}</span>
                                                            )}
                                                        </div>
                                                        <h4 className="font-semibold text-surface-900">{act.titulo}</h4>
                                                        {act.descripcion && (
                                                            <p className="text-sm text-surface-600 mt-1 whitespace-pre-wrap line-clamp-3">{act.descripcion}</p>
                                                        )}
                                                        {act.resultado && (
                                                            <div className="mt-2 text-sm bg-green-50 text-green-700 px-3 py-1.5 rounded-lg inline-flex items-center gap-1">
                                                                <CheckCircle className="w-3.5 h-3.5" /> {act.resultado}
                                                            </div>
                                                        )}
                                                    </div>
                                                    <div className="text-right shrink-0">
                                                        <span className="text-sm font-medium text-surface-700">
                                                            {new Date(act.fecha_evento).toLocaleDateString('es-NI', { day: 'numeric', month: 'short', year: 'numeric' })}
                                                        </span>
                                                        <br/>
                                                        <span className="text-xs text-surface-400">
                                                            {new Date(act.fecha_evento).toLocaleTimeString('es-NI', { hour: '2-digit', minute: '2-digit' })}
                                                        </span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                    </div>
                )}

                {/* ====== INFORMACIÓN GENERAL ====== */}
                {activeTab === 'general' && (
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        <div className="lg:col-span-2 space-y-6">
                            {/* Datos del proceso */}
                            <div className="card p-6 space-y-5">
                                <h3 className="font-semibold text-surface-800 border-b border-surface-100 pb-2 flex items-center gap-2">
                                    <Gavel className="w-4 h-4 text-primary-500" /> Datos del Proceso
                                </h3>
                                <div className="grid grid-cols-2 md:grid-cols-3 gap-y-5 gap-x-4">
                                    <div><label className="text-xs text-surface-500 block">Juzgado</label>
                                        <p className="text-surface-900 font-medium">{caseData.juzgado || '—'}</p></div>
                                    <div><label className="text-xs text-surface-500 block">Juez</label>
                                        <p className="text-surface-900 font-medium">{caseData.juez || '—'}</p></div>
                                    <div><label className="text-xs text-surface-500 block">Secretario</label>
                                        <p className="text-surface-900 font-medium">{caseData.secretario || '—'}</p></div>
                                    <div><label className="text-xs text-surface-500 block">Fecha Apertura</label>
                                        <p className="text-surface-900 font-medium">
                                            {caseData.fecha_apertura ? new Date(caseData.fecha_apertura).toLocaleDateString() : '—'}
                                        </p></div>
                                    <div><label className="text-xs text-surface-500 block">Número de Causa</label>
                                        <p className="text-surface-900 font-medium">{caseData.numero_causa || '—'}</p></div>
                                    <div><label className="text-xs text-surface-500 block">Materia Específica</label>
                                        <p className="text-surface-900 font-medium">{caseData.materia_especifica || '—'}</p></div>
                                </div>
                            </div>

                            {/* Valoración económica */}
                            <div className="card p-6 space-y-5">
                                <h3 className="font-semibold text-surface-800 border-b border-surface-100 pb-2 flex items-center gap-2">
                                    <Scale className="w-4 h-4 text-primary-500" /> Valoración Económica
                                </h3>
                                <div className="grid grid-cols-2 gap-y-4">
                                    <div><label className="text-xs text-surface-500 block">Cuantía Estimada</label>
                                        <p className="text-surface-900 font-medium text-lg">
                                            {caseData.moneda} {caseData.valor_estimado?.toLocaleString() || '0.00'}
                                        </p></div>
                                    <div><label className="text-xs text-surface-500 block">Prioridad</label>
                                        <span className={`inline-block px-2.5 py-1 rounded text-xs font-medium uppercase ${
                                            caseData.prioridad === 'urgente' ? 'bg-red-100 text-red-700' :
                                            caseData.prioridad === 'alta' ? 'bg-orange-100 text-orange-700' :
                                            'bg-blue-100 text-blue-700'
                                        }`}>{caseData.prioridad}</span></div>
                                </div>
                            </div>

                            {/* Datos específicos de la materia */}
                            {(caseData as any).datos_materia && Object.keys((caseData as any).datos_materia).length > 0 && (
                                <div className="card p-6 space-y-5">
                                    <h3 className="font-semibold text-surface-800 border-b border-surface-100 pb-2 flex items-center gap-2">
                                        <BookOpen className="w-4 h-4 text-primary-500" /> Datos Específicos — {ramoLabel}
                                    </h3>
                                    <div className="grid grid-cols-2 gap-y-4">
                                        {Object.entries((caseData as any).datos_materia).map(([key, val]) => (
                                            <div key={key}>
                                                <label className="text-xs text-surface-500 block capitalize">{key.replace(/_/g, ' ')}</label>
                                                <p className="text-surface-900 font-medium">{String(val) || '—'}</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Sidebar derecho */}
                        <div className="space-y-4">
                            {/* IA Card */}
                            <div className="card p-5 bg-gradient-to-br from-accent-50 to-white border-accent-100">
                                <h3 className="font-semibold text-accent-700 mb-3 flex items-center gap-2">
                                    <Lightbulb className="w-4 h-4" /> Análisis Legal IA
                                </h3>
                                <p className="text-sm text-surface-700 leading-relaxed">
                                    {caseData.observaciones_ia || 'No hay análisis generado aún.'}
                                </p>
                                <button onClick={() => setActiveTab('ia')}
                                    className="btn btn-sm bg-white border border-accent-200 text-accent-700 mt-3 hover:bg-accent-50 w-full">
                                    Generar Análisis con IA
                                </button>
                            </div>

                            {/* Resumen rápido */}
                            <div className="card p-5 space-y-3">
                                <h3 className="font-semibold text-surface-800 text-sm">Resumen Rápido</h3>
                                <div className="space-y-2 text-sm">
                                    <div className="flex justify-between">
                                        <span className="text-surface-500">Partes</span>
                                        <span className="font-medium">{caseData.partes?.length || 0}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-surface-500">Actuaciones</span>
                                        <span className="font-medium">{actuaciones.length}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-surface-500">Notas</span>
                                        <span className="font-medium">{notas.length}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* ====== BÓVEDA DE DISCUSIÓN / NOTAS ====== */}
                {activeTab === 'notas' && (
                    <div className="space-y-4">
                        <div className="flex justify-between items-center text-white bg-surface-900 -mx-4 -mt-4 p-6 sm:mx-0 sm:mt-0 sm:rounded-xl shadow-sm">
                            <div className="flex items-center gap-3">
                                <div className="p-3 bg-surface-800 rounded-lg"><MessageSquare className="w-6 h-6 text-primary-400" /></div>
                                <div>
                                    <h3 className="font-bold text-lg">Bóveda de Discusión</h3>
                                    <p className="text-sm text-surface-300">Hilos privados y registros de colaboración del equipo</p>
                                </div>
                            </div>
                            <button onClick={() => setShowNewNota(true)} className="btn btn-primary gap-1 shrink-0">
                                <Plus className="w-4 h-4" /> Nuevo Mensaje
                            </button>
                        </div>

                        {showNewNota && (
                            <div className="card p-6 border-2 border-amber-200 bg-amber-50/30 space-y-4">
                                <h4 className="font-semibold text-surface-800 flex items-center gap-2">
                                    <StickyNote className="w-4 h-4 text-amber-500" /> Nueva Nota Interna
                                </h4>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-surface-700 mb-1">Tipo</label>
                                        <select value={newNota.tipo} onChange={e => setNewNota(p => ({...p, tipo: e.target.value}))} className="input w-full">
                                            {Object.entries(NOTE_TYPE_CONFIG).map(([key, cfg]) => (
                                                <option key={key} value={key}>{cfg.icon} {cfg.label}</option>
                                            ))}
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-surface-700 mb-1">Prioridad</label>
                                        <select value={newNota.prioridad} onChange={e => setNewNota(p => ({...p, prioridad: e.target.value}))} className="input w-full">
                                            <option value="normal">Normal</option>
                                            <option value="importante">⚠️ Importante</option>
                                            <option value="urgente">🔴 Urgente</option>
                                        </select>
                                    </div>
                                    <div className="flex items-end">
                                        <label className="flex items-center gap-2 cursor-pointer">
                                            <input type="checkbox" checked={newNota.es_privada}
                                                onChange={e => setNewNota(p => ({...p, es_privada: e.target.checked}))}
                                                className="rounded border-surface-300" />
                                            <span className="text-sm text-surface-600">🔒 Solo visible para mí</span>
                                        </label>
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-surface-700 mb-1">Contenido *</label>
                                    <textarea value={newNota.contenido} onChange={e => setNewNota(p => ({...p, contenido: e.target.value}))}
                                        className="input w-full" rows={4} placeholder="Escriba su nota, observación, o análisis estratégico..." />
                                </div>
                                <div className="flex justify-end gap-2">
                                    <button onClick={() => setShowNewNota(false)} className="btn btn-outline">Cancelar</button>
                                    <button onClick={handleCreateNota} disabled={!newNota.contenido}
                                        className="btn btn-primary disabled:opacity-50">Guardar Nota</button>
                                </div>
                            </div>
                        )}

                        {loadingNotas ? (
                            <div className="text-center py-8 text-surface-500">Cargando notas...</div>
                        ) : notas.length === 0 ? (
                            <div className="card p-12 text-center">
                                <StickyNote className="w-12 h-12 mx-auto text-surface-300 mb-3" />
                                <h4 className="font-medium text-surface-700 mb-1">Sin notas internas</h4>
                                <p className="text-sm text-surface-500 mb-4">
                                    Registre estrategias, observaciones, o minutas de reunión con el cliente.
                                </p>
                                <button onClick={() => setShowNewNota(true)} className="btn btn-primary btn-sm gap-1">
                                    <Plus className="w-4 h-4" /> Primera Nota
                                </button>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {notas.map((nota: any) => {
                                    const cfg = NOTE_TYPE_CONFIG[nota.tipo] || NOTE_TYPE_CONFIG.observacion;
                                    return (
                                        <div key={nota.id} className={`card p-5 ${nota.prioridad === 'urgente' ? 'border-l-4 border-l-red-500' : nota.prioridad === 'importante' ? 'border-l-4 border-l-amber-400' : 'border-l-4 border-l-surface-200'}`}>
                                            <div className="flex items-start gap-4">
                                                {nota.autor_foto ? (
                                                    <img src={nota.autor_foto} alt="Author" className="w-10 h-10 rounded-full object-cover shrink-0" />
                                                ) : (
                                                    <div className="w-10 h-10 rounded-full bg-surface-100 flex items-center justify-center shrink-0 border border-surface-200">
                                                        <User className="w-5 h-5 text-surface-400" />
                                                    </div>
                                                )}
                                                <div className="flex-1 min-w-0">
                                                    <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-2">
                                                        <div className="flex items-center gap-2 flex-wrap">
                                                            <span className="font-semibold text-surface-900">{nota.autor_nombre || 'Sistema'}</span>
                                                            <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${cfg.color}`}>
                                                                {cfg.icon} {cfg.label}
                                                            </span>
                                                            {nota.es_privada && (
                                                                <span className="text-[10px] bg-slate-100 text-slate-500 px-2 py-0.5 rounded-full uppercase font-bold flex items-center gap-1"><Shield className="w-3 h-3" /> Equipo Interno</span>
                                                            )}
                                                        </div>
                                                        <span className="text-xs text-surface-400 mt-1 sm:mt-0 shrink-0">
                                                            {new Date(nota.created_at).toLocaleString('es-NI', { dateStyle: 'medium', timeStyle: 'short' })}
                                                        </span>
                                                    </div>
                                                    <div className="bg-surface-50 rounded-lg p-4 text-sm text-surface-800 whitespace-pre-wrap leading-relaxed border border-surface-100">
                                                        {nota.contenido}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                    </div>
                )}

                {/* ====== TEORÍA DEL CASO ====== */}
                {activeTab === 'teoria' && (
                    <CaseTheoryTab caseId={params.id} ramo={caseData.ramo} />
                )}

                {/* ====== PARTES (existente, mejorado) ====== */}
                {activeTab === 'partes' && (
                    <div className="card overflow-hidden">
                        <div className="p-4 border-b border-surface-200 flex justify-between items-center bg-surface-50">
                            <h3 className="font-semibold text-surface-800 flex items-center gap-2">
                                <Users className="w-4 h-4 text-primary-500" /> Sujetos Procesales
                            </h3>
                            <button className="btn btn-sm btn-outline gap-2"><Plus className="w-4 h-4" /> Agregar Parte</button>
                        </div>
                        <table className="w-full text-left text-sm">
                            <thead className="bg-white border-b border-surface-200">
                                <tr>
                                    <th className="px-6 py-3 font-semibold text-surface-600">Nombre</th>
                                    <th className="px-6 py-3 font-semibold text-surface-600">Rol Procesal</th>
                                    <th className="px-6 py-3 font-semibold text-surface-600">Tipo</th>
                                    <th className="px-6 py-3 font-semibold text-surface-600">Documento</th>
                                    <th className="px-6 py-3 font-semibold text-surface-600">Contacto</th>
                                    <th className="px-6 py-3 text-right">Acciones</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-surface-100">
                                {caseData.partes?.map((parte) => (
                                    <tr key={parte.id} className="hover:bg-surface-50 transition-colors">
                                        <td className="px-6 py-4 font-medium text-surface-900">{parte.nombre_completo}</td>
                                        <td className="px-6 py-4">
                                            <span className="capitalize bg-surface-100 px-2 py-1 rounded text-surface-700 text-xs">
                                                {parte.rol_procesal.replace(/_/g, ' ')}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 capitalize text-surface-600">{parte.tipo_persona}</td>
                                        <td className="px-6 py-4 text-surface-600">{parte.documento_identidad || '—'}</td>
                                        <td className="px-6 py-4 text-surface-600">{parte.telefono || parte.email || '—'}</td>
                                        <td className="px-6 py-4 text-right">
                                            <button className="text-surface-400 hover:text-primary-600">
                                                <MoreVertical className="w-4 h-4" />
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                                {(!caseData.partes || caseData.partes.length === 0) && (
                                    <tr><td colSpan={6} className="px-6 py-8 text-center text-surface-500">No hay partes registradas.</td></tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                )}

                {activeTab === 'tareas' && <TaskPanel caseId={caseData.id} />}
                {activeTab === 'plazos' && <DeadlineList caseId={caseData.id} />}
                {activeTab === 'documentos' && <DocumentList caseId={caseData.id} />}
                {activeTab === 'discusiones' && <DiscussionPanel caseId={caseData.id} />}
                {activeTab === 'aprobaciones' && <ApprovalsPanel />}
                {activeTab === 'ia' && <CaseTheoryAnalysis caseId={caseData.id} />}
            </div>
        </div>
    );
}


// === COMPONENTE TEORÍA DEL CASO ===
function CaseTheoryTab({ caseId, ramo }: { caseId: string; ramo: string }) {
    const [teoria, setTeoria] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [editing, setEditing] = useState(false);
    const toast = useToast();

    // Editable state
    const [hechos, setHechos] = useState<any[]>([]);
    const [pretensiones, setPretensiones] = useState<any[]>([]);
    const [pruebas, setPruebas] = useState<any[]>([]);
    const [estrategia, setEstrategia] = useState('');
    const [fortalezas, setFortalezas] = useState('');
    const [debilidades, setDebilidades] = useState('');

    useEffect(() => { loadTeoria(); }, [caseId]);

    const loadTeoria = async () => {
        setLoading(true);
        try {
            const { data } = await api.get(`/cases/${caseId}/teoria`);
            if (data) {
                setTeoria(data);
                setHechos(data.hechos_relevantes || []);
                setPretensiones(data.pretensiones || []);
                setPruebas(data.pruebas_plan || []);
                setEstrategia(data.estrategia_general || '');
                setFortalezas(data.fortalezas || '');
                setDebilidades(data.debilidades || '');
            }
        } catch (e) { console.error(e); }
        finally { setLoading(false); }
    };

    const handleSave = async () => {
        try {
            await api.post(`/cases/${caseId}/teoria`, {
                hechos_relevantes: hechos,
                pretensiones: pretensiones,
                pruebas_plan: pruebas,
                estrategia_general: estrategia,
                fortalezas: fortalezas,
                debilidades: debilidades,
            });
            toast.success('Teoría del caso guardada');
            setEditing(false);
            loadTeoria();
        } catch (e) { toast.error('Error al guardar'); }
    };

    const addHecho = () => setHechos(p => [...p, { orden: p.length + 1, hecho: '', fecha: '', probado: false }]);
    const addPretension = () => setPretensiones(p => [...p, { pretension: '', base_legal: '', fundamentacion: '' }]);
    const addPrueba = () => setPruebas(p => [...p, { tipo: '', descripcion: '', hecho_que_prueba: '', estado: 'pendiente' }]);

    if (loading) return <div className="text-center py-8 text-surface-500">Cargando teoría del caso...</div>;

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h3 className="font-semibold text-surface-800 flex items-center gap-2">
                        <Target className="w-5 h-5 text-primary-500" /> Teoría del Caso
                    </h3>
                    <p className="text-sm text-surface-500">Estructura: Hechos → Derecho → Pruebas → Estrategia</p>
                </div>
                <div className="flex gap-2">
                    {editing ? (
                        <>
                            <button onClick={() => setEditing(false)} className="btn btn-sm btn-outline">Cancelar</button>
                            <button onClick={handleSave} className="btn btn-sm btn-primary">Guardar v{(teoria?.version || 0) + 1}</button>
                        </>
                    ) : (
                        <button onClick={() => setEditing(true)} className="btn btn-sm btn-primary gap-1">
                            <Edit2 className="w-3.5 h-3.5" /> Editar Teoría
                        </button>
                    )}
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Column 1: HECHOS */}
                <div className="card p-5 space-y-3">
                    <h4 className="font-semibold text-surface-800 flex items-center gap-2 border-b pb-2">
                        📋 Hechos Relevantes
                        {editing && <button onClick={addHecho} className="ml-auto text-primary-500 hover:text-primary-700"><Plus className="w-4 h-4" /></button>}
                    </h4>
                    {hechos.length === 0 ? (
                        <p className="text-sm text-surface-400 italic">Sin hechos registrados</p>
                    ) : (
                        <ol className="space-y-2">
                            {hechos.map((h, i) => (
                                <li key={i} className="text-sm">
                                    {editing ? (
                                        <input value={h.hecho} onChange={e => {
                                            const copy = [...hechos]; copy[i] = {...copy[i], hecho: e.target.value}; setHechos(copy);
                                        }} className="input w-full text-sm" placeholder={`Hecho ${i+1}`} />
                                    ) : (
                                        <div className="flex items-start gap-2">
                                            <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs shrink-0 ${h.probado ? 'bg-green-100 text-green-600' : 'bg-surface-100 text-surface-400'}`}>
                                                {i+1}
                                            </span>
                                            <span className="text-surface-700">{h.hecho || 'Sin definir'}</span>
                                        </div>
                                    )}
                                </li>
                            ))}
                        </ol>
                    )}
                </div>

                {/* Column 2: DERECHO */}
                <div className="card p-5 space-y-3">
                    <h4 className="font-semibold text-surface-800 flex items-center gap-2 border-b pb-2">
                        ⚖️ Pretensiones / Derecho
                        {editing && <button onClick={addPretension} className="ml-auto text-primary-500 hover:text-primary-700"><Plus className="w-4 h-4" /></button>}
                    </h4>
                    {pretensiones.length === 0 ? (
                        <p className="text-sm text-surface-400 italic">Sin pretensiones definidas</p>
                    ) : (
                        <ul className="space-y-3">
                            {pretensiones.map((p, i) => (
                                <li key={i} className="text-sm">
                                    {editing ? (
                                        <div className="space-y-1">
                                            <input value={p.pretension} onChange={e => {
                                                const copy = [...pretensiones]; copy[i] = {...copy[i], pretension: e.target.value}; setPretensiones(copy);
                                            }} className="input w-full text-sm" placeholder="Pretensión" />
                                            <input value={p.base_legal} onChange={e => {
                                                const copy = [...pretensiones]; copy[i] = {...copy[i], base_legal: e.target.value}; setPretensiones(copy);
                                            }} className="input w-full text-sm" placeholder="Base legal (Art. ...)" />
                                        </div>
                                    ) : (
                                        <div className="bg-surface-50 rounded-lg p-2.5">
                                            <p className="font-medium text-surface-800">{p.pretension || 'Sin definir'}</p>
                                            {p.base_legal && <p className="text-xs text-primary-600 mt-0.5 font-mono">{p.base_legal}</p>}
                                        </div>
                                    )}
                                </li>
                            ))}
                        </ul>
                    )}
                </div>

                {/* Column 3: PRUEBAS */}
                <div className="card p-5 space-y-3">
                    <h4 className="font-semibold text-surface-800 flex items-center gap-2 border-b pb-2">
                        🔍 Plan Probatorio
                        {editing && <button onClick={addPrueba} className="ml-auto text-primary-500 hover:text-primary-700"><Plus className="w-4 h-4" /></button>}
                    </h4>
                    {pruebas.length === 0 ? (
                        <p className="text-sm text-surface-400 italic">Sin pruebas planificadas</p>
                    ) : (
                        <ul className="space-y-2">
                            {pruebas.map((pr, i) => (
                                <li key={i} className="text-sm">
                                    {editing ? (
                                        <div className="space-y-1">
                                            <input value={pr.descripcion} onChange={e => {
                                                const copy = [...pruebas]; copy[i] = {...copy[i], descripcion: e.target.value}; setPruebas(copy);
                                            }} className="input w-full text-sm" placeholder="Descripción de la prueba" />
                                        </div>
                                    ) : (
                                        <div className="flex items-start gap-2">
                                            <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium shrink-0 uppercase ${
                                                pr.estado === 'admitida' ? 'bg-green-100 text-green-700' :
                                                pr.estado === 'evacuada' ? 'bg-blue-100 text-blue-700' :
                                                'bg-surface-100 text-surface-500'
                                            }`}>{pr.estado || '?'}</span>
                                            <span className="text-surface-700">{pr.descripcion || 'Sin definir'}</span>
                                        </div>
                                    )}
                                </li>
                            ))}
                        </ul>
                    )}
                </div>
            </div>

            {/* Estrategia */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="card p-5 space-y-3">
                    <h4 className="font-semibold text-green-700 flex items-center gap-2">💪 Fortalezas</h4>
                    {editing ? (
                        <textarea value={fortalezas} onChange={e => setFortalezas(e.target.value)}
                            className="input w-full text-sm" rows={4} placeholder="¿Qué fortalezas tiene nuestro caso?" />
                    ) : (
                        <p className="text-sm text-surface-700">{fortalezas || 'Sin definir'}</p>
                    )}
                </div>
                <div className="card p-5 space-y-3">
                    <h4 className="font-semibold text-red-700 flex items-center gap-2">⚠️ Debilidades</h4>
                    {editing ? (
                        <textarea value={debilidades} onChange={e => setDebilidades(e.target.value)}
                            className="input w-full text-sm" rows={4} placeholder="¿Qué debilidades tiene nuestro caso?" />
                    ) : (
                        <p className="text-sm text-surface-700">{debilidades || 'Sin definir'}</p>
                    )}
                </div>
                <div className="card p-5 space-y-3">
                    <h4 className="font-semibold text-blue-700 flex items-center gap-2">🎯 Estrategia General</h4>
                    {editing ? (
                        <textarea value={estrategia} onChange={e => setEstrategia(e.target.value)}
                            className="input w-full text-sm" rows={4} placeholder="¿Cuál es nuestra estrategia para ganar?" />
                    ) : (
                        <p className="text-sm text-surface-700">{estrategia || 'Sin definir'}</p>
                    )}
                </div>
            </div>
        </div>
    );
}
