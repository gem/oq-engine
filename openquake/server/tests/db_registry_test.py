import ast
from pathlib import Path

from openquake.server.db import actions
from openquake.server.db.registry import ACTION_REGISTRY, get_action


def test_registry_contains_all_database_actions():
    path = Path(actions.__file__)
    tree = ast.parse(path.read_text())
    names = {
        node.name for node in tree.body
        if isinstance(node, ast.FunctionDef) and not node.name.startswith('_')}
    assert set(ACTION_REGISTRY) == names


def test_registry_resolves_actions():
    for name in ACTION_REGISTRY:
        spec, action = get_action(name)
        assert spec.name == name
        assert callable(action)


def test_worker_actions_are_not_database_actions():
    assert not set(ACTION_REGISTRY) & {
        'workers_start', 'workers_stop', 'workers_status',
        'workers_restart', 'workers_wait', 'workers_kill', 'workers_debug'}
