-- ============================================================
-- LexIntellectus — Seed Completo de Demostración
-- Estados de Expediente, Plazos Fatales, Audit Logs,
-- Expedientes adicionales y Clientes
-- ============================================================

DO $$
DECLARE
    v_tenant_id UUID;
    v_admin_id UUID;
    v_case_id UUID;
    v_case2_id UUID;
    v_case3_id UUID;
    v_case4_id UUID;
    v_case5_id UUID;
    -- status IDs
    v_status_activo UUID := gen_random_uuid();
    v_status_tramite UUID := gen_random_uuid();
    v_status_espera UUID := gen_random_uuid();
    v_status_pruebas UUID := gen_random_uuid();
    v_status_sentencia UUID := gen_random_uuid();
    v_status_resuelto UUID := gen_random_uuid();
    v_status_archivado UUID := gen_random_uuid();
    -- client IDs
    v_client1_id UUID := gen_random_uuid();
    v_client2_id UUID := gen_random_uuid();
    v_client3_id UUID := gen_random_uuid();
BEGIN
    SELECT id INTO v_tenant_id FROM tenants LIMIT 1;
    SELECT id INTO v_admin_id FROM users WHERE tipo_usuario = 'admin_despacho' LIMIT 1;
    SELECT id INTO v_case_id FROM cases LIMIT 1;

    IF v_tenant_id IS NULL THEN
        RAISE NOTICE 'No hay tenants.';
        RETURN;
    END IF;

    -- ========================================
    -- 1. ESTADOS DE EXPEDIENTE (case_statuses)
    -- ========================================
    DELETE FROM case_statuses WHERE tenant_id = v_tenant_id;

    INSERT INTO case_statuses (id, tenant_id, codigo, nombre, color_hex, es_final, orden) VALUES
    (v_status_activo,    v_tenant_id, 'activo',    'Activo',        '#3B82F6', false, 1),
    (v_status_tramite,   v_tenant_id, 'tramite',   'En Trámite',    '#8B5CF6', false, 2),
    (v_status_espera,    v_tenant_id, 'espera',    'En Espera',     '#F59E0B', false, 3),
    (v_status_pruebas,   v_tenant_id, 'pruebas',   'En Pruebas',    '#06B6D4', false, 4),
    (v_status_sentencia, v_tenant_id, 'sentencia', 'En Sentencia',  '#EC4899', false, 5),
    (v_status_resuelto,  v_tenant_id, 'resuelto',  'Resuelto',      '#10B981', true,  6),
    (v_status_archivado, v_tenant_id, 'archivado', 'Archivado',     '#6B7280', true,  7);

    -- Update existing case to have a status
    IF v_case_id IS NOT NULL THEN
        UPDATE cases SET estado_id = v_status_tramite WHERE id = v_case_id;
    END IF;

    RAISE NOTICE '✅ Estados de expediente creados';

    -- ========================================
    -- 2. CLIENTES ADICIONALES
    -- ========================================
    INSERT INTO users (id, tenant_id, email, password_hash, nombre, apellido, tipo_usuario, tipo_vinculo, status, created_at, updated_at)
    VALUES
    (v_client1_id, v_tenant_id, 'mlopez@gmail.com', '$2b$12$dummy_hash_for_seed_data_only', 'María', 'López Flores', 'cliente', 'cliente', 'activo', NOW() - INTERVAL '30 days', NOW()),
    (v_client2_id, v_tenant_id, 'rcastillo@yahoo.com', '$2b$12$dummy_hash_for_seed_data_only', 'Roberto', 'Castillo Mejía', 'cliente', 'cliente', 'activo', NOW() - INTERVAL '20 days', NOW()),
    (v_client3_id, v_tenant_id, 'anavarro@hotmail.com', '$2b$12$dummy_hash_for_seed_data_only', 'Ana', 'Navarro Solís', 'cliente', 'cliente', 'activo', NOW() - INTERVAL '10 days', NOW())
    ON CONFLICT (email) DO NOTHING;

    RAISE NOTICE '✅ Clientes adicionales creados';

    -- ========================================
    -- 3. EXPEDIENTES ADICIONALES
    -- ========================================
    v_case2_id := gen_random_uuid();
    v_case3_id := gen_random_uuid();
    v_case4_id := gen_random_uuid();
    v_case5_id := gen_random_uuid();

    INSERT INTO cases (id, tenant_id, numero_interno, numero_causa, ramo, materia_especifica, juzgado, juez, estado_id, resumen, fecha_apertura, abogado_responsable_id, cliente_principal_id, prioridad, tipo_proceso, created_at, updated_at) VALUES
    (v_case2_id, v_tenant_id, 'EXP-202603150001', '001-0241-2026', 'penal', 'Estafa',
     'Juzgado Quinto de Distrito Penal de Managua', 'Dra. Carmen Solano',
     v_status_activo, 'Caso de estafa contra empresa ACME S.A. por emisión de cheques sin fondos por C$500,000.',
     '2026-03-15', v_admin_id, v_client1_id, 'urgente', 'ordinario', NOW() - INTERVAL '19 days', NOW()),

    (v_case3_id, v_tenant_id, 'EXP-202603200002', '002-0105-2026', 'familia', 'Divorcio Contencioso',
     'Juzgado Primero de Distrito de Familia de Managua', 'Dr. Luis Hernández',
     v_status_pruebas, 'Divorcio contencioso con disputa de custodia de dos menores y liquidación de bienes gananciales.',
     '2026-03-20', v_admin_id, v_client1_id, 'alta', 'divorcio_contencioso', NOW() - INTERVAL '14 days', NOW()),

    (v_case4_id, v_tenant_id, 'EXP-202603250003', '003-0089-2026', 'laboral', 'Despido Injustificado',
     'Juzgado del Trabajo de Managua', 'Dra. Patricia Gutiérrez',
     v_status_espera, 'Demanda por despido injustificado. Trabajador con 8 años de antigüedad. Reclamo de indemnización completa.',
     '2026-03-25', v_admin_id, v_client2_id, 'normal', 'ordinario', NOW() - INTERVAL '9 days', NOW()),

    (v_case5_id, v_tenant_id, 'EXP-202604010004', '004-0312-2026', 'mercantil', 'Cobro Ejecutivo',
     'Juzgado Tercero Civil de Distrito de Managua', 'Dr. Fernando Rivas',
     v_status_tramite, 'Cobro de pagaré vencido por US$25,000 contra deudor comercial. Título ejecutivo válido.',
     '2026-04-01', v_admin_id, v_client2_id, 'alta', 'cobro_ejecutivo', NOW() - INTERVAL '2 days', NOW());

    -- Add parties to cases
    INSERT INTO case_parties (id, expediente_id, nombre_completo, tipo_persona, documento_identidad, tipo_documento, rol_procesal, representante_legal, created_at, updated_at) VALUES
    -- Penal
    (gen_random_uuid(), v_case2_id, 'ACME S.A.', 'juridica', 'J0310000123456', 'ruc', 'demandante', 'Dr. Carlos Vega', NOW(), NOW()),
    (gen_random_uuid(), v_case2_id, 'Pedro Martínez Orozco', 'natural', '001-150385-0012K', 'cedula', 'demandado', NULL, NOW(), NOW()),
    -- Familia
    (gen_random_uuid(), v_case3_id, 'María López Flores', 'natural', '001-200590-0034H', 'cedula', 'demandante', NULL, NOW(), NOW()),
    (gen_random_uuid(), v_case3_id, 'Jorge Ramírez Umaña', 'natural', '001-180188-0056L', 'cedula', 'demandado', 'Lic. Rosa Mendoza', NOW(), NOW()),
    -- Laboral
    (gen_random_uuid(), v_case4_id, 'Carlos Eduardo Téllez', 'natural', '281-040792-0001N', 'cedula', 'demandante', NULL, NOW(), NOW()),
    (gen_random_uuid(), v_case4_id, 'Comercial San Martín S.A.', 'juridica', 'J0610000789012', 'ruc', 'demandado', 'Lic. Mario Ruiz', NOW(), NOW()),
    -- Mercantil
    (gen_random_uuid(), v_case5_id, 'Inversiones del Norte S.A.', 'juridica', 'J0810000345678', 'ruc', 'demandante', NULL, NOW(), NOW()),
    (gen_random_uuid(), v_case5_id, 'Roberto Castillo Mejía', 'natural', '001-120575-0023M', 'cedula', 'demandado', NULL, NOW(), NOW());

    RAISE NOTICE '✅ Expedientes y partes procesales creadas';

    -- ========================================
    -- 4. PLAZOS FATALES (deadlines)
    -- ========================================
    INSERT INTO deadlines (id, expediente_id, descripcion, tipo_plazo, fecha_inicio, fecha_vencimiento, hora_vencimiento, dias_tipo, base_legal, status, prioridad, created_at, updated_at) VALUES
    -- Vencidos (pasados)
    (gen_random_uuid(), v_case2_id, 'Presentar contestación de acusación', 'procesal',
     '2026-03-20', '2026-03-30', '17:00:00', 'habiles', 'Art. 265 CPP',
     'pendiente', 'alta', NOW() - INTERVAL '15 days', NOW()),

    -- Vence hoy
    (gen_random_uuid(), v_case3_id, 'Audiencia de mediación familiar', 'procesal',
     '2026-03-28', CURRENT_DATE, '10:00:00', 'habiles', 'Art. 132 CF',
     'pendiente', 'critica', NOW() - INTERVAL '6 days', NOW()),

    -- Vence mañana
    (gen_random_uuid(), v_case4_id, 'Contestación de demanda laboral', 'procesal',
     '2026-03-28', CURRENT_DATE + INTERVAL '1 day', '17:00:00', 'habiles', 'Art. 278 CT',
     'pendiente', 'alta', NOW() - INTERVAL '5 days', NOW()),

    -- Vence en 3 días
    (gen_random_uuid(), v_case5_id, 'Plazo para oposición al embargo', 'procesal',
     '2026-04-01', CURRENT_DATE + INTERVAL '3 days', '17:00:00', 'habiles', 'Art. 515 CPC',
     'pendiente', 'alta', NOW() - INTERVAL '2 days', NOW()),

    -- Vence en 5 días
    (gen_random_uuid(), v_case2_id, 'Intercambio de información probatoria', 'procesal',
     '2026-04-01', CURRENT_DATE + INTERVAL '5 days', '17:00:00', 'habiles', 'Art. 270 CPP',
     'pendiente', 'normal', NOW() - INTERVAL '2 days', NOW()),

    -- Vence en 7 días
    (gen_random_uuid(), v_case3_id, 'Presentar pruebas documentales', 'procesal',
     '2026-04-01', CURRENT_DATE + INTERVAL '7 days', '17:00:00', 'habiles', 'Art. 444 CPC',
     'pendiente', 'normal', NOW() - INTERVAL '2 days', NOW()),

    -- Vence en 15 días
    (gen_random_uuid(), v_case4_id, 'Periodo probatorio - evacuar prueba testimonial', 'procesal',
     '2026-04-03', CURRENT_DATE + INTERVAL '15 days', '23:59:59', 'habiles', 'Art. 280 CT',
     'pendiente', 'normal', NOW(), NOW()),

    -- Vence en 30 días
    (gen_random_uuid(), v_case3_id, 'Liquidación de sociedad conyugal', 'procesal',
     '2026-04-03', CURRENT_DATE + INTERVAL '30 days', '17:00:00', 'habiles', 'Art. 136 CF',
     'pendiente', 'normal', NOW(), NOW()),

    -- Cumplidos
    (gen_random_uuid(), v_case2_id, 'Presentar denuncia formal al MP', 'procesal',
     '2026-03-10', '2026-03-15', '17:00:00', 'habiles', 'Art. 222 CPP',
     'cumplido', 'alta', NOW() - INTERVAL '25 days', NOW()),

    (gen_random_uuid(), v_case5_id, 'Inscripción de demanda ejecutiva', 'procesal',
     '2026-03-28', '2026-04-01', '17:00:00', 'habiles', 'Art. 509 CPC',
     'cumplido', 'normal', NOW() - INTERVAL '5 days', NOW());

    RAISE NOTICE '✅ Plazos fatales creados';

    -- ========================================
    -- 5. REGISTROS DE AUDITORÍA (audit_logs)
    -- ========================================
    INSERT INTO audit_logs (id, tenant_id, user_id, accion, entidad, entidad_id, datos_antes, datos_despues, ip_address, user_agent, created_at) VALUES
    -- Login events
    (gen_random_uuid(), v_tenant_id, v_admin_id, 'login', 'usuario', v_admin_id,
     NULL, '{"email": "admin@lexintellectus.com"}'::jsonb,
     '192.168.1.100', 'Mozilla/5.0 Chrome/120', NOW() - INTERVAL '2 hours'),

    (gen_random_uuid(), v_tenant_id, v_admin_id, 'login', 'usuario', v_admin_id,
     NULL, '{"email": "admin@lexintellectus.com"}'::jsonb,
     '192.168.1.100', 'Mozilla/5.0 Chrome/120', NOW() - INTERVAL '1 day'),

    (gen_random_uuid(), v_tenant_id, v_admin_id, 'login', 'usuario', v_admin_id,
     NULL, '{"email": "admin@lexintellectus.com"}'::jsonb,
     '10.0.0.15', 'Mozilla/5.0 Safari/17', NOW() - INTERVAL '3 days'),

    -- Case creation events
    (gen_random_uuid(), v_tenant_id, v_admin_id, 'crear', 'expediente', v_case2_id,
     NULL, '{"ramo": "penal", "numero_interno": "EXP-202603150001", "materia": "Estafa"}'::jsonb,
     '192.168.1.100', 'Mozilla/5.0 Chrome/120', NOW() - INTERVAL '19 days'),

    (gen_random_uuid(), v_tenant_id, v_admin_id, 'crear', 'expediente', v_case3_id,
     NULL, '{"ramo": "familia", "numero_interno": "EXP-202603200002", "materia": "Divorcio"}'::jsonb,
     '192.168.1.100', 'Mozilla/5.0 Chrome/120', NOW() - INTERVAL '14 days'),

    (gen_random_uuid(), v_tenant_id, v_admin_id, 'crear', 'expediente', v_case4_id,
     NULL, '{"ramo": "laboral", "numero_interno": "EXP-202603250003", "materia": "Despido"}'::jsonb,
     '192.168.1.100', 'Mozilla/5.0 Chrome/120', NOW() - INTERVAL '9 days'),

    (gen_random_uuid(), v_tenant_id, v_admin_id, 'crear', 'expediente', v_case5_id,
     NULL, '{"ramo": "mercantil", "numero_interno": "EXP-202604010004", "materia": "Cobro"}'::jsonb,
     '192.168.1.100', 'Mozilla/5.0 Chrome/120', NOW() - INTERVAL '2 days'),

    -- Case updates
    (gen_random_uuid(), v_tenant_id, v_admin_id, 'actualizar', 'expediente', v_case2_id,
     '{"estado": "Activo"}'::jsonb, '{"estado": "En Trámite", "nota": "Avanzó a fase de investigación"}'::jsonb,
     '192.168.1.100', 'Mozilla/5.0 Chrome/120', NOW() - INTERVAL '10 days'),

    (gen_random_uuid(), v_tenant_id, v_admin_id, 'actualizar', 'expediente', v_case3_id,
     '{"estado": "En Trámite"}'::jsonb, '{"estado": "En Pruebas", "nota": "Se admitió prueba documental"}'::jsonb,
     '192.168.1.100', 'Mozilla/5.0 Chrome/120', NOW() - INTERVAL '7 days'),

    -- Deadline creation
    (gen_random_uuid(), v_tenant_id, v_admin_id, 'crear', 'plazo', NULL,
     NULL, '{"descripcion": "Contestación de acusación", "caso": "EXP-202603150001"}'::jsonb,
     '192.168.1.100', 'Mozilla/5.0 Chrome/120', NOW() - INTERVAL '15 days'),

    (gen_random_uuid(), v_tenant_id, v_admin_id, 'crear', 'plazo', NULL,
     NULL, '{"descripcion": "Audiencia de mediación familiar", "caso": "EXP-202603200002"}'::jsonb,
     '192.168.1.100', 'Mozilla/5.0 Chrome/120', NOW() - INTERVAL '6 days'),

    -- User creation
    (gen_random_uuid(), v_tenant_id, v_admin_id, 'crear', 'usuario', v_client1_id,
     NULL, '{"nombre": "María López Flores", "tipo": "cliente"}'::jsonb,
     '192.168.1.100', 'Mozilla/5.0 Chrome/120', NOW() - INTERVAL '30 days'),

    (gen_random_uuid(), v_tenant_id, v_admin_id, 'crear', 'usuario', v_client2_id,
     NULL, '{"nombre": "Roberto Castillo Mejía", "tipo": "cliente"}'::jsonb,
     '192.168.1.100', 'Mozilla/5.0 Chrome/120', NOW() - INTERVAL '20 days'),

    (gen_random_uuid(), v_tenant_id, v_admin_id, 'crear', 'usuario', v_client3_id,
     NULL, '{"nombre": "Ana Navarro Solís", "tipo": "cliente"}'::jsonb,
     '192.168.1.100', 'Mozilla/5.0 Chrome/120', NOW() - INTERVAL '10 days'),

    -- IA queries
    (gen_random_uuid(), v_tenant_id, v_admin_id, 'consulta_ia', 'expediente', v_case2_id,
     NULL, '{"modo": "estratega", "consulta": "¿Cuáles son las posibilidades de éxito en un caso de estafa por cheques sin fondos?"}'::jsonb,
     '192.168.1.100', 'Mozilla/5.0 Chrome/120', NOW() - INTERVAL '5 days'),

    (gen_random_uuid(), v_tenant_id, v_admin_id, 'consulta_ia', 'expediente', v_case3_id,
     NULL, '{"modo": "consultor", "consulta": "Requisitos para custodia compartida según Código de Familia de Nicaragua"}'::jsonb,
     '192.168.1.100', 'Mozilla/5.0 Chrome/120', NOW() - INTERVAL '3 days'),

    -- Document upload
    (gen_random_uuid(), v_tenant_id, v_admin_id, 'crear', 'documento', gen_random_uuid(),
     NULL, '{"nombre": "Poder General de Representación.pdf", "caso": "EXP-202603150001"}'::jsonb,
     '192.168.1.100', 'Mozilla/5.0 Chrome/120', NOW() - INTERVAL '18 days'),

    (gen_random_uuid(), v_tenant_id, v_admin_id, 'crear', 'documento', gen_random_uuid(),
     NULL, '{"nombre": "Acta de Matrimonio.pdf", "caso": "EXP-202603200002"}'::jsonb,
     '192.168.1.100', 'Mozilla/5.0 Chrome/120', NOW() - INTERVAL '13 days'),

    (gen_random_uuid(), v_tenant_id, v_admin_id, 'descarga', 'documento', gen_random_uuid(),
     NULL, '{"nombre": "Contrato Laboral.pdf"}'::jsonb,
     '192.168.1.100', 'Mozilla/5.0 Chrome/120', NOW() - INTERVAL '4 days');

    RAISE NOTICE '✅ Registros de auditoría creados';
    RAISE NOTICE '🎉 Seed completo finalizado para tenant %', v_tenant_id;
END $$;
