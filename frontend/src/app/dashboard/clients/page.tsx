'use client';

import { useState, useEffect } from 'react';
import { Users, Search, Plus, Mail, Phone, MoreVertical, Shield } from 'lucide-react';
import { userService, User, CreateUserDto } from '@/services/userService';

export default function ClientsPage() {
    const [clients, setClients] = useState<User[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [showModal, setShowModal] = useState(false);
    const [saving, setSaving] = useState(false);
    const [formData, setFormData] = useState<CreateUserDto>({
        nombre: '',
        apellido: '',
        email: '',
        telefono: '',
        password: 'ClientPassword123!', // Default password for now
        tipo_usuario: 'cliente',
        tipo_vinculo: 'cliente'
    });

    useEffect(() => {
        fetchClients();
    }, []);

    const fetchClients = async () => {
        try {
            // Filter by role 'cliente' using the new backend capability
            const data = await userService.getAll(1, 100, '', 'cliente');
            setClients(data.items);
        } catch (error) {
            console.error('Failed to fetch clients', error);
        } finally {
            setLoading(false);
        }
    };

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        setSaving(true);
        try {
            await userService.create(formData);
            setShowModal(false);
            setFormData({
                nombre: '',
                apellido: '',
                email: '',
                telefono: '',
                password: 'ClientPassword123!',
                tipo_usuario: 'cliente',
                tipo_vinculo: 'cliente'
            });
            fetchClients();
        } catch (error: any) {
            console.error('Failed to create client', error);
            alert(error.response?.data?.detail || 'Error al crear el cliente. Verifica si el email ya existe.');
        } finally {
            setSaving(false);
        }
    };

    const filteredClients = clients.filter(c =>
        c.nombre.toLowerCase().includes(searchTerm.toLowerCase()) ||
        c.apellido.toLowerCase().includes(searchTerm.toLowerCase()) ||
        c.email.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (loading) {
        return <div className="p-8 text-center text-surface-500">Cargando directorio de clientes...</div>;
    }

    return (
        <div className="space-y-6 animate-fade-in">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="flex flex-col gap-1">
                    <h1 className="text-2xl font-bold text-surface-900 flex items-center gap-3">
                        <Users className="w-8 h-8 text-primary-500" />
                        Directorio de Clientes
                    </h1>
                    <p className="text-surface-500">Gestiona la base de datos de tus clientes y sus datos de contacto.</p>
                </div>
                <button
                    onClick={() => setShowModal(true)}
                    className="btn btn-primary flex items-center gap-2"
                >
                    <Plus className="w-4 h-4" /> Nuevo Cliente
                </button>
            </div>

            {/* Modal de Nuevo Cliente */}
            {showModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-surface-900/50 backdrop-blur-sm animate-fade-in">
                    <div className="bg-white rounded-2xl shadow-judicial-lg w-full max-w-lg overflow-hidden animate-slide-up">
                        <div className="p-6 border-b border-surface-200 flex justify-between items-center bg-surface-50">
                            <h2 className="text-xl font-bold text-surface-900 flex items-center gap-2">
                                <Users className="w-6 h-6 text-primary-500" />
                                Nuevo Cliente
                            </h2>
                            <button onClick={() => setShowModal(false)} className="text-surface-400 hover:text-surface-600 transition-colors text-2xl">&times;</button>
                        </div>

                        <form onSubmit={handleCreate} className="p-6 space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-1">
                                    <label className="text-xs font-bold text-surface-500 uppercase tracking-wider">Nombre</label>
                                    <input
                                        type="text"
                                        required
                                        className="input w-full"
                                        placeholder="Ej. Juan"
                                        value={formData.nombre}
                                        onChange={e => setFormData({ ...formData, nombre: e.target.value })}
                                    />
                                </div>
                                <div className="space-y-1">
                                    <label className="text-xs font-bold text-surface-500 uppercase tracking-wider">Apellido</label>
                                    <input
                                        type="text"
                                        required
                                        className="input w-full"
                                        placeholder="Ej. Pérez"
                                        value={formData.apellido}
                                        onChange={e => setFormData({ ...formData, apellido: e.target.value })}
                                    />
                                </div>
                            </div>

                            <div className="space-y-1">
                                <label className="text-xs font-bold text-surface-500 uppercase tracking-wider">Email</label>
                                <input
                                    type="email"
                                    required
                                    className="input w-full"
                                    placeholder="correo@ejemplo.com"
                                    value={formData.email}
                                    onChange={e => setFormData({ ...formData, email: e.target.value })}
                                />
                            </div>

                            <div className="space-y-1">
                                <label className="text-xs font-bold text-surface-500 uppercase tracking-wider">Teléfono</label>
                                <input
                                    type="tel"
                                    className="input w-full"
                                    placeholder="+505 8888 8888"
                                    value={formData.telefono}
                                    onChange={e => setFormData({ ...formData, telefono: e.target.value })}
                                />
                            </div>

                            <div className="pt-4 flex justify-end gap-3">
                                <button type="button" onClick={() => setShowModal(false)} className="btn btn-ghost">Cancelar</button>
                                <button type="submit" disabled={saving} className="btn btn-primary flex items-center gap-2">
                                    {saving ? 'Guardando...' : (<><Plus className="w-4 h-4" /> Guardar Cliente</>)}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            <div className="card overflow-hidden">
                <div className="p-4 border-b border-surface-200 bg-surface-50">
                    <div className="relative max-w-md">
                        <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-surface-400" />
                        <input
                            type="text"
                            placeholder="Buscar por nombre, apellido o email..."
                            className="input w-full pl-9 h-10 text-sm"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                </div>

                {filteredClients.length === 0 ? (
                    <div className="p-12 text-center space-y-4">
                        <div className="w-16 h-16 bg-surface-100 rounded-full flex items-center justify-center mx-auto">
                            <Users className="w-8 h-8 text-surface-400" />
                        </div>
                        <p className="text-surface-500 font-medium">No se encontraron clientes registrados.</p>
                        <button className="btn btn-sm btn-outline" onClick={() => setSearchTerm('')}>Limpiar búsqueda</button>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
                        {filteredClients.map((client) => (
                            <div key={client.id} className="p-5 border border-surface-200 rounded-xl hover:shadow-judicial transition-all bg-white group relative">
                                <div className="flex items-start justify-between mb-4">
                                    <div className="w-12 h-12 bg-primary-50 rounded-full flex items-center justify-center text-primary-600 font-bold text-lg">
                                        {client.nombre[0]}{client.apellido[0]}
                                    </div>
                                    <button className="p-1 hover:bg-surface-100 rounded text-surface-400">
                                        <MoreVertical className="w-4 h-4" />
                                    </button>
                                </div>

                                <h3 className="font-bold text-surface-900 text-lg mb-1">{client.nombre} {client.apellido}</h3>
                                <div className="space-y-2 mt-4">
                                    <div className="flex items-center gap-2 text-sm text-surface-600">
                                        <Mail className="w-4 h-4 text-surface-400" />
                                        <span className="truncate">{client.email}</span>
                                    </div>
                                    <div className="flex items-center gap-2 text-sm text-surface-600">
                                        <Phone className="w-4 h-4 text-surface-400" />
                                        <span>{client.telefono || 'Sin teléfono'}</span>
                                    </div>
                                </div>

                                <div className="mt-5 pt-4 border-t border-surface-100 flex items-center justify-between">
                                    <span className="inline-flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-green-600 bg-green-50 px-2 py-0.5 rounded">
                                        <Shield className="w-3 h-3" /> Activo
                                    </span>
                                    <button className="text-primary-600 text-xs font-semibold hover:underline">Ver Historial</button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
