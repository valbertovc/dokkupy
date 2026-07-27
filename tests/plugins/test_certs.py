import subprocess
import unittest
from unittest.mock import MagicMock, patch

from dokkupy.core import App, Dokku
from dokkupy.plugins.certs import Certs


@patch('dokkupy.core.subprocess.Popen')
class TestCertsAdd(unittest.TestCase):
    def test_adds_cert_and_key(self, mock_popen):
        process = MagicMock()
        process.communicate.return_value = ('', '')
        process.returncode = 0
        mock_popen.return_value = process

        dokku = Dokku('dokku@host.net')
        app = App('myapp', dokku)
        app.certs.add('/path/server.crt', '/path/server.key')

        invoked_cmd = mock_popen.call_args[0][0]
        self.assertEqual(
            invoked_cmd[-4:],
            ['certs:add', 'myapp', '/path/server.crt', '/path/server.key'],
        )

    def test_adds_cert_with_ca_chain(self, mock_popen):
        process = MagicMock()
        process.communicate.return_value = ('', '')
        process.returncode = 0
        mock_popen.return_value = process

        dokku = Dokku('dokku@host.net')
        app = App('myapp', dokku)
        app.certs.add(
            '/path/server.crt', '/path/server.key', ca_chain='/path/ca-chain.crt',
        )

        invoked_cmd = mock_popen.call_args[0][0]
        self.assertEqual(
            invoked_cmd[-5:],
            [
                'certs:add', 'myapp', '/path/server.crt',
                '/path/server.key', '/path/ca-chain.crt',
            ],
        )


@patch('dokkupy.core.subprocess.Popen')
class TestCertsGenerate(unittest.TestCase):
    def test_generates_self_signed_cert(self, mock_popen):
        process = MagicMock()
        process.communicate.return_value = ('', '')
        process.returncode = 0
        mock_popen.return_value = process

        dokku = Dokku('dokku@host.net')
        app = App('myapp', dokku)
        app.certs.generate(
            'BR', 'PB', 'City', 'Company', 'Section',
            'email@example.com', 'password', 'OptCo',
        )

        invoked_cmd = mock_popen.call_args[0][0]
        self.assertEqual(
            invoked_cmd[-3:],
            ['certs:generate', 'myapp', 'myapp.host.net'],
        )
        mock_popen.assert_called_once()
        self.assertEqual(mock_popen.call_args[1]['stdin'], subprocess.PIPE)


@patch('dokkupy.core.subprocess.Popen')
class TestCertsRemove(unittest.TestCase):
    def test_removes_cert(self, mock_popen):
        process = MagicMock()
        process.communicate.return_value = ('', '')
        process.returncode = 0
        mock_popen.return_value = process

        dokku = Dokku('dokku@host.net')
        app = App('myapp', dokku)
        app.certs.remove()

        invoked_cmd = mock_popen.call_args[0][0]
        self.assertEqual(invoked_cmd[-2:], ['certs:remove', 'myapp'])


@patch('dokkupy.core.subprocess.Popen')
class TestCertsHasCert(unittest.TestCase):
    def test_returns_true_when_ssl_enabled(self, mock_popen):
        process = MagicMock()
        process.communicate.return_value = (
            'Ssl enabled:         true\n', '',
        )
        process.returncode = 0
        mock_popen.return_value = process

        dokku = Dokku('dokku@host.net')
        app = App('myapp', dokku)
        self.assertTrue(app.certs.has_cert)


@patch.object(Certs, 'add')
@patch.object(Certs, 'generate')
class TestCertsApplyConfig(unittest.TestCase):
    def test_applies_add_and_generate_from_config(self, mock_generate, mock_add):
        dokku = Dokku('dokku@host.net')
        app = App('myapp', dokku)
        app.certs.apply_config({
            'add': {
                'crt': '/path/server.crt',
                'key': '/path/server.key',
            },
            'generate': {
                'country': 'BR',
                'state': 'PB',
                'city': 'City',
                'company': 'Company',
                'section': 'Section',
                'email': 'email@example.com',
                'password': 'password',
                'opt_company': 'OptCo',
            },
        })

        mock_add.assert_called_once_with(
            '/path/server.crt', '/path/server.key', ca_chain=None,
        )
        mock_generate.assert_called_once_with(
            country='BR',
            state='PB',
            city='City',
            company='Company',
            section='Section',
            email='email@example.com',
            password='password',
            opt_company='OptCo',
        )


@patch.object(App, 'deploy')
@patch.object(Certs, 'apply_config')
@patch.object(Certs, 'generate')
class TestDeployCertsConfig(unittest.TestCase):
    def test_uses_certs_config_when_present(
        self, mock_generate, mock_apply, mock_deploy,
    ):
        dokku = Dokku('dokku@host.net')
        with patch.object(dokku, '_list', return_value=['myapp']):
            dokku.deploy('myapp', {
                'certs': {
                    'add': {
                        'crt': '/path/server.crt',
                        'key': '/path/server.key',
                    },
                },
            }, destroy=False)

        mock_apply.assert_called_once()
        mock_generate.assert_not_called()

    def test_falls_back_to_legacy_generate_cert(
        self, mock_generate, mock_apply, mock_deploy,
    ):
        dokku = Dokku('dokku@host.net')
        with patch.object(dokku, '_list', return_value=['myapp']):
            dokku.deploy('myapp', {
                'generate_cert': True,
                'cert': {
                    'country': 'BR',
                    'state': 'PB',
                    'city': 'City',
                    'company': 'Company',
                    'section': 'Section',
                    'email': 'email@example.com',
                    'password': 'password',
                    'opt_company': 'OptCo',
                },
            }, destroy=False)

        mock_apply.assert_not_called()
        mock_generate.assert_called_once()
