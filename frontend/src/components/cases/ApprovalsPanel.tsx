'use client';

import { useState, useEffect } from 'react';
import { CheckCircle, XCircle, Clock, FileText, User, AlertTriangle, Loader2 } from 'lucide-react';
import api from '@/lib/api';
import { useToast } from '@/components/ui/ToastProvider';

interface Approval {
    id: string; documento_id: string; expediente_id?: string;
    solicitante_id: string; solicitante_nombre?: string;
    aprobador_id: string; aprobador_nombre?: string;
    estado: string; motivo_solicitud?: string;
    comentarios_aprobador?: string; version_documento: number;
    fecha_solicitud: string; fecha_respuesta?: string;
    fecha_limite?: string; created_at: string;
}

interface ApprovalsPanelProps {
    rol?: 'aprobador' | 'solicitante' | 'todos';
}

const STATUS_CONFIG: Record<string, { icon: typeof Clock; color: string; label: string }> = {
    pendiente: { icon: Clock, color: 'bg-amber-100 text-amber-700', label: 'Pendiente' },
    aprobado: { icon: CheckCircle, color: 'bg-green-100 text-green-700', label: 'Aprobado' },
    rechazado: { icon: XCircle, color: 'bg-red-100 text-red-700', label: 'Rechazado' },
    revision: { icon: AlertTriangle, color: 'bg-blue-100 text-blue-700', label: 'En Revisión' },
};

export default function ApprovalsPanel({ rol = 'aprobador' }: ApprovalsPanelProps) {
    const [approvals, setApprovals] = useState<Approval[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('pendiente');
    const [actionLoading, setActionLoading] = useState<string | null>(null);
    const [commentModal, setCommentModal] = useState<{ id: string; action: string } | null>(null);
    const [comment, setComment] = useState('');
    const toast = useToast();

    useEffect(() => { loadApprovals(); }, [filter, rol]);

    const loadApprovals = async () => {
        setLoading(true);
        try {
            const params = new URLSearchParams({ rol });
            if (filter) params.append('estado', filter);
            const { data } = await api.get(`/approvals?${params.toString()}`);
            setApprovals(data.items || []);
        } catch (e) { console.error(e); }
        finally { setLoading(false); }
    };

    const handleAction = async (approvalId: string, estado: string) => {
        setActionLoading(approvalId);
        try {
            await api.patch(`/approvals/${approvalId}`, {
                estado,
                comentarios_aprobador: comment || null,
            });
            toast.success(estado === 'aprobado' ? 'Documento aprobado' : estado === 'rechazado' ? 'Documento rechazado' : 'Revisión solicitada');
            setCommentModal(null);
            setComment('');
            loadApprovals();
        } catch (e: any) {
            toast.error(e?.response?.data?.detail || 'Error al procesar');
        } finally {
            setActionLoading(null);
        }
    };

    const isOverdue = (a: Approval) => a.fecha_limite && new Date(a.fecha_limite) < new Date() && a.estado === 'pendiente';

    return (
        <div className="space-y-4">
            {/* Header & Filters */}
            <div className="flex items-center justify-between flex-wrap gap-3">
                <h3 className="font-bold text-surface-800 flex items-center gap-2">
                    <FileText className="w-5 h-5 text-primary-500" /> Aprobaciones de Documentos
                </h3>
                <div className="flex gap-1">
                    {Object.entries(STATUS_CONFIG).map(([key, cfg]) => (
                        <button key={key} onClick={() => setFilter(key)}
                            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                                filter === key ? cfg.color + ' ring-1 ring-current' : 'bg-surface-50 text-surface-500 hover:bg-surface-100'
                            }`}>
                            {cfg.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Approvals List */}
            {loading ? (
                <div className="text-center py-8 text-surface-400">Cargando aprobaciones...</div>
            ) : approvals.length === 0 ? (
                <div className="card p-8 text-center">
                    <CheckCircle className="w-10 h-10 mx-auto text-surface-200 mb-3" />
                    <p className="text-surface-500 font-medium">No hay aprobaciones {filter === 'pendiente' ? 'pendientes' : ''}</p>
                </div>
            ) : (
                <div className="space-y-3">
                    {approvals.map(a => {
                        const cfg = STATUS_CONFIG[a.estado] || STATUS_CONFIG.pendiente;
                        const StatusIcon = cfg.icon;
                        return (
                            <div key={a.id} className={`card p-4 ${isOverdue(a) ? 'border-l-4 border-l-red-500' : ''}`}>
                                <div className="flex items-start justify-between gap-4">
                                    <div className="flex items-start gap-3 flex-1">
                                        <div className={`p-2 rounded-lg ${cfg.color}`}>
                                            <StatusIcon className="w-4 h-4" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2 flex-wrap mb-1">
                                                <span className={`badge text-[10px] font-bold ${cfg.color}`}>{cfg.label}</span>
                                                {isOverdue(a) && (
                                                    <span className="badge bg-red-100 text-red-700 text-[10px] animate-pulse">VENCIDO</span>
                                                )}
                                                <span className="text-xs text-surface-400">v{a.version_documento}</span>
                                            </div>
                                            {a.motivo_solicitud && (
                                                <p className="text-sm text-surface-700 mb-1">{a.motivo_solicitud}</p>
                                            )}
                                            <div className="flex items-center gap-3 text-xs text-surface-500">
                                                <span className="flex items-center gap-1">
                                                    <User className="w-3 h-3" /> {a.solicitante_nombre || 'Solicitante'}
                                                </span>
                                                <span>→</span>
                                                <span className="flex items-center gap-1">
                                                    <User className="w-3 h-3" /> {a.aprobador_nombre || 'Aprobador'}
                                                </span>
                                                <span>·</span>
                                                <span>{new Date(a.fecha_solicitud).toLocaleDateString('es-NI')}</span>
                                                {a.fecha_limite && (
                                                    <>
                                                        <span>·</span>
                                                        <span className={isOverdue(a) ? 'text-red-600 font-bold' : ''}>
                                                            Límite: {new Date(a.fecha_limite).toLocaleDateString('es-NI')}
                                                        </span>
                                                    </>
                                                )}
                                            </div>
                                            {a.comentarios_aprobador && (
                                                <div className="mt-2 text-sm bg-surface-50 rounded p-2 text-surface-600 border-l-2 border-surface-300">
                                                    💬 {a.comentarios_aprobador}
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    {/* Actions (only for pending and user is approver) */}
                                    {a.estado === 'pendiente' && (
                                        <div className="flex gap-1 shrink-0">
                                            <button
                                                onClick={() => setCommentModal({ id: a.id, action: 'aprobado' })}
                                                disabled={actionLoading === a.id}
                                                className="btn btn-sm bg-green-50 text-green-700 hover:bg-green-100 p-2"
                                                title="Aprobar"
                                            >
                                                {actionLoading === a.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
                                            </button>
                                            <button
                                                onClick={() => setCommentModal({ id: a.id, action: 'revision' })}
                                                className="btn btn-sm bg-blue-50 text-blue-700 hover:bg-blue-100 p-2"
                                                title="Solicitar revisión"
                                            >
                                                <AlertTriangle className="w-4 h-4" />
                                            </button>
                                            <button
                                                onClick={() => setCommentModal({ id: a.id, action: 'rechazado' })}
                                                className="btn btn-sm bg-red-50 text-red-700 hover:bg-red-100 p-2"
                                                title="Rechazar"
                                            >
                                                <XCircle className="w-4 h-4" />
                                            </button>
                                        </div>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}

            {/* Comment Modal */}
            {commentModal && (
                <>
                    <div className="fixed inset-0 bg-black/40 z-40" onClick={() => { setCommentModal(null); setComment(''); }} />
                    <div className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-md bg-white rounded-2xl shadow-2xl p-6 space-y-4">
                        <h4 className="font-bold text-surface-800">
                            {commentModal.action === 'aprobado' ? '✅ Aprobar Documento' :
                             commentModal.action === 'rechazado' ? '❌ Rechazar Documento' : '🔄 Solicitar Revisión'}
                        </h4>
                        <textarea
                            className="input w-full"
                            rows={3}
                            placeholder="Comentarios (opcional)..."
                            value={comment}
                            onChange={e => setComment(e.target.value)}
                        />
                        <div className="flex justify-end gap-2">
                            <button onClick={() => { setCommentModal(null); setComment(''); }} className="btn btn-outline">Cancelar</button>
                            <button
                                onClick={() => handleAction(commentModal.id, commentModal.action)}
                                className={`btn ${
                                    commentModal.action === 'aprobado' ? 'bg-green-600 text-white hover:bg-green-700' :
                                    commentModal.action === 'rechazado' ? 'bg-red-600 text-white hover:bg-red-700' :
                                    'btn-primary'
                                }`}
                            >
                                Confirmar
                            </button>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}
