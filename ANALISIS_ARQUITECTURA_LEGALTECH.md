# Análisis Integral y Arquitectura Maestra - LexIntellectus ERP Legal

Este documento representa la visión estratégica y arquitectura de datos a implementar para posicionar a LexIntellectus como un sistema de élite en la práctica y gestión legal. Se contemplan módulos proactivos y esquemas de tasación (financieros) alineados a los estándares de "Alternative Fee Arrangements" (AFAs) de firmas globales.

---

## 📌 Deuda Técnica / Pendientes
*   [x] **Fase 2:** Agregar submódulos / UI en la vista expandida del cliente para administrar CRUD de "Junta Directiva" y "Composición Accionaria". (Actual state: Read-only en la UI, funcional en API).

## 1. Gestión de Talento Legal y Enrutamiento Inteligente (HR & Smart Routing)
El valor base de una firma es el tiempo y especialidad de su gente. 
*   **Perfiles Estructurados:** Diferenciación entre Socio (Partner), Asociado Senior, Asociado Junior, Paralegal, y Soporte Administrativo.
*   **Registro de Facultades:** Número de colegiatura de la CSJ y ramas del derecho de especialidad (Penal, Tributario, Corporativo, etc.).
*   **Gestión de Carga de Trabajo (Workload Routing):** Sistema automatizado que al ingresar un nuevo servicio, sugiera asignaciones basándose en a) especialidad del abogado, b) horas facturables actuales (para evitar cuellos de botella) y c) rentabilidad.

## 2. Abstracción Continua de Servicios Legales (Workflows) 
Un cliente no solo "tiene casos". El sistema reemplazará la unidad central de "Expediente Judicial" por un esquema jerárquico superior denominado **Servicio Contratado**.
1.  **Litigios (Casos Judiciales):** Manejan contrapartes, juzgados y audiencias.
2.  **Protocolización (Notariado):** Maneja número de escrituras, folios y firmas.
3.  **Asesoría Continua (Compliance):** Maneja fechas de revisión, retenciones, etc.
4.  **Trámites Administrativos:** Exclusivos para registros de marca, propiedades, etc.

*Cada "Tipo de Servicio" gatillará automáticamente Tareas y Plazos predeterminados al momento de su creación.*

## 3. Inteligencia de Pruebas y Teoría del Caso (Evidence Engine)
Transición de un simple "repositorio de archivos" a una matriz probatoria interactiva.
*   **Nueva Entidad "Prueba":** Tipificada en Documental, Testifical, Pericial e Inspecciones.
*   **Valoración Estratégica:** Clasificación de pertinencia (Crítica, Alta, Media, Baja).
*   **Tablero de "Hechos vs. Pruebas":** Interfaz de construcción de la *Teoría del Caso*. Permite al abogado mapear los hechos narrativos de la demanda/respuesta y enlazar la prueba exacta en la plataforma que lo sustenta, conectándose a audios, videos o PDFs almacenados en MinIO.

## 4. CRM Legal Extendido y Prevención de Riesgos
Manejo profundo de la identidad con visión preventiva.
*   **Naturaleza Entidad:** Persona Natural vs. Persona Jurídica.
*   **Cadena de Representación Legal:** Mapeo de Apoderados Generales de Administración o Apoderados Generalísimos para el caso de empresas; guardando datos de la escritura pública que otorga dicho poder y su viabilidad.
*   **Motor "Conflict Check" (Detector de Conflictos de Interés):** Algoritmo preventivo. Analiza si el adversario en un nuevo caso pertenece a la matriz de una empresa cliente directa o histórica, generando una "alerta roja" para el Equipo Ético o los Socios.

## 5. Colaboración Omnicanal (Trazabilidad y Portal de Clientes)
*   **Bóveda de Discusión (Forum):** Hilos de correspondencia internos (entre abogados) y externos (con el cliente) directamente atados a la carpeta del caso, consolidando las comunicaciones que típicamente se pierden en correos y WhatsApp.
*   **Aprobación Digital:** Posibilidad de que el cliente revise documentos pre-sometimiento e inserte su Firma Electrónica (E-signature) de aprobación internamente antes de ejecutarlos.

---

## 6. Módulo de Tasación Financiera, Facturación y Cobro (Legal Billing & AFAs)
La monetización de la firma requiere máxima flexibilidad. El sistema integrará arquitecturas de facturación "Alternative Fee Arrangements" junto con las clásicas, acomodándose al tipo de [Servicio Legal] prestado:

### Esquemas de Cobro Soportados:
1.  **Tarifa por Hora (Hourly Billing):** 
    - *Ideal para:* Asesorías corporativas mixtas, estudios de caso iniciales o litigios altamente impredecibles.
    - *Mecanismo:* "Billable Hours Tracker" integrado al Dashboard. El abogado inicia el temporizador, que asocia tiempo puro frente a su ´Rate´ (Costo por hora según su Seniority).
2.  **Tarifa Fija o Plana (Flat / Fixed Fee):** 
    - *Ideal para:* Servicios predecibles como Constituciones de Sociedades, Trámites de Residencia, Divorcios de mutuo acuerdo o Escrituras de Compra-Venta.
    - *Mecanismo:* Se cobra un "paquete". El sistema mide la rentabilidad comparando la 'Tarifa Fija' cobrada vs las 'Horas Invertidas' indirectamente por el abogado.
3.  **Hitos y Etapas Procesales (Phased / Milestone Billing):**
    - *Ideal para:* Litigios complejos. 
    - *Mecanismo:* Se cobra % al interponer demanda, % a la apertura de pruebas, % a la casación. El ERP emite cuenta por cobrar cuando una tarea/fase del workflow se marca completada.
4.  **Iguala / Retenedor Mensual (Subscription / Retainer):**
    - *Ideal para:* Empresas con asesoría laboral o corporativa perpetua.
    - *Mecanismo:* El sistema factura un monto base el 1er día de mes, otorgando "X" cantidad de horas o "Y" cantidad de consultas. Se asocia a pagos recurrentes usando Stripe.
5.  **Cuota Litis o de Éxito (Contingency Fee):**
    - *Ideal para:* Casos laborales (por parte del trabajador) o civiles de indemnización.
    - *Mecanismo:* El despacho no cobra honorarios iniciales sino que factura un [Porcentaje] de la recuperación de la sentencia. Requiere Cuentas Escrow / Trust en el sistema para depositar el cheque del juzgado y hacer liquidación controlada.

### Pasarelas e Infraestructura:
El submódulo de Finanzas operará un catálogo de "Cuentas por Cobrar" y ofrecerá integración futura con procesadores como **Stripe** para emitir enlaces de pago por tarjeta al Portal del Cliente, registrando el abono en automático. 

---

**[Fin del Documento de Estrategia]**
