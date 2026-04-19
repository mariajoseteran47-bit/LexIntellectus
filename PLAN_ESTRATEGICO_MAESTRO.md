# LexIntellectus — Plan Estratégico Maestro v3.0
## Auditoría Completa, Análisis de Brechas y Roadmap de Producto

> **Fecha:** 19 de Abril, 2026  
> **Autor:** Equipo de Arquitectura LegalTech  
> **Alcance:** Revisión integral de requerimientos funcionales y no funcionales, estado actual del código, brechas identificadas, y ruta de desarrollo priorizada.

---

# PARTE I — INVENTARIO DEL SISTEMA ACTUAL

## 1.1 Infraestructura (Docker Compose)

| Componente | Tecnología | Estado |
|------------|-----------|--------|
| Base de Datos | PostgreSQL 16 + pgvector | ✅ Operativo |
| Caché / Colas | Redis 7 Alpine | ✅ Operativo |
| Almacenamiento de Objetos | MinIO (S3-compatible) | ✅ Operativo |
| Backend API | FastAPI (Python 3.11, asyncpg) | ✅ Operativo |
| Frontend | Next.js 14 + React 18 + Tailwind | ✅ Operativo |
| IA / Embeddings | Gemini 2.5 Flash + pgvector (3072 dim) | ✅ Operativo |
| Migraciones | Alembic | ⚠️ Parcialmente configurado |

## 1.2 Modelos de Datos Existentes (Backend)

| Modelo | Tabla | Campos Clave | Estado |
|--------|-------|-------------|--------|
| `Despacho` | tenants | nombre, ruc, plan_id, config_json | ✅ Completo |
| `Sede` | branches | nombre, ciudad, es_casa_matriz | ✅ Completo |
| `PlanSuscripcion` | subscription_plans | precio, moneda, limites | ✅ Completo |
| `PlanFuncionalidad` | plan_features | código, habilitado | ✅ Completo |
| `PlanLimite` | plan_limits | código, valor_limite | ✅ Completo |
| `HistorialSuscripcion` | subscription_history | fechas, método_pago, monto | ✅ Completo |
| `ConfiguracionPago` | payment_configs | stripe_id, paypal_id | ✅ Esqueleto |
| `TransaccionPago` | payment_transactions | monto, pasarela, status | ✅ Esqueleto |
| `Usuario` | users | tipo_usuario, tipo_vinculo, mfa | ✅ Funcional |
| `Rol` | roles | nombre, es_sistema | ✅ Completo |
| `Permiso` | permissions | código, módulo | ✅ Completo |
| `RolPermiso` | role_permissions | M:N rol↔permiso | ✅ Completo |
| `UsuarioRol` | user_roles | M:N usuario↔rol con sede | ✅ Completo |
| `SesionUsuario` | user_sessions | token_hash, ip, expires | ✅ Completo |
| `Expediente` | cases | ramo, juzgado, cliente, abogado, JSONB | ✅ Robusto |
| `ParteProcesal` | case_parties | tipo_persona, rol_procesal, representante | ✅ Funcional |
| `PlazoFatal` | deadlines | tipo, días_hábiles, alertas, IA | ✅ Completo |
| `EstadoExpediente` | case_statuses | código, color, es_final | ✅ Completo |
| `EtapaProcesal` | workflow_stages | ramo, orden, base_legal | ✅ Completo |
| `ActuacionProcesal` | case_events | 18 tipos, etapa, documentos | ✅ Completo |
| `NotaCaso` | case_notes | 8 tipos, privacidad, prioridad | ✅ Completo |
| `HistorialEstado` | case_status_history | antes→después, motivo | ✅ Completo |
| `TeoriaCaso` | case_theories | hechos, pretensiones, pruebas_plan | ✅ Completo |
| `Documento` | documents | storage MinIO, categoría | ⚠️ Básico |
| `LogAuditoria` | audit_logs | acción, entidad, datos antes/después | ✅ Completo |
| `LegalChunk` | legal_chunks | vector 3072, source_type | ✅ Completo |
| `LAASession` | laa_sessions | 4 modos IA, tokens | ✅ Completo |
| `LAAMessage` | laa_messages | chunks, feedback | ✅ Completo |
| `LAACaseTheory` | laa_case_theories | resumen, fortalezas, score | ✅ Completo |
| `LAAValidation` | laa_notarial_validations | resultado, errores | ✅ Completo |

## 1.3 APIs Existentes (14 archivos de rutas)

| Módulo API | Endpoints Principales | Estado |
|-----------|----------------------|--------|
| Health | `/health` | ✅ |
| Auth | login, register, refresh, me | ✅ |
| Users | CRUD paginado con filtro por rol | ✅ |
| Tenants | current tenant info | ✅ |
| Cases | CRUD + filtros + partes procesales | ✅ |
| Deadlines | CRUD con alertas | ✅ |
| Documents | Upload/Download MinIO | ✅ |
| Dashboard | stats, upcoming-deadlines | ✅ |
| Notifications | listado, marcar leído | ⚠️ Básico |
| AI Agent | chat, stats, ingest | ✅ |
| Audit | log consulta paginada | ✅ |
| Case Timeline | eventos, notas, historial | ✅ |
| Reports | overview con KPIs reales | ✅ |

## 1.4 Páginas Frontend (10 secciones)

| Página | Ruta | Estado |
|--------|------|--------|
| Dashboard Principal | `/dashboard` | ✅ Con KPIs y gráficos |
| Expedientes (Lista) | `/dashboard/cases` | ✅ |
| Expediente (Detalle) | `/dashboard/cases/[id]` | ✅ Con timeline |
| Nuevo Expediente | `/dashboard/cases/new` | ✅ |
| Agenda / Plazos | `/dashboard/agenda` | ✅ |
| Documentos | `/dashboard/documents` | ✅ Upload MinIO |
| Clientes | `/dashboard/clients` | ✅ Recién reparado |
| Usuarios | `/dashboard/users` | ✅ |
| Asistente IA | `/dashboard/ai` | ✅ 4 modos |
| Base Conocimiento | `/dashboard/knowledge` | ✅ Ingesta/Stats |
| Reportes | `/dashboard/reports` | ✅ |
| Auditoría | `/dashboard/audit` | ✅ |
| Configuración | `/dashboard/settings` | ✅ |

## 1.5 Servicios Backend (6 módulos)

| Servicio | Funcionalidad | Estado |
|---------|--------------|--------|
| `audit.py` | Registro de auditoría | ✅ |
| `email.py` | Envío de correos (placeholder) | ⚠️ Sin integración real |
| `ingestion.py` | Chunking + embedding de docs legales | ✅ |
| `prompts.py` | Librería de 4 modos IA | ✅ |
| `rag_engine.py` | Motor RAG completo con Gemini | ✅ |
| `storage.py` | Integración MinIO S3 | ✅ |

---

# PARTE II — ANÁLISIS DE BRECHAS CRÍTICAS

## 🔴 Brecha 1: Identidad Profesional del Equipo Legal (CRÍTICA)

**Problema:** El modelo `Usuario` tiene un campo `tipo_usuario` con valores como "abogado", "secretaria", etc., pero **NO tiene campos para**:
- Nivel jerárquico (Socio/Partner, Asociado Senior, Asociado Junior, Paralegal)
- Especialidad jurídica (Penal, Civil, Corporativo, Tributario, etc.)
- Número de colegiatura / carnet CSJ
- Tarifa por hora (billable rate)
- Carga de trabajo actual

**Impacto:** No se puede asignar inteligentemente, no se puede facturar por hora, y no se puede filtrar por competencia.

**Solución:** Crear tabla `professional_profiles` vinculada 1:1 a `users` donde `tipo_usuario IN (abogado, notario, secretaria, gestor)`.

## 🔴 Brecha 2: Identidad de Clientes (Natural vs Jurídica) (CRÍTICA)

**Problema:** El cliente es simplemente un `Usuario` con `tipo_usuario='cliente'`. **NO tiene campos para**:
- Tipo de persona (natural / jurídica)
- Razón social / nombre comercial (jurídicas)
- RUC o cédula de identidad
- Apoderado Generalísimo / Apoderado General de Administración
- Datos de la escritura pública del poder (número, fecha, notario, libro)
- Fecha de vencimiento del poder
- Estructura corporativa (empresa matriz / subsidiarias)

**Impacto:** Imposible distinguir si el cliente es Don Juan Pérez o la Sociedad Anónima "Grupo Pérez S.A." representada por su apoderado.

**Solución:** Crear tabla `client_profiles` vinculada 1:1 a `users` donde `tipo_usuario='cliente'`, con subtabla `legal_representatives` para apoderados.

## 🔴 Brecha 3: Tipos de Servicio Legal (CRÍTICA)

**Problema:** El sistema opera exclusivamente con `Expediente` (caso judicial). No contempla:
- Escrituras notariales (protocolización)
- Asesorías legales continuas (retainer/iguala)
- Trámites administrativos (registros, marcas, migratorios)
- Consultas puntuales

**Impacto:** El despacho solo puede registrar litigios. Toda la práctica notarial, asesoría corporativa y trámites queda fuera del sistema.

**Solución:** Añadir campo `tipo_servicio` al modelo `Expediente` y adaptar la interfaz para que los campos contextuales cambien según el tipo.

## 🟡 Brecha 4: Gestión Probatoria Estructurada (IMPORTANTE)

**Problema:** Existe `TeoriaCaso` con `pruebas_plan` como JSONB, pero **NO hay una entidad formal de Prueba** con:
- Clasificación probatoria (documental, testifical, pericial, inspección)
- Valoración/peso estratégico (crítica, alta, media, baja)
- Estado procesal (propuesta, admitida, evacuada, rechazada)
- Vinculación directa a documentos multimedia en MinIO
- Cadena de custodia interna

**Impacto:** El abogado litigante no puede construir su estrategia probatoria de forma estructurada.

**Solución:** Crear tabla `evidences` con relación M:N a `documents` y vinculación a `case_theories`.

## 🟡 Brecha 5: Colaboración y Comunicación (IMPORTANTE)

**Problema:** Cero funcionalidad de mensajería o foro. Los abogados y clientes no pueden:
- Discutir internamente un caso dentro del sistema
- Compartir archivos dentro de un hilo de conversación
- Dejar aprobaciones o comentarios documentados

**Impacto:** Las comunicaciones se pierden en WhatsApp y correo, sin trazabilidad.

**Solución:** Crear modelo `CaseThread` / `ThreadMessage` asociado a cada servicio/expediente, con canales internos vs. canal-cliente.

## 🟡 Brecha 6: Motor de Workflow Legal Especializado (IMPORTANTE)

**Problema:** `EtapaProcesal` / `workflow_stages` existe y es robusto, pero:
- No hay lógica de auto-creación de tareas al avanzar de etapa
- No hay plantillas de workflow por tipo de servicio (ej: al crear "Constitución de S.A." se deben crear automáticamente 5 tareas estándar)
- No hay reglas de transición (ej: no se puede pasar a "Sentencia" sin haber pasado por "Pruebas")

**Impacto:** Todo el flujo procesal es manual; el sistema no guía al abogado.

**Solución:** Crear `workflow_templates` con `template_tasks` por tipo de servicio, y motor de reglas de transición.

## 🟡 Brecha 7: Conflict Check (Detección de Conflictos de Interés) (IMPORTANTE)

**Problema:** No existe ningún algoritmo que al registrar un nuevo caso o cliente verifique si existe conflicto con clientes existentes o históricos.

**Impacto:** Riesgo ético-legal grave. Si la firma demanda a alguien que fue su propio cliente, puede resultar en sanciones del Colegio de Abogados.

**Solución:** Motor de búsqueda fuzzy que compare nombre/RUC/cédula del nuevo adversario contra toda la base de clientes/partes procesales.

## 🟢 Brecha 8: Facturación y Time Tracking (FUTURA — Diseñar Ahora)

**Problema:** Modelos de `ConfiguracionPago`, `TransaccionPago` e `HistorialSuscripcion` existen pero son para la **suscripción del SaaS** (lo que el despacho paga por usar LexIntellectus), NO para la **facturación que el despacho cobra a sus clientes**.

**Falta completamente:**
- Temporizador de horas facturables (billable hours tracker)
- Modelo de Factura/Invoice al cliente
- Modelo de Cuenta por Cobrar (CxC)
- Esquemas de cobro flexibles (por hora, fijo, hitos, iguala, contingencia)
- Pasarela de cobro al cliente final (Stripe Connect, PayPal)
- Trust Accounts / Cuentas Escrow para fondos en custodia

**Solución:** Suite financiera completa (Módulo Billing, descrito más adelante).

## 🟢 Brecha 9: Notificaciones Inteligentes (FUTURA)

**Problema:** El endpoint de notificaciones existe pero no hay:
- Integración con email real (SendGrid, SES)
- Push notifications (Web Push o Firebase)
- Alertas automatizadas por vencimiento de plazos
- Recordatorios de audiencias
- Digest semanal de actividad

## 🟢 Brecha 10: Integración de Calendario (FUTURA)

**Problema:** La agenda muestra plazos pero no se sincroniza con:
- Google Calendar
- Microsoft Outlook/365
- Formato iCal estándar

---

# PARTE III — PLAN ESTRATÉGICO DE DESARROLLO

## Principios de Diseño

1. **Legal-First**: Cada funcionalidad debe resolver un problema real de la práctica jurídica nicaragüense.
2. **Data Integrity**: Los datos legales son evidencia; tolerancia cero a pérdida o corrupción.
3. **Multi-Tenant Isolation**: Todo dato está aislado por `tenant_id`.
4. **Progressive Disclosure**: La interfaz no abruma; muestra lo relevante según el tipo de servicio.
5. **AI-Augmented, Human-Decided**: La IA sugiere, el abogado decide.

---

## FASE 1 — Identidad y Tipología (Sprint Inmediato)
> **Objetivo:** Que el sistema conozca quién es quién y qué servicio brinda.

### 1A. Perfiles Profesionales del Equipo Legal
**Nuevo modelo: `PerfilProfesional` (professional_profiles)**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| user_id | FK → users | Relación 1:1 |
| nivel_jerarquico | Enum | socio, asociado_senior, asociado_junior, paralegal, pasante |
| especialidades | JSONB[] | ["penal", "corporativo", "tributario"] |
| numero_colegiatura | String | Carnet CSJ |
| fecha_colegiatura | Date | Fecha de inscripción |
| universidad | String | Alma mater |
| anios_experiencia | Integer | Años de práctica |
| tarifa_hora_usd | Decimal | Rate por hora facturable |
| tarifa_hora_nio | Decimal | Rate en córdobas |
| idiomas | JSONB[] | ["es", "en"] |
| bio_profesional | Text | Perfil público |
| activo_litigio | Boolean | ¿Participa activamente en juicios? |

### 1B. Perfiles Extendidos de Clientes (CRM Legal)
**Nuevo modelo: `PerfilCliente` (client_profiles)**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| user_id | FK → users | Relación 1:1 |
| tipo_persona | Enum | natural, juridica |
| cedula_identidad | String | Para personas naturales |
| ruc | String | Registro Único de Contribuyente |
| razon_social | String | Solo jurídicas |
| nombre_comercial | String | Nombre de fantasía |
| fecha_constitucion | Date | Solo jurídicas |
| actividad_economica | String | Giro del negocio |
| direccion_domicilio | Text | Dirección legal |
| notas_internas | Text | Observaciones de la firma |
| fecha_primera_consulta | Date | Primera vez que acudió |
| referido_por | String | Cómo llegó |
| calificacion_riesgo | Enum | bajo, medio, alto |

**Nuevo modelo: `RepresentanteLegal` (legal_representatives)**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| client_profile_id | FK → client_profiles | Cliente jurídico |
| nombre_completo | String | Nombre del apoderado |
| tipo_poder | Enum | generalisimo, general_administracion, especial |
| numero_escritura | String | N° de escritura del poder |
| fecha_otorgamiento | Date | Cuándo se otorgó |
| fecha_vencimiento | Date | Cuándo caduca (si aplica) |
| notario_autorizante | String | Notario que autorizó |
| libro_protocolo | String | Referencia de protocolo |
| alcance_facultades | Text | Descripción de las facultades |
| vigente | Boolean | ¿Está vigente? |
| documento_id | FK → documents | Escaneo del poder en MinIO |

### 1C. Ampliación de Tipos de Servicio
**Modificación al modelo `Expediente`:**

Agregar campo `tipo_servicio`:
```
tipo_servicio ENUM:
  - litigio          → Caso judicial (comportamiento actual)
  - escritura        → Protocolo notarial
  - asesoria         → Asesoría/retainer continuo
  - tramite          → Trámite administrativo/registral
  - consulta         → Consulta puntual / opinión legal
  - mediacion        → Mediación / arbitraje
```

La interfaz frontend adaptará los campos visibles según el `tipo_servicio`:
- **Litigio:** Juzgado, juez, contrapartes, etapa procesal
- **Escritura:** Número de escritura, tomo, folio, tipo de acto, partes
- **Asesoría:** Período, tipo de retainer, alcance, renovación
- **Trámite:** Institución, tipo de trámite, referencia, estado

---

## FASE 2 — Motor Probatorio y Multimedia (Sprint 2)
> **Objetivo:** Que el sistema sea la pizarra de guerra del litigante.

### 2A. Gestión Estructurada de Pruebas
**Nuevo modelo: `Prueba` (evidences)**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| expediente_id | FK → cases | Caso al que pertenece |
| tipo_prueba | Enum | documental, testifical, pericial, inspeccion, confesional, presuncional |
| titulo | String | Nombre descriptivo |
| descripcion | Text | Detalle de la prueba |
| hecho_que_prueba | Text | Qué hecho sustenta |
| valoracion | Enum | critica, alta, media, baja |
| estado_procesal | Enum | propuesta, admitida, evacuada, rechazada, desistida |
| fecha_proposicion | Date | Cuándo se ofreció |
| fecha_admision | Date | Cuándo se admitió |
| fecha_evacuacion | Date | Cuándo se practicó |
| cadena_custodia | JSONB | Registro de quién aportó, cuándo, cómo |
| observaciones | Text | Notas estratégicas |

**Nuevo modelo: `PruebaDocumento` (evidence_documents)**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| prueba_id | FK → evidences | La prueba |
| documento_id | FK → documents | El archivo en MinIO |
| tipo_medio | Enum | pdf, foto, video, audio, otro |
| es_original | Boolean | ¿Es el original o copia? |
| descripcion | String | "Foto del contrato firmado" |

### 2B. Ampliación del Modelo de Documentos
Agregar a `documents`:
- `tipo_documento`: Enum (escrito, notificacion, evidencia, poder, contrato, sentencia, recurso, dictamen, acta)
- `es_confidencial`: Boolean
- `version`: Integer (versionamiento)
- `tags`: JSONB[] (etiquetas libres)
- Soporte MIME ampliado: audio/mp3, audio/wav, video/mp4

---

## FASE 3 — Colaboración Legal (Sprint 3)
> **Objetivo:** Que las comunicaciones queden documentadas y trazables.

### 3A. Hilos de Discusión por Caso
**Nuevo modelo: `HiloDiscusion` (case_threads)**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| expediente_id | FK → cases | Servicio/caso vinculado |
| titulo | String | Asunto del hilo |
| tipo_canal | Enum | interno, cliente |
| creado_por_id | FK → users | Quién inició |
| esta_cerrado | Boolean | ¿Archivado? |
| ultimo_mensaje_at | DateTime | Para ordenar por actividad |

**Nuevo modelo: `MensajeHilo` (thread_messages)**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| hilo_id | FK → case_threads | Hilo padre |
| autor_id | FK → users | Quién escribió |
| contenido | Text | Cuerpo del mensaje (markdown) |
| adjuntos | JSONB | document_ids adjuntados |
| es_resolucion | Boolean | Marca como decisión/acuerdo |
| editado | Boolean | Si fue editado |

### 3B. Aprobaciones de Documentos
**Nuevo modelo: `AprobacionDocumento` (document_approvals)**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| documento_id | FK → documents | Doc a aprobar |
| solicitado_por_id | FK → users | Abogado que pide aprobación |
| aprobado_por_id | FK → users | Cliente/socio que aprueba |
| estado | Enum | pendiente, aprobado, rechazado, con_observaciones |
| comentarios | Text | Observaciones |
| firma_hash | String | Hash de firma electrónica |
| ip_aprobacion | String | IP desde donde aprobó |

---

## FASE 4 — Motor de Workflow Legal Especializado (Sprint 4)
> **Objetivo:** Que el sistema guíe proactivamente al abogado.

### 4A. Plantillas de Flujo por Tipo de Servicio
**Nuevo modelo: `PlantillaWorkflow` (workflow_templates)**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| tipo_servicio | Enum | El tipo de servicio legal |
| ramo | Enum | Materia (solo para litigios) |
| tipo_proceso | String | Subtipo |
| nombre | String | "Constitución de S.A." |
| descripcion | Text | Descripción del flujo |
| tareas | JSONB[] | Lista ordenada de tareas auto-generadas |
| plazos | JSONB[] | Plazos legales asociados |
| documentos_requeridos | JSONB[] | Checklist documental |
| activo | Boolean | ¿Plantilla vigente? |

Ejemplo de `tareas` para "Constitución de Sociedad Anónima":
```json
[
  {"orden": 1, "titulo": "Solicitar identificaciones de socios", "dias_plazo": 3},
  {"orden": 2, "titulo": "Redactar Pacto Social / Escritura", "dias_plazo": 5},
  {"orden": 3, "titulo": "Revisión y firma de socios", "dias_plazo": 3},
  {"orden": 4, "titulo": "Protocolización ante Notario", "dias_plazo": 2},
  {"orden": 5, "titulo": "Inscripción en Registro Público Mercantil", "dias_plazo": 15},
  {"orden": 6, "titulo": "Obtención de RUC ante DGI", "dias_plazo": 10},
  {"orden": 7, "titulo": "Entrega de documentación al cliente", "dias_plazo": 2}
]
```

### 4B. Reglas de Transición Procesal

El motor de workflow debe validar transiciones de etapa según reglas:
- **Validaciones de prerequisito:** No pasar a "Pruebas" sin tener al menos una prueba registrada.
- **Validaciones temporales:** No cerrar etapa si hay plazos pendientes.
- **Alertas de omisión:** "Advertencia: No se ha subido la demanda como documento."

### 4C. Motor de Conflict Check (Conflictos de Interés)

Al registrar un nuevo caso o parte procesal:
1. Buscar nombre/cédula/RUC en `case_parties` históricas
2. Buscar en `client_profiles` activos e históricos
3. Buscar en `legal_representatives`
4. Algoritmo de similitud fuzzy (Levenshtein + trigrams de PostgreSQL)
5. Si hay coincidencia > 80%: **Alerta Roja** al administrador del despacho

---

## FASE 5 — Suite Financiera y Facturación (Sprint 5-6)
> **Objetivo:** Que el sistema monetice la firma con flexibilidad total.

### 5A. Esquemas de Tasación Soportados

| # | Esquema | Campo clave | Mecanismo de facturación |
|---|---------|------------|------------------------|
| 1 | **Tarifa por Hora** | tarifa_hora del profesional | Cronómetro → registros_tiempo → factura |
| 2 | **Tarifa Fija/Plana** | monto_pactado en contrato_servicio | Evento de inicio → factura única |
| 3 | **Por Hitos/Etapas** | hitos[] en contrato_servicio | Al completar etapa procesal → factura parcial |
| 4 | **Iguala/Retenedor** | monto_mensual + horas_incluidas | Recurrente (1º de mes) → factura automática |
| 5 | **Cuota Litis / Éxito** | porcentaje_exito en contrato_servicio | Al cobrar sentencia → liquidación |
| 6 | **Tarifa Mixta** | tarifa_base + bono_exito | Reducida por hora + bonus si se gana |
| 7 | **Tarifa con Tope** | tarifa_hora + tope_maximo | Por hora hasta el cap, luego gratis |
| 8 | **Descuento por Volumen** | descuento_pct si volumen > umbral | Automático al consolidar facturación mensual |

### 5B. Modelos de Datos Financieros

**`ContratoServicio` (service_contracts):** Vincula cliente + servicio + esquema de cobro.

**`RegistroTiempo` (time_entries):** Billable Hours Tracker.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| user_id | FK → users | Abogado que trabajó |
| expediente_id | FK → cases | Caso trabajado |
| descripcion | String | "Revisión de contestación de demanda" |
| fecha | Date | Día del trabajo |
| duracion_minutos | Integer | Tiempo invertido |
| es_facturable | Boolean | ¿Se cobra al cliente? |
| tarifa_aplicada | Decimal | Rate usado |
| monto_calculado | Decimal | duracion × tarifa |
| factura_id | FK → invoices | Si ya fue facturado |

**`Factura` (invoices):** Documento de cobro al cliente.

**`CuentaPorCobrar` (accounts_receivable):** Balance pendiente.

**`CuentaCustodia` (trust_accounts):** Fondos del cliente en poder del despacho (para fianzas, depósitos judiciales, etc.)

### 5C. Pasarelas de Pago
- **Stripe Connect:** Para cobros con tarjeta directamente desde el Portal del Cliente
- **PayPal:** Alternativa de pago
- **Transferencia Bancaria:** Registro manual con conciliación

---

## FASE 6 — IA Avanzada y Analítica Predictiva (Sprint 7+)
> **Objetivo:** Que la IA deje de ser solo un chatbot y se convierta en un copiloto legal.

### 6A. Funcionalidades IA Avanzadas
- **Generación Automática de Borradores:** Escritos judiciales con datos del caso pre-populados
- **Análisis Predictivo:** Basado en sentencias históricas, estimar probabilidad de éxito
- **Resumen Ejecutivo Automático:** Al agregar actuaciones, generar resumen del estado del caso
- **Alertas Inteligentes:** "Este juez típicamente requiere X prueba para este tipo de caso"
- **Auto-clasificación de Documentos:** Al subir un PDF, la IA identifica si es sentencia, demanda, contrato, etc.

### 6B. Integración de Calendario
- Sincronización bidireccional con Google Calendar / Outlook
- Exportación iCal de plazos y audiencias

### 6C. Portal del Cliente (Client Portal)
- Dashboard simplificado solo para clientes
- Ver sus casos y estado
- Ver/descargar documentos aprobados
- Foro de comunicación con su abogado
- Pagar facturas online (Stripe)
- Firmar documentos (E-Signature)

---

# PARTE IV — CRONOGRAMA Y PRIORIZACIÓN

```
FASE 1: Identidad y Tipología ──────────── [Semana 1-2]  ████████
  ├── 1A. Perfiles Profesionales
  ├── 1B. CRM Clientes (Natural/Jurídica)
  └── 1C. Tipos de Servicio Legal

FASE 2: Motor Probatorio ──────────────── [Semana 3-4]  ████████
  ├── 2A. Entidad Prueba + Multimedia
  └── 2B. Ampliación de Documentos

FASE 3: Colaboración ──────────────────── [Semana 5-6]  ████████
  ├── 3A. Hilos de Discusión
  └── 3B. Aprobaciones de Documentos

FASE 4: Workflow Legal ────────────────── [Semana 7-8]  ████████
  ├── 4A. Plantillas de Flujo
  ├── 4B. Reglas de Transición
  └── 4C. Conflict Check Engine

FASE 5: Suite Financiera ─────────────── [Semana 9-12] ████████████████
  ├── 5A. Time Tracking / Billable Hours
  ├── 5B. Facturación + CxC
  └── 5C. Pasarelas de Pago

FASE 6: IA Avanzada + Portal Cliente ─── [Semana 13+]  ████████████████
  ├── 6A. IA Predictiva y Generativa
  ├── 6B. Calendario Sync
  └── 6C. Portal del Cliente
```

---

# PARTE V — REQUERIMIENTOS NO FUNCIONALES

| Categoría | Requerimiento | Estado |
|-----------|--------------|--------|
| **Seguridad** | JWT + RBAC granular | ✅ Implementado |
| **Seguridad** | Aislamiento multi-tenant por tenant_id | ✅ Implementado |
| **Seguridad** | Auditoría completa de acciones | ✅ Implementado |
| **Seguridad** | MFA / Autenticación de 2 factores | ⚠️ Modelo existe, UI pendiente |
| **Seguridad** | Cifrado de datos sensibles at-rest | 🔴 Pendiente |
| **Seguridad** | Rate limiting / brute force protection | 🔴 Pendiente (Redis disponible) |
| **Rendimiento** | Paginación server-side | ✅ Implementado |
| **Rendimiento** | Índices en campos clave | ⚠️ Parcial |
| **Rendimiento** | Caché con Redis | ⚠️ Redis activo, no utilizado en queries |
| **Escalabilidad** | Contenedores Docker independientes | ✅ Implementado |
| **Escalabilidad** | Almacenamiento S3-compatible (MinIO) | ✅ Implementado |
| **Usabilidad** | Diseño responsivo (mobile-first) | ⚠️ Desktop OK, Mobile parcial |
| **Usabilidad** | Tema "Minimalismo Judicial" coherente | ✅ Implementado |
| **Compliance** | Ley 787 Protección de Datos (Nicaragua) | ⚠️ Arquitectura permite, falta política |
| **Compliance** | Ley 977 Anti-Lavado (KYC) | ⚠️ Modo Cartulario IA, falta workflow |
| **Disponibilidad** | Health checks en todos los servicios | ✅ Implementado |
| **Testing** | Suite de 47 tests automatizados | ✅ 100% passing |
| **Backup** | Estrategia de respaldo de datos | 🔴 No configurado |

---

**[Fin del Plan Estratégico Maestro v3.0]**
