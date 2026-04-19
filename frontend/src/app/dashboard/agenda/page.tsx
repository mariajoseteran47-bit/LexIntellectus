'use client';

import { useState, useEffect, useMemo } from 'react';
import { Calendar, Clock, AlertCircle, ExternalLink, ChevronLeft, ChevronRight, Filter, List, LayoutGrid } from 'lucide-react';
import { deadlineService, Deadline } from '@/services/deadlineService';
import Link from 'next/link';

export default function AgendaPage() {
    const [deadlines, setDeadlines] = useState<Deadline[]>([]);
    const [loading, setLoading] = useState(true);
    const [viewMode, setViewMode] = useState<'list' | 'calendar'>('list');
    const [filterPriority, setFilterPriority] = useState('');
    const [currentMonth, setCurrentMonth] = useState(new Date());

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

    const filteredDeadlines = useMemo(() => {
        let filtered = [...deadlines];
        if (filterPriority) {
            filtered = filtered.filter(d => d.prioridad === filterPriority);
        }
        return filtered.sort((a, b) =>
            new Date(a.fecha_vencimiento).getTime() - new Date(b.fecha_vencimiento).getTime()
        );
    }, [deadlines, filterPriority]);

    const getStatusInfo = (d: Deadline) => {
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const dueDate = new Date(d.fecha_vencimiento);
        dueDate.setHours(0, 0, 0, 0);
        const diffTime = dueDate.getTime() - today.getTime();
        const diffDays = Math.round(diffTime / (1000 * 60 * 60 * 24));

        if (diffDays < 0) return { label: `Vencido (${Math.abs(diffDays)}d)`, classes: 'bg-red-100 text-red-700', urgency: 'overdue' };
        if (diffDays === 0) return { label: 'Vence Hoy', classes: 'bg-red-100 text-red-700 animate-pulse', urgency: 'today' };
        if (diffDays === 1) return { label: 'Vence Mañana', classes: 'bg-orange-100 text-orange-700', urgency: 'tomorrow' };
        if (diffDays <= 3) return { label: `En ${diffDays} días`, classes: 'bg-amber-100 text-amber-700', urgency: 'soon' };
        if (diffDays <= 7) return { label: `En ${diffDays} días`, classes: 'bg-blue-100 text-blue-700', urgency: 'week' };
        return { label: new Date(d.fecha_vencimiento).toLocaleDateString('es-NI', { day: '2-digit', month: 'short' }), classes: 'bg-surface-100 text-surface-600', urgency: 'normal' };
    };

    const getPriorityDot = (prioridad: string) => {
        switch (prioridad) {
            case 'critica': return 'bg-red-500';
            case 'alta': return 'bg-amber-500';
            default: return 'bg-blue-400';
        }
    };

    // === Calendar helpers ===
    const calendarDays = useMemo(() => {
        const year = currentMonth.getFullYear();
        const month = currentMonth.getMonth();
        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        const startPad = firstDay.getDay(); // 0=Sun
        const totalDays = lastDay.getDate();

        const days: { day: number; inMonth: boolean; date: Date; deadlines: Deadline[] }[] = [];

        // Padding from previous month
        for (let i = startPad - 1; i >= 0; i--) {
            const d = new Date(year, month, -i);
            days.push({ day: d.getDate(), inMonth: false, date: d, deadlines: [] });
        }

        // Current month days
        for (let i = 1; i <= totalDays; i++) {
            const date = new Date(year, month, i);
            const dateStr = date.toISOString().split('T')[0];
            const dayDeadlines = deadlines.filter(dl => dl.fecha_vencimiento.startsWith(dateStr));
            days.push({ day: i, inMonth: true, date, deadlines: dayDeadlines });
        }

        // Padding to fill 6 rows (42 cells)
        while (days.length < 42) {
            const d = new Date(year, month + 1, days.length - startPad - totalDays + 1);
            days.push({ day: d.getDate(), inMonth: false, date: d, deadlines: [] });
        }

        return days;
    }, [currentMonth, deadlines]);

    const isToday = (date: Date) => {
        const today = new Date();
        return date.getDate() === today.getDate() &&
            date.getMonth() === today.getMonth() &&
            date.getFullYear() === today.getFullYear();
    };

    // Stats
    const overdueCount = deadlines.filter(d => {
        const diff = new Date(d.fecha_vencimiento).getTime() - new Date().getTime();
        return Math.ceil(diff / (1000 * 60 * 60 * 24)) < 0;
    }).length;

    const todayCount = deadlines.filter(d => {
        const date = new Date(d.fecha_vencimiento);
        const today = new Date();
        return date.toDateString() === today.toDateString();
    }).length;

    const weekCount = deadlines.filter(d => {
        const diff = new Date(d.fecha_vencimiento).getTime() - new Date().getTime();
        const days = Math.ceil(diff / (1000 * 60 * 60 * 24));
        return days >= 0 && days <= 7;
    }).length;

    if (loading) {
        return (
            <div className="p-8 flex flex-col items-center justify-center gap-3">
                <div className="w-10 h-10 border-3 border-primary-500 border-t-transparent rounded-full animate-spin" />
                <p className="text-surface-500 text-sm">Cargando agenda...</p>
            </div>
        );
    }

    return (
        <div className="space-y-6 animate-fade-in">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-surface-900 flex items-center gap-3">
                        <Calendar className="w-6 h-6 text-primary-500" />
                        Agenda Judicial
                    </h1>
                    <p className="text-surface-500 text-sm mt-1">Plazos fatales, audiencias y compromisos</p>
                </div>
                <div className="flex items-center gap-2">
                    {/* View toggle */}
                    <div className="flex items-center bg-surface-100 rounded-lg p-0.5">
                        <button
                            onClick={() => setViewMode('list')}
                            className={`p-2 rounded-md transition-all ${viewMode === 'list' ? 'bg-white shadow-sm text-primary-600' : 'text-surface-400 hover:text-surface-600'}`}
                        >
                            <List className="w-4 h-4" />
                        </button>
                        <button
                            onClick={() => setViewMode('calendar')}
                            className={`p-2 rounded-md transition-all ${viewMode === 'calendar' ? 'bg-white shadow-sm text-primary-600' : 'text-surface-400 hover:text-surface-600'}`}
                        >
                            <LayoutGrid className="w-4 h-4" />
                        </button>
                    </div>
                </div>
            </div>

            {/* Stats Strip */}
            <div className="grid grid-cols-3 gap-4">
                {[
                    { label: 'Vencidos', value: overdueCount, color: 'text-red-600', bg: 'bg-red-50', border: 'border-red-200' },
                    { label: 'Vence Hoy', value: todayCount, color: 'text-amber-600', bg: 'bg-amber-50', border: 'border-amber-200' },
                    { label: 'Esta Semana', value: weekCount, color: 'text-blue-600', bg: 'bg-blue-50', border: 'border-blue-200' },
                ].map((stat) => (
                    <div key={stat.label} className={`card p-4 ${stat.bg} border ${stat.border}`}>
                        <p className={`text-2xl font-bold ${stat.color}`}>{stat.value}</p>
                        <p className="text-xs font-medium text-surface-500 mt-0.5">{stat.label}</p>
                    </div>
                ))}
            </div>

            {/* Filter Bar */}
            <div className="card p-3 flex items-center gap-3">
                <Filter className="w-4 h-4 text-surface-400" />
                <select
                    value={filterPriority}
                    onChange={(e) => setFilterPriority(e.target.value)}
                    className="text-sm border border-surface-200 rounded-lg px-3 py-1.5 bg-white text-surface-700 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                >
                    <option value="">Todas las prioridades</option>
                    <option value="critica">🔴 Crítica</option>
                    <option value="alta">🟠 Alta</option>
                    <option value="normal">🔵 Normal</option>
                </select>
                <span className="text-xs text-surface-400 ml-auto">{filteredDeadlines.length} plazos</span>
            </div>

            {/* Calendar View */}
            {viewMode === 'calendar' && (
                <div className="card overflow-hidden">
                    {/* Calendar Header */}
                    <div className="px-6 py-4 border-b border-surface-200 flex items-center justify-between bg-surface-50/50">
                        <button onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1))} className="p-1 hover:bg-surface-200 rounded-lg transition-colors">
                            <ChevronLeft className="w-5 h-5 text-surface-600" />
                        </button>
                        <h3 className="font-bold text-surface-800 capitalize">
                            {currentMonth.toLocaleDateString('es-NI', { month: 'long', year: 'numeric' })}
                        </h3>
                        <button onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1))} className="p-1 hover:bg-surface-200 rounded-lg transition-colors">
                            <ChevronRight className="w-5 h-5 text-surface-600" />
                        </button>
                    </div>

                    {/* Day headers */}
                    <div className="grid grid-cols-7 border-b border-surface-200">
                        {['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'].map(day => (
                            <div key={day} className="py-2 text-center text-xs font-semibold text-surface-500 uppercase">
                                {day}
                            </div>
                        ))}
                    </div>

                    {/* Calendar Grid */}
                    <div className="grid grid-cols-7">
                        {calendarDays.map((cell, idx) => (
                            <div
                                key={idx}
                                className={`min-h-[80px] p-1.5 border-b border-r border-surface-100 ${
                                    !cell.inMonth ? 'bg-surface-50/50' : ''
                                } ${isToday(cell.date) ? 'bg-primary-50/50' : ''}`}
                            >
                                <span className={`text-xs font-medium ${
                                    !cell.inMonth ? 'text-surface-300' :
                                    isToday(cell.date) ? 'text-primary-600 font-bold' : 'text-surface-600'
                                }`}>
                                    {cell.day}
                                </span>
                                <div className="mt-1 space-y-0.5">
                                    {cell.deadlines.slice(0, 2).map((dl, i) => (
                                        <div key={i} className={`text-[10px] px-1 py-0.5 rounded truncate ${
                                            dl.prioridad === 'critica' ? 'bg-red-100 text-red-700' :
                                            dl.prioridad === 'alta' ? 'bg-amber-100 text-amber-700' :
                                            'bg-blue-100 text-blue-700'
                                        }`} title={dl.descripcion}>
                                            {dl.descripcion.length > 15 ? dl.descripcion.substring(0, 15) + '...' : dl.descripcion}
                                        </div>
                                    ))}
                                    {cell.deadlines.length > 2 && (
                                        <div className="text-[10px] text-surface-400 pl-1">+{cell.deadlines.length - 2} más</div>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* List View */}
            {viewMode === 'list' && (
                <div className="card overflow-hidden">
                    <div className="px-6 py-4 border-b border-surface-200 bg-surface-50/50 flex justify-between items-center">
                        <h2 className="font-semibold text-surface-800">Próximos Vencimientos</h2>
                        <span className="badge bg-primary-100 text-primary-700">{filteredDeadlines.length} Plazos</span>
                    </div>

                    {filteredDeadlines.length === 0 ? (
                        <div className="p-12 text-center space-y-4">
                            <div className="w-16 h-16 bg-surface-100 rounded-full flex items-center justify-center mx-auto">
                                <Clock className="w-8 h-8 text-surface-400" />
                            </div>
                            <p className="text-surface-500 font-medium">No hay plazos pendientes</p>
                            <p className="text-surface-400 text-sm">Los plazos registrados en sus expedientes aparecerán aquí</p>
                        </div>
                    ) : (
                        <div className="divide-y divide-surface-100">
                            {filteredDeadlines.map((d) => {
                                const status = getStatusInfo(d);
                                return (
                                    <div key={d.id} className="px-6 py-4 hover:bg-surface-50/50 transition-colors flex flex-col md:flex-row md:items-center justify-between gap-4">
                                        <div className="flex items-start gap-4">
                                            <div className="relative mt-1">
                                                <div className={`w-3 h-3 rounded-full ${getPriorityDot(d.prioridad)}`} />
                                                {status.urgency === 'overdue' && (
                                                    <div className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-red-500 animate-ping" />
                                                )}
                                            </div>
                                            <div>
                                                <h3 className="font-semibold text-surface-900">{d.descripcion}</h3>
                                                <div className="flex flex-wrap gap-x-4 gap-y-1 mt-1.5 text-xs text-surface-500">
                                                    <span className="flex items-center gap-1">
                                                        <Calendar className="w-3.5 h-3.5" />
                                                        {new Date(d.fecha_vencimiento).toLocaleDateString('es-NI', { weekday: 'short', day: '2-digit', month: 'short', year: 'numeric' })}
                                                    </span>
                                                    {d.hora_vencimiento && (
                                                        <span className="flex items-center gap-1">
                                                            <Clock className="w-3.5 h-3.5" /> {d.hora_vencimiento.substring(0, 5)}
                                                        </span>
                                                    )}
                                                    <span className="capitalize px-1.5 py-0.5 rounded bg-surface-100 text-surface-600">{d.tipo_plazo}</span>
                                                </div>
                                                {d.base_legal && <p className="text-xs text-surface-400 mt-1 italic">📖 {d.base_legal}</p>}
                                            </div>
                                        </div>

                                        <div className="flex items-center gap-3 ml-7 md:ml-0">
                                            <span className={`px-3 py-1 rounded-lg text-xs font-bold ${status.classes}`}>
                                                {status.label}
                                            </span>
                                            <Link
                                                href={`/dashboard/cases/${d.expediente_id}`}
                                                className="text-xs text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1 whitespace-nowrap"
                                            >
                                                Ver caso <ExternalLink className="w-3 h-3" />
                                            </Link>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
