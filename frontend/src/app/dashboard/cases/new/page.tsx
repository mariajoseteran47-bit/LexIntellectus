'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
    ArrowLeft, ArrowRight, Save, Plus, Trash2, User, ChevronDown, ChevronUp,
    Check, FileText, Briefcase, Building2
} from 'lucide-react';
import { ParteProcesal, TipoServicio, TIPOS_SERVICIO, ROLES_POR_SERVICIO, Expediente } from '@/types/case';
import { useToast } from '@/components/ui/ToastProvider';
import api from '@/lib/api';

// ═══════════════════════════════════════════════════════════════
// CONFIGURACIÓN DE CAMPOS POR TIPO DE SERVICIO
// ═══════════════════════════════════════════════════════════════

const TIPOS_PROCESO: Record<string, { value: string, label: string }[]> = {
    civil: [
        { value: 'ordinario', label: 'Ordinario' }, { value: 'ejecutivo', label: 'Ejecutivo' },
        { value: 'sumario', label: 'Sumario' }, { value: 'voluntario', label: 'Voluntario' },
    ],
    penal: [
        { value: 'ordinario', label: 'Ordinario' }, { value: 'especial', label: 'Especial' },
        { value: 'faltas', label: 'Juicio de Faltas' },
    ],
    familia: [
        { value: 'divorcio_contencioso', label: 'Divorcio Contencioso' },
        { value: 'divorcio_unilateral', label: 'Divorcio Unilateral' },
        { value: 'pension_alimenticia', label: 'Pensión Alimenticia' },
        { value: 'guarda', label: 'Guarda y Crianza' },
    ],
    laboral: [
        { value: 'ordinario', label: 'Ordinario' }, { value: 'conciliacion', label: 'Conciliación' },
    ],
    mercantil: [
        { value: 'cobro_ejecutivo', label: 'Cobro Ejecutivo' }, { value: 'concurso', label: 'Concurso de Acreedores' },
    ],
};

const TIPOS_ACTO_NOTARIAL = [
    { value: 'compraventa_inmueble', label: 'Compraventa de Inmueble' },
    { value: 'donacion', label: 'Donación' },
    { value: 'hipoteca', label: 'Constitución de Hipoteca' },
    { value: 'cancelacion_hipoteca', label: 'Cancelación de Hipoteca' },
    { value: 'constitucion_sa', label: 'Constitución de Sociedad Anónima' },
    { value: 'poder_general', label: 'Poder General de Administración' },
    { value: 'poder_especial', label: 'Poder Especial' },
    { value: 'testamento', label: 'Testamento' },
    { value: 'cesion_derechos', label: 'Cesión de Derechos' },
    { value: 'arrendamiento', label: 'Contrato de Arrendamiento' },
    { value: 'protocolizacion_acta', label: 'Protocolización de Acta' },
    { value: 'declaracion_jurada', label: 'Declaración Jurada' },
    { value: 'capitulaciones', label: 'Capitulaciones Matrimoniales' },
    { value: 'otro', label: 'Otro Acto Notarial' },
];

const TIPOS_CONTRATO = [
    { value: 'arrendamiento', label: 'Arrendamiento' },
    { value: 'servicios', label: 'Servicios Profesionales' },
    { value: 'distribucion', label: 'Distribución' },
    { value: 'franquicia', label: 'Franquicia' },
    { value: 'confidencialidad', label: 'NDA / Confidencialidad' },
    { value: 'trabajo', label: 'Contrato de Trabajo' },
    { value: 'licencia_software', label: 'Licencia de Software' },
    { value: 'construccion', label: 'Construcción' },
    { value: 'compraventa', label: 'Compraventa de Bienes' },
    { value: 'otro', label: 'Otro Tipo de Contrato' },
];

const TIPOS_TRAMITE = [
    { value: 'inscripcion_registral', label: 'Inscripción Registral' },
    { value: 'obtencion_ruc', label: 'Obtención de RUC' },
    { value: 'licencia_permiso', label: 'Licencia o Permiso Gubernamental' },
    { value: 'registro_sanitario', label: 'Registro Sanitario' },
    { value: 'residencia_trabajo', label: 'Permiso de Residencia / Trabajo' },
    { value: 'apostilla', label: 'Apostilla / Legalización' },
    { value: 'otro', label: 'Otro Trámite' },
];

const TIPOS_IP = [
    { value: 'registro_marca', label: 'Registro de Marca' },
    { value: 'renovacion_marca', label: 'Renovación de Marca' },
    { value: 'patente', label: 'Registro de Patente' },
    { value: 'derechos_autor', label: 'Derechos de Autor' },
    { value: 'oposicion_marca', label: 'Oposición / Defensa de Marca' },
    { value: 'otro', label: 'Otro' },
];

const TIPOS_CORPORATIVO = [
    { value: 'reforma_pacto', label: 'Reforma de Pacto Social' },
    { value: 'cambio_junta', label: 'Actualización de Junta Directiva' },
    { value: 'aumento_capital', label: 'Aumento de Capital' },
    { value: 'reduccion_capital', label: 'Reducción de Capital' },
    { value: 'fusion', label: 'Fusión de Sociedades' },
    { value: 'escision', label: 'Escisión' },
    { value: 'disolucion', label: 'Disolución / Liquidación' },
    { value: 'actualizacion_libros', label: 'Actualización de Libros Corporativos' },
    { value: 'cambio_representante', label: 'Cambio de Representante Legal' },
    { value: 'otro', label: 'Otro Acto Corporativo' },
];

const WIZARD_STEPS = [
    { id: 1, title: 'Tipo de Servicio', icon: '📋' },
    { id: 2, title: 'Información General', icon: '📝' },
    { id: 3, title: 'Participantes', icon: '👥' },
    { id: 4, title: 'Equipo y Valoración', icon: '⚖️' },
];

// ═══════════════════════════════════════════════════════════════
// COMPONENTE PRINCIPAL
// ═══════════════════════════════════════════════════════════════

export default function NewCasePage() {
    const router = useRouter();
    const [loading, setLoading] = useState(false);
    const toast = useToast();
    const [currentStep, setCurrentStep] = useState(1);

    // Form data
    const [formData, setFormData] = useState<Partial<Expediente>>({
        tipo_servicio: undefined,
        ramo: 'civil',
        tipo_proceso: 'ordinario',
        prioridad: 'normal',
        moneda: 'NIO',
        fecha_apertura: new Date().toISOString().split('T')[0],
    });

    const [datosMateria, setDatosMateria] = useState<Record<string, string>>({});
    const [partes, setPartes] = useState<Partial<ParteProcesal>[]>([]);
    const [expandedParte, setExpandedParte] = useState<number | null>(0);
    const [abogados, setAbogados] = useState<any[]>([]);

    // Fetch lawyers
    useEffect(() => {
        const fetchAbogados = async () => {
            try {
                const { data } = await api.get('/users');
                setAbogados(data.items || data || []);
            } catch (error) {
                console.error('Error fetching abogados:', error);
            }
        };
        fetchAbogados();
    }, []);

    // Reset parts when service type changes
    useEffect(() => {
        if (formData.tipo_servicio) {
            const roles = ROLES_POR_SERVICIO[formData.tipo_servicio as TipoServicio] || [];
            const defaultPartes: Partial<ParteProcesal>[] = roles.slice(0, 2).map(r => ({
                rol_procesal: r.value, tipo_persona: 'natural', nombre_completo: ''
            }));
            setPartes(defaultPartes.length > 0 ? defaultPartes : [{ rol_procesal: 'cliente', tipo_persona: 'natural', nombre_completo: '' }]);
            setDatosMateria({});
        }
    }, [formData.tipo_servicio]);

    // Helpers
    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleDatosMateriaChange = (key: string, value: string) => {
        setDatosMateria(prev => ({ ...prev, [key]: value }));
    };

    const handlePartyChange = (index: number, field: keyof ParteProcesal, value: string) => {
        const newPartes = [...partes];
        newPartes[index] = { ...newPartes[index], [field]: value };
        setPartes(newPartes);
    };

    const addParty = () => {
        const roles = ROLES_POR_SERVICIO[formData.tipo_servicio as TipoServicio] || [];
        const defaultRole = roles.length > 0 ? roles[roles.length > 2 ? 2 : 0].value : 'otro';
        setPartes([...partes, { rol_procesal: defaultRole, tipo_persona: 'natural', nombre_completo: '' }]);
        setExpandedParte(partes.length);
    };

    const removeParty = (index: number) => setPartes(partes.filter((_, i) => i !== index));

    const selectedService = TIPOS_SERVICIO.find(s => s.value === formData.tipo_servicio);

    const canAdvance = () => {
        if (currentStep === 1) return !!formData.tipo_servicio;
        if (currentStep === 2) return !!formData.resumen;
        return true;
    };

    // Submit
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            const validPartes = partes.filter(p => p.nombre_completo && p.nombre_completo.trim() !== '');
            const payload = {
                ...formData,
                ramo: formData.tipo_servicio === 'litigio' ? formData.ramo : null,
                tipo_proceso: formData.tipo_servicio === 'litigio' ? formData.tipo_proceso : datosMateria.subtipo || null,
                partes: validPartes,
                datos_materia: datosMateria,
            };
            const createdCase = await api.post('/cases', payload).then(r => r.data);
            toast.success('Asunto creado', `${selectedService?.label || 'Asunto'} registrado exitosamente.`);
            router.push(`/dashboard/cases/${createdCase.id}`);
        } catch (error) {
            console.error('Failed to create case', error);
            toast.error('Error al crear asunto', 'Verifique los datos o campos requeridos.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-5xl mx-auto pb-12">
            {/* Header */}
            <div className="flex items-center gap-4 mb-6">
                <Link href="/dashboard/cases" className="btn btn-ghost p-2 text-surface-500 hover:text-primary-600">
                    <ArrowLeft className="w-5 h-5" />
                </Link>
                <div>
                    <h1 className="text-2xl font-bold text-surface-900">Nuevo Asunto Legal</h1>
                    <p className="text-surface-500 text-sm">
                        {selectedService ? `${selectedService.icon} ${selectedService.label}` : 'Seleccione el tipo de servicio'}
                    </p>
                </div>
            </div>

            {/* Stepper */}
            <div className="flex items-center gap-1 mb-8 px-2">
                {WIZARD_STEPS.map((step, idx) => (
                    <div key={step.id} className="flex items-center flex-1">
                        <button
                            type="button"
                            onClick={() => step.id < currentStep && setCurrentStep(step.id)}
                            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all w-full
                                ${currentStep === step.id
                                    ? 'bg-primary-50 text-primary-700 ring-2 ring-primary-200'
                                    : step.id < currentStep
                                        ? 'bg-emerald-50 text-emerald-700 cursor-pointer hover:bg-emerald-100'
                                        : 'bg-surface-50 text-surface-400'
                                }`}
                        >
                            <span className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0
                                ${currentStep === step.id ? 'bg-primary-600 text-white'
                                    : step.id < currentStep ? 'bg-emerald-500 text-white' : 'bg-surface-200 text-surface-500'}`}>
                                {step.id < currentStep ? <Check className="w-4 h-4" /> : step.id}
                            </span>
                            <span className="hidden md:inline truncate">{step.title}</span>
                        </button>
                        {idx < WIZARD_STEPS.length - 1 && (
                            <div className={`w-4 h-0.5 mx-1 shrink-0 ${step.id < currentStep ? 'bg-emerald-300' : 'bg-surface-200'}`} />
                        )}
                    </div>
                ))}
            </div>

            <form onSubmit={handleSubmit}>
                {/* ═══ PASO 1: SELECCIÓN DE TIPO DE SERVICIO ═══ */}
                {currentStep === 1 && (
                    <div className="space-y-4">
                        <h2 className="text-lg font-semibold text-surface-800 mb-2">¿Qué tipo de servicio legal necesita?</h2>
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                            {TIPOS_SERVICIO.map(svc => (
                                <button
                                    key={svc.value}
                                    type="button"
                                    onClick={() => setFormData(prev => ({ ...prev, tipo_servicio: svc.value as TipoServicio }))}
                                    className={`group p-4 rounded-xl border-2 text-left transition-all duration-200 hover:shadow-md
                                        ${formData.tipo_servicio === svc.value
                                            ? 'border-primary-500 bg-primary-50/50 shadow-md ring-1 ring-primary-200'
                                            : 'border-surface-200 bg-white hover:border-primary-200 hover:bg-surface-50/50'
                                        }`}
                                >
                                    <div className="flex items-start gap-3">
                                        <span className="text-2xl">{svc.icon}</span>
                                        <div className="min-w-0">
                                            <div className="font-semibold text-surface-800 text-sm">{svc.label}</div>
                                            <div className="text-xs text-surface-500 mt-0.5 line-clamp-2">{svc.description}</div>
                                        </div>
                                        {formData.tipo_servicio === svc.value && (
                                            <Check className="w-5 h-5 text-primary-600 shrink-0 ml-auto" />
                                        )}
                                    </div>
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {/* ═══ PASO 2: INFORMACIÓN GENERAL (ADAPTATIVA) ═══ */}
                {currentStep === 2 && (
                    <div className="space-y-6">
                        {/* Título / Carátula — Universal */}
                        <div className="card p-6">
                            <div className="flex items-center gap-2 mb-4">
                                <span className="text-xl">{selectedService?.icon}</span>
                                <h2 className="text-lg font-semibold text-surface-800">Información del Asunto</h2>
                            </div>
                            <div className="space-y-4">
                                <div>
                                    <label className="label">Título / Carátula del Asunto *</label>
                                    <input type="text" name="resumen" required
                                        placeholder={
                                            formData.tipo_servicio === 'litigio' ? 'Ej: Demanda Ordinaria — Pérez vs. González' :
                                            formData.tipo_servicio === 'escritura' ? 'Ej: Escritura de Compraventa — Lote B-12 Residencial Los Pinos' :
                                            formData.tipo_servicio === 'contrato' ? 'Ej: Contrato de Arrendamiento — Local Comercial Plaza Central' :
                                            formData.tipo_servicio === 'tramite' ? 'Ej: Inscripción de S.A. ante Registro Público Mercantil' :
                                            formData.tipo_servicio === 'gestion_corporativa' ? 'Ej: Reforma Pacto Social — Grupo Pérez S.A.' :
                                            'Descripción breve del asunto'
                                        }
                                        className="input w-full text-lg font-medium"
                                        value={formData.resumen || ''} onChange={handleInputChange} />
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div>
                                        <label className="label">Fecha de Apertura</label>
                                        <input type="date" name="fecha_apertura" className="input w-full"
                                            value={formData.fecha_apertura || ''} onChange={handleInputChange} />
                                    </div>
                                    <div>
                                        <label className="label">Número de Referencia</label>
                                        <input type="text" name="numero_causa" className="input w-full"
                                            placeholder={
                                                formData.tipo_servicio === 'litigio' ? 'Nº Causa Judicial' :
                                                formData.tipo_servicio === 'escritura' ? 'Nº Escritura' :
                                                formData.tipo_servicio === 'tramite' ? 'Nº Expediente Institucional' :
                                                'Referencia interna'
                                            }
                                            value={formData.numero_causa || ''} onChange={handleInputChange} />
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Campos específicos por tipo */}
                        {formData.tipo_servicio === 'litigio' && (
                            <div className="card p-6 border-blue-200 bg-blue-50/30">
                                <h3 className="text-sm font-semibold text-blue-800 mb-4 uppercase tracking-wider flex items-center gap-2">
                                    <Briefcase className="w-4 h-4" /> Datos Judiciales
                                </h3>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    <div>
                                        <label className="label">Ramo Jurídico *</label>
                                        <select name="ramo" required className="input w-full"
                                            value={formData.ramo || 'civil'} onChange={handleInputChange}>
                                            <option value="civil">Civil</option>
                                            <option value="penal">Penal</option>
                                            <option value="familia">Familia</option>
                                            <option value="laboral">Laboral</option>
                                            <option value="mercantil">Mercantil</option>
                                            <option value="administrativo">Administrativo</option>
                                            <option value="constitucional">Constitucional</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className="label">Tipo de Proceso *</label>
                                        <select name="tipo_proceso" required className="input w-full"
                                            value={formData.tipo_proceso || ''} onChange={handleInputChange}>
                                            {(TIPOS_PROCESO[formData.ramo || 'civil'] || []).map(opt => (
                                                <option key={opt.value} value={opt.value}>{opt.label}</option>
                                            ))}
                                        </select>
                                    </div>
                                    <div>
                                        <label className="label">Materia Específica</label>
                                        <input type="text" name="materia_especifica" placeholder="Ej: Ejecución Hipotecaria"
                                            className="input w-full" value={formData.materia_especifica || ''} onChange={handleInputChange} />
                                    </div>
                                    <div className="md:col-span-2">
                                        <label className="label">Juzgado</label>
                                        <input type="text" name="juzgado" placeholder="Ej: Juzgado 2do Distrito Civil Managua"
                                            className="input w-full" value={formData.juzgado || ''} onChange={handleInputChange} />
                                    </div>
                                    <div>
                                        <label className="label">Juez</label>
                                        <input type="text" name="juez" placeholder="Nombre del Juez"
                                            className="input w-full" value={formData.juez || ''} onChange={handleInputChange} />
                                    </div>
                                </div>
                            </div>
                        )}

                        {formData.tipo_servicio === 'escritura' && (
                            <div className="card p-6 border-amber-200 bg-amber-50/30">
                                <h3 className="text-sm font-semibold text-amber-800 mb-4 uppercase tracking-wider">📜 Datos Notariales</h3>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    <div className="md:col-span-2">
                                        <label className="label">Tipo de Acto Notarial *</label>
                                        <select className="input w-full" value={datosMateria.tipo_acto || ''}
                                            onChange={e => handleDatosMateriaChange('tipo_acto', e.target.value)}>
                                            <option value="">Seleccione...</option>
                                            {TIPOS_ACTO_NOTARIAL.map(t => (
                                                <option key={t.value} value={t.value}>{t.label}</option>
                                            ))}
                                        </select>
                                    </div>
                                    <div>
                                        <label className="label">Nº Escritura</label>
                                        <input type="text" className="input w-full" placeholder="Ej: 42"
                                            value={datosMateria.numero_escritura || ''} onChange={e => handleDatosMateriaChange('numero_escritura', e.target.value)} />
                                    </div>
                                    <div>
                                        <label className="label">Tomo</label>
                                        <input type="text" className="input w-full" placeholder="Ej: III"
                                            value={datosMateria.tomo || ''} onChange={e => handleDatosMateriaChange('tomo', e.target.value)} />
                                    </div>
                                    <div>
                                        <label className="label">Folio</label>
                                        <input type="text" className="input w-full" placeholder="Ej: 120"
                                            value={datosMateria.folio || ''} onChange={e => handleDatosMateriaChange('folio', e.target.value)} />
                                    </div>
                                    <div>
                                        <label className="label">Libro Protocolo</label>
                                        <input type="text" className="input w-full" placeholder="Ej: Quinto"
                                            value={datosMateria.libro || ''} onChange={e => handleDatosMateriaChange('libro', e.target.value)} />
                                    </div>
                                </div>
                            </div>
                        )}

                        {formData.tipo_servicio === 'contrato' && (
                            <div className="card p-6 border-indigo-200 bg-indigo-50/30">
                                <h3 className="text-sm font-semibold text-indigo-800 mb-4 uppercase tracking-wider">📄 Datos del Contrato</h3>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    <div>
                                        <label className="label">Tipo de Contrato *</label>
                                        <select className="input w-full" value={datosMateria.subtipo || ''}
                                            onChange={e => handleDatosMateriaChange('subtipo', e.target.value)}>
                                            <option value="">Seleccione...</option>
                                            {TIPOS_CONTRATO.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                                        </select>
                                    </div>
                                    <div>
                                        <label className="label">Vigencia (meses)</label>
                                        <input type="number" className="input w-full" placeholder="12"
                                            value={datosMateria.vigencia_meses || ''} onChange={e => handleDatosMateriaChange('vigencia_meses', e.target.value)} />
                                    </div>
                                    <div>
                                        <label className="label">Fecha Vencimiento</label>
                                        <input type="date" className="input w-full"
                                            value={datosMateria.fecha_vencimiento || ''} onChange={e => handleDatosMateriaChange('fecha_vencimiento', e.target.value)} />
                                    </div>
                                    <div className="md:col-span-3">
                                        <label className="label">Objeto del Contrato</label>
                                        <textarea className="input w-full" rows={2} placeholder="Descripción del objeto contractual"
                                            value={datosMateria.objeto || ''} onChange={e => handleDatosMateriaChange('objeto', e.target.value)} />
                                    </div>
                                </div>
                            </div>
                        )}

                        {formData.tipo_servicio === 'tramite' && (
                            <div className="card p-6 border-violet-200 bg-violet-50/30">
                                <h3 className="text-sm font-semibold text-violet-800 mb-4 uppercase tracking-wider">📝 Datos del Trámite</h3>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    <div>
                                        <label className="label">Tipo de Trámite *</label>
                                        <select className="input w-full" value={datosMateria.subtipo || ''}
                                            onChange={e => handleDatosMateriaChange('subtipo', e.target.value)}>
                                            <option value="">Seleccione...</option>
                                            {TIPOS_TRAMITE.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                                        </select>
                                    </div>
                                    <div className="md:col-span-2">
                                        <label className="label">Institución Destino</label>
                                        <input type="text" className="input w-full" placeholder="Ej: Registro Público de la Propiedad"
                                            value={datosMateria.institucion || ''} onChange={e => handleDatosMateriaChange('institucion', e.target.value)} />
                                    </div>
                                </div>
                            </div>
                        )}

                        {formData.tipo_servicio === 'asesoria' && (
                            <div className="card p-6 border-emerald-200 bg-emerald-50/30">
                                <h3 className="text-sm font-semibold text-emerald-800 mb-4 uppercase tracking-wider">💼 Datos de la Asesoría</h3>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    <div>
                                        <label className="label">Tipo de Iguala</label>
                                        <select className="input w-full" value={datosMateria.tipo_iguala || ''}
                                            onChange={e => handleDatosMateriaChange('tipo_iguala', e.target.value)}>
                                            <option value="">Seleccione...</option>
                                            <option value="mensual">Mensual</option>
                                            <option value="trimestral">Trimestral</option>
                                            <option value="anual">Anual</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className="label">Horas Incluidas (mes)</label>
                                        <input type="number" className="input w-full" placeholder="20"
                                            value={datosMateria.horas_incluidas || ''} onChange={e => handleDatosMateriaChange('horas_incluidas', e.target.value)} />
                                    </div>
                                    <div>
                                        <label className="label">Alcance</label>
                                        <input type="text" className="input w-full" placeholder="Ej: Derecho laboral y corporativo"
                                            value={datosMateria.alcance || ''} onChange={e => handleDatosMateriaChange('alcance', e.target.value)} />
                                    </div>
                                </div>
                            </div>
                        )}

                        {formData.tipo_servicio === 'propiedad_intelectual' && (
                            <div className="card p-6 border-fuchsia-200 bg-fuchsia-50/30">
                                <h3 className="text-sm font-semibold text-fuchsia-800 mb-4 uppercase tracking-wider">🏷️ Propiedad Intelectual</h3>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    <div>
                                        <label className="label">Tipo *</label>
                                        <select className="input w-full" value={datosMateria.subtipo || ''}
                                            onChange={e => handleDatosMateriaChange('subtipo', e.target.value)}>
                                            <option value="">Seleccione...</option>
                                            {TIPOS_IP.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                                        </select>
                                    </div>
                                    <div>
                                        <label className="label">Nombre de la Marca / Invención</label>
                                        <input type="text" className="input w-full" placeholder="Ej: LexIntellectus®"
                                            value={datosMateria.nombre_marca || ''} onChange={e => handleDatosMateriaChange('nombre_marca', e.target.value)} />
                                    </div>
                                    <div>
                                        <label className="label">Clase Niza</label>
                                        <input type="text" className="input w-full" placeholder="Ej: Clase 42 (Software)"
                                            value={datosMateria.clase_niza || ''} onChange={e => handleDatosMateriaChange('clase_niza', e.target.value)} />
                                    </div>
                                </div>
                            </div>
                        )}

                        {formData.tipo_servicio === 'gestion_corporativa' && (
                            <div className="card p-6 border-teal-200 bg-teal-50/30">
                                <h3 className="text-sm font-semibold text-teal-800 mb-4 uppercase tracking-wider flex items-center gap-2">
                                    <Building2 className="w-4 h-4" /> Datos Corporativos
                                </h3>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    <div>
                                        <label className="label">Tipo de Acto Corporativo *</label>
                                        <select className="input w-full" value={datosMateria.subtipo || ''}
                                            onChange={e => handleDatosMateriaChange('subtipo', e.target.value)}>
                                            <option value="">Seleccione...</option>
                                            {TIPOS_CORPORATIVO.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                                        </select>
                                    </div>
                                    <div className="md:col-span-2">
                                        <label className="label">Sociedad / Empresa</label>
                                        <input type="text" className="input w-full" placeholder="Razón social de la empresa"
                                            value={datosMateria.sociedad || ''} onChange={e => handleDatosMateriaChange('sociedad', e.target.value)} />
                                    </div>
                                </div>
                            </div>
                        )}

                        {(formData.tipo_servicio === 'consulta' || formData.tipo_servicio === 'mediacion' || formData.tipo_servicio === 'due_diligence') && (
                            <div className="card p-6 border-surface-200">
                                <h3 className="text-sm font-semibold text-surface-700 mb-4 uppercase tracking-wider">
                                    {selectedService?.icon} Detalles Adicionales
                                </h3>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    {formData.tipo_servicio === 'consulta' && (
                                        <>
                                            <div>
                                                <label className="label">Modalidad</label>
                                                <select className="input w-full" value={datosMateria.modalidad || ''}
                                                    onChange={e => handleDatosMateriaChange('modalidad', e.target.value)}>
                                                    <option value="">Seleccione...</option>
                                                    <option value="presencial">Presencial</option>
                                                    <option value="virtual">Virtual</option>
                                                    <option value="escrita">Escrita (Opinión Legal)</option>
                                                </select>
                                            </div>
                                            <div>
                                                <label className="label">Área de Consulta</label>
                                                <input type="text" className="input w-full" placeholder="Ej: Derecho inmobiliario"
                                                    value={datosMateria.area || ''} onChange={e => handleDatosMateriaChange('area', e.target.value)} />
                                            </div>
                                        </>
                                    )}
                                    {formData.tipo_servicio === 'mediacion' && (
                                        <>
                                            <div>
                                                <label className="label">Centro de Mediación / Arbitraje</label>
                                                <input type="text" className="input w-full" placeholder="Nombre de la institución"
                                                    value={datosMateria.centro || ''} onChange={e => handleDatosMateriaChange('centro', e.target.value)} />
                                            </div>
                                            <div>
                                                <label className="label">Tipo</label>
                                                <select className="input w-full" value={datosMateria.subtipo || ''}
                                                    onChange={e => handleDatosMateriaChange('subtipo', e.target.value)}>
                                                    <option value="mediacion">Mediación</option>
                                                    <option value="conciliacion">Conciliación</option>
                                                    <option value="arbitraje_adhoc">Arbitraje Ad-hoc</option>
                                                    <option value="arbitraje_institucional">Arbitraje Institucional</option>
                                                </select>
                                            </div>
                                        </>
                                    )}
                                    {formData.tipo_servicio === 'due_diligence' && (
                                        <>
                                            <div>
                                                <label className="label">Objetivo de la Auditoría</label>
                                                <input type="text" className="input w-full" placeholder="Ej: Adquisición de Empresa XYZ"
                                                    value={datosMateria.objetivo || ''} onChange={e => handleDatosMateriaChange('objetivo', e.target.value)} />
                                            </div>
                                            <div>
                                                <label className="label">Fecha Límite</label>
                                                <input type="date" className="input w-full"
                                                    value={datosMateria.fecha_limite || ''} onChange={e => handleDatosMateriaChange('fecha_limite', e.target.value)} />
                                            </div>
                                        </>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* ═══ PASO 3: PARTICIPANTES (ROLES DINÁMICOS) ═══ */}
                {currentStep === 3 && (
                    <div className="card overflow-hidden">
                        <div className="bg-gradient-to-r from-surface-50 to-white px-6 py-4 border-b border-surface-200 flex justify-between items-center">
                            <h2 className="text-lg font-semibold text-surface-800 flex items-center gap-2">
                                <User className="w-5 h-5 text-primary-500" /> Participantes del Asunto
                            </h2>
                            <button type="button" onClick={addParty} className="btn btn-sm btn-outline text-primary-600">
                                <Plus className="w-4 h-4 mr-1" /> Añadir
                            </button>
                        </div>

                        <div className="p-4 space-y-3 bg-surface-50">
                            {partes.map((parte, index) => {
                                const isExpanded = expandedParte === index;
                                const availableRoles = ROLES_POR_SERVICIO[formData.tipo_servicio as TipoServicio] || [];
                                return (
                                    <div key={index} className="bg-white rounded-lg border border-surface-200 shadow-sm overflow-hidden">
                                        <div className="p-4 flex flex-wrap gap-4 items-center justify-between cursor-pointer hover:bg-surface-50/50"
                                            onClick={() => setExpandedParte(isExpanded ? null : index)}>
                                            <div className="flex items-center gap-4 flex-1">
                                                <span className="w-8 h-8 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center font-bold text-sm shrink-0">
                                                    {index + 1}
                                                </span>
                                                <div className="min-w-[160px]">
                                                    <select className="input w-full h-9 text-sm font-medium border-0 bg-transparent px-0"
                                                        value={parte.rol_procesal || ''} onChange={(e) => handlePartyChange(index, 'rol_procesal', e.target.value)}
                                                        onClick={(e) => e.stopPropagation()}>
                                                        {availableRoles.map(r => (
                                                            <option key={r.value} value={r.value}>{r.label}</option>
                                                        ))}
                                                        <option value="otro">Otro</option>
                                                    </select>
                                                </div>
                                                <div className="flex-1">
                                                    <input type="text" placeholder="Nombre completo o Razón Social"
                                                        className="input w-full h-9 border-surface-200"
                                                        value={parte.nombre_completo || ''} onChange={(e) => handlePartyChange(index, 'nombre_completo', e.target.value)}
                                                        onClick={(e) => e.stopPropagation()} />
                                                </div>
                                            </div>
                                            <div className="flex gap-2 shrink-0">
                                                {partes.length > 1 && (
                                                    <button type="button" onClick={(e) => { e.stopPropagation(); removeParty(index); }}
                                                        className="btn btn-sm btn-ghost text-red-500 hover:bg-red-50 p-2">
                                                        <Trash2 className="w-4 h-4" />
                                                    </button>
                                                )}
                                                <div className="p-2 text-surface-400">
                                                    {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                                                </div>
                                            </div>
                                        </div>

                                        {isExpanded && (
                                            <div className="p-4 pt-0 border-t border-surface-100 grid grid-cols-1 md:grid-cols-4 gap-4 bg-surface-50/30">
                                                <div className="mt-4">
                                                    <label className="text-xs font-semibold text-surface-500 uppercase tracking-wider mb-2 block">Tipo Persona</label>
                                                    <select className="input w-full text-sm" value={parte.tipo_persona}
                                                        onChange={(e) => handlePartyChange(index, 'tipo_persona', e.target.value)}>
                                                        <option value="natural">Persona Natural</option>
                                                        <option value="juridica">Persona Jurídica</option>
                                                    </select>
                                                </div>
                                                <div className="mt-4">
                                                    <label className="text-xs font-semibold text-surface-500 uppercase tracking-wider mb-2 block">Documento</label>
                                                    <input type="text" className="input w-full text-sm" placeholder="Cédula o RUC"
                                                        value={parte.documento_identidad || ''} onChange={(e) => handlePartyChange(index, 'documento_identidad', e.target.value)} />
                                                </div>
                                                <div className="mt-4">
                                                    <label className="text-xs font-semibold text-surface-500 uppercase tracking-wider mb-2 block">Teléfono</label>
                                                    <input type="text" className="input w-full text-sm" placeholder="+505 ..."
                                                        value={parte.telefono || ''} onChange={(e) => handlePartyChange(index, 'telefono', e.target.value)} />
                                                </div>
                                                <div className="mt-4">
                                                    <label className="text-xs font-semibold text-surface-500 uppercase tracking-wider mb-2 block">Email</label>
                                                    <input type="email" className="input w-full text-sm" placeholder="correo@ejemplo.com"
                                                        value={parte.email || ''} onChange={(e) => handlePartyChange(index, 'email', e.target.value)} />
                                                </div>
                                                <div className="md:col-span-2">
                                                    <label className="text-xs font-semibold text-surface-500 uppercase tracking-wider mb-2 block">Dirección</label>
                                                    <input type="text" className="input w-full text-sm" placeholder="Dirección completa"
                                                        value={parte.direccion || ''} onChange={(e) => handlePartyChange(index, 'direccion', e.target.value)} />
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}

                {/* ═══ PASO 4: EQUIPO Y VALORACIÓN ═══ */}
                {currentStep === 4 && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="card p-6">
                            <h2 className="text-lg font-semibold text-surface-800 mb-4 border-b border-surface-200 pb-2 flex items-center gap-2">
                                <Briefcase className="w-5 h-5 text-primary-500" /> Equipo Legal
                            </h2>
                            <div className="space-y-4">
                                <div>
                                    <label className="label">Abogado Responsable</label>
                                    <select name="abogado_responsable_id" className="input w-full"
                                        value={formData.abogado_responsable_id || ''} onChange={handleInputChange}>
                                        <option value="">Seleccione...</option>
                                        {abogados.map(user => (
                                            <option key={user.id} value={user.id}>{user.nombre_completo || user.email}</option>
                                        ))}
                                    </select>
                                </div>
                                {formData.tipo_servicio === 'litigio' && (
                                    <div>
                                        <label className="label">Abogado Contraparte</label>
                                        <input type="text" name="abogado_contraparte" placeholder="Nombre del litigante opuesto"
                                            className="input w-full" value={formData.abogado_contraparte || ''} onChange={handleInputChange} />
                                    </div>
                                )}
                                <div>
                                    <label className="label">Prioridad</label>
                                    <select name="prioridad" className="input w-full" value={formData.prioridad} onChange={handleInputChange}>
                                        <option value="baja">Baja</option>
                                        <option value="normal">Normal</option>
                                        <option value="alta">Alta</option>
                                        <option value="urgente">🔴 Urgente</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                        <div className="card p-6">
                            <h2 className="text-lg font-semibold text-surface-800 mb-4 border-b border-surface-200 pb-2 flex items-center gap-2">
                                <FileText className="w-5 h-5 text-primary-500" /> Valoración Económica
                            </h2>
                            <div className="space-y-4">
                                <div>
                                    <label className="label">
                                        {formData.tipo_servicio === 'litigio' ? 'Cuantía del Litigio' : 'Valor Estimado del Servicio'}
                                    </label>
                                    <div className="flex gap-2">
                                        <select name="moneda" className="input w-24 bg-surface-50 font-medium" value={formData.moneda} onChange={handleInputChange}>
                                            <option value="NIO">NIO (C$)</option>
                                            <option value="USD">USD ($)</option>
                                        </select>
                                        <input type="number" name="valor_estimado" placeholder="0.00" className="input flex-1"
                                            value={formData.valor_estimado || ''} onChange={handleInputChange} />
                                    </div>
                                </div>
                                <div>
                                    <label className="label">Observaciones Adicionales</label>
                                    <textarea name="resumen_notas" className="input w-full" rows={3}
                                        placeholder="Notas internas sobre este asunto..."
                                        value={datosMateria.notas || ''} onChange={e => handleDatosMateriaChange('notas', e.target.value)} />
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* ═══ NAVEGACIÓN ═══ */}
                <div className="flex items-center justify-between pt-6 mt-6 border-t border-surface-200">
                    <button type="button"
                        onClick={() => currentStep > 1 ? setCurrentStep(currentStep - 1) : router.back()}
                        className="btn btn-outline">
                        <ArrowLeft className="w-4 h-4 mr-2" />
                        {currentStep > 1 ? 'Anterior' : 'Cancelar'}
                    </button>

                    {currentStep < 4 ? (
                        <button type="button" disabled={!canAdvance()}
                            onClick={() => setCurrentStep(currentStep + 1)}
                            className="btn btn-primary min-w-[150px]">
                            Siguiente <ArrowRight className="w-4 h-4 ml-2" />
                        </button>
                    ) : (
                        <button type="submit" disabled={loading} className="btn btn-primary min-w-[180px]">
                            {loading ? 'Creando...' : <><Save className="w-4 h-4 mr-2" /> Crear Asunto</>}
                        </button>
                    )}
                </div>
            </form>
        </div>
    );
}
