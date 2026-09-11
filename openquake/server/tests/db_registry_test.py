import ast
from pathlib import Path

from openquake.commonlib.logs import WORKER_ACTIONS
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


def test_logs_callers_are_registered():
    root = Path(__file__).parents[3]
    actions_used = set()
    for path in root.rglob('*.py'):
        if 'tests' in path.parts:
            continue
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and
                    isinstance(node.func, ast.Attribute) and
                    node.func.attr == 'dbcmd' and
                    isinstance(node.func.value, ast.Name) and
                    node.func.value.id == 'logs' and node.args):
                continue
            action = node.args[0]
            if isinstance(action, ast.Constant) and isinstance(
                    action.value, str):
                actions_used.add(action.value)
    special = {'getpid'}
    assert actions_used <= set(ACTION_REGISTRY) | WORKER_ACTIONS | special
