# LexIntellectus — Plan Estratégico Maestro v4.1
## Tres Dimensiones: Despacho · Cliente · Integraciones

> **Fecha:** 26 de Abril, 2026
> **Versión:** 4.1 — Reemplaza v3.0
> **Autor:** Equipo de Arquitectura LegalTech
> **Alcance:** Revisión integral de requerimientos, estado actual, brechas, y ruta de desarrollo.

> [!IMPORTANT]
> **INSTRUCCIÓN PARA AGENTES IA:** Este documento es la fuente de verdad del proyecto.
> Todo desarrollo futuro DEBE seguir las fases, sprints y prioridades aquí definidas.
> No saltar sprints ni reordenar prioridades sin aprobación explícita del usuario.
> Consultar siempre este archivo al inicio de cada sesión para determinar el próximo paso.

---

# PARTE I — ARQUITECTURA DEL SISTEMA (3 DIMENSIONES)

LexIntellectus NO es solo un gestor de expedientes judiciales.
Es una plataforma integral con tres dimensiones:

```
┌──────────────────────────────────────────────────────────────────────┐
│                        LEXINTELLECTUS                               │
│                                                                      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────────┐  │
│  │  🏛️ BACKOFFICE   │  │  👤 PORTAL       │  │  🔌 INTEGRACIONES │  │
│  │  DEL DESPACHO    │  │  DEL CLIENTE     │  │  EXTERNAS         │  │
│  │                  │  │                  │  │                   │  │
│  │ Abogados         │  │ Clientes del     │  │ Contabilidad      │  │
│  │ Notarios         │  │ despacho ven:    │  │ (QuickBooks,      │  │
│  │ Secretarias      │  │ - Sus asuntos    │  │  Xero, SAP,       │  │
│  │ Gestores         │  │ - Documentos     │  │  Alegra)          │  │
│  │ Admin            │  │ - Facturas       │  │                   │  │
│  │                  │  │ - Comunicación   │  │ Banca             │  │
│  │ Gestión interna  │  │ - Pagos online   │  │ (Conciliación)    │  │
│  │ completa         │  │ - Firmas         │  │                   │  │
│  │                  │  │                  │  │ Webhooks          │  │
│  │ /dashboard/*     │  │ /portal/*        │  │ (eventos en       │  │
│  │ /api/v1/*        │  │ /api/v1/portal/* │  │  tiempo real)     │  │
│  └──────────────────┘  └──────────────────┘  └───────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────────┐│
│  │  🧠 CORE: PostgreSQL + Redis + MinIO + IA (Gemini) + Multi-Tenant││
│  └──────────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────┘
```

## Arquitectura de APIs

```
/api/v1/
  ├── /auth/*                 ← Login, registro, refresh (todos)
  ├── /health                 ← Health check público
  │
  ├── /cases/*                ┐
  ├── /deadlines/*            │
  ├── /documents/*            │
  ├── /users/*                │
  ├── /dashboard/*            ├── BACKOFFICE (requiere JWT + tipo ≠ cliente)
  ├── /ai-agent/*             │
  ├── /audit/*                │
  ├── /reports/*              │
  ├── /client-profiles/*      │
  ├── /evidences/*            ┘
  │
  ├── /portal/*               ← PORTAL CLIENTE (requiere JWT + tipo = cliente)
  │    ├── /dashboard
  │    ├── /matters
  │    ├── /documents
  │    ├── /invoices
  │    ├── /threads
  │    └── /approvals
  │
  └── /public/*               ← INTEGRACIONES (requiere API Key)
       ├── /invoices
       ├── /payments
       ├── /clients
       ├── /matters/summary
       ├── /time-entries
       └── /webhooks
```

---

# PARTE II — INVENTARIO DEL SISTEMA ACTUAL

## 2.1 Infraestructura (Docker Compose)

| Componente | Tecnología | Estado |
|------------|-----------|--------|
| Base de Datos | PostgreSQL 16 + pgvector | ✅ Operativo |
| Caché / Colas | Redis 7 Alpine | ✅ Operativo |
| Almacenamiento de Objetos | MinIO (S3-compatible) | ✅ Operativo |
| Backend API | FastAPI (Python 3.11, asyncpg) | ✅ Operativo |
| Frontend | Next.js 14 + React 18 + Tailwind | ✅ Operativo |
| IA / Embeddings | Gemini 2.5 Flash + pgvector (3072 dim) | ✅ Operativo |
| Migraciones | Alembic | ⚠️ Parcialmente configurado |

## 2.2 Modelos de Datos Existentes

| Modelo | Tabla | Estado |
|--------|-------|--------|
| `Despacho` | tenants | ✅ Completo |
| `Sede` | branches | ✅ Completo |
| `PlanSuscripcion` | subscription_plans | ✅ Completo |
| `Usuario` | users | ✅ Funcional |
| `Rol` / `Permiso` | roles, permissions | ✅ Completo |
| `Expediente` | cases | ✅ Robusto (tiene tipo_servicio enum con 6 tipos) |
| `ParteProcesal` | case_parties | ⚠️ Solo roles de litigio |
| `PlazoFatal` | deadlines | ✅ Completo |
| `EstadoExpediente` | case_statuses | ✅ Completo |
| `EtapaProcesal` | workflow_stages | ⚠️ Solo etapas de litigio |
| `ActuacionProcesal` | case_events | ⚠️ Solo tipos judiciales |
| `NotaInterna` | case_notes | ✅ Completo |
| `HistorialEstado` | case_status_history | ✅ Completo |
| `TeoriaCaso` | case_theories | ✅ Completo |
| `Documento` | documents | ✅ Con clasificación ampliada |
| `Prueba` | evidences | ✅ Completo |
| `PruebaDocumento` | evidence_documents | ✅ Completo |
| `PerfilProfesional` | professional_profiles | ✅ Completo |
| `PerfilCliente` | client_profiles | ✅ Con junta directiva y accionistas |
| `RepresentanteLegal` | legal_representatives | ✅ Completo |
| `MiembroJuntaDirectiva` | board_members | ✅ Completo |
| `Accionista` | shareholders | ✅ Completo |
| `DocumentoCliente` | client_documents | ✅ 17 tipos |
| `LegalChunk` / `LAASession` | legal_chunks, laa_* | ✅ IA funcional |
| `LogAuditoria` | audit_logs | ✅ Completo |

## 2.3 APIs Existentes (17 routers registrados)

| Módulo API | Estado |
|-----------|--------|
| Health, Auth, Users, Tenants | ✅ |
| Cases, Deadlines, Documents | ✅ |
| Dashboard, Notifications | ✅ (notificaciones básicas) |
| AI Agent, Audit, Case Timeline | ✅ |
| Reports, Client Profiles | ✅ |
| Professional Profiles, Evidences | ✅ |
| Client Documents | ✅ |

## 2.4 Páginas Frontend

| Página | Ruta | Estado |
|--------|------|--------|
| Dashboard | `/dashboard` | ✅ Con KPIs y gráficos |
| Expedientes (Lista) | `/dashboard/cases` | ✅ Solo litigio |
| Expediente (Detalle) | `/dashboard/cases/[id]` | ✅ Con timeline y stepper |
| Nuevo Expediente | `/dashboard/cases/new` | ⚠️ Solo formulario de litigio |
| Agenda / Plazos | `/dashboard/agenda` | ✅ |
| Documentos | `/dashboard/documents` | ✅ Upload MinIO |
| Clientes | `/dashboard/clients` | ✅ CRM con junta y accionistas |
| Usuarios | `/dashboard/users` | ✅ |
| Asistente IA | `/dashboard/ai` | ✅ 4 modos |
| Base Conocimiento | `/dashboard/knowledge` | ✅ Ingesta/Stats |
| Reportes | `/dashboard/reports` | ✅ |
| Auditoría | `/dashboard/audit` | ✅ |
| Configuración | `/dashboard/settings` | ✅ |

---

# PARTE III — TIPOS DE SERVICIO LEGAL (10 TIPOS)

Los despachos jurídicos latinoamericanos ofrecen estos servicios.
El sistema DEBE soportar TODOS como ciudadanos de primera clase.

## Catálogo Definitivo

| # | Tipo | Enum | Workflow |
|---|------|------|---------|
| 1 | **Litigio** | `litigio` | Por ramo: Civil, Penal, Familia, Laboral, Mercantil, etc. |
| 2 | **Escritura Notarial** | `escritura` | Solicitud → Recopilación → Redacción → Revisión → Firma → Inscripción → Entrega |
| 3 | **Asesoría Continua** | `asesoria` | Propuesta → Contrato → Vigencia → Reportes → Renovación/Cierre |
| 4 | **Trámite Administrativo** | `tramite` | Solicitud → Preparación → Presentación → Seguimiento → Resolución → Entrega |
| 5 | **Consulta Puntual** | `consulta` | Solicitud → Agenda → Consulta → Opinión Legal → Cierre |
| 6 | **Mediación/Arbitraje** | `mediacion` | Solicitud → Designación → Sesiones → Acuerdo/Laudo → Registro |
| 7 | **Administración de Contratos** | `contrato` | Solicitud → Redacción → Revisión → Negociación → Firma → Vigencia → Vencimiento |
| 8 | **Due Diligence** | `due_diligence` | Solicitud → Alcance → Data Room → Revisión → Hallazgos → Reporte → Cierre |
| 9 | **Propiedad Intelectual** | `propiedad_intelectual` | Búsqueda → Solicitud → Publicación → Oposición → Registro → Renovación |
| 10 | **Gestión Corporativa** | `gestion_corporativa` | Solicitud → Convocatoria → Asamblea → Acta → Escrituración → Inscripción |

## Roles de Participantes por Tipo

| Tipo Servicio | Roles | Roles actuales que aplican |
|--------------|-------|---------------------------|
| Litigio | demandante, demandado, tercero_interesado, ministerio_publico, testigo, perito | ✅ Ya existen |
| Escritura | otorgante, adquiriente, compareciente, testigo_instrumental, interprete | 🔴 Faltan |
| Contratos | parte_a, parte_b, garante | 🔴 Faltan |
| Mediación | parte_a, parte_b, mediador, arbitro | 🔴 Faltan |
| Trámites | solicitante, beneficiario, gestor | 🔴 Faltan |
| Corporativo | sociedad, socio_fundador, representante | 🔴 Faltan |
| Universal | cliente, contraparte, otro | 🔴 Faltan |

---

# PARTE IV — PLAN DE SPRINTS

## Estado de Completitud por Sprint

| Sprint | Descripción | Estado |
|--------|-------------|:------:|
| Sprint 1 | Backend Multi-Servicio | ✅ Completado |
| Sprint 2 | Frontend Universal | ✅ Completado |
| Sprint 3 | Hilos de Discusión + Aprobaciones | ✅ Completado |
| Sprint 4 | Workflow Inteligente + Conflict Check | ✅ Completado |
| Sprint 5 | Time Tracking + Facturación | 🔴 Pendiente |
| Sprint 6 | API Pública + Webhooks | 🔴 Pendiente |
| Sprint 7 | NFRs (Seguridad, Caché, Mobile) | 🔴 Pendiente |
| Sprint 8 | Portal del Cliente | 🔴 Pendiente |
| Sprint 9 | IA Avanzada + Calendario | 🔴 Pendiente |

---

## MACRO-FASE A: Fundamentos Multi-Servicio

### 🔵 SPRINT 1 — Backend Multi-Servicio

**Objetivo:** Que el backend acepte y distinga los 10 tipos de servicio legal.

**Tareas:**
1. Actualizar enum `tipo_servicio` en modelo Expediente (6 → 10 tipos)
2. Corregir schema Pydantic: `tipo_servicio: str = "litigio"`, `ramo: Optional[str] = None`
3. Ampliar enum `rol_procesal` con roles notariales, contractuales, trámite, corporativos
4. Ampliar enum `tipo_plazo` en PlazoFatal: agregar `registral`, `notarial`, `contractual`, `institucional`
5. Ampliar enum `event_type` en ActuacionProcesal con tipos para otros servicios
6. Agregar campo `tipo_servicio` a EtapaProcesal (workflow_stages)
7. Migración Alembic
8. Actualizar API de cases: filtro por `tipo_servicio`, workflow por tipo
9. Seed de etapas de workflow para los 10 tipos de servicio
10. Actualizar tipos TypeScript frontend

**Criterio de aceptación:**
- ✅ Se puede crear un asunto de cualquiera de los 10 tipos vía API
- ✅ Cada tipo tiene sus etapas de workflow
- ✅ Tests pasan

---

### 🔵 SPRINT 2 — Frontend Universal

**Objetivo:** Formulario wizard multi-servicio y lista/detalle adaptativo.

**Tareas:**
1. Formulario wizard de 5 pasos:
   - Paso 1: Selector visual de tipo de servicio (tarjetas con icono)
   - Paso 2: Datos generales adaptativos (Litigio→Juzgado, Escritura→Tomo/Folio, etc.)
   - Paso 3: Participantes con roles específicos al tipo
   - Paso 4: Equipo legal + prioridad + valor
   - Paso 5: Resumen y confirmación
2. Checklists documentales por tipo de acto
3. Lista de asuntos: badge/icono tipo, filtro por tipo, terminología "Asuntos Legales"
4. Vista detalle: WorkflowProgressBar adaptativo, campos específicos por tipo
5. Actualizar sidebar: "Asuntos" en vez de solo "Expedientes"

**Criterio de aceptación:**
- ✅ Un usuario puede crear una escritura notarial, un contrato, un trámite, etc.
- ✅ Los campos cambian dinámicamente según el tipo seleccionado
- ✅ La lista muestra y filtra correctamente por tipo de servicio

---

## MACRO-FASE B: Colaboración y Workflow Inteligente

### 🟢 SPRINT 3 — Hilos de Discusión + Aprobaciones

**Objetivo:** Comunicación trazable y aprobación formal de documentos.

**Tareas:**
1. Modelo `HiloDiscusion` (case_threads): expediente_id, titulo, tipo_canal (interno/cliente), cerrado
2. Modelo `MensajeHilo` (thread_messages): hilo_id, autor_id, contenido, adjuntos, es_resolucion
3. Modelo `AprobacionDocumento` (document_approvals): documento_id, solicitante, aprobador, estado, comentarios
4. API CRUD de hilos y mensajes por caso
5. API de solicitar/aprobar/rechazar documento
6. Frontend: Panel de chat/foro en vista de detalle del caso
7. Frontend: Canal interno vs. canal del cliente (pensando en Portal Sprint 8)
8. Frontend: Panel de aprobaciones pendientes

**Criterio de aceptación:**
- ✅ Los abogados pueden discutir un caso dentro del sistema
- ✅ Se puede solicitar y gestionar aprobación de documentos

---

### 🟢 SPRINT 4 — Workflow Inteligente + Conflict Check

**Objetivo:** Automatización de flujos y detección de conflictos de interés.

**Tareas:**
1. Modelo `PlantillaWorkflow` (workflow_templates): tipo_servicio, tareas[], plazos[], docs_requeridos[]
2. Auto-creación de tareas al crear un asunto según plantilla
3. Checklists dinámicos de documentos requeridos por plantilla
4. Reglas de transición: validar prerequisitos antes de avanzar etapa
5. Motor de Conflict Check: búsqueda fuzzy (pg_trgm) contra case_parties, client_profiles, legal_representatives
6. Frontend: panel de tareas con estado por asunto
7. Frontend: alerta visual de conflicto de interés al crear caso

**Criterio de aceptación:**
- ✅ Al crear un asunto se generan automáticamente tareas y checklists
- ✅ No se puede avanzar de etapa sin cumplir requisitos
- ✅ Se detectan y alertan conflictos de interés

---

## MACRO-FASE C: Finanzas, Integraciones y Calidad

### 🟡 SPRINT 5 — Time Tracking + Facturación

**Objetivo:** Monetizar el trabajo del despacho.

**Tareas:**
1. Modelo `ContratoServicio` (service_contracts): esquema de cobro flexible
2. Modelo `RegistroTiempo` (time_entries): horas facturables con tarifa
3. Modelo `Factura` (invoices) + `LineaFactura` (invoice_lines)
4. Modelo `CuentaPorCobrar` (accounts_receivable)
5. Campos de integración en facturas: `external_id`, `sync_status`, `synced_at`, `sync_platform`
6. Separación de gastos: honorarios (IVA 15%), registrales (exentos), judiciales, administrativos
7. Endpoint de exportación en formato estándar JSON/CSV
8. Frontend: cronómetro de horas integrado
9. Frontend: panel de facturación (crear, listar, estados)
10. Frontend: dashboard financiero del despacho

**Criterio de aceptación:**
- ✅ Se puede trackear tiempo por caso
- ✅ Se puede generar y gestionar facturas
- ✅ Las facturas tienen formato exportable para contabilidad

---

### 🟡 SPRINT 6 — API Pública + Webhooks

**Objetivo:** Que LexIntellectus se integre con software contable y financiero externo.

**Tareas:**
1. Router separado `/api/v1/public/` con auth por API Key
2. Modelo `ApiKey`: tenant_id, key_hash, scopes[], activo, last_used
3. Middleware de validación de API Key + rate limiting por key
4. Endpoints públicos: invoices, payments, clients, matters/summary, time-entries
5. Modelo `WebhookSubscription`: tenant_id, url, events[], secret, activo
6. Servicio async de despacho de webhooks (Redis queue, HMAC, reintentos)
7. 14 eventos de webhook: matter.created, invoice.paid, deadline.approaching, etc.
8. Frontend: panel de administración de API Keys y webhooks en Settings

**Criterio de aceptación:**
- ✅ Un sistema externo puede obtener facturas via API Key
- ✅ Un sistema externo recibe webhooks cuando hay eventos
- ✅ Se pueden gestionar API Keys y webhooks desde la UI

**Eventos de webhook disponibles:**
```
matter.created, matter.status_changed, matter.stage_changed, matter.closed,
invoice.created, invoice.paid, invoice.overdue,
document.uploaded, document.approved,
deadline.approaching, deadline.expired,
client.created, payment.received, conflict.detected
```

---

### 🟡 SPRINT 7 — NFRs (Seguridad, Caché, Mobile)

**Objetivo:** Robustecer el sistema para producción.

**Tareas:**
1. Rate limiting con Redis (anti-brute-force en login)
2. MFA / 2FA UI (activar desde perfil, flujo TOTP)
3. Caché Redis para workflow_stages, case_statuses, permisos
4. Índices DB: GIN en JSONB, compuestos (tenant_id + tipo_servicio), pg_trgm
5. Responsividad mobile: sidebar, formularios, tablas
6. Notificaciones email reales (SendGrid o SMTP)
7. Alertas automáticas de plazos vencidos

**Criterio de aceptación:**
- ✅ Login protegido contra brute force
- ✅ MFA funcional desde la UI
- ✅ Queries críticas cacheadas
- ✅ Sistema usable en teléfono móvil
- ✅ Emails de notificación se envían

---

## MACRO-FASE D: Portal del Cliente e IA Avanzada

### 🟣 SPRINT 8 — Portal del Cliente

**Objetivo:** Dashboard diferenciado para clientes del despacho.

**Tareas:**
1. Backend: router `/api/v1/portal/` con middleware `tipo_usuario='cliente'`
2. Filtro automático: solo datos donde `cliente_principal_id = current_user.id`
3. Endpoints del portal:
   - `GET /portal/dashboard` — Mi tablero
   - `GET /portal/matters` — Mis asuntos
   - `GET /portal/documents` — Mis documentos (solo compartidos)
   - `GET /portal/invoices` — Mis facturas
   - `POST /portal/invoices/{id}/pay` — Pagar (Stripe)
   - `GET/POST /portal/threads` — Mensajes con mi abogado
   - `GET/POST /portal/approvals` — Aprobar/rechazar documentos
   - `GET/PATCH /portal/profile` — Mi perfil
4. Frontend: layout propio `/portal/*` (sin sidebar admin)
5. Diseño mobile-first
6. Pasarela Stripe Checkout para pagos con tarjeta
7. Registro de pagos por transferencia bancaria
8. Notificaciones email al cliente: doc compartido, factura emitida, mensaje nuevo

**Criterio de aceptación:**
- ✅ Un cliente puede ver sus asuntos sin ver datos de otros
- ✅ Un cliente puede pagar una factura online
- ✅ Un cliente puede chatear con su abogado
- ✅ Un cliente puede aprobar un documento

**Control de acceso:**
```
Abogado (dashboard): Ve TODOS los asuntos según permisos de rol.
                     Crea, edita, asigna. Ve métricas. Usa IA.

Cliente (portal):    Ve SOLO sus asuntos. Solo lectura + chat +
                     aprobaciones + pagos. NO ve: otros clientes,
                     métricas, estrategia, notas internas, IA.
```

---

### 🟣 SPRINT 9 — IA Avanzada + Calendario

**Objetivo:** IA como copiloto legal real.

**Tareas:**
1. Generación de borradores: escritos judiciales, escrituras, contratos
2. Análisis predictivo: probabilidad de éxito basado en jurisprudencia
3. Auto-clasificación de documentos al subir PDF
4. Resumen ejecutivo automático al agregar actuaciones
5. Sincronización bidireccional Google Calendar / Outlook
6. Exportación iCal de plazos y audiencias
7. Firma electrónica de documentos (e-signature)
8. Cifrado at-rest de campos sensibles
9. Estrategia de backup automatizado

**Criterio de aceptación:**
- ✅ La IA puede generar borradores con datos del caso
- ✅ Los plazos se sincronizan con el calendario del abogado
- ✅ Los clientes pueden firmar documentos electrónicamente

---

# PARTE V — CRONOGRAMA VISUAL

```
MACRO-FASE A: FUNDAMENTOS MULTI-SERVICIO ──────────────────────────────
  Sprint 1: Backend Multi-Servicio ──────────── [Sesión 1]     ████
  Sprint 2: Frontend Universal ──────────────── [Sesión 2-3]   ████████

MACRO-FASE B: COLABORACIÓN + WORKFLOW ─────────────────────────────────
  Sprint 3: Hilos + Aprobaciones ────────────── [Sesión 4]     ████
  Sprint 4: Workflow Inteligente + Conflict ─── [Sesión 5-6]   ████████

MACRO-FASE C: FINANZAS + INTEGRACIONES ────────────────────────────────
  Sprint 5: Time Tracking + Facturación ─────── [Sesión 7-8]   ████████
  Sprint 6: API Pública + Webhooks ──────────── [Sesión 9]     ████
  Sprint 7: NFRs (Seguridad, Cache, Mobile) ─── [Sesión 10]    ████

MACRO-FASE D: PORTAL CLIENTE + IA AVANZADA ────────────────────────────
  Sprint 8: Portal del Cliente ──────────────── [Sesión 11-12] ████████
  Sprint 9: IA Avanzada + Calendario ────────── [Sesión 13-14] ████████
```

---

# PARTE VI — DEPENDENCIAS ENTRE SPRINTS

```
Sprint 1 (Backend Multi-Servicio)
  └──→ Sprint 2 (Frontend Universal)
         ├──→ Sprint 3 (Hilos + Aprobaciones)
         └──→ Sprint 4 (Workflow + Conflict)
                ├──→ Sprint 5 (Facturación)
                │      └──→ Sprint 6 (API Pública + Webhooks)
                └──→ Sprint 7 (NFRs)
                       └──→ Sprint 8 (Portal Cliente)
                              └──→ Sprint 9 (IA Avanzada)
```

**Regla:** No iniciar un sprint sin haber completado sus dependencias.

---

# PARTE VII — REQUERIMIENTOS NO FUNCIONALES

| Categoría | Requerimiento | Estado | Sprint |
|-----------|--------------|:------:|:------:|
| **Seguridad** | JWT + RBAC granular | ✅ | — |
| **Seguridad** | Aislamiento multi-tenant por tenant_id | ✅ | — |
| **Seguridad** | Auditoría completa de acciones | ✅ | — |
| **Seguridad** | MFA / 2FA | ⚠️ Modelo existe, UI pendiente | Sprint 7 |
| **Seguridad** | Rate limiting / brute force | 🔴 | Sprint 7 |
| **Seguridad** | Cifrado at-rest | 🔴 | Sprint 9 |
| **Rendimiento** | Paginación server-side | ✅ | — |
| **Rendimiento** | Índices en campos clave | ⚠️ Parcial | Sprint 7 |
| **Rendimiento** | Caché con Redis | ⚠️ Redis activo, no usado | Sprint 7 |
| **Escalabilidad** | Docker independientes | ✅ | — |
| **Escalabilidad** | MinIO S3-compatible | ✅ | — |
| **Usabilidad** | Responsivo mobile | ⚠️ Solo desktop | Sprint 7 |
| **Usabilidad** | Tema coherente | ✅ | — |
| **Integraciones** | API Pública con API Keys | 🔴 | Sprint 6 |
| **Integraciones** | Webhooks | 🔴 | Sprint 6 |
| **Integraciones** | Contabilidad (QB/Xero) | 🔴 | Sprint 6 |
| **Integraciones** | Pasarela de pago (Stripe) | 🔴 | Sprint 8 |
| **Compliance** | Ley 787 Protección de Datos | ⚠️ | Sprint 9 |
| **Compliance** | Ley 977 Anti-Lavado (KYC) | ⚠️ | Sprint 4 |
| **Disponibilidad** | Health checks | ✅ | — |
| **Testing** | Suite automatizada | ✅ 47 tests | Continuo |
| **Backup** | Respaldo automatizado | 🔴 | Sprint 9 |

---

# PARTE VIII — INTEGRACIONES EXTERNAS SOPORTADAS

| Plataforma | Tipo | Datos | Dirección | Sprint |
|-----------|------|-------|-----------|:------:|
| QuickBooks Online | Contabilidad | Facturas, pagos, clientes | LI → QB | 6 |
| Xero | Contabilidad | Facturas, pagos, clientes | LI → Xero | 6 |
| SAP Business One | ERP | Facturas, CxC, clientes | Bidireccional | 6 |
| Alegra | Contab. LATAM | Facturas, reportes fiscales | LI → Alegra | 6 |
| Stripe | Pagos | Cobros al cliente final | Bidireccional | 8 |
| Google Calendar | Calendario | Plazos, audiencias | Bidireccional | 9 |
| Outlook/365 | Calendario | Plazos, audiencias | Bidireccional | 9 |
| SendGrid/SMTP | Email | Notificaciones | LI → Email | 7 |

---

**[Fin del Plan Estratégico Maestro v4.1]**
