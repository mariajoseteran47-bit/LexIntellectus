-- ============================================
-- LexIntellectus - Seed: Default Roles & Permissions
-- Run this ONCE after initial DB setup.
-- ============================================

-- ╔══════════════════════════════════════════╗
-- ║          SYSTEM PERMISSIONS              ║
-- ╚══════════════════════════════════════════╝

INSERT INTO permissions (id, codigo, modulo, descripcion) VALUES
    -- Cases
    (gen_random_uuid(), 'cases.read', 'cases', 'Ver expedientes'),
    (gen_random_uuid(), 'cases.create', 'cases', 'Crear expedientes'),
    (gen_random_uuid(), 'cases.update', 'cases', 'Editar expedientes'),
    (gen_random_uuid(), 'cases.delete', 'cases', 'Eliminar expedientes'),
    -- Deadlines
    (gen_random_uuid(), 'deadlines.read', 'deadlines', 'Ver plazos fatales'),
    (gen_random_uuid(), 'deadlines.create', 'deadlines', 'Crear plazos fatales'),
    (gen_random_uuid(), 'deadlines.update', 'deadlines', 'Editar plazos fatales'),
    (gen_random_uuid(), 'deadlines.delete', 'deadlines', 'Eliminar plazos fatales'),
    -- Documents
    (gen_random_uuid(), 'documents.read', 'documents', 'Ver documentos'),
    (gen_random_uuid(), 'documents.create', 'documents', 'Subir documentos'),
    (gen_random_uuid(), 'documents.delete', 'documents', 'Eliminar documentos'),
    -- Users
    (gen_random_uuid(), 'users.read', 'users', 'Ver usuarios del despacho'),
    (gen_random_uuid(), 'users.create', 'users', 'Crear usuarios'),
    (gen_random_uuid(), 'users.update', 'users', 'Editar usuarios'),
    (gen_random_uuid(), 'users.delete', 'users', 'Desactivar usuarios'),
    -- Clients
    (gen_random_uuid(), 'clients.read', 'clients', 'Ver directorio de clientes'),
    (gen_random_uuid(), 'clients.create', 'clients', 'Crear clientes'),
    (gen_random_uuid(), 'clients.update', 'clients', 'Editar clientes'),
    -- Tenants / Settings
    (gen_random_uuid(), 'tenants.read', 'tenants', 'Ver información del despacho'),
    (gen_random_uuid(), 'tenants.update', 'tenants', 'Editar configuración del despacho'),
    (gen_random_uuid(), 'settings.read', 'settings', 'Ver configuración'),
    (gen_random_uuid(), 'settings.update', 'settings', 'Modificar configuración'),
    -- AI
    (gen_random_uuid(), 'ai.use', 'ai', 'Usar asistente legal con IA'),
    -- Knowledge / RAG
    (gen_random_uuid(), 'knowledge.read', 'knowledge', 'Ver base de conocimiento'),
    (gen_random_uuid(), 'knowledge.ingest', 'knowledge', 'Ingestar documentos legales'),
    -- Reports
    (gen_random_uuid(), 'reports.read', 'reports', 'Ver reportes y estadísticas'),
    -- Notifications
    (gen_random_uuid(), 'notifications.read', 'notifications', 'Ver notificaciones'),
    (gen_random_uuid(), 'notifications.manage', 'notifications', 'Administrar notificaciones')
ON CONFLICT (codigo) DO NOTHING;

-- ╔══════════════════════════════════════════╗
-- ║            SYSTEM ROLES                  ║
-- ╚══════════════════════════════════════════╝

-- System roles (tenant_id = NULL, es_sistema = true)
INSERT INTO roles (id, tenant_id, nombre, descripcion, es_sistema) VALUES
    (gen_random_uuid(), NULL, 'Administrador del Sistema', 'Acceso total a todas las funciones del sistema', true),
    (gen_random_uuid(), NULL, 'Administrador del Despacho', 'Administración completa del despacho y sus módulos', true),
    (gen_random_uuid(), NULL, 'Abogado', 'Gestión de expedientes, plazos, documentos y IA', true),
    (gen_random_uuid(), NULL, 'Notario', 'Gestión de casos notariales y validación de escrituras', true),
    (gen_random_uuid(), NULL, 'Secretaria', 'Gestión administrativa de expedientes y agenda', true),
    (gen_random_uuid(), NULL, 'Contador', 'Acceso a reportes financieros y facturación', true),
    (gen_random_uuid(), NULL, 'Gestor', 'Gestión de trámites y documentos', true),
    (gen_random_uuid(), NULL, 'Cliente', 'Acceso limitado a sus propios expedientes', true)
ON CONFLICT DO NOTHING;

-- ╔══════════════════════════════════════════╗
-- ║      ROLE-PERMISSION ASSIGNMENTS         ║
-- ╚══════════════════════════════════════════╝

-- Admin Despacho: all permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.nombre = 'Administrador del Despacho' AND r.es_sistema = true
ON CONFLICT DO NOTHING;

-- Abogado permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.nombre = 'Abogado' AND r.es_sistema = true
  AND p.codigo IN (
    'cases.read', 'cases.create', 'cases.update',
    'deadlines.read', 'deadlines.create', 'deadlines.update',
    'documents.read', 'documents.create',
    'clients.read', 'clients.create', 'clients.update',
    'ai.use', 'reports.read', 'notifications.read'
  )
ON CONFLICT DO NOTHING;

-- Notario permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.nombre = 'Notario' AND r.es_sistema = true
  AND p.codigo IN (
    'cases.read', 'cases.create', 'cases.update',
    'deadlines.read', 'deadlines.create', 'deadlines.update',
    'documents.read', 'documents.create',
    'clients.read', 'clients.create',
    'ai.use', 'notifications.read'
  )
ON CONFLICT DO NOTHING;

-- Secretaria permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.nombre = 'Secretaria' AND r.es_sistema = true
  AND p.codigo IN (
    'cases.read', 'cases.create',
    'deadlines.read', 'deadlines.create', 'deadlines.update',
    'documents.read', 'documents.create',
    'clients.read', 'clients.create',
    'notifications.read'
  )
ON CONFLICT DO NOTHING;

-- Contador permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.nombre = 'Contador' AND r.es_sistema = true
  AND p.codigo IN (
    'cases.read', 'reports.read', 'clients.read', 'notifications.read'
  )
ON CONFLICT DO NOTHING;

-- Gestor permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.nombre = 'Gestor' AND r.es_sistema = true
  AND p.codigo IN (
    'cases.read', 'deadlines.read',
    'documents.read', 'documents.create',
    'clients.read', 'notifications.read'
  )
ON CONFLICT DO NOTHING;

-- Cliente permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.nombre = 'Cliente' AND r.es_sistema = true
  AND p.codigo IN (
    'cases.read', 'documents.read', 'notifications.read'
  )
ON CONFLICT DO NOTHING;

-- Done!
SELECT 'Seed completed: ' || 
  (SELECT count(*) FROM permissions) || ' permissions, ' ||
  (SELECT count(*) FROM roles WHERE es_sistema = true) || ' system roles created.' AS result;
