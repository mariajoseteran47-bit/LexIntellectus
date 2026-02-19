'use client';

import { useState, useEffect } from 'react';
import { Calendar, Clock, AlertCircle, ExternalLink } from 'lucide-react';
import { deadlineService, Deadline } from '@/services/deadlineService';
import Link from 'next/link';

export default function AgendaPage() {
    const [deadlines, setDeadlines] = useState<Deadline[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchDeadlines();
    }, []);

    const fetchDeadlines = async () => {
        try {
            const data = await deadlineService.getAll({ status: 'pendiente' });
            setDeadlines(data);
        } catch (error) {
            console.error('Failed to fetch deadlines', error);
        } finally {
            setLoading(false);
        }
    };

    const getStatusInfo = (d: Deadline) => {
        const today = new Date();
        const dueDate = new Date(d.fecha_vencimiento);
        const diffTime = dueDate.getTime() - today.getTime();
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

        if (diffDays < 0) return { label: 'Vencido', classes: 'bg-red-100 text-red-700' };
        if (diffDays === 0) return { label: 'Vence Hoy', classes: 'bg-orange-100 text-orange-700 animate-pulse' };
        if (diffDays <= 3) return { label: `Próximo (${diffDays}d)`, classes: 'bg-orange-50 text-orange-600' };

        return { label: 'Pendiente', classes: 'bg-blue-50 text-blue-600' };
    };

    if (loading) {
        return <div className="p-8 text-center text-surface-500">Cargando agenda...</div>;
    }

    return (
        <div className="space-y-6 animate-fade-in">
            <div className="flex flex-col gap-2">
                <h1 className="text-2xl font-bold text-surface-900 flex items-center gap-3">
                    <Calendar className="w-8 h-8 text-primary-500" />
                    Agenda de Plazos
                </h1>
                <p className="text-surface-500">Gestiona tus plazos fatales y recordatorios judiciales.</p>
            </div>

            <div className="card overflow-hidden">
                <div className="p-4 border-b border-surface-200 bg-surface-50 flex justify-between items-center">
                    <h2 className="font-semibold text-surface-800">Próximos Vencimientos</h2>
                    <span className="badge bg-primary-100 text-primary-700">{deadlines.length} Plazos Pendientes</span>
                </div>

                {deadlines.length === 0 ? (
                    <div className="p-12 text-center space-y-4">
                        <div className="w-16 h-16 bg-surface-100 rounded-full flex items-center justify-center mx-auto">
                            <Clock className="w-8 h-8 text-surface-400" />
                        </div>
                        <p className="text-surface-500 font-medium">No tienes plazos pendientes registrados.</p>
                    </div>
                ) : (
                    <div className="divide-y divide-surface-100">
                        {deadlines.map((d) => {
                            const status = getStatusInfo(d);
                            return (
                                <div key={d.id} className="p-4 hover:bg-surface-50/50 transition-colors flex flex-col md:flex-row md:items-center justify-between gap-4">
                                    <div className="flex gap-4">
                                        <div className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 ${d.prioridad === 'critica' ? 'bg-red-50 text-red-500' : 'bg-primary-50 text-primary-500'}`}>
                                            <AlertCircle className="w-6 h-6" />
                                        </div>
                                        <div>
                                            <h3 className="font-bold text-surface-900">{d.descripcion}</h3>
                                            <div className="flex flex-wrap gap-x-4 gap-y-1 mt-1 text-sm text-surface-500">
                                                <span className="flex items-center gap-1">
                                                    <Calendar className="w-4 h-4" /> {new Date(d.fecha_vencimiento).toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
                                                </span>
                                                {d.hora_vencimiento && (
                                                    <span className="flex items-center gap-1">
                                                        <Clock className="w-4 h-4" /> {d.hora_vencimiento.substring(0, 5)}
                                                    </span>
                                                )}
                                            </div>
                                            {d.base_legal && <p className="text-xs text-surface-400 mt-1 italic">Base Legal: {d.base_legal}</p>}
                                        </div>
                                    </div>

                                    <div className="flex items-center justify-between md:justify-end gap-4 w-full md:w-auto mt-2 md:mt-0">
                                        <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${status.classes}`}>
                                            {status.label}
                                        </span>
                                        <Link
                                            href={`/dashboard/cases/${d.expediente_id}`}
                                            className="btn btn-sm btn-ghost gap-2 text-primary-600 hover:text-primary-700"
                                        >
                                            Ver Expediente <ExternalLink className="w-3 h-3" />
                                        </Link>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
}
