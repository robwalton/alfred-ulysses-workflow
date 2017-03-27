#!/usr/bin/python
# encoding: utf-8

import sys
import os.path
import argparse
import json

from workflow.workflow3 import Workflow3
from workflow.workflow import MATCH_ALL, MATCH_ALLCHARS
from workflow.workflow import ICON_WARNING

import parse_ulysses
from parse_ulysses import GROUPS_ROOT, UNFILED_ROOT


"""Return Alfred items representing Ulysses groups and/or sheets.

See parser below.

"""


UPDATE_SETTINGS = {'github_slug': 'robwalton/alfred-ulysses-workflow'}

HELP_URL = 'https://github.com/robwalton/alfred-ulysses-workflow'

ICON_UPDATE = 'update-available.png'

GROUP_BULLET = u'\u25B6'  # black triangle
INBOX_BULLET = u'\u25B7'  # white triangle
INBOX_SHEET_BULLET = u'\u25E6'  # white bullet

logger = None


def main(wf):

    # Parse args
    parser = argparse.ArgumentParser()
    parser.add_argument('query', type=str, nargs='?', default=None,
                        help='query used normally for searching')
    parser.add_argument('--kind', dest='kind', type=str, nargs='?',
                        help='items to return: group, sheet or all')
    parser.add_argument('--limit-scope-to-dir', dest='limit_scope_dir',
                        nargs='?',
                        help='limit search to directory on file system')
    parser.add_argument('--search-content', dest='search_content',
                        action='store_true',
                        help='search inside content')
    parser.add_argument('--search-ulysses-path', dest='search_ulysses_path',
                        action='store_true',
                        help='search full path to item, not just node name')

    args = parser.parse_args(wf.args)
    logger.info('ulysses_items.main(wf): args = \n' + str(args))
    validify_args(args)

    # Check for updates
    check_for_workflow_update(wf)

    # Parse entire ulysses data structure
    include_groups = args.kind in ('group', 'all')
    include_sheets = args.kind in ('sheet', 'all')
    groups = []
    sheets = []

    # Collect items from icloud
    if os.path.exists(GROUPS_ROOT+'x'):
        icld_groups, icld_sheets = parse_ulysses_for_groups_and_sheets(
            GROUPS_ROOT, args.limit_scope_dir, include_groups, include_sheets)
        groups.extend(icld_groups)
        sheets.extend(icld_sheets)
    else:
        logger.warn("No iCloud library found at '%s'" % GROUPS_ROOT)
        wf.add_item('No iCloud items found and external folders not supported',
                    icon=ICON_WARNING)


    # Collect items from Inbox
    inbox_groups, inbox_sheets = parse_ulysses_for_groups_and_sheets(
        UNFILED_ROOT, args.limit_scope_dir, include_groups, include_sheets)
    groups.extend(inbox_groups)
    sheets.extend(inbox_sheets)

    # filter on internal conent if applicable. Only really impacts sheets, but
    # use method on groups for simplicity.
    if args.search_content and args.query:
        groups, sheets = filter_based_on_content(groups, sheets, args.query)

    # Merge groups and sheets to create a single list of nodes
    nodes = groups + sheets

    # Filter nodes using fuzzy matching for {query}
    if args.query and not args.search_content:
        search_whole_path = args.search_ulysses_path or args.kind == 'group'
        nodes = fuzzy_filter_nodes(wf, nodes, args.query, search_whole_path)

    # Show error if there are no results. Otherwise, Alfred will show
    # its fallback searches (i.e. "Search Google for 'XYZ'")
    if not nodes:
        wf.add_item('No items', icon=ICON_WARNING)

    # Create, add and modify item to represent node
    for node in nodes:
        item = add_ulysses_item_to_wf_results(wf, args, node)
        # note that the wf keeps a copy of the item; we need only modify it
        item = add_modifier_to_go_up_hierarchy(args, node, item)
        if node.is_group:
            item = add_modifier_to_drill_down_hierarchy(args, node, item)

    wf.send_feedback()


def validify_args(args):
    """Validate args"""
    assert args.kind in ('group', 'sheet', 'all')
    if args.limit_scope_dir:
        assert (os.path.exists(args.limit_scope_dir),
                "Path does not exist: '%s'" % args.limit_scope_dir)
    if args.query:
        args.query = args.query.strip()
    if args.search_ulysses_path and args.search_content:
        raise Exception('search-ulysses-path incompatible with search-content')


def check_for_workflow_update(wf):
    if wf.update_available:
        wf.add_item('A newer version is available',
                    '↩ to install update',
                    autocomplete='wf:update',
                    icon=ICON_UPDATE)


def parse_ulysses_for_groups_and_sheets(
        root_dir, limit_scope_dir, include_groups, include_sheets):
    """Parse entire Ulysses trees and return list of groups and sheets"""

    # Get ulysses groups & sheets from iCloud
    groups_tree = parse_ulysses.create_tree(root_dir, None)
    if limit_scope_dir:
        group_to_search = parse_ulysses.find_group_by_path(groups_tree,
                                                           limit_scope_dir)
        groups = group_to_search.child_groups
        sheets = group_to_search.child_sheets
    else:
        groups, sheets = parse_ulysses.walk(groups_tree)
    if not include_groups:
        groups = []
    if not include_sheets:
        sheets = []
    return groups, sheets


def filter_based_on_content(groups, sheets, query):
    """Filter lists of groups and sheets.

    Return only items which are also find by spotlight's mdfind.
    """
    logger.info('>>> Filtering content with "%s"' % query)
    groups = parse_ulysses.filter_groups(groups, query)
    sheets = parse_ulysses.filter_sheets(sheets, query)
    return groups, sheets


def fuzzy_filter_nodes(wf, nodes, query, search_whole_path):
    """Filter list of nodes with query.

    If search_whole_path is true then search the Ulysses path for query,
    otherwise just the name of the sheet or group.
    """
    if search_whole_path:
        key_func = expanded_node_path
    else:
        key_func = node_title
    logger.info('Fuzzy matching with query="%s" and key func="%s"'
                % (query, key_func.__name__))
    # See: http://www.deanishe.net/alfred-workflow/user-manual/filtering.html
    nodes = wf.filter(query, nodes, key_func,
                      match_on=MATCH_ALL ^ MATCH_ALLCHARS)
    return nodes


def alfredworkflow(arg, node_type='', search_in='', content_query='',
                   kind_requested='', ulysses_path=''):
    """
    Return JSON dictionary used instead of a normal Ulysses item's arg.

    Used to return both arg and workflow environment variables. See:
    https://www.alfredforum.com/topic/9070-how-to-workflowenvironment-variables/

    - arg: the normal Alfred argument used to create {query} downstream
    - node_type: 'sheet' or 'group'
    - search_in: a group's location on disk (TODO: odd name)
    - content_query: query used to search content, or ''
    - kind_requested: record of nodes requested: 'sheet', 'group' or 'all'
    - ulysses_path - the Ulysses path of item. See:
                     https://ulyssesapp.com/kb/x-callback-url/#paths
    """
    variables_dict = dict(locals())
    del variables_dict['arg']  # handled differently
    return json.dumps(
        {'alfredworkflow': {'arg': arg, 'variables': variables_dict}})


def add_ulysses_item_to_wf_results(wf, args, node):
    """Create and add Ulysses item to workflow results for this call.

    Return item for subsequent modification
    """
    pathlist = path_list_from_main(node)
    ulysses_path = '/'.join([''] + pathlist)
    if node.is_group:
        ulysses_path += '/' + node.name
        if ulysses_path == '/Inbox':
            bullet = INBOX_BULLET
        else:
            bullet = GROUP_BULLET
        title = bullet + ' ' + node.name
        node_type = 'group'
        metadata = ' (%i)' % node.number_descendents()

    elif node.is_sheet:
        if node.first_line.strip() == '':
            name = '< first line blank >'
        else:
            name = node.first_line.replace('#', '').strip()
        if ulysses_path == '/Inbox':
            title = ' ' + INBOX_SHEET_BULLET + '  ' + name
        else:
            title = '    ' + name
        node_type = 'sheet'
        metadata = ''
    else:
        assert False
    logger.info(ulysses_path)
    content_query = args.query if args.search_content else ''
    item = wf.add_item(
        title,
        subtitle='      ' + '/' + '/'.join(pathlist) + metadata,
        arg=alfredworkflow(node.openable_file, node_type,
                           content_query=content_query,
                           kind_requested=args.kind,
                           ulysses_path=ulysses_path),
        autocomplete=node.name if node.is_group else node.first_line,
        valid=True,
        uid=node.openable_file,
        icon=node.openable_file,
        icontype='fileicon')
    return item


def add_modifier_to_go_up_hierarchy(args, node, item):
    """Add shift modifier to Ulysses item to request move up hierarchy."""
    ancestors = list(node.get_ancestors())
    try:
        current_group = ancestors.pop()  # this is actually the group we are in
        next_group_up = ancestors.pop()
        path_list = path_list_from_main(current_group, include_main=False)
        next_group_up_path = '/' + '/'.join(path_list)
    except IndexError:
        next_group_up = None
    content_query = args.query if args.search_content else ''
    if next_group_up:
        arg = alfredworkflow('', 'group',
                             search_in=next_group_up.dirpath,
                             content_query=content_query,
                             kind_requested=args.kind)
        item.add_modifier('shift',
                          subtitle='     Go up into: ' + next_group_up_path,
                          arg=arg)
    else:
        item.add_modifier('shift',
                          subtitle='     < at top level >',
                          valid=False)
    return item


def add_modifier_to_drill_down_hierarchy(args, node, item):
    """Add shift modifier to Ulysses item to request move down hierarchy."""
    contains_another_group = len(node.child_groups) > 0
    contains_sheets = len(node.child_sheets) > 0

    # work out if group should be drilled down into
    if args.kind == 'group':
        drillable = contains_another_group
    elif args.kind == 'all':
        drillable = contains_another_group or contains_sheets
    else:
        assert False

    content_query = args.query if args.search_content else ''

    if drillable:
        pathlist = path_list_from_main(node)
        subtitle = '     Go into: ' + '/'.join(pathlist) + '/' + node.name
        arg = alfredworkflow('', 'group', search_in=node.dirpath,
                             content_query=content_query,
                             kind_requested=args.kind)
        item.add_modifier('cmd', subtitle=subtitle, arg=arg)
    else:
        if args.kind == 'group':
            subtitle = '< no groups >'
        elif args.kind == 'all':
            subtitle = '< empty >'
        else:
            assert False
        item.add_modifier('cmd', subtitle='     ' + subtitle, valid=False)


def expanded_node_path(node):
    path_list = node.get_alfred_path_list()
    path_list.append(node.title)
    logger.info(' '.join(path_list))
    return ' '.join(path_list)


def node_title(node):
    return node.title


def path_list_from_main(node, include_main=False):
    pathlist = node.get_alfred_path_list()
    if pathlist and (pathlist[0] == 'Main'):
        if not include_main:
            pathlist = pathlist[1:]

    return pathlist


if __name__ == "__main__":
    wf = Workflow3(help_url=HELP_URL,
                   update_settings=UPDATE_SETTINGS)
    wf.magic_prefix = 'wf:'
    logger = wf.logger
    sys.exit(wf.run(main))
