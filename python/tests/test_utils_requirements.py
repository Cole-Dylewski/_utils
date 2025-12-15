"""
Tests for requirements utilities.
"""

import os
import tempfile

import pytest
from utils import requirements


@pytest.mark.unit
class TestRequirementsUtils:
    """Test requirements utility functions."""

    def test_merge_requirements(self, temp_dir):
        """Test merging requirements files."""
        target_file = os.path.join(temp_dir, "target.txt")
        source_file = os.path.join(temp_dir, "source.txt")

        # Create target file
        with open(target_file, "w") as f:
            f.write("pytest==7.4.0\n")
            f.write("requests==2.31.0\n")

        # Create source file
        with open(source_file, "w") as f:
            f.write("pytest==7.4.0\n")
            f.write("requests==2.31.0\n")
            f.write("click==8.1.0\n")  # New package

        requirements.merge_requirements(target_file, source_file)

        # Verify new package was added
        with open(target_file) as f:
            content = f.read()
            assert "click==8.1.0" in content or "click" in content
            assert "pytest==7.4.0" in content or "pytest" in content
