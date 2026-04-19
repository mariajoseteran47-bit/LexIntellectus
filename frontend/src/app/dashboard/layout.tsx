'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import LegalAIAgent from '@/components/ai/LegalAIAgent';
import GlobalSearch from '@/components/ui/GlobalSearch';

interface UserInfo {
    id: string;
    nombre: string;
    apellido: string;
    email: string;
    tipo_usuario: string;
    tenant_nombre?: string;
}

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const [user, setUser] = useState<UserInfo | null>(null);
    const pathname = usePathname();

    useEffect(() => {
        // Load user from localStorage
        const stored = localStorage.getItem('user');
        if (stored) {
            setUser(JSON.parse(stored));
        } else {
            window.location.href = '/login';
        }
    }, []);

    const handleLogout = () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        window.location.href = '/login';
    };

    if (!user) return null; // Or loading spinner

    return (
        <div className="min-h-screen bg-surface-50 flex">
            {/* Sidebar */}
            <aside className="w-64 bg-white border-r border-surface-200 flex flex-col fixed h-full z-10">
                {/* Logo */}
                <div className="h-16 flex items-center px-6 border-b border-surface-200">
                    <h1 className="text-lg font-bold text-primary-500">
                        Lex<span className="text-accent-400">Intellectus</span>
                    </h1>
                </div>

                {/* Navigation */}
                <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
                    <Link href="/dashboard" className={pathname === '/dashboard' ? 'sidebar-link-active' : 'sidebar-link'}>
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                        </svg>
                        Dashboard
                    </Link>
                    <Link href="/dashboard/cases" className={pathname?.startsWith('/dashboard/cases') ? 'sidebar-link-active' : 'sidebar-link'}>
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                        </svg>
                        Expedientes
                    </Link>
                    <Link href="/dashboard/agenda" className={pathname?.startsWith('/dashboard/agenda') ? 'sidebar-link-active' : 'sidebar-link'}>
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                        Agenda
                    </Link>
                    <Link href="/dashboard/documents" className={pathname?.startsWith('/dashboard/documents') ? 'sidebar-link-active' : 'sidebar-link'}>
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        Documentos
                    </Link>
                    <Link href="/dashboard/clients" className={pathname?.startsWith('/dashboard/clients') ? 'sidebar-link-active' : 'sidebar-link'}>
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-3-3h-1m-7 5h6m-6 0H7a3 3 0 01-3-3V8a3 3 0 013-3h3m0 0l3-3m0 0l3 3m-3-3v12" />
                        </svg>
                        Clientes
                    </Link>
                    <Link href="/dashboard/users" className={pathname?.startsWith('/dashboard/users') ? 'sidebar-link-active' : 'sidebar-link'}>
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                        </svg>
                        Usuarios
                    </Link>
                    <Link href="/dashboard/knowledge" className={pathname === '/dashboard/knowledge' ? 'sidebar-link-active' : 'sidebar-link'}>
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                        </svg>
                        Indexación Legal
                    </Link>

                    <div className="pt-4 mt-4 border-t border-surface-200">
                        <span className="px-4 text-xs font-semibold text-surface-400 uppercase tracking-wider">Herramientas</span>
                    </div>
                    <Link href="/dashboard/ai" className={`mt-2 ${pathname?.startsWith('/dashboard/ai') ? 'sidebar-link-active' : 'sidebar-link'}`}>
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 14.5M14.25 3.104c.251.023.501.05.75.082M19.8 14.5l-1.1 1.1a2.25 2.25 0 01-1.591.659H6.891a2.25 2.25 0 01-1.591-.659L4.2 14.5m15.6 0l.9.9m-16.5-.9l-.9.9" />
                        </svg>
                        <span className="flex items-center gap-2">
                            Asistente IA
                            <span className="badge bg-accent-400/15 text-accent-500 text-[10px]">LAA</span>
                        </span>
                    </Link>
                    <Link href="/dashboard/reports" className={pathname?.startsWith('/dashboard/reports') ? 'sidebar-link-active' : 'sidebar-link'}>
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                        </svg>
                        Reportes
                    </Link>
                    <Link href="/dashboard/audit" className={pathname?.startsWith('/dashboard/audit') ? 'sidebar-link-active' : 'sidebar-link'}>
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                        </svg>
                        Auditoría
                    </Link>
                    <Link href="/dashboard/settings" className={pathname?.startsWith('/dashboard/settings') ? 'sidebar-link-active' : 'sidebar-link'}>
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
                        </svg>
                        Configuración
                    </Link>
                </nav>

                {/* User footer */}
                <div className="p-4 border-t border-surface-200">
                    <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-full bg-gradient-judicial flex items-center justify-center text-white text-sm font-bold">
                            {user.nombre[0]}{user.apellido[0]}
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-surface-800 truncate">{user.nombre} {user.apellido}</p>
                            <p className="text-xs text-surface-400 truncate">{user.tenant_nombre || 'Despacho'}</p>
                        </div>
                        <button onClick={handleLogout} className="text-surface-400 hover:text-danger-500 transition-colors" title="Cerrar sesión">
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                            </svg>
                        </button>
                    </div>
                </div>
            </aside>

            {/* Main content wrapper */}
            <main className="flex-1 ml-64 flex flex-col min-h-screen">
                {/* Header */}
                <header className="h-16 bg-white border-b border-surface-200 flex items-center justify-between px-8 sticky top-0 z-10">
                    <div>
                        <h2 className="text-lg font-semibold text-surface-800">
                            {pathname === '/dashboard' ? 'Dashboard' :
                                pathname?.startsWith('/dashboard/cases') ? 'Expedientes' :
                                    pathname?.startsWith('/dashboard/agenda') ? 'Agenda' :
                                        pathname?.startsWith('/dashboard/documents') ? 'Documentos' :
                                            pathname?.startsWith('/dashboard/clients') ? 'Clientes' :
                                                pathname?.startsWith('/dashboard/knowledge') ? 'Indexación Legal' :
                                                    pathname?.startsWith('/dashboard/ai') ? 'Asistente IA' :
                                                        pathname?.startsWith('/dashboard/reports') ? 'Reportes' :
                                                            pathname?.startsWith('/dashboard/audit') ? 'Auditoría' :
                                                                pathname?.startsWith('/dashboard/settings') ? 'Configuración' :
                                                                    pathname?.startsWith('/dashboard/users') ? 'Usuarios' : 'LexIntellectus'}
                        </h2>
                    </div>
                    <div className="flex items-center gap-4">
                        <GlobalSearch />
                        <button className="relative text-surface-400 hover:text-surface-600 transition-colors">
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                            </svg>
                            <span className="absolute -top-1 -right-1 w-3 h-3 bg-accent-400 rounded-full border-2 border-white"></span>
                        </button>
                    </div>
                </header>

                <div className="flex-1 p-8 bg-surface-50">
                    {children}
                </div>
                <LegalAIAgent expedienteId={pathname?.startsWith('/dashboard/cases/') ? pathname.split('/').pop() : undefined} />
            </main>
        </div>
    );
}
