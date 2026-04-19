'use client';

import { useState, useEffect } from 'react';
import { ChevronDown, Check, Loader2, Gauge } from 'lucide-react';
import { caseService } from '@/services/caseService';
import { WorkflowStage } from '@/types/case';
import { useToast } from '@/components/ui/ToastProvider';

interface CaseStageToggleProps {
    caseId: string;
    ramo: string;
    tipoProceso?: string;
    currentStageId?: string;
    onStageChange: (newStageId: string) => void;
}

export default function CaseStageToggle({ caseId, ramo, tipoProceso, currentStageId, onStageChange }: CaseStageToggleProps) {
    const [stages, setStages] = useState<WorkflowStage[]>([]);
    const [isOpen, setIsOpen] = useState(false);
    const [loading, setLoading] = useState(false);
    const [fetching, setFetching] = useState(true);
    const toast = useToast();

    useEffect(() => {
        const fetchStages = async () => {
            try {
                // Normalizar ramo para la búsqueda
                const cleanRamo = ramo?.toLowerCase().trim();
                const data = await caseService.getStages(cleanRamo, tipoProceso);
                setStages(data);
            } catch (error) {
                console.error('Failed to fetch stages', error);
            } finally {
                setFetching(false);
            }
        };
        if (ramo) fetchStages();
    }, [ramo, tipoProceso]);

    const currentStage = stages.find(s => s.id === currentStageId);

    const handleStageUpdate = async (stageId: string) => {
        if (stageId === currentStageId) {
            setIsOpen(false);
            return;
        }
        
        setLoading(true);
        try {
            await caseService.changeStage(caseId, stageId);
            onStageChange(stageId);
            toast.success('Etapa procesal actualizada');
            setIsOpen(false);
        } catch (error) {
            toast.error('Error al cambiar la etapa');
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    if (fetching) return <div className="h-8 w-48 bg-surface-100 animate-pulse rounded-full"></div>;
    if (stages.length === 0) return null;

    return (
        <div className="relative">
            <button
                onClick={() => setIsOpen(!isOpen)}
                disabled={loading}
                className="flex items-center gap-2.5 px-4 py-1.5 rounded-full border border-primary-200 bg-primary-50/30 hover:bg-primary-50 transition-all shadow-sm group"
            >
                <Gauge className={`w-3.5 h-3.5 ${currentStage?.es_final ? 'text-green-500' : 'text-primary-500'}`} />
                <span className="text-xs font-bold text-primary-700 tracking-tight uppercase whitespace-nowrap">
                    ETAPA: {currentStage?.nombre || 'SELECCIONAR'}
                </span>
                {loading ? (
                    <Loader2 className="w-3 h-3 animate-spin text-primary-500" />
                ) : (
                    <ChevronDown className={`w-3.5 h-3.5 text-primary-400 group-hover:text-primary-600 transition-transform duration-300 ${isOpen ? 'rotate-180' : ''}`} />
                )}
            </button>

            {isOpen && (
                <>
                    <div className="fixed inset-0 z-30" onClick={() => setIsOpen(false)}></div>
                    <div className="absolute right-0 lg:left-0 mt-2 w-80 bg-white border border-surface-200 rounded-2xl shadow-2xl z-40 py-2.5 overflow-hidden animate-in fade-in slide-in-from-top-2 duration-200">
                        <div className="px-4 py-2 mb-1 border-b border-surface-50 flex items-center justify-between">
                            <span className="text-[10px] font-black text-primary-400 uppercase tracking-widest">Procedimiento {ramo?.toUpperCase()}</span>
                            {tipoProceso && <span className="text-[9px] bg-primary-100 text-primary-600 px-1.5 py-0.5 rounded font-bold capitalize">{tipoProceso}</span>}
                        </div>
                        <div className="max-h-[400px] overflow-y-auto custom-scrollbar">
                            {stages.map((stage, index) => (
                                <button
                                    key={stage.id}
                                    onClick={() => handleStageUpdate(stage.id)}
                                    className={`w-full text-left px-4 py-3 text-sm flex items-center justify-between hover:bg-primary-50 transition-colors group/item ${
                                        stage.id === currentStageId ? 'bg-primary-100/50 text-primary-800 font-bold' : 'text-surface-600 hover:text-surface-900 border-b border-surface-50/50'
                                    }`}
                                >
                                    <div className="flex items-center gap-3">
                                        <div className={`flex items-center justify-center w-6 h-6 rounded-full text-[10px] font-bold shrink-0 ${
                                            stage.id === currentStageId ? 'bg-primary-600 text-white ring-4 ring-primary-100' : 'bg-surface-100 text-surface-400'
                                        }`}>
                                            {index + 1}
                                        </div>
                                        <div className="flex flex-col overflow-hidden">
                                            <span className="truncate">{stage.nombre}</span>
                                            {stage.dias_plazo_legal && (
                                                <span className="text-[9px] text-surface-400 mt-1">Término de Ley: {stage.dias_plazo_legal} días hábiles</span>
                                            )}
                                        </div>
                                    </div>
                                    {stage.id === currentStageId && (
                                        <Check className="w-4 h-4 text-primary-600 shrink-0" />
                                    )}
                                </button>
                            ))}
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}
