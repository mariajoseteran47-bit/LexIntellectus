'use client';

import { useState, useEffect } from 'react';
import { Search, Plus, User as UserIcon, MoreVertical, X, Shield, Briefcase } from 'lucide-react';
import { userService, User, CreateUserDto } from '@/services/userService';
import { useToast } from '@/components/ui/ToastProvider';

export default function UsersPage() {
    const [users, setUsers] = useState<User[]>([]);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [search, setSearch] = useState('');
    const [showModal, setShowModal] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const toast = useToast();

    // Form State
    const [formData, setFormData] = useState<CreateUserDto>({
        email: '',
        password: '',
        nombre: '',
        apellido: '',
        telefono: '',
        tipo_usuario: 'abogado',
        tipo_vinculo: 'indefinido',
    });

    const fetchUsers = async () => {
        setLoading(true);
        try {
            const data = await userService.getAll(page, 20, search);
            setUsers(data.items);
        } catch (error) {
            console.error('Failed to fetch users', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        const timer = setTimeout(() => {
            fetchUsers();
        }, 300);
        return () => clearTimeout(timer);
    }, [page, search]);

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setSubmitting(true);
        try {
            await userService.create(formData);
            setShowModal(false);
            setFormData({
                email: '',
                password: '',
                nombre: '',
                apellido: '',
                telefono: '',
                tipo_usuario: 'abogado',
                tipo_vinculo: 'indefinido',
            });
            fetchUsers();
            toast.success('Usuario creado', `${formData.nombre} ${formData.apellido} fue registrado exitosamente.`);
        } catch (error) {
            console.error('Failed to create user', error);
            toast.error('Error al crear usuario', 'Verifique los datos e intente nuevamente.');
        } finally {
            setSubmitting(false);
        }
    };

    const userTypeLabel: Record<string, string> = {
        admin_sistema: 'Admin Sistema',
        admin_despacho: 'Admin Despacho',
        abogado: 'Abogado',
        notario: 'Notario',
        secretaria: 'Secretaria',
        contador: 'Contador',
        gestor: 'Gestor',
        cliente: 'Cliente',
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-surface-900">Gestión de Usuarios</h1>
                    <p className="text-surface-500 text-sm mt-1">Administra el personal del despacho y sus accesos</p>
                </div>
                <button
                    onClick={() => setShowModal(true)}
                    className="btn btn-primary flex items-center gap-2"
                >
                    <Plus className="w-4 h-4" />
                    Nuevo Usuario
                </button>
            </div>

            {/* Content */}
            <div className="card overflow-hidden">
                {/* Filters */}
                <div className="p-4 border-b border-surface-200">
                    <div className="relative max-w-md">
                        <Search className="w-5 h-5 text-surface-400 absolute left-3 top-1/2 -translate-y-1/2" />
                        <input
                            type="text"
                            placeholder="Buscar por nombre o email..."
                            className="input pl-10 w-full"
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                        />
                    </div>
                </div>

                {/* Table */}
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                        <thead className="bg-surface-50">
                            <tr>
                                <th className="px-6 py-3 font-semibold text-surface-700">Usuario</th>
                                <th className="px-6 py-3 font-semibold text-surface-700">Rol / Cargo</th>
                                <th className="px-6 py-3 font-semibold text-surface-700">Contacto</th>
                                <th className="px-6 py-3 font-semibold text-surface-700">Estado</th>
                                <th className="px-6 py-3 text-right">Acciones</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-surface-100">
                            {loading ? (
                                <tr><td colSpan={5} className="p-8 text-center">Cargando...</td></tr>
                            ) : users.length === 0 ? (
                                <tr><td colSpan={5} className="p-8 text-center text-surface-500">No se encontraron usuarios.</td></tr>
                            ) : (
                                users.map(user => (
                                    <tr key={user.id} className="hover:bg-surface-50/50">
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-3">
                                                <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center text-primary-700 font-bold text-xs">
                                                    {user.nombre[0]}{user.apellido[0]}
                                                </div>
                                                <div>
                                                    <div className="font-medium text-surface-900">{user.nombre} {user.apellido}</div>
                                                    <div className="text-xs text-surface-500">ID: ...{user.id.slice(-4)}</div>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-1.5">
                                                <Shield className="w-3.5 h-3.5 text-surface-400" />
                                                <span className="font-medium text-surface-700">{userTypeLabel[user.tipo_usuario] || user.tipo_usuario}</span>
                                            </div>
                                            <div className="text-xs text-surface-500 flex items-center gap-1.5 mt-0.5 ml-5">
                                                <Briefcase className="w-3 h-3" />
                                                <span className="capitalize">{user.tipo_vinculo}</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-surface-600">
                                            <div>{user.email}</div>
                                            <div className="text-xs text-surface-500">{user.telefono || '-'}</div>
                                        </td>
                                        <td className="px-6 py-4">
                                            {user.is_active ? (
                                                <span className="badge bg-green-100 text-green-700">Activo</span>
                                            ) : (
                                                <span className="badge bg-gray-100 text-gray-700">Inactivo</span>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <button className="btn btn-ghost p-1 text-surface-400 hover:text-primary-600">
                                                <MoreVertical className="w-4 h-4" />
                                            </button>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Create Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
                    <div className="bg-white rounded-xl shadow-xl w-full max-w-lg overflow-hidden animate-slide-up">
                        <div className="px-6 py-4 border-b border-surface-200 flex justify-between items-center bg-surface-50">
                            <h3 className="font-bold text-lg text-surface-800">Registrar Nuevo Usuario</h3>
                            <button onClick={() => setShowModal(false)} className="text-surface-400 hover:text-surface-600">
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                        <form onSubmit={handleSubmit} className="p-6 space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="label">Nombre *</label>
                                    <input required name="nombre" value={formData.nombre} onChange={handleInputChange} className="input w-full" />
                                </div>
                                <div>
                                    <label className="label">Apellido *</label>
                                    <input required name="apellido" value={formData.apellido} onChange={handleInputChange} className="input w-full" />
                                </div>
                            </div>
                            <div>
                                <label className="label">Email Corporativo *</label>
                                <input required type="email" name="email" value={formData.email} onChange={handleInputChange} className="input w-full" />
                            </div>
                            <div>
                                <label className="label">Contraseña Temporal *</label>
                                <input required type="password" name="password" value={formData.password} onChange={handleInputChange} className="input w-full" />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="label">Rol / Tipo *</label>
                                    <select name="tipo_usuario" value={formData.tipo_usuario} onChange={handleInputChange} className="input w-full">
                                        <option value="abogado">Abogado</option>
                                        <option value="notario">Notario</option>
                                        <option value="secretaria">Secretaria</option>
                                        <option value="contador">Contador</option>
                                        <option value="gestor">Gestor</option>
                                        <option value="admin_despacho">Admin Despacho</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="label">Vínculo *</label>
                                    <select name="tipo_vinculo" value={formData.tipo_vinculo} onChange={handleInputChange} className="input w-full">
                                        <option value="indefinido">Indefinido</option>
                                        <option value="determinado">Determinado</option>
                                        <option value="servicios">Servicios Prof.</option>
                                        <option value="socio">Socio</option>
                                    </select>
                                </div>
                            </div>
                            <div>
                                <label className="label">Teléfono</label>
                                <input name="telefono" value={formData.telefono || ''} onChange={handleInputChange} className="input w-full" />
                            </div>

                            <div className="flex justify-end gap-3 mt-6">
                                <button type="button" onClick={() => setShowModal(false)} className="btn btn-ghost">Cancelar</button>
                                <button type="submit" disabled={submitting} className="btn btn-primary">
                                    {submitting ? 'Guardando...' : 'Crear Usuario'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
