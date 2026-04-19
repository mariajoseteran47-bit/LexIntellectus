import { useState } from 'react';
import { Users, Plus, Trash2, ShieldCheck, FileText, CheckCircle2 } from 'lucide-react';
import api from '@/lib/api';
import { useToast } from '@/components/ui/ToastProvider';

interface BoardMember {
    id: string;
    nombre_completo: string;
    cargo: string;
    numero_acta_nombramiento?: string;
    activo: boolean;
}

interface Props {
    profileId: string;
    boardMembers: BoardMember[];
    onRefresh: () => void;
}

export default function JuntaDirectivaAdmin({ profileId, boardMembers, onRefresh }: Props) {
    const [isAdding, setIsAdding] = useState(false);
    const [loading, setLoading] = useState(false);
    const [formData, setFormData] = useState({
        nombre_completo: '',
        cargo: 'presidente',
        numero_acta_nombramiento: '',
        activo: true
    });
    const toast = useToast();

    const handleAdd = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            await api.post(`/clients/profiles/${profileId}/board-members`, formData);
            toast.success('Miembro agregado a la Junta Directiva');
            setIsAdding(false);
            setFormData({ nombre_completo: '', cargo: 'presidente', numero_acta_nombramiento: '', activo: true });
            onRefresh();
        } catch (error) {
            toast.error('Error al agregar miembro');
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm('¿Eliminar este miembro de la Junta Directiva?')) return;
        try {
            await api.delete(`/clients/board-members/${id}`);
            toast.success('Miembro eliminado');
            onRefresh();
        } catch (error) {
            toast.error('Error al eliminar miembro');
        }
    };

    return (
        <div className="mt-4">
            <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-bold text-surface-700 flex items-center gap-2">
                    <Users className="w-4 h-4 text-primary-500" /> Junta Directiva
                </h4>
                <button
                    onClick={() => setIsAdding(!isAdding)}
                    className="text-xs font-medium text-primary-600 hover:text-primary-700 flex items-center gap-1"
                >
                    <Plus className="w-3.5 h-3.5" /> Agregar Miembro
                </button>
            </div>

            {isAdding && (
                <form onSubmit={handleAdd} className="p-4 bg-primary-50/50 rounded-lg border border-primary-200 mb-3 space-y-3 animate-fade-in">
                    <div className="grid grid-cols-2 gap-3">
                        <div className="space-y-1">
                            <label className="text-[10px] font-bold text-surface-500 uppercase tracking-wider">Nombre Completo *</label>
                            <input type="text" required className="input w-full text-sm" placeholder="Ej: Maria Lopez"
                                value={formData.nombre_completo} onChange={e => setFormData({ ...formData, nombre_completo: e.target.value })} />
                        </div>
                        <div className="space-y-1">
                            <label className="text-[10px] font-bold text-surface-500 uppercase tracking-wider">Cargo *</label>
                            <select className="input w-full text-sm" required
                                value={formData.cargo} onChange={e => setFormData({ ...formData, cargo: e.target.value })}>
                                <option value="presidente">Presidente</option>
                                <option value="vicepresidente">Vicepresidente</option>
                                <option value="secretario">Secretario</option>
                                <option value="tesorero">Tesorero</option>
                                <option value="vocal">Vocal</option>
                                <option value="fiscal">Fiscal</option>
                                <option value="otro">Otro</option>
                            </select>
                        </div>
                        <div className="space-y-1">
                            <label className="text-[10px] font-bold text-surface-500 uppercase tracking-wider">Acta Nombramiento (Opcional)</label>
                            <input type="text" className="input w-full text-sm" placeholder="N° de acta"
                                value={formData.numero_acta_nombramiento} onChange={e => setFormData({ ...formData, numero_acta_nombramiento: e.target.value })} />
                        </div>
                        <div className="flex items-center gap-2 mt-5">
                            <label className="flex items-center gap-2 cursor-pointer text-sm font-medium text-surface-700">
                                <input type="checkbox" className="rounded border-surface-300 text-primary-600"
                                    checked={formData.activo} onChange={e => setFormData({ ...formData, activo: e.target.checked })} />
                                <CheckCircle2 className="w-4 h-4 text-green-500" /> Miembro Activo
                            </label>
                        </div>
                    </div>
                    <div className="flex justify-end gap-2 pt-2">
                        <button type="button" onClick={() => setIsAdding(false)} className="btn btn-sm btn-outline">Cancelar</button>
                        <button type="submit" disabled={loading} className="btn btn-sm btn-primary">
                            {loading ? 'Guardando...' : 'Guardar Miembro'}
                        </button>
                    </div>
                </form>
            )}

            {!boardMembers || boardMembers.length === 0 ? (
                <p className="text-xs text-surface-400 italic p-3 bg-surface-50 rounded-lg">No hay miembros de junta directiva registrados.</p>
            ) : (
                <div className="space-y-2">
                    {boardMembers.map(miembro => (
                        <div key={miembro.id} className="p-3 bg-white rounded-lg border border-surface-200 flex items-center justify-between group">
                            <div>
                                <p className="font-semibold text-surface-800">{miembro.nombre_completo}</p>
                                <p className="text-xs text-surface-500 mt-0.5 capitalize flex items-center gap-1">
                                    <ShieldCheck className="w-3 h-3 text-surface-400" /> {miembro.cargo}
                                    {miembro.numero_acta_nombramiento && (
                                        <><FileText className="w-3 h-3 text-surface-400 ml-1" /> Acta N° {miembro.numero_acta_nombramiento}</>
                                    )}
                                </p>
                            </div>
                            <div className="flex items-center gap-3">
                                <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded ${miembro.activo ? 'text-green-600 bg-green-50' : 'text-surface-500 bg-surface-100'}`}>
                                    {miembro.activo ? 'Activo' : 'Inactivo'}
                                </span>
                                <button onClick={() => handleDelete(miembro.id)}
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
