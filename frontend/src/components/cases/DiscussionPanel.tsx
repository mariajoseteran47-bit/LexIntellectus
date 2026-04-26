'use client';

import { useState, useEffect, useRef } from 'react';
import {
    MessageSquare, Plus, Send, Pin, Lock, Globe, X,
    Check, Edit3, Trash2, User, Paperclip, Hash
} from 'lucide-react';
import api from '@/lib/api';
import { useToast } from '@/components/ui/ToastProvider';

interface Thread {
    id: string; titulo: string; tipo_canal: string; cerrado: boolean;
    fijado: boolean; creado_por_id: string; creado_por_nombre?: string;
    total_mensajes: number; ultimo_mensaje_at?: string; created_at: string;
}

interface Message {
    id: string; hilo_id: string; autor_id: string; autor_nombre?: string;
    contenido: string; adjuntos: string[]; menciones: string[];
    es_resolucion: boolean; editado: boolean; created_at: string;
}

export default function DiscussionPanel({ caseId }: { caseId: string }) {
    const [threads, setThreads] = useState<Thread[]>([]);
    const [activeThread, setActiveThread] = useState<Thread | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [loadingThreads, setLoadingThreads] = useState(true);
    const [loadingMessages, setLoadingMessages] = useState(false);

    // New thread/message state
    const [showNewThread, setShowNewThread] = useState(false);
    const [newTitle, setNewTitle] = useState('');
    const [newChannel, setNewChannel] = useState('interno');
    const [newMessage, setNewMessage] = useState('');
    const [sending, setSending] = useState(false);

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const toast = useToast();

    useEffect(() => { loadThreads(); }, [caseId]);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const loadThreads = async () => {
        setLoadingThreads(true);
        try {
            const { data } = await api.get(`/cases/${caseId}/threads`);
            setThreads(data.items || []);
        } catch (e) { console.error(e); }
        finally { setLoadingThreads(false); }
    };

    const loadMessages = async (threadId: string) => {
        setLoadingMessages(true);
        try {
            const { data } = await api.get(`/threads/${threadId}/messages`);
            setMessages(data || []);
        } catch (e) { console.error(e); }
        finally { setLoadingMessages(false); }
    };

    const handleSelectThread = (thread: Thread) => {
        setActiveThread(thread);
        loadMessages(thread.id);
    };

    const handleCreateThread = async () => {
        if (!newTitle.trim()) return;
        try {
            const { data } = await api.post(`/cases/${caseId}/threads`, {
                expediente_id: caseId,
                titulo: newTitle,
                tipo_canal: newChannel,
            });
            setThreads(prev => [data, ...prev]);
            setActiveThread(data);
            setMessages([]);
            setShowNewThread(false);
            setNewTitle('');
            toast.success('Hilo creado');
        } catch (e) { toast.error('Error al crear hilo'); }
    };

    const handleSendMessage = async () => {
        if (!newMessage.trim() || !activeThread) return;
        setSending(true);
        try {
            const { data } = await api.post(`/threads/${activeThread.id}/messages`, {
                contenido: newMessage,
            });
            setMessages(prev => [...prev, data]);
            setNewMessage('');
            // Update thread counter
            setThreads(prev => prev.map(t =>
                t.id === activeThread.id
                    ? { ...t, total_mensajes: t.total_mensajes + 1, ultimo_mensaje_at: new Date().toISOString() }
                    : t
            ));
        } catch (e) { toast.error('Error al enviar mensaje'); }
        finally { setSending(false); }
    };

    const handleCloseThread = async () => {
        if (!activeThread) return;
        try {
            await api.patch(`/threads/${activeThread.id}`, { cerrado: !activeThread.cerrado });
            setActiveThread({ ...activeThread, cerrado: !activeThread.cerrado });
            setThreads(prev => prev.map(t =>
                t.id === activeThread.id ? { ...t, cerrado: !activeThread.cerrado } : t
            ));
            toast.success(activeThread.cerrado ? 'Hilo reabierto' : 'Hilo cerrado');
        } catch (e) { toast.error('Error'); }
    };

    const handlePinThread = async () => {
        if (!activeThread) return;
        try {
            await api.patch(`/threads/${activeThread.id}`, { fijado: !activeThread.fijado });
            setActiveThread({ ...activeThread, fijado: !activeThread.fijado });
            setThreads(prev => prev.map(t =>
                t.id === activeThread.id ? { ...t, fijado: !activeThread.fijado } : t
            ));
        } catch (e) { toast.error('Error'); }
    };

    return (
        <div className="flex h-[600px] rounded-xl overflow-hidden border border-surface-200 shadow-sm bg-white">
            {/* === Left: Thread list === */}
            <div className="w-80 border-r border-surface-200 flex flex-col bg-surface-50 shrink-0">
                <div className="p-3 border-b border-surface-200">
                    <div className="flex items-center justify-between mb-2">
                        <h3 className="font-bold text-surface-800 text-sm">Discusiones</h3>
                        <button onClick={() => setShowNewThread(true)}
                            className="btn btn-sm btn-primary p-1.5 rounded-lg">
                            <Plus className="w-4 h-4" />
                        </button>
                    </div>

                    {showNewThread && (
                        <div className="space-y-2 p-2 bg-white rounded-lg border border-primary-200 mb-2">
                            <input type="text" className="input w-full text-sm" placeholder="Título del hilo..."
                                value={newTitle} onChange={e => setNewTitle(e.target.value)}
                                onKeyDown={e => e.key === 'Enter' && handleCreateThread()} autoFocus />
                            <div className="flex gap-2">
                                <select className="input flex-1 text-xs" value={newChannel} onChange={e => setNewChannel(e.target.value)}>
                                    <option value="interno">🔒 Interno</option>
                                    <option value="cliente">🌐 Cliente</option>
                                </select>
                                <button onClick={handleCreateThread} className="btn btn-sm btn-primary text-xs px-3">Crear</button>
                                <button onClick={() => setShowNewThread(false)} className="btn btn-sm btn-ghost text-xs px-2">
                                    <X className="w-3 h-3" />
                                </button>
                            </div>
                        </div>
                    )}
                </div>

                <div className="flex-1 overflow-y-auto">
                    {loadingThreads ? (
                        <div className="p-4 text-center text-sm text-surface-400">Cargando...</div>
                    ) : threads.length === 0 ? (
                        <div className="p-6 text-center text-sm text-surface-400">
                            <MessageSquare className="w-8 h-8 mx-auto mb-2 text-surface-300" />
                            <p>Sin discusiones aún</p>
                            <button onClick={() => setShowNewThread(true)} className="btn btn-sm btn-outline mt-2 text-xs">
                                <Plus className="w-3 h-3 mr-1" /> Crear primera
                            </button>
                        </div>
                    ) : (
                        threads.map(t => (
                            <button key={t.id}
                                onClick={() => handleSelectThread(t)}
                                className={`w-full text-left p-3 border-b border-surface-100 hover:bg-white transition-colors ${
                                    activeThread?.id === t.id ? 'bg-white border-l-2 border-l-primary-500' : ''
                                }`}>
                                <div className="flex items-start gap-2">
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-1.5">
                                            {t.fijado && <Pin className="w-3 h-3 text-amber-500 shrink-0" />}
                                            {t.tipo_canal === 'interno' ?
                                                <Lock className="w-3 h-3 text-surface-400 shrink-0" /> :
                                                <Globe className="w-3 h-3 text-blue-400 shrink-0" />
                                            }
                                            <span className={`font-medium text-sm truncate ${t.cerrado ? 'text-surface-400 line-through' : 'text-surface-800'}`}>
                                                {t.titulo}
                                            </span>
                                        </div>
                                        <div className="flex items-center gap-2 mt-1 text-xs text-surface-400">
                                            <span>{t.creado_por_nombre || 'Usuario'}</span>
                                            <span>·</span>
                                            <span>{t.total_mensajes} msg</span>
                                        </div>
                                    </div>
                                </div>
                            </button>
                        ))
                    )}
                </div>
            </div>

            {/* === Right: Message area === */}
            <div className="flex-1 flex flex-col">
                {!activeThread ? (
                    <div className="flex-1 flex items-center justify-center text-surface-400">
                        <div className="text-center">
                            <Hash className="w-12 h-12 mx-auto mb-3 text-surface-200" />
                            <p className="font-medium">Seleccione un hilo de discusión</p>
                            <p className="text-sm mt-1">o cree uno nuevo desde el panel izquierdo</p>
                        </div>
                    </div>
                ) : (
                    <>
                        {/* Thread header */}
                        <div className="px-4 py-3 border-b border-surface-200 flex items-center justify-between bg-surface-50/50">
                            <div className="flex items-center gap-2 min-w-0">
                                {activeThread.tipo_canal === 'interno' ?
                                    <Lock className="w-4 h-4 text-amber-500 shrink-0" /> :
                                    <Globe className="w-4 h-4 text-blue-500 shrink-0" />
                                }
                                <h3 className="font-semibold text-surface-800 truncate">{activeThread.titulo}</h3>
                                {activeThread.cerrado && (
                                    <span className="badge bg-surface-100 text-surface-500 text-[10px]">CERRADO</span>
                                )}
                            </div>
                            <div className="flex gap-1 shrink-0">
                                <button onClick={handlePinThread} title={activeThread.fijado ? 'Desfijar' : 'Fijar'}
                                    className={`btn btn-ghost p-1.5 ${activeThread.fijado ? 'text-amber-500' : 'text-surface-400'}`}>
                                    <Pin className="w-4 h-4" />
                                </button>
                                <button onClick={handleCloseThread}
                                    className="btn btn-ghost p-1.5 text-surface-400 hover:text-surface-700">
                                    {activeThread.cerrado ? <MessageSquare className="w-4 h-4" /> : <Check className="w-4 h-4" />}
                                </button>
                            </div>
                        </div>

                        {/* Messages */}
                        <div className="flex-1 overflow-y-auto p-4 space-y-4">
                            {loadingMessages ? (
                                <div className="text-center text-sm text-surface-400 py-8">Cargando mensajes...</div>
                            ) : messages.length === 0 ? (
                                <div className="text-center text-sm text-surface-400 py-8">
                                    <MessageSquare className="w-8 h-8 mx-auto mb-2 text-surface-200" />
                                    <p>Sin mensajes aún. ¡Comience la discusión!</p>
                                </div>
                            ) : (
                                messages.map(msg => (
                                    <div key={msg.id} className={`flex gap-3 ${msg.es_resolucion ? 'bg-green-50 rounded-lg p-3 border border-green-200' : ''}`}>
                                        <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center shrink-0">
                                            <User className="w-4 h-4 text-primary-600" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2 flex-wrap">
                                                <span className="font-semibold text-sm text-surface-800">{msg.autor_nombre || 'Usuario'}</span>
                                                <span className="text-[10px] text-surface-400">
                                                    {new Date(msg.created_at).toLocaleString('es-NI', { dateStyle: 'short', timeStyle: 'short' })}
                                                </span>
                                                {msg.editado && <span className="text-[10px] text-surface-400 italic">(editado)</span>}
                                                {msg.es_resolucion && (
                                                    <span className="badge bg-green-100 text-green-700 text-[10px]">✅ RESOLUCIÓN</span>
                                                )}
                                            </div>
                                            <p className="text-sm text-surface-700 mt-1 whitespace-pre-wrap leading-relaxed">
                                                {msg.contenido}
                                            </p>
                                            {msg.adjuntos && msg.adjuntos.length > 0 && (
                                                <div className="flex gap-1 mt-2">
                                                    {msg.adjuntos.map((a, i) => (
                                                        <span key={i} className="badge bg-surface-100 text-surface-600 text-[10px] gap-1">
                                                            <Paperclip className="w-3 h-3" /> Adjunto {i + 1}
                                                        </span>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ))
                            )}
                            <div ref={messagesEndRef} />
                        </div>

                        {/* Message input */}
                        {!activeThread.cerrado && (
                            <div className="p-3 border-t border-surface-200 bg-surface-50/50">
                                <div className="flex gap-2">
                                    <input
                                        type="text"
                                        className="input flex-1"
                                        placeholder="Escriba su mensaje..."
                                        value={newMessage}
                                        onChange={e => setNewMessage(e.target.value)}
                                        onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSendMessage()}
                                    />
                                    <button
                                        onClick={handleSendMessage}
                                        disabled={!newMessage.trim() || sending}
                                        className="btn btn-primary px-4 disabled:opacity-50"
                                    >
                                        <Send className="w-4 h-4" />
                                    </button>
                                </div>
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
}
