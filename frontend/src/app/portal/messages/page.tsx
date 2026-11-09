'use client';

import { useState, useEffect } from 'react';

interface ThreadItem {
    id: string;
    expediente_id: string;
    numero_expediente: string;
    titulo: string;
    cerrado: boolean;
    total_mensajes: number;
    creado_por_nombre: string;
    created_at?: string;
    ultimo_mensaje_at?: string;
}

interface ThreadMessage {
    id: string;
    autor_id: string;
    autor_nombre: string;
    es_cliente: boolean;
    contenido: string;
    created_at?: string;
}

interface CaseBrief {
    id: string;
    numero_interno?: string;
    numero_causa?: string;
    tipo_servicio: string;
}

export default function PortalMessagesPage() {
    const [threads, setThreads] = useState<ThreadItem[]>([]);
    const [cases, setCases] = useState<CaseBrief[]>([]);
    const [selectedThread, setSelectedThread] = useState<ThreadItem | null>(null);
    const [messages, setMessages] = useState<ThreadMessage[]>([]);
    const [newMessage, setNewMessage] = useState('');
    const [loading, setLoading] = useState(true);
    const [sending, setSending] = useState(false);

    // New thread modal
    const [showNewModal, setShowNewModal] = useState(false);
    const [selectedCaseId, setSelectedCaseId] = useState('');
    const [newTitle, setNewTitle] = useState('');
    const [initialMessage, setInitialMessage] = useState('');

    const getAuthHeaders = () => {
        const token = localStorage.getItem('access_token');
        const userStr = localStorage.getItem('user');
        const user = userStr ? JSON.parse(userStr) : {};
        return {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
            'X-Tenant-ID': user.tenant_id || ''
        };
    };

    const fetchThreadsAndCases = async () => {
        try {
            const headers = getAuthHeaders();
            const [threadsRes, casesRes] = await Promise.all([
                fetch('/api/v1/portal/threads', { headers }),
                fetch('/api/v1/portal/cases?size=50', { headers })
            ]);
            if (threadsRes.ok) {
                const tData = await threadsRes.json();
                const list = tData.items || [];
                setThreads(list);
                if (list.length > 0 && !selectedThread) {
                    setSelectedThread(list[0]);
                }
            }
            if (casesRes.ok) {
                const cData = await casesRes.json();
                const cList = cData.items || [];
                setCases(cList);
                if (cList.length > 0 && !selectedCaseId) {
                    setSelectedCaseId(cList[0].id);
                }
            }
        } catch (err) {
            console.error('Error loading portal threads:', err);
        } finally {
            setLoading(false);
        }
    };

    const fetchMessages = async (threadId: string) => {
        try {
            const res = await fetch(`/api/v1/portal/threads/${threadId}/messages`, {
                headers: getAuthHeaders()
            });
            if (res.ok) {
                const data = await res.json();
                setMessages(data.messages || []);
            }
        } catch (err) {
            console.error('Error loading messages:', err);
        }
    };

    useEffect(() => {
        fetchThreadsAndCases();
    }, []);

    useEffect(() => {
        if (selectedThread) {
            fetchMessages(selectedThread.id);
        }
    }, [selectedThread]);

    const handleSendMessage = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedThread || !newMessage.trim()) return;
        setSending(true);
        try {
            const res = await fetch(`/api/v1/portal/threads/${selectedThread.id}/messages`, {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({ contenido: newMessage.trim() })
            });
            if (res.ok) {
                setNewMessage('');
                await fetchMessages(selectedThread.id);
                await fetchThreadsAndCases();
            }
        } catch (err) {
            console.error('Error sending message:', err);
        } finally {
            setSending(false);
        }
    };

    const handleCreateThread = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedCaseId || !newTitle.trim() || !initialMessage.trim()) return;
        setSending(true);
        try {
            const res = await fetch('/api/v1/portal/threads', {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({
                    expediente_id: selectedCaseId,
                    titulo: newTitle.trim(),
                    mensaje_inicial: initialMessage.trim()
                })
            });
            if (res.ok) {
                const created = await res.json();
                setShowNewModal(false);
                setNewTitle('');
                setInitialMessage('');
                await fetchThreadsAndCases();
                setSelectedThread({
                    id: created.id,
                    expediente_id: created.expediente_id,
                    numero_expediente: 'Consulta Reciente',
                    titulo: created.titulo,
                    cerrado: false,
                    total_mensajes: 1,
                    creado_por_nombre: 'Yo'
                });
            }
        } catch (err) {
            console.error('Error creating thread:', err);
        } finally {
            setSending(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[60vh]">
                <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-amber-500"></div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-extrabold text-white tracking-tight">Consultas con Mi Abogado</h1>
                    <p className="text-slate-400 text-sm mt-1">
                        Canal directo y cifrado de comunicación sobre sus expedientes y trámites activos.
                    </p>
                </div>
                <button
                    onClick={() => setShowNewModal(true)}
                    className="px-5 py-2.5 bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold rounded-xl shadow-lg transition-all"
                >
                    + Nueva Consulta Legal
                </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 min-h-[540px]">
                {/* Threads List */}
                <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-4 space-y-3 overflow-y-auto max-h-[600px]">
                    <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 px-2">
                        Conversaciones ({threads.length})
                    </h2>
                    {threads.length === 0 ? (
                        <div className="text-center py-12 px-4 space-y-2">
                            <div className="text-3xl">💬</div>
                            <p className="text-sm text-slate-400">Aún no ha iniciado consultas con su abogado.</p>
                        </div>
                    ) : (
                        threads.map((t) => (
                            <button
                                key={t.id}
                                onClick={() => setSelectedThread(t)}
                                className={`w-full text-left p-4 rounded-xl border transition-all ${
                                    selectedThread?.id === t.id
                                        ? 'bg-amber-500/10 border-amber-500/40 text-white'
                                        : 'bg-slate-950/40 border-slate-800/60 text-slate-300 hover:bg-slate-800/50'
                                }`}
                            >
                                <div className="flex items-center justify-between gap-2">
                                    <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-slate-800 text-amber-400">
                                        {t.numero_expediente}
                                    </span>
                                    <span className="text-[11px] text-slate-500">{t.total_mensajes} msj</span>
                                </div>
                                <h3 className="font-bold text-sm mt-2 truncate">{t.titulo}</h3>
                            </button>
                        ))
                    )}
                </div>

                {/* Active Conversation */}
                <div className="lg:col-span-2 bg-slate-900/60 border border-slate-800/80 rounded-2xl flex flex-col overflow-hidden">
                    {!selectedThread ? (
                        <div className="flex-1 flex flex-col items-center justify-center p-12 text-center">
                            <span className="text-5xl mb-3">📨</span>
                            <h3 className="text-lg font-bold text-white">Seleccione o inicie una conversación</h3>
                            <p className="text-sm text-slate-400 mt-1">
                                Sus mensajes quedarán vinculados directamente al expediente correspondiente.
                            </p>
                        </div>
                    ) : (
                        <>
                            <div className="p-4 border-b border-slate-800/80 bg-slate-950/50 flex items-center justify-between">
                                <div>
                                    <h3 className="font-bold text-white">{selectedThread.titulo}</h3>
                                    <p className="text-xs text-amber-400">{selectedThread.numero_expediente}</p>
                                </div>
                                <span className={`text-[10px] font-bold uppercase px-2.5 py-1 rounded-full ${
                                    selectedThread.cerrado ? 'bg-slate-800 text-slate-400' : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                }`}>
                                    {selectedThread.cerrado ? 'Cerrado' : 'Canal Activo'}
                                </span>
                            </div>

                            <div className="flex-1 p-6 space-y-4 overflow-y-auto max-h-[420px]">
                                {messages.map((m) => (
                                    <div
                                        key={m.id}
                                        className={`flex flex-col max-w-[80%] ${
                                            m.es_cliente ? 'ml-auto items-end' : 'mr-auto items-start'
                                        }`}
                                    >
                                        <span className="text-[11px] text-slate-400 mb-1 px-1">
                                            {m.autor_nombre} {m.created_at ? `• ${new Date(m.created_at).toLocaleString('es-NI')}` : ''}
                                        </span>
                                        <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                                            m.es_cliente
                                                ? 'bg-amber-500 text-slate-950 font-medium rounded-br-xs'
                                                : 'bg-slate-800 text-slate-100 border border-slate-700 rounded-bl-xs'
                                        }`}>
                                            {m.contenido}
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {!selectedThread.cerrado && (
                                <form onSubmit={handleSendMessage} className="p-4 border-t border-slate-800/80 bg-slate-950/40 flex gap-3">
                                    <input
                                        type="text"
                                        placeholder="Escriba su mensaje o consulta para su abogado..."
                                        value={newMessage}
                                        onChange={(e) => setNewMessage(e.target.value)}
                                        className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-amber-500"
                                    />
                                    <button
                                        type="submit"
                                        disabled={sending || !newMessage.trim()}
                                        className="px-5 py-2.5 bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold rounded-xl disabled:opacity-50"
                                    >
                                        Enviar
                                    </button>
                                </form>
                            )}
                        </>
                    )}
                </div>
            </div>

            {/* Modal Nueva Consulta */}
            {showNewModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-xs">
                    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 max-w-md w-full space-y-4 shadow-2xl">
                        <h3 className="text-lg font-bold text-white">Nueva Consulta al Abogado</h3>
                        <form onSubmit={handleCreateThread} className="space-y-4">
                            <div>
                                <label className="block text-xs font-semibold text-slate-400 mb-1">Expediente Relacionado *</label>
                                <select
                                    required
                                    value={selectedCaseId}
                                    onChange={(e) => setSelectedCaseId(e.target.value)}
                                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2.5 text-sm text-white"
                                >
                                    {cases.map((c) => (
                                        <option key={c.id} value={c.id}>
                                            {c.numero_interno || c.numero_causa || 'Expediente'} ({c.tipo_servicio})
                                        </option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="block text-xs font-semibold text-slate-400 mb-1">Asunto de la Consulta *</label>
                                <input
                                    type="text"
                                    required
                                    placeholder="Ej. Dudas sobre próxima audiencia o revisión de cláusula"
                                    value={newTitle}
                                    onChange={(e) => setNewTitle(e.target.value)}
                                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2.5 text-sm text-white"
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-semibold text-slate-400 mb-1">Mensaje *</label>
                                <textarea
                                    required
                                    rows={4}
                                    placeholder="Detalle su consulta..."
                                    value={initialMessage}
                                    onChange={(e) => setInitialMessage(e.target.value)}
                                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2.5 text-sm text-white"
                                />
                            </div>
                            <div className="flex justify-end gap-2 pt-2">
                                <button
                                    type="button"
                                    onClick={() => setShowNewModal(false)}
                                    className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-bold"
                                >
                                    Cancelar
                                </button>
                                <button
                                    type="submit"
                                    disabled={sending || !selectedCaseId}
                                    className="px-5 py-2 rounded-xl bg-amber-500 text-slate-950 text-xs font-bold"
                                >
                                    {sending ? 'Enviando...' : 'Iniciar Consulta'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
