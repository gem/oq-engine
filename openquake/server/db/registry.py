"""Registry of database actions exposed by the internal API."""

from dataclasses import dataclass
from openquake.server.db import actions


@dataclass(frozen=True)
class ActionSpec:
    """Metadata for one database action."""

    name: str
    transaction: str = 'autocommit'


_ACTION_NAMES = (
    'check_outdated', 'has_job_table', 'reset_is_running', 'keep',
    'set_status', 'create_job', 'import_job', 'delete_uncompleted_calculations',
    'get_job', 'get_jobs', 'get_uncompleted_jobs', 'get_running_jobs',
    'get_weight', 'list_calculations', 'list_outputs', 'get_outputs',
    'create_outputs', 'finish', 'del_calc', 'log', 'get_log',
    'get_jobs_by_date', 'get_job_stats', 'installation_id',
    'get_installation_id', 'get_path', 'get_dbpath', 'engine_version',
    'what_if_I_upgrade', 'db_version', 'upgrade_db', 'calc_info', 'get_calcs',
    'update_job', 'share_job', 'add_tag_to_job', 'remove_tag_from_job',
    'set_preferred_job_for_tag', 'unset_preferred_job_for_tag',
    'get_preferred_job_for_tag', 'create_tag', 'delete_tag', 'list_tags',
    'update_parent_child', 'get_log_slice', 'get_log_size', 'get_traceback',
    'get_result', 'get_results', 'get_output', 'get_executing_jobs',
    'get_calc_ids',
    'get_longest_jobs', 'find', 'update_job_checksum', 'get_checksum_from_job',
    'get_job_id_from_checksum', 'get_job_from_checksum',
)

_TRANSACTIONAL_ACTIONS = frozenset({
    'reset_is_running', 'keep', 'set_status', 'create_job', 'import_job',
    'delete_uncompleted_calculations', 'create_outputs', 'finish', 'del_calc',
    'log', 'upgrade_db', 'update_job', 'share_job', 'add_tag_to_job',
    'remove_tag_from_job', 'set_preferred_job_for_tag',
    'unset_preferred_job_for_tag', 'create_tag', 'delete_tag',
    'update_parent_child', 'update_job_checksum',
})

ACTION_REGISTRY = {
    name: ActionSpec(
        name, 'explicit' if name in _TRANSACTIONAL_ACTIONS else 'autocommit')
    for name in _ACTION_NAMES}


def get_action(name):
    """Return a registered database action and its metadata."""
    try:
        spec = ACTION_REGISTRY[name]
    except KeyError:
        raise KeyError('Unknown database action: %s' % name) from None
    return spec, getattr(actions, name)
