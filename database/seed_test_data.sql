-- LexIntellectus Test Data Population
-- Run: docker exec lexintellectus-db psql -U lexintellectus -f /docker-entrypoint-initdb.d/seed.sql lexintellectus

-- Get tenant_id and user_id
DO $$
DECLARE
    v_tenant_id UUID;
    v_user_id UUID;
    v_sede_id UUID;
    v_status_activo UUID;
    v_status_tramite UUID;
    v_case_id UUID;
BEGIN
    -- Get existing tenant and user
    SELECT id INTO v_tenant_id FROM tenants LIMIT 1;
    SELECT id, sede_id INTO v_user_id, v_sede_id FROM users WHERE tenant_id = v_tenant_id LIMIT 1;

    IF v_tenant_id IS NULL OR v_user_id IS NULL THEN
        RAISE EXCEPTION 'No tenant or user found. Register first!';
    END IF;

    RAISE NOTICE 'Tenant: %, User: %', v_tenant_id, v_user_id;

    -- Clean existing test data (idempotent)
    DELETE FROM deadlines WHERE expediente_id IN (SELECT id FROM cases WHERE tenant_id = v_tenant_id);
    DELETE FROM case_parties WHERE expediente_id IN (SELECT id FROM cases WHERE tenant_id = v_tenant_id);
    DELETE FROM cases WHERE tenant_id = v_tenant_id;
    DELETE FROM case_statuses WHERE tenant_id = v_tenant_id;

    -- 1. Create Case Statuses
    v_status_activo := gen_random_uuid();
    v_status_tramite := gen_random_uuid();

    INSERT INTO case_statuses (id, tenant_id, codigo, nombre, color_hex, es_final, orden, created_at) VALUES
        (v_status_activo, v_tenant_id, 'activo', 'Activo', '#22c55e', false, 1, NOW()),
        (v_status_tramite, v_tenant_id, 'en_tramite', 'En Trámite', '#3b82f6', false, 2, NOW()),
        (gen_random_uuid(), v_tenant_id, 'suspendido', 'Suspendido', '#f59e0b', false, 3, NOW()),
        (gen_random_uuid(), v_tenant_id, 'cerrado', 'Cerrado', '#6b7280', true, 4, NOW()),
        (gen_random_uuid(), v_tenant_id, 'archivado', 'Archivado', '#9ca3af', true, 5, NOW());

    RAISE NOTICE 'Case statuses created';

    -- 2. Case 1: Cobro Civil
    v_case_id := gen_random_uuid();
    INSERT INTO cases (id, tenant_id, sede_id, numero_interno, numero_causa, ramo, materia_especifica, juzgado, juez, secretario, estado_id, resumen, fecha_apertura, abogado_responsable_id, prioridad, valor_estimado, moneda, created_at, updated_at) VALUES
        (v_case_id, v_tenant_id, v_sede_id, 'EXP-20260001', '001456-ORM4-2026-CV', 'civil', 'Cobro de Bolívares',
         'Juzgado Primero Civil de Distrito de Managua', 'Dra. María Elena Sandoval Gutiérrez', 'Lic. Roberto Caldera Mora',
         v_status_activo, 'Demanda ordinaria de cobro por incumplimiento de contrato de compraventa. El demandante reclama C$450,000.00 más intereses legales y costas procesales.',
         CURRENT_DATE - INTERVAL '56 days', v_user_id, 'alta', 450000.00, 'NIO', NOW(), NOW());

    INSERT INTO case_parties (id, expediente_id, nombre_completo, tipo_persona, documento_identidad, tipo_documento, rol_procesal, representante_legal, telefono, created_at, updated_at) VALUES
        (gen_random_uuid(), v_case_id, 'Inversiones del Pacífico S.A.', 'juridica', 'J0310000012345', 'ruc', 'demandante', 'Lic. Alejandro Mejía Vásquez', '+505 2222-3344', NOW(), NOW()),
        (gen_random_uuid(), v_case_id, 'Comercializadora La Fe, S.A.', 'juridica', 'J0310000098765', 'ruc', 'demandado', NULL, '+505 2255-6677', NOW(), NOW());

    INSERT INTO deadlines (id, expediente_id, descripcion, tipo_plazo, fecha_inicio, fecha_vencimiento, base_legal, usuario_responsable_id, status, prioridad, created_at, updated_at) VALUES
        (gen_random_uuid(), v_case_id, 'Contestación de demanda', 'procesal', CURRENT_DATE, CURRENT_DATE + INTERVAL '10 days', 'Art. 259 CPC', v_user_id, 'pendiente', 'critica', NOW(), NOW()),
        (gen_random_uuid(), v_case_id, 'Período de pruebas', 'procesal', CURRENT_DATE, CURRENT_DATE + INTERVAL '30 days', 'Art. 267 CPC', v_user_id, 'pendiente', 'alta', NOW(), NOW());

    RAISE NOTICE 'Case 1 created: Cobro Civil';

    -- 3. Case 2: Penal - Estafa
    v_case_id := gen_random_uuid();
    INSERT INTO cases (id, tenant_id, sede_id, numero_interno, numero_causa, ramo, materia_especifica, juzgado, juez, secretario, estado_id, resumen, fecha_apertura, abogado_responsable_id, prioridad, valor_estimado, moneda, created_at, updated_at) VALUES
        (v_case_id, v_tenant_id, v_sede_id, 'EXP-20260002', '002189-ORM2-2026-PE', 'penal', 'Estafa agravada',
         'Juzgado Segundo de Distrito Penal de Managua', 'Dr. Carlos Alberto Hernández López', 'Lic. Ana María Rivas',
         v_status_activo, 'Acusación por estafa agravada en perjuicio de 15 personas por venta fraudulenta de lotes en Residencial Los Pinos. Monto defraudado: USD 120,000.',
         CURRENT_DATE - INTERVAL '49 days', v_user_id, 'urgente', 120000.00, 'USD', NOW(), NOW());

    INSERT INTO case_parties (id, expediente_id, nombre_completo, tipo_persona, rol_procesal, created_at, updated_at) VALUES
        (gen_random_uuid(), v_case_id, 'Estado de Nicaragua (Ministerio Público)', 'juridica', 'ministerio_publico', NOW(), NOW());
    INSERT INTO case_parties (id, expediente_id, nombre_completo, tipo_persona, documento_identidad, tipo_documento, rol_procesal, created_at, updated_at) VALUES
        (gen_random_uuid(), v_case_id, 'Marco Antonio Blandón Rojas', 'natural', '001-250785-0023T', 'cedula', 'demandado', NOW(), NOW()),
        (gen_random_uuid(), v_case_id, 'Rosa Elvira Guzmán Pérez', 'natural', '001-180990-0045K', 'cedula', 'demandante', NOW(), NOW());

    INSERT INTO deadlines (id, expediente_id, descripcion, tipo_plazo, fecha_inicio, fecha_vencimiento, base_legal, usuario_responsable_id, status, prioridad, created_at, updated_at) VALUES
        (gen_random_uuid(), v_case_id, 'Audiencia inicial', 'procesal', CURRENT_DATE, CURRENT_DATE + INTERVAL '5 days', 'Art. 265 CPP', v_user_id, 'pendiente', 'critica', NOW(), NOW());

    RAISE NOTICE 'Case 2 created: Estafa Penal';

    -- 4. Case 3: Familia - Divorcio
    v_case_id := gen_random_uuid();
    INSERT INTO cases (id, tenant_id, sede_id, numero_interno, numero_causa, ramo, materia_especifica, juzgado, juez, secretario, estado_id, resumen, fecha_apertura, abogado_responsable_id, prioridad, valor_estimado, moneda, created_at, updated_at) VALUES
        (v_case_id, v_tenant_id, v_sede_id, 'EXP-20260003', '000987-ORM1-2026-FM', 'familia', 'Divorcio por mutuo consentimiento',
         'Juzgado Primero de Familia de Managua', 'Dra. Lucía Fernanda Ortega Muñoz', 'Lic. Patricia Reyes Solís',
         v_status_tramite, 'Proceso de divorcio por mutuo consentimiento. Las partes han acordado la distribución de bienes gananciales y la custodia compartida de dos menores.',
         CURRENT_DATE - INTERVAL '42 days', v_user_id, 'normal', 0, 'NIO', NOW(), NOW());

    INSERT INTO case_parties (id, expediente_id, nombre_completo, tipo_persona, documento_identidad, tipo_documento, rol_procesal, telefono, created_at, updated_at) VALUES
        (gen_random_uuid(), v_case_id, 'José Manuel Torres Espinoza', 'natural', '001-120389-0012H', 'cedula', 'demandante', '+505 8876-5432', NOW(), NOW()),
        (gen_random_uuid(), v_case_id, 'María Gabriela Ruiz Lacayo', 'natural', '001-050491-0034L', 'cedula', 'demandado', '+505 8834-2211', NOW(), NOW());

    INSERT INTO deadlines (id, expediente_id, descripcion, tipo_plazo, fecha_inicio, fecha_vencimiento, base_legal, usuario_responsable_id, status, prioridad, created_at, updated_at) VALUES
        (gen_random_uuid(), v_case_id, 'Audiencia de mediación', 'procesal', CURRENT_DATE, CURRENT_DATE + INTERVAL '15 days', 'Art. 160 CF', v_user_id, 'pendiente', 'alta', NOW(), NOW()),
        (gen_random_uuid(), v_case_id, 'Sentencia estimada', 'procesal', CURRENT_DATE, CURRENT_DATE + INTERVAL '45 days', 'Art. 174 CF', v_user_id, 'pendiente', 'normal', NOW(), NOW());

    RAISE NOTICE 'Case 3 created: Divorcio Familia';

    -- 5. Case 4: Laboral - Despido
    v_case_id := gen_random_uuid();
    INSERT INTO cases (id, tenant_id, sede_id, numero_interno, numero_causa, ramo, materia_especifica, juzgado, juez, secretario, estado_id, resumen, fecha_apertura, abogado_responsable_id, prioridad, valor_estimado, moneda, created_at, updated_at) VALUES
        (v_case_id, v_tenant_id, v_sede_id, 'EXP-20260004', '003241-ORM3-2026-LB', 'laboral', 'Despido injustificado',
         'Juzgado Tercero de Trabajo de Managua', 'Dr. Francisco Javier Molina Ríos', 'Lic. Karla Vanessa Urbina',
         v_status_activo, 'Demanda por despido injustificado. El trabajador reclama prestaciones sociales, indemnización y salarios caídos por C$385,000.00.',
         CURRENT_DATE - INTERVAL '35 days', v_user_id, 'alta', 385000.00, 'NIO', NOW(), NOW());

    INSERT INTO case_parties (id, expediente_id, nombre_completo, tipo_persona, documento_identidad, tipo_documento, rol_procesal, representante_legal, created_at, updated_at) VALUES
        (gen_random_uuid(), v_case_id, 'Pedro Antonio Flores Castillo', 'natural', '001-090792-0067M', 'cedula', 'demandante', 'Lic. Sandra Guevara Paz', NOW(), NOW());
    INSERT INTO case_parties (id, expediente_id, nombre_completo, tipo_persona, documento_identidad, tipo_documento, rol_procesal, abogado_patrocinador, created_at, updated_at) VALUES
        (gen_random_uuid(), v_case_id, 'Distribuidora Nacional S.A.', 'juridica', 'J0310000054321', 'ruc', 'demandado', 'Lic. Humberto Morales Chen', NOW(), NOW());

    INSERT INTO deadlines (id, expediente_id, descripcion, tipo_plazo, fecha_inicio, fecha_vencimiento, base_legal, usuario_responsable_id, status, prioridad, created_at, updated_at) VALUES
        (gen_random_uuid(), v_case_id, 'Conciliación laboral', 'procesal', CURRENT_DATE, CURRENT_DATE + INTERVAL '8 days', 'Art. 326 CT', v_user_id, 'pendiente', 'alta', NOW(), NOW()),
        (gen_random_uuid(), v_case_id, 'Audiencia de juicio', 'procesal', CURRENT_DATE, CURRENT_DATE + INTERVAL '25 days', 'Art. 330 CT', v_user_id, 'pendiente', 'critica', NOW(), NOW());

    RAISE NOTICE 'Case 4 created: Despido Laboral';

    -- 6. Case 5: Mercantil - Incumplimiento
    v_case_id := gen_random_uuid();
    INSERT INTO cases (id, tenant_id, sede_id, numero_interno, numero_causa, ramo, materia_especifica, juzgado, juez, secretario, estado_id, resumen, fecha_apertura, abogado_responsable_id, prioridad, valor_estimado, moneda, created_at, updated_at) VALUES
        (v_case_id, v_tenant_id, v_sede_id, 'EXP-20260005', '004567-ORM5-2026-MR', 'mercantil', 'Incumplimiento contractual',
         'Juzgado Quinto Civil de Distrito de Managua', 'Dra. Elizabeth Chavarría Delgado', 'Lic. Miguel Ángel Bermúdez',
         v_status_activo, 'Demanda mercantil por incumplimiento de contrato de distribución exclusiva de productos farmacéuticos. Daños y perjuicios por USD 250,000.',
         CURRENT_DATE - INTERVAL '28 days', v_user_id, 'urgente', 250000.00, 'USD', NOW(), NOW());

    INSERT INTO case_parties (id, expediente_id, nombre_completo, tipo_persona, documento_identidad, tipo_documento, rol_procesal, created_at, updated_at) VALUES
        (gen_random_uuid(), v_case_id, 'Laboratorios Centroamericanos S.A.', 'juridica', 'J0310000011111', 'ruc', 'demandante', NOW(), NOW()),
        (gen_random_uuid(), v_case_id, 'Farmacias Unidas de Nicaragua S.A.', 'juridica', 'J0310000022222', 'ruc', 'demandado', NOW(), NOW());

    INSERT INTO deadlines (id, expediente_id, descripcion, tipo_plazo, fecha_inicio, fecha_vencimiento, base_legal, usuario_responsable_id, status, prioridad, created_at, updated_at) VALUES
        (gen_random_uuid(), v_case_id, 'Medida cautelar - embargo preventivo', 'procesal', CURRENT_DATE, CURRENT_DATE + INTERVAL '3 days', 'Art. 899 CC', v_user_id, 'pendiente', 'critica', NOW(), NOW());

    RAISE NOTICE 'Case 5 created: Mercantil';

    -- 7. Case 6: Sucesiones
    v_case_id := gen_random_uuid();
    INSERT INTO cases (id, tenant_id, sede_id, numero_interno, numero_causa, ramo, materia_especifica, juzgado, juez, secretario, estado_id, resumen, fecha_apertura, abogado_responsable_id, prioridad, valor_estimado, moneda, created_at, updated_at) VALUES
        (v_case_id, v_tenant_id, v_sede_id, 'EXP-20260006', '005678-ORM6-2026-SC', 'sucesiones', 'Declaratoria de herederos',
         'Juzgado Sexto Civil de Managua', 'Dr. Ramón Adolfo Zapata Luna', 'Lic. Gloria Elena Martínez',
         v_status_tramite, 'Proceso de declaratoria de herederos ab intestato. Masa sucesoria incluye dos propiedades en Managua y cuentas bancarias.',
         CURRENT_DATE - INTERVAL '21 days', v_user_id, 'normal', 800000.00, 'NIO', NOW(), NOW());

    INSERT INTO case_parties (id, expediente_id, nombre_completo, tipo_persona, documento_identidad, tipo_documento, rol_procesal, created_at, updated_at) VALUES
        (gen_random_uuid(), v_case_id, 'Laura Patricia Sánchez Montiel', 'natural', '001-300675-0089W', 'cedula', 'demandante', NOW(), NOW()),
        (gen_random_uuid(), v_case_id, 'Roberto Carlos Sánchez Montiel', 'natural', '001-150478-0045X', 'cedula', 'tercero_interesado', NOW(), NOW());

    INSERT INTO deadlines (id, expediente_id, descripcion, tipo_plazo, fecha_inicio, fecha_vencimiento, base_legal, usuario_responsable_id, status, prioridad, created_at, updated_at) VALUES
        (gen_random_uuid(), v_case_id, 'Publicación de edictos', 'procesal', CURRENT_DATE, CURRENT_DATE + INTERVAL '30 days', 'Art. 1200 CC', v_user_id, 'pendiente', 'normal', NOW(), NOW());

    RAISE NOTICE 'Case 6 created: Sucesiones';

    -- 8. Case 7: Administrativo - Amparo
    v_case_id := gen_random_uuid();
    INSERT INTO cases (id, tenant_id, sede_id, numero_interno, numero_causa, ramo, materia_especifica, juzgado, juez, secretario, estado_id, resumen, fecha_apertura, abogado_responsable_id, prioridad, valor_estimado, moneda, created_at, updated_at) VALUES
        (v_case_id, v_tenant_id, v_sede_id, 'EXP-20260007', '006789-ORM7-2026-AD', 'administrativo', 'Recurso de amparo',
         'Tribunal de Apelaciones de Managua, Sala Civil', 'Dra. Claudia Patricia Moreno Aráuz', 'Lic. Fernando Obregón Castro',
         v_status_activo, 'Recurso de amparo administrativo contra resolución del INSS que deniega pensión de invalidez parcial al recurrente.',
         CURRENT_DATE - INTERVAL '14 days', v_user_id, 'alta', 0, 'NIO', NOW(), NOW());

    INSERT INTO case_parties (id, expediente_id, nombre_completo, tipo_persona, documento_identidad, tipo_documento, rol_procesal, created_at, updated_at) VALUES
        (gen_random_uuid(), v_case_id, 'Julio César Alemán Díaz', 'natural', '001-221180-0034R', 'cedula', 'demandante', NOW(), NOW());
    INSERT INTO case_parties (id, expediente_id, nombre_completo, tipo_persona, rol_procesal, created_at, updated_at) VALUES
        (gen_random_uuid(), v_case_id, 'Instituto Nicaragüense de Seguridad Social (INSS)', 'juridica', 'demandado', NOW(), NOW());

    INSERT INTO deadlines (id, expediente_id, descripcion, tipo_plazo, fecha_inicio, fecha_vencimiento, base_legal, usuario_responsable_id, status, prioridad, created_at, updated_at) VALUES
        (gen_random_uuid(), v_case_id, 'Informe del recurrido (INSS)', 'procesal', CURRENT_DATE, CURRENT_DATE + INTERVAL '10 days', 'Art. 26 Ley de Amparo', v_user_id, 'pendiente', 'alta', NOW(), NOW());

    RAISE NOTICE 'Case 7 created: Amparo Administrativo';

    -- 9. Case 8: Civil - Reivindicación
    v_case_id := gen_random_uuid();
    INSERT INTO cases (id, tenant_id, sede_id, numero_interno, numero_causa, ramo, materia_especifica, juzgado, juez, secretario, estado_id, resumen, fecha_apertura, abogado_responsable_id, prioridad, valor_estimado, moneda, created_at, updated_at) VALUES
        (v_case_id, v_tenant_id, v_sede_id, 'EXP-20260008', '007890-ORM8-2026-CV', 'civil', 'Reivindicación de inmueble',
         'Juzgado Octavo Civil de Managua', 'Dr. Armando José Vallejos Bravo', 'Lic. Nancy del Socorro Tinoco',
         v_status_activo, 'Acción reivindicatoria sobre inmueble en Altamira, 500 m². Controversia sobre doble inscripción registral.',
         CURRENT_DATE - INTERVAL '7 days', v_user_id, 'alta', 1200000.00, 'NIO', NOW(), NOW());

    INSERT INTO case_parties (id, expediente_id, nombre_completo, tipo_persona, documento_identidad, tipo_documento, rol_procesal, created_at, updated_at) VALUES
        (gen_random_uuid(), v_case_id, 'Bienes Raíces del Sur S.A.', 'juridica', 'J0310000033333', 'ruc', 'demandante', NOW(), NOW()),
        (gen_random_uuid(), v_case_id, 'Enrique Alberto Solís Peña', 'natural', '001-180865-0023N', 'cedula', 'demandado', NOW(), NOW());
    INSERT INTO case_parties (id, expediente_id, nombre_completo, tipo_persona, rol_procesal, created_at, updated_at) VALUES
        (gen_random_uuid(), v_case_id, 'Registrador de la Propiedad de Managua', 'juridica', 'tercero_interesado', NOW(), NOW());

    INSERT INTO deadlines (id, expediente_id, descripcion, tipo_plazo, fecha_inicio, fecha_vencimiento, base_legal, usuario_responsable_id, status, prioridad, created_at, updated_at) VALUES
        (gen_random_uuid(), v_case_id, 'Inspección judicial del inmueble', 'procesal', CURRENT_DATE, CURRENT_DATE + INTERVAL '20 days', 'Art. 2777 CC', v_user_id, 'pendiente', 'alta', NOW(), NOW()),
        (gen_random_uuid(), v_case_id, 'Presentación de peritaje', 'procesal', CURRENT_DATE, CURRENT_DATE + INTERVAL '35 days', 'Art. 331 CPC', v_user_id, 'pendiente', 'normal', NOW(), NOW());

    RAISE NOTICE 'Case 8 created: Reivindicación Civil';

    RAISE NOTICE 'All test data populated successfully!';
END $$;
