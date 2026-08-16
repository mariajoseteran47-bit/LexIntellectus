'use client';

import { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';

interface InvoiceLine {
    id: string;
    descripcion: string;
    cantidad: number;
    precio_unitario: number;
    subtotal: number;
}

interface Invoice {
    id: string;
    numero_factura: string;
    estado: string;
    fecha_emision: string;
    fecha_vencimiento: string;
    subtotal: number;
    iva_monto: number;
    total_factura: number;
    neto_a_pagar: number;
    moneda: string;
    lineas: InvoiceLine[];
}

export default function PortalBilling() {
    const searchParams = useSearchParams();
    const router = useRouter();
    
    const [invoices, setInvoices] = useState<Invoice[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    
    // Payments processing state
    const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);
    const [payingProvider, setPayingProvider] = useState<string | null>(null);
    const [paymentStatus, setPaymentStatus] = useState<'idle' | 'processing' | 'success' | 'cancel' | 'error'>('idle');
    const [paymentMessage, setPaymentMessage] = useState('');

    const fetchInvoices = async () => {
        const token = localStorage.getItem('access_token');
        const userStr = localStorage.getItem('user');

        if (!token || !userStr) {
            window.location.href = '/login';
            return;
        }

        const user = JSON.parse(userStr);
        try {
            const res = await fetch('/api/v1/portal/invoices', {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'X-Tenant-ID': user.tenant_id
                }
            });

            if (!res.ok) throw new Error('Error al cargar facturas');
            const data = await res.json();
            setInvoices(data || []);
        } catch (err: any) {
            setError(err.message || 'Error de conexión');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchInvoices();
    }, []);

    // Handle payment callbacks/redirects
    useEffect(() => {
        const status = searchParams.get('status');
        const provider = searchParams.get('provider');
        const invoiceId = searchParams.get('invoice_id');
        const sessionId = searchParams.get('session_id');
        const orderId = searchParams.get('order_id');

        if (status === 'success' && invoiceId) {
            setPaymentStatus('processing');
            setPaymentMessage('Verificando y procesando su transacción de pago...');
            
            const confirmPayment = async () => {
                const token = localStorage.getItem('access_token');
                const userStr = localStorage.getItem('user');
                if (!token || !userStr) return;
                const user = JSON.parse(userStr);

                try {
                    let confirmRes;
                    if (provider === 'stripe' && sessionId) {
                        confirmRes = await fetch('/api/v1/payments/stripe-confirm', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'Authorization': `Bearer ${token}`,
                                'X-Tenant-ID': user.tenant_id
                            },
                            body: JSON.stringify({ session_id: sessionId, invoice_id: invoiceId })
                        });
                    } else if (provider === 'paypal' && orderId) {
                        confirmRes = await fetch('/api/v1/payments/paypal-capture', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'Authorization': `Bearer ${token}`,
                                'X-Tenant-ID': user.tenant_id
                            },
                            body: JSON.stringify({ order_id: orderId, invoice_id: invoiceId })
                        });
                    } else {
                        // General confirm fallback
                        throw new Error('Parámetros de confirmación incorrectos');
                    }

                    if (!confirmRes.ok) {
                        const errData = await confirmRes.json();
                        throw new Error(errData.detail || 'No se pudo verificar el pago');
                    }

                    setPaymentStatus('success');
                    setPaymentMessage('¡Su factura ha sido pagada exitosamente! Recibirá un comprobante por correo.');
                    
                    // Refresh invoices list
                    await fetchInvoices();
                } catch (err: any) {
                    setPaymentStatus('error');
                    setPaymentMessage(err.message || 'Error durante la verificación del pago.');
                }
            };

            confirmPayment();
        } else if (status === 'cancel') {
            setPaymentStatus('cancel');
            setPaymentMessage('El proceso de pago fue cancelado por el usuario.');
        }
    }, [searchParams]);

    const handlePayNow = async (invoice: Invoice, provider: 'stripe' | 'paypal') => {
        setPayingProvider(provider);
        const token = localStorage.getItem('access_token');
        const userStr = localStorage.getItem('user');
        
        if (!token || !userStr) return;
        const user = JSON.parse(userStr);

        try {
            const res = await fetch('/api/v1/payments/create-session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                    'X-Tenant-ID': user.tenant_id
                },
                body: JSON.stringify({
                    invoice_id: invoice.id,
                    provider: provider
                })
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || 'Error al iniciar pasarela de pagos');
            }

            const data = await res.json();
            
            // Redirect user directly to Stripe Checkout or PayPal Approve screen
            window.location.href = data.url;
        } catch (err: any) {
            alert(err.message || 'Error al procesar pago');
            setPayingProvider(null);
        }
    };

    const clearPaymentOverlay = () => {
        setPaymentStatus('idle');
        setSelectedInvoice(null);
        setPayingProvider(null);
        // Clear query parameters from URL elegantly without reloading
        router.replace('/portal/billing');
    };

    // Calculate Statements
    const unpaidInvoices = invoices.filter(inv => inv.estado !== 'pagada' && inv.estado !== 'anulada');
    const totalUSD = unpaidInvoices
        .filter(inv => inv.moneda === 'USD')
        .reduce((sum, inv) => sum + Number(inv.neto_a_pagar), 0);
    const totalNIO = unpaidInvoices
        .filter(inv => inv.moneda === 'NIO')
        .reduce((sum, inv) => sum + Number(inv.neto_a_pagar), 0);

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[60vh]">
                <div className="text-center space-y-4">
                    <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-amber-500 mx-auto"></div>
                    <p className="text-slate-400 text-sm">Cargando estado de cuenta...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-8 relative">
            {/* Page Header */}
            <div>
                <h1 className="text-3xl font-extrabold text-white tracking-tight">Estado de Cuenta & Pagos</h1>
                <p className="text-slate-400 text-sm mt-2">Revise sus facturas pendientes y realice pagos en línea de forma segura con tarjetas de crédito y billeteras digitales.</p>
            </div>

            {/* Metrics cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-slate-900/60 border border-slate-800/80 p-6 rounded-2xl flex items-center justify-between shadow-xl backdrop-blur-sm group hover:border-slate-700/80 transition-all duration-300">
                    <div className="space-y-1.5">
                        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Saldo Pendiente (USD)</span>
                        <h2 className="text-3xl font-extrabold text-white group-hover:text-amber-400 transition-colors">
                            ${totalUSD.toFixed(2)} USD
                        </h2>
                        <p className="text-xs text-slate-500">Facturas de servicios internacionales / honorarios</p>
                    </div>
                    <div className="w-12 h-12 bg-slate-800/80 border border-slate-700/60 rounded-xl flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">
                        💵
                    </div>
                </div>

                <div className="bg-slate-900/60 border border-slate-800/80 p-6 rounded-2xl flex items-center justify-between shadow-xl backdrop-blur-sm group hover:border-slate-700/80 transition-all duration-300">
                    <div className="space-y-1.5">
                        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Saldo Pendiente (NIO)</span>
                        <h2 className="text-3xl font-extrabold text-white group-hover:text-amber-400 transition-colors">
                            {totalNIO.toFixed(2)} C$ NIO
                        </h2>
                        <p className="text-xs text-slate-500">Facturas de aranceles y gastos locales</p>
                    </div>
                    <div className="w-12 h-12 bg-slate-800/80 border border-slate-700/60 rounded-xl flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">
                        🇳🇮
                    </div>
                </div>
            </div>

            {/* Invoices List */}
            {invoices.length === 0 ? (
                <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-12 text-center space-y-4">
                    <div className="text-5xl">📄</div>
                    <h3 className="text-lg font-bold text-white">Sin facturas emitidas</h3>
                    <p className="text-slate-400 text-sm max-w-sm mx-auto">No hay estados de cuenta o recibos generados a su nombre actualmente.</p>
                </div>
            ) : (
                <div className="bg-slate-900/30 border border-slate-800/80 rounded-2xl overflow-hidden shadow-2xl">
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="border-b border-slate-800/80 bg-slate-900/70 text-slate-400 text-xs font-semibold tracking-wider uppercase">
                                    <th className="px-6 py-4">Factura</th>
                                    <th className="px-6 py-4 hidden md:table-cell">Fecha Emisión</th>
                                    <th className="px-6 py-4 hidden md:table-cell">Vence</th>
                                    <th className="px-6 py-4">Total</th>
                                    <th className="px-6 py-4">Estado</th>
                                    <th className="px-6 py-4 text-right">Acción</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800/60 text-sm">
                                {invoices.map((inv) => (
                                    <tr key={inv.id} className="hover:bg-slate-900/40 transition-colors group">
                                        <td className="px-6 py-4">
                                            <div className="font-semibold text-white">
                                                {inv.numero_factura}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 hidden md:table-cell text-slate-400 text-xs">
                                            {inv.fecha_emision}
                                        </td>
                                        <td className="px-6 py-4 hidden md:table-cell text-slate-400 text-xs">
                                            {inv.fecha_vencimiento}
                                        </td>
                                        <td className="px-6 py-4 font-semibold text-white">
                                            {inv.moneda === 'USD' ? '$' : 'C$'} {Number(inv.neto_a_pagar).toFixed(2)}
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className={`inline-flex px-2 py-0.5 rounded text-[10px] font-semibold border uppercase ${
                                                inv.estado === 'pagada'
                                                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                                                    : inv.estado === 'vencida'
                                                    ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                                                    : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                                            }`}>
                                                {inv.estado === 'enviada' ? 'pendiente' : inv.estado}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            {inv.estado !== 'pagada' && inv.estado !== 'anulada' ? (
                                                <button
                                                    onClick={() => setSelectedInvoice(inv)}
                                                    className="px-4 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold rounded-xl shadow-lg shadow-amber-500/10 hover:shadow-amber-500/20 transition-all duration-200"
                                                >
                                                    Pagar Ahora
                                                </button>
                                            ) : (
                                                <span className="text-slate-500 text-xs font-semibold italic">Liquidada</span>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* Pay Modal Options */}
            {selectedInvoice && !payingProvider && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
                    <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm" onClick={() => setSelectedInvoice(null)} />
                    <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 lg:p-8 max-w-md w-full shadow-2xl relative z-10 space-y-6">
                        <div className="flex justify-between items-start">
                            <div className="space-y-1">
                                <h3 className="text-lg font-bold text-white">Método de Pago</h3>
                                <p className="text-xs text-slate-400">Seleccione su plataforma para pagar la factura <span className="font-semibold text-slate-200">{selectedInvoice.numero_factura}</span></p>
                            </div>
                            <button
                                onClick={() => setSelectedInvoice(null)}
                                className="p-1 rounded-lg text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 transition-colors"
                            >
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>

                        {/* Financial Detail */}
                        <div className="bg-slate-950/50 p-4 rounded-xl border border-slate-800/80 flex justify-between items-center text-sm font-semibold">
                            <span className="text-slate-400">Total a Pagar:</span>
                            <span className="text-white text-lg">
                                {selectedInvoice.moneda === 'USD' ? '$' : 'C$'} {Number(selectedInvoice.neto_a_pagar).toFixed(2)} {selectedInvoice.moneda}
                            </span>
                        </div>

                        {/* Gateways Buttons */}
                        <div className="space-y-3 pt-2">
                            {/* Stripe button */}
                            <button
                                onClick={() => handlePayNow(selectedInvoice, 'stripe')}
                                className="w-full flex items-center justify-center gap-3 py-3 rounded-2xl bg-white hover:bg-slate-100 text-slate-950 font-bold transition-all duration-200 shadow-xl border border-slate-200"
                            >
                                <span className="text-indigo-600 font-extrabold text-lg">stripe</span>
                                <span>Pagar con Tarjeta</span>
                            </button>

                            {/* PayPal button */}
                            <button
                                onClick={() => handlePayNow(selectedInvoice, 'paypal')}
                                className="w-full flex items-center justify-center gap-3 py-3 rounded-2xl bg-amber-400 hover:bg-amber-300 text-blue-900 font-bold transition-all duration-200 shadow-xl"
                            >
                                <span className="italic font-extrabold text-lg text-blue-800">Pay<span className="text-blue-500">Pal</span></span>
                                <span>Pagar con PayPal</span>
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Redirect / Processing Overlay */}
            {paymentStatus !== 'idle' && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
                    <div className="bg-slate-900 border border-slate-800 rounded-3xl p-8 max-w-md w-full shadow-2xl text-center space-y-6">
                        {paymentStatus === 'processing' && (
                            <div className="space-y-4">
                                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-amber-500 mx-auto"></div>
                                <h3 className="text-lg font-bold text-white">Verificando Pago</h3>
                                <p className="text-sm text-slate-400">{paymentMessage}</p>
                            </div>
                        )}

                        {paymentStatus === 'success' && (
                            <div className="space-y-4 animate-fade-in">
                                <div className="w-16 h-16 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-full flex items-center justify-center text-4xl mx-auto shadow-lg shadow-emerald-500/10 animate-bounce">
                                    ✓
                                </div>
                                <h3 className="text-xl font-bold text-white">¡Pago Confirmado!</h3>
                                <p className="text-sm text-slate-300 leading-relaxed">{paymentMessage}</p>
                                <button
                                    onClick={clearPaymentOverlay}
                                    className="px-6 py-2.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 rounded-xl text-xs font-bold transition-colors"
                                >
                                    Volver al Facturación
                                </button>
                            </div>
                        )}

                        {(paymentStatus === 'cancel' || paymentStatus === 'error') && (
                            <div className="space-y-4">
                                <div className="w-16 h-16 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-full flex items-center justify-center text-3xl mx-auto shadow-lg shadow-rose-500/10">
                                    !
                                </div>
                                <h3 className="text-xl font-bold text-white">
                                    {paymentStatus === 'cancel' ? 'Pago Cancelado' : 'Error en Pago'}
                                </h3>
                                <p className="text-sm text-slate-300 leading-relaxed">{paymentMessage}</p>
                                <button
                                    onClick={clearPaymentOverlay}
                                    className="px-6 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-bold transition-colors"
                                >
                                    Cerrar Mensaje
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
