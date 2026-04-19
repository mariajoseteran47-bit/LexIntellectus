import { useState } from 'react';
import { Building2, Plus, Trash2, ShieldAlert } from 'lucide-react';
import api from '@/lib/api';
import { useToast } from '@/components/ui/ToastProvider';

interface Shareholder {
    id: string;
    tipo_accionista: string;
    nombre_completo: string;
    numero_acciones?: number;
    porcentaje_participacion?: number;
    es_beneficiario_final: boolean;
}

interface Props {
    profileId: string;
    shareholders: Shareholder[];
    onRefresh: () => void;
}

export default function AccionistasAdmin({ profileId, shareholders, onRefresh }: Props) {
    const [isAdding, setIsAdding] = useState(false);
    const [loading, setLoading] = useState(false);
    const [formData, setFormData] = useState({
        nombre_completo: '',
        tipo_accionista: 'natural',
        numero_acciones: '',
        porcentaje_participacion: '',
        es_beneficiario_final: false
    });
    const toast = useToast();

    const handleAdd = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            const payload = {
                ...formData,
                numero_acciones: formData.numero_acciones ? parseInt(formData.numero_acciones) : undefined,
                porcentaje_participacion: formData.porcentaje_participacion ? parseFloat(formData.porcentaje_participacion) : undefined
            };
            await api.post(`/clients/profiles/${profileId}/shareholders`, payload);
            toast.success('Accionista registrado correctamente');
            setIsAdding(false);
            setFormData({ nombre_completo: '', tipo_accionista: 'natural', numero_acciones: '', porcentaje_participacion: '', es_beneficiario_final: false });
            onRefresh();
        } catch (error) {
            toast.error('Error al registrar accionista');
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm('¿Eliminar este accionista?')) return;
        try {
            await api.delete(`/clients/shareholders/${id}`);
            toast.success('Accionista eliminado');
            onRefresh();
        } catch (error) {
            toast.error('Error al eliminar accionista');
        }
    };

    return (
        <div className="mt-4">
            <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-bold text-surface-700 flex items-center gap-2">
                    <Building2 className="w-4 h-4 text-primary-500" /> Composición Accionaria
                </h4>
                <button
                    onClick={() => setIsAdding(!isAdding)}
                    className="text-xs font-medium text-primary-600 hover:text-primary-700 flex items-center gap-1"
                >
                    <Plus className="w-3.5 h-3.5" /> Nuevo Accionista
                </button>
            </div>

            {isAdding && (
                <form onSubmit={handleAdd} className="p-4 bg-primary-50/50 rounded-lg border border-primary-200 mb-3 space-y-3 animate-fade-in">
                    <div className="grid grid-cols-2 gap-3">
                        <div className="space-y-1 col-span-2 sm:col-span-1">
                            <label className="text-[10px] font-bold text-surface-500 uppercase tracking-wider">Nombre Completo *</label>
                            <input type="text" required className="input w-full text-sm" placeholder="Ej: Inversiones ABC S.A."
                                value={formData.nombre_completo} onChange={e => setFormData({ ...formData, nombre_completo: e.target.value })} />
                        </div>
                        <div className="space-y-1 col-span-2 sm:col-span-1">
                            <label className="text-[10px] font-bold text-surface-500 uppercase tracking-wider">Tipo *</label>
                            <select className="input w-full text-sm" required
                                value={formData.tipo_accionista} onChange={e => setFormData({ ...formData, tipo_accionista: e.target.value })}>
                                <option value="natural">Persona Natural</option>
                                <option value="juridica">Persona Jurídica</option>
                            </select>
                        </div>
                        <div className="space-y-1">
                            <label className="text-[10px] font-bold text-surface-500 uppercase tracking-wider">N° de Acciones</label>
                            <input type="number" min="0" className="input w-full text-sm" placeholder="Ej: 1000"
                                value={formData.numero_acciones} onChange={e => setFormData({ ...formData, numero_acciones: e.target.value })} />
                        </div>
                        <div className="space-y-1">
                            <label className="text-[10px] font-bold text-surface-500 uppercase tracking-wider">% Participación</label>
                            <input type="number" min="0" max="100" step="0.01" className="input w-full text-sm" placeholder="Ej: 51.5"
                                value={formData.porcentaje_participacion} onChange={e => setFormData({ ...formData, porcentaje_participacion: e.target.value })} />
                        </div>
                        <div className="col-span-2 flex items-center gap-2 mt-2">
                            <label className="flex items-center gap-2 cursor-pointer text-[11px] font-bold text-amber-700 bg-amber-50 px-3 py-2 rounded-lg border border-amber-200 w-full hover:bg-amber-100 transition-colors">
                                <input type="checkbox" className="rounded border-amber-300 text-amber-600 focus:ring-amber-500"
                                    checked={formData.es_beneficiario_final} onChange={e => setFormData({ ...formData, es_beneficiario_final: e.target.checked })} />
                                <ShieldAlert className="w-4 h-4 text-amber-500" /> Confirmar como Beneficiario Final (UAF / Ley 977)
                            </label>
                        </div>
                    </div>
                    <div className="flex justify-end gap-2 pt-2">
                        <button type="button" onClick={() => setIsAdding(false)} className="btn btn-sm btn-outline">Cancelar</button>
                        <button type="submit" disabled={loading} className="btn btn-sm btn-primary">
                            {loading ? 'Guardando...' : 'Guardar Accionista'}
                        </button>
                    </div>
                </form>
            )}

            {!shareholders || shareholders.length === 0 ? (
                <p className="text-xs text-surface-400 italic p-3 bg-surface-50 rounded-lg">No hay accionistas registrados.</p>
            ) : (
                <div className="space-y-2">
                    {shareholders.map(socio => (
                        <div key={socio.id} className="p-3 bg-white rounded-lg border border-surface-200 flex items-center justify-between group">
                            <div>
                                <p className="font-semibold text-surface-800 flex items-center gap-2">
                                    {socio.nombre_completo}
                                    <span className="text-[10px] font-bold text-surface-500 bg-surface-100 px-1.5 py-0.5 rounded capitalize">
                                        {socio.tipo_accionista}
                                    </span>
                                    {socio.es_beneficiario_final && (
                                        <span className="text-[10px] font-bold bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded" title="Beneficiario Final (Ley 977)">BF</span>
                                    )}
                                </p>
                                <p className="text-xs text-surface-500 mt-0.5">
                                    {socio.numero_acciones ? `${socio.numero_acciones} acciones` : `${socio.porcentaje_participacion}% participación`}
                                </p>
                            </div>
                            <div className="flex items-center gap-3">
                                <span className="text-sm font-bold text-primary-600">
                                    {socio.porcentaje_participacion ? `${socio.porcentaje_participacion}%` : ''}
                                </span>
                                <button onClick={() => handleDelete(socio.id)}
                                    className="p-1.5 rounded-lg text-surface-300 hover:bg-red-50 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity" title="Eliminar">
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
