import os
from os.path import join
import subprocess
import plistlib
import workflow
import logging

# SHEET = "com.soulmen.ulysses3.sheet"
# GROUP = "com.soulmen.ulysses3.group"

ULYSSES3_ICLOUD_LIB = join(os.environ['HOME'], 'Library', 'Mobile Documents',
                    'X5AZV975AG~com~soulmen~ulysses3', 'Documents', 'Library')
ICLOUD_GROUPS_ROOT = join(ULYSSES3_ICLOUD_LIB, 'Groups-ulgroup')
ICLOUD_UNFILED_ROOT = join(ULYSSES3_ICLOUD_LIB, 'Unfiled-ulgroup')  # a.k.a. Inbox

ULYSSES3_LOCAL_LIB = join(os.environ['HOME'], 'Library', 'Containers',
                          'com.soulmen.ulysses3', 'Data', 'Documents',
                          'Library')
LOCAL_GROUPS_ROOT = join(ULYSSES3_LOCAL_LIB, 'Groups-ulgroup')
LOCAL_UNFILED_ROOT = join(ULYSSES3_LOCAL_LIB, 'Unfiled-ulgroup')  # a.k.a. Inbox


MDFIND_SHEET_QUERY = '((** = "%s*"cdw) && (kMDItemKind = "Ulysses Sheet*"cdwt))'
MDFIND_GROUP_QUERY = '((** = "%s*"cdw) && (kMDItemKind = "Ulysses Group*"cdwt))'


logger = workflow.Workflow3().logger
logger.setLevel(logging.DEBUG)


class AbstractItem:  # consider abstract

    def __init__(self, dirpath, parent_group, _type):
        self.dirpath = dirpath
        self.parent_group = parent_group
        self.title = None
        self.type = _type

    def get_ancestors(self):
        ancestors = []
        ancestor = self.parent_group
        while ancestor:
            ancestors.append(ancestor)
            ancestor = ancestor.parent_group
        ancestors.reverse()
        return ancestors

    def get_alfred_path_list(self):
        return [a.title for a in self.get_ancestors()]


class Group(AbstractItem):

    def __init__(self, dirpath, parent_group):
        AbstractItem.__init__(self, dirpath, parent_group, 'group')
        self.containers = []
        self.sheets = []
        self.openable_file = join(self.dirpath, 'Info.ulgroup')
        self.title = plistlib.readPlist(
            join(self.dirpath, 'Info.ulgroup'))['displayName']

    def number_descendents(self):
        n = len(self.sheets)
        for child_group in self.containers:
            n = n + child_group.number_descendents()
        return n


class Sheet(AbstractItem):

    def __init__(self, dirpath, parent_group):
        AbstractItem.__init__(self, dirpath, parent_group, 'sheet')
        self.dirpath = dirpath
        self.openable_file = dirpath
        with open(join(self.dirpath, 'Text.txt'), 'r') as f:
            self.title = f.readline().decode('utf-8').strip()


def filter_nodes_by_openable_file(nodes, openable_file_list):
    return [node for node in nodes if node.openable_file in openable_file_list]


def filter_groups(groups, query):
    openable_files = subprocess.check_output(
        ['mdfind', MDFIND_GROUP_QUERY % query]).split('\n')
    return filter_nodes_by_openable_file(groups, openable_files)


def filter_sheets(sheets, query):
    openable_files = subprocess.check_output(
        ['mdfind', MDFIND_SHEET_QUERY % query]).split('\n')
    return filter_nodes_by_openable_file(sheets, openable_files)


def create_tree(rootgroupdir, parent_group):
    '''recursively build group tree starting from rootgroupdir
    '''
    assert rootgroupdir.endswith('-ulgroup')
    filelist = os.listdir(rootgroupdir)
    assert 'Info.ulgroup' in filelist
    sheetdirlist = [p for p in filelist if p.endswith('.ulysses')]
    groupdirlist = [p for p in filelist if p.endswith('-ulgroup')]

    # Create group
    group = Group(rootgroupdir, parent_group)

    # Add Sheets
    for sheetdir in sheetdirlist:
        sheet = Sheet(join(rootgroupdir, sheetdir), group)
        group.sheets.append(sheet)

    # Recursively add groups
    for child_groupdir in groupdirlist:
        child_group = create_tree(join(rootgroupdir, child_groupdir), group)
        assert child_group != group
        group.containers.append(child_group)

    return group


def walk(root_group):
    """Walk a tree of nodes and return sheets and groups"""
    groups = [root_group]
    sheets = list(root_group.sheets)
    for child_group in root_group.containers:
        descendent_groups, descendent_sheets = walk(child_group)
        groups += descendent_groups
        sheets += descendent_sheets
    return groups, sheets


def find_group_by_path(root_group, dirpath):
    """Walk a tree of nodes and return the one backed by given dirpath

    KeyError if not found
    """
    groups, _ = walk(root_group)
    for group in groups:
        if group.dirpath == dirpath:
            return group
    raise KeyError("Group with dirpath '%s' not found" % dirpath)
