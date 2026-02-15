'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Search, Plus, Filter, FileText, Calendar, MoreVertical, Briefcase } from 'lucide-react';
import { caseService } from '@/services/caseService';
import { Expediente } from '@/types/case';

export default function CasesPage() {
    const [cases, setCases] = useState<Expediente[]>([]);
    const [loading, setLoading] = useState(true);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [search, setSearch] = useState('');
    const [ramo, setRamo] = useState('');
    // const [estado, setEstado] = useState(''); // TODO: Fetch statuses

    const fetchCases = async () => {
        setLoading(true);
        try {
            const data = await caseService.getAll({
                page,
                size: 10,
                search: search || undefined,
                ramo: ramo || undefined,
            });
            setCases(data.items);
            setTotal(data.total);
        } catch (error) {
            console.error('Failed to fetch cases', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        // Debounce search? For now, fetch on effect
        const timer = setTimeout(() => {
            fetchCases();
        }, 300);
        return () => clearTimeout(timer);
    }, [page, search, ramo]);

    const ramoOptions = [
        { value: '', label: 'Todos los Ramos' },
        { value: 'civil', label: 'Civil' },
        { value: 'penal', label: 'Penal' },
        { value: 'familia', label: 'Familia' },
        { value: 'laboral', label: 'Laboral' },
        { value: 'mercantil', label: 'Mercantil' },
    ];

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-surface-900">Expedientes</h1>
                    <p className="text-surface-500 text-sm mt-1">Gestiona tus casos legales y procesos judiciales</p>
                </div>
                <Link href="/dashboard/cases/new" className="btn btn-primary flex items-center gap-2">
                    <Plus className="w-4 h-4" />
                    Nuevo Expediente
                </Link>
            </div>

            {/* Filters */}
            <div className="card p-4 flex flex-col sm:flex-row gap-4 items-center">
                <div className="relative flex-1 w-full">
                    <Search className="w-5 h-5 text-surface-400 absolute left-3 top-1/2 -translate-y-1/2" />
                    <input
                        type="text"
                        placeholder="Buscar por número, juzgado o cliente..."
                        className="input pl-10 w-full"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                    />
                </div>
                <div className="flex items-center gap-2 w-full sm:w-auto">
                    <Briefcase className="w-4 h-4 text-surface-500" />
                    <select
                        className="input w-full sm:w-48"
                        value={ramo}
                        onChange={(e) => setRamo(e.target.value)}
                    >
                        {ramoOptions.map(opt => (
                            <option key={opt.value} value={opt.value}>{opt.label}</option>
                        ))}
                    </select>
                </div>
            </div>

            {/* Table */}
            <div className="card overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                        <thead className="bg-surface-50 border-b border-surface-200">
                            <tr>
                                <th className="px-6 py-4 font-semibold text-surface-700">Expediente / Causa</th>
                                <th className="px-6 py-4 font-semibold text-surface-700">Carátula</th>
                                <th className="px-6 py-4 font-semibold text-surface-700">Materia / Juzgado</th>
                                <th className="px-6 py-4 font-semibold text-surface-700">Estado</th>
                                <th className="px-6 py-4 font-semibold text-surface-700">Fecha</th>
                                <th className="px-6 py-4 font-semibold text-surface-700 text-right">Acciones</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-surface-100">
                            {loading ? (
                                <tr>
                                    <td colSpan={6} className="px-6 py-8 text-center text-surface-500">
                                        Cargando expedientes...
                                    </td>
                                </tr>
                            ) : cases.length === 0 ? (
                                <tr>
                                    <td colSpan={6} className="px-6 py-12 text-center">
                                        <div className="flex flex-col items-center">
                                            <div className="w-12 h-12 bg-surface-100 rounded-full flex items-center justify-center mb-3">
                                                <FileText className="w-6 h-6 text-surface-400" />
                                            </div>
                                            <p className="text-surface-900 font-medium">No se encontraron expedientes</p>
                                            <p className="text-surface-500 text-sm">Prueba ajustando los filtros o crea uno nuevo.</p>
                                        </div>
                                    </td>
                                </tr>
                            ) : (
                                cases.map((c) => (
                                    <tr key={c.id} className="hover:bg-surface-50/50 transition-colors">
                                        <td className="px-6 py-4">
                                            <div className="font-medium text-primary-600">{c.numero_interno || 'Sin número'}</div>
                                            <div className="text-xs text-surface-500">{c.numero_causa || '---'}</div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="text-surface-900 font-medium truncate max-w-xs" title={c.resumen || ''}>
                                                {c.resumen ? (c.resumen.length > 40 ? c.resumen.substring(0, 40) + '...' : c.resumen) : 'Sin carátula'}
                                            </div>
                                            <div className="inline-flex items-center gap-1.5 mt-1 px-2 py-0.5 rounded text-xs font-medium bg-surface-100 text-surface-600 capitalize">
                                                {c.ramo}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="text-surface-700">{c.materia_especifica || 'General'}</div>
                                            <div className="text-xs text-surface-500 truncate max-w-[150px]">{c.juzgado || 'Sin asignar'}</div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className="badge bg-green-100 text-green-700">Activo</span>
                                            {/* TODO: Use real status from EstadoExpediente */}
                                        </td>
                                        <td className="px-6 py-4 text-surface-600">
                                            <div className="flex items-center gap-1.5">
                                                <Calendar className="w-3.5 h-3.5" />
                                                {c.fecha_apertura ? new Date(c.fecha_apertura).toLocaleDateString() : '-'}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <Link href={`/dashboard/cases/${c.id}`} className="btn btn-ghost p-2 text-surface-400 hover:text-primary-600">
                                                <MoreVertical className="w-4 h-4" />
                                            </Link>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>

                {/* Pagination */}
                {total > 0 && (
                    <div className="px-6 py-4 border-t border-surface-200 flex items-center justify-between">
                        <p className="text-sm text-surface-500">
                            Mostrando {(page - 1) * 10 + 1} a {Math.min(page * 10, total)} de {total} resultados
                        </p>
                        <div className="flex items-center gap-2">
                            <button
                                onClick={() => setPage(p => Math.max(1, p - 1))}
                                disabled={page === 1}
                                className="btn btn-outline py-1 px-3 text-sm disabled:opacity-50"
                            >
                                Anterior
                            </button>
                            <button
                                onClick={() => setPage(p => p + 1)}
                                disabled={page * 10 >= total}
                                className="btn btn-outline py-1 px-3 text-sm disabled:opacity-50"
                            >
                                Siguiente
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
