"""
LexIntellectus - Cryptographic QR Verification & Automation Service
Generates tamper-proof HMAC-SHA256 signed verification tokens and SVG QR codes
for Executive Reports, Invoices, Electronic Signatures/Documents, and Legal Cases.
"""

import base64
import hashlib
import hmac
import io
import json
from datetime import datetime
from typing import Any, Dict, Optional
import qrcode
import qrcode.image.svg

from app.core.config import settings


class QRVerificationService:
    """
    Servicio de generación y validación criptográfica de Códigos QR
    para certificar reportes, facturas, documentos firmados y expedientes.
    """

    @staticmethod
    def _get_signing_key() -> bytes:
        secret = getattr(settings, "JWT_SECRET_KEY", "lexintellectus-qr-secret-key")
        return secret.encode("utf-8")

    @classmethod
    def create_signed_token(cls, payload: Dict[str, Any]) -> Dict[str, str]:
        """
        Empaqueta un payload JSON y lo firma con HMAC-SHA256, devolviendo:
        - `token`: cadena base64url (`payload_b64.signature_hex`)
        - `verification_code`: código corto legible (`LEX-XXXX-XXXX`)
        - `sha256_hash`: huella criptográfica completa SHA-256
        """
        canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        payload_b64 = base64.urlsafe_b64encode(canonical_json).decode("utf-8").rstrip("=")

        signature_hex = hmac.new(
            cls._get_signing_key(),
            payload_b64.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        full_hash = hashlib.sha256(canonical_json + signature_hex.encode("utf-8")).hexdigest()
        short_code = f"LEX-{full_hash[:4].upper()}-{full_hash[4:8].upper()}-{full_hash[8:12].upper()}"

        return {
            "token": f"{payload_b64}.{signature_hex}",
            "verification_code": short_code,
            "sha256_hash": full_hash,
            "signature": signature_hex,
        }

    @classmethod
    def verify_signed_token(cls, token: str) -> Optional[Dict[str, Any]]:
        """
        Verifica la firma HMAC-SHA256 de un token QR y retorna el payload original
        junto con su código de verificación y hash SHA-256, o None si fue alterado.
        """
        if not token or "." not in token:
            return None

        try:
            payload_b64, provided_sig = token.split(".", 1)
            expected_sig = hmac.new(
                cls._get_signing_key(),
                payload_b64.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()

            if not hmac.compare_digest(provided_sig, expected_sig):
                return None

            padding = "=" * (-len(payload_b64) % 4)
            canonical_json = base64.urlsafe_b64decode((payload_b64 + padding).encode("utf-8"))
            payload = json.loads(canonical_json.decode("utf-8"))

            full_hash = hashlib.sha256(canonical_json + expected_sig.encode("utf-8")).hexdigest()
            short_code = f"LEX-{full_hash[:4].upper()}-{full_hash[4:8].upper()}-{full_hash[8:12].upper()}"

            return {
                "valid": True,
                "verification_code": short_code,
                "sha256_hash": full_hash,
                "signature": expected_sig,
                "payload": payload,
            }
        except Exception:
            return None

    @staticmethod
    def generate_qr_svg_data_uri(data_url: str) -> str:
        """
        Genera una imagen SVG de código QR en formato `data:image/svg+xml;base64,...`
        lista para incrustar en el frontend, reportes impresos o PDFs sin requerir librerías nativas C.
        """
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=2,
        )
        qr.add_data(data_url)
        qr.make(fit=True)

        img = qr.make_image(image_factory=qrcode.image.svg.SvgPathImage)
        stream = io.BytesIO()
        img.save(stream)
        svg_bytes = stream.getvalue()
        b64_svg = base64.b64encode(svg_bytes).decode("utf-8")
        return f"data:image/svg+xml;base64,{b64_svg}"


qr_verification_service = QRVerificationService()
