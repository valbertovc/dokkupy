import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from dokkupy.core import Command, CommandError, Dokku, safe_log


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
