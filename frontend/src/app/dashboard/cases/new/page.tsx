'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Save, Plus, Trash2, User, Gavel, Scale, FileText, ChevronDown, ChevronUp } from 'lucide-react';
import { caseService } from '@/services/caseService';
import { Expediente, ParteProcesal } from '@/types/case';
import { useToast } from '@/components/ui/ToastProvider';
import api from '@/lib/api';

const TIPOS_PROCESO: Record<string, { value: string, label: string }[]> = {
    civil: [
        { value: 'ordinario', label: 'Ordinario' },
        { value: 'ejecutivo', label: 'Ejecutivo' },
        { value: 'sumario', label: 'Sumario' },
        { value: 'voluntario', label: 'Voluntario' },
    ],
    penal: [
        { value: 'ordinario', label: 'Ordinario' },
        { value: 'especial', label: 'Especial' },
        { value: 'faltas', label: 'Juicio de Faltas' },
    ],
    familia: [
        { value: 'divorcio_contencioso', label: 'Divorcio Contencioso' },
        { value: 'divorcio_unilateral', label: 'Divorcio Unilateral' },
        { value: 'pension_alimenticia', label: 'Pensión Alimenticia' },
        { value: 'guarda', label: 'Guarda y Crianza' },
    ],
    laboral: [
        { value: 'ordinario', label: 'Ordinario' },
        { value: 'conciliacion', label: 'Conciliación' },
    ],
    mercantil: [
        { value: 'cobro_ejecutivo', label: 'Cobro Ejecutivo' },
        { value: 'concurso', label: 'Concurso de Acreedores' },
    ],
};

export default function NewCasePage() {
    const router = useRouter();
    const [loading, setLoading] = useState(false);
    const toast = useToast();

    // Estado principal del formulario
    const [formData, setFormData] = useState<Partial<Expediente>>({
        ramo: 'civil',
        tipo_proceso: 'ordinario',
        prioridad: 'normal',
        moneda: 'NIO',
        fecha_apertura: new Date().toISOString().split('T')[0],
        juez: '',
        secretario: '',
        abogado_contraparte: '',
    });

    // Estado para datos específicos de la materia
    const [datosMateria, setDatosMateria] = useState<Record<string, string>>({});

    // Estado de partes procesales
    const [partes, setPartes] = useState<Partial<ParteProcesal>[]>([
        { rol_procesal: 'demandante', tipo_persona: 'natural', nombre_completo: '' },
        { rol_procesal: 'demandado', tipo_persona: 'natural', nombre_completo: '' }
    ]);
    const [expandedParte, setExpandedParte] = useState<number | null>(0); // Indice expandido

    const [abogados, setAbogados] = useState<any[]>([]);

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

    // Cambiar opciones de tipo_proceso cuando cambia el ramo
    useEffect(() => {
        const opciones = TIPOS_PROCESO[formData.ramo || 'civil'];
        if (opciones && opciones.length > 0) {
            setFormData(prev => ({ ...prev, tipo_proceso: opciones[0].value }));
        }
        setDatosMateria({}); // Limpiar datos específicos al cambiar de ramo
    }, [formData.ramo]);


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
        setPartes([...partes, { rol_procesal: 'tercero_interesado', tipo_persona: 'natural', nombre_completo: '' }]);
        setExpandedParte(partes.length);
    };

    const removeParty = (index: number) => {
        const newPartes = partes.filter((_, i) => i !== index);
        setPartes(newPartes);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            const validPartes = partes.filter(p => p.nombre_completo && p.nombre_completo.trim() !== '');

            const payload = {
                ...formData,
                partes: validPartes,
                datos_materia: datosMateria
            };

            const createdCase = await api.post('/cases', payload).then(r => r.data);
            toast.success('Expediente creado', `El expediente ${formData.ramo} ha sido registrado exitosamente.`);
            router.push(`/dashboard/cases/${createdCase.id}`);
        } catch (error) {
            console.error('Failed to create case', error);
            toast.error('Error al crear expediente', 'Verifique los datos de conexión o campos requeridos.');
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
                    <h1 className="text-2xl font-bold text-surface-900">Aperturar Nuevo Expediente</h1>
                    <p className="text-surface-500 text-sm">Registro de caso y asignación de equipo de litigio</p>
                </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
                
                {/* 1. SECCIÓN PRINCIPAL: TIPO Y JUZGADO */}
                <div className="card overflow-hidden">
                    <div className="bg-gradient-to-r from-surface-50 to-white px-6 py-4 border-b border-surface-200">
                        <h2 className="text-lg font-semibold text-surface-800 flex items-center gap-2">
                            <Gavel className="w-5 h-5 text-primary-500" /> Clasificación y Radicación
                        </h2>
                    </div>
                    
                    <div className="p-6 grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div className="md:col-span-3">
                            <label className="label">Carátula del Expediente *</label>
                            <input type="text" name="resumen" required
                                placeholder="Ej: Demanda de Divorcio Unilateral - Pérez vs. González"
                                className="input w-full text-lg font-medium"
                                value={formData.resumen || ''} onChange={handleInputChange} />
                        </div>

                        <div>
                            <label className="label">Ramo Jurídico *</label>
                            <select name="ramo" required className="input w-full bg-surface-50"
                                value={formData.ramo} onChange={handleInputChange}>
                                <option value="civil">Civil</option>
                                <option value="penal">Penal</option>
                                <option value="familia">Familia</option>
                                <option value="laboral">Laboral</option>
                                <option value="mercantil">Mercantil</option>
                                <option value="administrativo">Administrativo</option>
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
                            <label className="label">Materia Específica (Subtema)</label>
                            <input type="text" name="materia_especifica" placeholder="Ej: Ejecución Hipotecaria"
                                className="input w-full" value={formData.materia_especifica || ''} onChange={handleInputChange} />
                        </div>

                        <div className="md:col-span-2">
                            <label className="label">Juzgado u Oficina</label>
                            <input type="text" name="juzgado" placeholder="Ej: Juzgado Segundo Distrito Familia de Managua"
                                className="input w-full" value={formData.juzgado || ''} onChange={handleInputChange} />
                        </div>
                        <div>
                            <label className="label">Número de Causa Judicial</label>
                            <input type="text" name="numero_causa" placeholder="Ej: 0023-ORM1-2026-CV"
                                className="input w-full" value={formData.numero_causa || ''} onChange={handleInputChange} />
                        </div>

                        <div>
                            <label className="label">Juez</label>
                            <input type="text" name="juez" placeholder="Nombre del Juez"
                                className="input w-full" value={formData.juez || ''} onChange={handleInputChange} />
                        </div>
                        <div>
                            <label className="label">Secretario de Actuaciones</label>
                            <input type="text" name="secretario" placeholder="Nombre del Secretario"
                                className="input w-full" value={formData.secretario || ''} onChange={handleInputChange} />
                        </div>
                        <div>
                            <label className="label">Fecha de Presentación</label>
                            <input type="date" name="fecha_apertura" className="input w-full"
                                value={formData.fecha_apertura || ''} onChange={handleInputChange} />
                        </div>
                    </div>
                </div>

                {/* 2. CAMPOS DINÁMICOS POR MATERIA */}
                {formData.ramo === 'familia' && (
                    <div className="card p-6 bg-pink-50/30 border-pink-100">
                        <h3 className="text-sm font-semibold text-pink-800 mb-4 uppercase tracking-wider">Detalles Adicionales — Familia</h3>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div>
                                <label className="label text-pink-700">Cant. Menores Hijos</label>
                                <input type="number" className="input w-full bg-white" placeholder="0"
                                    value={datosMateria.menores_involucrados || ''} onChange={e => handleDatosMateriaChange('menores_involucrados', e.target.value)} />
                            </div>
                            <div>
                                <label className="label text-pink-700">Pensión Solicitada</label>
                                <input type="text" className="input w-full bg-white" placeholder="C$"
                                    value={datosMateria.pension_provisional || ''} onChange={e => handleDatosMateriaChange('pension_provisional', e.target.value)} />
                            </div>
                        </div>
                    </div>
                )}
                {formData.ramo === 'laboral' && (
                    <div className="card p-6 bg-amber-50/30 border-amber-100">
                        <h3 className="text-sm font-semibold text-amber-800 mb-4 uppercase tracking-wider">Detalles Adicionales — Laboral</h3>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div>
                                <label className="label text-amber-900">Salario Base Mensual</label>
                                <input type="number" className="input w-full bg-white" placeholder="C$"
                                    value={datosMateria.salario_base || ''} onChange={e => handleDatosMateriaChange('salario_base', e.target.value)} />
                            </div>
                            <div>
                                <label className="label text-amber-900">Fecha Ingreso</label>
                                <input type="date" className="input w-full bg-white" 
                                    value={datosMateria.fecha_ingreso || ''} onChange={e => handleDatosMateriaChange('fecha_ingreso', e.target.value)} />
                            </div>
                            <div>
                                <label className="label text-amber-900">Causa Despido</label>
                                <select className="input w-full bg-white" value={datosMateria.causa_despido || ''} onChange={e => handleDatosMateriaChange('causa_despido', e.target.value)}>
                                    <option value="">Seleccione...</option>
                                    <option value="injustificado">Injustificado</option>
                                    <option value="justificado_art48">Justificado (Art. 48 CT)</option>
                                    <option value="renuncia">Renuncia Voluntaria</option>
                                    <option value="mutuo_acuerdo">Mutuo Acuerdo</option>
                                </select>
                            </div>
                        </div>
                    </div>
                )}
                {formData.ramo === 'penal' && (
                    <div className="card p-6 bg-red-50/30 border-red-100">
                        <h3 className="text-sm font-semibold text-red-800 mb-4 uppercase tracking-wider">Detalles Adicionales — Penal</h3>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div>
                                <label className="label text-red-900">Delito / Tipo Penal Mayor</label>
                                <input type="text" className="input w-full bg-white" placeholder="Ej: Robo agravado"
                                    value={datosMateria.delito_principal || ''} onChange={e => handleDatosMateriaChange('delito_principal', e.target.value)} />
                            </div>
                            <div>
                                <label className="label text-red-900">Medida Cautelar Actual</label>
                                <select className="input w-full bg-white" value={datosMateria.medida_cautelar || ''} onChange={e => handleDatosMateriaChange('medida_cautelar', e.target.value)}>
                                    <option value="">Ninguna</option>
                                    <option value="prision_preventiva">Prisión Preventiva</option>
                                    <option value="arresto_domiciliar">Arresto Domiciliar</option>
                                    <option value="presentacion_periodica">Presentación Periódica</option>
                                </select>
                            </div>
                            <div>
                                <label className="label text-red-900">Fiscal a cargo</label>
                                <input type="text" className="input w-full bg-white" placeholder="Nombre completo"
                                    value={datosMateria.fiscal || ''} onChange={e => handleDatosMateriaChange('fiscal', e.target.value)} />
                            </div>
                        </div>
                    </div>
                )}


                {/* 3. PARTES PROCESALES EXPANDIDO */}
                <div className="card overflow-hidden">
                    <div className="bg-gradient-to-r from-surface-50 to-white px-6 py-4 border-b border-surface-200 flex justify-between items-center">
                        <h2 className="text-lg font-semibold text-surface-800 flex items-center gap-2">
                            <User className="w-5 h-5 text-primary-500" /> Sujetos y Partes Procesales
                        </h2>
                        <button type="button" onClick={addParty} className="btn btn-sm btn-outline text-primary-600">
                            <Plus className="w-4 h-4 mr-1" /> Añadir Parte
                        </button>
                    </div>

                    <div className="p-4 space-y-4 bg-surface-50">
                        {partes.map((parte, index) => {
                            const isExpanded = expandedParte === index;
                            return (
                                <div key={index} className="bg-white rounded-lg border border-surface-200 shadow-sm overflow-hidden transition-all duration-200">
                                    {/* Cabecera colapsable */}
                                    <div 
                                        className="p-4 flex flex-wrap gap-4 items-center justify-between cursor-pointer hover:bg-surface-50/50"
                                        onClick={() => setExpandedParte(isExpanded ? null : index)}
                                    >
                                        <div className="flex items-center gap-4 flex-1">
                                            <span className="w-8 h-8 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center font-bold text-sm shrink-0">
                                                {index + 1}
                                            </span>
                                            <div className="min-w-[150px]">
                                                <select className="input w-full h-9 text-sm font-medium border-0 bg-transparent px-0"
                                                    value={parte.rol_procesal} onChange={(e) => handlePartyChange(index, 'rol_procesal', e.target.value)}
                                                    onClick={(e) => e.stopPropagation()}>
                                                    <option value="demandante">Demandante / Actor</option>
                                                    <option value="demandado">Demandado / Acusado</option>
                                                    <option value="tercero_interesado">Tercero Interesado</option>
                                                    <option value="ministerio_publico">Ministerio Público</option>
                                                </select>
                                                <div className="text-[10px] text-surface-400 capitalize -mt-1">{parte.tipo_persona}</div>
                                            </div>
                                            <div className="flex-1">
                                                <input type="text" placeholder="Nombre completo o Razón Social"
                                                    className="input w-full h-9 border-surface-200 focus:bg-white bg-surface-50"
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
                                                {isExpanded ? <ChevronUp className="w-5 h-5"/> : <ChevronDown className="w-5 h-5"/>}
                                            </div>
                                        </div>
                                    </div>

                                    {/* Detalles expandibles */}
                                    {isExpanded && (
                                        <div className="p-4 pt-0 border-t border-surface-100 grid grid-cols-1 md:grid-cols-4 gap-4 bg-surface-50/30">
                                            <div className="mt-4">
                                                <label className="text-xs font-semibold text-surface-500 uppercase tracking-wider mb-2 block">Tipo Persona</label>
                                                <select className="input w-full text-sm" value={parte.tipo_persona}
                                                    onChange={(e) => handlePartyChange(index, 'tipo_persona', e.target.value)}>
                                                    <option value="natural">Persona Natural</option>
                                                    <option value="juridica">Persona Jurídica (Empresa)</option>
                                                </select>
                                            </div>
                                            <div className="mt-4">
                                                <label className="text-xs font-semibold text-surface-500 uppercase tracking-wider mb-2 block">Documento Identidad</label>
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
                                            
                                            {parte.tipo_persona === 'juridica' && (
                                                <div className="md:col-span-2">
                                                    <label className="text-xs font-semibold text-surface-500 uppercase tracking-wider mb-2 block">Representante Legal</label>
                                                    <input type="text" className="input w-full text-sm" placeholder="Nombre completo del representante"
                                                        value={parte.representante_legal || ''} onChange={(e) => handlePartyChange(index, 'representante_legal', e.target.value)} />
                                                </div>
                                            )}
                                            
                                            <div className="md:col-span-2">
                                                <label className="text-xs font-semibold text-surface-500 uppercase tracking-wider mb-2 block">Domicilio Notificaciones</label>
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

                {/* 4. EQUIPO LEGAL Y COSTOS */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="card p-6">
                        <h2 className="text-lg font-semibold text-surface-800 mb-4 border-b border-surface-200 pb-2 flex items-center gap-2">
                            <Scale className="w-5 h-5 text-primary-500" /> Valoración del Litigio
                        </h2>
                        <div className="space-y-4">
                            <div>
                                <label className="label">Abogado Responsable (Titular)</label>
                                <select name="abogado_responsable_id" className="input w-full" value={formData.abogado_responsable_id || ''} onChange={handleInputChange}>
                                    <option value="">Seleccione abogado...</option>
                                    {abogados.map(user => (
                                        <option key={user.id} value={user.id}>{user.nombre_completo || user.email}</option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="label">Abogado Contraparte</label>
                                <input type="text" name="abogado_contraparte" placeholder="Nombre del litigante opuesto"
                                    className="input w-full" value={formData.abogado_contraparte || ''} onChange={handleInputChange} />
                            </div>
                            <div>
                                <label className="label">Prioridad de Atención</label>
                                <select name="prioridad" className="input w-full" value={formData.prioridad} onChange={handleInputChange}>
                                    <option value="normal">Normal</option>
                                    <option value="alta">Alta</option>
                                    <option value="urgente">🔴 Urgente Institucional</option>
                                </select>
                            </div>
                            <div>
                                <label className="label">Cuantía / Valor Estimado</label>
                                <div className="flex gap-2">
                                    <select name="moneda" className="input w-24 bg-surface-50 font-medium" value={formData.moneda} onChange={handleInputChange}>
                                        <option value="NIO">NIO (C$)</option>
                                        <option value="USD">USD ($)</option>
                                    </select>
                                    <input type="number" name="valor_estimado" placeholder="0.00" className="input flex-1"
                                        value={formData.valor_estimado || ''} onChange={handleInputChange} />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Form Actions */}
                <div className="flex items-center justify-end gap-3 pt-6 border-t border-surface-200">
                    <button type="button" onClick={() => router.back()} className="btn btn-outline">Cancelar</button>
                    <button type="submit" disabled={loading} className="btn btn-primary min-w-[150px]">
                        {loading ? 'Inicializando...' : <><Save className="w-4 h-4 mr-2" /> Crear Expediente</>}
                    </button>
                </div>
            </form>
        </div>
    );
}
