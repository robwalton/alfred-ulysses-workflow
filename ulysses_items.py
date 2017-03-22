#!/usr/bin/python
# encoding: utf-8

import sys
import os.path
import argparse

from workflow.workflow3 import Workflow3
from workflow.workflow import MATCH_ALL, MATCH_ALLCHARS
from workflow.workflow import ICON_WARNING

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

logger = None


def alfredworkflow(arg, node_type, search_in='', content_query=''):
    return '{"alfredworkflow" :{"arg": "%s", "variables": {"search_in": "%s", "node_type": "%s", "content_query": "%s"}}}' % (arg, search_in, node_type, content_query)


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
        if args.search_ulysses_path:
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

        pathlist = node.get_alfred_path_list()
        if pathlist and (pathlist[0] == 'Main'):
            pathlist = pathlist[1:]

        if node.is_group:
            title = u'\u25B8' + ' ' + node.name
            node_type = 'group'
        elif node.is_sheet:
            title = '   ' + node.first_line
            node_type = 'sheet'
        else:
            assert False

        content_query = args.query if args.search_content else None
        item = wf.add_item(
            title,
            subtitle='     ' + '/'.join(pathlist),
            arg=alfredworkflow(node.openable_file, node_type, content_query=content_query),
            autocomplete=node.name if node.is_group else node.first_line,
            valid=True,
            uid=node.openable_file,
            icon=node.openable_file,
            icontype='fileicon',
        )

        if node.is_group:
            contains_another_group = len(node.child_groups) > 0

            if contains_another_group:
                item.add_modifier(
                    'cmd',
                    subtitle='     Go into: ' + '/'.join(pathlist) + '/' + node.name,
                    arg=alfredworkflow('', 'group', search_in=node.dirpath, content_query=content_query),
                )
            else:
                item.add_modifier(
                    'cmd',
                    subtitle='     No more groups in: ' + '/'.join(pathlist) + '/' + node.name,
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


if __name__ == "__main__":
    wf = Workflow3(help_url=HELP_URL,
                   update_settings=UPDATE_SETTINGS)
    wf.magic_prefix = 'wf:'
    logger = wf.logger
    sys.exit(wf.run(main))
