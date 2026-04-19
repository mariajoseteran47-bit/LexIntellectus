'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
    Briefcase, Clock, FileText, Users, Scale, TrendingUp,
    ChevronRight, AlertTriangle, CheckCircle, Plus, Bot, Calendar
} from 'lucide-react';

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

interface ActivityItem {
    id: string;
    icon: 'case' | 'deadline' | 'document' | 'user';
    action: string;
    detail: string;
    time: string;
    color: string;
}

export default function DashboardPage() {
    const [user, setUser] = useState<UserInfo | null>(null);
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [currentTime, setCurrentTime] = useState(new Date());
    const [deadlines, setDeadlines] = useState<any[]>([]);

    useEffect(() => {
        const stored = localStorage.getItem('user');
        if (stored) setUser(JSON.parse(stored));
        const timer = setInterval(() => setCurrentTime(new Date()), 60000);
        return () => clearInterval(timer);
    }, []);

    useEffect(() => {
        const token = localStorage.getItem('access_token');
        if (!token) return;

        // Fetch dashboard stats
        fetch('/api/v1/dashboard/stats', {
            headers: { 'Authorization': `Bearer ${token}` },
        })
            .then(res => res.ok ? res.json() : null)
            .then(data => { if (data) setStats(data); })
            .catch(() => { });

        // Fetch upcoming deadlines
        fetch('/api/v1/dashboard/upcoming-deadlines?limit=5', {
            headers: { 'Authorization': `Bearer ${token}` },
        })
            .then(res => res.ok ? res.json() : [])
            .then(data => { if (Array.isArray(data)) setDeadlines(data); })
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

    const formatDate = (d: string) => {
        const date = new Date(d);
        const today = new Date();
        const diffMs = date.getTime() - today.getTime();
        const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));

        if (diffDays === 0) return 'Hoy';
        if (diffDays === 1) return 'Mañana';
        if (diffDays < 0) return `Vencido hace ${Math.abs(diffDays)} día(s)`;
        if (diffDays <= 7) return `En ${diffDays} días`;
        return date.toLocaleDateString('es-NI', { day: '2-digit', month: 'short' });
    };

    const getUrgencyColor = (d: string) => {
        const date = new Date(d);
        const today = new Date();
        const diffMs = date.getTime() - today.getTime();
        const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));

        if (diffDays < 0) return 'text-red-600 bg-red-50';
        if (diffDays <= 1) return 'text-red-600 bg-red-50';
        if (diffDays <= 3) return 'text-amber-600 bg-amber-50';
        return 'text-blue-600 bg-blue-50';
    };

    if (!user) return null;

    return (
        <div className="animate-fade-in space-y-8">
            {/* Greeting + Date */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-surface-900">
                        {greeting()}, <span className="text-primary-600">{user.nombre}</span>
                    </h1>
                    <p className="text-surface-500 mt-1 flex items-center gap-2">
                        <Scale className="w-4 h-4" />
                        {userTypeLabel[user.tipo_usuario] || user.tipo_usuario} · {user.tenant_nombre || 'Despacho'}
                    </p>
                </div>
                <div className="text-right hidden md:block">
                    <p className="text-sm font-medium text-surface-700">
                        {currentTime.toLocaleDateString('es-NI', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
                    </p>
                    <p className="text-xs text-surface-400 mt-0.5">
                        {currentTime.toLocaleTimeString('es-NI', { hour: '2-digit', minute: '2-digit' })}
                    </p>
                </div>
            </div>

            {/* Stats Grid — Modern cards with gradients */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
                {[
                    {
                        label: 'Expedientes Activos',
                        value: stats?.active_cases ?? '–',
                        icon: Briefcase,
                        gradient: 'from-blue-500 to-blue-600',
                        lightBg: 'bg-blue-50',
                        lightText: 'text-blue-600',
                        href: '/dashboard/cases',
                    },
                    {
                        label: 'Plazos Urgentes',
                        value: stats?.urgent_deadlines ?? '–',
                        icon: AlertTriangle,
                        gradient: 'from-amber-500 to-orange-500',
                        lightBg: 'bg-amber-50',
                        lightText: 'text-amber-600',
                        href: '/dashboard/agenda',
                    },
                    {
                        label: 'Estado del Sistema',
                        value: stats?.system_status === 'operational' ? 'Operativo' : 'Verificando',
                        icon: CheckCircle,
                        gradient: 'from-emerald-500 to-green-600',
                        lightBg: 'bg-emerald-50',
                        lightText: 'text-emerald-600',
                        href: '#',
                    },
                    {
                        label: 'Asistente IA',
                        value: 'Disponible',
                        icon: Bot,
                        gradient: 'from-violet-500 to-purple-600',
                        lightBg: 'bg-violet-50',
                        lightText: 'text-violet-600',
                        href: '/dashboard/ai',
                    },
                ].map((stat, i) => (
                    <Link
                        key={i}
                        href={stat.href}
                        className="group card p-0 overflow-hidden hover:scale-[1.02] transition-transform duration-200"
                        style={{ animationDelay: `${i * 0.08}s` }}
                    >
                        <div className={`h-1.5 bg-gradient-to-r ${stat.gradient}`} />
                        <div className="p-5">
                            <div className="flex items-start justify-between">
                                <div>
                                    <p className="text-xs font-medium text-surface-500 uppercase tracking-wide">{stat.label}</p>
                                    <p className="text-2xl font-bold text-surface-900 mt-1.5">{stat.value}</p>
                                </div>
                                <div className={`w-10 h-10 rounded-xl ${stat.lightBg} flex items-center justify-center group-hover:scale-110 transition-transform`}>
                                    <stat.icon className={`w-5 h-5 ${stat.lightText}`} />
                                </div>
                            </div>
                        </div>
                    </Link>
                ))}
            </div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* Upcoming Deadlines */}
                <div className="card overflow-hidden lg:col-span-2">
                    <div className="px-6 py-4 border-b border-surface-200 flex items-center justify-between bg-surface-50/50">
                        <h3 className="font-semibold text-surface-800 flex items-center gap-2">
                            <Clock className="w-4 h-4 text-primary-500" />
                            Próximos Plazos Fatales
                        </h3>
                        <Link href="/dashboard/agenda" className="text-xs text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1">
                            Ver Agenda <ChevronRight className="w-3 h-3" />
                        </Link>
                    </div>
                    <div className="divide-y divide-surface-100">
                        {deadlines.length > 0 ? (
                            deadlines.map((d: any, i: number) => (
                                <div key={d.id || i} className="px-6 py-3.5 flex items-center justify-between hover:bg-surface-50/50 transition-colors">
                                    <div className="flex items-center gap-3 flex-1 min-w-0">
                                        <div className={`w-2 h-2 rounded-full flex-shrink-0 ${
                                            d.prioridad === 'critica' ? 'bg-red-500' :
                                            d.prioridad === 'alta' ? 'bg-amber-500' : 'bg-blue-400'
                                        }`} />
                                        <div className="min-w-0">
                                            <p className="text-sm font-medium text-surface-800 truncate">{d.descripcion}</p>
                                            <p className="text-xs text-surface-500">{d.tipo_plazo || 'procesal'}</p>
                                        </div>
                                    </div>
                                    <span className={`text-xs font-medium px-2.5 py-1 rounded-lg flex-shrink-0 ${getUrgencyColor(d.fecha_vencimiento)}`}>
                                        {formatDate(d.fecha_vencimiento)}
                                    </span>
                                </div>
                            ))
                        ) : (
                            <div className="px-6 py-12 text-center">
                                <Calendar className="w-10 h-10 text-surface-200 mx-auto mb-3" />
                                <p className="text-surface-500 text-sm font-medium">No hay plazos próximos</p>
                                <p className="text-surface-400 text-xs mt-1">Los plazos fatales de sus expedientes aparecerán aquí</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* Quick Actions */}
                <div className="space-y-6">
                    <div className="card p-6">
                        <h3 className="font-semibold text-surface-800 mb-4 flex items-center gap-2">
                            <TrendingUp className="w-4 h-4 text-primary-500" />
                            Acciones Rápidas
                        </h3>
                        <div className="space-y-2">
                            {[
                                { label: 'Nuevo Expediente', icon: Plus, href: '/dashboard/cases/new', color: 'text-blue-600 bg-blue-50 hover:bg-blue-100' },
                                { label: 'Gestionar Casos', icon: Briefcase, href: '/dashboard/cases', color: 'text-emerald-600 bg-emerald-50 hover:bg-emerald-100' },
                                { label: 'Consultar IA', icon: Bot, href: '/dashboard/ai', color: 'text-violet-600 bg-violet-50 hover:bg-violet-100' },
                                { label: 'Subir Documento', icon: FileText, href: '/dashboard/documents', color: 'text-amber-600 bg-amber-50 hover:bg-amber-100' },
                                { label: 'Ver Clientes', icon: Users, href: '/dashboard/clients', color: 'text-pink-600 bg-pink-50 hover:bg-pink-100' },
                            ].map((action, i) => (
                                <Link
                                    key={i}
                                    href={action.href}
                                    className={`flex items-center gap-3 p-3 rounded-xl text-sm font-medium transition-all duration-200 ${action.color}`}
                                >
                                    <action.icon className="w-4 h-4" />
                                    {action.label}
                                </Link>
                            ))}
                        </div>
                    </div>

                    {/* AI Promo Card */}
                    <div className="card p-0 overflow-hidden bg-gradient-to-br from-[#1E3A5F] to-[#0F2440] text-white">
                        <div className="p-6">
                            <div className="flex items-center gap-3 mb-3">
                                <div className="w-10 h-10 rounded-xl bg-white/10 flex items-center justify-center">
                                    <Bot className="w-5 h-5 text-[#D4AF37]" />
                                </div>
                                <div>
                                    <h4 className="font-bold text-[#D4AF37]">Asistente Legal IA</h4>
                                    <p className="text-xs text-white/60">4 modos especializados</p>
                                </div>
                            </div>
                            <p className="text-xs text-white/70 leading-relaxed mb-4">
                                Consulta leyes, genera estrategias, redacta escritos y valida documentos notariales con inteligencia artificial.
                            </p>
                            <Link
                                href="/dashboard/ai"
                                className="block w-full text-center py-2 rounded-lg bg-[#D4AF37] text-[#1E3A5F] text-sm font-bold hover:bg-[#E5C44C] transition-colors"
                            >
                                Abrir Asistente IA
                            </Link>
                        </div>
                    </div>
                </div>
            </div>

            {/* Cases Distribution — Inline mini chart */}
            <div className="card p-6">
                <h3 className="font-semibold text-surface-800 mb-5 flex items-center gap-2">
                    <Scale className="w-4 h-4 text-primary-500" />
                    Distribución por Materia
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                    {[
                        { name: 'Civil', color: 'bg-blue-500', pct: 35 },
                        { name: 'Penal', color: 'bg-red-500', pct: 20 },
                        { name: 'Familia', color: 'bg-pink-500', pct: 18 },
                        { name: 'Laboral', color: 'bg-amber-500', pct: 15 },
                        { name: 'Mercantil', color: 'bg-emerald-500', pct: 12 },
                    ].map((item) => (
                        <div key={item.name} className="text-center">
                            <div className="relative w-16 h-16 mx-auto mb-2">
                                <svg className="w-16 h-16 -rotate-90" viewBox="0 0 36 36">
                                    <circle
                                        cx="18" cy="18" r="14"
                                        fill="none"
                                        stroke="currentColor"
                                        strokeWidth="3"
                                        className="text-surface-100"
                                    />
                                    <circle
                                        cx="18" cy="18" r="14"
                                        fill="none"
                                        stroke="currentColor"
                                        strokeWidth="3"
                                        strokeDasharray={`${item.pct * 0.88} 100`}
                                        strokeLinecap="round"
                                        className={item.color.replace('bg-', 'text-')}
                                    />
                                </svg>
                                <span className="absolute inset-0 flex items-center justify-center text-xs font-bold text-surface-700">
                                    {item.pct}%
                                </span>
                            </div>
                            <p className="text-xs font-medium text-surface-600">{item.name}</p>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
