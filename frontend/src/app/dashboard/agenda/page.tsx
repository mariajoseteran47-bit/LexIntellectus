'use client';

import { useState, useEffect, useMemo } from 'react';
import {
    Calendar, Clock, ExternalLink, ChevronLeft, ChevronRight,
    Filter, List, LayoutGrid, Plus, Calculator, CheckCircle2,
    Download, X, Sparkles, ShieldAlert
} from 'lucide-react';
import { deadlineService, Deadline, DeadlineCalculationResult } from '@/services/deadlineService';
import api from '@/lib/api';
import Link from 'next/link';

export default function AgendaPage() {
    const [deadlines, setDeadlines] = useState<Deadline[]>([]);
    const [cases, setCases] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [viewMode, setViewMode] = useState<'list' | 'calendar'>('list');
    const [filterPriority, setFilterPriority] = useState('');
    const [filterStatus, setFilterStatus] = useState('pendiente');
    const [currentMonth, setCurrentMonth] = useState(new Date());

    // Modal state for New Deadline + CPCN Calculator
    const [showModal, setShowModal] = useState(false);
    const [expedienteId, setExpedienteId] = useState('');
    const [descripcion, setDescripcion] = useState('');
    const [tipoPlazo, setTipoPlazo] = useState('procesal');
    const [prioridad, setPrioridad] = useState('alta');
    const [fechaInicio, setFechaInicio] = useState(new Date().toISOString().split('T')[0]);
    const [cantidadDias, setCantidadDias] = useState(5);
    const [diasTipo, setDiasTipo] = useState<'habiles' | 'calendario'>('habiles');
    const [municipio, setMunicipio] = useState('managua');
    const [incluirVacaciones, setIncluirVacaciones] = useState(true);
    const [fechaVencimientoManual, setFechaVencimientoManual] = useState('');
    const [baseLegal, setBaseLegal] = useState('');
    const [calcResult, setCalcResult] = useState<DeadlineCalculationResult | null>(null);
    const [calculating, setCalculating] = useState(false);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        fetchDeadlines();
        fetchCases();
    }, [filterStatus]);

    const fetchDeadlines = async () => {
        setLoading(true);
        try {
            const params = filterStatus === 'todos' ? {} : { status: filterStatus };
            const data = await deadlineService.getAll(params);
            setDeadlines(data);
        } catch (error) {
            console.error('Failed to fetch deadlines', error);
        } finally {
            setLoading(false);
        }
    };

    const fetchCases = async () => {
        try {
            const { data } = await api.get('/cases', { params: { size: 100 } });
            const items = data.items || data || [];
            setCases(items);
            if (items.length > 0 && !expedienteId) {
                setExpedienteId(items[0].id);
            }
        } catch (error) {
            console.error('Failed to fetch cases', error);
        }
    };

    const handleSimulateCalculation = async () => {
        if (!fechaInicio || cantidadDias < 1) return;
        setCalculating(true);
        try {
            const res = await deadlineService.calculate({
                fecha_inicio: fechaInicio,
                cantidad_dias: cantidadDias,
                dias_tipo: diasTipo,
                municipio,
                incluir_vacaciones_judiciales: incluirVacaciones
            });
            setCalcResult(res);
            setFechaVencimientoManual(res.fecha_vencimiento);
            if (!baseLegal) {
                setBaseLegal(res.base_legal_aplicada);
            }
        } catch (error) {
            console.error('Error calculating deadline:', error);
        } finally {
            setCalculating(false);
        }
    };

    const handleCreateDeadline = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!expedienteId || !descripcion) return;
        setSaving(true);
        try {
            await deadlineService.create({
                expediente_id: expedienteId,
                descripcion,
                tipo_plazo: tipoPlazo,
                fecha_inicio: fechaInicio,
                fecha_vencimiento: fechaVencimientoManual || undefined,
                cantidad_dias: cantidadDias,
                municipio,
                incluir_vacaciones_judiciales: incluirVacaciones,
                dias_tipo: diasTipo,
                prioridad,
                base_legal: baseLegal || undefined
            });
            setShowModal(false);
            setDescripcion('');
            setCalcResult(null);
            await fetchDeadlines();
        } catch (error) {
            console.error('Error creating deadline:', error);
        } finally {
            setSaving(false);
        }
    };

    const handleMarkCompleted = async (id: string) => {
        try {
            await deadlineService.update(id, { status: 'cumplido' });
            await fetchDeadlines();
        } catch (error) {
            console.error('Error updating deadline:', error);
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
        if (d.status === 'cumplido') {
            return { label: 'Cumplido', classes: 'bg-emerald-100 text-emerald-700', urgency: 'completed' };
        }
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

    const calendarDays = useMemo(() => {
        const year = currentMonth.getFullYear();
        const month = currentMonth.getMonth();
        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        const startPad = firstDay.getDay();
        const totalDays = lastDay.getDate();

        const days: { day: number; inMonth: boolean; date: Date; deadlines: Deadline[] }[] = [];

        for (let i = startPad - 1; i >= 0; i--) {
            const d = new Date(year, month, -i);
            days.push({ day: d.getDate(), inMonth: false, date: d, deadlines: [] });
        }

        for (let i = 1; i <= totalDays; i++) {
            const date = new Date(year, month, i);
            const dateStr = date.toISOString().split('T')[0];
            const dayDeadlines = deadlines.filter(dl => dl.fecha_vencimiento.startsWith(dateStr));
            days.push({ day: i, inMonth: true, date, deadlines: dayDeadlines });
        }

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

    const overdueCount = deadlines.filter(d => {
        if (d.status === 'cumplido') return false;
        const diff = new Date(d.fecha_vencimiento).getTime() - new Date().getTime();
        return Math.ceil(diff / (1000 * 60 * 60 * 24)) < 0;
    }).length;

    const todayCount = deadlines.filter(d => {
        if (d.status === 'cumplido') return false;
        const date = new Date(d.fecha_vencimiento);
        const today = new Date();
        return date.toDateString() === today.toDateString();
    }).length;

    const weekCount = deadlines.filter(d => {
        if (d.status === 'cumplido') return false;
        const diff = new Date(d.fecha_vencimiento).getTime() - new Date().getTime();
        const days = Math.ceil(diff / (1000 * 60 * 60 * 24));
        return days >= 0 && days <= 7;
    }).length;

    if (loading) {
        return (
            <div className="p-8 flex flex-col items-center justify-center gap-3">
                <div className="w-10 h-10 border-3 border-primary-500 border-t-transparent rounded-full animate-spin" />
                <p className="text-surface-500 text-sm">Cargando agenda judicial...</p>
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
                        Agenda Judicial & Motor de Plazos CPCN
                    </h1>
                    <p className="text-surface-500 text-sm mt-1">
                        Cómputo legal de días hábiles, feriados oficiales de Nicaragua, vacaciones CSJ y sincronización iCal
                    </p>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                    <a
                        href={deadlineService.getIcalUrl()}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-3 py-2 text-xs font-semibold rounded-lg border border-surface-200 bg-white text-surface-700 hover:bg-surface-50 flex items-center gap-1.5 shadow-sm"
                    >
                        <Download className="w-4 h-4 text-primary-600" />
                        Exportar iCal (.ics)
                    </a>
                    <button
                        onClick={() => setShowModal(true)}
                        className="px-4 py-2 text-xs font-bold rounded-lg bg-primary-600 hover:bg-primary-700 text-white flex items-center gap-1.5 shadow-sm transition-colors"
                    >
                        <Calculator className="w-4 h-4" />
                        Nuevo Plazo / Calculadora CPCN
                    </button>
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
            <div className="card p-3 flex flex-wrap items-center gap-3">
                <Filter className="w-4 h-4 text-surface-400" />
                <select
                    value={filterStatus}
                    onChange={(e) => setFilterStatus(e.target.value)}
                    className="text-sm border border-surface-200 rounded-lg px-3 py-1.5 bg-white text-surface-700 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                >
                    <option value="pendiente">⏳ Pendientes</option>
                    <option value="cumplido">✅ Cumplidos</option>
                    <option value="vencido">🚨 Vencidos</option>
                    <option value="todos">📋 Todos los estados</option>
                </select>
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

                    <div className="grid grid-cols-7 border-b border-surface-200">
                        {['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'].map(day => (
                            <div key={day} className="py-2 text-center text-xs font-semibold text-surface-500 uppercase">
                                {day}
                            </div>
                        ))}
                    </div>

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
                            <p className="text-surface-500 font-medium">No hay plazos en esta vista</p>
                            <p className="text-surface-400 text-sm">Usa el botón &ldquo;Nuevo Plazo / Calculadora CPCN&rdquo; para programar un término legal</p>
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
                                                    <span className="capitalize px-1.5 py-0.5 rounded bg-blue-50 text-blue-700">{d.dias_tipo}</span>
                                                </div>
                                                {d.base_legal && <p className="text-xs text-surface-400 mt-1 italic">📖 {d.base_legal}</p>}
                                            </div>
                                        </div>

                                        <div className="flex items-center gap-3 ml-7 md:ml-0">
                                            <span className={`px-3 py-1 rounded-lg text-xs font-bold ${status.classes}`}>
                                                {status.label}
                                            </span>
                                            {d.status === 'pendiente' && (
                                                <button
                                                    onClick={() => handleMarkCompleted(d.id)}
                                                    className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-emerald-50 text-emerald-700 hover:bg-emerald-100 flex items-center gap-1 transition-colors"
                                                    title="Marcar plazo como cumplido"
                                                >
                                                    <CheckCircle2 className="w-3.5 h-3.5" /> Cumplido
                                                </button>
                                            )}
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

            {/* Modal: Nuevo Plazo + Calculadora Procesal CPCN */}
            {showModal && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-xs z-50 flex items-center justify-center p-4 overflow-y-auto">
                    <div className="bg-white rounded-2xl shadow-2xl border border-surface-200 max-w-2xl w-full p-6 space-y-5 my-8">
                        <div className="flex items-center justify-between border-b border-surface-200 pb-4">
                            <div className="flex items-center gap-2.5">
                                <div className="w-9 h-9 rounded-xl bg-primary-50 text-primary-600 flex items-center justify-center">
                                    <Calculator className="w-5 h-5" />
                                </div>
                                <div>
                                    <h3 className="text-lg font-bold text-surface-900">Motor de Cómputo de Plazos Procesales (CPCN)</h3>
                                    <p className="text-xs text-surface-500">Arts. 129-135 CPCN (Ley 902) y Art. 90 LOPJ Nicaragua</p>
                                </div>
                            </div>
                            <button onClick={() => setShowModal(false)} className="p-1.5 text-surface-400 hover:text-surface-700 rounded-lg">
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        <form onSubmit={handleCreateDeadline} className="space-y-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="md:col-span-2">
                                    <label className="block text-xs font-semibold text-surface-700 mb-1">Asunto / Expediente *</label>
                                    <select
                                        required
                                        value={expedienteId}
                                        onChange={(e) => setExpedienteId(e.target.value)}
                                        className="w-full text-sm border border-surface-200 rounded-lg px-3 py-2 bg-white text-surface-800"
                                    >
                                        <option value="">Seleccione un expediente...</option>
                                        {cases.map((c) => (
                                            <option key={c.id} value={c.id}>
                                                {c.numero_interno || c.numero_causa || 'Sin número'} — {c.resumen ? c.resumen.slice(0, 60) : c.tipo_servicio}
                                            </option>
                                        ))}
                                    </select>
                                </div>

                                <div className="md:col-span-2">
                                    <label className="block text-xs font-semibold text-surface-700 mb-1">Descripción del Término o Actuación *</label>
                                    <input
                                        type="text"
                                        required
                                        placeholder="Ej. Contestación de Demanda / Interposición de Recurso de Apelación"
                                        value={descripcion}
                                        onChange={(e) => setDescripcion(e.target.value)}
                                        className="w-full text-sm border border-surface-200 rounded-lg px-3 py-2"
                                    />
                                </div>

                                <div>
                                    <label className="block text-xs font-semibold text-surface-700 mb-1">Fecha de Notificación (`dies a quo`)</label>
                                    <input
                                        type="date"
                                        value={fechaInicio}
                                        onChange={(e) => setFechaInicio(e.target.value)}
                                        className="w-full text-sm border border-surface-200 rounded-lg px-3 py-2"
                                    />
                                </div>

                                <div>
                                    <label className="block text-xs font-semibold text-surface-700 mb-1">Cantidad de Días del Término</label>
                                    <input
                                        type="number"
                                        min={1}
                                        max={365}
                                        value={cantidadDias}
                                        onChange={(e) => setCantidadDias(Number(e.target.value))}
                                        className="w-full text-sm border border-surface-200 rounded-lg px-3 py-2"
                                    />
                                </div>

                                <div>
                                    <label className="block text-xs font-semibold text-surface-700 mb-1">Tipo de Cómputo</label>
                                    <select
                                        value={diasTipo}
                                        onChange={(e) => setDiasTipo(e.target.value as 'habiles' | 'calendario')}
                                        className="w-full text-sm border border-surface-200 rounded-lg px-3 py-2 bg-white"
                                    >
                                        <option value="habiles">Días Hábiles Procesales (CPCN)</option>
                                        <option value="calendario">Días Calendario (Continuos)</option>
                                    </select>
                                </div>

                                <div>
                                    <label className="block text-xs font-semibold text-surface-700 mb-1">Sede Judicial / Municipio (Feriados Locales)</label>
                                    <select
                                        value={municipio}
                                        onChange={(e) => setMunicipio(e.target.value)}
                                        className="w-full text-sm border border-surface-200 rounded-lg px-3 py-2 bg-white"
                                    >
                                        <option value="managua">Managua (1 y 10 Ago Santo Domingo)</option>
                                        <option value="leon">León (24 Sep La Merced)</option>
                                        <option value="granada">Granada (15 Ago La Asunción)</option>
                                        <option value="masaya">Masaya (30 Sep San Jerónimo)</option>
                                        <option value="chinandega">Chinandega (26 Jul Santa Ana)</option>
                                        <option value="esteli">Estelí (7 Oct El Rosario)</option>
                                        <option value="matagalpa">Matagalpa (24 Sep La Merced)</option>
                                    </select>
                                </div>

                                <div>
                                    <label className="block text-xs font-semibold text-surface-700 mb-1">Tipo de Plazo</label>
                                    <select
                                        value={tipoPlazo}
                                        onChange={(e) => setTipoPlazo(e.target.value)}
                                        className="w-full text-sm border border-surface-200 rounded-lg px-3 py-2 bg-white"
                                    >
                                        <option value="procesal">Procesal Judicial</option>
                                        <option value="registral">Registral</option>
                                        <option value="notarial">Notarial</option>
                                        <option value="contractual">Contractual</option>
                                        <option value="administrativo">Administrativo</option>
                                    </select>
                                </div>

                                <div>
                                    <label className="block text-xs font-semibold text-surface-700 mb-1">Prioridad</label>
                                    <select
                                        value={prioridad}
                                        onChange={(e) => setPrioridad(e.target.value)}
                                        className="w-full text-sm border border-surface-200 rounded-lg px-3 py-2 bg-white"
                                    >
                                        <option value="critica">🔴 Crítica (Fatal)</option>
                                        <option value="alta">🟠 Alta</option>
                                        <option value="normal">🔵 Normal</option>
                                    </select>
                                </div>
                            </div>

                            <div className="flex items-center justify-between bg-surface-50 p-3 rounded-xl border border-surface-200">
                                <label className="flex items-center gap-2 text-xs text-surface-700 font-medium cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={incluirVacaciones}
                                        onChange={(e) => setIncluirVacaciones(e.target.checked)}
                                        className="rounded border-surface-300 text-primary-600"
                                    />
                                    Suspender cómputo durante Vacaciones Judiciales CSJ (Semana Santa y 24 Dic – 6 Ene)
                                </label>
                                <button
                                    type="button"
                                    onClick={handleSimulateCalculation}
                                    disabled={calculating}
                                    className="px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-600 text-white text-xs font-bold flex items-center gap-1.5 shadow-xs transition-colors"
                                >
                                    <Sparkles className="w-3.5 h-3.5" />
                                    {calculating ? 'Calculando...' : 'Calcular Vencimiento CPCN'}
                                </button>
                            </div>

                            {calcResult && (
                                <div className="p-4 rounded-xl bg-primary-50/70 border border-primary-200 space-y-2">
                                    <div className="flex items-center justify-between">
                                        <span className="text-xs font-bold text-primary-800 uppercase tracking-wider">
                                            Resultado del Motor Procesal
                                        </span>
                                        <span className="text-sm font-extrabold text-primary-700 bg-white px-3 py-1 rounded-lg border border-primary-200">
                                            Vence: {calcResult.fecha_vencimiento}
                                        </span>
                                    </div>
                                    <p className="text-xs text-surface-600">{calcResult.base_legal_aplicada}</p>
                                    {calcResult.dias_excluidos.length > 0 && (
                                        <div className="pt-1">
                                            <p className="text-[11px] font-semibold text-surface-700 mb-1">
                                                Días inhábiles excluidos del cómputo ({calcResult.dias_excluidos.length}):
                                            </p>
                                            <div className="max-h-24 overflow-y-auto flex flex-wrap gap-1.5">
                                                {calcResult.dias_excluidos.map((ex, i) => (
                                                    <span key={i} className="text-[10px] px-2 py-0.5 rounded bg-white border border-surface-200 text-surface-600">
                                                        <strong>{ex.fecha}:</strong> {ex.motivo}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-xs font-semibold text-surface-700 mb-1">
                                        Fecha de Vencimiento Definitiva (Auto o Manual)
                                    </label>
                                    <input
                                        type="date"
                                        value={fechaVencimientoManual}
                                        onChange={(e) => setFechaVencimientoManual(e.target.value)}
                                        className="w-full text-sm border border-surface-200 rounded-lg px-3 py-2"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-semibold text-surface-700 mb-1">Base Legal (Opcional)</label>
                                    <input
                                        type="text"
                                        placeholder="Ej. Art. 420 CPCN - 30 días hábiles"
                                        value={baseLegal}
                                        onChange={(e) => setBaseLegal(e.target.value)}
                                        className="w-full text-sm border border-surface-200 rounded-lg px-3 py-2"
                                    />
                                </div>
                            </div>

                            <div className="flex justify-end gap-2 pt-3 border-t border-surface-200">
                                <button
                                    type="button"
                                    onClick={() => setShowModal(false)}
                                    className="px-4 py-2 rounded-lg text-xs font-semibold text-surface-600 hover:bg-surface-100"
                                >
                                    Cancelar
                                </button>
                                <button
                                    type="submit"
                                    disabled={saving || !expedienteId || !descripcion}
                                    className="px-5 py-2 rounded-lg text-xs font-bold bg-primary-600 hover:bg-primary-700 text-white disabled:opacity-50"
                                >
                                    {saving ? 'Guardando...' : 'Guardar Plazo Fatal'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
