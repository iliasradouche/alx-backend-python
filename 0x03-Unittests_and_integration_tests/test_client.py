#!/usr/bin/env python3
"""Unit tests for the GithubOrgClient class in client.py.
"""

import unittest
from unittest.mock import patch, PropertyMock
from parameterized import parameterized, parameterized_class
from client import GithubOrgClient
import fixtures


class TestGithubOrgClient(unittest.TestCase):
    """Test cases for the GithubOrgClient class."""

    @parameterized.expand([
        ("google", {"repos_url": "https://api.github.com/orgs/google/repos"}),
        ("abc", {"repos_url": "https://api.github.com/orgs/abc/repos"}),
    ])
    @patch("client.get_json")
    def test_org(self, org_name, expected_payload, mock_get_json):
        """
        Tests that GithubOrgClient.org returns the correct payload and that
        get_json is called once with the expected argument.
        """
        mock_get_json.return_value = expected_payload

        client = GithubOrgClient(org_name)
        result = client.org

        mock_get_json.assert_called_once_with(
            f"https://api.github.com/orgs/{org_name}"
        )
        self.assertEqual(result, expected_payload)

    def test_public_repos_url(self):
        """
        Tests that _public_repos_url returns the correct repos_url from
        the mocked org property.
        """
        with patch.object(
            GithubOrgClient,
            "org",
            new_callable=property
        ) as mock_org:
            mock_org.return_value = {
                "repos_url": "https://api.github.com/orgs/test/repos"
            }
            client = GithubOrgClient("test")
            result = client._public_repos_url
            self.assertEqual(
                result,
                "https://api.github.com/orgs/test/repos"
            )

    @patch("client.get_json")
    def test_public_repos(self, mock_get_json):
        """
        Tests that public_repos returns the expected list of repo names,
        that _public_repos_url and get_json are each called once.
        """
        test_payload = [
            {"name": "repo1"},
            {"name": "repo2"},
            {"name": "repo3"},
        ]
        mock_get_json.return_value = test_payload

        with patch.object(
            GithubOrgClient,
            "_public_repos_url",
            new_callable=PropertyMock
        ) as mock_repos_url:
            mock_repos_url.return_value = (
                "https://api.github.com/orgs/test/repos"
            )
            client = GithubOrgClient("test")
            result = client.public_repos()
            self.assertEqual(
                result,
                ["repo1", "repo2", "repo3"]
            )
            mock_get_json.assert_called_once_with(
                "https://api.github.com/orgs/test/repos"
            )
            mock_repos_url.assert_called_once()

    @parameterized.expand([
        ({"license": {"key": "my_license"}}, "my_license", True),
        ({"license": {"key": "other_license"}}, "my_license", False),
    ])
    def test_has_license(self, repo, license_key, expected):
        """
        Tests that has_license returns the expected value for different
        license keys.
        """
        result = GithubOrgClient.has_license(repo, license_key)
        self.assertEqual(result, expected)
        
    @parameterized_class([
    {
        "org_payload": fixtures.ORG_PAYLOAD,
        "repos_payload": fixtures.REPOS_PAYLOAD,
        "expected_repos": fixtures.EXPECTED_REPOS,
        "apache2_repos": fixtures.APACHE2_REPOS,
    }
])
    class TestIntegrationGithubOrgClient(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.get_patcher = patch("requests.get")
        cls.mock_get = cls.get_patcher.start()

        def get_json_side_effect(url):
            if url == GithubOrgClient.ORG_URL.format(org="google"):
                return MockResponse(cls.org_payload)
            elif url == cls.org_payload["repos_url"]:
                return MockResponse(cls.repos_payload)
            return MockResponse(None)

        cls.mock_get.side_effect = get_json_side_effect

    @classmethod
    def tearDownClass(cls):
        cls.get_patcher.stop()

class MockResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload
