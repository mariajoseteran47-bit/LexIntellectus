'use client';

import { useState, useEffect } from 'react';
import {
    BarChart3, Download, Calendar, Briefcase, Clock,
    TrendingUp, FileText, Users, ArrowUpRight, ArrowDownRight,
    AlertTriangle, Scale, User
} from 'lucide-react';
import { reportService, ReportOverview } from '@/services/reportService';

export default function ReportsPage() {
    const [report, setReport] = useState<ReportOverview | null>(null);
    const [loading, setLoading] = useState(true);
    const [period, setPeriod] = useState('month');
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchReport();
    }, [period]);

    const fetchReport = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await reportService.getOverview(period);
            setReport(data);
        } catch (e: any) {
            console.error('Failed to load report', e);
            setError('No se pudieron cargar los reportes. Verifica la conexión.');
        } finally {
            setLoading(false);
        }
    };

    // Color mapping for ramo bars
    const ramoColors: Record<string, string> = {
        civil: 'from-blue-400 to-blue-600',
        penal: 'from-red-400 to-red-600',
        familia: 'from-pink-400 to-pink-600',
        laboral: 'from-amber-400 to-amber-600',
        mercantil: 'from-emerald-400 to-emerald-600',
        constitucional: 'from-violet-400 to-violet-600',
        sucesiones: 'from-cyan-400 to-cyan-600',
        administrativo: 'from-orange-400 to-orange-600',
    };

    // Color mapping for status
    const statusColorMap: Record<string, string> = {
        '#3B82F6': 'bg-blue-500',
        '#F59E0B': 'bg-amber-500',
        '#10B981': 'bg-green-500',
        '#6B7280': 'bg-surface-400',
        '#EF4444': 'bg-red-500',
        '#8B5CF6': 'bg-violet-500',
    };

    const getStatusColor = (hexColor: string | null) => {
        if (!hexColor) return 'bg-surface-400';
        return statusColorMap[hexColor] || 'bg-primary-500';
    };

    // Priority color/label mapping
    const priorityConfig: Record<string, { label: string; color: string; icon: any }> = {
        baja: { label: 'Baja', color: 'text-surface-500 bg-surface-100', icon: null },
        normal: { label: 'Normal', color: 'text-blue-600 bg-blue-50', icon: null },
        alta: { label: 'Alta', color: 'text-amber-600 bg-amber-50', icon: AlertTriangle },
        urgente: { label: 'Urgente', color: 'text-red-600 bg-red-50', icon: AlertTriangle },
    };

    if (loading) {
        return (
            <div className="p-8 flex flex-col items-center justify-center gap-3">
                <div className="w-10 h-10 border-3 border-primary-500 border-t-transparent rounded-full animate-spin" />
                <p className="text-surface-500 text-sm">Generando reportes...</p>
            </div>
        );
    }

    if (error || !report) {
        return (
            <div className="p-8 text-center space-y-4">
                <AlertTriangle className="w-12 h-12 text-amber-500 mx-auto" />
                <p className="text-surface-600 font-medium">{error || 'Sin datos disponibles'}</p>
                <button onClick={fetchReport} className="btn btn-primary btn-sm">Reintentar</button>
            </div>
        );
    }

    const { kpis } = report;

    return (
        <div className="space-y-6 animate-fade-in">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-surface-900 flex items-center gap-3">
                        <BarChart3 className="w-6 h-6 text-primary-500" />
                        Reportes y Estadísticas
                    </h1>
                    <p className="text-surface-500 text-sm mt-1">
                        Análisis de productividad y gestión del despacho
                        <span className="text-surface-400 ml-2">
                            ({report.date_range.start} — {report.date_range.end})
                        </span>
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    {/* Period Toggle */}
                    <div className="flex items-center bg-surface-100 rounded-lg p-0.5">
                        {[
                            { key: 'week', label: 'Semana' },
                            { key: 'month', label: 'Mes' },
                            { key: 'quarter', label: 'Trimestre' },
                            { key: 'year', label: 'Año' },
                        ].map((p) => (
                            <button
                                key={p.key}
                                onClick={() => setPeriod(p.key)}
                                className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
                                    period === p.key ? 'bg-white shadow-sm text-primary-600' : 'text-surface-500 hover:text-surface-700'
                                }`}
                            >
                                {p.label}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
                {[
                    {
                        label: 'Expedientes Activos',
                        value: kpis.active_cases,
                        sub: `${kpis.new_cases_period} nuevos este período`,
                        icon: Briefcase,
                        gradient: 'from-blue-500 to-blue-600',
                    },
                    {
                        label: 'Plazos Pendientes',
                        value: kpis.pending_deadlines,
                        sub: kpis.overdue_deadlines > 0
                            ? `⚠️ ${kpis.overdue_deadlines} vencidos`
                            : `${kpis.urgent_deadlines} urgentes`,
                        icon: Clock,
                        gradient: kpis.overdue_deadlines > 0 ? 'from-red-500 to-red-600' : 'from-amber-500 to-orange-500',
                    },
                    {
                        label: 'Tasa de Resolución',
                        value: `${kpis.resolution_rate}%`,
                        sub: `${kpis.closed_cases_period} cerrados este período`,
                        icon: TrendingUp,
                        gradient: 'from-emerald-500 to-green-600',
                    },
                    {
                        label: 'Documentos del Período',
                        value: kpis.docs_period,
                        sub: `${kpis.active_clients} clientes activos`,
                        icon: FileText,
                        gradient: 'from-violet-500 to-purple-600',
                    },
                ].map((kpi, i) => (
                    <div key={i} className="card p-0 overflow-hidden">
                        <div className={`h-1.5 bg-gradient-to-r ${kpi.gradient}`} />
                        <div className="p-5">
                            <div className="flex items-start justify-between">
                                <div>
                                    <p className="text-xs font-medium text-surface-500 uppercase tracking-wide">{kpi.label}</p>
                                    <p className="text-3xl font-bold text-surface-900 mt-1">{kpi.value}</p>
                                </div>
                                <kpi.icon className="w-5 h-5 text-surface-300" />
                            </div>
                            <p className="text-xs text-surface-500 mt-2">{kpi.sub}</p>
                        </div>
                    </div>
                ))}
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Cases by Ramo */}
                <div className="card p-6">
                    <h3 className="font-semibold text-surface-800 mb-5 flex items-center gap-2">
                        <Scale className="w-4 h-4 text-primary-500" />
                        Expedientes por Materia
                    </h3>
                    {report.cases_by_ramo.length === 0 ? (
                        <p className="text-sm text-surface-400 text-center py-8">Sin datos de expedientes</p>
                    ) : (
                        <div className="space-y-4">
                            {report.cases_by_ramo.map((item) => (
                                <div key={item.name}>
                                    <div className="flex items-center justify-between text-sm mb-1.5">
                                        <span className="font-medium text-surface-700">{item.name}</span>
                                        <span className="text-surface-500">{item.count} ({item.pct}%)</span>
                                    </div>
                                    <div className="w-full bg-surface-100 rounded-full h-2.5">
                                        <div
                                            className={`h-2.5 rounded-full bg-gradient-to-r ${
                                                ramoColors[item.name.toLowerCase()] || 'from-primary-400 to-primary-600'
                                            } transition-all duration-700`}
                                            style={{ width: `${Math.max(item.pct, 3)}%` }}
                                        />
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Status Distribution */}
                <div className="card p-6">
                    <h3 className="font-semibold text-surface-800 mb-5 flex items-center gap-2">
                        <TrendingUp className="w-4 h-4 text-primary-500" />
                        Estado de Expedientes
                    </h3>

                    {report.status_distribution.length === 0 ? (
                        <p className="text-sm text-surface-400 text-center py-8">Sin estados configurados</p>
                    ) : (
                        <>
                            {/* Stacked Bar */}
                            <div className="flex rounded-xl overflow-hidden h-8 mb-6">
                                {report.status_distribution.map((item) => (
                                    <div
                                        key={item.label}
                                        className={`${getStatusColor(item.color_hex)} transition-all duration-500`}
                                        style={{ width: `${Math.max(item.pct, 2)}%` }}
                                        title={`${item.label}: ${item.count}`}
                                    />
                                ))}
                            </div>

                            <div className="grid grid-cols-2 gap-3">
                                {report.status_distribution.map((item) => (
                                    <div key={item.label} className="flex items-center gap-2.5 p-2.5 rounded-lg bg-surface-50">
                                        <div className={`w-3 h-3 rounded-full ${getStatusColor(item.color_hex)}`} />
                                        <div>
                                            <p className="text-sm font-medium text-surface-700">{item.label}</p>
                                            <p className="text-xs text-surface-500">{item.count} expedientes ({item.pct}%)</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </>
                    )}
                </div>
            </div>

            {/* Monthly Activity — Mini bar chart */}
            <div className="card p-6">
                <div className="flex items-center justify-between mb-5">
                    <h3 className="font-semibold text-surface-800 flex items-center gap-2">
                        <Calendar className="w-4 h-4 text-primary-500" />
                        Actividad Mensual
                    </h3>
                    <div className="flex items-center gap-4 text-xs text-surface-500">
                        <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-sm bg-primary-500" /> Expedientes</span>
                        <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-sm bg-accent-400" /> Plazos</span>
                    </div>
                </div>
                <div className="flex items-end gap-6 h-40">
                    {report.monthly_activity.map((m) => {
                        const maxVal = Math.max(
                            ...report.monthly_activity.flatMap(x => [x.cases, x.deadlines]),
                            1 // Prevent division by zero
                        );
                        return (
                            <div key={`${m.month}-${m.year}`} className="flex-1 flex flex-col items-center gap-2">
                                <div className="flex items-end gap-1.5 w-full justify-center" style={{ height: '120px' }}>
                                    <div
                                        className="w-6 bg-gradient-to-t from-primary-600 to-primary-400 rounded-t-md transition-all duration-500"
                                        style={{ height: `${Math.max((m.cases / maxVal) * 100, 2)}%` }}
                                        title={`${m.cases} expedientes`}
                                    />
                                    <div
                                        className="w-6 bg-gradient-to-t from-accent-500 to-accent-300 rounded-t-md transition-all duration-500"
                                        style={{ height: `${Math.max((m.deadlines / maxVal) * 100, 2)}%` }}
                                        title={`${m.deadlines} plazos`}
                                    />
                                </div>
                                <span className="text-xs text-surface-500 font-medium">{m.month}</span>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Bottom Row: Priority + Top Lawyers */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Priority Distribution */}
                <div className="card p-6">
                    <h3 className="font-semibold text-surface-800 mb-5 flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4 text-amber-500" />
                        Distribución por Prioridad
                    </h3>
                    {report.priority_distribution.length === 0 ? (
                        <p className="text-sm text-surface-400 text-center py-4">Sin datos de prioridad</p>
                    ) : (
                        <div className="space-y-3">
                            {report.priority_distribution.map((item) => {
                                const config = priorityConfig[item.priority] || priorityConfig.normal;
                                return (
                                    <div key={item.priority} className="flex items-center justify-between p-3 rounded-lg bg-surface-50">
                                        <span className={`text-xs font-bold uppercase tracking-wider px-2.5 py-1 rounded ${config.color}`}>
                                            {config.label}
                                        </span>
                                        <span className="text-lg font-bold text-surface-800">{item.count}</span>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>

                {/* Top Lawyers */}
                <div className="card p-6">
                    <h3 className="font-semibold text-surface-800 mb-5 flex items-center gap-2">
                        <User className="w-4 h-4 text-primary-500" />
                        Carga de Trabajo por Abogado
                    </h3>
                    {report.top_lawyers.length === 0 ? (
                        <p className="text-sm text-surface-400 text-center py-4">Sin datos de asignación</p>
                    ) : (
                        <div className="space-y-3">
                            {report.top_lawyers.map((lawyer, idx) => {
                                const maxCount = Math.max(...report.top_lawyers.map(l => l.case_count), 1);
                                return (
                                    <div key={idx} className="flex items-center gap-3">
                                        <div className="w-8 h-8 bg-primary-50 rounded-full flex items-center justify-center text-primary-600 font-bold text-xs shrink-0">
                                            {lawyer.nombre.split(' ').map(n => n[0]).join('').slice(0, 2)}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center justify-between mb-1">
                                                <span className="text-sm font-medium text-surface-700 truncate">{lawyer.nombre}</span>
                                                <span className="text-sm font-bold text-surface-800 ml-2">{lawyer.case_count}</span>
                                            </div>
                                            <div className="w-full bg-surface-100 rounded-full h-1.5">
                                                <div
                                                    className="h-1.5 rounded-full bg-gradient-to-r from-primary-400 to-primary-600 transition-all duration-500"
                                                    style={{ width: `${(lawyer.case_count / maxCount) * 100}%` }}
                                                />
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>
            </div>

            {/* Export Coming Soon */}
            <div className="card p-6 bg-gradient-to-r from-surface-50 to-surface-100 border-dashed border-2 border-surface-200 text-center">
                <Download className="w-8 h-8 text-surface-300 mx-auto mb-3" />
                <h3 className="font-semibold text-surface-700">Exportar Reportes</h3>
                <p className="text-sm text-surface-500 mt-1">
                    La exportación a PDF y Excel estará disponible en la próxima versión.
                </p>
            </div>
        </div>
    );
}
