'use client';

import { useState } from 'react';

export default function LoginPage() {
    const [isRegister, setIsRegister] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    // Login form state
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');

    // Register form state
    const [nombre, setNombre] = useState('');
    const [apellido, setApellido] = useState('');
    const [tenantNombre, setTenantNombre] = useState('');

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const res = await fetch('/api/v1/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password }),
            });

            if (!res.ok) {
                let errorMessage = 'Error de autenticación';
                try {
                    const data = await res.json();
                    errorMessage = data.detail || errorMessage;
                } catch {
                    errorMessage = `Error del servidor (${res.status})`;
                }
                throw new Error(errorMessage);
            }

            const data = await res.json();
            localStorage.setItem('access_token', data.token.access_token);
            localStorage.setItem('refresh_token', data.token.refresh_token);
            localStorage.setItem('user', JSON.stringify(data.user));
            window.location.href = '/dashboard';
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleRegister = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const res = await fetch('/api/v1/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email,
                    password,
                    nombre,
                    apellido,
                    tenant_nombre: tenantNombre,
                }),
            });

            if (!res.ok) {
                let errorMessage = 'Error al registrar';
                try {
                    const data = await res.json();
                    errorMessage = data.detail || errorMessage;
                } catch {
                    errorMessage = `Error del servidor (${res.status})`;
                }
                throw new Error(errorMessage);
            }

            const data = await res.json();
            localStorage.setItem('access_token', data.token.access_token);
            localStorage.setItem('refresh_token', data.token.refresh_token);
            localStorage.setItem('user', JSON.stringify(data.user));
            window.location.href = '/dashboard';
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex">
            {/* Left panel — branding */}
            <div className="hidden lg:flex lg:w-1/2 bg-gradient-judicial relative overflow-hidden items-center justify-center">
                {/* Decorative elements */}
                <div className="absolute inset-0 opacity-10">
                    <div className="absolute top-20 left-20 w-64 h-64 border border-white/30 rounded-full" />
                    <div className="absolute bottom-32 right-16 w-96 h-96 border border-white/20 rounded-full" />
                    <div className="absolute top-1/2 left-1/3 w-32 h-32 border border-accent-400/40 rounded-full" />
                </div>

                <div className="relative z-10 max-w-lg px-12 text-center">
                    {/* Logo / Icon */}
                    <div className="mx-auto w-20 h-20 bg-white/10 rounded-2xl flex items-center justify-center mb-8 shadow-gold-glow animate-pulse-gold">
                        <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M20 2L4 10V18C4 28.6 10.8 38.2 20 40C29.2 38.2 36 28.6 36 18V10L20 2Z" fill="rgba(212,175,55,0.2)" stroke="#D4AF37" strokeWidth="2" />
                            <path d="M13 20L18 25L28 15" stroke="#D4AF37" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                    </div>

                    <h1 className="text-4xl font-bold text-white mb-4 tracking-tight">
                        Lex<span className="text-accent-400">Intellectus</span>
                    </h1>
                    <p className="text-primary-200 text-lg leading-relaxed">
                        ERP Legal SaaS para el sector jurídico nicaragüense.
                        Gestión procesal, notarial, financiera y asistente legal con IA.
                    </p>

                    <div className="mt-12 grid grid-cols-3 gap-6 text-center">
                        <div className="space-y-1">
                            <div className="text-accent-400 text-2xl font-bold">360°</div>
                            <div className="text-primary-300 text-xs">Gestión de Casos</div>
                        </div>
                        <div className="space-y-1">
                            <div className="text-accent-400 text-2xl font-bold">IA</div>
                            <div className="text-primary-300 text-xs">Asistente Legal</div>
                        </div>
                        <div className="space-y-1">
                            <div className="text-accent-400 text-2xl font-bold">SaaS</div>
                            <div className="text-primary-300 text-xs">Multi-tenant</div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Right panel — auth form */}
            <div className="w-full lg:w-1/2 flex items-center justify-center px-6 py-12 bg-surface-50">
                <div className="w-full max-w-md animate-fade-in">
                    {/* Mobile logo */}
                    <div className="lg:hidden text-center mb-8">
                        <h1 className="text-3xl font-bold text-primary-500">
                            Lex<span className="text-accent-400">Intellectus</span>
                        </h1>
                    </div>

                    <div className="card p-8">
                        <div className="text-center mb-8">
                            <h2 className="text-2xl font-bold text-surface-900">
                                {isRegister ? 'Crear cuenta' : 'Bienvenido'}
                            </h2>
                            <p className="mt-2 text-surface-500 text-sm">
                                {isRegister
                                    ? 'Registre su despacho para comenzar'
                                    : 'Ingrese a su plataforma legal'}
                            </p>
                        </div>

                        {error && (
                            <div className="mb-6 p-3 bg-danger-400/10 border border-danger-400/20 rounded-lg text-danger-500 text-sm animate-slide-up">
                                {error}
                            </div>
                        )}

                        <form onSubmit={isRegister ? handleRegister : handleLogin} className="space-y-5">
                            {isRegister && (
                                <>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-sm font-medium text-surface-700 mb-1.5">Nombre</label>
                                            <input
                                                type="text"
                                                value={nombre}
                                                onChange={(e) => setNombre(e.target.value)}
                                                className="input-field"
                                                placeholder="Juan"
                                                required
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-surface-700 mb-1.5">Apellido</label>
                                            <input
                                                type="text"
                                                value={apellido}
                                                onChange={(e) => setApellido(e.target.value)}
                                                className="input-field"
                                                placeholder="Pérez"
                                                required
                                            />
                                        </div>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-surface-700 mb-1.5">Nombre del Despacho</label>
                                        <input
                                            type="text"
                                            value={tenantNombre}
                                            onChange={(e) => setTenantNombre(e.target.value)}
                                            className="input-field"
                                            placeholder="Bufete Pérez & Asociados"
                                            required
                                        />
                                    </div>
                                </>
                            )}

                            <div>
                                <label className="block text-sm font-medium text-surface-700 mb-1.5">Correo electrónico</label>
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="input-field"
                                    placeholder="correo@despacho.com"
                                    required
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-surface-700 mb-1.5">Contraseña</label>
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="input-field"
                                    placeholder="••••••••"
                                    minLength={8}
                                    required
                                />
                            </div>

                            {!isRegister && (
                                <div className="flex items-center justify-between text-sm">
                                    <label className="flex items-center gap-2 text-surface-600 cursor-pointer">
                                        <input type="checkbox" className="w-4 h-4 rounded border-surface-300 text-primary-500 focus:ring-primary-500/20" />
                                        Recordarme
                                    </label>
                                    <a href="#" className="text-primary-500 hover:text-primary-600 font-medium transition-colors">
                                        ¿Olvidó su contraseña?
                                    </a>
                                </div>
                            )}

                            <button
                                type="submit"
                                disabled={loading}
                                className="btn-primary w-full flex items-center justify-center gap-2"
                            >
                                {loading ? (
                                    <svg className="animate-spin w-5 h-5" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                    </svg>
                                ) : null}
                                {loading ? 'Procesando...' : (isRegister ? 'Crear cuenta' : 'Iniciar sesión')}
                            </button>
                        </form>

                        <div className="mt-6 text-center">
                            <span className="text-surface-500 text-sm">
                                {isRegister ? '¿Ya tiene cuenta?' : '¿No tiene cuenta?'}{' '}
                            </span>
                            <button
                                onClick={() => {
                                    setIsRegister(!isRegister);
                                    setError('');
                                }}
                                className="text-primary-500 hover:text-primary-600 font-medium text-sm transition-colors"
                            >
                                {isRegister ? 'Iniciar sesión' : 'Registrar despacho'}
                            </button>
                        </div>
                    </div>

                    <p className="mt-8 text-center text-surface-400 text-xs">
                        © 2026 LexIntellectus. Todos los derechos reservados.
                    </p>
                </div>
            </div>
        </div>
    );
}
