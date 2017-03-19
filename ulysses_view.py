import sys
import os.path

import workflow.workflow3
import parse_ulysses

"""

"""

logger = None


# Views match entries in Ulysses' View menu
views = ['Default', 'Library', 'Sheets', 'Editor Only']


def main(wf):

    sheet_or_group = wf.args[0]
    assert sheet_or_group in ['sheet', 'group']

    configured_view = get_view_setting(sheet_or_group)

    for view in views:
        if view is 'Default':
            subtitle = 'Let Ulysses decide how to open items'
        else:
            subtitle = "Switch to '%s' view after opening" % view
        title = view + (' (selected)' if configured_view==view else '')
        wf.add_item(
            title,
            subtitle=subtitle,
            arg=view,
            valid=True,
            autocomplete=view,
        )

    wf.send_feedback()


def get_view_setting(sheet_or_group):
    assert sheet_or_group in ['sheet', 'group']
    wf = workflow.workflow3.Workflow3()
    view = wf.settings.get('open_%s_with_view' % sheet_or_group, None)
    if view not in views:
        if sheet_or_group == 'sheet':
            view = 'Editor Only'
        else:  # group
            view = 'Sheets'
    return view

def set_view_setting(sheet_or_group, view):
    assert sheet_or_group in ['sheet', 'group']
    wf = workflow.workflow3.Workflow3()
    wf.settings['open_%s_with_view' % sheet_or_group] = view


if __name__ == "__main__":
    wf = workflow.workflow3.Workflow3()
    logger = wf.logger
    sys.exit(wf.run(main))
