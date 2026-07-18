import os
import subprocess
import unittest
from unittest.mock import MagicMock, patch

from dokkupy.core import Dokku
from dokkupy.plugins.registry import resolve_config_value


class TestResolveConfigValue(unittest.TestCase):
    def test_returns_plain_string(self):
        self.assertEqual(resolve_config_value('hello'), 'hello')

    def test_resolves_env_dict(self):
        with patch.dict(os.environ, {'MY_VAR': 'secret'}):
            self.assertEqual(
                resolve_config_value({'env': 'MY_VAR'}),
                'secret',
            )


@patch('dokkupy.core.subprocess.Popen')
class TestRegistryLogin(unittest.TestCase):
    def test_global_login_with_password(self, mock_popen):
        process = MagicMock()
        process.communicate.return_value = ('', '')
        process.returncode = 0
        mock_popen.return_value = process

        dokku = Dokku('dokku@host.net')
        dokku.registry.login(
            'docker.io', 'user', 'pass', global_=True,
        )

        invoked_cmd = mock_popen.call_args[0][0]
        self.assertEqual(
            invoked_cmd,
            [
                'ssh', '-t', '-t', 'dokku@host.net',
                'registry:login', '--global', 'docker.io', 'user', 'pass',
            ],
        )

    def test_per_app_login(self, mock_popen):
        process = MagicMock()
        process.communicate.return_value = ('', '')
        process.returncode = 0
        mock_popen.return_value = process

        dokku = Dokku('dokku@host.net')
        dokku.registry.login(
            'registry.gitlab.com', 'token-user', 'token',
            app='myapp',
        )

        invoked_cmd = mock_popen.call_args[0][0]
        self.assertEqual(
            invoked_cmd[-5:],
            ['registry:login', 'myapp', 'registry.gitlab.com', 'token-user', 'token'],
        )

    def test_password_stdin(self, mock_popen):
        process = MagicMock()
        process.communicate.return_value = ('', '')
        process.returncode = 0
        mock_popen.return_value = process

        dokku = Dokku('dokku@host.net')
        dokku.registry.login(
            'docker.io', 'user', 'pass', global_=True, password_stdin=True,
        )

        invoked_cmd = mock_popen.call_args[0][0]
        self.assertIn('--password-stdin', invoked_cmd)
        self.assertNotIn('pass', invoked_cmd)
        mock_popen.assert_called_once()
        self.assertEqual(mock_popen.call_args[1]['stdin'], subprocess.PIPE)


@patch('dokkupy.core.subprocess.Popen')
class TestRegistrySet(unittest.TestCase):
    def test_sets_property_for_app(self, mock_popen):
        process = MagicMock()
        process.communicate.return_value = ('', '')
        process.returncode = 0
        mock_popen.return_value = process

        dokku = Dokku('dokku@host.net')
        dokku.registry.set('server', 'docker.io', app='myapp')

        invoked_cmd = mock_popen.call_args[0][0]
        self.assertEqual(
            invoked_cmd[-4:],
            ['registry:set', 'myapp', 'server', 'docker.io'],
        )

    def test_clears_property(self, mock_popen):
        process = MagicMock()
        process.communicate.return_value = ('', '')
        process.returncode = 0
        mock_popen.return_value = process

        dokku = Dokku('dokku@host.net')
        dokku.registry.set('server', app='myapp')

        invoked_cmd = mock_popen.call_args[0][0]
        self.assertEqual(
            invoked_cmd[-3:],
            ['registry:set', 'myapp', 'server'],
        )

    def test_sets_global_property(self, mock_popen):
        process = MagicMock()
        process.communicate.return_value = ('', '')
        process.returncode = 0
        mock_popen.return_value = process

        dokku = Dokku('dokku@host.net')
        dokku.registry.set('push-on-release', 'true', global_=True)

        invoked_cmd = mock_popen.call_args[0][0]
        self.assertEqual(
            invoked_cmd[-4:],
            ['registry:set', '--global', 'push-on-release', 'true'],
        )


@patch.object(Dokku, 'run')
class TestRegistryApplyConfig(unittest.TestCase):
    def test_applies_login_and_set_from_config(self, mock_run):
        dokku = Dokku('dokku@host.net')
        dokku.registry.apply_config({
            'login': {
                'global': True,
                'server': 'registry.gitlab.com',
                'username': 'user',
                'password': 'pass',
            },
            'set': {
                'server': 'registry.gitlab.com',
                'image-repo': 'group/project',
            },
        }, 'myapp')

        mock_run.assert_any_call(
            'registry:login', '--global', 'registry.gitlab.com', 'user', 'pass',
        )
        mock_run.assert_any_call(
            'registry:set', 'myapp', 'server', 'registry.gitlab.com',
        )
        mock_run.assert_any_call(
            'registry:set', 'myapp', 'image-repo', 'group/project',
        )

    def test_resolves_password_from_env(self, mock_run):
        dokku = Dokku('dokku@host.net')
        with patch.dict(os.environ, {'REGISTRY_PASSWORD': 'secret'}):
            dokku.registry.apply_config({
                'login': {
                    'global': True,
                    'server': 'docker.io',
                    'username': 'user',
                    'password': {'env': 'REGISTRY_PASSWORD'},
                },
            }, 'myapp')

        mock_run.assert_called_once_with(
            'registry:login', '--global', 'docker.io', 'user', 'secret',
        )
