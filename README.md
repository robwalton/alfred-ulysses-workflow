# Alfred Ulysses Workflow

[Alfred 3 workflow](https://www.alfredapp.com/workflows/) to search and create tasks in [Ulysses](https://ulyssesapp.com). There is a [discussion thread on the Alfred forum](http://www.alfredforum.com/topic/9662-ulysses-workflow/).

## Install
To install, download the [latest Ulysses.alfredworkflow](https://github.com/robwalton/alfred-ulysses-workflow/releases/latest) file and double-click to open in Alfred 3. Alternatively, download what should be the most recent version hosted on [Packal](http://www.packal.org/workflow/ulysses).

## Get help

- `u:help` -- Show this brief summary of commands

## Open group or sheet

- `uf` -- Find a group or sheet based on internal content
- `u` -- Open group or sheet (cmd-return to drill down)
- `ug` -- Open group (cmd-return to drill down)
- `us` -- Open sheet

## Pop open Ulysses Open dialogue

- `uo <arg>` -- Search for <arg> within Ulysses’ Open dialogue

## Create sheets
- `un` -- create new sheet with optional text (shift-enter to create in /Inbox)

## Alfred file action

- Use the **Open in Ulysses** file action to open text-like files in Ulysses
- Use the **Import into Ulysses** file action to create a new sheet from text-like content

## Configure view to open

- `u:setsheetview` -- Set the view for opening sheets with (defaults to 'Editor Only')
- `u:setgroupview` -- Set the view for opening groups with (defaults to 'Sheets')

## Thanks
- [dfay](https://www.alfredforum.com/profile/3468-dfay/) for the new sheet code and file opener and importer as well as general encouragement
- [deanishe](https://www.alfredforum.com/profile/5235-deanishe/) for the awesome [Python workflow library](http://www.deanishe.net/alfred-workflow/index.html)
- [dunkaroo](https://www.alfredforum.com/profile/11116-dunkaroo/) for searching and file action help
- [katie](https://www.alfredforum.com/profile/5999-katie/) for thoughts on how find command should work

## Versions

**1.0.4**
- Fixed ExpatError exception that **completely broke the workflow with Ulysses 13 update**.

**1.0.3**
- Fixed to work with unicode search strings

**1.0.2**
- Fixed 'uo' command to work with renamed UlyssesMac application name under Ulysses 12 update

**1.0.1**
- Fixed displayName KeyError exception that **completely broke the workflow with Ulysses 12 update**
- Fixed an older issue with 'un' command 

**1.0**
- Fixed 100% cpu hang on Sierra with update of alfred-workflow to 1.25.1
- Added `uf` command to find groups and sheets based on their internal content
- `u`, `ug` and `uf` now use fuzzy search Ulysses' path to groups and sheets
- Added `un` command to create new sheet with optional text
- Added an Alfred file action to open text-like files in Ulysses
- Added support for Inbox items
- Added support for local Ulysses (non-iCloud) items (still no external folders)
- Added warning when no iCloud files found
- Fixed race condition with `uo` command when Ulysses is not activated

**0.9.2**
- Fix race condition where toggling view state fails if Ulysses is launching

**0.9.1**
- Added feature to select view for opening items with and commands to configure
- Behind the scenes the workflow now uses (not enough of) deanishe's https://github.com/deanishe/alfred-workflow
- Help now opens in Safari
- `ug` command no longer lets user drill into empty groups

**0.9**
- Initial public release

## To contribute
To contribute to the workflow please fork on github: https://github.com/robwalton/alfred-ulysses-workflow .

