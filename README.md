# Alfred Ulysses Workflow

[Alfred 2 workflow](https://www.alfredapp.com/workflows/) to search and create tasks in [Ulysses](https://ulyssesapp.com).

## Install
To install, download a released Ulysses.alfredworkflow and double-click to open in Alfred 2. Alternatively, download what should be the most recent version hosted on [Packal](http://www.packal.org/workflow/ulysses). There is a [discussion thread on the Alfred forum](http://www.alfredforum.com/topic/9662-ulysses-workflow/).

## Get help
Use the keyword:

- **u:help** -- Show a brief summary of commands

## Open group or sheet
Use the keywords:

- **u** -- Open group or sheet (cmd-return to drill down)
- **ug** -- Open group (cmd-return to drill down)
- **us** -- Open sheet

## Pop open Ulysses Open dialogue

Use the keyword:
- **uo <arg>** -- Search for <arg> within Ulysses’ Open dialogue

## Configure view to open

- **u:setsheetview** -- Set the view for opening sheets with (defaults to 'Editor Only')
- **u:setgroupview** -- Set the view for opening groups with (defaults to 'Sheets')

## Versions

**0.9**
- Initial public release

**0.9.1**
- Added feature to select view for opening items with and commands to confure
- Behind the scenes the workflow now uses (not enough of) deanishe's https://github.com/deanishe/alfred-workflow
- Help now opens in Safari
- 'ug' command no longer lets user drill into empty groups   

**0.9.2**
- Fix race condition where toggling view state fails if Ulysses is launching

## To contribute
To contribute to the workflow please fork on github: https://github.com/robwalton/alfred-ulysses-workflow

