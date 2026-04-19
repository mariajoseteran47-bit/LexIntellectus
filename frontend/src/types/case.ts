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
    ramo: string;
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
