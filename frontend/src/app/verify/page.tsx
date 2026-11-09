'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';

function VerifyContent() {
    const searchParams = useSearchParams();
    const initialToken = searchParams.get('token') || '';

    const [tokenInput, setTokenInput] = useState(initialToken);
    const [result, setResult] = useState<any | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const verifyToken = async (targetToken: string) => {
        if (!targetToken.trim()) return;
        setLoading(true);
        setError('');
        try {
            const res = await fetch(`/api/v1/qr/verify?token=${encodeURIComponent(targetToken.trim())}`);
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || 'El sello QR no pudo ser verificado');
            }
            const data = await res.json();
            setResult(data);
        } catch (e: any) {
            setResult(null);
            setError(e.message || 'Error al validar el certificado QR');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (initialToken) {
            verifyToken(initialToken);
        }
    }, [initialToken]);

    return (
        <div className="min-h-screen bg-slate-950 text-slate-100 py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-3xl mx-auto space-y-8">
                {/* Brand Header */}
                <div className="text-center space-y-2">
                    <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-bold uppercase tracking-wider">
                        🏛️ Autoridad de Validación Criptográfica LexIntellectus
                    </div>
                    <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
                        Verificador Oficial de Sellos QR
                    </h1>
                    <p className="text-slate-400 text-sm max-w-xl mx-auto">
                        Valide en tiempo real la autenticidad e integridad de Reportes Ejecutivos, Facturas, Documentos Firmados Electrónicamente y Expedientes generados por LexIntellectus ERP.
                    </p>
                </div>

                {/* Manual Token Input */}
                <form
                    onSubmit={(e) => {
                        e.preventDefault();
                        verifyToken(tokenInput);
                    }}
                    className="bg-slate-900/70 border border-slate-800 rounded-2xl p-4 flex flex-col sm:flex-row gap-3 shadow-xl"
                >
                    <input
                        type="text"
                        placeholder="Pegue aquí el token del código QR para verificar su firma HMAC-SHA256..."
                        value={tokenInput}
                        onChange={(e) => setTokenInput(e.target.value)}
                        className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs font-mono text-slate-200 focus:outline-none focus:border-amber-500"
                    />
                    <button
                        type="submit"
                        disabled={loading || !tokenInput.trim()}
                        className="px-6 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold transition-colors disabled:opacity-50"
                    >
                        {loading ? 'Verificando...' : 'Validar Sello QR'}
                    </button>
                </form>

                {/* Error State */}
                {error && (
                    <div className="bg-rose-500/10 border border-rose-500/30 rounded-2xl p-6 text-center space-y-2">
                        <div className="text-4xl">⚠️</div>
                        <h3 className="text-lg font-bold text-rose-400">Sello Criptográfico Inválido</h3>
                        <p className="text-sm text-slate-300">{error}</p>
                    </div>
                )}

                {/* Valid Certificate Result */}
                {result && result.valid && (
                    <div className="bg-slate-900 border border-emerald-500/40 rounded-3xl p-6 sm:p-8 shadow-2xl space-y-6">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-6">
                            <div className="flex items-center gap-4">
                                <div className="w-14 h-14 rounded-2xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 flex items-center justify-center text-3xl font-bold">
                                    ✓
                                </div>
                                <div>
                                    <span className="text-xs font-bold uppercase tracking-wider text-emerald-400">
                                        Documento / Reporte Auténtico e Íntegro
                                    </span>
                                    <h2 className="text-2xl font-extrabold text-white mt-0.5">
                                        {result.verification_code}
                                    </h2>
                                    <p className="text-xs text-slate-400">{result.issuer}</p>
                                </div>
                            </div>
                            <span className="px-3 py-1 rounded-full bg-slate-800 text-amber-400 text-xs font-bold uppercase self-start sm:self-center">
                                Tipo: {result.entity_type}
                            </span>
                        </div>

                        {/* Cryptographic Metadata */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 bg-slate-950/60 p-4 rounded-2xl border border-slate-800/80 text-xs">
                            <div>
                                <span className="text-slate-500 block font-semibold uppercase">Fecha de Emisión</span>
                                <span className="text-slate-200 font-mono">{result.issued_at}</span>
                            </div>
                            <div>
                                <span className="text-slate-500 block font-semibold uppercase">Fecha de Verificación</span>
                                <span className="text-slate-200 font-mono">{result.verified_at}</span>
                            </div>
                            <div className="sm:col-span-2">
                                <span className="text-slate-500 block font-semibold uppercase">Huella Digital SHA-256 (Inmutable)</span>
                                <span className="text-emerald-400 font-mono break-all">{result.sha256_hash}</span>
                            </div>
                        </div>

                        {/* Live Status by Entity Type */}
                        {result.entity_type === 'report' && result.live_status && (
                            <div className="space-y-3">
                                <h3 className="text-sm font-bold text-amber-400 uppercase tracking-wider">
                                    📊 Datos Certificados del Reporte Ejecutivo
                                </h3>
                                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                                    <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                                        <span className="text-[11px] text-slate-400 block">Casos Activos</span>
                                        <span className="text-xl font-bold text-white">
                                            {result.live_status.metricas_certificadas?.active_cases ?? 0}
                                        </span>
                                    </div>
                                    <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                                        <span className="text-[11px] text-slate-400 block">Total Casos</span>
                                        <span className="text-xl font-bold text-white">
                                            {result.live_status.metricas_certificadas?.total_cases ?? 0}
                                        </span>
                                    </div>
                                    <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                                        <span className="text-[11px] text-slate-400 block">Plazos Pendientes</span>
                                        <span className="text-xl font-bold text-white">
                                            {result.live_status.metricas_certificadas?.pending_deadlines ?? 0}
                                        </span>
                                    </div>
                                    <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                                        <span className="text-[11px] text-slate-400 block">Tasa Resolución</span>
                                        <span className="text-xl font-bold text-emerald-400">
                                            {result.live_status.metricas_certificadas?.resolution_rate ?? 0}%
                                        </span>
                                    </div>
                                </div>
                                <p className="text-xs text-slate-400">
                                    Despacho Emisor: <strong className="text-white">{result.live_status.despacho}</strong> • Emitido por: <strong className="text-white">{result.live_status.emitido_por}</strong>
                                </p>
                            </div>
                        )}

                        {result.entity_type === 'invoice' && result.live_status && (
                            <div className="space-y-4">
                                <h3 className="text-sm font-bold text-amber-400 uppercase tracking-wider">
                                    🧾 Estado Fiscal y Contable en Tiempo Real
                                </h3>
                                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-sm">
                                    <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                                        <span className="text-xs text-slate-400 block">No. Factura</span>
                                        <span className="font-bold text-white">{result.live_status.numero_factura}</span>
                                    </div>
                                    <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                                        <span className="text-xs text-slate-400 block">Estado en Vivo</span>
                                        <span className="font-bold uppercase text-emerald-400">{result.live_status.estado_actual}</span>
                                    </div>
                                    <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                                        <span className="text-xs text-slate-400 block">Neto a Pagar</span>
                                        <span className="font-bold text-white">
                                            {result.live_status.moneda} {result.live_status.neto_a_pagar}
                                        </span>
                                    </div>
                                </div>
                                {result.live_status.action_url && (
                                    <Link
                                        href={result.live_status.action_url}
                                        className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold"
                                    >
                                        💳 Ir al Portal de Pagos Online &rarr;
                                    </Link>
                                )}
                            </div>
                        )}

                        {result.entity_type === 'document' && result.live_status && (
                            <div className="space-y-3">
                                <h3 className="text-sm font-bold text-amber-400 uppercase tracking-wider">
                                    📄 Certificación de Documento y Firma Electrónica
                                </h3>
                                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2 text-xs">
                                    <p>Archivo: <strong className="text-white">{result.live_status.nombre_archivo}</strong></p>
                                    <p>Firmas Electrónicas Registradas: <strong className="text-emerald-400">{result.live_status.total_firmas_electronicas}</strong></p>
                                    {result.live_status.ultima_firma_hash && (
                                        <p className="font-mono text-slate-300 break-all">
                                            Hash Firma Electrónica: {result.live_status.ultima_firma_hash}
                                        </p>
                                    )}
                                </div>
                            </div>
                        )}

                        {result.entity_type === 'case' && result.live_status && (
                            <div className="space-y-3">
                                <h3 className="text-sm font-bold text-amber-400 uppercase tracking-wider">
                                    ⚖️ Ficha de Expediente Judicial Verificada
                                </h3>
                                <div className="grid grid-cols-2 gap-3 text-xs bg-slate-950 p-4 rounded-xl border border-slate-800">
                                    <div>
                                        <span className="text-slate-400 block">No. Interno</span>
                                        <strong className="text-white">{result.live_status.numero_interno}</strong>
                                    </div>
                                    <div>
                                        <span className="text-slate-400 block">No. Causa Judicial</span>
                                        <strong className="text-white">{result.live_status.numero_causa || 'N/A'}</strong>
                                    </div>
                                    <div>
                                        <span className="text-slate-400 block">Tipo de Servicio</span>
                                        <strong className="text-white uppercase">{result.live_status.tipo_servicio}</strong>
                                    </div>
                                    <div>
                                        <span className="text-slate-400 block">Juzgado / Sede</span>
                                        <strong className="text-white">{result.live_status.juzgado || 'Sede Central'}</strong>
                                    </div>
                                </div>
                                {result.live_status.action_url && (
                                    <Link
                                        href={result.live_status.action_url}
                                        className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold"
                                    >
                                        📂 Abrir Expediente en LexIntellectus &rarr;
                                    </Link>
                                )}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

export default function VerifyQRPage() {
    return (
        <Suspense fallback={<div className="min-h-screen bg-slate-950 text-white flex items-center justify-center">Cargando verificador QR...</div>}>
            <VerifyContent />
        </Suspense>
    );
}
