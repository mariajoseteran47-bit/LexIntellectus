'use client';

import { useState, useEffect } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import { ShieldCheck, ShieldAlert, Copy, Check, X, Smartphone, KeyRound, Loader2 } from 'lucide-react';
import { useToast } from '@/components/ui/ToastProvider';
import { settingsService } from '@/services/settingsService';

interface MfaModalProps {
    isOpen: boolean;
    onClose: () => void;
    isCurrentlyEnabled: boolean;
    onSuccess: (newStatus: boolean) => void;
}

export default function MfaModal({ isOpen, onClose, isCurrentlyEnabled, onSuccess }: MfaModalProps) {
    const toast = useToast();
    const [loading, setLoading] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [mfaData, setMfaData] = useState<{ secret: string; qr_uri: string } | null>(null);
    const [otpCode, setOtpCode] = useState('');
    const [copied, setCopied] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        if (isOpen && !isCurrentlyEnabled) {
            setOtpCode('');
            setError('');
            initSetup();
        } else if (isOpen && isCurrentlyEnabled) {
            setOtpCode('');
            setError('');
        }
    }, [isOpen, isCurrentlyEnabled]);

    const initSetup = async () => {
        setLoading(true);
        setError('');
        try {
            const data = await settingsService.setupMfa();
            setMfaData(data);
        } catch (err: any) {
            setError(err?.response?.data?.detail || 'No se pudo generar la clave de seguridad 2FA.');
        } finally {
            setLoading(false);
        }
    };

    const handleCopySecret = () => {
        if (!mfaData?.secret) return;
        navigator.clipboard.writeText(mfaData.secret);
        setCopied(true);
        toast.success('Clave copiada', 'La clave secreta ha sido copiada al portapapeles.');
        setTimeout(() => setCopied(false), 2500);
    };

    const handleVerifyAndActivate = async (e: React.FormEvent) => {
        e.preventDefault();
        if (otpCode.length !== 6) {
            setError('Por favor ingresa un código válido de 6 dígitos.');
            return;
        }

        setSubmitting(true);
        setError('');
        try {
            await settingsService.verifyMfa(otpCode);
            toast.success('2FA Activado', 'La autenticación de dos factores ha sido activada exitosamente.');
            onSuccess(true);
            onClose();
        } catch (err: any) {
            setError(err?.response?.data?.detail || 'Código de verificación incorrecto. Intenta de nuevo.');
        } finally {
            setSubmitting(false);
        }
    };

    const handleDisableMfa = async (e: React.FormEvent) => {
        e.preventDefault();
        if (otpCode.length !== 6) {
            setError('Por favor ingresa el código de 6 dígitos para confirmar.');
            return;
        }

        setSubmitting(true);
        setError('');
        try {
            await settingsService.disableMfa(otpCode);
            toast.success('2FA Desactivado', 'La autenticación de dos factores ha sido desactivada.');
            onSuccess(false);
            onClose();
        } catch (err: any) {
            setError(err?.response?.data?.detail || 'Código incorrecto. No se pudo desactivar el 2FA.');
        } finally {
            setSubmitting(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm animate-fade-in">
            <div 
                className="relative w-full max-w-lg bg-white rounded-2xl shadow-2xl border border-surface-200 overflow-hidden"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-5 border-b border-surface-100 bg-surface-50/50">
                    <div className="flex items-center gap-3">
                        <div className={`p-2.5 rounded-xl ${isCurrentlyEnabled ? 'bg-red-50 text-red-600' : 'bg-primary-50 text-primary-600'}`}>
                            {isCurrentlyEnabled ? <ShieldAlert className="w-6 h-6" /> : <ShieldCheck className="w-6 h-6" />}
                        </div>
                        <div>
                            <h3 className="text-lg font-bold text-surface-900">
                                {isCurrentlyEnabled ? 'Desactivar Autenticación 2FA' : 'Configurar Autenticación 2FA'}
                            </h3>
                            <p className="text-xs text-surface-500">
                                {isCurrentlyEnabled 
                                    ? 'Confirma tu identidad para remover la protección'
                                    : 'Seguridad reforzada para tu cuenta de LexIntellectus'}
                            </p>
                        </div>
                    </div>
                    <button 
                        onClick={onClose}
                        className="p-1.5 rounded-lg text-surface-400 hover:text-surface-600 hover:bg-surface-100 transition-colors"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Content */}
                <div className="p-6 space-y-6 max-h-[80vh] overflow-y-auto">
                    {error && (
                        <div className="p-3.5 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-center gap-2">
                            <span className="font-semibold">Error:</span> {error}
                        </div>
                    )}

                    {!isCurrentlyEnabled ? (
                        /* ACTIVATION FLOW */
                        loading ? (
                            <div className="py-12 flex flex-col items-center justify-center space-y-3">
                                <Loader2 className="w-8 h-8 text-primary-600 animate-spin" />
                                <p className="text-sm text-surface-500 font-medium">Generando código de seguridad...</p>
                            </div>
                        ) : (
                            <form onSubmit={handleVerifyAndActivate} className="space-y-6">
                                {/* Step 1: QR */}
                                <div className="space-y-3">
                                    <div className="flex items-center gap-2 text-sm font-semibold text-surface-800">
                                        <div className="w-5 h-5 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center text-xs">1</div>
                                        <span>Escanea el código QR con tu aplicación</span>
                                    </div>
                                    <p className="text-xs text-surface-500">
                                        Abre Google Authenticator, Authy, Microsoft Authenticator o 1Password en tu celular y escanea:
                                    </p>
                                    <div className="flex justify-center p-4 bg-white rounded-xl border border-surface-200 shadow-sm w-fit mx-auto">
                                        {mfaData?.qr_uri && (
                                            <QRCodeSVG 
                                                value={mfaData.qr_uri} 
                                                size={170}
                                                level="M"
                                                includeMargin={true}
                                            />
                                        )}
                                    </div>
                                </div>

                                {/* Step 2: Manual Key */}
                                <div className="space-y-2">
                                    <div className="flex items-center gap-2 text-sm font-semibold text-surface-800">
                                        <div className="w-5 h-5 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center text-xs">2</div>
                                        <span>O ingresa la clave manualmente</span>
                                    </div>
                                    <div className="flex items-center gap-2 p-2.5 rounded-lg bg-surface-100 border border-surface-200">
                                        <KeyRound className="w-4 h-4 text-surface-500 flex-shrink-0" />
                                        <span className="font-mono text-xs font-semibold text-surface-800 tracking-wider select-all flex-1 truncate">
                                            {mfaData?.secret || 'Cargando...'}
                                        </span>
                                        <button
                                            type="button"
                                            onClick={handleCopySecret}
                                            className="px-2.5 py-1 text-xs font-medium text-primary-700 bg-white hover:bg-primary-50 border border-surface-200 rounded-md transition-colors flex items-center gap-1"
                                        >
                                            {copied ? <Check className="w-3.5 h-3.5 text-green-600" /> : <Copy className="w-3.5 h-3.5" />}
                                            {copied ? 'Copiado' : 'Copiar'}
                                        </button>
                                    </div>
                                </div>

                                {/* Step 3: Confirmation Code */}
                                <div className="space-y-2 pt-2 border-t border-surface-100">
                                    <div className="flex items-center gap-2 text-sm font-semibold text-surface-800">
                                        <div className="w-5 h-5 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center text-xs">3</div>
                                        <span>Ingresa el código de 6 dígitos</span>
                                    </div>
                                    <div className="max-w-xs mx-auto">
                                        <input
                                            type="text"
                                            inputMode="numeric"
                                            pattern="[0-9]*"
                                            maxLength={6}
                                            placeholder="000000"
                                            value={otpCode}
                                            onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ''))}
                                            className="w-full py-3 px-4 text-center font-mono text-2xl font-bold tracking-[0.4em] rounded-xl border-2 border-primary-200 focus:border-primary-500 focus:ring-4 focus:ring-primary-500/10 transition-all outline-none"
                                            autoFocus
                                        />
                                    </div>
                                </div>

                                {/* Footer */}
                                <div className="flex items-center justify-end gap-3 pt-4 border-t border-surface-100">
                                    <button
                                        type="button"
                                        onClick={onClose}
                                        className="px-4 py-2 text-sm font-medium text-surface-600 hover:text-surface-800 hover:bg-surface-100 rounded-lg transition-colors"
                                    >
                                        Cancelar
                                    </button>
                                    <button
                                        type="submit"
                                        disabled={submitting || otpCode.length !== 6}
                                        className="btn-primary py-2.5 px-6 text-sm font-medium rounded-lg disabled:opacity-50 flex items-center gap-2 shadow-md"
                                    >
                                        {submitting && <Loader2 className="w-4 h-4 animate-spin" />}
                                        Verificar y Activar
                                    </button>
                                </div>
                            </form>
                        )
                    ) : (
                        /* DISABLE FLOW */
                        <form onSubmit={handleDisableMfa} className="space-y-5">
                            <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-sm space-y-1">
                                <p className="font-semibold flex items-center gap-1.5">
                                    <ShieldAlert className="w-4 h-4 text-amber-700" />
                                    Advertencia de seguridad
                                </p>
                                <p className="text-xs text-amber-800">
                                    Al desactivar el 2FA, tu cuenta quedará protegida únicamente con tu contraseña.
                                </p>
                            </div>

                            <div className="space-y-2">
                                <label className="block text-sm font-medium text-surface-700">
                                    Ingresa el código TOTP de tu app autenticadora para confirmar:
                                </label>
                                <div className="max-w-xs mx-auto">
                                    <input
                                        type="text"
                                        inputMode="numeric"
                                        pattern="[0-9]*"
                                        maxLength={6}
                                        placeholder="000000"
                                        value={otpCode}
                                        onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ''))}
                                        className="w-full py-3 px-4 text-center font-mono text-2xl font-bold tracking-[0.4em] rounded-xl border-2 border-surface-300 focus:border-red-500 focus:ring-4 focus:ring-red-500/10 transition-all outline-none"
                                        autoFocus
                                    />
                                </div>
                            </div>

                            <div className="flex items-center justify-end gap-3 pt-4 border-t border-surface-100">
                                <button
                                    type="button"
                                    onClick={onClose}
                                    className="px-4 py-2 text-sm font-medium text-surface-600 hover:text-surface-800 hover:bg-surface-100 rounded-lg transition-colors"
                                >
                                    Cancelar
                                </button>
                                <button
                                    type="submit"
                                    disabled={submitting || otpCode.length !== 6}
                                    className="bg-red-600 hover:bg-red-700 text-white font-medium py-2.5 px-6 text-sm rounded-lg transition-colors disabled:opacity-50 flex items-center gap-2 shadow-md"
                                >
                                    {submitting && <Loader2 className="w-4 h-4 animate-spin" />}
                                    Desactivar 2FA
                                </button>
                            </div>
                        </form>
                    )}
                </div>
            </div>
        </div>
    );
}
