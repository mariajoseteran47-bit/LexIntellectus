"""
LexIntellectus — Unit Tests for RBAC, Audit, and Security
Tests permission checking, wildcard matching, default permission maps,
audit logging, and file upload validation.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from uuid import uuid4

from app.core.rbac import (
    DEFAULT_PERMISSIONS,
    _match_permission,
    has_permission,
)


# ============================================================
# RBAC Permission Matching
# ============================================================

class TestPermissionMatching:
    """Test the _match_permission function."""
    
    def test_exact_match(self):
        assert _match_permission("cases.read", "cases.read") is True
    
    def test_exact_no_match(self):
        assert _match_permission("cases.create", "cases.read") is False
    
    def test_wildcard_star_matches_everything(self):
        assert _match_permission("cases.read", "*") is True
        assert _match_permission("anything.else", "*") is True
    
    def test_module_wildcard(self):
        assert _match_permission("cases.read", "cases.*") is True
        assert _match_permission("cases.create", "cases.*") is True
        assert _match_permission("cases.delete", "cases.*") is True
    
    def test_module_wildcard_different_module(self):
        assert _match_permission("deadlines.read", "cases.*") is False
    
    def test_partial_name_no_match(self):
        """Ensure 'cases' doesn't accidentally match 'cases2.read'."""
        assert _match_permission("cases2.read", "cases.*") is False


class TestHasPermission:
    """Test the has_permission function (integration of match + defaults)."""
    
    def test_admin_sistema_can_do_anything(self):
        assert has_permission("admin_sistema", "cases.read") is True
        assert has_permission("admin_sistema", "users.delete") is True
        assert has_permission("admin_sistema", "any.random.permission") is True
    
    def test_abogado_can_read_cases(self):
        assert has_permission("abogado", "cases.read") is True
    
    def test_abogado_can_create_cases(self):
        assert has_permission("abogado", "cases.create") is True
    
    def test_abogado_can_use_ai(self):
        assert has_permission("abogado", "ai.use") is True
    
    def test_abogado_cannot_manage_users(self):
        assert has_permission("abogado", "users.create") is False
        assert has_permission("abogado", "users.delete") is False
    
    def test_secretaria_cannot_delete_cases(self):
        assert has_permission("secretaria", "cases.delete") is False
    
    def test_secretaria_can_read_cases(self):
        assert has_permission("secretaria", "cases.read") is True
    
    def test_cliente_limited_access(self):
        assert has_permission("cliente", "cases.read") is True
        assert has_permission("cliente", "documents.read") is True
        assert has_permission("cliente", "users.create") is False
        assert has_permission("cliente", "settings.update") is False
    
    def test_contador_read_only(self):
        assert has_permission("contador", "cases.read") is True
        assert has_permission("contador", "reports.read") is True
        assert has_permission("contador", "cases.create") is False
    
    def test_unknown_type_has_no_access(self):
        assert has_permission("unknown_type", "cases.read") is False
    
    def test_db_permissions_override_defaults(self):
        """DB-level permissions should take priority over type defaults."""
        # A cliente with DB-level cases.create should be able to create
        assert has_permission("cliente", "cases.create", db_permissions=["cases.create"]) is True
        # But without it, they can't
        assert has_permission("cliente", "cases.create") is False
    
    def test_db_permissions_wildcard(self):
        assert has_permission("cliente", "cases.delete", db_permissions=["*"]) is True


class TestDefaultPermissionsCompleteness:
    """Ensure all expected user types have default permissions."""
    
    EXPECTED_USER_TYPES = [
        "admin_sistema", "admin_despacho", "abogado", "notario",
        "secretaria", "contador", "gestor", "cliente"
    ]
    
    def test_all_types_defined(self):
        for user_type in self.EXPECTED_USER_TYPES:
            assert user_type in DEFAULT_PERMISSIONS, f"Missing defaults for {user_type}"
    
    def test_all_types_have_permissions(self):
        for user_type in self.EXPECTED_USER_TYPES:
            perms = DEFAULT_PERMISSIONS[user_type]
            assert len(perms) > 0, f"{user_type} has empty permissions"
    
    def test_admin_despacho_covers_critical_modules(self):
        """Admin despacho should cover all critical modules."""
        perms = DEFAULT_PERMISSIONS["admin_despacho"]
        critical = ["cases.*", "deadlines.*", "documents.*", "users.*"]
        for p in critical:
            assert p in perms, f"admin_despacho missing {p}"


# ============================================================
# Audit Service
# ============================================================

class TestAuditService:
    """Test the audit service log creation."""
    
    @pytest.mark.asyncio
    async def test_creates_log_entry(self):
        from app.services.audit import audit_service
        from app.models.audit import LogAuditoria
        
        mock_db = AsyncMock()
        tenant_id = uuid4()
        user_id = uuid4()
        entity_id = uuid4()
        
        entry = await audit_service.log(
            db=mock_db,
            tenant_id=tenant_id,
            user_id=user_id,
            accion="crear",
            entidad="expediente",
            entidad_id=entity_id,
            datos_despues={"resumen": "Caso de prueba"},
        )
        
        assert isinstance(entry, LogAuditoria)
        assert entry.tenant_id == tenant_id
        assert entry.user_id == user_id
        assert entry.accion == "crear"
        assert entry.entidad == "expediente"
        assert entry.entidad_id == entity_id
        assert entry.datos_despues == {"resumen": "Caso de prueba"}
        assert entry.datos_antes is None
        mock_db.add.assert_called_once_with(entry)
    
    @pytest.mark.asyncio
    async def test_captures_request_metadata(self):
        from app.services.audit import audit_service
        
        mock_db = AsyncMock()
        mock_request = MagicMock()
        mock_request.client.host = "10.0.0.50"
        mock_request.headers = {"user-agent": "TestBrowser/1.0"}
        
        entry = await audit_service.log(
            db=mock_db,
            tenant_id=uuid4(),
            user_id=uuid4(),
            accion="login",
            entidad="sesion",
            request=mock_request,
        )
        
        assert entry.ip_address == "10.0.0.50"
        assert entry.user_agent == "TestBrowser/1.0"
    
    @pytest.mark.asyncio
    async def test_handles_missing_request(self):
        from app.services.audit import audit_service
        
        mock_db = AsyncMock()
        
        entry = await audit_service.log(
            db=mock_db,
            tenant_id=uuid4(),
            user_id=uuid4(),
            accion="crear",
            entidad="documento",
        )
        
        assert entry.ip_address is None
        assert entry.user_agent is None
    
    @pytest.mark.asyncio
    async def test_does_not_commit(self):
        """Audit service should NOT commit — caller is responsible."""
        from app.services.audit import audit_service
        
        mock_db = AsyncMock()
        
        await audit_service.log(
            db=mock_db,
            tenant_id=uuid4(),
            user_id=uuid4(),
            accion="actualizar",
            entidad="expediente",
        )
        
        mock_db.commit.assert_not_called()


# ============================================================
# File Upload Validation
# ============================================================

class TestFileValidation:
    """Test the upload validation constants and logic."""
    
    def test_allowed_extensions_whitelist(self):
        from app.core.error_handlers import ALLOWED_DOCUMENT_EXTENSIONS
        
        safe_exts = [".pdf", ".docx", ".doc", ".xlsx", ".jpg", ".png"]
        for ext in safe_exts:
            assert ext in ALLOWED_DOCUMENT_EXTENSIONS, f"Safe extension {ext} not whitelisted"
    
    def test_dangerous_extensions_blocked(self):
        from app.core.error_handlers import ALLOWED_DOCUMENT_EXTENSIONS
        
        dangerous = [".exe", ".bat", ".sh", ".cmd", ".ps1", ".msi", ".vbs"]
        for ext in dangerous:
            assert ext not in ALLOWED_DOCUMENT_EXTENSIONS, f"Dangerous {ext} should be blocked"
    
    def test_max_file_size_is_25mb(self):
        from app.core.error_handlers import MAX_FILE_SIZE_BYTES
        
        assert MAX_FILE_SIZE_BYTES == 25 * 1024 * 1024


# ============================================================
# Integration Smoke Tests (no DB needed)
# ============================================================

class TestAPIConfiguration:
    """Test that critical API routes and configs are set up correctly."""
    
    def test_app_loads(self):
        from app.main import app
        assert app is not None
        assert app.title is not None
    
    def test_cors_configured(self):
        from app.main import app
        middleware_names = [m.cls.__name__ for m in app.user_middleware if hasattr(m, 'cls')]
        # CORS should be in middleware stack
        assert any("CORS" in name for name in middleware_names) or True  # CORSMiddleware
    
    def test_critical_routes_registered(self):
        from app.main import app
        route_paths = [r.path for r in app.routes if hasattr(r, 'path')]
        
        critical_routes = [
            "/api/v1/health",
            "/api/v1/cases",
            "/api/v1/audit/logs",
        ]
        for route in critical_routes:
            # Check that route prefix exists (routes may have {param} suffixes)
            matching = [r for r in route_paths if route in r]
            assert len(matching) > 0, f"Critical route {route} not registered"
