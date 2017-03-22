#!/usr/bin/python
# encoding: utf-8

import sys
import os.path

from workflow.workflow3 import Workflow3
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
    logger.info('>>> ulysses_items.main(wf): wf.args = ' + str(wf.args))

        # Update available?
    if wf.update_available:
        wf.add_item('A newer version is available',
                    '↩ to install update',
                    autocomplete='workflow:update',
                    icon=ICON_UPDATE)


    # parse single argdict argument
    argdict = eval(wf.args[0].strip())
    kind = argdict['kind']  # required
    only_in_path = argdict.get('only_in_path')
    content_query = argdict.get('content_query')

    assert kind in ('group', 'sheet', 'all')
    if only_in_path:
        assert os.path.exists(only_in_path), "Path does not exist: '%s'" % only_in_path
    if content_query:
        content_query = content_query.strip()

    # get all ulysses groups & sheets
    groups_tree = parse_ulysses.create_tree(parse_ulysses.GROUPS_ROOT, None)
    if only_in_path:
        group_to_search = parse_ulysses.find_group_by_path(groups_tree,
                                                           only_in_path)
        groups = group_to_search.child_groups
        sheets = group_to_search.child_sheets
    else:
        groups, sheets = parse_ulysses.walk(groups_tree)


    # filter if applicable
    if content_query:
        logger.info('>>> Filtering on "%s"' % content_query)
        groups = parse_ulysses.filter_groups(groups, content_query)
        sheets = parse_ulysses.filter_sheets(sheets, content_query)

    # include only desired kinds of nodes
    nodes = []
    if kind in ('group', 'all'):
        nodes.extend(groups)
    if kind in ('sheet', 'all'):
        nodes.extend(sheets)

    # add nodes to script filter results
    for node in nodes:

        node_is_sheet = isinstance(node, parse_ulysses.Sheet)
        node_is_group = isinstance(node, parse_ulysses.Group)
        assert node_is_sheet or node_is_group


        pathlist = node.get_alfred_path_list()
        if pathlist and (pathlist[0] == 'Main'):
            pathlist = pathlist[1:]

        if node_is_group:
            title = u'\u25B8' + ' ' + node.name
            node_type = 'group'
        else: # node_is_sheet:
            title = '   ' + node.first_line
            node_type = 'sheet'

        item = wf.add_item(
            title,
            subtitle='     ' + '/'.join(pathlist),
            arg=alfredworkflow(node.openable_file, node_type, content_query=content_query),
            autocomplete=node.name if node_is_group else node.first_line,
            valid=True,
            uid=node.openable_file,
            icon=node.openable_file,
            icontype='fileicon',
        )

        if node_is_group:
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


if __name__ == "__main__":
    wf = Workflow3(help_url=HELP_URL,
                   update_settings=UPDATE_SETTINGS)
    logger = wf.logger
    sys.exit(wf.run(main))
