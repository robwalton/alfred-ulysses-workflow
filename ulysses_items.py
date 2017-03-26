#!/usr/bin/python
# encoding: utf-8

import sys
import os.path
import argparse
import json

from workflow.workflow3 import Workflow3
from workflow.workflow import MATCH_ALL, MATCH_ALLCHARS
from workflow.workflow import ICON_WARNING, ICON_ROOT

import parse_ulysses

"""Alfred script filter to return Ulysses groups and/or sheets

Returns a list of group and/or sheet items to Alfred. Call with:

    $ ulysses_items.py argdict

where argdict must contain:

    kind = 'group'|'sheet'|'all'

and may contain any of:

    only_in_path = 'path/to/root'                 # will limit the search scope
    content_query = 'some text to find in file'   # used by mdfind

"""


UPDATE_SETTINGS = {'github_slug': 'robwalton/alfred-ulysses-workflow'}

HELP_URL = 'https://github.com/robwalton/alfred-ulysses-workflow'

ICON_UPDATE = 'update-available.png'

GROUP_BULLET = u'\u25B6'  # u'\u25B8' (smaller triangle)


logger = None


def alfredworkflow(arg, node_type='', search_in='', content_query='', kind_requested='', ulysses_path=''):
    # https://www.alfredforum.com/topic/9070-how-to-workflowenvironment-variables/
    variables_dict = dict(locals())
    del variables_dict['arg']  # handled differently
    return json.dumps({'alfredworkflow': {'arg': arg, 'variables': variables_dict}})

def main(wf):

    parser = argparse.ArgumentParser()
    parser.add_argument('query', type=str, nargs='?', default=None)
    parser.add_argument('--kind', dest='kind', type=str, nargs='?')
    parser.add_argument('--limit-scope-to-dir', dest='limit_scope_dir', nargs='?')
    parser.add_argument('--search-content', dest='search_content', action='store_true')
    parser.add_argument('--search-ulysses-path', dest='search_ulysses_path', action='store_true')

    args = parser.parse_args(wf.args)
    logger.info('>>> ulysses_items.main(wf): args = ' + str(args))

    # Validy args
    assert args.kind in ('group', 'sheet', 'all')
    if args.limit_scope_dir:
        assert os.path.exists(args.limit_scope_dir), "Path does not exist: '%s'" % args.limit_scope_dir
    if args.query:
        args.query = args.query.strip()
    if args.search_ulysses_path and args.search_content:
        raise Exception('search-ulysses-path incompatible with search-content')

    # Let workflow check for updates
    if wf.update_available:
        wf.add_item('A newer version is available',
                    '↩ to install update',
                    autocomplete='wf:update',
                    icon=ICON_UPDATE)

    # TODO: refactor as logic is getting pretty tougth to follow
    #       too bad there are no tests

    # get all ulysses groups & sheets
    groups_tree = parse_ulysses.create_tree(parse_ulysses.GROUPS_ROOT, None)
    if args.limit_scope_dir:
        group_to_search = parse_ulysses.find_group_by_path(groups_tree,
                                                           args.limit_scope_dir)
        groups = group_to_search.child_groups
        sheets = group_to_search.child_sheets
    else:
        groups, sheets = parse_ulysses.walk(groups_tree)

    # filter on internal conent if applicable. Only really impacts sheets, but
    # use method on groups for simplicity.
    if args.search_content and args.query:
        logger.info('>>> Filtering content with "%s"' % args.query)
        groups = parse_ulysses.filter_groups(groups, args.query)
        sheets = parse_ulysses.filter_sheets(sheets, args.query)

    # include only desired kinds of nodes
    nodes = []
    if args.kind in ('group', 'all'):
        nodes.extend(groups)
    if args.kind in ('sheet', 'all'):
        nodes.extend(sheets)

    # apply fuzzy matching
    if args.query and not args.search_content:
        if args.search_ulysses_path or args.kind == 'group':
            key_func = expanded_node_path
        else:
            key_func = node_title

        logger.info('Fuzzy matching with query="%s" and key func="%s"'
                    % (args.query, key_func.__name__))
        # (See: http://www.deanishe.net/alfred-workflow/user-manual/filtering.html#filtering)
        nodes = wf.filter(args.query, nodes, expanded_node_path,
                          match_on=MATCH_ALL ^ MATCH_ALLCHARS)

    # add nodes to script filter results
    if not nodes:
         # Show error if there are no results. Otherwise, Alfred will show
         # its fallback searches (i.e. "Search Google for 'XYZ'")
        wf.add_item('No items', icon=ICON_WARNING)

    for node in nodes:

        pathlist = path_list_from_main(node)

        if node.is_group:
            title = GROUP_BULLET + ' ' + node.name
            node_type = 'group'
            metadata = ' (%i)' % node.number_descendents()
        elif node.is_sheet:
            title = '    ' + node.first_line.replace('#', '').strip()
            node_type = 'sheet'
            metadata = ''
        else:
            assert False

        content_query = args.query if args.search_content else None
        item = wf.add_item(
            title,
            subtitle='      ' + '/'.join(pathlist) + metadata,
            arg=alfredworkflow(node.openable_file, node_type,
                               content_query=content_query,
                               kind_requested=args.kind),
            autocomplete=node.name if node.is_group else node.first_line,
            valid=True,
            uid=node.openable_file,
            icon=node.openable_file,
            icontype='fileicon',
        )

        ancestors = list(node.get_ancestors())
        try:
            current_group = ancestors.pop()  # this is actually the group we are in
            next_group_up = ancestors.pop()
            next_group_up_path = '/'.join(path_list_from_main(current_group, include_main=True)) # add next_group_up.name?
        except IndexError:
            next_group_up = None

        if next_group_up:
            item.add_modifier(
                'shift',
                subtitle='     Go up into: ' + next_group_up_path,
                arg=alfredworkflow('', 'group', search_in=next_group_up.dirpath,
                                   content_query=content_query,
                                   kind_requested=args.kind),
            )
        else:
            item.add_modifier(
                'shift',
                subtitle='     < at top level >',
                valid=False
            )

        if node.is_group:
            contains_another_group = len(node.child_groups) > 0
            contains_sheets = len(node.child_sheets) > 0

            # work out if group should be drilled down into
            if args.kind == 'group':
                drillable = contains_another_group
            elif args.kind == 'all':
                drillable = contains_another_group or contains_sheets
            else:
                assert False

            ulysses_path = '/' + '/'.join(node.get_alfred_path_list()) + '/' + node.name
            if drillable:
                item.add_modifier(
                    'cmd',
                    subtitle='     Go into: ' + '/'.join(pathlist) + '/' + node.name,
                    arg=alfredworkflow('', 'group', search_in=node.dirpath,
                                       content_query=content_query,
                                       kind_requested=args.kind,
                                       ulysses_path=ulysses_path),
                )
            else:
                if args.kind == 'group':
                    subtitle = '< no groups >'
                elif args.kind == 'all':
                    subtitle = '< empty >'
                else:
                    assert False

                item.add_modifier(
                    'cmd',
                    subtitle='     ' + subtitle,
                    valid = False
                )

    wf.send_feedback()


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
