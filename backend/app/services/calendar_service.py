from datetime import datetime, date, timedelta
from typing import List
import uuid
from app.models.case import PlazoFatal

class CalendarService:
    @staticmethod
    def generate_ical(plazos: List[PlazoFatal], calendar_name: str = "LexIntellectus Deadlines") -> str:
        """
        Generates an iCalendar (RFC 5545) compliant string from a list of PlazoFatal.
        """
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//LexIntellectus//ERP Calendar//ES",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            f"X-WR-CALNAME:{calendar_name}",
            "X-WR-TIMEZONE:America/Managua",
        ]

        now_str = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

        for plazo in plazos:
            # Generate UID based on deadline id or random if not present
            plazo_uid = f"plazo-{plazo.id or uuid.uuid4()}@lexintellectus.com"
            
            # Date/Time formatting
            venc_date = plazo.fecha_vencimiento
            if not venc_date:
                continue
                
            # If venc_date is a datetime, cast or extract date
            if isinstance(venc_date, datetime):
                venc_date = venc_date.date()

            # Construct DTSTART and DTEND
            # Deadlines are usually all-day events or expire at a specific time
            time_str = plazo.hora_vencimiento or "23:59:59"
            # Extract just HHMMSS
            time_parts = [p.zfill(2) for p in time_str.split(":")[:3]]
            while len(time_parts) < 3:
                time_parts.append("00")
            time_str_clean = "".join(time_parts)[:6]
            
            # Let's format as a specific date-time
            dt_str = f"{venc_date.strftime('%Y%m%d')}T{time_str_clean}"
            
            # Priority mapping
            # RFC 5545: 1 (highest), 5 (medium), 9 (lowest)
            priority_val = 5
            if plazo.prioridad == 'critica':
                priority_val = 1
            elif plazo.prioridad == 'alta':
                priority_val = 3
            elif plazo.prioridad == 'normal':
                priority_val = 5

            # Summary
            case_info = f" [{plazo.expediente.numero_causa or 'Expediente sin causa'}]" if plazo.expediente else ""
            summary = f"Plazo Fatal: {plazo.descripcion}{case_info}"
            
            # Clean text for iCal (escape backslashes, commas, semicolons)
            summary_escaped = summary.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;")
            desc_escaped = (plazo.base_legal or "Sin base legal").replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;")
            
            lines.extend([
                "BEGIN:VEVENT",
                f"UID:{plazo_uid}",
                f"DTSTAMP:{now_str}",
                f"DTSTART:{dt_str}",
                f"DTEND:{dt_str}",
                f"SUMMARY:{summary_escaped}",
                f"DESCRIPTION:Base Legal: {desc_escaped}\\nPrioridad: {plazo.prioridad}\\nEstado: {plazo.status}",
                f"PRIORITY:{priority_val}",
                "STATUS:CONFIRMED",
                "END:VEVENT"
            ])

        lines.append("END:VCALENDAR")
        # Ensure CRLF line endings as required by iCalendar RFC 5545
        return "\r\n".join(lines) + "\r\n"
