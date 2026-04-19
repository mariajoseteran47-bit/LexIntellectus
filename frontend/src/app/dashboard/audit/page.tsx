'use client';

import { useState, useEffect } from 'react';
import {
    Shield, Filter, ChevronLeft, ChevronRight,
    Eye, Activity, Users, Briefcase, FileText,
    Clock, Bot, Download, LogIn, LogOut
} from 'lucide-react';
import { auditService, AuditLogEntry, AuditFilterParams } from '@/services/auditService';

const actionConfig: Record<string, { label: string; color: string; icon: any }> = {
    crear:        { label: 'Creación',       color: 'bg-green-100 text-green-700',   icon: FileText },
    actualizar:   { label: 'Actualización',  color: 'bg-blue-100 text-blue-700',     icon: Activity },
    eliminar:     { label: 'Eliminación',    color: 'bg-red-100 text-red-700',       icon: FileText },
    login:        { label: 'Inicio Sesión',  color: 'bg-violet-100 text-violet-700', icon: LogIn },
    logout:       { label: 'Cierre Sesión',  color: 'bg-surface-100 text-surface-600', icon: LogOut },
    consulta_ia:  { label: 'Consulta IA',    color: 'bg-amber-100 text-amber-700',   icon: Bot },
    descarga:     { label: 'Descarga',       color: 'bg-cyan-100 text-cyan-700',     icon: Download },
};

const entityConfig: Record<string, { label: string; icon: any }> = {
    expediente: { label: 'Expediente',     icon: Briefcase },
    plazo:      { label: 'Plazo Fatal',    icon: Clock },
    documento:  { label: 'Documento',      icon: FileText },
    usuario:    { label: 'Usuario',        icon: Users },
    tenant:     { label: 'Despacho',       icon: Shield },
    parte:      { label: 'Parte Procesal', icon: Users },
};

export default function AuditPage() {
    const [logs, setLogs] = useState<AuditLogEntry[]>([]);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [total, setTotal] = useState(0);
    const [size] = useState(20);
    const [filterAccion, setFilterAccion] = useState('');
    const [filterEntidad, setFilterEntidad] = useState('');
    const [selectedLog, setSelectedLog] = useState<AuditLogEntry | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchLogs();
    }, [page, filterAccion, filterEntidad]);

    const fetchLogs = async () => {
        setLoading(true);
        setError(null);
        try {
            const params: AuditFilterParams = { page, size };
            if (filterAccion) (params as any).accion = filterAccion;
            if (filterEntidad) (params as any).entidad = filterEntidad;

            const data = await auditService.getAll(params);
            setLogs(data.items || []);
            setTotal(data.total || 0);
        } catch (e: any) {
            console.error('Failed to load audit logs', e);
            setError('No se pudieron cargar los registros de auditoría.');
        } finally {
            setLoading(false);
        }
    };

    const totalPages = Math.ceil(total / size);

    const formatDate = (d: string | null | undefined) => {
        if (!d) return '—';
        return new Date(d).toLocaleString('es-NI', {
            year: 'numeric', month: 'short', day: '2-digit',
            hour: '2-digit', minute: '2-digit',
        });
    };

    const formatRelativeTime = (d: string | null | undefined) => {
        if (!d) return '';
        const now = new Date().getTime();
        const then = new Date(d).getTime();
        const diff = now - then;
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);

        if (minutes < 1) return 'Justo ahora';
        if (minutes < 60) return `Hace ${minutes}m`;
        if (hours < 24) return `Hace ${hours}h`;
        if (days < 7) return `Hace ${days}d`;
        return '';
    };

    // Stats
    const todayLogs = logs.filter(l => {
        if (!l.created_at) return false;
        return new Date(l.created_at).toDateString() === new Date().toDateString();
    }).length;

    return (
        <div className="space-y-6 animate-fade-in">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-surface-900 flex items-center gap-3">
                        <Shield className="w-6 h-6 text-primary-500" />
                        Registro de Auditoría
                    </h1>
                    <p className="text-surface-500 text-sm mt-1">
                        Historial completo de acciones realizadas en el sistema
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <div className="text-right">
                        <p className="text-2xl font-bold text-surface-800">{total}</p>
                        <p className="text-xs text-surface-500">registros totales</p>
                    </div>
                    <div className="w-px h-10 bg-surface-200" />
                    <div className="text-right">
                        <p className="text-2xl font-bold text-primary-600">{todayLogs}</p>
                        <p className="text-xs text-surface-500">hoy</p>
                    </div>
                </div>
            </div>

            {/* Filters */}
            <div className="card p-4 flex flex-wrap items-center gap-3">
                <Filter className="w-4 h-4 text-surface-400" />
                <select
                    value={filterAccion}
                    onChange={(e) => { setFilterAccion(e.target.value); setPage(1); }}
                    className="text-sm border border-surface-200 rounded-lg px-3 py-1.5 bg-white text-surface-700 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                >
                    <option value="">Todas las acciones</option>
                    <option value="crear">🟢 Creación</option>
                    <option value="actualizar">🔵 Actualización</option>
                    <option value="eliminar">🔴 Eliminación</option>
                    <option value="login">🟣 Login</option>
                    <option value="logout">⚪ Logout</option>
                    <option value="consulta_ia">🟡 Consulta IA</option>
                    <option value="descarga">🔷 Descarga</option>
                </select>
                <select
                    value={filterEntidad}
                    onChange={(e) => { setFilterEntidad(e.target.value); setPage(1); }}
                    className="text-sm border border-surface-200 rounded-lg px-3 py-1.5 bg-white text-surface-700 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                >
                    <option value="">Todas las entidades</option>
                    <option value="expediente">📁 Expediente</option>
                    <option value="plazo">⏰ Plazo Fatal</option>
                    <option value="documento">📄 Documento</option>
                    <option value="usuario">👤 Usuario</option>
                    <option value="tenant">🏛️ Despacho</option>
                </select>
                {(filterAccion || filterEntidad) && (
                    <button
                        onClick={() => { setFilterAccion(''); setFilterEntidad(''); setPage(1); }}
                        className="text-xs text-primary-600 hover:text-primary-700 font-medium"
                    >
                        Limpiar filtros
                    </button>
                )}
                <span className="text-xs text-surface-400 ml-auto">{total} registros</span>
            </div>

            {/* Error */}
            {error && (
                <div className="card p-4 bg-red-50 border border-red-200 text-red-700 text-sm flex items-center gap-2">
                    <Shield className="w-4 h-4" />
                    {error}
                    <button onClick={fetchLogs} className="ml-auto text-xs font-semibold underline">Reintentar</button>
                </div>
            )}

            {/* Table */}
            <div className="card overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                        <thead className="bg-surface-50">
                            <tr>
                                <th className="px-5 py-3 font-semibold text-surface-700">Fecha</th>
                                <th className="px-5 py-3 font-semibold text-surface-700">Acción</th>
                                <th className="px-5 py-3 font-semibold text-surface-700">Entidad</th>
                                <th className="px-5 py-3 font-semibold text-surface-700">IP</th>
                                <th className="px-5 py-3 text-right">Detalle</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-surface-100">
                            {loading ? (
                                <tr><td colSpan={5} className="px-5 py-12 text-center text-surface-500">
                                    <div className="w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                                    Cargando registros...
                                </td></tr>
                            ) : logs.length === 0 ? (
                                <tr><td colSpan={5} className="px-5 py-12 text-center text-surface-500">
                                    <Shield className="w-10 h-10 text-surface-200 mx-auto mb-2" />
                                    <p className="font-medium">No hay registros de auditoría</p>
                                    <p className="text-xs text-surface-400 mt-1">Las acciones del sistema se registrarán aquí automáticamente</p>
                                </td></tr>
                            ) : (
                                logs.map((log) => {
                                    const action = actionConfig[log.accion] || { label: log.accion, color: 'bg-surface-100 text-surface-600', icon: Activity };
                                    const entity = entityConfig[log.entidad] || { label: log.entidad, icon: FileText };
                                    const ActionIcon = action.icon;
                                    const EntityIcon = entity.icon;
                                    const relTime = formatRelativeTime(log.created_at);

                                    return (
                                        <tr key={log.id} className="hover:bg-surface-50/50 transition-colors group">
                                            <td className="px-5 py-3.5">
                                                <p className="text-surface-700 text-xs whitespace-nowrap">{formatDate(log.created_at)}</p>
                                                {relTime && <p className="text-[10px] text-surface-400 mt-0.5">{relTime}</p>}
                                            </td>
                                            <td className="px-5 py-3.5">
                                                <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold ${action.color}`}>
                                                    <ActionIcon className="w-3 h-3" />
                                                    {action.label}
                                                </span>
                                            </td>
                                            <td className="px-5 py-3.5">
                                                <div className="flex items-center gap-2">
                                                    <EntityIcon className="w-4 h-4 text-surface-400" />
                                                    <div>
                                                        <span className="text-surface-800 font-medium">{entity.label}</span>
                                                        {log.entidad_id && (
                                                            <span className="text-[10px] text-surface-400 block mt-0.5 font-mono">
                                                                ...{log.entidad_id.slice(-8)}
                                                            </span>
                                                        )}
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="px-5 py-3.5 text-xs text-surface-500 font-mono">
                                                {log.ip_address || '—'}
                                            </td>
                                            <td className="px-5 py-3.5 text-right">
                                                <button
                                                    onClick={() => setSelectedLog(log)}
                                                    className="text-primary-600 hover:text-primary-700 p-1.5 rounded-lg hover:bg-primary-50 transition-colors opacity-0 group-hover:opacity-100"
                                                    title="Ver detalle"
                                                >
                                                    <Eye className="w-4 h-4" />
                                                </button>
                                            </td>
                                        </tr>
                                    );
                                })
                            )}
                        </tbody>
                    </table>
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                    <div className="px-5 py-3 border-t border-surface-200 flex items-center justify-between bg-surface-50/50">
                        <span className="text-xs text-surface-500">
                            Página {page} de {totalPages} ({total} registros)
                        </span>
                        <div className="flex items-center gap-1">
                            <button
                                onClick={() => setPage(p => Math.max(1, p - 1))}
                                disabled={page <= 1}
                                className="p-1.5 rounded-lg hover:bg-surface-200 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                            >
                                <ChevronLeft className="w-4 h-4" />
                            </button>
                            {/* Page numbers */}
                            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                                const p = Math.max(1, Math.min(page - 2, totalPages - 4)) + i;
                                if (p > totalPages) return null;
                                return (
                                    <button
                                        key={p}
                                        onClick={() => setPage(p)}
                                        className={`w-8 h-8 rounded-lg text-xs font-medium transition-colors ${
                                            p === page
                                                ? 'bg-primary-600 text-white'
                                                : 'text-surface-600 hover:bg-surface-200'
                                        }`}
                                    >
                                        {p}
                                    </button>
                                );
                            })}
                            <button
                                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                                disabled={page >= totalPages}
                                className="p-1.5 rounded-lg hover:bg-surface-200 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                            >
                                <ChevronRight className="w-4 h-4" />
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {/* Detail Modal */}
            {selectedLog && (
                <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => setSelectedLog(null)}>
                    <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg animate-slide-up overflow-hidden" onClick={(e) => e.stopPropagation()}>
                        <div className="px-6 py-4 border-b border-surface-100 bg-surface-50 flex items-center justify-between">
                            <h3 className="font-bold text-surface-800 flex items-center gap-2">
                                <Shield className="w-4 h-4 text-primary-500" />
                                Detalle de Auditoría
                            </h3>
                            <button onClick={() => setSelectedLog(null)} className="text-surface-400 hover:text-surface-600 text-xl">&times;</button>
                        </div>
                        <div className="p-6 space-y-4">
                            <div className="grid grid-cols-2 gap-4 text-sm">
                                <div>
                                    <p className="text-xs text-surface-500 mb-1">Acción</p>
                                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold ${(actionConfig[selectedLog.accion] || { color: 'bg-surface-100 text-surface-600' }).color}`}>
                                        {(actionConfig[selectedLog.accion] || { label: selectedLog.accion }).label}
                                    </span>
                                </div>
                                <div>
                                    <p className="text-xs text-surface-500 mb-1">Entidad</p>
                                    <p className="font-medium text-surface-800">{(entityConfig[selectedLog.entidad] || { label: selectedLog.entidad }).label}</p>
                                </div>
                                <div>
                                    <p className="text-xs text-surface-500 mb-1">Fecha</p>
                                    <p className="text-surface-700">{formatDate(selectedLog.created_at)}</p>
                                </div>
                                <div>
                                    <p className="text-xs text-surface-500 mb-1">IP</p>
                                    <p className="font-mono text-surface-700">{selectedLog.ip_address || '—'}</p>
                                </div>
                                {selectedLog.entidad_id && (
                                    <div className="col-span-2">
                                        <p className="text-xs text-surface-500 mb-1">ID de Entidad</p>
                                        <p className="font-mono text-xs text-surface-600 bg-surface-50 px-3 py-1.5 rounded-lg">{selectedLog.entidad_id}</p>
                                    </div>
                                )}
                            </div>

                            {selectedLog.detalles && (
                                <div>
                                    <p className="text-xs font-semibold text-surface-500 mb-1.5">Datos del Cambio</p>
                                    <pre className="text-xs bg-surface-50 border border-surface-200 rounded-lg p-3 overflow-auto max-h-40 text-surface-700">
                                        {JSON.stringify(selectedLog.detalles, null, 2)}
                                    </pre>
                                </div>
                            )}

                            {!selectedLog.detalles && (
                                <div className="text-center py-4 text-surface-400 text-sm">
                                    No hay datos de detalle disponibles para esta acción.
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
