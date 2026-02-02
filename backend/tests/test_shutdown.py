"""Graceful shutdown lifecycle tests."""
import pytest


class TestLifespan:
    def test_lifespan_defined(self):
        from app.main import lifespan
        assert callable(lifespan)

    def test_app_has_lifespan(self):
        from app.main import app
        assert app.router.lifespan_context is not None

    def test_lifespan_is_async_context_manager(self):
        import inspect
        from app.main import lifespan
        assert inspect.isasyncgenfunction(lifespan.__wrapped__) or hasattr(lifespan, "__aenter__")


class TestShutdownTargets:
    def test_db_engine_has_dispose(self):
        from app.core.database import engine
        assert hasattr(engine, "dispose")

    def test_temporal_client_module_accessible(self):
        from app.core import temporal
        assert hasattr(temporal, "_client")

    def test_observability_called_in_lifespan(self):
        """setup_langfuse is called inside lifespan, not at module level."""
        import ast
        with open("app/main.py") as f:
            tree = ast.parse(f.read())
        # Find the lifespan function
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "lifespan":
                body_src = ast.dump(node)
                assert "setup_langfuse" in body_src
                break
        else:
            pytest.fail("lifespan function not found")
