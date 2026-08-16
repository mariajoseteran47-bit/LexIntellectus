"""
LexIntellectus ERP - Corpus Jurídico de Nicaragua: Siembra Masiva
Populates pgvector with core articles of all major Nicaraguan codes.
Uses raw SQL to bypass SQLAlchemy Enum type issues in dev environments.
"""

import asyncio
import uuid
import hashlib
from typing import List
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

SQLALCHEMY_DATABASE_URL = "postgresql+asyncpg://lexintellectus:lexintellectus_dev_2026@postgres:5432/lexintellectus"

def get_deterministic_embedding(content: str) -> List[float]:
    """Generates a deterministic 3072-dimensional vector embedding based on content hash."""
    val = int(hashlib.md5(content.encode("utf-8")).hexdigest(), 16) % 100 / 1000.0
    return [val] * 3072

def embedding_to_pgvector_literal(embedding: List[float]) -> str:
    """Converts a python float list to a pgvector literal string '[0.01,0.01,...]'"""
    return "[" + ",".join(str(v) for v in embedding) + "]"

async def seed_codes():
    engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    print("🚀 Iniciando la siembra masiva del Corpus Jurídico de Nicaragua...")
    print("   Leyes Civiles, Familia, Penal, Registros Públicos, Mercantil y Notarial\n")

    # ─────────────────────────────────────────────────────────────────────
    # CORPUS LEGAL DE NICARAGUA
    # ─────────────────────────────────────────────────────────────────────
    laws_corpus = {
        # ═══════════════════════════════════════════════════════════════
        # 1. CÓDIGO CIVIL DE NICARAGUA
        # ═══════════════════════════════════════════════════════════════
        "Código Civil de la República de Nicaragua": {
            "tipo": "ley",
            "articles": [
                # Libro I - Personas
                "Art. 1.- La ley es obligatoria para todos los habitantes de la República, sean nacionales o extranjeros, domiciliados o transeúntes.",
                "Art. 2.- La promulgación de la ley se hará por medio de publicación en La Gaceta, Diario Oficial.",
                "Art. 7.- Las leyes no tienen efecto retroactivo. Pero las leyes concernientes a la sustanciación y ritualidad de los juicios prevalecen sobre las anteriores desde el momento de su vigencia.",
                "Art. 20.- La personalidad civil comienza con el nacimiento y se extingue con la muerte.",
                "Art. 26.- El domicilio civil es el lugar donde una persona tiene su residencia habitual con ánimo de permanecer.",
                # Libro II - Bienes y Propiedad
                "Art. 597.- Son bienes las cosas que pueden ser objeto de apropiación.",
                "Art. 611.- La propiedad es el derecho de gozar y disponer de una cosa, sin más limitaciones que las establecidas en las leyes.",
                "Art. 615.- El propietario de un terreno es dueño de su superficie y de lo que está debajo de ella, y puede hacer en él las obras, plantaciones y excavaciones que le convengan.",
                "Art. 888.- El usufructo da derecho a disfrutar los bienes ajenos con la obligación de conservar su forma y sustancia.",
                "Art. 1476.- Hipoteca es un derecho real que grava los bienes inmuebles para garantizar el cumplimiento de una obligación y su preferencia en el pago.",
                # Libro III - Obligaciones y Contratos
                "Art. 1831.- Las obligaciones nacen de la ley, de los contratos y cuasi-contratos, y de los actos y omisiones ilícitos o en que intervenga cualquier género de culpa o negligencia.",
                "Art. 1836.- Las obligaciones que nacen de los contratos tienen fuerza de ley entre las partes contratantes, y deben cumplirse al tenor de los mismos.",
                "Art. 1863.- El consentimiento es la base del contrato y consiste en el acuerdo de voluntades sobre el objeto y la causa que han de constituir el contrato.",
                "Art. 1875.- Es nulo el consentimiento prestado por error, arrancado por violencia o sorprendido por dolo.",
                "Art. 2010.- Si el obligado a hacer alguna cosa no la hiciere, se mandará ejecutar a su costa. La mora del deudor da derecho al acreedor a solicitar la resolución del contrato o su cumplimiento con indemnización de daños y perjuicios.",
                "Art. 2018.- El deudor está obligado a cumplir su obligación en el lugar, tiempo y forma convenidos.",
                "Art. 2481.- Por el contrato de compra y venta uno de los contratantes se obliga a entregar una cosa determinada y el otro a pagar por ella un precio cierto, en dinero o signo que lo represente.",
                "Art. 2810.- El arrendamiento es un contrato por el cual una de las partes se obliga a conceder el uso o goce de una cosa, y la otra a pagar por este uso o goce un precio determinado.",
                "Art. 3293.- El mandato es un contrato por el cual una persona encomienda la gestión de uno o más negocios a otra, que se hace cargo de ellos por cuenta y riesgo de la primera.",
                "Art. 3417.- La fianza es una obligación accesoria en virtud de la cual una o más personas responden de una obligación ajena, comprometiéndose para con el acreedor a cumplirla en todo o en parte.",
                # Libro IV - Sucesiones
                "Art. 933.- La sucesión se defiere por la voluntad del hombre manifestada en testamento, y a falta de testamento, por disposición de la ley.",
                "Art. 945.- Es capaz de suceder toda persona que exista al tiempo de abrirse la sucesión.",
                "Art. 1000.- El testamento es un acto más o menos solemne en que una persona dispone del todo o de una parte de sus bienes para después de su muerte.",
                "Art. 1188.- Son herederos forzosos los hijos, los padres y el cónyuge o compañero en unión de hecho estable.",
                # Libro V - Prescripción
                "Art. 874.- La prescripción es un medio de adquirir el dominio de las cosas ajenas o de extinguir las acciones y derechos ajenos, por haberse poseído las cosas durante cierto lapso de tiempo.",
                "Art. 879.- La prescripción ordinaria de dominio se adquiere por la posesión continua, pública, pacífica e ininterrumpida de un bien raíz durante diez años.",
                "Art. 905.- Prescribe en tres años la acción para exigir la responsabilidad civil por injuria o calumnia y por las obligaciones derivadas de la culpa o negligencia.",
            ]
        },
        # ═══════════════════════════════════════════════════════════════
        # 2. CÓDIGO DE FAMILIA DE NICARAGUA (Ley 870)
        # ═══════════════════════════════════════════════════════════════
        "Código de Familia de Nicaragua (Ley 870)": {
            "tipo": "ley",
            "articles": [
                "Art. 1.- El presente Código de Familia regula las relaciones jurídicas de carácter familiar, estableciendo los derechos y deberes de los miembros de la familia.",
                "Art. 53.- La unión de hecho estable es la relación de convivencia de un hombre y una mujer de forma libre, con estabilidad y capacidad de contraer matrimonio.",
                "Art. 67.- El matrimonio es la unión voluntaria de un hombre y una mujer constituida por el libre y mutuo consentimiento de los contrayentes, formalizada de conformidad con la ley.",
                "Art. 82.- Son deberes y derechos de los cónyuges: contribuir al sostenimiento del hogar, respetarse mutuamente y guardarse lealtad.",
                "Art. 123.- La disolución del vínculo matrimonial se produce por sentencia firme que declare el divorcio o por la muerte de uno de los cónyuges.",
                "Art. 138.- La pensión alimenticia es una obligación de orden público e interés social. Comprende alimentos, habitación, vestido, salud, educación, cultura, recreación y transporte.",
                "Art. 143.- Es deber de los padres alimentar a sus hijos e hijas menores de edad. Esta obligación se extiende hasta los 21 años si cursan estudios universitarios con aprovechamiento satisfactorio.",
                "Art. 158.- La pensión alimenticia puede ser modificada o extinguida por sentencia judicial cuando varíen las circunstancias que motivaron su fijación.",
                "Art. 185.- La filiación es el vínculo jurídico existente entre el padre o la madre y su hijo o hija.",
                "Art. 200.- Toda persona tiene derecho a investigar quién es su padre o madre, de conformidad con lo establecido en este Código.",
                "Art. 245.- El patrimonio familiar es la institución jurídica social por medio de la cual se destina uno o más bienes de manera inembargable e inalienable al sostenimiento de la familia.",
                "Art. 268.- La adopción plena confiere al adoptado la condición de hijo del adoptante, con los mismos derechos y obligaciones.",
                "Art. 312.- La autoridad parental comprende el conjunto de derechos y deberes que los padres y madres tienen respecto de sus hijos e hijas menores de edad no emancipados.",
                "Art. 325.- Los padres administran los bienes de sus hijos menores de edad. Esta administración está sujeta a las limitaciones que establece la ley.",
                "Art. 420.- La tutela es una institución de protección de menores de edad o personas declaradas incapaces judicialmente.",
            ]
        },
        # ═══════════════════════════════════════════════════════════════
        # 3. CÓDIGO PENAL DE NICARAGUA (Ley 641)
        # ═══════════════════════════════════════════════════════════════
        "Código Penal de la República de Nicaragua (Ley 641)": {
            "tipo": "ley",
            "articles": [
                "Art. 1.- (Principio de Legalidad) Ninguna persona podrá ser condenada por una acción u omisión que no esté prevista como delito o falta por ley penal anterior a su realización.",
                "Art. 2.- (Principio de Irretroactividad) Las leyes penales tienen efecto retroactivo en cuanto favorezcan al reo, aunque al publicarse la ley favorable haya recaído sentencia firme.",
                "Art. 9.- Son delitos o faltas las acciones u omisiones dolosas o imprudentes que estén penadas por la ley.",
                "Art. 23.- Son causas que eximen de responsabilidad penal: la legítima defensa, el estado de necesidad, el cumplimiento de un deber legal, el miedo insuperable.",
                "Art. 34.- (Legítima Defensa) Obra en legítima defensa el que ejecuta un acto en defensa de su persona o derechos, de la persona o derechos de otro, siempre que concurran agresión ilegítima y necesidad racional del medio empleado.",
                "Art. 125.- (Homicidio) Quien prive de la vida a otra persona será sancionado con pena de diez a quince años de prisión.",
                "Art. 138.- (Lesiones Graves) Quien causare a otro daño grave en el cuerpo o en la salud será sancionado con prisión de tres a ocho años.",
                "Art. 145.- (Estafa) Comete delito de estafa quien, con ánimo de lucro y utilizando engaño bastante, induzca a otro a realizar un acto de disposición patrimonial en su propio perjuicio.",
                "Art. 155.- (Robo) Quien se apodere de cosa mueble ajena con fuerza en las cosas o violencia o intimidación en las personas, será sancionado con prisión de tres a seis años.",
                "Art. 218.- (Abuso de Confianza) Quien en perjuicio de otro disponga para sí o para un tercero de cualquier cosa mueble ajena que tenga legítimamente en su poder.",
                "Art. 235.- (Daños) Quien destruya, inutilice o dañe una cosa mueble o inmueble ajena.",
                "Art. 275.- (Falsedad Documental) Quien haga en todo o en parte un documento falso o altere uno verdadero, de modo que pueda resultar perjuicio.",
                "Art. 335.- (Desobediencia) Quien desobedezca una orden, resolución o mandato judicial emanados de autoridad competente.",
            ]
        },
        # ═══════════════════════════════════════════════════════════════
        # 4. LEY GENERAL DE REGISTROS PÚBLICOS (Ley 698)
        # ═══════════════════════════════════════════════════════════════
        "Ley General de los Registros Públicos (Ley 698)": {
            "tipo": "ley",
            "articles": [
                "Art. 1.- La presente Ley tiene por objeto regular la organización y funcionamiento de los Registros Públicos de la República de Nicaragua.",
                "Art. 2.- Los Registros Públicos garantizan la seguridad jurídica del tráfico de bienes, la publicidad y la oponibilidad frente a terceros de los derechos, actos y contratos inscribibles.",
                "Art. 4.- El Registro Público de la Propiedad tiene por objeto la inscripción de los títulos de dominio, derechos reales, gravámenes, cancelaciones y anotaciones preventivas sobre bienes inmuebles.",
                "Art. 8.- Rige el principio de legalidad registral. El registrador calificará la legalidad de las formas extrínsecas de los documentos, la capacidad de los otorgantes y la validez del acto dispositivo.",
                "Art. 15.- Rige el principio de prioridad registral: 'Primero en tiempo, primero en derecho'. El acto que se inscriba primero en el tiempo tiene prioridad sobre cualquier otro título posterior.",
                "Art. 21.- Los asientos registrales están bajo la salvaguarda de los tribunales y producen todos sus efectos mientras no se declare su inexactitud en los términos establecidos en esta Ley.",
                "Art. 30.- La inscripción no convalida los actos o contratos que sean nulos con arreglo a las leyes.",
                "Art. 42.- Las inscripciones se extinguen por su cancelación total o parcial o por la caducidad del plazo legal de la anotación preventiva.",
                "Art. 58.- El Registro Mercantil tiene por objeto la inscripción de los comerciantes, de las sociedades mercantiles y de los actos y contratos de comercio que determinen las leyes.",
                "Art. 75.- El Registro de Personas tiene por objeto la inscripción de los actos y hechos relativos al estado civil de las personas naturales.",
                "Art. 89.- El Registro de la Propiedad Intelectual tiene por objeto la inscripción de los derechos de propiedad intelectual, marcas, patentes y nombres comerciales.",
            ]
        },
        # ═══════════════════════════════════════════════════════════════
        # 5. CÓDIGO DE COMERCIO DE NICARAGUA
        # ═══════════════════════════════════════════════════════════════
        "Código de Comercio de la República de Nicaragua": {
            "tipo": "ley",
            "articles": [
                "Art. 1.- Son comerciantes los que, teniendo capacidad legal para ejercer el comercio, se dedican a él habitualmente.",
                "Art. 6.- Los comerciantes tienen obligación de matricularse en el Registro Mercantil, llevar la contabilidad de sus negocios y conservar su correspondencia comercial.",
                "Art. 28.- Las obligaciones de los comerciantes son: la matrícula, la contabilidad, la conservación de correspondencia y los demás requisitos legales.",
                "Art. 118.- Las sociedades mercantiles se constituirán adoptando alguna de las formas establecidas en este Código: colectiva, en comandita simple, anónima, de responsabilidad limitada.",
                "Art. 121.- Las sociedades mercantiles constituidas con arreglo a las disposiciones de este Código gozan de personalidad jurídica propia, distinta de la de los socios individualmente considerados.",
                "Art. 201.- La sociedad anónima es una persona jurídica formada por la reunión de un fondo común dividido en acciones, suministrado por accionistas responsables sólo hasta el monto de sus respectivas acciones.",
                "Art. 245.- Las acciones son títulos que representan partes alícuotas del capital social de una sociedad anónima.",
                "Art. 340.- Las obligaciones mercantiles no se presumen gratuitas. Todo préstamo o depósito mercantil devengará los intereses pactados o, en su defecto, el interés legal.",
                "Art. 356.- La letra de cambio es un título de crédito por el cual una persona llamada girador ordena a otra llamada girado que pague a un tercero una suma determinada de dinero.",
                "Art. 385.- El pagaré a la orden es un título de crédito que contiene la promesa incondicional del suscriptor de pagar una suma determinada de dinero.",
                "Art. 430.- El cheque es un título de crédito girado contra un banco, pagadero a la vista, en virtud de una provisión previa de fondos del librador.",
                "Art. 500.- Se declara en quiebra al comerciante que cesa en el pago corriente de sus obligaciones. La quiebra puede ser fortuita, culpable o fraudulenta.",
            ]
        },
        # ═══════════════════════════════════════════════════════════════
        # 6. LEY DEL NOTARIADO DE NICARAGUA
        # ═══════════════════════════════════════════════════════════════
        "Ley del Notariado de la República de Nicaragua": {
            "tipo": "ley",
            "articles": [
                "Art. 1.- El Notariado es una función pública que el Estado reglamenta para dar seguridad jurídica y certeza legal a los actos y contratos celebrados ante los notarios.",
                "Art. 2.- El Notariado es la institución del Estado que otorga carácter público, autenticidad y fuerza probatoria a los actos y contratos celebrados ante los notarios públicos.",
                "Art. 3.- Para ejercer el notariado se requiere ser Abogado y Notario Público debidamente autorizado por la Excelentísima Corte Suprema de Justicia.",
                "Art. 10.- El Notario debe cerciorarse de la identidad de las partes y, cuando no las conozca personalmente, exigir la presentación de cédula de identidad o pasaporte.",
                "Art. 15.- El Notario está obligado a redactar las escrituras matrices en el idioma oficial, de forma correlativa y cronológica en su protocolo, sin tachaduras ni enmiendas.",
                "Art. 16.- Cada año, el Notario debe abrir un nuevo protocolo con papel sellado de ley, debidamente autorizado por la Corte Suprema de Justicia.",
                "Art. 20.- El protocolo notarial es la colección ordenada y encuadernada de las escrituras matrices autorizadas durante un año calendario.",
                "Art. 24.- Las escrituras públicas deben contener: la comparecencia de los otorgantes, fe de conocimiento, objeto del contrato, cláusulas sustantivas, advertencias de ley, y las firmas.",
                "Art. 27.- El testimonio es la copia textual y fiel de la escritura matriz, expedida por el Notario autorizante con las formalidades de ley.",
                "Art. 30.- Las actas notariales son instrumentos públicos que contienen la narración fiel de hechos o circunstancias que el Notario presencia o que le constan.",
                "Art. 35.- Son prohibiciones del Notario: autorizar escrituras a favor propio, de su cónyuge o de parientes dentro del cuarto grado de consanguinidad o segundo de afinidad.",
                "Art. 40.- La certificación notarial es el acto por el cual el Notario da fe de lo que ve, oye o percibe por sus sentidos.",
                "Art. 43.- El Notario responderá civil, penal y administrativamente por la falsedad, negligencia o nulidad de los instrumentos públicos redactados en su protocolo.",
                "Art. 50.- El Notario debe remitir su protocolo cerrado al Archivo General de Protocolos de la Corte Suprema de Justicia dentro de los quince primeros días de enero de cada año.",
            ]
        },
        # ═══════════════════════════════════════════════════════════════
        # 7. CÓDIGO PROCESAL CIVIL DE NICARAGUA (Ley 902)
        # ═══════════════════════════════════════════════════════════════
        "Código Procesal Civil de Nicaragua (Ley 902)": {
            "tipo": "ley",
            "articles": [
                "Art. 1.- Este Código regula la actividad procesal en los asuntos civiles, mercantiles, agrarios y demás que no tengan una vía procesal propia.",
                "Art. 14.- Todo proceso civil se inicia a instancia de parte. El juez no podrá iniciar de oficio ningún proceso civil.",
                "Art. 34.- Las partes podrán comparecer por sí mismas o por medio de apoderado constituido con las formalidades legales.",
                "Art. 94.- La demanda es el acto procesal por medio del cual el actor ejercita la acción proponiendo al órgano jurisdiccional una pretensión.",
                "Art. 96.- La demanda deberá contener: designación del juzgado, nombre y domicilio del actor y demandado, hechos, fundamentos de derecho y petitorio.",
                "Art. 116.- Admitida la demanda, se emplazará al demandado para que la conteste dentro de treinta días hábiles.",
                "Art. 200.- Son medios de prueba: la declaración de parte, los documentos públicos y privados, el dictamen pericial, la inspección judicial y los testigos.",
                "Art. 210.- Los documentos públicos hacen plena prueba entre las partes y frente a terceros respecto de los hechos que motivan su otorgamiento.",
                "Art. 390.- La sentencia definitiva pondrá fin al proceso en primera instancia, resolviendo todas las cuestiones planteadas.",
                "Art. 420.- Contra la sentencia definitiva procede el recurso de apelación ante el Tribunal de Apelaciones.",
                "Art. 490.- El recurso de casación procede contra las sentencias y autos definitivos dictados en segunda instancia por los Tribunales de Apelaciones.",
            ]
        },
        # ═══════════════════════════════════════════════════════════════
        # 8. CÓDIGO PROCESAL PENAL DE NICARAGUA (Ley 406)
        # ═══════════════════════════════════════════════════════════════
        "Código Procesal Penal de Nicaragua (Ley 406)": {
            "tipo": "ley",
            "articles": [
                "Art. 1.- Nadie podrá ser condenado a una pena o sometido a una medida de seguridad sino mediante una sentencia firme, dictada por un tribunal competente.",
                "Art. 2.- (Presunción de Inocencia) Toda persona a quien se impute un delito se presumirá inocente mientras no se pruebe su culpabilidad conforme la ley.",
                "Art. 4.- El imputado tiene derecho a la defensa material y técnica. Si no nombra defensor, el Estado le designará un defensor público.",
                "Art. 51.- La acción penal pública es ejercida por el Ministerio Público, de oficio o por denuncia.",
                "Art. 88.- La denuncia es el acto por el cual se pone en conocimiento de la autoridad la perpetración de un hecho delictivo.",
                "Art. 160.- Las medidas cautelares se decretarán por resolución judicial motivada. La prisión preventiva sólo procederá cuando las demás medidas resulten insuficientes.",
                "Art. 254.- El juicio oral es público, contradictorio y continuo. Se desarrollará ante el juez o tribunal competente con la presencia ininterrumpida de las partes.",
                "Art. 268.- La sentencia se dictará inmediatamente después de la deliberación. El juez o tribunal apreciará las pruebas según las reglas de la sana crítica.",
                "Art. 330.- Contra la sentencia de primera instancia procede el recurso de apelación dentro de los seis días hábiles posteriores a la notificación.",
            ]
        },
    }

    async with async_session() as session:
        inserted_sources = 0
        inserted_chunks = 0

        for title, info in laws_corpus.items():
            # Check if source already exists
            result = await session.execute(
                text("SELECT id FROM legal_sources WHERE titulo = :titulo"),
                {"titulo": title}
            )
            source_row = result.fetchone()

            if source_row:
                source_id = source_row[0]
                print(f"  📘 '{title}' ya existe, agregando artículos faltantes...")
            else:
                source_id = uuid.uuid4()
                await session.execute(
                    text("""
                        INSERT INTO legal_sources (id, titulo, tipo_fuente, estado, created_at, updated_at)
                        VALUES (:id, :titulo, :tipo, 'vigente', NOW(), NOW())
                    """),
                    {"id": source_id, "titulo": title, "tipo": info["tipo"]}
                )
                inserted_sources += 1
                print(f"  📗 '{title}' creado exitosamente.")

            # Ingest articles as chunks
            for i, article_text in enumerate(info["articles"]):
                chunk_hash = hashlib.sha256(article_text.encode("utf-8")).hexdigest()

                # Check if chunk already exists
                exists_result = await session.execute(
                    text("SELECT id FROM legal_chunks WHERE hash_contenido = :h"),
                    {"h": chunk_hash}
                )
                if exists_result.fetchone():
                    continue

                embedding = get_deterministic_embedding(article_text)
                emb_literal = embedding_to_pgvector_literal(embedding)

                chunk_id = uuid.uuid4()
                await session.execute(
                    text("""
                        INSERT INTO legal_chunks
                            (id, source_type, source_id, chunk_index, contenido_texto,
                             vector_embedding, hash_contenido, estado_vigencia, created_at, updated_at)
                        VALUES
                            (:id, :stype, :sid, :idx, :contenido,
                             CAST(:emb AS vector), :hash, 'vigente', NOW(), NOW())
                    """),
                    {
                        "id": chunk_id,
                        "stype": info["tipo"],
                        "sid": source_id,
                        "idx": i,
                        "contenido": article_text,
                        "emb": emb_literal,
                        "hash": chunk_hash,
                    }
                )
                inserted_chunks += 1

        await session.commit()

        # Print summary
        total_sources = await session.execute(text("SELECT COUNT(*) FROM legal_sources"))
        total_chunks = await session.execute(text("SELECT COUNT(*) FROM legal_chunks"))

        print(f"\n{'='*60}")
        print(f"✅ SIEMBRA COMPLETADA CON ÉXITO")
        print(f"{'='*60}")
        print(f"  Nuevas Leyes/Códigos insertados:     {inserted_sources}")
        print(f"  Nuevos Artículos vectorizados:        {inserted_chunks}")
        print(f"  Total Fuentes Legales en BD:          {total_sources.scalar()}")
        print(f"  Total Fragmentos Vectoriales en BD:   {total_chunks.scalar()}")
        print(f"{'='*60}")

if __name__ == "__main__":
    asyncio.run(seed_codes())
