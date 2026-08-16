'use client';

import { useState, useEffect } from 'react';

interface Party {
    id: string;
    nombre_completo: string;
    rol_procesal: string;
    tipo_persona: string;
}

interface CaseDetails {
    id: string;
    numero_causa?: string;
    numero_interno?: string;
    tipo_servicio: string;
    ramo?: string;
    tipo_proceso?: string;
    juzgado?: string;
    juez?: string;
    secretario?: string;
    resumen?: string;
    prioridad: string;
    fecha_apertura?: string;
    moneda?: string;
    valor_estimado?: number;
    partes: Party[];
}

export default function PortalCases() {
    const [cases, setCases] = useState<CaseDetails[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    
    // Modal state
    const [selectedCase, setSelectedCase] = useState<CaseDetails | null>(null);

    useEffect(() => {
        const fetchCases = async () => {
            const token = localStorage.getItem('access_token');
            const userStr = localStorage.getItem('user');

            if (!token || !userStr) {
                window.location.href = '/login';
                return;
            }

            const user = JSON.parse(userStr);
            try {
                const res = await fetch('/api/v1/portal/cases', {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'X-Tenant-ID': user.tenant_id
                    }
                });

                if (!res.ok) throw new Error('Error al cargar expedientes');
                const data = await res.json();
                setCases(data.items || []);
            } catch (err: any) {
                setError(err.message || 'Error de conexión');
            } finally {
                setLoading(false);
            }
        };

        fetchCases();
    }, []);

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[60vh]">
                <div className="text-center space-y-4">
                    <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-amber-500 mx-auto"></div>
                    <p className="text-slate-400 text-sm">Cargando sus expedientes...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-8">
            {/* Page Header */}
            <div>
                <h1 className="text-3xl font-extrabold text-white tracking-tight">Mis Expedientes</h1>
                <p className="text-slate-400 text-sm mt-2">Consulte el estado, los tribunales asignados y la composición de las partes en sus litigios vigentes.</p>
            </div>

            {cases.length === 0 ? (
                <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-12 text-center space-y-4">
                    <div className="text-5xl">📂</div>
                    <h3 className="text-lg font-bold text-white">Sin expedientes registrados</h3>
                    <p className="text-slate-400 text-sm max-w-sm mx-auto">Actualmente no posee causas legales activas en nuestro sistema de seguimiento.</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {cases.map((c) => (
                        <div 
                            key={c.id} 
                            className="bg-slate-900/50 border border-slate-800/80 hover:border-slate-700/80 rounded-2xl p-6 shadow-xl backdrop-blur-sm group flex flex-col justify-between transition-all duration-300"
                        >
                            <div className="space-y-4">
                                <div className="flex items-start justify-between">
                                    <div className="space-y-1">
                                        <span className="text-[10px] uppercase font-bold text-amber-500 tracking-wider">
                                            {c.tipo_servicio}
                                        </span>
                                        <h3 className="text-lg font-bold text-white group-hover:text-amber-400 transition-colors">
                                            {c.numero_causa || 'Número de causa en trámite'}
                                        </h3>
                                        <p className="text-xs text-slate-400">
                                            Número interno: <span className="font-mono text-slate-300">{c.numero_interno}</span>
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

                                <div className="space-y-2 text-xs border-t border-slate-800/60 pt-4">
                                    <div className="flex justify-between">
                                        <span className="text-slate-400">Juzgado:</span>
                                        <span className="text-slate-200 font-medium truncate max-w-[200px]">{c.juzgado || 'Por definir'}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-slate-400">Tipo de Proceso:</span>
                                        <span className="text-slate-200 font-medium">{c.tipo_proceso || 'General'}</span>
                                    </div>
                                    {c.fecha_apertura && (
                                        <div className="flex justify-between">
                                            <span className="text-slate-400">Fecha de Apertura:</span>
                                            <span className="text-slate-200 font-medium">{c.fecha_apertura}</span>
                                        </div>
                                    )}
                                </div>
                            </div>

                            <div className="pt-6 mt-4 border-t border-slate-800/40 flex justify-end">
                                <button
                                    onClick={() => setSelectedCase(c)}
                                    className="px-4 py-2 text-xs font-semibold bg-slate-800 hover:bg-amber-500 hover:text-slate-950 text-slate-200 rounded-xl transition-all duration-300"
                                >
                                    Detalle Expediente
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Sleek details modal */}
            {selectedCase && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
                    {/* Backdrop */}
                    <div 
                        className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm transition-opacity"
                        onClick={() => setSelectedCase(null)}
                    />
                    
                    {/* Content Box */}
                    <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 lg:p-8 max-w-2xl w-full shadow-2xl relative z-10 space-y-6 max-h-[85vh] overflow-y-auto">
                        <div className="flex justify-between items-start">
                            <div className="space-y-1">
                                <span className="text-xs font-bold text-amber-500 uppercase tracking-wider">{selectedCase.tipo_servicio}</span>
                                <h2 className="text-2xl font-bold text-white">{selectedCase.numero_causa || 'Causa en trámite'}</h2>
                                <p className="text-xs text-slate-400">Interno: <span className="font-mono text-slate-300">{selectedCase.numero_interno}</span></p>
                            </div>
                            <button
                                onClick={() => setSelectedCase(null)}
                                className="p-1 rounded-lg text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 transition-colors"
                            >
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>

                        {/* Description / Summary */}
                        {selectedCase.resumen && (
                            <div className="space-y-2 bg-slate-950/50 p-4 rounded-xl border border-slate-800/80">
                                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Resumen Informativo</h4>
                                <p className="text-slate-300 text-sm leading-relaxed">{selectedCase.resumen}</p>
                            </div>
                        )}

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
                            {/* Court Metadata */}
                            <div className="space-y-4">
                                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider border-b border-slate-800 pb-2">Información del Juzgado</h4>
                                <div className="space-y-2 text-xs">
                                    <div className="flex justify-between py-1">
                                        <span className="text-slate-400">Juzgado/Tribunal:</span>
                                        <span className="text-white font-medium">{selectedCase.juzgado || 'No definido'}</span>
                                    </div>
                                    <div className="flex justify-between py-1">
                                        <span className="text-slate-400">Juez:</span>
                                        <span className="text-white font-medium">{selectedCase.juez || 'Por definir'}</span>
                                    </div>
                                    <div className="flex justify-between py-1">
                                        <span className="text-slate-400">Secretario:</span>
                                        <span className="text-white font-medium">{selectedCase.secretario || 'Por definir'}</span>
                                    </div>
                                    <div className="flex justify-between py-1">
                                        <span className="text-slate-400">Ramo Judicial:</span>
                                        <span className="text-white font-medium">{selectedCase.ramo || 'General'}</span>
                                    </div>
                                </div>
                            </div>

                            {/* Case Parties */}
                            <div className="space-y-4">
                                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider border-b border-slate-800 pb-2">Sujetos Procesales</h4>
                                {selectedCase.partes.length === 0 ? (
                                    <p className="text-xs text-slate-400 italic">No hay contrapartes o sujetos registrados.</p>
                                ) : (
                                    <div className="space-y-2">
                                        {selectedCase.partes.map((p) => (
                                            <div key={p.id} className="flex justify-between py-1.5 border-b border-slate-800/40 last:border-b-0">
                                                <span className="text-slate-200 text-xs truncate max-w-[160px]">{p.nombre_completo}</span>
                                                <span className="text-[10px] font-semibold text-amber-500 bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/20 uppercase">
                                                    {p.rol_procesal}
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>

                        <div className="pt-6 border-t border-slate-800 flex justify-end">
                            <button
                                onClick={() => setSelectedCase(null)}
                                className="px-6 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold transition-colors"
                            >
                                Cerrar Ventana
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
