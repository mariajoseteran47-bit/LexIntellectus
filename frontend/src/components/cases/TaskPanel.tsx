'use client';

import { useState, useEffect } from 'react';
import {
    CheckSquare, Square, Plus, Clock, User, X,
    AlertTriangle, Loader2, Trash2, ChevronDown, ListChecks
} from 'lucide-react';
import api from '@/lib/api';
import { useToast } from '@/components/ui/ToastProvider';

interface Task {
    id: string; titulo: string; descripcion?: string; estado: string;
    categoria: string; obligatoria: boolean; asignado_a_id?: string;
    asignado_nombre?: string; fecha_limite?: string;
    fecha_completada?: string; etapa_codigo?: string; orden: number;
}

const CATEGORY_COLORS: Record<string, string> = {
    procesal: 'bg-blue-100 text-blue-700',
    documental: 'bg-amber-100 text-amber-700',
    administrativa: 'bg-surface-100 text-surface-600',
    cliente: 'bg-purple-100 text-purple-700',
    interna: 'bg-green-100 text-green-700',
};

export default function TaskPanel({ caseId }: { caseId: string }) {
    const [tasks, setTasks] = useState<Task[]>([]);
    const [loading, setLoading] = useState(true);
    const [showNew, setShowNew] = useState(false);
    const [newTask, setNewTask] = useState({ titulo: '', descripcion: '', categoria: 'administrativa', obligatoria: false, fecha_limite: '' });
    const [stats, setStats] = useState({ total: 0, completadas: 0, pendientes: 0 });
    const [filter, setFilter] = useState('');
    const toast = useToast();

    useEffect(() => { loadTasks(); }, [caseId, filter]);

    const loadTasks = async () => {
        setLoading(true);
        try {
            const params = new URLSearchParams();
            if (filter) params.append('estado', filter);
            const { data } = await api.get(`/cases/${caseId}/tasks?${params}`);
            setTasks(data.items || []);
            setStats({ total: data.total, completadas: data.completadas, pendientes: data.pendientes });
        } catch (e) { console.error(e); }
        finally { setLoading(false); }
    };

    const toggleTask = async (task: Task) => {
        const newState = task.estado === 'completada' ? 'pendiente' : 'completada';
        try {
            await api.patch(`/tasks/${task.id}`, { estado: newState });
            loadTasks();
        } catch (e) { toast.error('Error al actualizar tarea'); }
    };

    const handleCreate = async () => {
        if (!newTask.titulo.trim()) return;
        try {
            await api.post(`/cases/${caseId}/tasks`, {
                ...newTask,
                fecha_limite: newTask.fecha_limite || null,
            });
            setShowNew(false);
            setNewTask({ titulo: '', descripcion: '', categoria: 'administrativa', obligatoria: false, fecha_limite: '' });
            loadTasks();
            toast.success('Tarea creada');
        } catch (e) { toast.error('Error al crear tarea'); }
    };

    const deleteTask = async (taskId: string) => {
        try {
            await api.delete(`/tasks/${taskId}`);
            loadTasks();
        } catch (e) { toast.error('Error al eliminar'); }
    };

    const applyTemplate = async () => {
        try {
            const { data } = await api.post(`/cases/${caseId}/apply-template`);
            toast.success(data.message);
            loadTasks();
        } catch (e) { toast.error('Error al aplicar plantilla'); }
    };

    const isOverdue = (t: Task) => t.fecha_limite && new Date(t.fecha_limite) < new Date() && t.estado !== 'completada';
    const progress = stats.total > 0 ? Math.round((stats.completadas / stats.total) * 100) : 0;

    return (
        <div className="space-y-4">
            {/* Header + Progress */}
            <div className="card p-4">
                <div className="flex items-center justify-between mb-3">
                    <h3 className="font-bold text-surface-800 flex items-center gap-2">
                        <ListChecks className="w-5 h-5 text-primary-500" /> Tareas del Asunto
                    </h3>
                    <div className="flex gap-2">
                        <button onClick={applyTemplate} className="btn btn-sm btn-outline text-xs" title="Aplicar plantilla">
                            📋 Plantilla
                        </button>
                        <button onClick={() => setShowNew(true)} className="btn btn-sm btn-primary gap-1">
                            <Plus className="w-3 h-3" /> Tarea
                        </button>
                    </div>
                </div>
                {/* Progress bar */}
                <div className="flex items-center gap-3">
                    <div className="flex-1 bg-surface-100 rounded-full h-2.5 overflow-hidden">
                        <div className="h-full bg-gradient-to-r from-primary-500 to-emerald-500 rounded-full transition-all duration-500"
                            style={{ width: `${progress}%` }} />
                    </div>
                    <span className="text-sm font-bold text-surface-700 shrink-0">{progress}%</span>
                    <span className="text-xs text-surface-400">{stats.completadas}/{stats.total}</span>
                </div>
            </div>

            {/* Filters */}
            <div className="flex gap-1 text-xs">
                {[{ v: '', l: 'Todas' }, { v: 'pendiente', l: 'Pendientes' }, { v: 'en_progreso', l: 'En progreso' }, { v: 'completada', l: 'Completadas' }].map(f => (
                    <button key={f.v} onClick={() => setFilter(f.v)}
                        className={`px-3 py-1.5 rounded-lg font-medium transition-colors ${filter === f.v ? 'bg-primary-100 text-primary-700' : 'bg-surface-50 text-surface-500 hover:bg-surface-100'}`}>
                        {f.l}
                    </button>
                ))}
            </div>

            {/* New Task Form */}
            {showNew && (
                <div className="card p-4 border-2 border-primary-200 bg-primary-50/30 space-y-3">
                    <input type="text" className="input w-full" placeholder="Título de la tarea..."
                        value={newTask.titulo} onChange={e => setNewTask(p => ({ ...p, titulo: e.target.value }))}
                        onKeyDown={e => e.key === 'Enter' && handleCreate()} autoFocus />
                    <div className="grid grid-cols-3 gap-3">
                        <select className="input text-sm" value={newTask.categoria}
                            onChange={e => setNewTask(p => ({ ...p, categoria: e.target.value }))}>
                            <option value="administrativa">Administrativa</option>
                            <option value="procesal">Procesal</option>
                            <option value="documental">Documental</option>
                            <option value="cliente">Cliente</option>
                            <option value="interna">Interna</option>
                        </select>
                        <input type="date" className="input text-sm" value={newTask.fecha_limite}
                            onChange={e => setNewTask(p => ({ ...p, fecha_limite: e.target.value }))} />
                        <label className="flex items-center gap-2 text-sm text-surface-600">
                            <input type="checkbox" checked={newTask.obligatoria}
                                onChange={e => setNewTask(p => ({ ...p, obligatoria: e.target.checked }))}
                                className="rounded" />
                            Obligatoria
                        </label>
                    </div>
                    <div className="flex justify-end gap-2">
                        <button onClick={() => setShowNew(false)} className="btn btn-sm btn-outline">Cancelar</button>
                        <button onClick={handleCreate} disabled={!newTask.titulo.trim()} className="btn btn-sm btn-primary">Crear</button>
                    </div>
                </div>
            )}

            {/* Task List */}
            {loading ? (
                <div className="text-center py-6 text-surface-400">Cargando tareas...</div>
            ) : tasks.length === 0 ? (
                <div className="card p-8 text-center">
                    <CheckSquare className="w-10 h-10 mx-auto text-surface-200 mb-3" />
                    <p className="text-surface-500 font-medium">Sin tareas registradas</p>
                    <p className="text-sm text-surface-400 mt-1">Cree una tarea o aplique una plantilla de workflow</p>
                </div>
            ) : (
                <div className="space-y-1.5">
                    {tasks.map(task => (
                        <div key={task.id}
                            className={`flex items-start gap-3 p-3 rounded-lg border transition-all ${
                                task.estado === 'completada'
                                    ? 'bg-surface-50/50 border-surface-100'
                                    : isOverdue(task)
                                        ? 'bg-red-50/30 border-red-200'
                                        : 'bg-white border-surface-200 hover:border-primary-200'
                            }`}>
                            {/* Checkbox */}
                            <button onClick={() => toggleTask(task)} className="mt-0.5 shrink-0">
                                {task.estado === 'completada' ? (
                                    <CheckSquare className="w-5 h-5 text-emerald-500" />
                                ) : (
                                    <Square className="w-5 h-5 text-surface-300 hover:text-primary-500" />
                                )}
                            </button>

                            {/* Content */}
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 flex-wrap">
                                    <span className={`font-medium text-sm ${task.estado === 'completada' ? 'text-surface-400 line-through' : 'text-surface-800'}`}>
                                        {task.titulo}
                                    </span>
                                    {task.obligatoria && (
                                        <span className="badge bg-red-100 text-red-600 text-[10px]">OBLIGATORIA</span>
                                    )}
                                    <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${CATEGORY_COLORS[task.categoria] || CATEGORY_COLORS.administrativa}`}>
                                        {task.categoria}
                                    </span>
                                    {isOverdue(task) && (
                                        <span className="badge bg-red-100 text-red-700 text-[10px] animate-pulse">VENCIDA</span>
                                    )}
                                </div>
                                <div className="flex items-center gap-3 mt-1 text-xs text-surface-400">
                                    {task.asignado_nombre && (
                                        <span className="flex items-center gap-1"><User className="w-3 h-3" /> {task.asignado_nombre}</span>
                                    )}
                                    {task.fecha_limite && (
                                        <span className={`flex items-center gap-1 ${isOverdue(task) ? 'text-red-600 font-bold' : ''}`}>
                                            <Clock className="w-3 h-3" /> {new Date(task.fecha_limite).toLocaleDateString('es-NI')}
                                        </span>
                                    )}
                                </div>
                            </div>

                            {/* Delete */}
                            <button onClick={() => deleteTask(task.id)}
                                className="btn btn-ghost p-1 text-surface-300 hover:text-red-500 shrink-0">
                                <Trash2 className="w-3.5 h-3.5" />
                            </button>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
