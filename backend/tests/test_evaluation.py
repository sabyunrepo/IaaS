"""Langfuse evaluation module tests."""
import pytest


class TestScoreConfigurations:
    """Test score configuration constants."""

    def test_score_configs_importable(self):
        """SCORE_CONFIGS is importable and has expected keys."""
        from app.core.evaluation import SCORE_CONFIGS
        assert isinstance(SCORE_CONFIGS, dict)
        assert "question_quality" in SCORE_CONFIGS
        assert "relevance" in SCORE_CONFIGS
        assert "difficulty_accuracy" in SCORE_CONFIGS
        assert "completion_status" in SCORE_CONFIGS
        assert "has_follow_ups" in SCORE_CONFIGS
        assert "has_terminology" in SCORE_CONFIGS

    def test_numeric_score_config_structure(self):
        """NUMERIC score configs have required fields."""
        from app.core.evaluation import SCORE_CONFIGS

        numeric_config = SCORE_CONFIGS["question_quality"]
        assert numeric_config["name"] == "question_quality"
        assert numeric_config["data_type"] == "NUMERIC"
        assert "min_value" in numeric_config
        assert "max_value" in numeric_config
        assert numeric_config["min_value"] == 0.0
        assert numeric_config["max_value"] == 1.0

    def test_categorical_score_config_structure(self):
        """CATEGORICAL score configs have required fields."""
        from app.core.evaluation import SCORE_CONFIGS

        categorical_config = SCORE_CONFIGS["difficulty_accuracy"]
        assert categorical_config["name"] == "difficulty_accuracy"
        assert categorical_config["data_type"] == "CATEGORICAL"
        assert "categories" in categorical_config
        assert isinstance(categorical_config["categories"], list)
        assert len(categorical_config["categories"]) > 0

    def test_boolean_score_config_structure(self):
        """BOOLEAN score configs have required fields."""
        from app.core.evaluation import SCORE_CONFIGS

        boolean_config = SCORE_CONFIGS["has_follow_ups"]
        assert boolean_config["name"] == "has_follow_ups"
        assert boolean_config["data_type"] == "BOOLEAN"

    def test_get_score_config_returns_config(self):
        """get_score_config returns correct config."""
        from app.core.evaluation import get_score_config

        config = get_score_config("question_quality")
        assert config is not None
        assert config["name"] == "question_quality"

    def test_get_score_config_returns_none_for_unknown(self):
        """get_score_config returns None for unknown score names."""
        from app.core.evaluation import get_score_config

        config = get_score_config("nonexistent_score")
        assert config is None

    def test_list_score_configs(self):
        """list_score_configs returns all score names."""
        from app.core.evaluation import list_score_configs

        names = list_score_configs()
        assert isinstance(names, list)
        assert "question_quality" in names
        assert "relevance" in names
        assert len(names) >= 6


class TestScoreCreation:
    """Test score creation functions."""

    def test_create_score_importable(self):
        """create_score function is importable."""
        from app.core.evaluation import create_score
        assert callable(create_score)

    def test_create_scores_batch_importable(self):
        """create_scores_batch function is importable."""
        from app.core.evaluation import create_scores_batch
        assert callable(create_scores_batch)

    def test_create_score_returns_none_when_disabled(self, monkeypatch):
        """create_score returns None when Langfuse is disabled."""
        monkeypatch.setattr(
            "app.core.observability.settings.LANGFUSE_PUBLIC_KEY", None
        )
        monkeypatch.setattr(
            "app.core.observability.settings.LANGFUSE_SECRET_KEY", None
        )

        from app.core.evaluation import create_score

        result = create_score("trace-123", "question_quality", 0.8)
        assert result is None

    def test_create_scores_batch_returns_empty_when_disabled(self, monkeypatch):
        """create_scores_batch returns empty list when Langfuse is disabled."""
        monkeypatch.setattr(
            "app.core.observability.settings.LANGFUSE_PUBLIC_KEY", None
        )
        monkeypatch.setattr(
            "app.core.observability.settings.LANGFUSE_SECRET_KEY", None
        )

        from app.core.evaluation import create_scores_batch

        scores = [
            {"name": "question_quality", "value": 0.8},
            {"name": "relevance", "value": 0.9},
        ]
        result = create_scores_batch("trace-123", scores)
        assert result == []


class TestDatasetManagement:
    """Test dataset management functions."""

    def test_create_dataset_importable(self):
        """create_dataset function is importable."""
        from app.core.evaluation import create_dataset
        assert callable(create_dataset)

    def test_add_dataset_item_importable(self):
        """add_dataset_item function is importable."""
        from app.core.evaluation import add_dataset_item
        assert callable(add_dataset_item)

    def test_get_dataset_importable(self):
        """get_dataset function is importable."""
        from app.core.evaluation import get_dataset
        assert callable(get_dataset)

    def test_create_dataset_returns_none_when_disabled(self, monkeypatch):
        """create_dataset returns None when Langfuse is disabled."""
        monkeypatch.setattr(
            "app.core.observability.settings.LANGFUSE_PUBLIC_KEY", None
        )
        monkeypatch.setattr(
            "app.core.observability.settings.LANGFUSE_SECRET_KEY", None
        )

        from app.core.evaluation import create_dataset

        result = create_dataset("test-dataset", "Test description")
        assert result is None

    def test_add_dataset_item_returns_none_when_disabled(self, monkeypatch):
        """add_dataset_item returns None when Langfuse is disabled."""
        monkeypatch.setattr(
            "app.core.observability.settings.LANGFUSE_PUBLIC_KEY", None
        )
        monkeypatch.setattr(
            "app.core.observability.settings.LANGFUSE_SECRET_KEY", None
        )

        from app.core.evaluation import add_dataset_item

        result = add_dataset_item(
            "test-dataset",
            {"input": "test"},
            {"output": "expected"},
        )
        assert result is None

    def test_get_dataset_returns_none_when_disabled(self, monkeypatch):
        """get_dataset returns None when Langfuse is disabled."""
        monkeypatch.setattr(
            "app.core.observability.settings.LANGFUSE_PUBLIC_KEY", None
        )
        monkeypatch.setattr(
            "app.core.observability.settings.LANGFUSE_SECRET_KEY", None
        )

        from app.core.evaluation import get_dataset

        result = get_dataset("test-dataset")
        assert result is None


class TestInterviewEvaluationTemplates:
    """Test interview-specific evaluation templates."""

    def test_create_interview_evaluation_dataset_importable(self):
        """create_interview_evaluation_dataset function is importable."""
        from app.core.evaluation import create_interview_evaluation_dataset
        assert callable(create_interview_evaluation_dataset)

    def test_add_interview_test_case_importable(self):
        """add_interview_test_case function is importable."""
        from app.core.evaluation import add_interview_test_case
        assert callable(add_interview_test_case)

    def test_create_interview_evaluation_dataset_returns_none_when_disabled(self, monkeypatch):
        """create_interview_evaluation_dataset returns None when disabled."""
        monkeypatch.setattr(
            "app.core.observability.settings.LANGFUSE_PUBLIC_KEY", None
        )
        monkeypatch.setattr(
            "app.core.observability.settings.LANGFUSE_SECRET_KEY", None
        )

        from app.core.evaluation import create_interview_evaluation_dataset

        result = create_interview_evaluation_dataset()
        assert result is None

    def test_add_interview_test_case_returns_none_when_disabled(self, monkeypatch):
        """add_interview_test_case returns None when disabled."""
        monkeypatch.setattr(
            "app.core.observability.settings.LANGFUSE_PUBLIC_KEY", None
        )
        monkeypatch.setattr(
            "app.core.observability.settings.LANGFUSE_SECRET_KEY", None
        )

        from app.core.evaluation import add_interview_test_case

        result = add_interview_test_case(
            "test-dataset",
            jd_text="Software Engineer position...",
            experience_level="Senior",
        )
        assert result is None


class TestMetricsQueries:
    """Test metrics query functions."""

    def test_get_trace_metrics_importable(self):
        """get_trace_metrics function is importable."""
        from app.core.evaluation import get_trace_metrics
        assert callable(get_trace_metrics)

    def test_get_session_metrics_importable(self):
        """get_session_metrics function is importable."""
        from app.core.evaluation import get_session_metrics
        assert callable(get_session_metrics)

    def test_get_trace_metrics_returns_none_when_disabled(self, monkeypatch):
        """get_trace_metrics returns None when Langfuse is disabled."""
        monkeypatch.setattr(
            "app.core.observability.settings.LANGFUSE_PUBLIC_KEY", None
        )
        monkeypatch.setattr(
            "app.core.observability.settings.LANGFUSE_SECRET_KEY", None
        )

        from app.core.evaluation import get_trace_metrics

        result = get_trace_metrics("trace-123")
        assert result is None

    def test_get_session_metrics_returns_none_when_disabled(self, monkeypatch):
        """get_session_metrics returns None when Langfuse is disabled."""
        monkeypatch.setattr(
            "app.core.observability.settings.LANGFUSE_PUBLIC_KEY", None
        )
        monkeypatch.setattr(
            "app.core.observability.settings.LANGFUSE_SECRET_KEY", None
        )

        from app.core.evaluation import get_session_metrics

        result = get_session_metrics("session-123")
        assert result is None


class TestPhase4AgentGraphFunctions:
    """Test Phase 4 Agent Graph visualization functions."""

    def test_create_agent_observation_importable(self):
        """create_agent_observation function is importable."""
        from app.core.observability import create_agent_observation
        assert callable(create_agent_observation)

    def test_create_tool_observation_importable(self):
        """create_tool_observation function is importable."""
        from app.core.observability import create_tool_observation
        assert callable(create_tool_observation)

    def test_create_retrieval_observation_importable(self):
        """create_retrieval_observation function is importable."""
        from app.core.observability import create_retrieval_observation
        assert callable(create_retrieval_observation)

    def test_end_observation_importable(self):
        """end_observation function is importable."""
        from app.core.observability import end_observation
        assert callable(end_observation)

    def test_create_agent_observation_returns_none_when_disabled(self, monkeypatch):
        """create_agent_observation returns None when Langfuse is disabled."""
        monkeypatch.setattr(
            "app.core.observability.settings.LANGFUSE_PUBLIC_KEY", None
        )
        monkeypatch.setattr(
            "app.core.observability.settings.LANGFUSE_SECRET_KEY", None
        )

        from app.core.observability import create_agent_observation

        result = create_agent_observation(
            trace_id="trace-123",
            name="test-agent",
            input_data={"query": "test"},
        )
        assert result is None

    def test_create_tool_observation_returns_none_when_disabled(self, monkeypatch):
        """create_tool_observation returns None when Langfuse is disabled."""
        monkeypatch.setattr(
            "app.core.observability.settings.LANGFUSE_PUBLIC_KEY", None
        )
        monkeypatch.setattr(
            "app.core.observability.settings.LANGFUSE_SECRET_KEY", None
        )

        from app.core.observability import create_tool_observation

        result = create_tool_observation(
            trace_id="trace-123",
            name="test-tool",
            input_data={"param": "value"},
        )
        assert result is None

    def test_create_retrieval_observation_returns_none_when_disabled(self, monkeypatch):
        """create_retrieval_observation returns None when Langfuse is disabled."""
        monkeypatch.setattr(
            "app.core.observability.settings.LANGFUSE_PUBLIC_KEY", None
        )
        monkeypatch.setattr(
            "app.core.observability.settings.LANGFUSE_SECRET_KEY", None
        )

        from app.core.observability import create_retrieval_observation

        result = create_retrieval_observation(
            trace_id="trace-123",
            name="test-retrieval",
            query="search query",
            documents=[{"content": "doc1"}],
        )
        assert result is None

    def test_end_observation_handles_none(self):
        """end_observation handles None observation gracefully."""
        from app.core.observability import end_observation

        # Should not raise
        end_observation(None)

    def test_end_observation_handles_none_with_output(self):
        """end_observation handles None observation with output data."""
        from app.core.observability import end_observation

        # Should not raise
        end_observation(None, output_data={"result": "test"}, status="success")
