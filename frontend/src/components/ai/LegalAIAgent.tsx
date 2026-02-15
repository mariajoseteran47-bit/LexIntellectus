'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, Settings, FileText, Scale, Zap, ShieldAlert, ChevronDown, Paperclip, X } from 'lucide-react';
import { aiService, AIMode, ChatMessage } from '@/services/aiService';

interface LegalAIAgentProps {
    expedienteId?: string;
    initialMode?: AIMode;
}

const LegalAIAgent: React.FC<LegalAIAgentProps> = ({ expedienteId, initialMode = 'consultor' }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [mode, setMode] = useState<AIMode>(initialMode);
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [sessionId, setSessionId] = useState<string | undefined>(undefined);

    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim() || isLoading) return;

        const userMsg: ChatMessage = { role: 'user', content: input };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setIsLoading(true);

        try {
            const response = await aiService.chat({
                message: input,
                mode: mode,
                session_id: sessionId,
                expediente_id: expedienteId
            });

            const botMsg: ChatMessage = {
                role: 'assistant',
                content: response.response,
                metadata: response.metadata
            };

            setMessages(prev => [...prev, botMsg]);
            if (response.session_id) setSessionId(response.session_id);
        } catch (error) {
            console.error('Error in LAA:', error);
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: 'Lo siento, ha ocurrido un error al procesar tu solicitud. Por favor intenta de nuevo.'
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    const getModeIcon = (m: AIMode) => {
        switch (m) {
            case 'consultor': return <Scale className="w-4 h-4" />;
            case 'estratega': return <Zap className="w-4 h-4" />;
            case 'redactor': return <FileText className="w-4 h-4" />;
            case 'cartulario': return <ShieldAlert className="w-4 h-4" />;
        }
    };

    const modes: { id: AIMode; label: string; desc: string }[] = [
        { id: 'consultor', label: 'Consultor', desc: 'Respuestas legales con citas exactas.' },
        { id: 'estratega', label: 'Estratega', desc: 'Análisis de expedientes y teoría del caso.' },
        { id: 'redactor', label: 'Redactor', desc: 'Generación de borradores jurídicos.' },
        { id: 'cartulario', label: 'Cartulario', desc: 'Validación notarial de escrituras.' },
    ];

    if (!isOpen) {
        return (
            <button
                onClick={() => setIsOpen(true)}
                className="fixed bottom-6 right-6 w-14 h-14 bg-[#1E3A5F] text-[#D4AF37] rounded-full shadow-2xl flex items-center justify-center hover:scale-110 transition-all duration-300 z-50 border-2 border-[#D4AF37]/50"
            >
                <Bot size={32} />
            </button>
        );
    }

    return (
        <div className="fixed bottom-6 right-6 w-[450px] h-[650px] bg-white rounded-2xl shadow-3xl flex flex-col z-50 border border-[#1E3A5F]/20 overflow-hidden animate-in slide-in-from-bottom-5 duration-300">
            {/* Header */}
            <div className="bg-[#1E3A5F] p-4 flex items-center justify-between text-white">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-white/10 rounded-lg flex items-center justify-center text-[#D4AF37]">
                        <Bot size={24} />
                    </div>
                    <div>
                        <h3 className="font-semibold text-sm">Legal AI Agent (LAA)</h3>
                        <p className="text-[10px] text-[#D4AF37]/80 uppercase tracking-widest font-mono">Socio Senior Digital</p>
                    </div>
                </div>
                <button onClick={() => setIsOpen(false)} className="hover:bg-white/10 p-1 rounded-md">
                    <X size={24} />
                </button>
            </div>

            {/* Mode Selector */}
            <div className="bg-[#1E3A5F]/5 p-2 grid grid-cols-4 gap-1 border-b">
                {modes.map((m) => (
                    <button
                        key={m.id}
                        onClick={() => setMode(m.id)}
                        title={m.desc}
                        className={`flex flex-col items-center p-2 rounded-xl transition-all ${mode === m.id
                                ? 'bg-white text-[#1E3A5F] shadow-sm border border-[#D4AF37]/30'
                                : 'text-gray-500 hover:bg-white/50'
                            }`}
                    >
                        {getModeIcon(m.id)}
                        <span className="text-[10px] font-medium mt-1">{m.label}</span>
                    </button>
                ))}
            </div>

            {/* Chat Area */}
            <div
                ref={scrollRef}
                className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50"
            >
                {messages.length === 0 && (
                    <div className="text-center py-10 px-6">
                        <Bot className="w-12 h-12 text-[#1E3A5F]/20 mx-auto mb-4" />
                        <h4 className="text-gray-800 font-medium mb-2">Bienvenido a LexIntellectus AI</h4>
                        <p className="text-sm text-gray-500">
                            Actualmente estoy en modo <strong>{modes.find(m => m.id === mode)?.label}</strong>.
                            {expedienteId ? ' Estoy analizando el expediente seleccionado.' : ' ¿En qué puedo ayudarte hoy?'}
                        </p>
                    </div>
                )}

                {messages.map((msg, i) => (
                    <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`flex gap-3 max-w-[85%] ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${msg.role === 'user' ? 'bg-[#D4AF37] text-white' : 'bg-[#1E3A5F] text-[#D4AF37]'
                                }`}>
                                {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
                            </div>
                            <div className={`p-3 rounded-2xl text-sm ${msg.role === 'user'
                                    ? 'bg-[#1E3A5F] text-white rounded-tr-none'
                                    : 'bg-white border rounded-tl-none text-gray-800 shadow-sm'
                                }`}>
                                {msg.content.split('\n').map((line, idx) => (
                                    <p key={idx} className={line === '' ? 'h-2' : ''}>{line}</p>
                                ))}
                            </div>
                        </div>
                    </div>
                ))}

                {isLoading && (
                    <div className="flex justify-start">
                        <div className="flex gap-3 bg-white p-3 rounded-2xl border shadow-sm rounded-tl-none">
                            <div className="flex gap-1">
                                <div className="w-1.5 h-1.5 bg-[#1E3A5F] rounded-full animate-bounce" />
                                <div className="w-1.5 h-1.5 bg-[#1E3A5F] rounded-full animate-bounce [animation-delay:-0.15s]" />
                                <div className="w-1.5 h-1.5 bg-[#1E3A5F] rounded-full animate-bounce [animation-delay:-0.3s]" />
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Input Area */}
            <div className="p-4 bg-white border-t">
                <div className="relative flex items-end gap-2 bg-gray-100 rounded-2xl p-2 focus-within:bg-white focus-within:ring-2 focus-within:ring-[#1E3A5F]/20 transition-all">
                    <textarea
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Haz una pregunta legal..."
                        rows={1}
                        className="flex-1 bg-transparent border-none focus:ring-0 resize-none py-2 px-2 text-sm max-h-32"
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault();
                                handleSend();
                            }
                        }}
                    />
                    <div className="flex flex-col gap-1 pb-1">
                        <button className="p-2 text-gray-400 hover:text-[#1E3A5F] transition-colors">
                            <Paperclip size={18} />
                        </button>
                        <button
                            disabled={!input.trim() || isLoading}
                            onClick={handleSend}
                            className={`p-2 rounded-xl transition-all ${input.trim() && !isLoading ? 'bg-[#1E3A5F] text-[#D4AF37]' : 'text-gray-300'
                                }`}
                        >
                            <Send size={18} />
                        </button>
                    </div>
                </div>
                <p className="text-[10px] text-center text-gray-400 mt-2 italic">
                    Las respuestas de la IA deben ser validadas por profesionales legales.
                </p>
            </div>
        </div>
    );
};

export default LegalAIAgent;
