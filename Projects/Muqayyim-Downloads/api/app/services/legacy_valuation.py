"""Adapt preserved Mizan methods without importing the separate ML application's startup.

No formulas are copied from those engines. Fixed legacy confidence/range heuristics
are deliberately not exposed by the new workflow.
"""
from functools import lru_cache
from pathlib import Path
import hashlib
import importlib.util
import sys
import types


@lru_cache()
def engines():
    folder = Path(__file__).resolve().parents[4] / 'Mizan-Antigravity/src/mizan_engine/approaches'
    package = '_mizan_preserved_approaches'
    namespace = types.ModuleType(package)
    namespace.__path__ = [str(folder)]
    sys.modules[package] = namespace
    loaded = {}
    digest = hashlib.sha256()
    for name in ['base', 'income', 'cost']:
        path = folder / (name+'.py')
        digest.update(path.read_bytes())
        spec = importlib.util.spec_from_file_location(package+'.'+name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        loaded[name] = module
    return loaded['income'].IncomeApproach, loaded['cost'].CostApproach, digest.hexdigest()
