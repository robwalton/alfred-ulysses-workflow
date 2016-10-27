import json
import parse_ulysses
import sys


SHEET = 'sheet'
GROUP = 'group'
ALL = 'all'


def script_filter_items(kind, onlyin=None):
    '''kind may be SHEET, GROUP or ALL. If provided onlyin will be a group's
    enclosing directory path.
    '''

    groups_tree = parse_ulysses.create_tree(parse_ulysses.GROUPS_ROOT, None)
    if onlyin:
        group_to_search = parse_ulysses.find_group_by_path(groups_tree, onlyin)
        groups = group_to_search.child_groups
        sheets = group_to_search.child_sheets
    else:
        groups, sheets = parse_ulysses.walk(groups_tree)

    if kind == SHEET:
        groups = []
    elif kind == GROUP:
        sheets = []
    else:
        assert kind == ALL

    def alfredworkflow(arg='', search_in=''):
        return '{"alfredworkflow" :{"arg": "%s", "variables": {"search_in": "%s"}}}' % (arg, search_in)

    items = []

    for group in groups:
        pathlist = group.get_alfred_path_list()
        if pathlist and (pathlist[0] == 'Main'):
            pathlist = pathlist[1:]

        item = {
            'uid': group.openable_file,
            'title': u'\u25B8' + ' ' + group.name,
            'autocomplete': group.name,
            'subtitle': '     ' + '/'.join(pathlist),
            'arg': alfredworkflow(arg=group.openable_file),
            'icon': {
                'type': 'fileicon',
                'path': group.openable_file
            },
            'mods': {
                'cmd': {
                    'valid': True,
                    'arg': alfredworkflow(arg='', search_in=group.dirpath),
                    'subtitle': '     Go into: ' + '/'.join(pathlist) + '/' + group.name
                }
            }
        }
        items.append(item)

    for sheet in sheets:
        # full_path = '/'.join(get_ancestor_names(path)[:-1])
        pathlist = sheet.get_alfred_path_list()
        if pathlist and (pathlist[0] == 'Main'):
            pathlist = pathlist[1:]
        item = {
            'uid': sheet.openable_file,
            'title': '   ' + sheet.first_line,
            'subtitle': '     ' + '/'.join(pathlist),
            'arg': alfredworkflow(arg=sheet.openable_file),
            'icon': {
                'type': 'fileicon',
                'path': sheet.openable_file
            },
            'mods': {
                'cmd': {
                    'valid': False,
                }
            }
        }
        items.append(item)

    return items


def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    # else
    return text
