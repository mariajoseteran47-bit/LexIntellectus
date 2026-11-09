'use client';

import { useState, useEffect, useRef } from 'react';

interface DocumentInfo {
    id: string;
    nombre_archivo: string;
    tipo_archivo: string;
    tamano_bytes: number;
    created_at: string;
    descripcion?: string;
    categoria: string;
    tags?: string[];
}

export default function PortalDocuments() {
    const [documents, setDocuments] = useState<DocumentInfo[]>([]);
    const [search, setSearch] = useState('');
    const [categoryFilter, setCategoryFilter] = useState('all');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [downloadingId, setDownloadingId] = useState<string | null>(null);

    // Signature Modal State
    const [signingDoc, setSigningDoc] = useState<DocumentInfo | null>(null);
    const [isSubmittingSignature, setIsSubmittingSignature] = useState(false);
    const [copySuccess, setCopySuccess] = useState(false);
    const [approvals, setApprovals] = useState<any[]>([]);
    const [decidingId, setDecidingId] = useState<string | null>(null);

    // Canvas references for drawing
    const canvasRef = useRef<HTMLCanvasElement | null>(null);
    const [isDrawing, setIsDrawing] = useState(false);

    const fetchDocuments = async () => {
        const token = localStorage.getItem('access_token');
        const userStr = localStorage.getItem('user');

        if (!token || !userStr) {
            window.location.href = '/login';
            return;
        }

        const user = JSON.parse(userStr);
        try {
            const res = await fetch('/api/v1/portal/documents', {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'X-Tenant-ID': user.tenant_id
                }
            });

            if (!res.ok) throw new Error('Error al cargar documentos');
            const data = await res.json();
            setDocuments(data.items || []);

            const appRes = await fetch('/api/v1/portal/approvals', {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'X-Tenant-ID': user.tenant_id
                }
            });
            if (appRes.ok) {
                const appData = await appRes.json();
                setApprovals(appData.items || []);
            }
        } catch (err: any) {
            setError(err.message || 'Error de conexión');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchDocuments();
    }, []);

    const handleDownload = async (docId: string, filename: string) => {
        setDownloadingId(docId);
        const token = localStorage.getItem('access_token');
        const userStr = localStorage.getItem('user');
        
        if (!token || !userStr) return;
        const user = JSON.parse(userStr);

        try {
            const res = await fetch(`/api/v1/portal/documents/${docId}/download`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'X-Tenant-ID': user.tenant_id
                }
            });

            if (!res.ok) throw new Error('No se pudo generar el enlace de descarga');
            const data = await res.json();
            window.open(data.url, '_blank');
        } catch (err: any) {
            alert(err.message || 'Error al descargar documento');
        } finally {
            setDownloadingId(null);
        }
    };

    // Calendar Sync URL Generation
    const getCalendarSyncUrl = () => {
        if (typeof window === 'undefined') return '';
        const token = localStorage.getItem('access_token') || '';
        const protocol = window.location.protocol;
        const host = window.location.host;
        // In development backend runs on 8000, but in production it maps to the same domain.
        // We output the backend URL directly.
        const port = host.includes('localhost') ? '8000' : '';
        const domain = host.split(':')[0];
        const backendBase = port ? `${protocol}//${domain}:${port}` : `${protocol}//${host}`;
        
        return `${backendBase}/api/v1/portal/calendar/ical.ics?token=${token}`;
    };

    const handleCopyCalendarUrl = () => {
        const url = getCalendarSyncUrl();
        navigator.clipboard.writeText(url);
        setCopySuccess(true);
        setTimeout(() => setCopySuccess(false), 3000);
    };

    const handleApprovalDecision = async (approvalId: string, estado: 'aprobado' | 'rechazado') => {
        const token = localStorage.getItem('access_token');
        const userStr = localStorage.getItem('user');
        if (!token || !userStr) return;
        const user = JSON.parse(userStr);
        setDecidingId(approvalId);
        try {
            const res = await fetch(`/api/v1/portal/approvals/${approvalId}/decision`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                    'X-Tenant-ID': user.tenant_id
                },
                body: JSON.stringify({
                    approval_id: approvalId,
                    estado,
                    comentarios: estado === 'aprobado' ? 'Aprobado por el cliente desde el Portal' : 'Observado / Rechazado por el cliente'
                })
            });
            if (res.ok) {
                await fetchDocuments();
            }
        } catch (err) {
            console.error('Error deciding approval:', err);
        } finally {
            setDecidingId(null);
        }
    };

    // Canvas drawing logic
    const startDrawing = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        setIsDrawing(true);

        const rect = canvas.getBoundingClientRect();
        let clientX = 0;
        let clientY = 0;

        if ('touches' in e) {
            clientX = e.touches[0].clientX;
            clientY = e.touches[0].clientY;
        } else {
            clientX = e.clientX;
            clientY = e.clientY;
        }

        ctx.beginPath();
        ctx.moveTo(clientX - rect.left, clientY - rect.top);
        ctx.strokeStyle = '#f59e0b'; // Amber Gold color for rubric
        ctx.lineWidth = 3;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
    };

    const draw = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
        if (!isDrawing) return;
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        const rect = canvas.getBoundingClientRect();
        let clientX = 0;
        let clientY = 0;

        if ('touches' in e) {
            // Prevent scrolling on mobile when drawing
            e.preventDefault();
            clientX = e.touches[0].clientX;
            clientY = e.touches[0].clientY;
        } else {
            clientX = e.clientX;
            clientY = e.clientY;
        }

        ctx.lineTo(clientX - rect.left, clientY - rect.top);
        ctx.stroke();
    };

    const stopDrawing = () => {
        setIsDrawing(false);
    };

    const clearCanvas = () => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
    };

    // Electronic Signature Submission
    const handleSignDocument = async () => {
        const canvas = canvasRef.current;
        if (!canvas || !signingDoc) return;

        setIsSubmittingSignature(true);
        const token = localStorage.getItem('access_token');
        const userStr = localStorage.getItem('user');
        if (!token || !userStr) return;
        const user = JSON.parse(userStr);

        // Convert signature canvas drawing to base64 Data URL representation
        const signatureBase64 = canvas.toDataURL('image/png');

        try {
            const res = await fetch(`/api/v1/portal/documents/${signingDoc.id}/sign`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                    'X-Tenant-ID': user.tenant_id
                },
                body: JSON.stringify({ signature_svg: signatureBase64 })
            });

            if (!res.ok) throw new Error('Error al registrar firma electrónica');
            
            // Reload documents and close modal
            await fetchDocuments();
            setSigningDoc(null);
            alert('¡Documento firmado electrónicamente con éxito! Se ha generado un registro de auditoría inmutable.');
        } catch (err: any) {
            alert(err.message || 'Error al firmar documento');
        } finally {
            setIsSubmittingSignature(false);
        }
    };

    const formatBytes = (bytes: number, decimals = 2) => {
        if (!bytes || bytes === 0) return '0 Bytes';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    };

    const filteredDocs = documents.filter(doc => {
        const matchesSearch = doc.nombre_archivo.toLowerCase().includes(search.toLowerCase()) || 
                             (doc.descripcion && doc.descripcion.toLowerCase().includes(search.toLowerCase()));
        const matchesCategory = categoryFilter === 'all' || doc.categoria === categoryFilter;
        return matchesSearch && matchesCategory;
    });

    const categories = ['all', 'general', 'evidencia', 'escrito', 'notificacion', 'sentencia', 'contrato'];

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[60vh]">
                <div className="text-center space-y-4">
                    <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-amber-500 mx-auto"></div>
                    <p className="text-slate-400 text-sm">Cargando bóveda documental...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-8">
            {/* Page Header */}
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
                <div>
                    <h1 className="text-3xl font-extrabold text-white tracking-tight">Bóveda Documental</h1>
                    <p className="text-slate-400 text-sm mt-2">Explore, firme y descargue copias digitales certificadas de sus expedientes judiciales en tiempo real.</p>
                </div>

                {/* iCal Subscription Button */}
                <div className="relative shrink-0">
                    <button
                        onClick={handleCopyCalendarUrl}
                        className="inline-flex items-center gap-2.5 px-4 py-2.5 rounded-xl bg-gradient-to-r from-amber-500/10 to-yellow-600/10 hover:from-amber-500/20 hover:to-yellow-600/20 text-amber-400 border border-amber-500/30 font-semibold text-sm hover:scale-[1.02] active:scale-[0.98] transition-all duration-200"
                        title="Suscribirse a Google Calendar o Outlook"
                    >
                        <span>📅</span>
                        <span>{copySuccess ? '¡Enlace Copiado!' : 'Sincronizar Calendario iCal'}</span>
                    </button>
                    {copySuccess && (
                        <span className="absolute -bottom-6 right-0 text-[10px] text-green-400 font-mono">
                            ¡Pega este enlace en tu app de calendario!
                        </span>
                    )}
                </div>
            </div>

            {/* Approvals Inbox (if any) */}
            {approvals.length > 0 && (
                <div className="bg-slate-900/50 border border-amber-500/30 rounded-2xl p-6 space-y-4">
                    <div className="flex items-center justify-between">
                        <h3 className="text-sm font-bold text-amber-400 uppercase tracking-wider">
                            📋 Bandeja de Aprobación de Documentos ({approvals.filter(a => a.estado === 'pendiente').length} pendientes)
                        </h3>
                    </div>
                    <div className="divide-y divide-slate-800/80">
                        {approvals.map((ap) => (
                            <div key={ap.id} className="py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                                <div>
                                    <p className="text-sm font-bold text-white">{ap.nombre_archivo}</p>
                                    <p className="text-xs text-slate-400">
                                        Solicitado por {ap.solicitante_nombre} • {ap.motivo_solicitud || 'Revisión de borrador'}
                                    </p>
                                </div>
                                <div className="flex items-center gap-2">
                                    {ap.estado === 'pendiente' ? (
                                        <>
                                            <button
                                                onClick={() => handleApprovalDecision(ap.id, 'aprobado')}
                                                disabled={decidingId === ap.id}
                                                className="px-3 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-bold"
                                            >
                                                ✓ Aprobar
                                            </button>
                                            <button
                                                onClick={() => handleApprovalDecision(ap.id, 'rechazado')}
                                                disabled={decidingId === ap.id}
                                                className="px-3 py-1.5 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/30 text-xs font-bold"
                                            >
                                                ✕ Rechazar
                                            </button>
                                        </>
                                    ) : (
                                        <span className={`px-2.5 py-1 rounded text-[10px] font-bold uppercase ${
                                            ap.estado === 'aprobado'
                                                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                                : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                                        }`}>
                                            {ap.estado}
                                        </span>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Filters Bar */}
            <div className="flex flex-col md:flex-row gap-4 justify-between items-start md:items-center bg-slate-900/40 p-4 border border-slate-800/80 rounded-2xl">
                {/* Search */}
                <div className="relative w-full md:w-96">
                    <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">
                        🔍
                    </span>
                    <input
                        type="text"
                        placeholder="Buscar por nombre o descripción..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 text-white rounded-xl py-2.5 pl-10 pr-4 text-sm focus:outline-none focus:ring-1 focus:ring-amber-500/50 focus:border-amber-500/50 transition-all duration-200"
                    />
                </div>

                {/* Categories Scrollable Tabs */}
                <div className="flex gap-2 overflow-x-auto max-w-full pb-1 md:pb-0 scrollbar-none">
                    {categories.map((cat) => (
                        <button
                            key={cat}
                            onClick={() => setCategoryFilter(cat)}
                            className={`px-3 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wider border transition-all duration-200 ${
                                categoryFilter === cat
                                    ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                                    : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-white hover:border-slate-700'
                            }`}
                        >
                            {cat}
                        </button>
                    ))}
                </div>
            </div>

            {/* Documents List */}
            {filteredDocs.length === 0 ? (
                <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-12 text-center space-y-4">
                    <div className="text-5xl">📂</div>
                    <h3 className="text-lg font-bold text-white">No se hallaron documentos</h3>
                    <p className="text-slate-400 text-sm max-w-sm mx-auto">No hay archivos compartidos que coincidan con sus criterios de búsqueda.</p>
                </div>
            ) : (
                <div className="bg-slate-900/30 border border-slate-800/80 rounded-2xl overflow-hidden shadow-2xl">
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="border-b border-slate-800/80 bg-slate-900/70 text-slate-400 text-xs font-semibold tracking-wider uppercase">
                                    <th className="px-6 py-4">Nombre Archivo</th>
                                    <th className="px-6 py-4 hidden md:table-cell">Categoría</th>
                                    <th className="px-6 py-4 hidden md:table-cell">Tamaño</th>
                                    <th className="px-6 py-4 hidden lg:table-cell">Estado Firma</th>
                                    <th className="px-6 py-4 text-right">Acciones</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800/60 text-sm">
                                {filteredDocs.map((doc) => {
                                    const isSigned = doc.tags?.includes('firmado') || false;
                                    return (
                                        <tr key={doc.id} className="hover:bg-slate-900/40 transition-colors group">
                                            <td className="px-6 py-4">
                                                <div className="flex items-center gap-3">
                                                    <div className="w-10 h-10 rounded-xl bg-slate-800 border border-slate-700/60 flex items-center justify-center text-xl shrink-0 group-hover:scale-105 transition-transform">
                                                        📄
                                                    </div>
                                                    <div className="min-w-0">
                                                        <h4 className="font-semibold text-white truncate max-w-[200px] md:max-w-sm">
                                                            {doc.nombre_archivo}
                                                        </h4>
                                                        {doc.descripcion && (
                                                            <p className="text-xs text-slate-400 truncate max-w-[200px] md:max-w-sm">{doc.descripcion}</p>
                                                        )}
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 hidden md:table-cell text-slate-300">
                                                <span className="inline-flex px-2 py-0.5 rounded text-[10px] font-semibold border bg-slate-800/80 border-slate-700/60 uppercase">
                                                    {doc.categoria}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 hidden md:table-cell text-slate-300 font-mono text-xs">
                                                {formatBytes(doc.tamano_bytes)}
                                            </td>
                                            <td className="px-6 py-4 hidden lg:table-cell">
                                                {isSigned ? (
                                                    <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                                                        <span>✓</span> Firmado Electrónicamente
                                                    </span>
                                                ) : (
                                                    <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                                                        <span>✍️</span> Firma Pendiente
                                                    </span>
                                                )}
                                            </td>
                                            <td className="px-6 py-4 text-right">
                                                <div className="flex items-center justify-end gap-2">
                                                    {/* Sign Button */}
                                                    {!isSigned && (
                                                        <button
                                                            onClick={() => setSigningDoc(doc)}
                                                            className="inline-flex items-center justify-center p-2 rounded-xl bg-amber-500/10 hover:bg-amber-500 text-amber-400 hover:text-slate-950 border border-amber-500/30 hover:border-amber-500 transition-all duration-200"
                                                            title="Firmar Documento"
                                                        >
                                                            <span className="text-xs font-semibold px-1">Firmar</span>
                                                        </button>
                                                    )}

                                                    {/* Download Button */}
                                                    <button
                                                        onClick={() => handleDownload(doc.id, doc.nombre_archivo)}
                                                        disabled={downloadingId !== null}
                                                        className="inline-flex items-center justify-center p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 disabled:opacity-50 transition-all duration-200"
                                                        title="Descargar"
                                                    >
                                                        {downloadingId === doc.id ? (
                                                            <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-slate-200"></div>
                                                        ) : (
                                                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                                            </svg>
                                                        )}
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* Interactive Electronic Signature Modal */}
            {signingDoc && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-md p-4">
                    <div className="relative w-full max-w-lg bg-slate-900 border border-slate-800 rounded-3xl overflow-hidden shadow-2xl p-6 md:p-8 space-y-6">
                        {/* Modal Header */}
                        <div>
                            <div className="flex justify-between items-start">
                                <h3 className="text-xl font-bold text-white tracking-tight">Firma Electrónica Simple</h3>
                                <button
                                    onClick={() => setSigningDoc(null)}
                                    className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/80"
                                >
                                    ✕
                                </button>
                            </div>
                            <p className="text-xs text-slate-400 mt-1">
                                Documento: <span className="font-semibold text-amber-400 font-mono">{signingDoc.nombre_archivo}</span>
                            </p>
                        </div>

                        {/* Security Disclaimer */}
                        <div className="bg-amber-500/5 border border-amber-500/10 p-3.5 rounded-2xl text-[11px] text-amber-300 leading-relaxed">
                            <strong>⚠️ AVISO DE AUDITORÍA LEGAL</strong><br />
                            Al proceder, capturaremos su rúbrica digitalizada, dirección IP de origen, huella del navegador y estampa de tiempo, calculando una firma hash SHA-256 inmutable de auditoría forense para este archivo.
                        </div>

                        {/* Signature Board (HTML5 Canvas) */}
                        <div className="space-y-2">
                            <label className="text-xs font-semibold text-slate-300">Dibuje su Rúbrica / Firma:</label>
                            <div className="bg-slate-950 border border-slate-800 rounded-2xl overflow-hidden touch-none relative h-52">
                                <canvas
                                    ref={canvasRef}
                                    width={450}
                                    height={208}
                                    className="w-full h-full cursor-crosshair"
                                    onMouseDown={startDrawing}
                                    onMouseMove={draw}
                                    onMouseUp={stopDrawing}
                                    onMouseLeave={stopDrawing}
                                    onTouchStart={startDrawing}
                                    onTouchMove={draw}
                                    onTouchEnd={stopDrawing}
                                />
                            </div>
                            <div className="flex justify-end">
                                <button
                                    onClick={clearCanvas}
                                    className="text-xs font-semibold text-slate-400 hover:text-white transition-colors"
                                >
                                    🔄 Limpiar rúbrica
                                </button>
                            </div>
                        </div>

                        {/* Modal Actions */}
                        <div className="flex justify-end gap-3 pt-2">
                            <button
                                onClick={() => setSigningDoc(null)}
                                className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-semibold transition-all"
                            >
                                Cancelar
                            </button>
                            <button
                                onClick={handleSignDocument}
                                disabled={isSubmittingSignature}
                                className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-yellow-600 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 text-slate-950 text-xs font-bold transition-all duration-200"
                            >
                                {isSubmittingSignature ? 'Registrando Firma...' : 'Firmar Electrónicamente'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
