import json
import os
import subprocess
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from dokkupy.core import Command, CommandError, Dokku, Registry, resolve_config_value, safe_log


class TestSafeLog(unittest.TestCase):
    def test_masks_sensitive_words(self):
        command = ['deploy', '--password=secret', 'key=value']
        self.assertEqual(
            safe_log(command),
            ['deploy', '******', '******'],
        )

    def test_leaves_safe_parts_unchanged(self):
        command = ['ssh', 'dokku@host.net', 'apps:list']
        self.assertEqual(safe_log(command), command)


class TestCommandGetCommand(unittest.TestCase):
    def test_builds_command_with_extra_params(self):
        command = Command('ssh', '-t', 'dokku@host.net')
        self.assertEqual(
            command.get_command('apps:list'),
            ['ssh', '-t', 'dokku@host.net', 'apps:list'],
        )


@patch('dokkupy.core.subprocess.Popen')
class TestCommandRun(unittest.TestCase):
    def test_returns_stdout_on_success(self, mock_popen):
        process = MagicMock()
        process.communicate.return_value = ('ok', '')
        process.returncode = 0
        mock_popen.return_value = process

        command = Command('echo')
        self.assertEqual(command.run('hello'), 'ok')

    def test_raises_command_error_on_failure(self, mock_popen):
        process = MagicMock()
        process.communicate.return_value = ('', 'failed')
        process.returncode = 1
        mock_popen.return_value = process

        command = Command('false')
        with self.assertRaises(CommandError):
            command.run()


class TestDokkuInitWithoutHostname(unittest.TestCase):
    def test_uses_local_dokku_command(self):
        dokku = Dokku()
        self.assertIsNone(dokku.hostname)
        self.assertEqual(
            dokku.get_command('apps:list'),
            ['dokku', 'apps:list'],
        )


class TestDokkuInitWithDefaultSshPort(unittest.TestCase):
    def test_sets_ssh_port_to_22(self):
        dokku = Dokku('dokku@host.net')
        self.assertEqual(dokku.ssh_port, 22)


class TestDokkuInitWithCustomSshPort(unittest.TestCase):
    def test_stores_custom_ssh_port(self):
        dokku = Dokku('dokku@host.net', ssh_port=2222)
        self.assertEqual(dokku.ssh_port, 2222)


class TestDokkuInitRejectsInvalidSshPort(unittest.TestCase):
    def test_rejects_port_below_range(self):
        with self.assertRaises(ValueError):
            Dokku('dokku@host.net', ssh_port=0)

    def test_rejects_port_above_range(self):
        with self.assertRaises(ValueError):
            Dokku('dokku@host.net', ssh_port=70000)


class TestDokkuGetCommand(unittest.TestCase):
    def test_uses_standard_ssh_command_for_default_port(self):
        dokku = Dokku('dokku@host.net')
        self.assertEqual(
            dokku.get_command('apps:list'),
            ['ssh', '-t', '-t', 'dokku@host.net', 'apps:list'],
        )

    def test_adds_p_flag_for_custom_port(self):
        dokku = Dokku('dokku@host.net', ssh_port=2222)
        self.assertEqual(
            dokku.get_command('apps:list'),
            ['ssh', '-t', '-t', '-p', '2222', 'dokku@host.net', 'apps:list'],
        )


class TestDokkuGitRemoteUrl(unittest.TestCase):
    def test_uses_scp_style_url_for_default_port(self):
        dokku = Dokku('dokku@host.net')
        self.assertEqual(dokku.git_remote_url('myapp'), 'dokku@host.net:myapp')

    def test_uses_ssh_url_for_custom_port(self):
        dokku = Dokku('dokku@host.net', ssh_port=2222)
        self.assertEqual(
            dokku.git_remote_url('myapp'),
            'ssh://dokku@host.net:2222/myapp',
        )


class TestDokkuHostnameOnly(unittest.TestCase):
    def test_strips_user_from_hostname(self):
        dokku = Dokku('dokku@host.net')
        self.assertEqual(dokku.hostname_only, 'host.net')

    def test_returns_hostname_when_user_is_absent(self):
        dokku = Dokku('host.net')
        self.assertEqual(dokku.hostname_only, 'host.net')


class TestDokkuLoadJson(unittest.TestCase):
    def test_reads_json_from_file(self):
        dokku = Dokku('dokku@host.net')
        config = {'scale': {'web': 1}}

        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as handle:
            json.dump(config, handle)
            filename = handle.name

        self.addCleanup(os.remove, filename)
        self.assertEqual(dokku._load_json(filename), config)


@patch('dokkupy.core.subprocess.Popen')
class TestDokkuRun(unittest.TestCase):
    def test_invokes_ssh_with_dokku_subcommand(self, mock_popen):
        process = MagicMock()
        process.communicate.return_value = ('====> myapp\n', '')
        process.returncode = 0
        mock_popen.return_value = process

        dokku = Dokku('dokku@host.net', ssh_port=2222)
        output = dokku.run('apps:list')

        mock_popen.assert_called_once()
        invoked_cmd = mock_popen.call_args[0][0]
        self.assertEqual(
            invoked_cmd,
            ['ssh', '-t', '-t', '-p', '2222', 'dokku@host.net', 'apps:list'],
        )
        self.assertEqual(output, '====> myapp\n')


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
class TestDokkuApplyRegistryConfig(unittest.TestCase):
    def test_applies_login_and_set_from_config(self, mock_run):
        dokku = Dokku('dokku@host.net')
        dokku._apply_registry_config({
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
            dokku._apply_registry_config({
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
