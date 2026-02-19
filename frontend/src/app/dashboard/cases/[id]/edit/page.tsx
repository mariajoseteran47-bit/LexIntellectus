'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Save } from 'lucide-react';
import { caseService } from '@/services/caseService';
import { Expediente } from '@/types/case';

export default function EditCasePage() {
    const router = useRouter();
    const params = useParams();
    const id = params.id as string;

    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [formData, setFormData] = useState<Partial<Expediente>>({
        ramo: 'civil',
        prioridad: 'normal',
        moneda: 'NIO',
    });

    useEffect(() => {
        if (id) {
            loadCase();
        }
    }, [id]);

    const loadCase = async () => {
        try {
            const data = await caseService.getById(id);
            // Format date for input type="date"
            if (data.fecha_apertura) {
                data.fecha_apertura = new Date(data.fecha_apertura).toISOString().split('T')[0];
            }
            setFormData(data);
        } catch (error) {
            console.error('Failed to load case', error);
            alert('Error al cargar el expediente');
        } finally {
            setLoading(false);
        }
    };

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setSaving(true);
        try {
            // Remove parties from payload as the current update endpoint doesn't handle them
            const { partes, created_at, updated_at, id: caseId, ...payload } = formData as any;

            await caseService.update(id, payload);
            router.push(`/dashboard/cases/${id}`);
        } catch (error) {
            console.error('Failed to update case', error);
            alert('Error al actualizar el expediente.');
        } finally {
            setSaving(false);
        }
    };

    if (loading) {
        return <div className="p-8 text-center text-surface-500">Cargando expediente...</div>;
    }

    return (
        <div className="max-w-4xl mx-auto pb-12">
            {/* Header */}
            <div className="flex items-center gap-4 mb-6">
                <button
                    onClick={() => router.back()}
                    className="btn btn-ghost p-2 text-surface-500 hover:text-primary-600"
                >
                    <ArrowLeft className="w-5 h-5" />
                </button>
                <div>
                    <h1 className="text-2xl font-bold text-surface-900">Editar Expediente</h1>
                    <p className="text-surface-500 text-sm">Actualiza la información del caso {formData.numero_interno}</p>
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
                    <button type="button" onClick={() => router.back()} className="btn btn-ghost">Cancelar</button>
                    <button type="submit" className="btn btn-primary flex items-center gap-2" disabled={saving}>
                        <Save className="w-4 h-4" />
                        {saving ? 'Guardando...' : 'Actualizar Expediente'}
                    </button>
                </div>
            </form>
        </div>
    );
}
