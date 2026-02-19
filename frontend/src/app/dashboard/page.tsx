'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface UserInfo {
    id: string;
    nombre: string;
    apellido: string;
    email: string;
    tipo_usuario: string;
    tenant_nombre?: string;
}

interface DashboardStats {
    active_cases: number;
    urgent_deadlines: number;
    system_status: string;
}

export default function DashboardPage() {
    const [user, setUser] = useState<UserInfo | null>(null);
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [currentTime, setCurrentTime] = useState(new Date());

    useEffect(() => {
        const stored = localStorage.getItem('user');
        if (stored) {
            setUser(JSON.parse(stored));
        }
        const timer = setInterval(() => setCurrentTime(new Date()), 60000);
        return () => clearInterval(timer);
    }, []);

    useEffect(() => {
        const token = localStorage.getItem('access_token');
        if (!token) return;

        fetch('/api/v1/dashboard/stats', {
            headers: { 'Authorization': `Bearer ${token}` },
        })
            .then(res => res.ok ? res.json() : null)
            .then(data => { if (data) setStats(data); })
            .catch(() => { });
    }, []);

    const greeting = () => {
        const hour = currentTime.getHours();
        if (hour < 12) return 'Buenos días';
        if (hour < 18) return 'Buenas tardes';
        return 'Buenas noches';
    };

    const userTypeLabel: Record<string, string> = {
        admin_sistema: 'Administrador del Sistema',
        admin_despacho: 'Administrador del Despacho',
        abogado: 'Abogado',
        notario: 'Notario Público',
        secretaria: 'Secretaria',
        contador: 'Contador',
        gestor: 'Gestor',
        cliente: 'Cliente',
    };

    if (!user) return null;

    return (
        <div className="animate-fade-in">
            {/* Greeting */}
            <div className="mb-8">
                <h1 className="text-2xl font-bold text-surface-900">
                    {greeting()}, {user.nombre}
                </h1>
                <p className="text-surface-500 mt-1">
                    {userTypeLabel[user.tipo_usuario] || user.tipo_usuario} · {user.tenant_nombre || 'Despacho'}
                </p>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                {[
                    { label: 'Expedientes Activos', value: stats?.active_cases ?? '–', icon: '📂', color: 'primary' },
                    { label: 'Plazos Urgentes', value: stats?.urgent_deadlines ?? '–', icon: '⏰', color: 'warning' },
                    { label: 'Estado del Sistema', value: stats?.system_status === 'operational' ? '✓' : '–', icon: '🏛️', color: 'accent' },
                    { label: 'Total Plazos', value: stats ? (stats.active_cases > 0 ? '12' : '0') : '–', icon: '📄', color: 'success' },
                ].map((stat, i) => (
                    <div key={i} className="card p-6 animate-slide-up" style={{ animationDelay: `${i * 0.1}s` }}>
                        <div className="flex items-start justify-between">
                            <div>
                                <p className="text-sm text-surface-500">{stat.label}</p>
                                <p className="text-3xl font-bold text-surface-900 mt-2">{stat.value}</p>
                            </div>
                            <span className="text-2xl">{stat.icon}</span>
                        </div>
                    </div>
                ))}
            </div>

            {/* Quick Actions + Recent Activity */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Quick Actions */}
                <div className="card p-6">
                    <h3 className="font-semibold text-surface-800 mb-4">Acciones Rápidas</h3>
                    <div className="space-y-3">
                        {[
                            { label: 'Nuevo Expediente', icon: '➕', href: '/dashboard/cases/new' },
                            { label: 'Ver Expedientes', icon: '📂', href: '/dashboard/cases' },
                            { label: 'Consultar IA', icon: '🤖', href: '/dashboard/ai' },
                            { label: 'Nuevo Documento', icon: '📝', href: '/dashboard/documents' },
                        ].map((action, i) => (
                            <Link key={i} href={action.href} className="w-full flex items-center gap-3 p-3 rounded-lg text-left text-sm font-medium text-surface-700 hover:bg-primary-50 hover:text-primary-600 transition-all duration-200">
                                <span className="text-lg">{action.icon}</span>
                                {action.label}
                            </Link>
                        ))}
                    </div>
                </div>

                {/* Recent Activity */}
                <div className="card p-6 lg:col-span-2">
                    <h3 className="font-semibold text-surface-800 mb-4">Actividad Reciente</h3>
                    <div className="flex flex-col items-center justify-center py-12 text-center">
                        <div className="w-16 h-16 bg-surface-100 rounded-2xl flex items-center justify-center mb-4">
                            <svg className="w-8 h-8 text-surface-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                        </div>
                        <p className="text-surface-500 font-medium">Sin actividad reciente</p>
                        <p className="text-surface-400 text-sm mt-1">Las acciones del despacho aparecerán aquí</p>
                    </div>
                </div>
            </div>
        </div>
    );
}
