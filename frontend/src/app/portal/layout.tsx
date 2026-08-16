'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

interface UserInfo {
    id: string;
    nombre: string;
    apellido: string;
    email: string;
    tipo_usuario: string;
}

export default function PortalLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const [user, setUser] = useState<UserInfo | null>(null);
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
    const pathname = usePathname();

    useEffect(() => {
        const stored = localStorage.getItem('user');
        if (stored) {
            const parsedUser = JSON.parse(stored) as UserInfo;
            if (parsedUser.tipo_usuario !== 'cliente') {
                // If not a client, kick out to normal dashboard
                window.location.href = '/dashboard';
            } else {
                setUser(parsedUser);
            }
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

    if (!user) {
        return (
            <div className="min-h-screen bg-slate-950 flex items-center justify-center text-white">
                <div className="text-center space-y-4">
                    <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-amber-500 mx-auto"></div>
                    <p className="text-slate-400 font-medium">Verificando credenciales...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-amber-500/30 selection:text-amber-200">
            {/* Background elements */}
            <div className="absolute top-0 left-0 right-0 h-[500px] bg-gradient-to-b from-amber-500/5 to-transparent pointer-events-none z-0" />
            <div className="absolute top-[20%] right-[10%] w-[300px] h-[300px] bg-amber-500/5 rounded-full filter blur-[120px] pointer-events-none z-0" />

            {/* Mobile Header */}
            <header className="lg:hidden h-16 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-xl flex items-center justify-between px-6 sticky top-0 z-40">
                <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                    <span className="text-amber-400">🏛️</span>
                    <span>Portal<span className="text-amber-400 font-semibold">Cliente</span></span>
                </h1>
                <button
                    className="p-2 text-slate-400 hover:text-white transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-amber-500/50 rounded-lg"
                    onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                >
                    {isMobileMenuOpen ? (
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    ) : (
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16m-7 6h7" />
                        </svg>
                    )}
                </button>
            </header>

            {/* Mobile Menu Backdrop */}
            {isMobileMenuOpen && (
                <div
                    className="fixed inset-0 bg-slate-950/75 backdrop-blur-md z-45 lg:hidden transition-opacity duration-300"
                    onClick={() => setIsMobileMenuOpen(false)}
                />
            )}

            <div className="flex flex-1 z-10">
                {/* Sidebar */}
                <aside className={`fixed lg:sticky top-0 h-[calc(100vh-4rem)] lg:h-screen w-72 bg-slate-900/90 backdrop-blur-xl border-r border-slate-800/80 flex flex-col z-48 transition-transform duration-300 lg:translate-x-0 ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}`}>
                    {/* Brand */}
                    <div className="hidden lg:flex h-20 items-center justify-center border-b border-slate-800/80">
                        <Link href="/portal" className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                            <span className="text-amber-400 text-3xl">🏛️</span>
                            <span>Lex<span className="text-amber-400">Portal</span></span>
                        </Link>
                    </div>

                    {/* User profile brief */}
                    <div className="p-6 border-b border-slate-800/60 bg-slate-950/40">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-amber-600 to-amber-400 flex items-center justify-center font-bold text-slate-950">
                                {user.nombre[0].toUpperCase()}
                            </div>
                            <div className="min-w-0">
                                <h3 className="text-sm font-semibold text-white truncate">{user.nombre} {user.apellido}</h3>
                                <p className="text-xs text-slate-400 truncate">{user.email}</p>
                                <span className="mt-1.5 inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                                    Cliente VIP
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* Navigation */}
                    <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
                        <Link
                            href="/portal"
                            className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${pathname === '/portal' ? 'bg-amber-500/10 text-amber-400 border-l-2 border-amber-400 shadow-md shadow-amber-500/5' : 'text-slate-400 hover:text-white hover:bg-slate-800/50'}`}
                            onClick={() => setIsMobileMenuOpen(false)}
                        >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                            </svg>
                            Resumen Portal
                        </Link>
                        <Link
                            href="/portal/cases"
                            className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${pathname === '/portal/cases' ? 'bg-amber-500/10 text-amber-400 border-l-2 border-amber-400 shadow-md shadow-amber-500/5' : 'text-slate-400 hover:text-white hover:bg-slate-800/50'}`}
                            onClick={() => setIsMobileMenuOpen(false)}
                        >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                            </svg>
                            Mis Expedientes
                        </Link>
                        <Link
                            href="/portal/documents"
                            className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${pathname === '/portal/documents' ? 'bg-amber-500/10 text-amber-400 border-l-2 border-amber-400 shadow-md shadow-amber-500/5' : 'text-slate-400 hover:text-white hover:bg-slate-800/50'}`}
                            onClick={() => setIsMobileMenuOpen(false)}
                        >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            Bóveda Documental
                        </Link>
                        <Link
                            href="/portal/billing"
                            className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${pathname === '/portal/billing' ? 'bg-amber-500/10 text-amber-400 border-l-2 border-amber-400 shadow-md shadow-amber-500/5' : 'text-slate-400 hover:text-white hover:bg-slate-800/50'}`}
                            onClick={() => setIsMobileMenuOpen(false)}
                        >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            Estado de Cuenta / Pagos
                        </Link>
                    </nav>

                    {/* Footer / Logout */}
                    <div className="p-4 border-t border-slate-800/60 bg-slate-950/20">
                        <button
                            onClick={handleLogout}
                            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-rose-500/15 hover:text-rose-400 text-slate-300 border border-slate-700/60 hover:border-rose-500/25 transition-all duration-200"
                        >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                            </svg>
                            Cerrar Sesión
                        </button>
                    </div>
                </aside>

                {/* Main Content Area */}
                <main className="flex-1 min-w-0 min-h-screen px-6 py-8 lg:p-12 z-10 overflow-y-auto">
                    {children}
                </main>
            </div>
        </div>
    );
}
