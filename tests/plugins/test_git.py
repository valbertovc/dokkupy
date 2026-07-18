import unittest
from unittest.mock import MagicMock, patch

from dokkupy.core import App, Dokku
from dokkupy.plugins.git import Git


@patch('dokkupy.core.subprocess.Popen')
class TestGitFromImage(unittest.TestCase):
    def test_minimal_args(self, mock_popen):
        process = MagicMock()
        process.communicate.return_value = ('', '')
        process.returncode = 0
        mock_popen.return_value = process

        dokku = Dokku('dokku@host.net')
        app = App('myapp', dokku)
        app.git.from_image('registry.gitlab.com/group/project:tag')

        invoked_cmd = mock_popen.call_args[0][0]
        self.assertEqual(
            invoked_cmd[-3:],
            ['git:from-image', 'myapp', 'registry.gitlab.com/group/project:tag'],
        )

    def test_with_force_and_build_dir(self, mock_popen):
        process = MagicMock()
        process.communicate.return_value = ('', '')
        process.returncode = 0
        mock_popen.return_value = process

        dokku = Dokku('dokku@host.net')
        app = App('myapp', dokku)
        app.git.from_image(
            'registry/app:tag',
            force=True,
            build_dir='path/to/build',
        )

        invoked_cmd = mock_popen.call_args[0][0]
        self.assertEqual(
            invoked_cmd[-5:],
            [
                '--force', '--build-dir', 'path/to/build',
                'myapp', 'registry/app:tag',
            ],
        )

    def test_with_author(self, mock_popen):
        process = MagicMock()
        process.communicate.return_value = ('', '')
        process.returncode = 0
        mock_popen.return_value = process

        dokku = Dokku('dokku@host.net')
        app = App('myapp', dokku)
        app.git.from_image(
            'registry/app:tag',
            author_name='Camila',
            author_email='camila@example.com',
        )

        invoked_cmd = mock_popen.call_args[0][0]
        self.assertEqual(
            invoked_cmd[-5:],
            [
                'git:from-image', 'myapp', 'registry/app:tag',
                'Camila', 'camila@example.com',
            ],
        )


@patch.object(Git, 'from_image')
class TestGitApplyConfig(unittest.TestCase):
    def test_passes_image_config_to_from_image(self, mock_from_image):
        dokku = Dokku('dokku@host.net')
        app = App('myapp', dokku)
        app.git.apply_config({
            'method': 'image',
            'image': {
                'from': 'registry/app:tag',
                'force': True,
                'build_dir': 'path/to/build',
                'author': {
                    'name': 'Camila',
                    'email': 'camila@example.com',
                },
            },
        })

        mock_from_image.assert_called_once_with(
            'registry/app:tag',
            force=True,
            build_dir='path/to/build',
            author_name='Camila',
            author_email='camila@example.com',
        )


@patch.object(App, 'deploy')
@patch.object(Git, 'apply_config')
class TestDeployImageMethod(unittest.TestCase):
    def test_uses_from_image_when_method_is_image(self, mock_apply, mock_deploy):
        dokku = Dokku('dokku@host.net')
        with patch.object(dokku, '_list', return_value=['myapp']):
            dokku.deploy('myapp', {
                'deployment': {
                    'method': 'image',
                    'image': {'from': 'registry/app:tag'},
                },
            }, destroy=False)

        mock_apply.assert_called_once()
        mock_deploy.assert_not_called()

    def test_uses_git_push_by_default(self, mock_apply, mock_deploy):
        dokku = Dokku('dokku@host.net')
        with patch.object(dokku, '_list', return_value=['myapp']):
            dokku.deploy('myapp', {}, destroy=False)

        mock_apply.assert_not_called()
        mock_deploy.assert_called_once()
