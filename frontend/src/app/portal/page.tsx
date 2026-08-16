'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface CaseInfo {
    id: string;
    numero_causa?: string;
    numero_interno?: string;
    tipo_servicio: string;
    juzgado?: string;
    prioridad: string;
}

interface InvoiceInfo {
    id: string;
    numero_factura: string;
    estado: string;
    total_factura: number;
    neto_a_pagar: number;
    moneda: string;
}

interface DocumentInfo {
    id: string;
    nombre_archivo: string;
    categoria: string;
    created_at: string;
}

export default function PortalDashboard() {
    const [cases, setCases] = useState<CaseInfo[]>([]);
    const [invoices, setInvoices] = useState<InvoiceInfo[]>([]);
    const [documents, setDocuments] = useState<DocumentInfo[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchDashboardData = async () => {
            const token = localStorage.getItem('access_token');
            const userStr = localStorage.getItem('user');
            
            if (!token || !userStr) {
                window.location.href = '/login';
                return;
            }

            const user = JSON.parse(userStr);
            const headers = {
                'Authorization': `Bearer ${token}`,
                'X-Tenant-ID': user.tenant_id
            };

            try {
                // Fetch cases
                const casesRes = await fetch('/api/v1/portal/cases?size=5', { headers });
                if (!casesRes.ok) throw new Error('Error al cargar expedientes');
                const casesData = await casesRes.json();
                setCases(casesData.items || []);

                // Fetch invoices
                const invoicesRes = await fetch('/api/v1/portal/invoices', { headers });
                if (!invoicesRes.ok) throw new Error('Error al cargar facturas');
                const invoicesData = await invoicesRes.json();
                setInvoices(invoicesData || []);

                // Fetch documents
                const docsRes = await fetch('/api/v1/portal/documents', { headers });
                if (!docsRes.ok) throw new Error('Error al cargar documentos');
                const docsData = await docsRes.json();
                setDocuments((docsData.items || []).slice(0, 5));

            } catch (err: any) {
                setError(err.message || 'Error de conexión');
            } finally {
                setLoading(false);
            }
        };

        fetchDashboardData();
    }, []);

    // Calculated metrics
    const activeCasesCount = cases.length;
    const unpaidInvoices = invoices.filter(inv => inv.estado !== 'pagada' && inv.estado !== 'anulada');
    const pendingPaymentsCount = unpaidInvoices.length;
    
    // Sum by currency
    const totalPendingUSD = unpaidInvoices
        .filter(inv => inv.moneda === 'USD')
        .reduce((sum, inv) => sum + Number(inv.neto_a_pagar), 0);
    const totalPendingNIO = unpaidInvoices
        .filter(inv => inv.moneda === 'NIO')
        .reduce((sum, inv) => sum + Number(inv.neto_a_pagar), 0);

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[60vh]">
                <div className="text-center space-y-4">
                    <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-amber-500 mx-auto"></div>
                    <p className="text-slate-400 text-sm">Cargando su resumen...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-10">
            {/* Header / Welcome banner */}
            <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 border border-slate-800/80 p-8 rounded-3xl relative overflow-hidden shadow-2xl">
                <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none">
                    <span className="text-8xl">🏛️</span>
                </div>
                <div className="relative z-10 space-y-3 max-w-2xl">
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                        LexIntellectus ERP
                    </span>
                    <h1 className="text-3xl lg:text-4xl font-bold tracking-tight text-white">
                        Bienvenido a su <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-200 via-amber-400 to-amber-200">Portal de Servicios</span>
                    </h1>
                    <p className="text-slate-300 text-sm lg:text-base leading-relaxed">
                        Aquí puede dar seguimiento al estado de sus casos legales, descargar documentos compartidos firmados de forma segura y realizar el pago de sus facturas vigentes.
                    </p>
                </div>
            </div>

            {/* Metrics cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Cases card */}
                <div className="bg-slate-900/60 border border-slate-800/80 p-6 rounded-2xl flex items-center justify-between shadow-xl backdrop-blur-sm group hover:border-slate-700/80 transition-all duration-300">
                    <div className="space-y-1.5">
                        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Casos Activos</span>
                        <h2 className="text-3xl font-bold text-white group-hover:text-amber-400 transition-colors">{activeCasesCount}</h2>
                        <Link href="/portal/cases" className="text-xs font-medium text-amber-500 hover:text-amber-400 flex items-center gap-1 pt-1.5 transition-colors">
                            Ver todos los casos
                            <span>&rarr;</span>
                        </Link>
                    </div>
                    <div className="w-12 h-12 bg-slate-800/80 border border-slate-700/60 rounded-xl flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">
                        📂
                    </div>
                </div>

                {/* Outstanding balance card */}
                <div className="bg-slate-900/60 border border-slate-800/80 p-6 rounded-2xl flex items-center justify-between shadow-xl backdrop-blur-sm group hover:border-slate-700/80 transition-all duration-300">
                    <div className="space-y-1.5">
                        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Saldo Pendiente</span>
                        <h2 className="text-2xl font-bold text-white group-hover:text-amber-400 transition-colors">
                            {totalPendingUSD > 0 && `$${totalPendingUSD.toFixed(2)} USD`}
                            {totalPendingUSD > 0 && totalPendingNIO > 0 && <span className="text-slate-500 text-sm font-normal mx-2">/</span>}
                            {totalPendingNIO > 0 && `${totalPendingNIO.toFixed(2)} C$ NIO`}
                            {totalPendingUSD === 0 && totalPendingNIO === 0 && '¡Sin deudas! $0.00'}
                        </h2>
                        <Link href="/portal/billing" className="text-xs font-medium text-amber-500 hover:text-amber-400 flex items-center gap-1 pt-1.5 transition-colors">
                            Pagar facturas pendientes
                            <span>&rarr;</span>
                        </Link>
                    </div>
                    <div className="w-12 h-12 bg-slate-800/80 border border-slate-700/60 rounded-xl flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">
                        💳
                    </div>
                </div>

                {/* Documents card */}
                <div className="bg-slate-900/60 border border-slate-800/80 p-6 rounded-2xl flex items-center justify-between shadow-xl backdrop-blur-sm group hover:border-slate-700/80 transition-all duration-300">
                    <div className="space-y-1.5">
                        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Documentos Compartidos</span>
                        <h2 className="text-3xl font-bold text-white group-hover:text-amber-400 transition-colors">{documents.length}</h2>
                        <Link href="/portal/documents" className="text-xs font-medium text-amber-500 hover:text-amber-400 flex items-center gap-1 pt-1.5 transition-colors">
                            Bóveda de documentos
                            <span>&rarr;</span>
                        </Link>
                    </div>
                    <div className="w-12 h-12 bg-slate-800/80 border border-slate-700/60 rounded-xl flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">
                        🔒
                    </div>
                </div>
            </div>

            {/* Dashboard sections (Grid layout) */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Left Section: Active cases brief */}
                <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 shadow-xl backdrop-blur-sm space-y-6">
                    <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
                        <h3 className="text-lg font-bold text-white flex items-center gap-2">
                            <span className="text-amber-400">📂</span> Expedientes Asignados
                        </h3>
                        <Link href="/portal/cases" className="text-xs text-amber-500 hover:text-amber-400 font-semibold transition-colors">
                            Ver todos
                        </Link>
                    </div>

                    {cases.length === 0 ? (
                        <div className="text-center py-10 space-y-3">
                            <div className="text-4xl text-slate-600">📁</div>
                            <p className="text-slate-400 text-sm font-medium">No tiene expedientes judiciales asignados por el momento.</p>
                        </div>
                    ) : (
                        <div className="divide-y divide-slate-800/60">
                            {cases.map((c) => (
                                <div key={c.id} className="py-4 first:pt-0 last:pb-0 flex items-start justify-between group">
                                    <div className="space-y-1">
                                        <h4 className="text-sm font-semibold text-white group-hover:text-amber-400 transition-colors">
                                            {c.numero_causa || 'Causa en trámite'}
                                        </h4>
                                        <p className="text-xs text-slate-400">
                                            Interno: <span className="text-slate-300 font-mono">{c.numero_interno}</span>
                                        </p>
                                        <p className="text-xs text-slate-400 truncate max-w-sm">
                                            Juzgado: <span className="text-slate-300">{c.juzgado || 'Pendiente'}</span>
                                        </p>
                                    </div>
                                    <span className={`inline-flex px-2 py-0.5 rounded text-[10px] font-semibold border ${
                                        c.prioridad === 'urgente' 
                                            ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' 
                                            : c.prioridad === 'alta'
                                            ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                                            : 'bg-slate-500/10 text-slate-300 border-slate-700/60'
                                    }`}>
                                        {c.prioridad.toUpperCase()}
                                    </span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Right Section: Recent shared documents vault */}
                <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 shadow-xl backdrop-blur-sm space-y-6">
                    <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
                        <h3 className="text-lg font-bold text-white flex items-center gap-2">
                            <span className="text-amber-400">📄</span> Documentos Recientes
                        </h3>
                        <Link href="/portal/documents" className="text-xs text-amber-500 hover:text-amber-400 font-semibold transition-colors">
                            Ver bóveda
                        </Link>
                    </div>

                    {documents.length === 0 ? (
                        <div className="text-center py-10 space-y-3">
                            <div className="text-4xl text-slate-600">📁</div>
                            <p className="text-slate-400 text-sm font-medium">Aún no se han compartido documentos oficiales con usted.</p>
                        </div>
                    ) : (
                        <div className="divide-y divide-slate-800/60">
                            {documents.map((doc) => (
                                <div key={doc.id} className="py-4 first:pt-0 last:pb-0 flex items-center justify-between group">
                                    <div className="space-y-1">
                                        <h4 className="text-sm font-semibold text-white truncate max-w-xs group-hover:text-amber-400 transition-colors">
                                            {doc.nombre_archivo}
                                        </h4>
                                        <p className="text-xs text-slate-400">
                                            Categoría: <span className="text-slate-300">{doc.categoria}</span>
                                        </p>
                                    </div>
                                    <Link 
                                        href="/portal/documents" 
                                        className="p-2 bg-slate-800 hover:bg-amber-500/10 border border-slate-700 hover:border-amber-500/20 text-slate-300 hover:text-amber-400 rounded-lg transition-all duration-200"
                                    >
                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                        </svg>
                                    </Link>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
