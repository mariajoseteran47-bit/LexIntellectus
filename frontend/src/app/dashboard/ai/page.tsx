'use client';

import LegalAIAgent from '@/components/ai/LegalAIAgent';
import { Bot, Scale, Zap, FileText, ShieldAlert } from 'lucide-react';

export default function AIAssistantPage() {
    return (
        <div className="space-y-6 animate-fade-in">
            {/* Header */}
            <div className="flex flex-col gap-2">
                <h1 className="text-2xl font-bold text-surface-900 flex items-center gap-3">
                    <Bot className="text-[#D4AF37]" /> Asistente Legal con IA (LAA)
                </h1>
                <p className="text-surface-600">
                    Tu socio senior digital. Consulta leyes, analiza expedientes, redacta documentos y valida escrituras notariales.
                </p>
            </div>

            {/* Modes Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {[
                    {
                        icon: <Scale className="w-6 h-6" />,
                        title: 'Consultor',
                        desc: 'Respuestas legales con citas exactas del Digesto Jurídico y jurisprudencia de la CSJ.',
                        color: 'bg-blue-50 text-blue-600 border-blue-200',
                    },
                    {
                        icon: <Zap className="w-6 h-6" />,
                        title: 'Estratega',
                        desc: 'Análisis estratégico de expedientes, teoría del caso y recomendaciones tácticas.',
                        color: 'bg-amber-50 text-amber-600 border-amber-200',
                    },
                    {
                        icon: <FileText className="w-6 h-6" />,
                        title: 'Redactor',
                        desc: 'Generación de borradores de demandas, contestaciones, recursos y escritos jurídicos.',
                        color: 'bg-green-50 text-green-600 border-green-200',
                    },
                    {
                        icon: <ShieldAlert className="w-6 h-6" />,
                        title: 'Cartulario',
                        desc: 'Validación notarial de escrituras públicas conforme a la Ley del Notariado.',
                        color: 'bg-purple-50 text-purple-600 border-purple-200',
                    },
                ].map((mode, i) => (
                    <div key={i} className={`card p-5 border ${mode.color} space-y-3`}>
                        <div className="flex items-center gap-3">
                            {mode.icon}
                            <h3 className="font-bold">{mode.title}</h3>
                        </div>
                        <p className="text-sm opacity-80">{mode.desc}</p>
                    </div>
                ))}
            </div>

            {/* Info */}
            <div className="card p-6 bg-[#1E3A5F] text-white">
                <div className="flex items-start gap-4">
                    <div className="w-12 h-12 bg-white/10 rounded-xl flex items-center justify-center text-[#D4AF37] flex-shrink-0">
                        <Bot size={28} />
                    </div>
                    <div className="space-y-2">
                        <h3 className="font-bold text-[#D4AF37]">¿Cómo usar el Asistente?</h3>
                        <p className="text-sm text-white/80">
                            Haz clic en el botón flotante <span className="inline-flex items-center justify-center w-6 h-6 bg-[#D4AF37] rounded-full text-[#1E3A5F] text-xs font-bold mx-1">⚡</span> en la esquina inferior derecha para abrir el chat.
                            Selecciona un modo según tu necesidad y escribe tu consulta legal.
                        </p>
                        <p className="text-xs text-white/50 italic mt-2">
                            Las respuestas de la IA deben ser validadas por profesionales legales.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
