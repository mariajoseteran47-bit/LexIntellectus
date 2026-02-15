'use client';

import React, { useState } from 'react';
import { Zap, Shield, FileText, CheckCircle2, AlertCircle, PlayCircle, Loader2 } from 'lucide-react';
import { aiService } from '@/services/aiService';

interface CaseTheoryAnalysisProps {
    caseId: string;
}

const CaseTheoryAnalysis: React.FC<CaseTheoryAnalysisProps> = ({ caseId }) => {
    const [loading, setLoading] = useState(false);
    const [data, setData] = useState<any>(null);

    const handleGenerate = async () => {
        setLoading(true);
        try {
            // In a real scenario, this would call the 'estratega' mode
            const result = await aiService.chat({
                message: "Generar Teoría del Caso",
                mode: 'estratega',
                expediente_id: caseId
            });
            // The backend returns a text confirmation, but in a real app, 
            // it might return the JSON directly or we fetch it from a separate endpoint.
            // For this demo, we'll simulate the structured display.

            // Mocked data based on what the AI would return in JSON mode
            setData({
                resumen_ejecutivo: "Litigio civil por incumplimiento de contrato de arrendamiento comercial. El demandante busca la rescisión y el pago de cánones adeudados.",
                hechos_facticos: [
                    { fecha: "2023-05-10", hecho: "Firma del contrato por 24 meses.", prueba_ref: "Contrato Arrendamiento" },
                    { fecha: "2024-01-05", hecho: "Cese de pagos por parte del arrendatario.", prueba_ref: "Estado de Cuenta" },
                    { fecha: "2024-02-20", hecho: "Notificación judicial de mora.", prueba_ref: "Cédula Judicial" }
                ],
                fundamento_juridico: [
                    { articulo: "Art. 1820 del Código Civil", aplicacion: "Resolución del contrato por mora." },
                    { articulo: "Art. 1834 del Código Civil", aplicacion: "Pago de daños y perjuicios." }
                ],
                estrategia: "Proceder con la vía sumaria civil para una resolución rápida, solicitando el embargo preventivo de bienes para asegurar el pago de los meses restantes."
            });
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="card p-12 flex flex-col items-center justify-center space-y-4">
                <Loader2 className="w-10 h-10 text-primary-500 animate-spin" />
                <p className="text-surface-600 font-medium">LAA está procesando el expediente...</p>
                <p className="text-xs text-surface-400">Analizando hechos, leyes y jurisprudencia relevante.</p>
            </div>
        );
    }

    if (!data) {
        return (
            <div className="card p-8 border-dashed border-2 flex flex-col items-center justify-center text-center space-y-4">
                <div className="w-16 h-16 bg-accent-100 rounded-full flex items-center justify-center text-accent-600">
                    <Zap size={32} />
                </div>
                <div>
                    <h3 className="text-lg font-bold text-surface-900">Teoría del Caso Automatizada</h3>
                    <p className="text-surface-500 max-w-md mx-auto mt-1">
                        Utiliza el modo Estratega de LAA para generar un análisis estructurado de hechos, fundamentos y estrategia legal basado en la legislación de Nicaragua.
                    </p>
                </div>
                <button
                    onClick={handleGenerate}
                    className="btn btn-primary gap-2 px-8"
                >
                    <PlayCircle size={20} /> Generar Análisis Ahora
                </button>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Resumen */}
            <div className="card p-6 border-l-4 border-primary-500">
                <h4 className="text-xs font-bold text-primary-600 uppercase tracking-widest mb-2">Resumen Ejecutivo</h4>
                <p className="text-surface-800 leading-relaxed italic">"{data.resumen_ejecutivo}"</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Hechos */}
                <div className="card overflow-hidden">
                    <div className="p-4 border-b bg-surface-50 flex items-center gap-2 font-bold text-surface-800">
                        <FileText size={18} className="text-primary-500" /> Línea de Tiempo / Hechos
                    </div>
                    <div className="p-0">
                        {data.hechos_facticos.map((h: any, i: number) => (
                            <div key={i} className="p-4 border-b last:border-0 hover:bg-surface-50 transition-colors">
                                <div className="flex justify-between items-start mb-1">
                                    <span className="text-xs font-mono font-bold text-primary-600">{h.fecha}</span>
                                    <span className="text-[10px] bg-accent-100 text-accent-700 px-1.5 py-0.5 rounded uppercase font-bold">Ref: {h.prueba_ref}</span>
                                </div>
                                <p className="text-sm text-surface-700">{h.hecho}</p>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Fundamentos */}
                <div className="card overflow-hidden">
                    <div className="p-4 border-b bg-surface-50 flex items-center gap-2 font-bold text-surface-800">
                        <Shield size={18} className="text-primary-500" /> Fundamentación Jurídica
                    </div>
                    <div className="p-4 space-y-4">
                        {data.fundamento_juridico.map((f: any, i: number) => (
                            <div key={i} className="flex gap-3">
                                <CheckCircle2 size={18} className="text-green-500 flex-shrink-0" />
                                <div>
                                    <h5 className="text-sm font-bold text-surface-900">{f.articulo}</h5>
                                    <p className="text-sm text-surface-600">{f.aplicacion}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Estrategia */}
            <div className="card p-6 bg-[#1E3A5F] text-white">
                <div className="flex items-center gap-3 mb-4">
                    <Zap className="text-[#D4AF37]" size={24} />
                    <h4 className="text-lg font-bold">Estrategia Recomendada</h4>
                </div>
                <p className="text-sm leading-relaxed text-surface-100">
                    {data.estrategia}
                </p>
                <div className="mt-6 pt-6 border-t border-white/10 flex justify-between items-center text-xs">
                    <span className="text-surface-300">Generado por LAA Strategist Mode</span>
                    <button className="text-[#D4AF37] hover:underline font-bold uppercase tracking-wider">Exportar a PDF</button>
                </div>
            </div>
        </div>
    );
};

export default CaseTheoryAnalysis;
