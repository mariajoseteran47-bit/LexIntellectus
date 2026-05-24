'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import {
    Clock, Play, Pause, Square, Plus, DollarSign, FileText,
    Timer, Trash2, Send, AlertTriangle, CheckCircle, CreditCard,
    Receipt, TrendingUp, Calendar
} from 'lucide-react';
import api from '@/lib/api';
import { useToast } from '@/components/ui/ToastProvider';

interface TimeEntry {
    id: string;
    horas: number;
    descripcion: string;
    fecha_registro: string;
    es_facturable: boolean;
    tarifa_aplicada: number;
    facturado: boolean;
    created_at: string;
}

interface Invoice {
    id: string;
    numero_factura: string;
    estado: string;
    fecha_emision: string;
    fecha_vencimiento: string;
    es_credito: boolean;
    dias_credito: number;
    subtotal: number;
    iva_porcentaje: number;
    iva_monto: number;
    retencion_ir_porcentaje: number;
    retencion_ir_monto: number;
    retencion_alma_porcentaje: number;
    retencion_alma_monto: number;
    tasa_interes_moratorio: number;
    monto_interes_moratorio: number;
    total_factura: number;
    neto_a_pagar: number;
    moneda: string;
}

// Format seconds into HH:MM:SS
function formatDuration(totalSeconds: number): string {
    const h = Math.floor(totalSeconds / 3600);
    const m = Math.floor((totalSeconds % 3600) / 60);
    const s = totalSeconds % 60;
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

// Format decimal hours to display
function formatHours(hours: number): string {
    const h = Math.floor(hours);
    const m = Math.round((hours - h) * 60);
    return `${h}h ${m}m`;
}

const ESTADO_CONFIG: Record<string, { label: string; color: string; icon: typeof CheckCircle }> = {
    borrador: { label: 'Borrador', color: 'bg-gray-100 text-gray-600', icon: FileText },
    enviada: { label: 'Enviada', color: 'bg-blue-100 text-blue-700', icon: Send },
    pagada: { label: 'Pagada', color: 'bg-green-100 text-green-700', icon: CheckCircle },
    vencida: { label: 'Vencida', color: 'bg-red-100 text-red-700', icon: AlertTriangle },
    anulada: { label: 'Anulada', color: 'bg-slate-100 text-slate-500', icon: Trash2 },
};

export default function BillingPanel({ caseId }: { caseId: string }) {
    const toast = useToast();

    // === TIME TRACKER STATE ===
    const [isRunning, setIsRunning] = useState(false);
    const [elapsed, setElapsed] = useState(0);
    const [timerDescription, setTimerDescription] = useState('');
    const intervalRef = useRef<NodeJS.Timeout | null>(null);

    // === TIME ENTRIES STATE ===
    const [entries, setEntries] = useState<TimeEntry[]>([]);
    const [loadingEntries, setLoadingEntries] = useState(true);
    const [showManualEntry, setShowManualEntry] = useState(false);
    const [manualEntry, setManualEntry] = useState({ horas: '', descripcion: '', es_facturable: true });

    // === INVOICES STATE ===
    const [invoices, setInvoices] = useState<Invoice[]>([]);
    const [loadingInvoices, setLoadingInvoices] = useState(true);
    const [activeView, setActiveView] = useState<'tiempo' | 'facturas'>('tiempo');

    // === LOAD DATA ===
    useEffect(() => {
        loadTimeEntries();
        loadInvoices();
    }, [caseId]);

    const loadTimeEntries = async () => {
        setLoadingEntries(true);
        try {
            const { data } = await api.get(`/billing/time-entries?case_id=${caseId}`);
            setEntries(data || []);
        } catch (e) { console.error(e); }
        finally { setLoadingEntries(false); }
    };

    const loadInvoices = async () => {
        setLoadingInvoices(true);
        try {
            const { data } = await api.get(`/billing/invoices?case_id=${caseId}`);
            setInvoices(data || []);
        } catch (e) { console.error(e); }
        finally { setLoadingInvoices(false); }
    };

    // === TIMER CONTROLS ===
    const startTimer = useCallback(() => {
        if (isRunning) return;
        setIsRunning(true);
        intervalRef.current = setInterval(() => {
            setElapsed(prev => prev + 1);
        }, 1000);
    }, [isRunning]);

    const pauseTimer = useCallback(() => {
        setIsRunning(false);
        if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
        }
    }, []);

    const stopAndSaveTimer = useCallback(async () => {
        pauseTimer();
        if (elapsed < 60) {
            toast.error('El registro mínimo es de 1 minuto');
            return;
        }
        const horas = parseFloat((elapsed / 3600).toFixed(2));
        try {
            await api.post('/billing/time-entries', {
                case_id: caseId,
                horas,
                descripcion: timerDescription || 'Trabajo registrado con cronómetro',
                es_facturable: true,
            });
            toast.success(`${formatHours(horas)} registradas exitosamente`);
            setElapsed(0);
            setTimerDescription('');
            loadTimeEntries();
        } catch (e) {
            toast.error('Error al guardar tiempo');
        }
    }, [elapsed, timerDescription, caseId]);

    useEffect(() => {
        return () => {
            if (intervalRef.current) clearInterval(intervalRef.current);
        };
    }, []);

    // === MANUAL ENTRY ===
    const handleManualEntry = async () => {
        const horas = parseFloat(manualEntry.horas);
        if (isNaN(horas) || horas <= 0) {
            toast.error('Ingrese un número de horas válido');
            return;
        }
        try {
            await api.post('/billing/time-entries', {
                case_id: caseId,
                horas,
                descripcion: manualEntry.descripcion || 'Registro manual',
                es_facturable: manualEntry.es_facturable,
            });
            toast.success('Tiempo registrado');
            setShowManualEntry(false);
            setManualEntry({ horas: '', descripcion: '', es_facturable: true });
            loadTimeEntries();
        } catch (e) { toast.error('Error al registrar tiempo'); }
    };

    // === DELETE ENTRY ===
    const handleDeleteEntry = async (id: string) => {
        try {
            await api.delete(`/billing/time-entries/${id}`);
            toast.success('Registro eliminado');
            loadTimeEntries();
        } catch (e: any) {
            toast.error(e.response?.data?.detail || 'Error al eliminar');
        }
    };

    // === STATS ===
    const totalHoras = entries.reduce((sum, e) => sum + e.horas, 0);
    const horasFacturables = entries.filter(e => e.es_facturable && !e.facturado).reduce((sum, e) => sum + e.horas, 0);
    const montoFacturable = entries.filter(e => e.es_facturable && !e.facturado).reduce((sum, e) => sum + (e.horas * e.tarifa_aplicada), 0);
    const totalFacturado = invoices.filter(i => i.estado !== 'anulada').reduce((sum, i) => sum + i.neto_a_pagar, 0);
    const totalPendiente = invoices.filter(i => i.estado === 'enviada' || i.estado === 'vencida').reduce((sum, i) => sum + i.neto_a_pagar, 0);

    return (
        <div className="space-y-6">
            {/* === HEADER & VIEW TOGGLE === */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
                <div className="flex items-center gap-3">
                    <div className="p-2.5 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl text-white shadow-lg shadow-emerald-200">
                        <DollarSign className="w-5 h-5" />
                    </div>
                    <div>
                        <h3 className="font-bold text-surface-900 text-lg">Tiempo & Facturación</h3>
                        <p className="text-xs text-surface-500">Cronómetro, registros y facturas del expediente</p>
                    </div>
                </div>
                <div className="flex bg-surface-100 rounded-lg p-0.5">
                    <button onClick={() => setActiveView('tiempo')}
                        className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${activeView === 'tiempo' ? 'bg-white shadow text-surface-900' : 'text-surface-500 hover:text-surface-700'}`}>
                        <Clock className="w-3.5 h-3.5 inline mr-1.5" />Tiempo
                    </button>
                    <button onClick={() => setActiveView('facturas')}
                        className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all ${activeView === 'facturas' ? 'bg-white shadow text-surface-900' : 'text-surface-500 hover:text-surface-700'}`}>
                        <Receipt className="w-3.5 h-3.5 inline mr-1.5" />Facturas
                    </button>
                </div>
            </div>

            {/* === KPI CARDS === */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                <div className="card p-4 border-l-4 border-l-blue-500">
                    <p className="text-xs text-surface-500 uppercase font-semibold tracking-wide">Horas Totales</p>
                    <p className="text-2xl font-bold text-surface-900 mt-1">{totalHoras.toFixed(1)}</p>
                </div>
                <div className="card p-4 border-l-4 border-l-amber-500">
                    <p className="text-xs text-surface-500 uppercase font-semibold tracking-wide">Sin Facturar</p>
                    <p className="text-2xl font-bold text-amber-600 mt-1">{formatHours(horasFacturables)}</p>
                    <p className="text-xs text-surface-400">≈ C${montoFacturable.toFixed(2)}</p>
                </div>
                <div className="card p-4 border-l-4 border-l-green-500">
                    <p className="text-xs text-surface-500 uppercase font-semibold tracking-wide">Total Facturado</p>
                    <p className="text-2xl font-bold text-green-600 mt-1">C${totalFacturado.toFixed(2)}</p>
                </div>
                <div className="card p-4 border-l-4 border-l-red-500">
                    <p className="text-xs text-surface-500 uppercase font-semibold tracking-wide">Pendiente Cobro</p>
                    <p className="text-2xl font-bold text-red-600 mt-1">C${totalPendiente.toFixed(2)}</p>
                </div>
            </div>

            {/* ============================== */}
            {/* === TIME TRACKING VIEW ======= */}
            {/* ============================== */}
            {activeView === 'tiempo' && (
                <div className="space-y-5">
                    {/* === LIVE STOPWATCH === */}
                    <div className="card overflow-hidden">
                        <div className="bg-gradient-to-r from-surface-800 to-surface-900 p-6 text-white">
                            <div className="flex flex-col md:flex-row items-center gap-6">
                                <div className="flex flex-col items-center gap-2">
                                    <div className={`font-mono text-5xl font-bold tracking-wider tabular-nums ${isRunning ? 'text-emerald-400' : 'text-white'}`}>
                                        {formatDuration(elapsed)}
                                    </div>
                                    {isRunning && (
                                        <div className="flex items-center gap-1.5 text-emerald-400 text-xs animate-pulse">
                                            <div className="w-2 h-2 bg-emerald-400 rounded-full" /> Grabando tiempo...
                                        </div>
                                    )}
                                </div>
                                <div className="flex-1 w-full md:w-auto">
                                    <input
                                        type="text"
                                        value={timerDescription}
                                        onChange={(e) => setTimerDescription(e.target.value)}
                                        placeholder="¿En qué estás trabajando?"
                                        className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-2.5 text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-emerald-400/50 text-sm"
                                    />
                                </div>
                                <div className="flex items-center gap-2">
                                    {!isRunning ? (
                                        <button onClick={startTimer}
                                            className="p-3 bg-emerald-500 hover:bg-emerald-600 rounded-xl text-white transition-all shadow-lg shadow-emerald-500/30 hover:scale-105">
                                            <Play className="w-5 h-5" />
                                        </button>
                                    ) : (
                                        <button onClick={pauseTimer}
                                            className="p-3 bg-amber-500 hover:bg-amber-600 rounded-xl text-white transition-all shadow-lg shadow-amber-500/30">
                                            <Pause className="w-5 h-5" />
                                        </button>
                                    )}
                                    <button onClick={stopAndSaveTimer} disabled={elapsed < 60}
                                        className="p-3 bg-red-500 hover:bg-red-600 rounded-xl text-white transition-all shadow-lg shadow-red-500/30 disabled:opacity-30 disabled:cursor-not-allowed">
                                        <Square className="w-5 h-5" />
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* === ACTIONS BAR === */}
                    <div className="flex justify-between items-center">
                        <h4 className="font-semibold text-surface-800">Registros de Tiempo</h4>
                        <button onClick={() => setShowManualEntry(!showManualEntry)}
                            className="btn btn-sm btn-outline gap-1">
                            <Plus className="w-4 h-4" /> Registro Manual
                        </button>
                    </div>

                    {/* === MANUAL ENTRY FORM === */}
                    {showManualEntry && (
                        <div className="card p-5 border-2 border-emerald-200 bg-emerald-50/30 space-y-4">
                            <h4 className="font-semibold text-surface-800 flex items-center gap-2">
                                <Timer className="w-4 h-4 text-emerald-500" /> Registro Manual de Tiempo
                            </h4>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-surface-700 mb-1">Horas *</label>
                                    <input type="number" step="0.25" min="0.25" max="24"
                                        value={manualEntry.horas}
                                        onChange={e => setManualEntry(p => ({ ...p, horas: e.target.value }))}
                                        className="input w-full" placeholder="Ej: 1.5" />
                                </div>
                                <div className="md:col-span-2">
                                    <label className="block text-sm font-medium text-surface-700 mb-1">Descripción *</label>
                                    <input value={manualEntry.descripcion}
                                        onChange={e => setManualEntry(p => ({ ...p, descripcion: e.target.value }))}
                                        className="input w-full" placeholder="Revisión de expediente judicial..." />
                                </div>
                            </div>
                            <div className="flex items-center justify-between">
                                <label className="flex items-center gap-2 cursor-pointer">
                                    <input type="checkbox" checked={manualEntry.es_facturable}
                                        onChange={e => setManualEntry(p => ({ ...p, es_facturable: e.target.checked }))}
                                        className="rounded border-surface-300" />
                                    <span className="text-sm text-surface-600">💰 Facturable al cliente</span>
                                </label>
                                <div className="flex gap-2">
                                    <button onClick={() => setShowManualEntry(false)} className="btn btn-sm btn-outline">Cancelar</button>
                                    <button onClick={handleManualEntry}
                                        disabled={!manualEntry.horas || !manualEntry.descripcion}
                                        className="btn btn-sm btn-primary disabled:opacity-50 gap-1">
                                        <CheckCircle className="w-4 h-4" /> Guardar
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* === TIME ENTRIES LIST === */}
                    {loadingEntries ? (
                        <div className="text-center py-8 text-surface-500">Cargando registros...</div>
                    ) : entries.length === 0 ? (
                        <div className="card p-12 text-center">
                            <Timer className="w-12 h-12 mx-auto text-surface-300 mb-3" />
                            <h4 className="font-medium text-surface-700 mb-1">Sin registros de tiempo</h4>
                            <p className="text-sm text-surface-500 mb-4">
                                Use el cronómetro o agregue un registro manual para empezar.
                            </p>
                        </div>
                    ) : (
                        <div className="card overflow-hidden">
                            <table className="w-full text-left text-sm">
                                <thead className="bg-surface-50 border-b border-surface-200">
                                    <tr>
                                        <th className="px-4 py-3 font-semibold text-surface-600">Fecha</th>
                                        <th className="px-4 py-3 font-semibold text-surface-600">Descripción</th>
                                        <th className="px-4 py-3 font-semibold text-surface-600 text-right">Horas</th>
                                        <th className="px-4 py-3 font-semibold text-surface-600 text-right">Tarifa</th>
                                        <th className="px-4 py-3 font-semibold text-surface-600 text-right">Monto</th>
                                        <th className="px-4 py-3 font-semibold text-surface-600 text-center">Estado</th>
                                        <th className="px-4 py-3"></th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-surface-100">
                                    {entries.map(entry => (
                                        <tr key={entry.id} className="hover:bg-surface-50 transition-colors">
                                            <td className="px-4 py-3 text-surface-600">
                                                {new Date(entry.fecha_registro).toLocaleDateString('es-NI', { day: 'numeric', month: 'short' })}
                                            </td>
                                            <td className="px-4 py-3 text-surface-900 font-medium max-w-xs truncate">{entry.descripcion}</td>
                                            <td className="px-4 py-3 text-right font-mono font-semibold text-surface-800">{entry.horas.toFixed(2)}</td>
                                            <td className="px-4 py-3 text-right text-surface-500">C${entry.tarifa_aplicada.toFixed(2)}</td>
                                            <td className="px-4 py-3 text-right font-semibold text-surface-900">
                                                C${(entry.horas * entry.tarifa_aplicada).toFixed(2)}
                                            </td>
                                            <td className="px-4 py-3 text-center">
                                                {entry.facturado ? (
                                                    <span className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-green-100 text-green-700 font-bold uppercase">
                                                        <CheckCircle className="w-3 h-3" /> Facturado
                                                    </span>
                                                ) : entry.es_facturable ? (
                                                    <span className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 font-bold uppercase">
                                                        <Clock className="w-3 h-3" /> Pendiente
                                                    </span>
                                                ) : (
                                                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-surface-100 text-surface-500 font-bold uppercase">
                                                        No facturable
                                                    </span>
                                                )}
                                            </td>
                                            <td className="px-4 py-3 text-right">
                                                {!entry.facturado && (
                                                    <button onClick={() => handleDeleteEntry(entry.id)}
                                                        className="text-surface-400 hover:text-red-500 transition-colors">
                                                        <Trash2 className="w-4 h-4" />
                                                    </button>
                                                )}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            )}

            {/* ============================== */}
            {/* === INVOICES VIEW ============ */}
            {/* ============================== */}
            {activeView === 'facturas' && (
                <div className="space-y-5">
                    {loadingInvoices ? (
                        <div className="text-center py-8 text-surface-500">Cargando facturas...</div>
                    ) : invoices.length === 0 ? (
                        <div className="card p-12 text-center">
                            <Receipt className="w-12 h-12 mx-auto text-surface-300 mb-3" />
                            <h4 className="font-medium text-surface-700 mb-1">Sin facturas generadas</h4>
                            <p className="text-sm text-surface-500 mb-4">
                                Las facturas se generan desde la vista de facturación del cliente.
                            </p>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            {invoices.map(inv => {
                                const cfg = ESTADO_CONFIG[inv.estado] || ESTADO_CONFIG.borrador;
                                const isOverdue = inv.estado === 'vencida';
                                return (
                                    <div key={inv.id} className={`card p-5 hover:shadow-md transition-shadow ${isOverdue ? 'border-l-4 border-l-red-500 bg-red-50/30' : ''}`}>
                                        <div className="flex flex-col md:flex-row justify-between gap-4">
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-3 mb-2 flex-wrap">
                                                    <span className="font-bold text-surface-900 text-lg font-mono">{inv.numero_factura}</span>
                                                    <span className={`text-[11px] px-2.5 py-0.5 rounded-full font-bold uppercase ${cfg.color}`}>
                                                        {cfg.label}
                                                    </span>
                                                    {inv.es_credito && (
                                                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-100 text-purple-700 font-bold uppercase flex items-center gap-1">
                                                            <CreditCard className="w-3 h-3" /> Crédito {inv.dias_credito}d
                                                        </span>
                                                    )}
                                                </div>
                                                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm mt-3">
                                                    <div>
                                                        <span className="text-surface-500 text-xs block">Subtotal</span>
                                                        <span className="font-medium text-surface-900">{inv.moneda} {inv.subtotal.toFixed(2)}</span>
                                                    </div>
                                                    <div>
                                                        <span className="text-surface-500 text-xs block">IVA ({inv.iva_porcentaje}%)</span>
                                                        <span className="font-medium text-surface-900">{inv.moneda} {inv.iva_monto.toFixed(2)}</span>
                                                    </div>
                                                    {inv.retencion_ir_monto > 0 && (
                                                        <div>
                                                            <span className="text-surface-500 text-xs block">IR DGI ({inv.retencion_ir_porcentaje}%)</span>
                                                            <span className="font-medium text-red-600">-{inv.moneda} {inv.retencion_ir_monto.toFixed(2)}</span>
                                                        </div>
                                                    )}
                                                    {inv.retencion_alma_monto > 0 && (
                                                        <div>
                                                            <span className="text-surface-500 text-xs block">ALMA ({inv.retencion_alma_porcentaje}%)</span>
                                                            <span className="font-medium text-red-600">-{inv.moneda} {inv.retencion_alma_monto.toFixed(2)}</span>
                                                        </div>
                                                    )}
                                                    {inv.monto_interes_moratorio > 0 && (
                                                        <div>
                                                            <span className="text-surface-500 text-xs block">Interés Moratorio</span>
                                                            <span className="font-medium text-red-600">+{inv.moneda} {inv.monto_interes_moratorio.toFixed(2)}</span>
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                            <div className="text-right shrink-0 flex flex-col justify-between">
                                                <div>
                                                    <p className="text-xs text-surface-500">Emitida: {new Date(inv.fecha_emision).toLocaleDateString('es-NI')}</p>
                                                    <p className={`text-xs ${isOverdue ? 'text-red-600 font-bold' : 'text-surface-500'}`}>
                                                        Vence: {new Date(inv.fecha_vencimiento).toLocaleDateString('es-NI')}
                                                    </p>
                                                </div>
                                                <div className="mt-2">
                                                    <p className="text-xs text-surface-400">Neto a Pagar</p>
                                                    <p className={`text-2xl font-bold ${isOverdue ? 'text-red-600' : 'text-surface-900'}`}>
                                                        {inv.moneda} {inv.neto_a_pagar.toFixed(2)}
                                                    </p>
                                                </div>
                                            </div>
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
