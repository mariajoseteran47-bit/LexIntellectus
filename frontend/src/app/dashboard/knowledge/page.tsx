'use client';

import React, { useState } from 'react';
import { Upload, Database, CheckCircle, AlertCircle, FileText, Scale, Loader2, Info } from 'lucide-react';
import { aiService } from '@/services/aiService';

export default function KnowledgeIngestionPage() {
    const [file, setFile] = useState<File | null>(null);
    const [sourceType, setSourceType] = useState('ley');
    const [status, setStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
    const [result, setResult] = useState<any>(null);
    const [stats, setStats] = useState<any>(null);

    React.useEffect(() => {
        const fetchStats = async () => {
            try {
                const token = localStorage.getItem('access_token');
                const res = await fetch('/api/v1/ai/stats', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (res.ok) {
                    const data = await res.json();
                    setStats(data);
                }
            } catch (error) {
                console.error(error);
            }
        };
        fetchStats();
    }, []);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
        }
    };

    const handleUpload = async () => {
        if (!file) return;
        setStatus('uploading');
        try {
            const resp = await aiService.ingestDocument(file, sourceType);
            setResult(resp);
            setStatus('success');
            setFile(null);
            // Refresh stats
            try {
                const token = localStorage.getItem('access_token');
                const res = await fetch('/api/v1/ai/stats', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (res.ok) {
                    const data = await res.json();
                    setStats(data);
                }
            } catch (err) {
                console.error('Error fetching stats:', err);
            }
        } catch (error) {
            console.error(error);
            setStatus('error');
        }
    };

    return (
        <div className="max-w-4xl mx-auto space-y-8">
            <div className="flex flex-col gap-2">
                <h1 className="text-2xl font-bold text-surface-900 flex items-center gap-3">
                    <Database className="text-[#D4AF37]" /> Gestión de Conocimiento Base (RAG)
                </h1>
                <p className="text-surface-600">
                    Alimenta la inteligencia de LexIntellectus subiendo el Digesto Jurídico, Jurisprudencia de la CSJ y Gacetas.
                </p>
                {stats && !stats.api_key_configured && (
                    <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl flex items-start gap-3 mt-4">
                        <AlertCircle className="text-amber-500 mt-0.5 flex-shrink-0" />
                        <div>
                            <p className="text-sm font-bold text-amber-800">Falta GOOGLE_API_KEY</p>
                            <p className="text-xs text-amber-700">
                                Las funciones de IA, incluyendo la ingesta vectorial, no funcionarán hasta que configures la clave `GOOGLE_API_KEY` en el archivo `.env` del servidor.
                            </p>
                        </div>
                    </div>
                )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {/* Stats Card */}
                <div className="card p-6 bg-[#1E3A5F] text-white space-y-4">
                    <h3 className="text-sm font-bold text-[#D4AF37] uppercase tracking-wider">Estado de la Base</h3>
                    <div className="flex items-center justify-between">
                        <span className="text-surface-300 text-sm">Leyes Indexadas:</span>
                        <span className="font-mono font-bold">{stats?.leyes_count ?? '...'}</span>
                    </div>
                    <div className="flex items-center justify-between">
                        <span className="text-surface-300 text-sm">Jurisprudencia:</span>
                        <span className="font-mono font-bold">{stats?.jurisprudencia_count ?? '...'}</span>
                    </div>
                    <div className="flex items-center justify-between">
                        <span className="text-surface-300 text-sm">Total Chunks (Vectores):</span>
                        <span className="font-mono font-bold text-[#D4AF37]">{stats?.total_chunks ?? '...'}</span>
                    </div>
                    <div className="pt-4 border-t border-white/10">
                        <p className="text-[10px] text-surface-400">Última actualización: Justo ahora</p>
                    </div>
                </div>

                {/* Upload Form */}
                <div className="card p-6 md:col-span-2 space-y-6">
                    <h3 className="font-bold text-surface-800 flex items-center gap-2">
                        <Upload size={18} className="text-primary-500" /> Ingestar Nuevo Documento Legal
                    </h3>

                    <div className="space-y-4">
                        <div>
                            <label className="text-sm font-medium text-surface-700 block mb-2">Tipo de Fuente</label>
                            <div className="grid grid-cols-2 gap-3">
                                <button
                                    onClick={() => setSourceType('ley')}
                                    className={`p-3 border rounded-xl flex items-center gap-3 transition-all ${sourceType === 'ley' ? 'bg-primary-50 border-primary-500 text-primary-700' : 'hover:bg-surface-50'
                                        }`}
                                >
                                    <Scale size={20} />
                                    <div className="text-left">
                                        <p className="text-sm font-bold">Ley / Decreto</p>
                                        <p className="text-[10px] opacity-70">Normativa vigente</p>
                                    </div>
                                </button>
                                <button
                                    onClick={() => setSourceType('jurisprudencia')}
                                    className={`p-3 border rounded-xl flex items-center gap-3 transition-all ${sourceType === 'jurisprudencia' ? 'bg-primary-50 border-primary-500 text-primary-700' : 'hover:bg-surface-50'
                                        }`}
                                >
                                    <FileText size={20} />
                                    <div className="text-left">
                                        <p className="text-sm font-bold">Jurisprudencia</p>
                                        <p className="text-[10px] opacity-70">Sentencias CSJ</p>
                                    </div>
                                </button>
                            </div>
                        </div>

                        <div className="border-2 border-dashed border-surface-200 rounded-2xl p-8 flex flex-col items-center justify-center text-center space-y-3 bg-surface-50/50 hover:bg-surface-50 transition-colors">
                            <input
                                type="file"
                                onChange={handleFileChange}
                                className="hidden"
                                id="doc-upload"
                                accept=".pdf,.txt"
                            />
                            <label htmlFor="doc-upload" className="cursor-pointer flex flex-col items-center">
                                <div className="w-12 h-12 bg-white rounded-full shadow-sm flex items-center justify-center text-surface-400 mb-2">
                                    <Upload size={24} />
                                </div>
                                <span className="text-sm font-medium text-surface-800">
                                    {file ? file.name : 'Haz clic para subir o arrastra un archivo PDF'}
                                </span>
                                <span className="text-xs text-surface-400 mt-1">Máximo 20MB (.pdf, .txt)</span>
                            </label>
                        </div>

                        <button
                            disabled={!file || status === 'uploading'}
                            onClick={handleUpload}
                            className="btn btn-primary w-full py-4 gap-2 text-lg"
                        >
                            {status === 'uploading' ? (
                                <>
                                    <Loader2 className="animate-spin" /> Procesando Chunks...
                                </>
                            ) : (
                                <>
                                    <Database size={20} /> Iniciar Ingesta Vectorial
                                </>
                            )}
                        </button>
                    </div>

                    {status === 'success' && (
                        <div className="animate-in fade-in slide-in-from-top-2 p-4 bg-green-50 border border-green-200 rounded-xl flex items-start gap-3">
                            <CheckCircle className="text-green-500 mt-1 flex-shrink-0" />
                            <div>
                                <p className="text-sm font-bold text-green-800">¡Ingesta completada!</p>
                                <p className="text-xs text-green-700">El documento ha sido fragmentado en {result?.chunks_created || 42} bloques vectoriales y está listo para consultas en modo Consultor.</p>
                            </div>
                        </div>
                    )}

                    {status === 'error' && (
                        <div className="animate-in fade-in slide-in-from-top-2 p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3">
                            <AlertCircle className="text-red-500 mt-1 flex-shrink-0" />
                            <div>
                                <p className="text-sm font-bold text-red-800">Error en la ingesta</p>
                                <p className="text-xs text-red-700">No se pudo procesar el archivo. Verifica el formato y tu conexión.</p>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            <div className="card p-6">
                <h4 className="font-bold text-surface-800 mb-4 flex items-center gap-2">
                    <Info size={18} className="text-accent-500" /> Notas sobre Seguridad y RAG
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm text-surface-600">
                    <div className="space-y-2">
                        <p className="font-semibold text-surface-800">Privacidad del Cliente</p>
                        <p>Los archivos subidos aquí son accesibles por todos los abogados del despacho pero NO se usan para entrenar modelos públicos.</p>
                    </div>
                    <div className="space-y-2">
                        <p className="font-semibold text-surface-800">Técnica de Fragmentación</p>
                        <p>Usamos un "Sliding Window" de 512 tokens con 10% de solapamiento para garantizar que el contexto legal no se pierda entre bloques.</p>
                    </div>
                </div>
            </div>
        </div>
    );
}
