'use client';

import { Settings, Clock } from 'lucide-react';

export default function SettingsPage() {
    return (
        <div className="flex flex-col items-center justify-center py-20 text-center animate-fade-in">
            <div className="w-20 h-20 bg-primary-50 rounded-2xl flex items-center justify-center mb-6">
                <Settings className="w-10 h-10 text-primary-400" />
            </div>
            <h1 className="text-2xl font-bold text-surface-900 mb-2">Configuración</h1>
            <p className="text-surface-500 max-w-md">
                El módulo de Configuración está en desarrollo. Pronto podrás personalizar el sistema, roles y permisos desde aquí.
            </p>
            <div className="mt-6 flex items-center gap-2 text-sm text-surface-400">
                <Clock className="w-4 h-4" />
                Próximamente
            </div>
        </div>
    );
}
