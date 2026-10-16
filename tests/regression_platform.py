"""Keep semantic helpers importable without POSIX resource telemetry."""
import builtins
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))


class PlatformBoundaryTests(unittest.TestCase):
    def test_missing_resource_preserves_helpers_but_rejects_campaign(self):
        original = builtins.__import__
        def without_resource(name, *args, **kwargs):
            if name == 'resource':
                raise ImportError('simulated platform without resource')
            return original(name, *args, **kwargs)
        spec = importlib.util.spec_from_file_location(
            'workload_identifiability.platform_fixture',
            ROOT/'src/workload_identifiability/experiments.py')
        module = importlib.util.module_from_spec(spec)
        with patch('builtins.__import__', without_resource):
            spec.loader.exec_module(module)
        self.assertEqual(len(module.tiny_model()['queries']), 6)
        self.assertEqual(len(module.mutation_cases(
            module.cascade(2, [1, 2]), module.produce(module.cascade(2, [1, 2])))), 16)
        with self.assertRaisesRegex(RuntimeError, 'requires Linux'):
            module.apply_limits()


if __name__ == '__main__':
    unittest.main()
