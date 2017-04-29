# test against live ulysses database


import os

from ulysses_items import ICLOUD_GROUPS_ROOT
import parse_ulysses
import sys


import ulysses


# Only valid for a particular local Ulysses install
MANUALLY_CONFIGURED_TOKEN = 'c6e4ef1a29e44e62acdcee4e5eabc423'


def setup_module(module):
    ulysses.xcallback.set_access_token(MANUALLY_CONFIGURED_TOKEN)

####

# Differences
# 1. parsed iCloud group is called 'Main' rather than 'iCloud'
# 2. parsed iClloud does not include 'Inbox'; called does


def test_parse_ulysses_top_level_name():
    assert os.path.exists(ICLOUD_GROUPS_ROOT)
    icloud_tree = parse_ulysses.create_tree(ICLOUD_GROUPS_ROOT, None)
    assert icloud_tree.title == 'Main'  # difference #1


def test_ulysses_top_level_group_titles():
    trees = ulysses.get_root_items(recursive=True)
    assert trees[0].title == 'iCloud'
    assert trees[1].title == 'On My Mac'


def test_iCloud_container_titles_agree():
    parsed_icloud_root = parse_ulysses.create_tree(ICLOUD_GROUPS_ROOT, None)
    called_icloud_root = ulysses.get_root_items(recursive=True)[0]
    parsed_container_names = [
        group.title for group in parsed_icloud_root.containers]
    called_container_names = [
        group.title for group in called_icloud_root.containers]
    # difference #2:
    assert ['Inbox'] + parsed_container_names == called_container_names
    

def test_compare_library_keys():
    assert set(ulysses.library().keys()) == set(parse_ulysses.library().keys()) == {'On My Mac', 'iCloud'}


def test_compare_library_group_titles():
    parsed_lib = parse_ulysses.library()
    called_lib = ulysses.library()
    
    # iCloud
    assert parsed_lib['iCloud'].title == called_lib['iCloud'].title == 'iCloud'
    
    # iCloud/Inbox
    assert called_lib['iCloud'].containers_by_title['Inbox'].title == 'Inbox'
    assert parsed_lib['iCloud'].containers_by_title['Inbox'].title == 'Inbox'

    # On My Mac
    assert parsed_lib['On My Mac'].title == called_lib['On My Mac'].title == 'On My Mac'
    
    # On My Mac/Inbox
    assert called_lib['On My Mac'].containers_by_title['Inbox'].title == 'Inbox'
    assert parsed_lib['On My Mac'].containers_by_title['Inbox'].title == 'Inbox'


def test_iCloud_tree():
    parsed_containers = walk_containers(parse_ulysses.library()['iCloud'])
    called_containers = walk_containers(ulysses.library()['iCloud'])
    # Not a great test as orders differ. Just check all items are present in each
    parsed_titles = {c.title for c in parsed_containers}
    called_titles = {c.title for c in called_containers}
    print 'parsed_titles:', parsed_titles
    print 'called_titles:', called_titles
    assert parsed_titles == called_titles


def walk_containers(container):
    container_list = [container]
    for child_container in container.containers:
        container_list.extend(walk_containers(child_container))
    return container_list

