'use client';

import { useState, useEffect } from 'react';
import { ChevronDown, Check, Loader2 } from 'lucide-react';
import { caseService } from '@/services/caseService';
import { CaseStatus } from '@/types/case';
import { useToast } from '@/components/ui/ToastProvider';

interface CaseStatusToggleProps {
    caseId: string;
    currentStatusId?: string;
    onStatusChange: (newStatusId: string) => void;
}

export default function CaseStatusToggle({ caseId, currentStatusId, onStatusChange }: CaseStatusToggleProps) {
    const [statuses, setStatuses] = useState<CaseStatus[]>([]);
    const [isOpen, setIsOpen] = useState(false);
    const [loading, setLoading] = useState(false);
    const [fetching, setFetching] = useState(true);
    const toast = useToast();

    useEffect(() => {
        const fetchStatuses = async () => {
            try {
                const data = await caseService.getStatuses();
                setStatuses(data);
            } catch (error) {
                console.error('Failed to fetch statuses', error);
            } finally {
                setFetching(false);
            }
        };
        fetchStatuses();
    }, []);

    const currentStatus = statuses.find(s => s.id === currentStatusId);

    const handleStatusUpdate = async (statusId: string) => {
        if (statusId === currentStatusId) {
            setIsOpen(false);
            return;
        }
        
        setLoading(true);
        try {
            await caseService.changeStatus(caseId, statusId);
            onStatusChange(statusId);
            toast.success('Estado procesal actualizado');
            setIsOpen(false);
        } catch (error) {
            toast.error('Error al cambiar el estado');
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    if (fetching) return <div className="h-8 w-32 bg-surface-100 animate-pulse rounded-full"></div>;

    return (
        <div className="relative">
            <button
                onClick={() => setIsOpen(!isOpen)}
                disabled={loading}
                className="flex items-center gap-2.5 px-3.5 py-1.5 rounded-full border border-surface-200 bg-white hover:border-primary-200 hover:bg-primary-50/30 transition-all shadow-sm group"
            >
                <div 
                    className={`w-2 h-2 rounded-full ${currentStatus?.es_final ? 'ring-2 ring-offset-1 ring-surface-200' : ''}`} 
                    style={{ backgroundColor: currentStatus?.color_hex || '#94a3b8' }}
                ></div>
                <span className="text-xs font-bold text-surface-700 tracking-tight">
                    {currentStatus?.nombre?.toUpperCase() || 'SIN ESTADO'}
                </span>
                {loading ? (
                    <Loader2 className="w-3 h-3 animate-spin text-primary-500" />
                ) : (
                    <ChevronDown className={`w-3.5 h-3.5 text-surface-400 group-hover:text-primary-500 transition-transform duration-300 ${isOpen ? 'rotate-180' : ''}`} />
                )}
            </button>

            {isOpen && (
                <>
                    <div className="fixed inset-0 z-30" onClick={() => setIsOpen(false)}></div>
                    <div className="absolute left-0 mt-2 w-64 bg-white border border-surface-200 rounded-2xl shadow-2xl z-40 py-2.5 overflow-hidden animate-in fade-in slide-in-from-top-2 duration-200">
                        <div className="px-4 py-2 mb-1 border-b border-surface-50">
                            <span className="text-[10px] font-black text-surface-400 uppercase tracking-widest">Flujo Procesal</span>
                        </div>
                        <div className="max-h-[300px] overflow-y-auto custom-scrollbar">
                            {statuses.map((status) => (
                                <button
                                    key={status.id}
                                    onClick={() => handleStatusUpdate(status.id)}
                                    className={`w-full text-left px-4 py-3 text-sm flex items-center justify-between hover:bg-surface-50 transition-colors group/item ${
                                        status.id === currentStatusId ? 'bg-primary-50/50 text-primary-700 font-bold' : 'text-surface-600 hover:text-surface-900'
                                    }`}
                                >
                                    <div className="flex items-center gap-3">
                                        <div 
                                            className="w-2.5 h-2.5 rounded-full shadow-inner group-hover/item:scale-125 transition-transform" 
                                            style={{ backgroundColor: status.color_hex || '#94a3b8' }}
                                        ></div>
                                        <div className="flex flex-col">
                                            <span className="leading-none">{status.nombre}</span>
                                            {status.es_final && <span className="text-[9px] text-surface-400 font-medium">Estado Final de Cierre</span>}
                                        </div>
                                    </div>
                                    {status.id === currentStatusId ? (
                                        <Check className="w-4 h-4 text-primary-600" />
                                    ) : (
                                        <div className="w-4 h-4 rounded-full border border-surface-200 group-hover/item:border-primary-300"></div>
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
