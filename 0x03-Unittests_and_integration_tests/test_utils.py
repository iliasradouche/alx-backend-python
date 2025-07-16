#!/usr/bin/env python3
"""Unit tests for the utility functions in utils.py.
This module tests access_nested_map and get_json for various input scenarios.
"""

import unittest
from unittest.mock import patch, Mock
from parameterized import parameterized
from typing import Any, Dict, Tuple
from utils import access_nested_map, get_json, memoize


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
        Checks that access_nested_map returns expected output
        for various inputs.
        """
        self.assertEqual(
            access_nested_map(nested_map, path),
            expected
        )

    @parameterized.expand([
        ({}, ("a",), "a"),
        ({"a": 1}, ("a", "b"), "b"),
    ])
    def test_access_nested_map_exception(
        self,
        nested_map: Dict[str, Any],
        path: Tuple[str, ...],
        expected_key: str
    ) -> None:
        """
        Verifies that access_nested_map raises KeyError with the correct message
        when an invalid path is provided.
        """
        with self.assertRaises(KeyError) as context:
            access_nested_map(nested_map, path)
        self.assertEqual(
            str(context.exception),
            f"'{expected_key}'"
        )


class TestGetJson(unittest.TestCase):
    """Test cases for the get_json function."""

    @parameterized.expand([
        ("http://example.com", {"payload": True}),
        ("http://holberton.io", {"payload": False}),
    ])
    def test_get_json(
        self,
        test_url: str,
        test_payload: Dict[str, Any]
    ) -> None:
        """
        Tests that get_json returns the expected payload and that requests.get
        is called exactly once with the correct URL.
        """
        with patch("utils.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = test_payload
            mock_get.return_value = mock_response

            result = get_json(test_url)
            mock_get.assert_called_once_with(
                test_url
            )
            self.assertEqual(
                result,
                test_payload
            )


class TestMemoize(unittest.TestCase):
    """Test cases for the memoize decorator."""

    def test_memoize(self) -> None:
        """
        Tests that memoize caches the result of a_property so that
        a_method is only called once.
        """

        class TestClass:
            def a_method(self):
                return 42

            @memoize
            def a_property(self):
                return self.a_method()

        with patch.object(TestClass, "a_method", return_value=42) as mock_method:
            obj = TestClass()
            result1 = obj.a_property
            result2 = obj.a_property
            self.assertEqual(
                result1,
                42
            )
            self.assertEqual(
                result2,
                42
            )
            mock_method.assert_called_once()
