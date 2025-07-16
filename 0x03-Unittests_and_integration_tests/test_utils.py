#!/usr/bin/env python3
"""Unit tests for the utility functions in utils.py.
This module tests access_nested_map for various input scenarios.
"""

import unittest
from parameterized import parameterized
from typing import Any, Dict, Tuple
from utils import access_nested_map


class TestAccessNestedMap(unittest.TestCase):
    """Test cases for the access_nested_map function."""

    @parameterized.expand([
        ({"a": 1}, ("a",), 1),
        ({"a": {"b": 2}}, ("a",), {"b": 2}),
        ({"a": {"b": 2}}, ("a", "b"), 2),
    ])
    def test_access_nested_map(
        self,
        nested_map: Dict[str, Any],
        path: Tuple[str, ...],
        expected: Any
    ) -> None:
        """
        Checks that access_nested_map returns expected output for various inputs.
        """
        self.assertEqual(
            access_nested_map(nested_map, path),
            expected
        )
