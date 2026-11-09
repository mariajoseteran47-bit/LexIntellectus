'use client';

import { useState, useEffect } from 'react';
import { DollarSign, Receipt, AlertTriangle, Send, CheckCircle, Trash2, Download } from 'lucide-react';
import api from '@/lib/api';
import { useToast } from '@/components/ui/ToastProvider';

interface Invoice {
    id: string;
    numero_factura: string;
    estado: string;
    fecha_emision: string;
    fecha_vencimiento: string;
    es_credito: boolean;
    dias_credito: number;
    subtotal: number;
    iva_monto: number;
    retencion_ir_monto: number;
    retencion_alma_monto: number;
    monto_interes_moratorio: number;
    neto_a_pagar: number;
    moneda: string;
    case_id?: string;
}

const ESTADO_CONFIG: Record<string, { label: string; color: string; icon: any }> = {
    borrador: { label: 'Borrador', color: 'bg-gray-100 text-gray-600', icon: Receipt },
    enviada: { label: 'Enviada', color: 'bg-blue-100 text-blue-700', icon: Send },
    pagada: { label: 'Pagada', color: 'bg-green-100 text-green-700', icon: CheckCircle },
    vencida: { label: 'Vencida', color: 'bg-red-100 text-red-700', icon: AlertTriangle },
    anulada: { label: 'Anulada', color: 'bg-slate-100 text-slate-500', icon: Trash2 },
};

export default function BillingOverviewPage() {
    const toast = useToast();
    const [invoices, setInvoices] = useState<Invoice[]>([]);
    const [loading, setLoading] = useState(true);
    const [exporting, setExporting] = useState(false);

    useEffect(() => {
        loadInvoices();
    }, []);

    const loadInvoices = async () => {
        setLoading(true);
        try {
            const { data } = await api.get('/billing/invoices');
            setInvoices(data || []);
        } catch (e) {
            console.error(e);
            toast.error('Error al cargar las facturas');
        } finally {
            setLoading(false);
        }
    };

    const handleExport = async (format: 'json' | 'csv' = 'json') => {
        setExporting(true);
        try {
            if (format === 'csv') {
                const { data } = await api.get('/billing/invoices/export/csv', { responseType: 'blob' });
                const blob = new Blob([data], { type: 'text/csv;charset=utf-8;' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `facturas_lexintellectus_${new Date().toISOString().split('T')[0]}.csv`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            } else {
                const { data } = await api.get('/billing/invoices/export/json');
                const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `facturas_lexintellectus_${new Date().toISOString().split('T')[0]}.json`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            }
            
            toast.success(`Exportación ${format.toUpperCase()} exitosa`);
        } catch (e) {
            console.error(e);
            toast.error('Error al exportar datos');
        } finally {
            setExporting(false);
        }
    };

    // Calculate KPIs
    const totalFacturadoMes = invoices
        .filter(i => i.estado !== 'anulada' && new Date(i.fecha_emision).getMonth() === new Date().getMonth())
        .reduce((sum, i) => sum + i.neto_a_pagar, 0);

    const totalPendiente = invoices
        .filter(i => i.estado === 'enviada' || i.estado === 'vencida')
        .reduce((sum, i) => sum + i.neto_a_pagar, 0);

    const totalVencido = invoices
        .filter(i => i.estado === 'vencida')
        .reduce((sum, i) => sum + i.neto_a_pagar, 0);

    const totalPagado = invoices
        .filter(i => i.estado === 'pagada')
        .reduce((sum, i) => sum + i.neto_a_pagar, 0);

    if (loading) {
        return <div className="p-8 text-center text-surface-500">Cargando datos de facturación...</div>;
    }

    return (
        <div className="space-y-6 max-w-7xl mx-auto">
            {/* === HEADER === */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div className="flex items-center gap-3">
                    <div className="p-3 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl text-white shadow-lg shadow-emerald-200">
                        <DollarSign className="w-6 h-6" />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-surface-900">Facturación y Finanzas</h1>
                        <p className="text-sm text-surface-500">Gestión global de facturación del despacho</p>
                    </div>
                </div>
                <div className="flex gap-2">
                    <button 
                        onClick={() => handleExport('csv')} 
                        disabled={exporting}
                        className="btn btn-outline flex items-center gap-2 bg-white"
                    >
                        <Download className="w-4 h-4" /> 
                        {exporting ? 'Exportando...' : 'Exportar CSV'}
                    </button>
                    <button 
                        onClick={() => handleExport('json')} 
                        disabled={exporting}
                        className="btn btn-outline flex items-center gap-2 bg-white"
                    >
                        <Download className="w-4 h-4" /> 
                        {exporting ? 'Exportando...' : 'Exportar JSON'}
                    </button>
                </div>
            </div>

            {/* === KPI CARDS === */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="card p-5 border-l-4 border-l-blue-500">
                    <p className="text-xs text-surface-500 uppercase font-semibold tracking-wide">Facturado (Mes Actual)</p>
                    <p className="text-3xl font-bold text-surface-900 mt-2">C$ {totalFacturadoMes.toLocaleString(undefined, { minimumFractionDigits: 2 })}</p>
                </div>
                <div className="card p-5 border-l-4 border-l-green-500">
                    <p className="text-xs text-surface-500 uppercase font-semibold tracking-wide">Total Pagado</p>
                    <p className="text-3xl font-bold text-green-600 mt-2">C$ {totalPagado.toLocaleString(undefined, { minimumFractionDigits: 2 })}</p>
                </div>
                <div className="card p-5 border-l-4 border-l-amber-500">
                    <p className="text-xs text-surface-500 uppercase font-semibold tracking-wide">Pendiente de Cobro</p>
                    <p className="text-3xl font-bold text-amber-600 mt-2">C$ {totalPendiente.toLocaleString(undefined, { minimumFractionDigits: 2 })}</p>
                </div>
                <div className="card p-5 border-l-4 border-l-red-500">
                    <p className="text-xs text-surface-500 uppercase font-semibold tracking-wide">Total Vencido</p>
                    <p className="text-3xl font-bold text-red-600 mt-2">C$ {totalVencido.toLocaleString(undefined, { minimumFractionDigits: 2 })}</p>
                </div>
            </div>

            {/* === INVOICES TABLE === */}
            <div className="card overflow-hidden">
                <div className="p-5 border-b border-surface-200 bg-surface-50 flex justify-between items-center">
                    <h3 className="font-semibold text-surface-800 flex items-center gap-2">
                        <Receipt className="w-5 h-5 text-emerald-600" /> Historial de Facturas
                    </h3>
                </div>
                
                {invoices.length === 0 ? (
                    <div className="p-12 text-center">
                        <Receipt className="w-12 h-12 mx-auto text-surface-300 mb-3" />
                        <h4 className="font-medium text-surface-700 mb-1">Sin facturas emitidas</h4>
                        <p className="text-sm text-surface-500">
                            Las facturas se generan desde la vista de detalle de cada expediente judicial o servicio legal.
                        </p>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm whitespace-nowrap">
                            <thead className="bg-surface-50 border-b border-surface-200">
                                <tr>
                                    <th className="px-6 py-4 font-semibold text-surface-600">No. Factura</th>
                                    <th className="px-6 py-4 font-semibold text-surface-600">Estado</th>
                                    <th className="px-6 py-4 font-semibold text-surface-600">Fecha Emisión</th>
                                    <th className="px-6 py-4 font-semibold text-surface-600">Vencimiento</th>
                                    <th className="px-6 py-4 font-semibold text-surface-600 text-right">Subtotal</th>
                                    <th className="px-6 py-4 font-semibold text-surface-600 text-right">Impuestos/Ret.</th>
                                    <th className="px-6 py-4 font-semibold text-surface-600 text-right">Mora</th>
                                    <th className="px-6 py-4 font-semibold text-surface-600 text-right">Neto a Pagar</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-surface-100">
                                {invoices.map(inv => {
                                    const cfg = ESTADO_CONFIG[inv.estado] || ESTADO_CONFIG.borrador;
                                    const StatusIcon = cfg.icon;
                                    const retenciones = inv.retencion_ir_monto + inv.retencion_alma_monto;
                                    
                                    return (
                                        <tr key={inv.id} className="hover:bg-surface-50 transition-colors">
                                            <td className="px-6 py-4 font-bold font-mono text-surface-900">{inv.numero_factura}</td>
                                            <td className="px-6 py-4">
                                                <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold uppercase tracking-wider ${cfg.color}`}>
                                                    <StatusIcon className="w-3.5 h-3.5" />
                                                    {cfg.label}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 text-surface-600">
                                                {new Date(inv.fecha_emision).toLocaleDateString('es-NI')}
                                            </td>
                                            <td className={`px-6 py-4 ${inv.estado === 'vencida' ? 'text-red-600 font-medium' : 'text-surface-600'}`}>
                                                {new Date(inv.fecha_vencimiento).toLocaleDateString('es-NI')}
                                            </td>
                                            <td className="px-6 py-4 text-right text-surface-600">
                                                {inv.moneda} {inv.subtotal.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                            </td>
                                            <td className="px-6 py-4 text-right">
                                                <div className="flex flex-col text-xs">
                                                    <span className="text-surface-600">+ IVA: {inv.moneda} {inv.iva_monto.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
                                                    {retenciones > 0 && (
                                                        <span className="text-red-500">- Ret: {inv.moneda} {retenciones.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
                                                    )}
                                                </div>
                                            </td>
                                            <td className={`px-6 py-4 text-right ${inv.monto_interes_moratorio > 0 ? 'text-red-500 font-medium' : 'text-surface-400'}`}>
                                                {inv.monto_interes_moratorio > 0 ? `+ ${inv.moneda} ${inv.monto_interes_moratorio.toLocaleString(undefined, { minimumFractionDigits: 2 })}` : '-'}
                                            </td>
                                            <td className="px-6 py-4 text-right font-bold text-surface-900 text-base">
                                                {inv.moneda} {inv.neto_a_pagar.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
}
