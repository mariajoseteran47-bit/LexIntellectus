// === Service Types ===
export type TipoServicio =
    | 'litigio'
    | 'escritura'
    | 'asesoria'
    | 'tramite'
    | 'consulta'
    | 'mediacion'
    | 'contrato'
    | 'due_diligence'
    | 'propiedad_intelectual'
    | 'gestion_corporativa';

export const TIPOS_SERVICIO: { value: TipoServicio; label: string; icon: string; description: string; color: string }[] = [
    { value: 'litigio', label: 'Litigio', icon: '⚖️', description: 'Caso judicial ante tribunales', color: 'bg-blue-100 text-blue-700' },
    { value: 'escritura', label: 'Escritura Notarial', icon: '📜', description: 'Protocolo notarial / instrumento público', color: 'bg-amber-100 text-amber-700' },
    { value: 'asesoria', label: 'Asesoría Legal', icon: '💼', description: 'Asesoría continua / iguala / retainer', color: 'bg-emerald-100 text-emerald-700' },
    { value: 'tramite', label: 'Trámite Administrativo', icon: '📝', description: 'Gestión ante instituciones gubernamentales', color: 'bg-violet-100 text-violet-700' },
    { value: 'consulta', label: 'Consulta Puntual', icon: '💬', description: 'Consulta legal / opinión jurídica', color: 'bg-cyan-100 text-cyan-700' },
    { value: 'mediacion', label: 'Mediación / Arbitraje', icon: '🤝', description: 'Resolución alternativa de conflictos', color: 'bg-orange-100 text-orange-700' },
    { value: 'contrato', label: 'Administración de Contratos', icon: '📄', description: 'Redacción, negociación y seguimiento de contratos', color: 'bg-indigo-100 text-indigo-700' },
    { value: 'due_diligence', label: 'Due Diligence', icon: '🔍', description: 'Auditoría legal / investigación exhaustiva', color: 'bg-rose-100 text-rose-700' },
    { value: 'propiedad_intelectual', label: 'Propiedad Intelectual', icon: '🏷️', description: 'Marcas, patentes y derechos de autor', color: 'bg-fuchsia-100 text-fuchsia-700' },
    { value: 'gestion_corporativa', label: 'Gestión Corporativa', icon: '🏢', description: 'Mantenimiento societario y gobierno corporativo', color: 'bg-teal-100 text-teal-700' },
];

// === Participant Roles by Service Type ===
export const ROLES_POR_SERVICIO: Record<TipoServicio, { value: string; label: string }[]> = {
    litigio: [
        { value: 'demandante', label: 'Demandante / Actor' },
        { value: 'demandado', label: 'Demandado / Acusado' },
        { value: 'tercero_interesado', label: 'Tercero Interesado' },
        { value: 'tercero_excluyente', label: 'Tercero Excluyente' },
        { value: 'ministerio_publico', label: 'Ministerio Público' },
        { value: 'testigo', label: 'Testigo' },
        { value: 'perito', label: 'Perito' },
        { value: 'abogado_contraparte', label: 'Abogado Contraparte' },
    ],
    escritura: [
        { value: 'otorgante', label: 'Otorgante' },
        { value: 'adquiriente', label: 'Adquiriente' },
        { value: 'compareciente', label: 'Compareciente' },
        { value: 'testigo_instrumental', label: 'Testigo Instrumental' },
        { value: 'interprete', label: 'Intérprete' },
    ],
    contrato: [
        { value: 'parte_a', label: 'Parte A (Nuestro Cliente)' },
        { value: 'parte_b', label: 'Parte B (Contraparte)' },
        { value: 'garante', label: 'Garante / Fiador' },
    ],
    mediacion: [
        { value: 'parte_a', label: 'Parte A (Nuestro Cliente)' },
        { value: 'parte_b', label: 'Parte B' },
        { value: 'mediador', label: 'Mediador' },
        { value: 'arbitro', label: 'Árbitro' },
    ],
    tramite: [
        { value: 'solicitante', label: 'Solicitante' },
        { value: 'beneficiario', label: 'Beneficiario' },
        { value: 'gestor', label: 'Gestor Asignado' },
    ],
    consulta: [
        { value: 'cliente', label: 'Consultante' },
    ],
    asesoria: [
        { value: 'cliente', label: 'Cliente' },
        { value: 'contraparte', label: 'Contraparte (si aplica)' },
    ],
    due_diligence: [
        { value: 'cliente', label: 'Cliente Solicitante' },
        { value: 'contraparte', label: 'Empresa Objetivo' },
    ],
    propiedad_intelectual: [
        { value: 'solicitante', label: 'Titular / Solicitante' },
        { value: 'contraparte', label: 'Opositor (si aplica)' },
    ],
    gestion_corporativa: [
        { value: 'sociedad', label: 'Sociedad (Cliente)' },
        { value: 'socio_fundador', label: 'Socio / Accionista' },
        { value: 'representante', label: 'Representante Legal' },
    ],
};

export interface ParteProcesal {
    id: string;
    expediente_id: string;
    nombre_completo: string;
    tipo_persona: 'natural' | 'juridica';
    documento_identidad?: string;
    tipo_documento?: string;
    rol_procesal: string;
    representante_legal?: string;
    abogado_patrocinador?: string;
    direccion?: string;
    telefono?: string;
    email?: string;
    notas?: string;
    created_at?: string;
}

export interface Expediente {
    id: string;
    tenant_id: string;
    numero_interno?: string;
    numero_causa?: string;
    tipo_servicio: TipoServicio;
    ramo?: string;
    tipo_proceso?: string;
    materia_especifica?: string;
    juzgado?: string;
    juez?: string;
    secretario?: string;
    estado_id?: string;
    etapa_actual_id?: string;
    resumen?: string;
    fecha_apertura?: string;
    fecha_cierre?: string;
    abogado_responsable_id?: string;
    cliente_principal_id?: string;
    co_abogados?: string[];
    abogado_contraparte?: string;
    prioridad: 'baja' | 'normal' | 'alta' | 'urgente';
    valor_estimado?: number;
    moneda: string;
    observaciones_ia?: string;
    // Resolution fields
    tipo_resolucion?: string;
    numero_sentencia?: string;
    fecha_sentencia?: string;
    resultado_detalle?: string;
    monto_adjudicado?: number;
    recurso_pendiente?: boolean;
    // Materia specific
    datos_materia?: Record<string, string | number | boolean>;
    created_at: string;
    updated_at: string;
    partes?: ParteProcesal[];
}

export interface ExpedienteListResponse {
    items: Expediente[];
    total: number;
    page: number;
    size: number;
}

export interface CaseStatus {
    id: string;
    codigo: string;
    nombre: string;
    color_hex?: string;
    es_final: boolean;
    orden: number;
}

export interface WorkflowStage {
    id: string;
    ramo?: string;
    tipo_servicio?: string;
    tipo_proceso?: string;
    nombre: string;
    orden: number;
    dias_plazo_legal?: number;
    es_final: boolean;
}
