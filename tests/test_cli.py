import json
import os
import tempfile
import unittest
from unittest.mock import patch


class TestMain(unittest.TestCase):
    @patch('dokkupy.cli.dokkupy.Dokku')
    def test_passes_ssh_port_to_dokku(self, mock_dokku):
        from dokkupy.cli import main

        config = {'scale': {'web': 1}}
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as handle:
            json.dump(config, handle)
            config_path = handle.name

        self.addCleanup(os.remove, config_path)

        with patch('sys.argv', [
            'dokkupycli',
            '--project-name', 'myapp',
            '--address', 'dokku@host.net',
            '--ssh-port', '2222',
            '--config', config_path,
            'deploy',
        ]):
            main()

        mock_dokku.assert_called_once_with('dokku@host.net', ssh_port=2222)
        mock_dokku.return_value.deploy_from_file.assert_called_once_with(
            'myapp',
            config_path,
            destroy=False,
        )
