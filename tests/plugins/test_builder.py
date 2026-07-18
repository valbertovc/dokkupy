import unittest
from unittest.mock import MagicMock, patch

from dokkupy.core import App, Dokku


@patch('dokkupy.core.subprocess.Popen')
class TestBuilderSet(unittest.TestCase):
    def test_sets_property_for_app(self, mock_popen):
        process = MagicMock()
        process.communicate.return_value = ('', '')
        process.returncode = 0
        mock_popen.return_value = process

        dokku = Dokku('dokku@host.net')
        app = App('myapp', dokku)
        app.builder.set('selected', 'dockerfile')

        invoked_cmd = mock_popen.call_args[0][0]
        self.assertEqual(
            invoked_cmd[-4:],
            ['builder:set', 'myapp', 'selected', 'dockerfile'],
        )

    def test_clears_property(self, mock_popen):
        process = MagicMock()
        process.communicate.return_value = ('', '')
        process.returncode = 0
        mock_popen.return_value = process

        dokku = Dokku('dokku@host.net')
        app = App('myapp', dokku)
        app.builder.set('selected')

        invoked_cmd = mock_popen.call_args[0][0]
        self.assertEqual(
            invoked_cmd[-3:],
            ['builder:set', 'myapp', 'selected'],
        )

    def test_sets_global_property(self, mock_popen):
        process = MagicMock()
        process.communicate.return_value = ('', '')
        process.returncode = 0
        mock_popen.return_value = process

        dokku = Dokku('dokku@host.net')
        app = App('myapp', dokku)
        app.builder.set('selected', 'herokuish', global_=True)

        invoked_cmd = mock_popen.call_args[0][0]
        self.assertEqual(
            invoked_cmd[-4:],
            ['builder:set', '--global', 'selected', 'herokuish'],
        )


@patch.object(Dokku, 'run')
class TestBuilderApplyConfig(unittest.TestCase):
    def test_applies_set_properties_from_config(self, mock_run):
        dokku = Dokku('dokku@host.net')
        app = App('myapp', dokku)
        app.builder.apply_config({
            'selected': 'dockerfile',
            'build-dir': 'app2',
        })

        mock_run.assert_any_call(
            'builder:set', 'myapp', 'selected', 'dockerfile',
        )
        mock_run.assert_any_call(
            'builder:set', 'myapp', 'build-dir', 'app2',
        )

    def test_clears_property_when_value_empty(self, mock_run):
        dokku = Dokku('dokku@host.net')
        app = App('myapp', dokku)
        app.builder.apply_config({'selected': None})

        mock_run.assert_called_once_with(
            'builder:set', 'myapp', 'selected',
        )
