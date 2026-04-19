'use client';

import React, { useRef, useEffect } from 'react';
import { CheckCircle, ChevronRight, ChevronLeft } from 'lucide-react';
import { WorkflowStage } from '@/types/case';

interface WorkflowProgressBarProps {
    stages: WorkflowStage[];
    currentStageId?: string;
    tipoProceso?: string;
}

export default function WorkflowProgressBar({ stages, currentStageId, tipoProceso }: WorkflowProgressBarProps) {
    const scrollContainerRef = useRef<HTMLDivElement>(null);

    // Encontrar el índice de la etapa actual
    const currentStageIndex = currentStageId 
        ? stages.findIndex(s => s.id === currentStageId)
        : 0;

    // Auto-scroll al paso actual al cargar
    useEffect(() => {
        if (scrollContainerRef.current) {
            const currentElement = scrollContainerRef.current.querySelector('[data-current="true"]');
            if (currentElement) {
                currentElement.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
            }
        }
    }, [currentStageId, stages]);

    return (
        <div className="card p-4 mt-2 bg-gradient-to-r from-surface-50 to-white border-surface-200 shadow-sm relative overflow-hidden group">
            <div className="flex items-center justify-between mb-4 px-2">
                <div className="flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-primary-500 animate-pulse"></div>
                    <h3 className="text-[10px] font-black text-surface-400 uppercase tracking-[0.2em]">
                        Línea de Tiempo Procesal: <span className="text-primary-600">{tipoProceso?.replace(/_/g, ' ')}</span>
                    </h3>
                </div>
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button className="p-1 hover:bg-surface-100 rounded text-surface-400" onClick={() => scrollContainerRef.current?.scrollBy({ left: -200, behavior: 'smooth' })}>
                        <ChevronLeft className="w-4 h-4" />
                    </button>
                    <button className="p-1 hover:bg-surface-100 rounded text-surface-400" onClick={() => scrollContainerRef.current?.scrollBy({ left: 200, behavior: 'smooth' })}>
                        <ChevronRight className="w-4 h-4" />
                    </button>
                </div>
            </div>

            <div 
                ref={scrollContainerRef}
                className="relative flex items-start overflow-x-auto pb-12 custom-scrollbar-hide select-none"
                style={{ scrollSnapType: 'x proximity' }}
            >
                {/* Línea conectora de fondo */}
                <div className="absolute top-4 left-0 right-0 h-0.5 bg-surface-100 z-0 mx-10"></div>
                
                {stages.map((stage, idx) => {
                    const isCompleted = idx < currentStageIndex;
                    const isCurrent = idx === currentStageIndex;
                    const isPending = idx > currentStageIndex;
                    
                    return (
                        <div 
                            key={stage.id} 
                            data-current={isCurrent}
                            className="relative z-10 flex flex-col items-center min-w-[140px] px-4 scroll-snap-align-center"
                        >
                            {/* Punto de la etapa */}
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-500 ring-4 ring-white shadow-sm ${
                                isCompleted ? 'bg-emerald-500 text-white' : 
                                isCurrent ? 'bg-primary-600 text-white scale-110 ring-primary-100 shadow-lg shadow-primary-200' : 
                                'bg-white text-surface-400 border border-surface-200'
                            }`}>
                                {isCompleted ? <CheckCircle className="w-5 h-5" /> : (idx + 1)}
                            </div>
                            
                            {/* Etiqueta con diseño mejorado */}
                            <div className={`mt-3 text-center transition-all duration-300 ${isCurrent ? 'scale-105' : 'opacity-80'}`}>
                                <p className={`text-[10px] font-bold leading-tight line-clamp-2 px-1 max-w-[120px] ${
                                    isCurrent ? 'text-primary-800' : 
                                    isCompleted ? 'text-emerald-700' : 'text-surface-500'
                                }`}>
                                    {stage.nombre.toUpperCase()}
                                </p>
                                {isCurrent && (
                                    <span className="text-[8px] bg-primary-100 text-primary-600 px-1.5 py-0.5 rounded mt-1 inline-block font-black tracking-tighter">
                                        FASE ACTUAL
                                    </span>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>
            
            {/* Gradientes de scroll para indicar que hay más contenido */}
            <div className="absolute left-0 top-0 bottom-0 w-8 bg-gradient-to-r from-surface-50 to-transparent pointer-events-none opacity-50"></div>
            <div className="absolute right-0 top-0 bottom-0 w-8 bg-gradient-to-l from-white to-transparent pointer-events-none opacity-50"></div>
        </div>
    );
}
