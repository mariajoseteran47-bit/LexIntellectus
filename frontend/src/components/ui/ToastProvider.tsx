'use client';

import { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { CheckCircle, XCircle, AlertTriangle, Info, X } from 'lucide-react';

// === Types ===
type ToastType = 'success' | 'error' | 'warning' | 'info';

interface Toast {
    id: string;
    type: ToastType;
    title: string;
    message?: string;
    duration?: number;
}

interface ToastContextValue {
    toasts: Toast[];
    addToast: (toast: Omit<Toast, 'id'>) => void;
    removeToast: (id: string) => void;
    success: (title: string, message?: string) => void;
    error: (title: string, message?: string) => void;
    warning: (title: string, message?: string) => void;
    info: (title: string, message?: string) => void;
}

// === Context ===
const ToastContext = createContext<ToastContextValue | undefined>(undefined);

export function useToast() {
    const context = useContext(ToastContext);
    if (!context) {
        throw new Error('useToast must be used within a ToastProvider');
    }
    return context;
}

// === Icons & Styles by type ===
const toastConfig: Record<ToastType, { icon: typeof CheckCircle; bg: string; border: string; iconColor: string }> = {
    success: {
        icon: CheckCircle,
        bg: 'bg-emerald-50',
        border: 'border-emerald-200',
        iconColor: 'text-emerald-500',
    },
    error: {
        icon: XCircle,
        bg: 'bg-red-50',
        border: 'border-red-200',
        iconColor: 'text-red-500',
    },
    warning: {
        icon: AlertTriangle,
        bg: 'bg-amber-50',
        border: 'border-amber-200',
        iconColor: 'text-amber-500',
    },
    info: {
        icon: Info,
        bg: 'bg-blue-50',
        border: 'border-blue-200',
        iconColor: 'text-blue-500',
    },
};

// === Toast Item Component ===
function ToastItem({ toast, onRemove }: { toast: Toast; onRemove: (id: string) => void }) {
    const config = toastConfig[toast.type];
    const Icon = config.icon;

    return (
        <div
            className={`
                flex items-start gap-3 p-4 rounded-xl border shadow-lg
                ${config.bg} ${config.border}
                animate-slide-up backdrop-blur-sm
                max-w-sm w-full pointer-events-auto
            `}
            role="alert"
        >
            <Icon className={`w-5 h-5 ${config.iconColor} flex-shrink-0 mt-0.5`} />
            <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-surface-900">{toast.title}</p>
                {toast.message && (
                    <p className="text-xs text-surface-600 mt-0.5 leading-relaxed">{toast.message}</p>
                )}
            </div>
            <button
                onClick={() => onRemove(toast.id)}
                className="text-surface-400 hover:text-surface-600 transition-colors flex-shrink-0"
            >
                <X className="w-4 h-4" />
            </button>
        </div>
    );
}

// === Provider ===
export function ToastProvider({ children }: { children: ReactNode }) {
    const [toasts, setToasts] = useState<Toast[]>([]);

    const removeToast = useCallback((id: string) => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
    }, []);

    const addToast = useCallback(
        (toast: Omit<Toast, 'id'>) => {
            const id = `toast-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
            const newToast: Toast = { ...toast, id };

            setToasts((prev) => [...prev, newToast]);

            // Auto-remove after duration
            const duration = toast.duration ?? (toast.type === 'error' ? 6000 : 4000);
            setTimeout(() => removeToast(id), duration);
        },
        [removeToast]
    );

    const success = useCallback(
        (title: string, message?: string) => addToast({ type: 'success', title, message }),
        [addToast]
    );

    const error = useCallback(
        (title: string, message?: string) => addToast({ type: 'error', title, message, duration: 6000 }),
        [addToast]
    );

    const warning = useCallback(
        (title: string, message?: string) => addToast({ type: 'warning', title, message }),
        [addToast]
    );

    const info = useCallback(
        (title: string, message?: string) => addToast({ type: 'info', title, message }),
        [addToast]
    );

    return (
        <ToastContext.Provider value={{ toasts, addToast, removeToast, success, error, warning, info }}>
            {children}

            {/* Toast Container — fixed in bottom-right */}
            <div className="fixed bottom-6 right-6 z-[100] flex flex-col-reverse gap-3 pointer-events-none">
                {toasts.map((toast) => (
                    <ToastItem key={toast.id} toast={toast} onRemove={removeToast} />
                ))}
            </div>
        </ToastContext.Provider>
    );
}
