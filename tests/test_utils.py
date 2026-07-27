import os
import unittest
from unittest.mock import patch

from dokkupy.utils import resolve_config_value


class TestResolveConfigValue(unittest.TestCase):
    def test_returns_plain_string(self):
        self.assertEqual(resolve_config_value('hello'), 'hello')

    def test_resolves_env_dict(self):
        with patch.dict(os.environ, {'MY_VAR': 'secret'}):
            self.assertEqual(
                resolve_config_value({'env': 'MY_VAR'}),
                'secret',
            )
