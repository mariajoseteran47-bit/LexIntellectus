'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Clock, Users, FileText, Activity, Plus, MoreVertical, Edit2 } from 'lucide-react';
import { caseService } from '@/services/caseService';
import { Expediente } from '@/types/case';
import DeadlineList from '@/components/deadlines/DeadlineList';
import DocumentList from '@/components/documents/DocumentList';
import CaseTheoryAnalysis from '@/components/cases/CaseTheoryAnalysis';

export default function CaseDetailPage({ params }: { params: { id: string } }) {
    const [caseData, setCaseData] = useState<Expediente | null>(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('general');

    useEffect(() => {
        if (params.id) {
            loadCase(params.id);
        }
    }, [params.id]);

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

    if (loading) {
        return <div className="p-8 text-center">Cargando expediente...</div>;
    }

    if (!caseData) {
        return <div className="p-8 text-center">Expediente no encontrado</div>;
    }

    return (
        <div className="pb-12 space-y-6">
            {/* Header */}
            <div className="flex flex-col gap-4">
                <Link href="/dashboard/cases" className="text-surface-500 hover:text-primary-600 flex items-center gap-2 w-fit">
                    <ArrowLeft className="w-4 h-4" /> Volver al listado
                </Link>

                <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                    <div>
                        <div className="flex items-center gap-3 mb-1">
                            <h1 className="text-2xl font-bold text-surface-900">{caseData.numero_interno || 'Sin Número'}</h1>
                            <span className="badge bg-green-100 text-green-700">Activo</span>
                        </div>
                        <h2 className="text-lg text-surface-700 font-medium">{caseData.resumen}</h2>
                        <div className="flex items-center gap-4 mt-2 text-sm text-surface-500">
                            <div className="flex items-center gap-1.5">
                                <FileText className="w-4 h-4" />
                                {caseData.numero_causa || 'Sin Causa Judicial'}
                            </div>
                            <div className="flex items-center gap-1.5">
                                <Activity className="w-4 h-4" />
                                {caseData.ramo} - {caseData.materia_especifica}
                            </div>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <button className="btn btn-outline flex items-center gap-2">
                            <Edit2 className="w-4 h-4" /> Editar
                        </button>
                        <button className="btn btn-primary flex items-center gap-2">
                            <Plus className="w-4 h-4" /> Nueva Actuación
                        </button>
                    </div>
                </div>
            </div>

            {/* Tabs */}
            <div className="border-b border-surface-200">
                <nav className="flex gap-6">
                    <button
                        onClick={() => setActiveTab('general')}
                        className={`pb-3 text-sm font-medium border-b-2 transition-colors ${activeTab === 'general'
                            ? 'border-primary-500 text-primary-600'
                            : 'border-transparent text-surface-500 hover:text-surface-700'
                            }`}
                    >
                        Información General
                    </button>
                    <button
                        onClick={() => setActiveTab('partes')}
                        className={`pb-3 text-sm font-medium border-b-2 transition-colors ${activeTab === 'partes'
                            ? 'border-primary-500 text-primary-600'
                            : 'border-transparent text-surface-500 hover:text-surface-700'
                            }`}
                    >
                        Partes Procesales <span className="ml-1 px-1.5 py-0.5 rounded-full bg-surface-100 text-xs">{caseData.partes?.length || 0}</span>
                    </button>
                    <button
                        onClick={() => setActiveTab('plazos')}
                        className={`pb-3 text-sm font-medium border-b-2 transition-colors ${activeTab === 'plazos'
                            ? 'border-primary-500 text-primary-600'
                            : 'border-transparent text-surface-500 hover:text-surface-700'
                            }`}
                    >
                        Plazos Fatales
                    </button>
                    <button
                        onClick={() => setActiveTab('documentos')}
                        className={`pb-3 text-sm font-medium border-b-2 transition-colors ${activeTab === 'documentos'
                            ? 'border-primary-500 text-primary-600'
                            : 'border-transparent text-surface-500 hover:text-surface-700'
                            }`}
                    >
                        Documentos
                    </button>
                    <button
                        onClick={() => setActiveTab('ia')}
                        className={`pb-3 text-sm font-medium border-b-2 transition-colors ${activeTab === 'ia'
                            ? 'border-accent-400 text-accent-500'
                            : 'border-transparent text-surface-500 hover:text-surface-700'
                            }`}
                    >
                        Análisis IA <span className="ml-1 badge bg-accent-400/10 text-accent-500 text-[10px]">PRO</span>
                    </button>
                </nav>
            </div>

            {/* Tab Content */}
            <div className="animate-fade-in">
                {activeTab === 'general' && (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div className="card p-6 md:col-span-2 space-y-6">
                            <h3 className="font-semibold text-surface-800 border-b border-surface-100 pb-2">Datos del Proceso</h3>
                            <div className="grid grid-cols-2 gap-y-4">
                                <div>
                                    <label className="text-xs text-surface-500 block">Juzgado</label>
                                    <p className="text-surface-900 font-medium">{caseData.juzgado || '—'}</p>
                                </div>
                                <div>
                                    <label className="text-xs text-surface-500 block">Juez</label>
                                    <p className="text-surface-900 font-medium">{caseData.juez || '—'}</p>
                                </div>
                                <div>
                                    <label className="text-xs text-surface-500 block">Secretario</label>
                                    <p className="text-surface-900 font-medium">{caseData.secretario || '—'}</p>
                                </div>
                                <div>
                                    <label className="text-xs text-surface-500 block">Fecha Apertura</label>
                                    <p className="text-surface-900 font-medium">
                                        {caseData.fecha_apertura ? new Date(caseData.fecha_apertura).toLocaleDateString() : '—'}
                                    </p>
                                </div>
                            </div>

                            <h3 className="font-semibold text-surface-800 border-b border-surface-100 pb-2 pt-4">Valoración</h3>
                            <div className="grid grid-cols-2 gap-y-4">
                                <div>
                                    <label className="text-xs text-surface-500 block">Cuantía</label>
                                    <p className="text-surface-900 font-medium">
                                        {caseData.moneda} {caseData.valor_estimado?.toLocaleString() || '0.00'}
                                    </p>
                                </div>
                                <div>
                                    <label className="text-xs text-surface-500 block">Prioridad</label>
                                    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium uppercase ${caseData.prioridad === 'urgente' ? 'bg-red-100 text-red-700' :
                                        caseData.prioridad === 'alta' ? 'bg-orange-100 text-orange-700' :
                                            'bg-blue-100 text-blue-700'
                                        }`}>
                                        {caseData.prioridad}
                                    </span>
                                </div>
                            </div>
                        </div>

                        <div className="card p-6 bg-accent-50/30 border-accent-100">
                            <h3 className="font-semibold text-accent-700 mb-4 flex items-center gap-2">
                                <span className="text-lg">🤖</span> Análisis Legal IA
                            </h3>
                            <p className="text-sm text-surface-700 leading-relaxed">
                                {caseData.observaciones_ia || 'No hay observaciones generadas por la IA para este caso.'}
                            </p>
                            <button className="btn btn-sm bg-white border border-accent-200 text-accent-700 mt-4 hover:bg-accent-50 w-full">
                                Generar nuevo análisis
                            </button>
                        </div>
                    </div>
                )}

                {activeTab === 'partes' && (
                    <div className="card overflow-hidden">
                        <div className="p-4 border-b border-surface-200 flex justify-between items-center bg-surface-50">
                            <h3 className="font-semibold text-surface-800">Sujetos Procesales</h3>
                            <button className="btn btn-sm btn-outline gap-2">
                                <Plus className="w-4 h-4" /> Agregar Parte
                            </button>
                        </div>
                        <table className="w-full text-left text-sm">
                            <thead className="bg-white border-b border-surface-200">
                                <tr>
                                    <th className="px-6 py-3 font-semibold text-surface-600">Nombre</th>
                                    <th className="px-6 py-3 font-semibold text-surface-600">Rol Procesal</th>
                                    <th className="px-6 py-3 font-semibold text-surface-600">Tipo</th>
                                    <th className="px-6 py-3 text-right">Acciones</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-surface-100">
                                {caseData.partes?.map((parte) => (
                                    <tr key={parte.id}>
                                        <td className="px-6 py-4 font-medium text-surface-900">{parte.nombre_completo}</td>
                                        <td className="px-6 py-4">
                                            <span className="capitalize bg-surface-100 px-2 py-1 rounded text-surface-700 text-xs">
                                                {parte.rol_procesal.replace('_', ' ')}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 capitalize text-surface-600">{parte.tipo_persona}</td>
                                        <td className="px-6 py-4 text-right">
                                            <button className="text-surface-400 hover:text-primary-600">
                                                <MoreVertical className="w-4 h-4" />
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                                {(!caseData.partes || caseData.partes.length === 0) && (
                                    <tr>
                                        <td colSpan={4} className="px-6 py-8 text-center text-surface-500">
                                            No hay partes registradas.
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                )}

                {activeTab === 'plazos' && (
                    <DeadlineList caseId={caseData.id} />
                )}

                {activeTab === 'documentos' && (
                    <DocumentList caseId={caseData.id} />
                )}

                {activeTab === 'ia' && (
                    <CaseTheoryAnalysis caseId={caseData.id} />
                )}
            </div>
        </div>
    );
}
