'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Save, Plus, Trash2, User } from 'lucide-react';
import { caseService } from '@/services/caseService';
import { Expediente, ParteProcesal } from '@/types/case';

export default function NewCasePage() {
    const router = useRouter();
    const [loading, setLoading] = useState(false);

    // Form State
    const [formData, setFormData] = useState<Partial<Expediente>>({
        ramo: 'civil',
        prioridad: 'normal',
        moneda: 'NIO',
        fecha_apertura: new Date().toISOString().split('T')[0],
    });

    // Parties State
    const [partes, setPartes] = useState<Partial<ParteProcesal>[]>([
        { rol_procesal: 'demandante', tipo_persona: 'natural', nombre_completo: '' },
        { rol_procesal: 'demandado', tipo_persona: 'natural', nombre_completo: '' }
    ]);

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handlePartyChange = (index: number, field: keyof ParteProcesal, value: string) => {
        const newPartes = [...partes];
        newPartes[index] = { ...newPartes[index], [field]: value };
        setPartes(newPartes);
    };

    const addParty = () => {
        setPartes([...partes, { rol_procesal: 'tercero_interesado', tipo_persona: 'natural', nombre_completo: '' }]);
    };

    const removeParty = (index: number) => {
        const newPartes = partes.filter((_, i) => i !== index);
        setPartes(newPartes);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            // Clean up parties
            const validPartes = partes.filter(p => p.nombre_completo && p.nombre_completo.trim() !== '');

            const payload = {
                ...formData,
                partes: validPartes
            };

            const createdCase = await caseService.create(payload);
            router.push(`/dashboard/cases/${createdCase.id}`);
        } catch (error) {
            console.error('Failed to create case', error);
            alert('Error al crear el expediente. Verifica los datos.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-4xl mx-auto pb-12">
            {/* Header */}
            <div className="flex items-center gap-4 mb-6">
                <Link href="/dashboard/cases" className="btn btn-ghost p-2 text-surface-500 hover:text-primary-600">
                    <ArrowLeft className="w-5 h-5" />
                </Link>
                <div>
                    <h1 className="text-2xl font-bold text-surface-900">Nuevo Expediente</h1>
                    <p className="text-surface-500 text-sm">Registra un nuevo caso judicial</p>
                </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-8">
                {/* Section 1: General Info */}
                <div className="card p-6">
                    <h2 className="text-lg font-semibold text-surface-800 mb-4 border-b border-surface-200 pb-2">
                        Datos Generales
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="md:col-span-2">
                            <label className="label">Resumen / Carátula *</label>
                            <input
                                type="text"
                                name="resumen"
                                required
                                placeholder="Ej: Divorcio Unilateral - Pérez vs. González"
                                className="input w-full"
                                value={formData.resumen || ''}
                                onChange={handleInputChange}
                            />
                        </div>
                        <div>
                            <label className="label">Ramo / Materia *</label>
                            <select
                                name="ramo"
                                required
                                className="input w-full"
                                value={formData.ramo}
                                onChange={handleInputChange}
                            >
                                <option value="civil">Civil</option>
                                <option value="penal">Penal</option>
                                <option value="familia">Familia</option>
                                <option value="laboral">Laboral</option>
                                <option value="mercantil">Mercantil</option>
                                <option value="administrativo">Administrativo</option>
                            </select>
                        </div>
                        <div>
                            <label className="label">Materia Específica</label>
                            <input
                                type="text"
                                name="materia_especifica"
                                placeholder="Ej: Divorcio, Cobro Ejecutivo"
                                className="input w-full"
                                value={formData.materia_especifica || ''}
                                onChange={handleInputChange}
                            />
                        </div>
                        <div>
                            <label className="label">Juzgado de Radicación</label>
                            <input
                                type="text"
                                name="juzgado"
                                placeholder="Ej: Juzgado Segundo Distrito Familia"
                                className="input w-full"
                                value={formData.juzgado || ''}
                                onChange={handleInputChange}
                            />
                        </div>
                        <div>
                            <label className="label">Número de Causa (Judicial)</label>
                            <input
                                type="text"
                                name="numero_causa"
                                placeholder="Ej: 000234-ORM1-2026-FA"
                                className="input w-full"
                                value={formData.numero_causa || ''}
                                onChange={handleInputChange}
                            />
                        </div>
                    </div>
                </div>

                {/* Section 2: Parties */}
                <div className="card p-6">
                    <div className="flex items-center justify-between mb-4 border-b border-surface-200 pb-2">
                        <h2 className="text-lg font-semibold text-surface-800">Partes Procesales</h2>
                        <button type="button" onClick={addParty} className="btn btn-sm btn-ghost text-primary-600">
                            <Plus className="w-4 h-4 mr-1" /> Agregar Parte
                        </button>
                    </div>

                    <div className="space-y-4">
                        {partes.map((parte, index) => (
                            <div key={index} className="flex flex-col md:flex-row gap-4 p-4 bg-surface-50 rounded-lg border border-surface-200 relative group">
                                <div className="flex-1">
                                    <label className="text-xs font-medium text-surface-500 mb-1 block">Rol Procesal</label>
                                    <select
                                        className="input w-full h-9 text-sm"
                                        value={parte.rol_procesal}
                                        onChange={(e) => handlePartyChange(index, 'rol_procesal', e.target.value)}
                                    >
                                        <option value="demandante">Demandante / Actor</option>
                                        <option value="demandado">Demandado</option>
                                        <option value="tercero_interesado">Tercero Interesado</option>
                                        <option value="ministerio_publico">Ministerio Público</option>
                                        <option value="testigo">Testigo</option>
                                    </select>
                                </div>
                                <div className="flex-[2]">
                                    <label className="text-xs font-medium text-surface-500 mb-1 block">Nombre Completo</label>
                                    <div className="relative">
                                        <User className="w-4 h-4 text-surface-400 absolute left-3 top-1/2 -translate-y-1/2" />
                                        <input
                                            type="text"
                                            placeholder="Nombre de la persona o entidad"
                                            className="input w-full h-9 pl-9 text-sm"
                                            value={parte.nombre_completo || ''}
                                            onChange={(e) => handlePartyChange(index, 'nombre_completo', e.target.value)}
                                        />
                                    </div>
                                </div>
                                <div className="w-32">
                                    <label className="text-xs font-medium text-surface-500 mb-1 block">Tipo</label>
                                    <select
                                        className="input w-full h-9 text-sm"
                                        value={parte.tipo_persona}
                                        onChange={(e) => handlePartyChange(index, 'tipo_persona', e.target.value as 'natural' | 'juridica')}
                                    >
                                        <option value="natural">Natural</option>
                                        <option value="juridica">Jurídica</option>
                                    </select>
                                </div>
                                {partes.length > 1 && (
                                    <button
                                        type="button"
                                        onClick={() => removeParty(index)}
                                        className="absolute top-2 right-2 p-1 text-surface-400 hover:text-danger-500 opacity-0 group-hover:opacity-100 transition-opacity"
                                        title="Eliminar"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                )}
                            </div>
                        ))}
                    </div>
                </div>

                {/* Section 3: Extra Info */}
                <div className="card p-6">
                    <h2 className="text-lg font-semibold text-surface-800 mb-4 border-b border-surface-200 pb-2">
                        Detalles Adicionales
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div>
                            <label className="label">Prioridad</label>
                            <select
                                name="prioridad"
                                className="input w-full"
                                value={formData.prioridad}
                                onChange={handleInputChange}
                            >
                                <option value="baja">Baja</option>
                                <option value="normal">Normal</option>
                                <option value="alta">Alta</option>
                                <option value="urgente">Urgente</option>
                            </select>
                        </div>
                        <div>
                            <label className="label">Valor Estimado</label>
                            <div className="flex gap-2">
                                <select
                                    name="moneda"
                                    className="input w-24"
                                    value={formData.moneda}
                                    onChange={handleInputChange}
                                >
                                    <option value="NIO">NIO</option>
                                    <option value="USD">USD</option>
                                </select>
                                <input
                                    type="number"
                                    name="valor_estimado"
                                    placeholder="0.00"
                                    className="input flex-1"
                                    value={formData.valor_estimado || ''}
                                    onChange={handleInputChange}
                                />
                            </div>
                        </div>
                        <div>
                            <label className="label">Fecha Apertura</label>
                            <input
                                type="date"
                                name="fecha_apertura"
                                className="input w-full"
                                value={typeof formData.fecha_apertura === 'string' ? formData.fecha_apertura : ''}
                                onChange={handleInputChange}
                            />
                        </div>
                        <div className="md:col-span-3">
                            <label className="label">Observaciones Iniciales (IA)</label>
                            <textarea
                                name="observaciones_ia"
                                rows={3}
                                className="input w-full h-auto py-2"
                                placeholder="Notas estratégicas iniciales..."
                                value={formData.observaciones_ia || ''}
                                onChange={handleInputChange}
                            />
                        </div>
                    </div>
                </div>

                <div className="flex justify-end gap-4">
                    <Link href="/dashboard/cases" className="btn btn-ghost">Cancelar</Link>
                    <button type="submit" className="btn btn-primary flex items-center gap-2" disabled={loading}>
                        <Save className="w-4 h-4" />
                        {loading ? 'Guardando...' : 'Guardar Expediente'}
                    </button>
                </div>
            </form>
        </div>
    );
}
