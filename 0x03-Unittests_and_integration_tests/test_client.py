#!/usr/bin/env python3
"""
Unit and integration tests for client.py
"""

import unittest
from unittest.mock import patch, PropertyMock
from parameterized import parameterized, parameterized_class
from client import GithubOrgClient
from fixtures import TEST_PAYLOAD
import requests


class TestGithubOrgClient(unittest.TestCase):
    """Tests for GithubOrgClient class"""

    @parameterized.expand([
        ("google",),
        ("abc",)
    ])
    @patch('client.get_json')
    def test_org(self, org_name, mock_get_json):
        """Test org method returns correct data"""
        mock_get_json.return_value = {
            "login": org_name
        }
        client = GithubOrgClient(org_name)
        self.assertEqual(
            client.org,
            {"login": org_name}
        )
        url = f"https://api.github.com/orgs/{org_name}"
        mock_get_json.assert_called_once_with(url)

    @patch('client.GithubOrgClient.org', new_callable=PropertyMock)
    def test_public_repos_url(self, mock_org):
        """Test _public_repos_url returns expected value"""
        mock_org.return_value = {
            "repos_url": "https://api.github.com/orgs/test/repos"
        }
        client = GithubOrgClient("test")
        self.assertEqual(
            client._public_repos_url,
            "https://api.github.com/orgs/test/repos"
        )

    @patch('client.get_json')
    @patch('client.GithubOrgClient._public_repos_url',
           new_callable=PropertyMock)
    def test_public_repos(self, mock_repos_url, mock_get_json):
        """Test public_repos returns expected list"""
        mock_repos_url.return_value = (
            "https://api.github.com/orgs/test/repos")
        mock_get_json.return_value = [
            {"name": "repo1"},
            {"name": "repo2"},
            {"name": "repo3"},
        ]
        client = GithubOrgClient("test")
        repos = client.public_repos()
        self.assertEqual(
            repos,
            [
                "repo1",
                "repo2",
                "repo3",
            ]
        )
        mock_repos_url.assert_called_once()
        mock_get_json.assert_called_once()

    @parameterized.expand([
        ({"license": {"key": "my_license"}}, "my_license", True),
        ({"license": {"key": "other_license"}}, "my_license", False),
    ])
    def test_has_license(self, repo, license_key, expected):
        """Test has_license returns correct boolean"""
        client = GithubOrgClient("test")
        self.assertEqual(
            client.has_license(repo, license_key),
            expected
        )


@parameterized_class(
    ('org_payload', 'repos_payload', 'expected_repos', 'apache2_repos'),
    TEST_PAYLOAD
)
class TestIntegrationGithubOrgClient(unittest.TestCase):
    """Integration tests for GithubOrgClient"""

    @classmethod
    def setUpClass(cls):
        """Set up mock for requests.get"""
        cls.get_patcher = patch('requests.get')
        cls.mock_get = cls.get_patcher.start()

        ORG_URL = "/orgs/google"
        REPOS_URL = "/orgs/google/repos"

        def side_effect(url, *args, **kwargs):
            if url.endswith(ORG_URL):
                return MockResponse(cls.org_payload)
            elif url.endswith(REPOS_URL):
                return MockResponse(cls.repos_payload)
            return MockResponse(None)

        cls.mock_get.side_effect = side_effect

    @classmethod
    def tearDownClass(cls):
        """Stop patching"""
        cls.get_patcher.stop()

    def test_public_repos(self):
        """Test public_repos with integration setup"""
        client = GithubOrgClient("google")
        self.assertEqual(
            client.public_repos(),
            self.expected_repos
        )

    def test_public_repos_with_license(self):
        """Test public_repos filtering by license"""
        client = GithubOrgClient("google")
        self.assertEqual(
            client.public_repos(license="apache-2.0"),
            self.apache2_repos
        )


class MockResponse:
    """Mocked JSON response"""

    def __init__(self, json_data):
        self._json_data = json_data

    def json(self):
        """Return the mocked JSON data."""
        return self._json_data
    