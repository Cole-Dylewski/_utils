"""
Tests for Django models utilities.
"""

import datetime as dt
import uuid

from models import django_models
import pytest


@pytest.mark.unit
class TestDjangoModelsUtils:
    """Test Django models utility functions."""

    def test_value_to_model_field_type(self):
        """Test converting value to Django model field type."""
        result = django_models.value_to_model_field_type("test_string")
        assert isinstance(result, str)

        result = django_models.value_to_model_field_type(123)
        assert isinstance(result, (str, int))

    def test_dict_to_model_field_type(self):
        """Test converting dictionary to Django model field types."""
        data = {
            "name": "Test",
            "age": 25,
            "active": True,
        }
        result = django_models.dict_to_model_field_type(data)
        assert isinstance(result, dict)

    def test_dict_to_model_class(self):
        """Test converting dictionary to Django model class."""
        data = {
            "name": "Test",
            "age": 25,
        }
        result = django_models.dict_to_model_class("TestModel", data)
        assert isinstance(result, str)
        assert "class TestModel" in result

    def test_format_model_dict(self):
        """Test formatting model dictionary."""
        data = {
            "name": "Test",
            "age": 25,
        }
        result = django_models.format_model_dict("TestModel", data)
        assert isinstance(result, dict)

    def test_django_model_field_desc(self):
        """Test Django model field descriptions."""
        assert "AutoField" in django_models.django_model_field_desc
        assert "CharField" in django_models.django_model_field_desc

    def test_django_model_field_types(self):
        """Test Django model field type mappings."""
        assert django_models.django_model_field_types["CharField"] is str
        assert django_models.django_model_field_types["IntegerField"] is int

    def test_python_to_django_model_field_types(self):
        """Test Python to Django model field type mappings."""
        assert str in django_models.python_to_django_model_field_types
        assert int in django_models.python_to_django_model_field_types
