'use client';

import React, { useState, useEffect } from 'react';
import { Sparkles, FileText, CheckCircle, Loader2, Save, X, Lightbulb } from 'lucide-react';
import { aiService, AIMode } from '@/services/aiService';

interface AIDocumentDrafterProps {
    caseId: string;
}

export const AIDocumentDrafter: React.FC<AIDocumentDrafterProps> = ({ caseId }) => {
    const [loadingSugs, setLoadingSugs] = useState(true);
    const [suggestions, setSuggestions] = useState<any[]>([]);
    
    const [drafting, setDrafting] = useState(false);
    const [draftText, setDraftText] = useState('');
    const [selectedSug, setSelectedSug] = useState<any | null>(null);

    useEffect(() => {
        const fetchSuggestions = async () => {
            setLoadingSugs(true);
            try {
                const res = await aiService.getSuggestions(caseId);
                setSuggestions(res.sugerencias || []);
            } catch (error) {
                console.error("Error fetching suggestions", error);
            } finally {
                setLoadingSugs(false);
            }
        };
        fetchSuggestions();
    }, [caseId]);

    const handleGenerate = async (sug: any) => {
        setSelectedSug(sug);
        setDrafting(true);
        setDraftText('');
        try {
            const response = await aiService.chat({
                message: `Generar documento: ${sug.titulo}. Instrucciones: Toma en cuenta la etapa procesal, los datos del caso, las partes involucradas, y aplica RAG sobre el historial y la legislación correspondiente.`,
                mode: sug.mode as AIMode,
                expediente_id: caseId
            });
            setDraftText(response.response || 'No se generó contenido.');
        } catch (error) {
            console.error(error);
            setDraftText('Ocurrió un error al generar el borrador.');
        } finally {
            setDrafting(false);
        }
    };

    const handleSave = () => {
        // En una app real, aquí se guardaría el documento en la bóveda
        alert('Documento guardado en el expediente exitosamente.');
        setSelectedSug(null);
        setDraftText('');
    };

    if (selectedSug || drafting) {
        return (
            <div className="card flex flex-col h-full bg-white border border-surface-200 overflow-hidden">
                <div className="p-4 bg-primary-50 border-b flex justify-between items-center">
                    <div className="flex items-center gap-3">
                        <Sparkles className="text-primary-600" size={20} />
                        <h3 className="font-bold text-primary-900">
                            LAA Redactando: {selectedSug?.titulo}
                        </h3>
                    </div>
                    <button onClick={() => { setSelectedSug(null); setDraftText(''); }} className="text-surface-500 hover:text-surface-800">
                        <X size={20} />
                    </button>
                </div>
                
                <div className="p-6 flex-grow flex flex-col">
                    {drafting ? (
                        <div className="flex-grow flex flex-col items-center justify-center space-y-4 py-12">
                            <Loader2 className="w-12 h-12 text-primary-500 animate-spin" />
                            <h4 className="text-lg font-bold text-surface-800">Analizando contexto y generando...</h4>
                            <p className="text-sm text-surface-500 max-w-sm text-center">
                                Aplicando RAG sobre documentos previos y marco legal vigente. Configurando datos de las partes...
                            </p>
                        </div>
                    ) : (
                        <div className="flex flex-col h-full space-y-4">
                            <div className="flex justify-between items-center">
                                <p className="text-sm text-surface-600 font-medium">Borrador generado. Puedes editarlo antes de guardar.</p>
                                <button onClick={handleSave} className="btn btn-primary btn-sm gap-2">
                                    <Save size={16} /> Guardar Documento
                                </button>
                            </div>
                            <textarea 
                                className="input h-96 font-mono text-sm leading-relaxed p-4 bg-surface-50 border-surface-300"
                                value={draftText}
                                onChange={(e) => setDraftText(e.target.value)}
                            />
                        </div>
                    )}
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h3 className="font-bold text-surface-800 flex items-center gap-2">
                    <Lightbulb className="text-yellow-500" size={20} /> Sugerencias Inteligentes
                </h3>
            </div>

            {loadingSugs ? (
                <div className="p-8 text-center text-surface-500">Cargando contexto procesal...</div>
            ) : suggestions.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {suggestions.map((sug, idx) => (
                        <div key={idx} className="card p-5 border border-surface-200 hover:border-primary-300 hover:shadow-md transition-all cursor-pointer group" onClick={() => handleGenerate(sug)}>
                            <div className="flex items-start justify-between mb-2">
                                <div className="flex items-center gap-2 font-bold text-surface-900 group-hover:text-primary-600 transition-colors">
                                    <FileText size={18} /> {sug.titulo}
                                </div>
                                <span className="text-[10px] bg-accent-100 text-accent-700 px-2 py-1 rounded-full font-bold uppercase">
                                    Modo: {sug.mode}
                                </span>
                            </div>
                            <p className="text-xs text-surface-500 mb-4 h-8">{sug.descripcion}</p>
                            <button className="text-xs font-bold text-primary-600 flex items-center gap-1 group-hover:underline">
                                <Sparkles size={14} /> Redactar con IA
                            </button>
                        </div>
                    ))}
                </div>
            ) : (
                <div className="card p-6 text-center border-dashed">
                    <p className="text-surface-500 text-sm">No hay sugerencias para esta etapa. Puedes pedir un documento personalizado.</p>
                </div>
            )}
        </div>
    );
};
