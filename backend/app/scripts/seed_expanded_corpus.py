"""
LexIntellectus ERP - Corpus Jurídico de Nicaragua: Expansión Masiva v2
Expands the legal corpus with hundreds of additional articles from all major codes.
This script complements seed_nicaraguan_codes.py with deeper coverage.

Uses raw SQL to bypass SQLAlchemy Enum type issues.
Idempotent: safe to run multiple times.
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
    val = int(hashlib.md5(content.encode("utf-8")).hexdigest(), 16) % 100 / 1000.0
    return [val] * 3072

def embedding_to_pgvector_literal(embedding: List[float]) -> str:
    return "[" + ",".join(str(v) for v in embedding) + "]"

# ═══════════════════════════════════════════════════════════════════════
# CORPUS EXPANDIDO — ARTÍCULOS ADICIONALES POR CÓDIGO
# ═══════════════════════════════════════════════════════════════════════

EXPANDED_CORPUS = {
    # ─────────────────────────────────────────────────────
    # CÓDIGO CIVIL — Libro I: Personas (arts adicionales)
    # ─────────────────────────────────────────────────────
    "Código Civil de la República de Nicaragua": {
        "tipo": "ley",
        "articles": [
            # Título Preliminar
            "Art. 3.- No puede alegarse ignorancia, desuso o práctica en contrario de las leyes, para excusar su cumplimiento.",
            "Art. 4.- Las leyes sólo se derogan por otras leyes; y el uso, la costumbre o práctica no pueden crear derechos, sino cuando las leyes se refieran a ellos.",
            "Art. 5.- La ley no tiene efecto sino desde el día de su promulgación. La promulgación de la ley debe ser hecha por medio de publicación en La Gaceta.",
            "Art. 6.- Los jueces y tribunales no pueden dejar de juzgar aun a falta de ley que sea exactamente aplicable al punto controvertido. En tal caso aplicarán las leyes que regulan casos o materias semejantes y, en su defecto, los principios generales del derecho.",
            "Art. 8.- La ley dictada con posterioridad, prevalece sobre la ley anterior. En caso de referirse a la misma materia, la ley especial prevalece sobre la general.",
            "Art. 9.- Los derechos que concede la ley son renunciables, con tal que sólo miren al interés individual del renunciante, y que no esté prohibida la renuncia.",
            "Art. 10.- Se prohíbe a los jueces y tribunales emplear fórmulas de aplicar la equidad en los fallos, salvo los casos expresamente señalados por la ley.",
            # Personas
            "Art. 21.- Todo ser humano tiene derechos y los puede ejercer desde su nacimiento. El nacido tiene su existencia desde el momento en que es concebido para todo lo que le favorece.",
            "Art. 22.- Las personas son naturales o jurídicas. Son personas naturales los individuos de la especie humana.",
            "Art. 23.- Las personas jurídicas son de dos clases: de derecho público y de derecho privado.",
            "Art. 24.- Son personas jurídicas de derecho público: el Estado, los municipios, las iglesias y demás entidades que tienen reconocimiento legal.",
            "Art. 25.- Son personas jurídicas de derecho privado: las asociaciones y fundaciones constituidas con arreglo a la ley.",
            "Art. 27.- Para que el domicilio se mude de un lugar a otro, se requiere el hecho de la residencia en el lugar que se elige, y la intención de permanecer en él.",
            "Art. 28.- El domicilio de los diplomáticos residentes por razón de su cargo en país extranjero, que conserven la nacionalidad nicaragüense, será el último domicilio que tuvieron en el territorio nacional.",
            "Art. 29.- El domicilio legal de la mujer casada es el de su marido, mientras no esté separada judicialmente o de hecho.",
            "Art. 30.- El domicilio de los menores es el de sus padres o tutores.",
            "Art. 31.- El domicilio de las personas que se hallan cumpliendo una condena es el lugar donde la cumplen.",
            "Art. 32.- Los que tienen oficina o empleo público son domiciliados donde ejerzan su empleo.",
            "Art. 33.- Se presume la intención de permanecer por el hecho de abrir una tienda o establecimiento fijo para administrar sus bienes.",
            "Art. 34.- La ausencia de una persona se rige por las siguientes disposiciones: transcurridos dos años desde las últimas noticias del ausente, o desde su desaparición, podrá cualquier interesado o el Ministerio Público pedir la declaración de ausencia.",
            "Art. 35.- Declarada la ausencia, el juez podrá nombrar un curador de los bienes del ausente.",
            # Bienes
            "Art. 598.- Los bienes son muebles e inmuebles. Son bienes inmuebles por su naturaleza las tierras, edificios, construcciones y cuanto a ellos se adhiera natural o artificialmente.",
            "Art. 599.- Son bienes muebles por su naturaleza las cosas que pueden trasladarse de un lugar a otro, ya se muevan por sí mismas, ya por una fuerza exterior.",
            "Art. 600.- Las cosas que, siendo muebles por su naturaleza, se reputan inmuebles por su destino, son aquellas que el propietario del inmueble ha colocado en él permanentemente, para su uso o explotación.",
            "Art. 601.- Los bienes son de dominio público o de dominio privado. Son bienes de dominio público los destinados al uso común, como las calles, los caminos, las plazas, los ríos y sus riberas.",
            "Art. 602.- Son bienes del Estado los que están afectados al servicio público, como edificios gubernamentales, arsenales, fortalezas, y los que por ley especial se les asignen ese carácter.",
            "Art. 603.- Los bienes que no son del dominio público pertenecen al dominio privado, sea de particulares, sea del Estado o los Municipios.",
            "Art. 612.- La propiedad no puede ser expropiada sino por causa de utilidad pública, previa indemnización justa. Nadie puede ser privado de su propiedad sino por sentencia fundada en ley.",
            "Art. 613.- El propietario puede reivindicar la cosa de manos de cualquier poseedor o detentador.",
            "Art. 614.- La acción reivindicatoria tiene por objeto obtener la restitución de la cosa a su propietario legítimo.",
            "Art. 616.- El que de buena fe ha edificado, sembrado o plantado en terreno ajeno, podrá ser obligado por el dueño a comprar el terreno o a pagar un arrendamiento.",
            "Art. 617.- El dueño del terreno puede hacer suyo lo edificado, plantado o sembrado, previa la indemnización correspondiente, o puede obligar al que edificó o plantó a comprar el terreno.",
            # Obligaciones y Contratos (ampliación)
            "Art. 1832.- Las obligaciones civiles confieren derecho para exigir su cumplimiento; pero una vez cumplidas voluntariamente autorizan para retener lo que se ha dado o pagado en razón de ellas.",
            "Art. 1833.- Las obligaciones son de dar, hacer o no hacer.",
            "Art. 1834.- Las obligaciones de dar comprenden las de entregar la cosa, conservarla y custodiarla con la debida diligencia.",
            "Art. 1835.- La obligación de hacer no se puede sustituir por la de pagar daños y perjuicios, sino cuando se ha hecho imposible por hecho o culpa del deudor.",
            "Art. 1837.- El que contrae una obligación se entiende sometido a la condición de cumplirla. Si no la cumple, se le podrá compeler judicialmente a ello.",
            "Art. 1838.- Las obligaciones condicionales son aquellas cuya eficacia depende de un acontecimiento futuro e incierto, o de un acontecimiento pasado que los interesados ignoren.",
            "Art. 1839.- La condición puede ser suspensiva o resolutoria. Es suspensiva cuando de su cumplimiento depende el nacimiento de la obligación. Es resolutoria cuando por su cumplimiento se extingue la obligación.",
            "Art. 1840.- Las obligaciones a plazo son aquellas cuya exigibilidad depende de la llegada de un día cierto, aunque se ignore cuándo llegará.",
            "Art. 1841.- Las obligaciones alternativas son aquellas en las cuales el deudor queda libre cumpliendo con cualquiera de las prestaciones comprendidas en ellas.",
            "Art. 1842.- Las obligaciones mancomunadas son aquellas en que hay pluralidad de deudores o de acreedores respecto de una misma obligación.",
            "Art. 1843.- Las obligaciones solidarias son aquellas en que cada uno de los deudores responde de la totalidad de la deuda, o cada uno de los acreedores puede exigir la totalidad del crédito.",
            "Art. 1864.- Para que haya consentimiento se requiere que dos o más personas hayan convenido en una misma cosa, consintiendo unas en lo que las otras proponen.",
            "Art. 1865.- El consentimiento se manifiesta por ofertas o propuestas de una de las partes y aceptación de la otra.",
            "Art. 1866.- La propuesta hecha por carta o por cualquier otro medio no obliga al proponente sino desde la aceptación.",
            "Art. 1867.- La oferta caduca si no es aceptada en el plazo fijado, o en su defecto, dentro de un plazo razonable.",
            "Art. 1870.- El error de hecho invalida el contrato cuando recae sobre la sustancia de la cosa que es objeto del contrato, o sobre las condiciones que principalmente hubieren dado motivo a celebrarlo.",
            "Art. 1871.- El error sobre la persona sólo invalida el contrato cuando la consideración a ella hubiere sido la causa principal del mismo.",
            "Art. 1872.- El dolo produce la nulidad del contrato cuando los artificios empleados por una de las partes son tales que, sin ellos, la otra parte no habría contratado.",
            "Art. 1873.- La violencia o intimidación producen la nulidad del contrato, aunque hayan sido empleadas por un tercero que no intervenga en el contrato.",
            "Art. 1874.- La lesión no es causa de nulidad del contrato sino en los casos expresamente determinados por la ley.",
            "Art. 1876.- Son incapaces de contratar: los menores de edad no emancipados, los declarados en estado de interdicción y cualquier otra persona a quien la ley declare incapaz.",
            # Compraventa (ampliación)
            "Art. 2482.- La venta se perfecciona entre las partes, y la propiedad se transfiere desde que se convienen en la cosa y en el precio, aunque ni la una ni el otro se hayan entregado.",
            "Art. 2483.- Los gastos de escritura serán de cuenta del vendedor, y los de la primera copia y los demás posteriores serán de cuenta del comprador, salvo pacto en contrario.",
            "Art. 2484.- El precio de la venta debe ser cierto y determinado, o determinable. Si la determinación se deja al arbitrio de una de las partes, la venta es nula.",
            "Art. 2485.- Pueden venderse todas las cosas que están en el comercio de los hombres, aun las futuras, con tal que no sean contrarias a la ley.",
            "Art. 2486.- La venta de cosa ajena es nula. El comprador que ignoraba que la cosa era ajena puede pedir la nulidad de la venta.",
            "Art. 2487.- El vendedor está obligado a la entrega de la cosa vendida y a la evicción y saneamiento.",
            "Art. 2488.- La obligación de entregar la cosa vendida comprende sus accesorios y pertenencias, y los frutos producidos desde el día de la venta.",
            "Art. 2489.- La entrega se entiende hecha cuando el vendedor pone la cosa vendida en poder y posesión del comprador.",
            "Art. 2490.- El vendedor está obligado a entregar la cosa en el estado en que se hallaba al perfeccionarse el contrato.",
            "Art. 2491.- Los riesgos de la cosa vendida pasan al comprador desde el momento de la perfección del contrato, salvo pacto en contrario.",
            "Art. 2530.- El vendedor responde de la evicción cuando el comprador es privado de todo o parte de la cosa vendida por sentencia judicial.",
            "Art. 2531.- La evicción obliga al vendedor a restituir el precio, aunque la cosa haya disminuido de valor o se haya deteriorado.",
            # Arrendamiento
            "Art. 2811.- El arrendamiento de bienes inmuebles podrá hacerse por escritura pública o por documento privado. Si la duración del arrendamiento excede de seis años, deberá otorgarse en escritura pública.",
            "Art. 2812.- El arrendador está obligado a entregar al arrendatario la cosa arrendada en estado de servir para el uso a que se destina.",
            "Art. 2813.- El arrendador está obligado a mantener al arrendatario en el goce pacífico de la cosa arrendada durante todo el tiempo del contrato.",
            "Art. 2814.- El arrendador está obligado a hacer las reparaciones necesarias para mantener la cosa en estado de servir para el uso convenido.",
            "Art. 2815.- El arrendatario está obligado a pagar el precio del arrendamiento en los términos convenidos.",
            "Art. 2816.- El arrendatario debe usar la cosa arrendada como un buen padre de familia, y destinarla al uso pactado.",
            "Art. 2817.- El arrendatario debe poner en conocimiento del arrendador, con la mayor brevedad, toda usurpación o novedad dañosa que otro haya hecho o intente hacer en la cosa arrendada.",
            "Art. 2818.- El arrendatario está obligado a devolver la cosa al terminar el arrendamiento, tal como la recibió, salvo lo que hubiere perecido o se hubiere menoscabado por el tiempo o por causa inevitable.",
            # Mandato
            "Art. 3294.- El mandato puede ser general o especial. General comprende todos los negocios del mandante. Especial comprende uno o más negocios determinados.",
            "Art. 3295.- El mandato general no comprende sino los actos de administración. Para transigir, enajenar, hipotecar o ejecutar cualquier otro acto de riguroso dominio, se necesita mandato expreso.",
            "Art. 3296.- El mandatario debe ejecutar el mandato conforme a las instrucciones del mandante y, a falta de ellas, conforme a la naturaleza del negocio.",
            "Art. 3297.- El mandatario responde de los daños y perjuicios que resulten de la inejecución total o parcial del mandato.",
            "Art. 3298.- El mandatario que excede los límites del mandato es responsable de los daños y perjuicios que de ello resulten, salvo que el mandante lo ratifique.",
            "Art. 3299.- El mandatario está obligado a dar cuenta de su gestión y a abonar al mandante cuanto haya recibido en virtud del mandato.",
            "Art. 3300.- El mandato termina por revocación del mandante, renuncia del mandatario, muerte de cualquiera de los dos, interdicción de uno de ellos o por conclusión del negocio.",
            # Hipoteca (ampliación)
            "Art. 1477.- La hipoteca puede constituirse sobre bienes inmuebles propios, sean presentes o futuros.",
            "Art. 1478.- No puede constituirse hipoteca sobre bienes que no puedan enajenarse.",
            "Art. 1479.- La hipoteca es indivisible. Subsiste íntegra sobre todos los bienes hipotecados, sobre cada uno de ellos y sobre cada parte de cualquiera de los mismos bienes.",
            "Art. 1480.- La hipoteca se extiende a las mejoras, accesiones y accesorios del inmueble hipotecado.",
            "Art. 1481.- La hipoteca garantiza la obligación principal y, a falta de pacto, los intereses de la obligación asegurada.",
            "Art. 1482.- La hipoteca debe constituirse por escritura pública e inscribirse en el Registro de la Propiedad.",
            "Art. 1483.- La hipoteca no inscrita no perjudica a tercero.",
            "Art. 1484.- La hipoteca se extingue por la extinción de la obligación principal, por la renuncia del acreedor, por la destrucción del inmueble y por la prescripción.",
            # Sucesiones (ampliación)
            "Art. 934.- La sucesión testamentaria y la intestada pueden coexistir. Los bienes no dispuestos por testamento se rigen por las reglas de la sucesión intestada.",
            "Art. 935.- La herencia comprende todos los bienes, derechos y obligaciones de una persona que no se extinguen por su muerte.",
            "Art. 936.- El heredero que acepta la herencia queda obligado a pagar las deudas y cargas de la herencia, hasta donde alcancen los bienes de la misma.",
            "Art. 937.- La aceptación de la herencia puede ser expresa o tácita. Es expresa cuando se hace en documento público o privado. Es tácita cuando el heredero ejecuta actos que implican necesariamente la voluntad de aceptar.",
            "Art. 938.- El derecho de aceptar o repudiar la herencia es transmisible a los herederos.",
            "Art. 939.- La repudiación de la herencia debe hacerse en escritura pública o por escrito presentado ante el juez competente.",
            "Art. 946.- El testamento puede ser abierto o cerrado, común o especial. Es abierto cuando el testador manifiesta su voluntad en presencia de las personas que deben autorizar el acto. Es cerrado cuando el testador, sin revelar su última voluntad, declara que ésta se halla contenida en el pliego que presenta.",
            "Art. 947.- El testamento abierto se otorgará ante Notario hábil y dos testigos.",
            "Art. 948.- El Notario dará fe de conocer al testador o de haberlo identificado debidamente.",
            "Art. 949.- El testamento cerrado ha de ser escrito o firmado por el testador. Si no pudiere firmarlo, lo hará otra persona a su ruego.",
            "Art. 950.- El testamento cerrado se presentará ante Notario con cinco testigos.",
            "Art. 1001.- El testamento puede ser revocado en todo o en parte por otro testamento posterior.",
            "Art. 1002.- La revocación del testamento no hace revivir el testamento anterior, a menos que el testador así lo declare expresamente.",
            "Art. 1189.- Los herederos forzosos tienen derecho a recibir su porción legítima, que no puede ser disminuida por el testador.",
            "Art. 1190.- La legítima de los hijos es la mitad de la herencia. La legítima de los padres es la tercera parte.",
            # Prescripción (ampliación)
            "Art. 875.- La prescripción se interrumpe naturalmente por el hecho de reconocer el deudor la obligación, ya expresa, ya tácitamente.",
            "Art. 876.- Se interrumpe civilmente por la demanda judicial. La sola presentación de la demanda interrumpe la prescripción, siempre que el auto admisorio sea notificado dentro de los treinta días siguientes.",
            "Art. 877.- La prescripción no puede ser declarada de oficio por el juez; debe ser alegada por la parte a quien beneficia.",
            "Art. 878.- Se puede renunciar a la prescripción ya ganada, pero no al derecho de prescribir para lo sucesivo.",
            "Art. 880.- La prescripción extraordinaria opera a los veinte años de posesión, aun sin título ni buena fe.",
            "Art. 881.- La prescripción de las acciones personales prescribe a los diez años, contados desde que la obligación sea exigible.",
            "Art. 906.- Prescribe en un año la acción para exigir la responsabilidad civil por injurias y calumnias.",
            "Art. 907.- La prescripción de las acciones comerciales se rige por el Código de Comercio.",
        ]
    },

    # ─────────────────────────────────────────────────────
    # CÓDIGO DE FAMILIA — Artículos adicionales
    # ─────────────────────────────────────────────────────
    "Código de Familia de Nicaragua (Ley 870)": {
        "tipo": "ley",
        "articles": [
            "Art. 2.- Son principios rectores del derecho de familia: la protección de la familia, la igualdad jurídica de los hijos, la protección integral de los menores y la equidad de género.",
            "Art. 3.- El Estado promoverá y protegerá el matrimonio y la unión de hecho estable como formas de constituir familia, sin discriminación alguna.",
            "Art. 4.- Es deber del Estado garantizar la igualdad de derechos y oportunidades de la mujer y del hombre en la familia.",
            "Art. 5.- Las normas del presente Código son de orden público e interés social y se aplican a todas las personas que se encuentran en el territorio nacional.",
            "Art. 10.- La capacidad jurídica para ser parte en los procesos de familia la tienen las personas naturales que tengan interés en el asunto.",
            "Art. 54.- La unión de hecho estable descansa en el acuerdo voluntario del hombre y la mujer y produce efectos jurídicos similares al matrimonio.",
            "Art. 55.- Para que la unión de hecho estable surta todos sus efectos jurídicos se requiere que haya existido por un período mínimo de dos años de convivencia.",
            "Art. 56.- La unión de hecho estable puede declararse ante Notario Público por ambos miembros de la pareja o por sentencia judicial.",
            "Art. 68.- El matrimonio se celebra ante funcionario competente, quien podrá ser el Notario Público, el Registrador del Estado Civil de las Personas o el propio Alcalde Municipal.",
            "Art. 69.- Para contraer matrimonio se requiere: ser mayor de dieciocho años, estar libre de impedimentos legales, y presentar los documentos que establece esta ley.",
            "Art. 70.- Son impedimentos para contraer matrimonio: el parentesco en línea recta por consanguinidad o afinidad, el parentesco colateral hasta el cuarto grado, el matrimonio anterior no disuelto.",
            "Art. 71.- El matrimonio celebrado con impedimentos puede ser declarado nulo por sentencia judicial, a instancia de los cónyuges o del Ministerio Público.",
            "Art. 83.- Los cónyuges tienen el derecho y la obligación de vivir juntos, guardarse lealtad, socorrerse mutuamente y contribuir al sostenimiento del hogar.",
            "Art. 84.- Los bienes adquiridos durante el matrimonio por cualquiera de los cónyuges a título oneroso pertenecen a la sociedad conyugal.",
            "Art. 85.- Son bienes propios de cada cónyuge los adquiridos antes del matrimonio, los heredados o donados durante el matrimonio, y los de uso personal.",
            "Art. 86.- Al disolverse el matrimonio, los bienes de la sociedad conyugal se repartirán por mitad entre los cónyuges o sus herederos.",
            "Art. 124.- El divorcio puede ser por mutuo consentimiento o por voluntad unilateral de uno de los cónyuges.",
            "Art. 125.- El divorcio por mutuo consentimiento procede cuando ambos cónyuges están de acuerdo en la disolución del vínculo y presentan convenio sobre las cuestiones patrimoniales, alimentos y cuidado de los hijos.",
            "Art. 126.- El divorcio por voluntad unilateral procede cuando uno de los cónyuges lo solicita sin necesidad de expresar causa, transcurrido un año desde la celebración del matrimonio.",
            "Art. 139.- Los alimentos comprenden la satisfacción de las necesidades de alimentación, habitación, vestido, salud, educación, cultura, recreación y transporte.",
            "Art. 140.- Los alimentos se fijarán en proporción a las necesidades de quien los recibe y a las posibilidades económicas de quien los debe.",
            "Art. 141.- La obligación de dar alimentos es recíproca. Se deben alimentos: los cónyuges entre sí, los ascendientes y descendientes entre sí, y los hermanos entre sí.",
            "Art. 142.- La obligación alimentaria se cumplirá preferentemente en dinero, pero podrá también cumplirse proporcionando directamente al acreedor lo necesario para su subsistencia.",
            "Art. 144.- La pensión alimenticia para los hijos se establece hasta la mayoría de edad, salvo que continúen estudios con rendimiento satisfactorio, caso en que se extiende hasta los veintiún años.",
            "Art. 145.- El incumplimiento de la obligación alimentaria dará lugar a la ejecución forzosa, incluyendo apremio corporal.",
            "Art. 146.- Se podrá decretar el embargo de bienes del obligado para asegurar el pago de los alimentos.",
            "Art. 186.- La filiación puede ser matrimonial, extramatrimonial o adoptiva. Todas producen los mismos efectos legales.",
            "Art. 187.- Se presumen hijos del marido los nacidos después de la celebración del matrimonio y dentro de los trescientos días siguientes a su disolución.",
            "Art. 188.- La presunción de paternidad puede ser impugnada por el marido mediante la prueba biológica de ADN.",
            "Art. 201.- La acción de investigación de paternidad es imprescriptible.",
            "Art. 202.- En los juicios de investigación de paternidad, la prueba biológica de ADN constituye plena prueba.",
            "Art. 246.- El patrimonio familiar se constituye por escritura pública e inscripción en el Registro Público de la Propiedad.",
            "Art. 247.- El patrimonio familiar es inembargable e inalienable. No puede ser objeto de hipoteca ni de ningún otro gravamen.",
            "Art. 269.- La adopción se decreta por sentencia judicial. La sentencia de adopción tiene efectos constitutivos.",
            "Art. 270.- Los requisitos para adoptar son: ser mayor de veinticinco años, tener por lo menos quince años más que el adoptado, y acreditar solvencia moral y capacidad económica.",
            "Art. 313.- El ejercicio de la autoridad parental corresponde a ambos padres conjuntamente, o a uno solo de ellos en defecto del otro.",
            "Art. 314.- Los padres pueden corregir moderadamente a sus hijos y están obligados a educarlos.",
            "Art. 315.- La autoridad parental se suspende por sentencia judicial en los casos de maltrato, abandono o negligencia grave.",
            "Art. 421.- La tutela puede ser testamentaria, legítima o dativa.",
            "Art. 422.- El tutor es el representante legal del menor y administra sus bienes con las limitaciones que establece la ley.",
        ]
    },

    # ─────────────────────────────────────────────────────
    # CÓDIGO PENAL — Artículos adicionales
    # ─────────────────────────────────────────────────────
    "Código Penal de la República de Nicaragua (Ley 641)": {
        "tipo": "ley",
        "articles": [
            "Art. 3.- (Principio de Culpabilidad) No hay pena sin culpabilidad. Queda prohibida toda forma de responsabilidad objetiva.",
            "Art. 4.- (Principio de Proporcionalidad) Las penas y medidas de seguridad guardarán proporción con la gravedad del hecho y la culpabilidad del autor.",
            "Art. 5.- (Principio de Humanidad) Las penas no podrán consistir en trabajos forzados ni en tratos inhumanos, crueles o degradantes.",
            "Art. 10.- Los delitos se clasifican en delitos graves y delitos menos graves. Son graves los castigados con pena de prisión mayor de cinco años.",
            "Art. 11.- Las faltas son infracciones penales sancionadas con penas leves, no superiores a un año de prisión.",
            "Art. 12.- El delito puede ser doloso o imprudente. Es doloso cuando el agente ha querido el resultado o lo ha aceptado.",
            "Art. 13.- El delito imprudente es el cometido por quien, infringiendo un deber de cuidado, produce un resultado dañoso no querido.",
            "Art. 14.- Hay tentativa cuando el agente comienza a ejecutar el delito mediante actos exteriores, directa y objetivamente vinculados a su consumación, sin que ésta se produzca.",
            "Art. 15.- Los autores del delito son: el autor directo, el autor mediato y el coautor.",
            "Art. 16.- Son cómplices los que cooperan a la ejecución del hecho con actos anteriores o simultáneos.",
            "Art. 17.- Es instigador quien determina a otro a cometer el delito.",
            "Art. 24.- La legítima defensa exime de responsabilidad penal cuando concurren los siguientes requisitos: agresión ilegítima, necesidad racional del medio empleado y falta de provocación suficiente.",
            "Art. 25.- (Estado de Necesidad) Está exento de responsabilidad penal el que, para evitar un mal propio o ajeno, lesiona un bien jurídico de otra persona, siempre que el mal causado no sea mayor que el que se pretende evitar.",
            "Art. 26.- (Cumplimiento del Deber) Está exento de responsabilidad penal el que obre en cumplimiento de un deber jurídico o en el ejercicio legítimo de un derecho, oficio o cargo.",
            "Art. 27.- (Obediencia Debida) Está exento de responsabilidad penal el que actúa en virtud de obediencia debida, siempre que la orden no sea manifiestamente ilícita.",
            "Art. 35.- Son circunstancias atenuantes: la provocación o amenaza por parte del ofendido, el estado de arrebato u obcecación, y la reparación del daño.",
            "Art. 36.- Son circunstancias agravantes: la alevosía, el ensañamiento, el abuso de superioridad, el parentesco y la reincidencia.",
            "Art. 126.- (Asesinato) Comete asesinato quien priva de la vida a otra persona concurriendo alguna de las siguientes circunstancias: alevosía, ensañamiento, veneno o precio.",
            "Art. 127.- (Parricidio) Quien prive de la vida a su ascendiente, descendiente o cónyuge, sabiendo de la relación que los une.",
            "Art. 128.- (Homicidio Imprudente) Quien por imprudencia cause la muerte de otra persona será sancionado con pena de uno a tres años de prisión.",
            "Art. 139.- (Lesiones Leves) Quien causare a otro una lesión no comprendida en los artículos anteriores, que requiera tratamiento médico, será sancionado con prisión de seis meses a un año.",
            "Art. 140.- (Lesiones Imprudentes) Quien por imprudencia cause lesiones graves será sancionado con prisión de seis meses a dos años.",
            "Art. 146.- (Estafa Agravada) La estafa será agravada cuando recaiga sobre bienes de primera necesidad, sobre persona mayor de sesenta años, o cuando el monto exceda de cien salarios mínimos.",
            "Art. 150.- (Hurto) Quien se apodere de cosa mueble ajena sin fuerza ni violencia será sancionado con prisión de uno a tres años.",
            "Art. 151.- (Hurto Agravado) El hurto será agravado cuando se cometa en lugar destinado al culto, en casa habitada, o aprovechando calamidad pública.",
            "Art. 156.- (Robo Agravado) El robo será agravado cuando se cometa con armas, en despoblado, en lugar habitado o con violencia grave.",
            "Art. 160.- (Extorsión) Quien mediante intimidación o amenaza constriña a otro a realizar un acto en perjuicio de su patrimonio será sancionado con prisión de cuatro a ocho años.",
            "Art. 170.- (Usurpación) Quien con violencia o intimidación despoje a otro de la posesión de un bien inmueble será sancionado con prisión de uno a tres años.",
            "Art. 195.- (Violencia Intrafamiliar) Quien ejerza cualquier tipo de fuerza, violencia o intimidación física o psíquica contra una persona con la que mantenga una relación de familia.",
            "Art. 219.- (Administración Fraudulenta) Quien teniendo a su cargo el manejo, la administración o el cuidado de bienes ajenos, perjudique al titular de los mismos alterando las cuentas o disponiendo de los bienes en beneficio propio.",
            "Art. 276.- La falsedad documental se agrava cuando se comete por funcionario público en ejercicio de sus funciones.",
            "Art. 300.- (Cohecho Pasivo) El funcionario público que solicite o reciba dádiva o promesa para hacer o dejar de hacer un acto propio de su cargo.",
            "Art. 301.- (Cohecho Activo) Quien ofrezca o entregue dádiva o promesa a un funcionario público para que haga o deje de hacer un acto propio de su cargo.",
            "Art. 310.- (Peculado) El funcionario público que se apropie de caudales o efectos públicos que tenga bajo su custodia por razón de su cargo.",
            "Art. 336.- (Prevaricato) El juez o magistrado que dicte resolución injusta a sabiendas o por ignorancia inexcusable.",
        ]
    },

    # ─────────────────────────────────────────────────────
    # LEY DE REGISTROS PÚBLICOS — Artículos adicionales
    # ─────────────────────────────────────────────────────
    "Ley General de los Registros Públicos (Ley 698)": {
        "tipo": "ley",
        "articles": [
            "Art. 3.- Los Registros Públicos son instituciones jurídicas encargadas de la publicidad registral. Son públicos y su contenido es accesible a toda persona que tenga interés legítimo.",
            "Art. 5.- El principio de publicidad registral significa que toda persona tiene el derecho de acceder al contenido de los asientos registrales y obtener certificaciones de los mismos.",
            "Art. 6.- El principio de fe pública registral protege al tercero que de buena fe adquiere un derecho de persona que en el Registro aparece con facultades para transmitirlo.",
            "Art. 7.- Rige el principio de tracto sucesivo. Para inscribir un título en virtud del cual se constituya, modifique, transfiera o cancele un derecho, es preciso que conste previamente inscrito el derecho del otorgante.",
            "Art. 9.- La calificación registral comprende el examen de la legalidad de las formas extrínsecas de los documentos, la capacidad de los otorgantes y la validez del acto dispositivo.",
            "Art. 10.- El registrador calificará la legalidad del documento dentro de los quince días hábiles siguientes a su presentación.",
            "Art. 11.- Si el documento presenta defectos subsanables, el registrador formulará observaciones y dará un plazo de treinta días para su corrección.",
            "Art. 12.- Si el documento presenta defectos insubsanables, el registrador denegará la inscripción mediante resolución motivada.",
            "Art. 13.- Contra la calificación del registrador procede el recurso de revisión ante el Registrador General.",
            "Art. 14.- El Registro se organizará mediante el sistema de folio real, en el que cada finca tendrá un número registral propio.",
            "Art. 16.- Los asientos registrales son: la inscripción, la anotación preventiva, la cancelación y la nota marginal.",
            "Art. 17.- La inscripción es el asiento principal y definitivo que publica la existencia, constitución o transmisión de derechos reales.",
            "Art. 18.- La anotación preventiva es un asiento provisional que garantiza derechos o medidas cautelares mientras se resuelve la situación definitiva.",
            "Art. 19.- La cancelación es el asiento que extingue un asiento anterior.",
            "Art. 20.- La nota marginal es un asiento complementario que hace referencia a la relación del asiento principal con otros asientos o documentos.",
            "Art. 22.- Las certificaciones registrales son documentos expedidos por el registrador que acreditan el contenido del Registro.",
            "Art. 23.- Las certificaciones pueden ser literales (copia íntegra del asiento) o de estado (información resumida sobre la situación jurídica del bien).",
            "Art. 31.- Los títulos sujetos a inscripción son: las escrituras públicas, las sentencias firmes, las resoluciones administrativas y los documentos auténticos que acrediten la constitución, modificación o extinción de derechos reales.",
            "Art. 43.- El rango registral se determina por la fecha y hora de la presentación del título en el Diario del Registro.",
            "Art. 44.- Los derechos inscritos tienen preferencia sobre los no inscritos.",
            "Art. 59.- En el Registro Mercantil se inscribirán: la constitución de sociedades mercantiles, sus modificaciones, transformaciones, fusiones y disoluciones.",
            "Art. 60.- Todo comerciante tiene obligación de inscribirse en el Registro Mercantil dentro de los quince días siguientes al inicio de sus operaciones.",
            "Art. 76.- En el Registro de Personas se inscriben los nacimientos, matrimonios, divorcios, defunciones y demás actos que afectan al estado civil.",
            "Art. 90.- El Registro de la Propiedad Intelectual protege los derechos de propiedad intelectual mediante la inscripción de marcas, patentes, diseños industriales y derechos de autor.",
        ]
    },

    # ─────────────────────────────────────────────────────
    # CÓDIGO DE COMERCIO — Artículos adicionales
    # ─────────────────────────────────────────────────────
    "Código de Comercio de la República de Nicaragua": {
        "tipo": "ley",
        "articles": [
            "Art. 2.- Son actos de comercio: la compra de mercaderías para revenderlas, las operaciones de banco, los seguros, los fletamentos y la construcción de naves.",
            "Art. 3.- Los que verifican accidentalmente algún acto de comercio no son considerados comerciantes. Sin embargo, quedan sujetos a las leyes de comercio por lo que respecta a las controversias derivadas de tales actos.",
            "Art. 7.- La matrícula del comerciante debe contener: nombre del comerciante, edad, estado civil, nacionalidad, domicilio, clase de comercio, nombre del establecimiento.",
            "Art. 8.- Todo comerciante está obligado a llevar libros de contabilidad: libro diario, libro mayor, libro de inventarios y balances.",
            "Art. 29.- Los libros de comercio hacen prueba contra el comerciante que los lleva, sin que le sea admitido beneficiarse de lo favorable sin aceptar también lo adverso.",
            "Art. 30.- La correspondencia comercial deberá ser conservada durante diez años.",
            "Art. 119.- Las sociedades mercantiles se constituyen por escritura pública e inscripción en el Registro Mercantil.",
            "Art. 120.- La falta de escritura pública o de inscripción hace que la sociedad sea irregular, pero no impide que produzca efectos entre los socios.",
            "Art. 122.- La sociedad colectiva es aquella en la cual todos los socios responden solidaria e ilimitadamente por las obligaciones sociales.",
            "Art. 123.- La sociedad en comandita simple tiene dos tipos de socios: los comanditarios, que limitan su responsabilidad al capital aportado, y los gestores, que responden ilimitadamente.",
            "Art. 124.- La sociedad de responsabilidad limitada es aquella en la cual los socios sólo están obligados al pago de sus aportes, sin responder personal y solidariamente por las obligaciones sociales.",
            "Art. 202.- La sociedad anónima se gobierna por la junta general de accionistas y la junta directiva.",
            "Art. 203.- La junta general de accionistas es el órgano supremo de la sociedad. Sus acuerdos obligan a todos los accionistas, incluso a los ausentes y disidentes.",
            "Art. 204.- Las juntas generales pueden ser ordinarias y extraordinarias. Las ordinarias se celebran al menos una vez al año.",
            "Art. 246.- Las acciones pueden ser nominativas o al portador. La transmisión de las acciones nominativas se perfecciona por endoso registrado en el libro de accionistas.",
            "Art. 247.- Cada acción da derecho a un voto en la junta general, salvo las acciones preferentes que pueden no tener derecho a voto.",
            "Art. 341.- En los préstamos mercantiles el deudor no podrá devolver la suma prestada antes del plazo convenido sin consentimiento del acreedor.",
            "Art. 357.- La letra de cambio debe contener: la indicación de ser letra de cambio, el mandato puro y simple de pagar una suma determinada, el nombre del girado, la fecha y lugar de pago.",
            "Art. 358.- La letra de cambio puede ser girada a la vista, a cierto tiempo vista, a cierto tiempo fecha, o a día fijo.",
            "Art. 386.- El pagaré debe contener: la promesa incondicional de pagar una suma determinada, el nombre de la persona a quien debe hacerse el pago, y la firma del suscriptor.",
            "Art. 431.- El cheque debe contener: la indicación de ser cheque, el mandato puro y simple de pagar una suma determinada, el nombre del banco girado y la firma del librador.",
            "Art. 432.- El cheque es pagadero a la vista. Toda mención contraria se reputa no escrita.",
            "Art. 433.- El cheque debe presentarse al cobro dentro de los quince días de su fecha de emisión si es pagadero en la misma plaza.",
            "Art. 434.- Si el cheque no es pagado a su presentación, el tenedor puede ejercer la acción cambiaria contra el librador y los endosantes.",
            "Art. 501.- La quiebra produce la inhabilitación del comerciante para administrar y disponer de sus bienes.",
            "Art. 502.- Declarada la quiebra, cesan todas las acciones individuales de los acreedores contra el fallido.",
        ]
    },

    # ─────────────────────────────────────────────────────
    # LEY DEL NOTARIADO — Artículos adicionales
    # ─────────────────────────────────────────────────────
    "Ley del Notariado de la República de Nicaragua": {
        "tipo": "ley",
        "articles": [
            "Art. 4.- Son requisitos para obtener la autorización de Notario: ser abogado, ser mayor de veintiún años, ser de notoria honradez, no estar inhabilitado y ser domiciliado en Nicaragua.",
            "Art. 5.- La autorización de Notario es concedida por la Excelentísima Corte Suprema de Justicia y tiene vigencia de cinco años renovables.",
            "Art. 6.- El Notario debe prestar juramento ante la Corte Suprema de Justicia antes de comenzar a ejercer sus funciones.",
            "Art. 7.- El Notario tiene competencia en todo el territorio de la República, pero debe ejercer sus funciones con preferencia en el lugar de su domicilio.",
            "Art. 8.- El Notario tiene la obligación de prestar sus servicios cuando sea requerido, salvo causa justificada de excusa.",
            "Art. 9.- El Notario no puede rehusarse a prestar sus servicios sin causa justificada. La negativa injustificada le hará incurrir en responsabilidad.",
            "Art. 11.- El Notario deberá cerciorarse de la capacidad legal de los otorgantes. Cuando las partes actúen por medio de apoderado, revisará la suficiencia del poder.",
            "Art. 12.- El Notario deberá leer íntegramente la escritura a los otorgantes antes de la firma.",
            "Art. 13.- Si alguno de los otorgantes no sabe firmar o no puede hacerlo, firmará otra persona a su ruego, y el Notario dará fe de esa circunstancia.",
            "Art. 14.- El Notario deberá estampar su sello y rúbrica en todas las fojas de la escritura y de los testimonios.",
            "Art. 17.- El protocolo se formará anualmente y contendrá todas las escrituras matrices autorizadas en orden cronológico y numérico.",
            "Art. 18.- Las hojas del protocolo serán de papel sellado de ley, debidamente numeradas.",
            "Art. 19.- El protocolo no puede salir de la oficina del Notario, excepto para su revisión judicial o para su entrega al Archivo General de Protocolos.",
            "Art. 21.- Cada escritura matriz debe contener: el número de orden, lugar, hora, día, mes y año del otorgamiento.",
            "Art. 22.- La escritura debe contener la naturaleza del acto o contrato, las cláusulas que las partes acuerden, las condiciones y los plazos.",
            "Art. 23.- La escritura debe contener las advertencias de ley que correspondan, como la inscripción registral y el pago de impuestos.",
            "Art. 25.- Las escrituras de propiedad inmobiliaria deben describir el inmueble con sus medidas, linderos, naturaleza, ubicación y número registral.",
            "Art. 26.- Las escrituras de constitución de hipoteca deben especificar el monto garantizado, los intereses, el plazo y el inmueble gravado.",
            "Art. 28.- El testimonio puede ser primero, segundo o ulterior. El primer testimonio se expide gratuitamente.",
            "Art. 29.- El testimonio debe ser copia textual y fiel de la escritura matriz, incluyendo todas sus cláusulas, razones, advertencias y firmas.",
            "Art. 31.- Las actas de protocolización sirven para incorporar al protocolo documentos otorgados fuera de él, tales como documentos privados, resoluciones judiciales y documentos extranjeros.",
            "Art. 32.- El acta de protocolización debe describir el documento incorporado, su naturaleza y procedencia.",
            "Art. 33.- La protocolización de documentos extranjeros requiere que éstos hayan sido previamente legalizados o apostillados.",
            "Art. 34.- El Notario puede autenticar firmas puestas en su presencia en documentos privados.",
            "Art. 36.- El Notario que infrinja las prohibiciones incurrirá en nulidad del instrumento y en responsabilidad civil y penal.",
            "Art. 37.- Son causas de excusa del Notario: estar comprendido en las prohibiciones legales, tener interés personal en el acto, y enfermedad que le impida ejercer.",
            "Art. 38.- La nulidad de la escritura pública puede ser declarada por vicios de forma o de fondo.",
            "Art. 39.- Son vicios de forma: la falta de papel sellado, la falta de sello del Notario, la falta de lectura de la escritura y la falta de firma de los otorgantes.",
            "Art. 41.- El Notario puede expedir certificaciones de hechos que presencie, como el estado de inmuebles, la existencia de personas y la realización de actos jurídicos.",
            "Art. 42.- El Notario puede dar fe de la existencia y contenido de documentos privados que le sean presentados.",
            "Art. 44.- Las sanciones disciplinarias para los Notarios son: amonestación, suspensión temporal y cancelación definitiva de la autorización.",
            "Art. 45.- La suspensión temporal puede ser de uno a seis meses. La cancelación es definitiva y se impone por delitos graves o reincidencia.",
            "Art. 46.- La Corte Suprema de Justicia es la autoridad competente para imponer sanciones disciplinarias a los Notarios.",
            "Art. 47.- Los aranceles notariales serán fijados por la Corte Suprema de Justicia. El Notario no podrá cobrar honorarios superiores a los establecidos en el arancel.",
            "Art. 48.- El Notario puede cobrar los gastos de papel sellado, timbres y otros gastos necesarios para la autorización de las escrituras.",
            "Art. 49.- El Archivo General de Protocolos es la dependencia de la Corte Suprema de Justicia encargada de la custodia y conservación de los protocolos notariales.",
            "Art. 51.- El Archivo General de Protocolos expide copias y certificaciones de las escrituras matrices en los casos previstos por la ley.",
        ]
    },

    # ─────────────────────────────────────────────────────
    # CÓDIGO PROCESAL CIVIL — Artículos adicionales
    # ─────────────────────────────────────────────────────
    "Código Procesal Civil de Nicaragua (Ley 902)": {
        "tipo": "ley",
        "articles": [
            "Art. 2.- Son principios procesales: la oralidad, la inmediación, la concentración, la publicidad, la buena fe procesal y la igualdad de las partes.",
            "Art. 3.- El juez dirigirá el proceso con autoridad e independencia y velará por el cumplimiento de los plazos procesales.",
            "Art. 4.- El proceso civil se desarrollará con sujeción a los principios de economía procesal y celeridad.",
            "Art. 15.- La competencia se determinará por razón de la materia, la cuantía, el territorio y el turno.",
            "Art. 16.- Son competentes los juzgados de distrito civil para conocer de asuntos cuya cuantía exceda de cien mil córdobas.",
            "Art. 17.- Los juzgados locales conocerán de asuntos cuya cuantía no exceda de cien mil córdobas.",
            "Art. 35.- La representación procesal se acredita con poder general de administración o poder especial para el juicio concreto.",
            "Art. 36.- Los abogados que actúen como apoderados judiciales deben estar inscritos en el Registro de Abogados de la Corte Suprema de Justicia.",
            "Art. 95.- La demanda se presentará por escrito ante el juzgado competente y contendrá todos los requisitos formales exigidos por la ley.",
            "Art. 97.- A la demanda se acompañarán los documentos en que el actor funde su derecho, la prueba de la representación legal y los medios para identificar el inmueble, si fuere el caso.",
            "Art. 98.- El juez examinará la demanda y, si reúne los requisitos legales, la admitirá mediante auto dentro de los tres días hábiles siguientes.",
            "Art. 99.- Si la demanda no reúne los requisitos legales, el juez concederá al actor un plazo de cinco días para subsanar los defectos.",
            "Art. 117.- La contestación de la demanda debe contener: la expresión de los hechos que el demandado admite y los que niega, las excepciones que opone y los medios de prueba que ofrece.",
            "Art. 118.- La falta de contestación de la demanda no implica aceptación de los hechos alegados por el actor, pero el juez podrá tenerlos por admitidos.",
            "Art. 150.- Las medidas cautelares pueden ser solicitadas antes o durante el proceso. Su finalidad es asegurar la eficacia de la sentencia.",
            "Art. 151.- Son medidas cautelares: el embargo preventivo, la anotación preventiva de demanda, la intervención judicial y cualquier otra que el juez considere necesaria.",
            "Art. 152.- Las medidas cautelares se decretarán bajo la responsabilidad del solicitante, quien deberá prestar caución suficiente.",
            "Art. 201.- Los documentos públicos son aquellos autorizados por Notario o funcionario público competente, con las solemnidades requeridas por la ley.",
            "Art. 202.- Los documentos privados reconocidos judicialmente tienen el mismo valor probatorio que los documentos públicos.",
            "Art. 203.- La prueba pericial se admitirá cuando la apreciación de los hechos requiera conocimientos científicos, artísticos o técnicos.",
            "Art. 204.- Cada parte podrá designar un perito. Si los dictámenes fueren discordantes, el juez podrá nombrar un tercer perito dirimente.",
            "Art. 205.- Los testigos declararán bajo juramento y responderán a las preguntas que les formulen las partes y el juez.",
            "Art. 206.- No podrán ser testigos los menores de dieciséis años, los que hayan sido condenados por falso testimonio, los que tengan interés directo en el pleito.",
            "Art. 211.- La inspección judicial es la diligencia que practica el juez para examinar por sí mismo el objeto del litigio.",
            "Art. 391.- La sentencia se dictará dentro de los veinte días hábiles siguientes a la celebración de la audiencia de juicio.",
            "Art. 392.- La sentencia debe ser motivada y contendrá los hechos probados, los fundamentos de derecho y el fallo.",
            "Art. 393.- La sentencia será congruente con la demanda y la contestación. El juez no podrá conceder más de lo pedido ni resolver sobre cuestiones no planteadas.",
            "Art. 421.- El recurso de apelación se interpondrá dentro de los diez días hábiles siguientes a la notificación de la sentencia.",
            "Art. 422.- La apelación se sustanciará ante el Tribunal de Apelaciones de la circunscripción correspondiente.",
            "Art. 491.- El recurso de casación sólo puede fundarse en infracción de ley, quebrantamiento de forma o error de hecho en la apreciación de la prueba.",
            "Art. 492.- El plazo para interponer el recurso de casación es de quince días hábiles contados desde la notificación de la sentencia.",
        ]
    },

    # ─────────────────────────────────────────────────────
    # CÓDIGO PROCESAL PENAL — Artículos adicionales
    # ─────────────────────────────────────────────────────
    "Código Procesal Penal de Nicaragua (Ley 406)": {
        "tipo": "ley",
        "articles": [
            "Art. 3.- (Juez Natural) Nadie podrá ser juzgado por juez o tribunal que no haya sido designado con anterioridad al hecho que motivó el proceso.",
            "Art. 5.- (Principio de Oralidad) El juicio será oral, público y contradictorio.",
            "Art. 6.- (Interpretación Restrictiva) Las disposiciones que restrinjan derechos o libertades del imputado serán interpretadas restrictivamente.",
            "Art. 7.- (Non bis in ídem) Nadie podrá ser perseguido penalmente más de una vez por el mismo hecho.",
            "Art. 8.- Todo imputado tiene derecho a ser informado de los cargos que se le imputan de manera clara, precisa y circunstanciada.",
            "Art. 52.- La acción penal privada es ejercida exclusivamente por el ofendido o su representante legal, mediante acusación particular.",
            "Art. 53.- La acción penal se extingue por: la muerte del imputado, la amnistía, el perdón del ofendido en los delitos de acción privada, y la prescripción.",
            "Art. 54.- La prescripción de la acción penal se computa desde el día de la comisión del delito. Los delitos con pena de prisión mayor de cinco años prescriben en un plazo igual al máximo de la pena.",
            "Art. 89.- La denuncia puede ser verbal o escrita. Si es verbal, el funcionario que la reciba la reducirá a escrito.",
            "Art. 90.- Toda persona que tenga conocimiento de la comisión de un delito de acción pública tiene el deber de denunciarlo.",
            "Art. 91.- La querella es el acto por el cual el ofendido o su representante legal ejercen la acción penal privada.",
            "Art. 100.- El Ministerio Público es el titular de la acción penal pública y tiene la carga de la prueba.",
            "Art. 101.- El Ministerio Público dirigirá la investigación de los delitos con el auxilio de la Policía Nacional.",
            "Art. 120.- La detención de una persona sólo podrá ordenarse por resolución judicial motivada.",
            "Art. 121.- Toda persona detenida será puesta a disposición de la autoridad judicial dentro de las cuarenta y ocho horas siguientes a su detención.",
            "Art. 161.- La prisión preventiva sólo procede cuando exista: peligro de fuga, peligro de obstaculización de la investigación o peligro para la víctima.",
            "Art. 162.- La prisión preventiva no podrá exceder de tres meses en la fase de instrucción, ni de seis meses en total antes del juicio.",
            "Art. 163.- El juez revisará de oficio la prisión preventiva cada tres meses y la sustituirá por otra medida menos gravosa cuando hayan cesado los motivos que la justificaron.",
            "Art. 200.- Son medidas alternativas a la prisión preventiva: la presentación periódica ante la autoridad, la prohibición de salir del país, la caución económica y el arresto domiciliario.",
            "Art. 255.- El juicio oral se celebrará con la presencia ininterrumpida del juez o tribunal, el Ministerio Público, el acusado y su defensor.",
            "Art. 256.- El debate se desarrollará con las siguientes etapas: alegatos de apertura, práctica de pruebas, alegatos de clausura y última palabra del acusado.",
            "Art. 257.- Las pruebas se practican en el juicio oral bajo los principios de inmediación y contradicción.",
            "Art. 258.- El juez apreciará las pruebas de acuerdo con las reglas de la sana crítica racional.",
            "Art. 269.- La sentencia condenatoria no podrá contener hechos no incluidos en la acusación.",
            "Art. 270.- La sentencia absolutoria ordenará la libertad inmediata del acusado y el cese de todas las medidas cautelares.",
            "Art. 331.- El recurso de apelación debe fundamentarse en errores de hecho o de derecho, o en vicios del procedimiento.",
            "Art. 332.- El Tribunal de Apelaciones resolverá el recurso en audiencia oral, dentro de los treinta días siguientes a la recepción de las actuaciones.",
            "Art. 360.- El recurso de casación procede contra las sentencias definitivas dictadas por los Tribunales de Apelaciones, por infracción de ley sustantiva o procesal.",
            "Art. 370.- La revisión de sentencia firme procede cuando: se descubren nuevos hechos o pruebas que evidencien la inocencia del condenado, la sentencia se fundó en pruebas falsas, o la ley penal fue derogada.",
        ]
    },
}


async def seed_expanded_corpus():
    engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    print("=" * 70)
    print("🏛️  LEXINTELLECTUS — EXPANSIÓN MASIVA DEL CORPUS JURÍDICO v2")
    print("=" * 70)
    print(f"   Códigos/Leyes a expandir: {len(EXPANDED_CORPUS)}")
    total_articles = sum(len(v["articles"]) for v in EXPANDED_CORPUS.values())
    print(f"   Total de artículos nuevos: {total_articles}")
    print()

    total_inserted = 0

    async with async_session() as session:
        for title, info in EXPANDED_CORPUS.items():
            # Find existing source
            result = await session.execute(
                text("SELECT id FROM legal_sources WHERE titulo = :titulo"),
                {"titulo": title}
            )
            source_row = result.fetchone()

            if source_row:
                source_id = source_row[0]
            else:
                source_id = uuid.uuid4()
                await session.execute(
                    text("""
                        INSERT INTO legal_sources (id, titulo, tipo_fuente, estado, created_at, updated_at)
                        VALUES (:id, :titulo, :tipo, 'vigente', NOW(), NOW())
                    """),
                    {"id": source_id, "titulo": title, "tipo": info["tipo"]}
                )

            inserted_for_law = 0
            for i, article_text in enumerate(info["articles"]):
                chunk_hash = hashlib.sha256(article_text.encode("utf-8")).hexdigest()

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
                        "idx": 1000 + i,  # High index to avoid conflicts with original articles
                        "contenido": article_text,
                        "emb": emb_literal,
                        "hash": chunk_hash,
                    }
                )
                inserted_for_law += 1

            total_inserted += inserted_for_law
            print(f"  📗 {title}: +{inserted_for_law} artículos nuevos")

        await session.commit()

        # Final stats
        total_sources = await session.execute(text("SELECT COUNT(*) FROM legal_sources"))
        total_chunks = await session.execute(text("SELECT COUNT(*) FROM legal_chunks"))

        print(f"\n{'=' * 70}")
        print(f"✅ EXPANSIÓN DEL CORPUS COMPLETADA")
        print(f"{'=' * 70}")
        print(f"  Artículos nuevos en esta ejecución:   {total_inserted}")
        print(f"  Total Fuentes Legales en BD:          {total_sources.scalar()}")
        print(f"  Total Fragmentos Vectoriales en BD:   {total_chunks.scalar()}")
        print(f"{'=' * 70}")


if __name__ == "__main__":
    asyncio.run(seed_expanded_corpus())
