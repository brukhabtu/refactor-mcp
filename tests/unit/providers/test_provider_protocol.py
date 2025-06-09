"""
Tests for enhanced RefactoringProvider protocol features.

This module tests the enhanced provider interface including metadata support,
capability reporting, health checks, versioning, and priority systems.
"""

import pytest

from refactor_mcp.models.params import AnalyzeParams
from tests.mocks.providers import MockRopeProvider


class TestProviderMetadata:
    """Test provider metadata capabilities"""

    def test_provider_has_metadata_method(self):
        """Provider should expose metadata information"""
        provider = MockRopeProvider()

        # Provider should have get_metadata method
        assert hasattr(provider, "get_metadata")
        metadata = provider.get_metadata()
        assert metadata is not None

    def test_provider_metadata_structure(self):
        """Provider metadata should have required fields"""
        provider = MockRopeProvider()

        # This will fail - get_metadata doesn't exist yet
        try:
            metadata = provider.get_metadata()

            # Check required metadata fields
            assert hasattr(metadata, "name")
            assert hasattr(metadata, "version")
            assert hasattr(metadata, "description")
            assert hasattr(metadata, "author")
            assert hasattr(metadata, "supported_languages")

            # Validate types
            assert isinstance(metadata.name, str)
            assert isinstance(metadata.version, str)
            assert isinstance(metadata.description, str)
            assert isinstance(metadata.author, str)
            assert isinstance(metadata.supported_languages, list)

        except AttributeError:
            pytest.fail("Provider should have get_metadata() method")


class TestCapabilityReporting:
    """Test enhanced capability reporting"""

    def test_get_detailed_capabilities(self):
        """Provider should report detailed capabilities per language"""
        provider = MockRopeProvider()

        # Provider should have get_detailed_capabilities method
        assert hasattr(provider, "get_detailed_capabilities")
        capabilities = provider.get_detailed_capabilities("python")
        assert capabilities is not None

    def test_capability_reporting_structure(self):
        """Capability reporting should have structured format"""
        provider = MockRopeProvider()

        try:
            capabilities = provider.get_detailed_capabilities("python")

            # Should be a dict with operation categories
            assert isinstance(capabilities, dict)
            assert "analysis" in capabilities
            assert "refactoring" in capabilities
            assert "discovery" in capabilities

            # Each category should list specific operations
            assert isinstance(capabilities["analysis"], list)
            assert isinstance(capabilities["refactoring"], list)
            assert isinstance(capabilities["discovery"], list)

        except AttributeError:
            pytest.fail("Provider should have get_detailed_capabilities() method")

    def test_operation_support_levels(self):
        """Operations should have support level indicators"""
        provider = MockRopeProvider()

        try:
            capabilities = provider.get_detailed_capabilities("python")

            # Each operation should have support level
            for category, operations in capabilities.items():
                for operation in operations:
                    assert hasattr(operation, "name")
                    assert hasattr(operation, "support_level")
                    assert operation.support_level in [
                        "full",
                        "partial",
                        "experimental",
                    ]

        except AttributeError:
            pytest.fail("Provider should report operation support levels")


class TestProviderHealthCheck:
    """Test provider health check and validation"""

    def test_provider_health_check(self):
        """Provider should have health check method"""
        provider = MockRopeProvider()

        # Provider should have health_check method
        assert hasattr(provider, "health_check")
        health = provider.health_check()
        assert health is not None

    def test_health_check_result_structure(self):
        """Health check should return structured result"""
        provider = MockRopeProvider()

        try:
            health = provider.health_check()

            assert hasattr(health, "status")
            assert hasattr(health, "details")
            assert hasattr(health, "dependencies")

            assert health.status in ["healthy", "degraded", "unhealthy"]
            assert isinstance(health.details, dict)
            assert isinstance(health.dependencies, list)

        except AttributeError:
            pytest.fail("Provider should have health_check() method")

    def test_validate_configuration(self):
        """Provider should validate its configuration"""
        provider = MockRopeProvider()

        # Provider should have validate_configuration method
        assert hasattr(provider, "validate_configuration")
        validation = provider.validate_configuration()
        assert validation is not None


class TestProviderPriority:
    """Test provider priority system"""

    def test_provider_has_priority(self):
        """Provider should expose priority for selection logic"""
        provider = MockRopeProvider()

        # Provider should have get_priority method
        assert hasattr(provider, "get_priority")
        priority = provider.get_priority("python")
        assert priority is not None

    def test_priority_calculation(self):
        """Priority should be calculated based on language and capabilities"""
        provider = MockRopeProvider()

        try:
            python_priority = provider.get_priority("python")
            javascript_priority = provider.get_priority("javascript")

            # Python should have higher priority for rope provider
            assert isinstance(python_priority, int)
            assert isinstance(javascript_priority, int)
            assert python_priority > javascript_priority

        except AttributeError:
            pytest.fail("Provider should have get_priority() method")


class TestProviderVersioning:
    """Test provider versioning and compatibility"""

    def test_provider_version_info(self):
        """Provider should expose version information"""
        provider = MockRopeProvider()

        try:
            metadata = provider.get_metadata()
            assert hasattr(metadata, "version")
            assert hasattr(metadata, "min_protocol_version")
            assert hasattr(metadata, "max_protocol_version")

        except AttributeError:
            pytest.fail("Provider should expose version information")

    def test_compatibility_check(self):
        """Provider should check protocol compatibility"""
        provider = MockRopeProvider()

        # Provider should have is_compatible method
        assert hasattr(provider, "is_compatible")
        compatible = provider.is_compatible("1.0.0")
        assert compatible is not None

    def test_compatibility_validation(self):
        """Compatibility check should validate protocol versions"""
        provider = MockRopeProvider()

        try:
            # Should be compatible with same version
            assert provider.is_compatible("1.0.0")

            # Should handle version comparisons
            result = provider.is_compatible("0.5.0")
            assert isinstance(result, bool)

        except AttributeError:
            pytest.fail("Provider should validate protocol compatibility")


class TestBackwardsCompatibility:
    """Test that existing protocol methods still work"""

    def test_existing_methods_still_work(self):
        """All existing protocol methods should remain functional"""
        provider = MockRopeProvider()

        # Test existing methods that should continue working
        assert provider.supports_language("python")
        assert not provider.supports_language("javascript")

        # get_capabilities should still work but might be enhanced
        capabilities = provider.get_capabilities("python")
        assert isinstance(capabilities, list)
        assert len(capabilities) > 0

    def test_analyze_symbol_still_works(self):
        """analyze_symbol should continue working as before"""
        provider = MockRopeProvider()
        params = AnalyzeParams(symbol_name="get_user_info", project_path="/test")

        result = provider.analyze_symbol(params)
        assert result.success
        assert result.symbol_info.name == "get_user_info"


class TestEnhancedProtocolIntegration:
    """Test that all enhanced features work together"""

    def test_complete_provider_interface(self):
        """Provider should implement complete enhanced interface"""
        provider = MockRopeProvider()

        # This comprehensive test will fail until all methods are implemented
        required_methods = [
            "get_metadata",
            "get_detailed_capabilities",
            "health_check",
            "validate_configuration",
            "get_priority",
            "is_compatible",
        ]

        for method_name in required_methods:
            assert hasattr(provider, method_name), (
                f"Provider missing {method_name} method"
            )

    def test_provider_registration_compatibility(self):
        """Enhanced providers should work with existing registry"""
        from refactor_mcp.providers.registry import RefactoringEngine

        engine = RefactoringEngine()
        provider = MockRopeProvider()

        # Enhanced providers should work with existing engine
        try:
            engine.register_provider(provider)
            retrieved = engine.get_provider("python")
            assert retrieved is provider
        except Exception as e:
            pytest.fail(f"Engine should handle enhanced providers: {e}")
