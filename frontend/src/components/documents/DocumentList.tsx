'use client';

import { useState, useEffect } from 'react';
import { Plus, FileText, Download, Trash2, X, Upload } from 'lucide-react';
import { documentService, Document, UploadDocumentDto } from '@/services/documentService';

interface DocumentListProps {
    caseId: string;
}

export default function DocumentList({ caseId }: DocumentListProps) {
    const [documents, setDocuments] = useState<Document[]>([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [submitting, setSubmitting] = useState(false);

    // Form State
    const [file, setFile] = useState<File | null>(null);
    const [descripcion, setDescripcion] = useState('');
    const [categoria, setCategoria] = useState('general');

    const fetchDocuments = async () => {
        setLoading(true);
        try {
            const data = await documentService.getByCaseId(caseId);
            setDocuments(data);
        } catch (error) {
            console.error('Failed to fetch documents', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (caseId) fetchDocuments();
    }, [caseId]);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!file) {
            alert('Selecciona un archivo');
            return;
        }

        setSubmitting(true);
        try {
            await documentService.upload({
                expediente_id: caseId,
                file: file,
                descripcion: descripcion,
                categoria: categoria
            });

            setShowModal(false);
            setFile(null);
            setDescripcion('');
            setCategoria('general');
            fetchDocuments();
        } catch (error) {
            console.error('Failed to upload document', error);
            alert('Error al subir documento');
        } finally {
            setSubmitting(false);
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
        if (!confirm('¿Estás seguro de eliminar este documento?')) return;
        try {
            await documentService.delete(id);
            fetchDocuments();
        } catch (error) {
            console.error('Failed to delete document', error);
        }
    };

    return (
        <div className="card overflow-hidden">
            <div className="p-4 border-b border-surface-200 flex justify-between items-center bg-surface-50">
                <h3 className="font-semibold text-surface-800 flex items-center gap-2">
                    <FileText className="w-4 h-4" /> Documentos del Caso
                </h3>
                <button onClick={() => setShowModal(true)} className="btn btn-sm btn-outline gap-2">
                    <Upload className="w-4 h-4" /> Subir Documento
                </button>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                    <thead className="bg-white border-b border-surface-200">
                        <tr>
                            <th className="px-6 py-3 font-semibold text-surface-600">Nombre / Descripción</th>
                            <th className="px-6 py-3 font-semibold text-surface-600">Categoría</th>
                            <th className="px-6 py-3 font-semibold text-surface-600">Fecha</th>
                            <th className="px-6 py-3 font-semibold text-surface-600">Tamaño</th>
                            <th className="px-6 py-3 text-right">Acciones</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-surface-100">
                        {loading ? (
                            <tr><td colSpan={5} className="p-8 text-center text-surface-500">Cargando...</td></tr>
                        ) : documents.length === 0 ? (
                            <tr><td colSpan={5} className="p-8 text-center text-surface-500">No hay documentos registrados.</td></tr>
                        ) : (
                            documents.map(d => (
                                <tr key={d.id} className="hover:bg-surface-50/50">
                                    <td className="px-6 py-4">
                                        <div className="font-medium text-surface-900">{d.nombre_archivo}</div>
                                        {d.descripcion && <div className="text-xs text-surface-500">{d.descripcion}</div>}
                                    </td>
                                    <td className="px-6 py-4 capitalize">
                                        <span className="bg-surface-100 text-surface-600 px-2 py-1 rounded text-xs">{d.categoria}</span>
                                    </td>
                                    <td className="px-6 py-4 text-surface-600">
                                        {new Date(d.created_at).toLocaleDateString()}
                                    </td>
                                    <td className="px-6 py-4 text-surface-600 text-xs">
                                        {(d.tamano_bytes / 1024).toFixed(1)} KB
                                    </td>
                                    <td className="px-6 py-4 text-right flex justify-end gap-2">
                                        <button
                                            onClick={() => handleDownload(d)}
                                            className="p-1 text-surface-400 hover:text-primary-600"
                                            title="Descargar"
                                        >
                                            <Download className="w-4 h-4" />
                                        </button>
                                        <button
                                            onClick={() => handleDelete(d.id)}
                                            className="p-1 text-surface-400 hover:text-red-600"
                                            title="Eliminar"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* Upload Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
                    <div className="bg-white rounded-xl shadow-xl w-full max-w-md animate-slide-up">
                        <div className="px-6 py-4 border-b border-surface-200 flex justify-between items-center bg-surface-50">
                            <h3 className="font-bold text-lg text-surface-800">Subir Documento</h3>
                            <button onClick={() => setShowModal(false)} className="text-surface-400 hover:text-surface-600">
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                        <form onSubmit={handleSubmit} className="p-6 space-y-4">
                            <div>
                                <label className="label">Archivo *</label>
                                <input required type="file" onChange={handleFileChange} className="input w-full p-2" />
                            </div>

                            <div>
                                <label className="label">Descripción</label>
                                <input
                                    value={descripcion}
                                    onChange={(e) => setDescripcion(e.target.value)}
                                    className="input w-full"
                                    placeholder="Ej: Escrito de contestación de demanda"
                                />
                            </div>

                            <div>
                                <label className="label">Categoría</label>
                                <select
                                    value={categoria}
                                    onChange={(e) => setCategoria(e.target.value)}
                                    className="input w-full"
                                >
                                    <option value="general">General</option>
                                    <option value="evidencia">Evidencia</option>
                                    <option value="escrito">Escrito Judicial</option>
                                    <option value="notificacion">Notificación</option>
                                    <option value="sentencia">Sentencia / Auto</option>
                                </select>
                            </div>

                            <div className="flex justify-end gap-3 mt-4">
                                <button type="button" onClick={() => setShowModal(false)} className="btn btn-ghost">Cancelar</button>
                                <button type="submit" disabled={submitting} className="btn btn-primary">
                                    {submitting ? 'Subiendo...' : 'Subir Archivo'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
