'use client';

import { useState } from 'react';
import { AlertTriangle, CheckCircle, Search, Loader2, Shield, ExternalLink } from 'lucide-react';
import api from '@/lib/api';

interface ConflictMatch {
    tabla: string; id: string; nombre: string;
    caso_id?: string; caso_titulo?: string; similitud: number;
}

interface ConflictCheckProps {
    onResult?: (hasConflict: boolean) => void;
}

export default function ConflictCheckAlert({ onResult }: ConflictCheckProps) {
    const [nombre, setNombre] = useState('');
    const [documento, setDocumento] = useState('');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<{
        tiene_conflicto: boolean; coincidencias: ConflictMatch[]; total: number;
    } | null>(null);
    const [checked, setChecked] = useState(false);

    const handleCheck = async () => {
        if (!nombre.trim()) return;
        setLoading(true);
        try {
            const { data } = await api.post('/conflict-check', {
                nombre: nombre.trim(),
                documento: documento.trim() || null,
            });
            setResult({
                tiene_conflicto: data.tiene_conflicto,
                coincidencias: data.coincidencias,
                total: data.total_coincidencias,
            });
            setChecked(true);
            onResult?.(data.tiene_conflicto);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="card border-2 border-surface-200 overflow-hidden">
            <div className="px-4 py-3 bg-surface-800 text-white flex items-center gap-2">
                <Shield className="w-4 h-4 text-amber-400" />
                <span className="font-bold text-sm">Verificación de Conflicto de Interés</span>
            </div>

            <div className="p-4 space-y-3">
                <p className="text-sm text-surface-500">
                    Busque si la persona o entidad ya aparece en otros asuntos del despacho antes de crear el caso.
                </p>

                <div className="flex gap-2">
                    <input type="text" className="input flex-1" placeholder="Nombre de la parte..."
                        value={nombre} onChange={e => { setNombre(e.target.value); setChecked(false); setResult(null); }} />
                    <input type="text" className="input w-40" placeholder="Cédula/RUC (opc.)"
                        value={documento} onChange={e => setDocumento(e.target.value)} />
                    <button onClick={handleCheck} disabled={!nombre.trim() || loading}
                        className="btn btn-primary px-4 disabled:opacity-50">
                        {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                    </button>
                </div>

                {/* Results */}
                {checked && result && (
                    <div className={`rounded-lg p-4 ${
                        result.tiene_conflicto
                            ? 'bg-red-50 border border-red-200'
                            : 'bg-green-50 border border-green-200'
                    }`}>
                        {result.tiene_conflicto ? (
                            <>
                                <div className="flex items-center gap-2 mb-3">
                                    <AlertTriangle className="w-5 h-5 text-red-600" />
                                    <span className="font-bold text-red-800">
                                        ⚠️ Se encontraron {result.total} coincidencia(s) potencial(es)
                                    </span>
                                </div>
                                <div className="space-y-2">
                                    {result.coincidencias.map((m, i) => (
                                        <div key={i} className="flex items-center justify-between bg-white rounded p-3 border border-red-100">
                                            <div>
                                                <span className="font-medium text-surface-800">{m.nombre}</span>
                                                <span className="text-xs ml-2 text-surface-400">({m.tabla.replace('_', ' ')})</span>
                                                {m.caso_titulo && (
                                                    <p className="text-xs text-surface-500 mt-0.5">
                                                        📁 Caso: {m.caso_titulo}
                                                    </p>
                                                )}
                                            </div>
                                            <div className="text-right">
                                                <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                                                    m.similitud >= 0.8 ? 'bg-red-200 text-red-800' :
                                                    m.similitud >= 0.5 ? 'bg-amber-200 text-amber-800' :
                                                    'bg-surface-200 text-surface-600'
                                                }`}>
                                                    {Math.round(m.similitud * 100)}% similar
                                                </span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                                <p className="text-xs text-red-600 mt-3">
                                    Revise las coincidencias antes de continuar. Si procede, documente la resolución del conflicto.
                                </p>
                            </>
                        ) : (
                            <div className="flex items-center gap-2">
                                <CheckCircle className="w-5 h-5 text-green-600" />
                                <span className="font-medium text-green-800">
                                    ✅ Sin conflictos detectados para "{nombre}"
                                </span>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
