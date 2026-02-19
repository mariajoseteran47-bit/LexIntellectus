'use client';

import { useState, useEffect } from 'react';
import { FileText, Download, Trash2, Search, ExternalLink, Filter } from 'lucide-react';
import { documentService, Document } from '@/services/documentService';
import Link from 'next/link';

export default function DocumentsPage() {
    const [documents, setDocuments] = useState<Document[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        fetchDocuments();
    }, []);

    const fetchDocuments = async () => {
        try {
            const data = await documentService.getByCaseId(); // No ID returns all for tenant
            setDocuments(data);
        } catch (error) {
            console.error('Failed to fetch documents', error);
        } finally {
            setLoading(false);
        }
    };

    const handleDownload = async (doc: Document) => {
        try {
            const url = await documentService.getDownloadUrl(doc.id);
            window.open(url, '_blank');
        } catch (error) {
            console.error('Failed to get download URL', error);
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm('¿Estás seguro de eliminar este documento de forma permanente?')) return;
        try {
            await documentService.delete(id);
            fetchDocuments();
        } catch (error) {
            console.error('Failed to delete document', error);
        }
    };

    const filteredDocs = documents.filter(doc =>
        doc.nombre_archivo.toLowerCase().includes(searchTerm.toLowerCase()) ||
        doc.descripcion?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        doc.categoria.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (loading) {
        return <div className="p-8 text-center text-surface-500">Cargando repositorio de documentos...</div>;
    }

    return (
        <div className="space-y-6 animate-fade-in">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="flex flex-col gap-1">
                    <h1 className="text-2xl font-bold text-surface-900 flex items-center gap-3">
                        <FileText className="w-8 h-8 text-primary-500" />
                        Repositorio de Documentos
                    </h1>
                    <p className="text-surface-500">Gestión centralizada de toda la documentación del despacho.</p>
                </div>
            </div>

            <div className="card overflow-hidden">
                <div className="p-4 border-b border-surface-200 bg-surface-50 flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="relative flex-1 max-w-md">
                        <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-surface-400" />
                        <input
                            type="text"
                            placeholder="Buscar en archivos, descripciones o categorías..."
                            className="input w-full pl-9 h-10 text-sm"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                    <div className="flex items-center gap-2">
                        <button className="btn btn-sm btn-ghost gap-2 text-surface-500">
                            <Filter className="w-4 h-4" /> Filtros
                        </button>
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                        <thead className="bg-white border-b border-surface-200">
                            <tr>
                                <th className="px-6 py-3 font-semibold text-surface-600">Archivo / Descripción</th>
                                <th className="px-6 py-3 font-semibold text-surface-600">Categoría</th>
                                <th className="px-6 py-3 font-semibold text-surface-600">Fecha</th>
                                <th className="px-6 py-3 font-semibold text-surface-600">Tamaño</th>
                                <th className="px-6 py-3 text-right">Acciones</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-surface-100">
                            {filteredDocs.length === 0 ? (
                                <tr>
                                    <td colSpan={5} className="px-6 py-12 text-center text-surface-500">
                                        No se encontraron documentos que coincidan con la búsqueda.
                                    </td>
                                </tr>
                            ) : (
                                filteredDocs.map((doc) => (
                                    <tr key={doc.id} className="hover:bg-surface-50/50 transition-colors">
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-3">
                                                <div className="w-8 h-8 rounded bg-primary-50 flex items-center justify-center flex-shrink-0">
                                                    <FileText className="w-4 h-4 text-primary-500" />
                                                </div>
                                                <div>
                                                    <div className="font-medium text-surface-900">{doc.nombre_archivo}</div>
                                                    {doc.descripcion && <div className="text-xs text-surface-500 truncate max-w-xs">{doc.descripcion}</div>}
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 capitalize">
                                            <span className="bg-surface-100 text-surface-600 px-2 py-1 rounded text-[10px] font-bold tracking-wider uppercase">
                                                {doc.categoria}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-surface-600">
                                            {new Date(doc.created_at).toLocaleDateString()}
                                        </td>
                                        <td className="px-6 py-4 text-surface-400 text-xs">
                                            {(doc.tamano_bytes / 1024).toFixed(1)} KB
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <div className="flex justify-end gap-1">
                                                <Link
                                                    href={`/dashboard/cases/${doc.expediente_id}`}
                                                    className="p-1.5 text-surface-400 hover:text-primary-600 transition-colors"
                                                    title="Ver Expediente"
                                                >
                                                    <ExternalLink className="w-4 h-4" />
                                                </Link>
                                                <button
                                                    onClick={() => handleDownload(doc)}
                                                    className="p-1.5 text-surface-400 hover:text-primary-600 transition-colors"
                                                    title="Descargar"
                                                >
                                                    <Download className="w-4 h-4" />
                                                </button>
                                                <button
                                                    onClick={() => handleDelete(doc.id)}
                                                    className="p-1.5 text-surface-400 hover:text-red-600 transition-colors"
                                                    title="Eliminar"
                                                >
                                                    <Trash2 className="w-4 h-4" />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
