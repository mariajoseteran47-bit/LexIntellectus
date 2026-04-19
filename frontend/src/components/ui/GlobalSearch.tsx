'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Search, X, FileText, Calendar, Users, Briefcase, Bot, ArrowRight } from 'lucide-react';
import api from '@/lib/api';

interface SearchResult {
    id: string;
    type: 'case' | 'deadline' | 'document' | 'client';
    title: string;
    subtitle?: string;
    href: string;
}

// Quick navigation items (always shown when search is empty)
const quickNavigation = [
    { label: 'Nuevo Expediente', icon: Briefcase, href: '/dashboard/cases/new', color: 'text-blue-500' },
    { label: 'Ver Agenda', icon: Calendar, href: '/dashboard/agenda', color: 'text-amber-500' },
    { label: 'Consultar IA', icon: Bot, href: '/dashboard/ai', color: 'text-violet-500' },
    { label: 'Gestionar Clientes', icon: Users, href: '/dashboard/clients', color: 'text-pink-500' },
];

export default function GlobalSearch() {
    const [isOpen, setIsOpen] = useState(false);
    const [query, setQuery] = useState('');
    const [results, setResults] = useState<SearchResult[]>([]);
    const [loading, setLoading] = useState(false);
    const [selectedIndex, setSelectedIndex] = useState(0);

    const inputRef = useRef<HTMLInputElement>(null);
    const router = useRouter();

    // Open with Ctrl+K / Cmd+K
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
                e.preventDefault();
                setIsOpen(true);
            }
            if (e.key === 'Escape') {
                setIsOpen(false);
            }
        };
        document.addEventListener('keydown', handleKeyDown);
        return () => document.removeEventListener('keydown', handleKeyDown);
    }, []);

    // Focus input when opened
    useEffect(() => {
        if (isOpen && inputRef.current) {
            setTimeout(() => inputRef.current?.focus(), 100);
        }
        if (!isOpen) {
            setQuery('');
            setResults([]);
            setSelectedIndex(0);
        }
    }, [isOpen]);

    // Search debounced
    useEffect(() => {
        if (!query.trim()) {
            setResults([]);
            return;
        }

        const timer = setTimeout(async () => {
            setLoading(true);
            try {
                // Search cases
                const { data: casesData } = await api.get('/cases', {
                    params: { search: query, size: 5 }
                });
                const caseResults: SearchResult[] = (casesData.items || []).map((c: any) => ({
                    id: c.id,
                    type: 'case' as const,
                    title: c.resumen || c.numero_interno || 'Sin título',
                    subtitle: `${c.ramo} · ${c.numero_causa || 'Sin causa'}`,
                    href: `/dashboard/cases/${c.id}`,
                }));

                setResults(caseResults);
                setSelectedIndex(0);
            } catch (e) {
                console.error('Search failed', e);
            } finally {
                setLoading(false);
            }
        }, 300);

        return () => clearTimeout(timer);
    }, [query]);

    // Keyboard navigation
    const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
        const items = query.trim() ? results : quickNavigation;
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            setSelectedIndex(prev => Math.min(prev + 1, items.length - 1));
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            setSelectedIndex(prev => Math.max(prev - 1, 0));
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (query.trim() && results[selectedIndex]) {
                router.push(results[selectedIndex].href);
                setIsOpen(false);
            } else if (!query.trim() && quickNavigation[selectedIndex]) {
                router.push(quickNavigation[selectedIndex].href);
                setIsOpen(false);
            }
        }
    }, [query, results, selectedIndex, router]);

    const typeIcons: Record<string, typeof FileText> = {
        case: Briefcase,
        deadline: Calendar,
        document: FileText,
        client: Users,
    };

    if (!isOpen) {
        return (
            <button
                onClick={() => setIsOpen(true)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-surface-200 bg-surface-50 text-sm text-surface-400 hover:bg-surface-100 hover:text-surface-600 transition-all w-64"
            >
                <Search className="w-4 h-4" />
                <span className="flex-1 text-left">Buscar...</span>
                <kbd className="hidden sm:inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[10px] font-mono bg-surface-200 text-surface-500 rounded">
                    Ctrl K
                </kbd>
            </button>
        );
    }

    return (
        <>
            {/* Backdrop */}
            <div
                className="fixed inset-0 bg-black/40 z-50 animate-fade-in"
                onClick={() => setIsOpen(false)}
            />

            {/* Search Modal */}
            <div className="fixed inset-x-0 top-[15%] z-50 flex justify-center px-4 animate-slide-up">
                <div className="w-full max-w-xl bg-white rounded-2xl shadow-2xl border border-surface-200 overflow-hidden">
                    {/* Search Input */}
                    <div className="flex items-center gap-3 px-5 py-4 border-b border-surface-100">
                        <Search className={`w-5 h-5 ${loading ? 'text-primary-500 animate-pulse' : 'text-surface-400'}`} />
                        <input
                            ref={inputRef}
                            type="text"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Buscar expedientes, plazos, documentos..."
                            className="flex-1 text-sm text-surface-800 placeholder:text-surface-400 outline-none bg-transparent"
                            autoFocus
                        />
                        {query && (
                            <button onClick={() => setQuery('')} className="text-surface-400 hover:text-surface-600">
                                <X className="w-4 h-4" />
                            </button>
                        )}
                        <button
                            onClick={() => setIsOpen(false)}
                            className="text-xs text-surface-400 px-1.5 py-0.5 rounded border border-surface-200 hover:bg-surface-50"
                        >
                            ESC
                        </button>
                    </div>

                    {/* Results */}
                    <div className="max-h-[50vh] overflow-y-auto">
                        {/* Quick Navigation (when no query) */}
                        {!query.trim() && (
                            <div className="p-3">
                                <p className="text-xs font-semibold text-surface-400 uppercase tracking-wider px-2 mb-2">Acceso Rápido</p>
                                {quickNavigation.map((item, i) => (
                                    <button
                                        key={item.label}
                                        onClick={() => { router.push(item.href); setIsOpen(false); }}
                                        className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                                            selectedIndex === i ? 'bg-primary-50 text-primary-700' : 'text-surface-600 hover:bg-surface-50'
                                        }`}
                                    >
                                        <item.icon className={`w-4 h-4 ${item.color}`} />
                                        <span className="font-medium">{item.label}</span>
                                        <ArrowRight
                                            className={`w-3 h-3 ml-auto transition-opacity ${
                                                selectedIndex === i ? 'opacity-100 text-primary-400' : 'opacity-0'
                                            }`}
                                        />
                                    </button>
                                ))}
                            </div>
                        )}

                        {/* Search Results */}
                        {query.trim() && !loading && results.length > 0 && (
                            <div className="p-3">
                                <p className="text-xs font-semibold text-surface-400 uppercase tracking-wider px-2 mb-2">
                                    {results.length} resultado(s)
                                </p>
                                {results.map((result, i) => {
                                    const Icon = typeIcons[result.type] || FileText;
                                    return (
                                        <button
                                            key={result.id}
                                            onClick={() => { router.push(result.href); setIsOpen(false); }}
                                            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                                                selectedIndex === i ? 'bg-primary-50 text-primary-700' : 'text-surface-600 hover:bg-surface-50'
                                            }`}
                                        >
                                            <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                                                selectedIndex === i ? 'bg-primary-100' : 'bg-surface-100'
                                            }`}>
                                                <Icon className="w-4 h-4" />
                                            </div>
                                            <div className="flex-1 min-w-0 text-left">
                                                <p className="font-medium truncate">{result.title}</p>
                                                {result.subtitle && (
                                                    <p className="text-xs text-surface-400 truncate">{result.subtitle}</p>
                                                )}
                                            </div>
                                            <ArrowRight
                                                className={`w-3 h-3 flex-shrink-0 transition-opacity ${
                                                    selectedIndex === i ? 'opacity-100 text-primary-400' : 'opacity-0'
                                                }`}
                                            />
                                        </button>
                                    );
                                })}
                            </div>
                        )}

                        {/* No results */}
                        {query.trim() && !loading && results.length === 0 && (
                            <div className="px-5 py-8 text-center">
                                <Search className="w-8 h-8 text-surface-200 mx-auto mb-2" />
                                <p className="text-sm text-surface-500">No se encontraron resultados para &quot;{query}&quot;</p>
                                <p className="text-xs text-surface-400 mt-1">Intenta con otro término de búsqueda</p>
                            </div>
                        )}

                        {/* Loading */}
                        {loading && (
                            <div className="px-5 py-6 text-center">
                                <div className="w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto" />
                                <p className="text-xs text-surface-400 mt-2">Buscando...</p>
                            </div>
                        )}
                    </div>

                    {/* Footer */}
                    <div className="px-5 py-2.5 border-t border-surface-100 bg-surface-50/50 flex items-center gap-4 text-[10px] text-surface-400">
                        <span className="flex items-center gap-1"><kbd className="px-1 py-0.5 rounded bg-surface-200">↑↓</kbd> navegar</span>
                        <span className="flex items-center gap-1"><kbd className="px-1 py-0.5 rounded bg-surface-200">↵</kbd> abrir</span>
                        <span className="flex items-center gap-1"><kbd className="px-1 py-0.5 rounded bg-surface-200">esc</kbd> cerrar</span>
                    </div>
                </div>
            </div>
        </>
    );
}
