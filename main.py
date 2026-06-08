#!/usr/bin/env python3

if __name__ in {'__main__', '__mp_main__'}:
    from nicegui import ui
    with ui.column().classes('w-full'):
        with ui.tabs() as tabs:
            ui.tab('p', label='Project', icon='rocket_launch')
            ui.tab('s', label='Stages', icon='apps')
            ui.tab('a', label='About', icon='info')

        with ui.tab_panels(tabs, value='p').classes('w-full'):
            with ui.tab_panel('p'):
                from project import Project
                Project(ui.column().classes('w-full'))
            with ui.tab_panel('s'):
                from stageeditor import StageEditor
                StageEditor(ui.column())
            with ui.tab_panel('a'):
                ui.label('Infos')

    from common import run
    run()
