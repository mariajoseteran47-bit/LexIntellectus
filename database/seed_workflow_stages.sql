-- ============================================================
-- LexIntellectus — Seed: Etapas Procesales por Ramo Jurídico
-- Cada ramo tiene su propio flujo procesal con plazos legales
-- Jurisdicción: Nicaragua
-- ============================================================

-- Usar el tenant_id del despacho principal
-- Ajustar este UUID al tenant real de su instalación
DO $$
DECLARE
    v_tenant_id UUID;
BEGIN
    -- Obtener el primer tenant (ajustar si es necesario)
    SELECT id INTO v_tenant_id FROM tenants LIMIT 1;
    
    IF v_tenant_id IS NULL THEN
        RAISE NOTICE 'No hay tenants. Cree uno antes de ejecutar este seed.';
        RETURN;
    END IF;

    -- ========================================
    -- CIVIL ORDINARIO
    -- ========================================
    INSERT INTO workflow_stages (id, tenant_id, ramo, tipo_proceso, codigo, nombre, descripcion, orden, dias_plazo_legal, tipo_dias, base_legal, es_final) VALUES
    (gen_random_uuid(), v_tenant_id, 'civil', 'ordinario', 'demanda', 'Demanda', 'Presentación de la demanda ante el juzgado competente', 1, NULL, 'habiles', 'Art. 420 CPC', false),
    (gen_random_uuid(), v_tenant_id, 'civil', 'ordinario', 'emplazamiento', 'Emplazamiento', 'Notificación al demandado para que conteste', 2, 3, 'habiles', 'Art. 428 CPC', false),
    (gen_random_uuid(), v_tenant_id, 'civil', 'ordinario', 'contestacion', 'Contestación de Demanda', 'Plazo del demandado para contestar y/o reconvenir', 3, 30, 'habiles', 'Art. 430 CPC', false),
    (gen_random_uuid(), v_tenant_id, 'civil', 'ordinario', 'excepciones', 'Excepciones Previas', 'Resolución de excepciones dilatorias y perentorias', 4, 15, 'habiles', 'Art. 432 CPC', false),
    (gen_random_uuid(), v_tenant_id, 'civil', 'ordinario', 'pruebas_apertura', 'Apertura a Pruebas', 'Auto de apertura del periodo probatorio', 5, NULL, 'habiles', 'Art. 444 CPC', false),
    (gen_random_uuid(), v_tenant_id, 'civil', 'ordinario', 'pruebas_periodo', 'Periodo Probatorio', 'Evacuación de pruebas documentales, testimoniales, periciales', 6, 30, 'habiles', 'Art. 446 CPC', false),
    (gen_random_uuid(), v_tenant_id, 'civil', 'ordinario', 'alegatos', 'Alegatos de Bien Probado', 'Presentación de los argumentos finales de ambas partes', 7, 6, 'habiles', 'Art. 448 CPC', false),
    (gen_random_uuid(), v_tenant_id, 'civil', 'ordinario', 'sentencia_1ra', 'Sentencia Primera Instancia', 'Dictado de sentencia por el juez de primera instancia', 8, 15, 'habiles', 'Art. 450 CPC', false),
    (gen_random_uuid(), v_tenant_id, 'civil', 'ordinario', 'apelacion', 'Recurso de Apelación', 'Interposición de apelación ante tribunal de alzada', 9, 3, 'habiles', 'Art. 460 CPC', false),
    (gen_random_uuid(), v_tenant_id, 'civil', 'ordinario', 'sentencia_2da', 'Sentencia Segunda Instancia', 'Resolución del tribunal de apelaciones', 10, 30, 'habiles', 'Art. 465 CPC', false),
    (gen_random_uuid(), v_tenant_id, 'civil', 'ordinario', 'casacion', 'Recurso de Casación', 'Recurso extraordinario ante la Corte Suprema', 11, 15, 'calendario', 'Art. 470 CPC', false),
    (gen_random_uuid(), v_tenant_id, 'civil', 'ordinario', 'ejecutoria', 'Sentencia Firme / Ejecutoria', 'La sentencia adquiere firmeza y es ejecutable', 12, NULL, 'habiles', NULL, true);

    -- ========================================
    -- CIVIL EJECUTIVO
    -- ========================================
    INSERT INTO workflow_stages (id, tenant_id, ramo, tipo_proceso, codigo, nombre, descripcion, orden, dias_plazo_legal, tipo_dias, base_legal, es_final) VALUES
    (gen_random_uuid(), v_tenant_id, 'civil', 'ejecutivo', 'demanda_ejecutiva', 'Demanda Ejecutiva', 'Presentación con título ejecutivo (pagaré, letra, sentencia)', 1, NULL, 'habiles', 'Art. 509 CPC', false),
    (gen_random_uuid(), v_tenant_id, 'civil', 'ejecutivo', 'auto_solvendo', 'Auto Solvendo', 'Orden judicial de pago o embargo', 2, 3, 'habiles', 'Art. 510 CPC', false),
    (gen_random_uuid(), v_tenant_id, 'civil', 'ejecutivo', 'embargo', 'Embargo de Bienes', 'Práctica del embargo sobre bienes del deudor', 3, NULL, 'habiles', 'Art. 512 CPC', false),
    (gen_random_uuid(), v_tenant_id, 'civil', 'ejecutivo', 'oposicion', 'Oposición / Excepciones', 'Plazo para que el ejecutado oponga excepciones', 4, 6, 'habiles', 'Art. 515 CPC', false),
    (gen_random_uuid(), v_tenant_id, 'civil', 'ejecutivo', 'pruebas_ej', 'Periodo de Pruebas', 'Si hay excepciones, se abre periodo probatorio reducido', 5, 8, 'habiles', 'Art. 518 CPC', false),
    (gen_random_uuid(), v_tenant_id, 'civil', 'ejecutivo', 'sentencia_remate', 'Sentencia de Remate', 'Sentencia que ordena el remate de bienes embargados', 6, 8, 'habiles', 'Art. 520 CPC', false),
    (gen_random_uuid(), v_tenant_id, 'civil', 'ejecutivo', 'ejecucion', 'Ejecución / Remate', 'Ejecución forzosa o pago voluntario', 7, NULL, 'habiles', NULL, true);

    -- ========================================
    -- PENAL
    -- ========================================
    INSERT INTO workflow_stages (id, tenant_id, ramo, tipo_proceso, codigo, nombre, descripcion, orden, dias_plazo_legal, tipo_dias, base_legal, es_final) VALUES
    (gen_random_uuid(), v_tenant_id, 'penal', 'ordinario', 'denuncia', 'Denuncia / Querella', 'Presentación de la denuncia o querella ante MP o juzgado', 1, NULL, 'habiles', 'Art. 222 CPP', false),
    (gen_random_uuid(), v_tenant_id, 'penal', 'ordinario', 'investigacion', 'Investigación', 'Fase de investigación dirigida por el Ministerio Público', 2, 90, 'calendario', 'Art. 253 CPP', false),
    (gen_random_uuid(), v_tenant_id, 'penal', 'ordinario', 'audiencia_preliminar', 'Audiencia Preliminar', 'Evaluación de evidencia para determinar causa probable', 3, NULL, 'habiles', 'Art. 265 CPP', false),
    (gen_random_uuid(), v_tenant_id, 'penal', 'ordinario', 'auto_prision', 'Auto de Prisión / Libertad', 'Resolución sobre medida cautelar personal', 4, NULL, 'habiles', 'Art. 268 CPP', false),
    (gen_random_uuid(), v_tenant_id, 'penal', 'ordinario', 'intercambio', 'Intercambio de Información', 'Fase de descubrimiento de pruebas entre partes', 5, 5, 'habiles', 'Art. 270 CPP', false),
    (gen_random_uuid(), v_tenant_id, 'penal', 'ordinario', 'acusacion', 'Acusación Formal', 'Presentación de la acusación por el MP', 6, NULL, 'habiles', 'Art. 272 CPP', false),
    (gen_random_uuid(), v_tenant_id, 'penal', 'ordinario', 'audiencia_inicial', 'Audiencia Inicial', 'Lectura de acusación y fijación de fecha de juicio', 7, NULL, 'habiles', 'Art. 275 CPP', false),
    (gen_random_uuid(), v_tenant_id, 'penal', 'ordinario', 'juicio_oral', 'Juicio Oral y Público', 'Desarrollo del juicio con evacuación de pruebas', 8, NULL, 'habiles', 'Art. 281 CPP', false),
    (gen_random_uuid(), v_tenant_id, 'penal', 'ordinario', 'deliberacion', 'Deliberación', 'Deliberación del juez o jurado', 9, 5, 'habiles', 'Art. 317 CPP', false),
    (gen_random_uuid(), v_tenant_id, 'penal', 'ordinario', 'sentencia_penal', 'Sentencia', 'Dictado del fallo (absolutoria o condenatoria)', 10, 5, 'habiles', 'Art. 319 CPP', false),
    (gen_random_uuid(), v_tenant_id, 'penal', 'ordinario', 'apelacion_penal', 'Apelación', 'Recurso ante tribunal de apelaciones', 11, 6, 'habiles', 'Art. 361 CPP', false),
    (gen_random_uuid(), v_tenant_id, 'penal', 'ordinario', 'casacion_penal', 'Casación', 'Recurso extraordinario ante CSJ', 12, 10, 'calendario', 'Art. 369 CPP', false),
    (gen_random_uuid(), v_tenant_id, 'penal', 'ordinario', 'ejecutoria_penal', 'Sentencia Firme', 'Sentencia en firme', 13, NULL, 'habiles', NULL, true);

    -- ========================================
    -- FAMILIA — DIVORCIO CONTENCIOSO
    -- ========================================
    INSERT INTO workflow_stages (id, tenant_id, ramo, tipo_proceso, codigo, nombre, descripcion, orden, dias_plazo_legal, tipo_dias, base_legal, es_final) VALUES
    (gen_random_uuid(), v_tenant_id, 'familia', 'divorcio_contencioso', 'solicitud_div', 'Solicitud de Divorcio', 'Presentación de la solicitud con causales', 1, NULL, 'habiles', 'Art. 129 CF', false),
    (gen_random_uuid(), v_tenant_id, 'familia', 'divorcio_contencioso', 'emplazamiento_div', 'Emplazamiento', 'Notificación al cónyuge demandado', 2, 5, 'habiles', 'Art. 530 CPC', false),
    (gen_random_uuid(), v_tenant_id, 'familia', 'divorcio_contencioso', 'contestacion_div', 'Contestación', 'Respuesta del cónyuge demandado', 3, 10, 'habiles', 'Art. 131 CF', false),
    (gen_random_uuid(), v_tenant_id, 'familia', 'divorcio_contencioso', 'mediacion', 'Mediación Familiar', 'Trámite de mediación obligatorio (puede durar hasta 2 sesiones)', 4, 15, 'habiles', 'Art. 132 CF', false),
    (gen_random_uuid(), v_tenant_id, 'familia', 'divorcio_contencioso', 'medidas_prov', 'Medidas Provisionales', 'Pensión provisional, guarda provisional, régimen de visitas', 5, NULL, 'habiles', 'Art. 133 CF', false),
    (gen_random_uuid(), v_tenant_id, 'familia', 'divorcio_contencioso', 'audiencia_vista', 'Audiencia de Vista', 'Audiencia principal con evacuación de pruebas', 6, NULL, 'habiles', 'Art. 536 CPC', false),
    (gen_random_uuid(), v_tenant_id, 'familia', 'divorcio_contencioso', 'sentencia_fam', 'Sentencia', 'Resolución del divorcio, pensión definitiva, guarda', 7, 10, 'habiles', 'Art. 134 CF', false),
    (gen_random_uuid(), v_tenant_id, 'familia', 'divorcio_contencioso', 'liquidacion', 'Liquidación de Bienes', 'Partición de bienes gananciales y sociedad conyugal', 8, 30, 'habiles', 'Art. 136 CF', false),
    (gen_random_uuid(), v_tenant_id, 'familia', 'divorcio_contencioso', 'ejecutoria_fam', 'Sentencia Firme', 'Inscripción en Registro Civil', 9, NULL, 'habiles', NULL, true);

    -- ========================================
    -- FAMILIA — PENSIÓN ALIMENTICIA
    -- ========================================
    INSERT INTO workflow_stages (id, tenant_id, ramo, tipo_proceso, codigo, nombre, descripcion, orden, dias_plazo_legal, tipo_dias, base_legal, es_final) VALUES
    (gen_random_uuid(), v_tenant_id, 'familia', 'pension_alimenticia', 'solicitud_pa', 'Solicitud de Pensión', 'Presentación de demanda de pensión alimenticia', 1, NULL, 'habiles', 'Art. 306 CF', false),
    (gen_random_uuid(), v_tenant_id, 'familia', 'pension_alimenticia', 'pension_prov', 'Pensión Provisional', 'Fijación de pensión provisional mientras dura el proceso', 2, 3, 'habiles', 'Art. 320 CF', false),
    (gen_random_uuid(), v_tenant_id, 'familia', 'pension_alimenticia', 'mediacion_pa', 'Mediación', 'Trámite conciliatorio ante el juzgado', 3, 15, 'habiles', 'Art. 321 CF', false),
    (gen_random_uuid(), v_tenant_id, 'familia', 'pension_alimenticia', 'pruebas_pa', 'Periodo Probatorio', 'Pruebas de ingresos, gastos, necesidades', 4, 15, 'habiles', 'Art. 323 CF', false),
    (gen_random_uuid(), v_tenant_id, 'familia', 'pension_alimenticia', 'sentencia_pa', 'Sentencia de Pensión', 'Fijación definitiva del monto de pensión', 5, 8, 'habiles', 'Art. 325 CF', true);

    -- ========================================
    -- LABORAL
    -- ========================================
    INSERT INTO workflow_stages (id, tenant_id, ramo, tipo_proceso, codigo, nombre, descripcion, orden, dias_plazo_legal, tipo_dias, base_legal, es_final) VALUES
    (gen_random_uuid(), v_tenant_id, 'laboral', 'ordinario', 'demanda_lab', 'Demanda Laboral', 'Presentación de la demanda ante el juzgado del trabajo', 1, NULL, 'habiles', 'Art. 274 CT', false),
    (gen_random_uuid(), v_tenant_id, 'laboral', 'ordinario', 'conciliacion_lab', 'Trámite Conciliatorio', 'Audiencia de conciliación obligatoria', 2, 10, 'habiles', 'Art. 276 CT', false),
    (gen_random_uuid(), v_tenant_id, 'laboral', 'ordinario', 'contestacion_lab', 'Contestación', 'Respuesta del empleador a la demanda', 3, 6, 'habiles', 'Art. 278 CT', false),
    (gen_random_uuid(), v_tenant_id, 'laboral', 'ordinario', 'pruebas_lab', 'Periodo Probatorio', 'Evacuación de pruebas (inversión carga probatoria)', 4, 10, 'habiles', 'Art. 280 CT', false),
    (gen_random_uuid(), v_tenant_id, 'laboral', 'ordinario', 'alegatos_lab', 'Alegatos', 'Alegatos finales de ambas partes', 5, 3, 'habiles', 'Art. 283 CT', false),
    (gen_random_uuid(), v_tenant_id, 'laboral', 'ordinario', 'sentencia_lab', 'Sentencia Laboral', 'Fallo del juez sobre prestaciones y derechos', 6, 10, 'habiles', 'Art. 285 CT', false),
    (gen_random_uuid(), v_tenant_id, 'laboral', 'ordinario', 'apelacion_lab', 'Apelación', 'Recurso ante tribunal de apelaciones del trabajo', 7, 3, 'habiles', 'Art. 350 CT', false),
    (gen_random_uuid(), v_tenant_id, 'laboral', 'ordinario', 'ejecutoria_lab', 'Sentencia Firme', 'Sentencia ejecutoriada y cálculo de liquidación final', 8, NULL, 'habiles', NULL, true);

    -- ========================================
    -- MERCANTIL — COBRO EJECUTIVO
    -- ========================================
    INSERT INTO workflow_stages (id, tenant_id, ramo, tipo_proceso, codigo, nombre, descripcion, orden, dias_plazo_legal, tipo_dias, base_legal, es_final) VALUES
    (gen_random_uuid(), v_tenant_id, 'mercantil', 'cobro_ejecutivo', 'demanda_merc', 'Demanda Ejecutiva Mercantil', 'Cobro basado en título valor (letra, pagaré, cheque)', 1, NULL, 'habiles', 'Art. 509 CPC / CC', false),
    (gen_random_uuid(), v_tenant_id, 'mercantil', 'cobro_ejecutivo', 'auto_solvendo_m', 'Auto Solvendo', 'Intimación de pago y orden de embargo', 2, 3, 'habiles', 'Art. 510 CPC', false),
    (gen_random_uuid(), v_tenant_id, 'mercantil', 'cobro_ejecutivo', 'embargo_merc', 'Embargo', 'Práctica del embargo sobre bienes del deudor', 3, NULL, 'habiles', 'Art. 512 CPC', false),
    (gen_random_uuid(), v_tenant_id, 'mercantil', 'cobro_ejecutivo', 'oposicion_merc', 'Oposición', 'Excepciones del ejecutado', 4, 6, 'habiles', 'Art. 515 CPC', false),
    (gen_random_uuid(), v_tenant_id, 'mercantil', 'cobro_ejecutivo', 'sentencia_merc', 'Sentencia de Remate', 'Orden de remate y ejecución', 5, 8, 'habiles', 'Art. 520 CPC', false),
    (gen_random_uuid(), v_tenant_id, 'mercantil', 'cobro_ejecutivo', 'ejecucion_merc', 'Ejecución', 'Remate o pago', 6, NULL, 'habiles', NULL, true);

    RAISE NOTICE 'Seed de etapas procesales completado para tenant %', v_tenant_id;
END $$;
