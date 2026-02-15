'use client';

import { useState, useEffect } from 'react';
import { Plus, Clock, AlertCircle, X, Check } from 'lucide-react';
import { deadlineService, Deadline, CreateDeadlineDto } from '@/services/deadlineService';

interface DeadlineListProps {
    caseId: string;
}

export default function DeadlineList({ caseId }: DeadlineListProps) {
    const [deadlines, setDeadlines] = useState<Deadline[]>([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [submitting, setSubmitting] = useState(false);

    // Form State
    const [formData, setFormData] = useState<Partial<CreateDeadlineDto>>({
        prioridad: 'normal',
        tipo_plazo: 'procesal',
        dias_tipo: 'habiles',
        hora_vencimiento: '23:59:59',
    });

    const fetchDeadlines = async () => {
        setLoading(true);
        try {
            const data = await deadlineService.getByCaseId(caseId);
            setDeadlines(data);
        } catch (error) {
            console.error('Failed to fetch deadlines', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (caseId) fetchDeadlines();
    }, [caseId]);

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setSubmitting(true);
        try {
            await deadlineService.create({
                expediente_id: caseId,
                descripcion: formData.descripcion!,
                fecha_vencimiento: formData.fecha_vencimiento!,
                tipo_plazo: formData.tipo_plazo || 'procesal',
                prioridad: formData.prioridad || 'normal',
                hora_vencimiento: formData.hora_vencimiento,
                base_legal: formData.base_legal,
            } as CreateDeadlineDto);

            setShowModal(false);
            setFormData({
                prioridad: 'normal',
                tipo_plazo: 'procesal',
                dias_tipo: 'habiles',
                hora_vencimiento: '23:59:59'
            });
            fetchDeadlines();
        } catch (error) {
            console.error('Failed to create deadline', error);
            alert('Error al crear plazo');
        } finally {
            setSubmitting(false);
        }
    };

    // Helper to determine status color
    const getStatusBadge = (d: Deadline) => {
        const today = new Date();
        const dueDate = new Date(d.fecha_vencimiento);
        const diffTime = dueDate.getTime() - today.getTime();
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

        if (d.status === 'cumplido') return <span className="badge bg-green-100 text-green-700">Cumplido</span>;
        if (d.status === 'cancelado') return <span className="badge bg-gray-100 text-gray-700">Cancelado</span>;

        if (diffDays < 0) return <span className="badge bg-red-100 text-red-700 font-bold">Vencido</span>;
        if (diffDays <= 3) return <span className="badge bg-orange-100 text-orange-700 font-bold">Próximo ({diffDays}d)</span>;

        return <span className="badge bg-blue-50 text-blue-700">Pendiente</span>;
    };

    return (
        <div className="card overflow-hidden">
            <div className="p-4 border-b border-surface-200 flex justify-between items-center bg-surface-50">
                <h3 className="font-semibold text-surface-800 flex items-center gap-2">
                    <Clock className="w-4 h-4" /> Plazos Fatales
                </h3>
                <button onClick={() => setShowModal(true)} className="btn btn-sm btn-outline gap-2">
                    <Plus className="w-4 h-4" /> Nuevo Plazo
                </button>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                    <thead className="bg-white border-b border-surface-200">
                        <tr>
                            <th className="px-6 py-3 font-semibold text-surface-600">Descripción / Base Legal</th>
                            <th className="px-6 py-3 font-semibold text-surface-600">Vencimiento</th>
                            <th className="px-6 py-3 font-semibold text-surface-600">Prioridad</th>
                            <th className="px-6 py-3 font-semibold text-surface-600">Estado</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-surface-100">
                        {loading ? (
                            <tr><td colSpan={4} className="p-8 text-center text-surface-500">Cargando...</td></tr>
                        ) : deadlines.length === 0 ? (
                            <tr><td colSpan={4} className="p-8 text-center text-surface-500">No hay plazos registrados.</td></tr>
                        ) : (
                            deadlines.map(d => (
                                <tr key={d.id} className="hover:bg-surface-50/50">
                                    <td className="px-6 py-4">
                                        <div className="font-medium text-surface-900">{d.descripcion}</div>
                                        {d.base_legal && <div className="text-xs text-surface-500">{d.base_legal}</div>}
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="font-medium text-surface-900">{new Date(d.fecha_vencimiento).toLocaleDateString()}</div>
                                        <div className="text-xs text-surface-500">{d.hora_vencimiento?.substring(0, 5)}</div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className={`text-xs px-2 py-0.5 rounded uppercase font-medium ${d.prioridad === 'critica' ? 'bg-red-50 text-red-700' :
                                                d.prioridad === 'alta' ? 'bg-orange-50 text-orange-700' :
                                                    'bg-surface-100 text-surface-600'
                                            }`}>{d.prioridad}</span>
                                    </td>
                                    <td className="px-6 py-4">
                                        {getStatusBadge(d)}
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* Create Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
                    <div className="bg-white rounded-xl shadow-xl w-full max-w-md animate-slide-up">
                        <div className="px-6 py-4 border-b border-surface-200 flex justify-between items-center bg-surface-50">
                            <h3 className="font-bold text-lg text-surface-800">Registrar Plazo Fatal</h3>
                            <button onClick={() => setShowModal(false)} className="text-surface-400 hover:text-surface-600">
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                        <form onSubmit={handleSubmit} className="p-6 space-y-4">
                            <div>
                                <label className="label">Descripción *</label>
                                <input required name="descripcion" value={formData.descripcion || ''} onChange={handleInputChange} className="input w-full" placeholder="Ej: Contestar demanda" />
                            </div>

                            <div>
                                <label className="label">Base Legal</label>
                                <input name="base_legal" value={formData.base_legal || ''} onChange={handleInputChange} className="input w-full" placeholder="Art. 43 CPCN" />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="label">Vencimiento *</label>
                                    <input required type="date" name="fecha_vencimiento" value={formData.fecha_vencimiento || ''} onChange={handleInputChange} className="input w-full" />
                                </div>
                                <div>
                                    <label className="label">Hora</label>
                                    <input type="time" name="hora_vencimiento" value={formData.hora_vencimiento || ''} onChange={handleInputChange} className="input w-full" />
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="label">Tipo</label>
                                    <select name="tipo_plazo" value={formData.tipo_plazo} onChange={handleInputChange} className="input w-full">
                                        <option value="procesal">Procesal</option>
                                        <option value="contractual">Contractual</option>
                                        <option value="administrativo">Administrativo</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="label">Prioridad</label>
                                    <select name="prioridad" value={formData.prioridad} onChange={handleInputChange} className="input w-full">
                                        <option value="normal">Normal</option>
                                        <option value="alta">Alta</option>
                                        <option value="critica">Crítica</option>
                                    </select>
                                </div>
                            </div>

                            <div className="flex justify-end gap-3 mt-4">
                                <button type="button" onClick={() => setShowModal(false)} className="btn btn-ghost">Cancelar</button>
                                <button type="submit" disabled={submitting} className="btn btn-primary">Guardar</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
