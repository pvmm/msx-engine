#!/usr/bin/env python3
# encoding: utf-8

from nicegui import ui
from common import UiMetatile

from stageeditor import StageEditor


stage_editor: StageEditor


def update_stage_editor() -> None:
    if 'stage_editor' in globals():
        stage_editor.update_tiles()


@ui.page('/')
def main() -> None:
    background_tiles: list[UiMetatile] = []

    from nicegui import ui
    with ui.tabs(on_change=lambda e: update_stage_editor()) as tabs:
        ui.tab('p', label='Project', icon='rocket_launch')
        ui.tab('s', label='Stages', icon='apps')
        ui.tab('a', label='About', icon='info')

    with ui.tab_panels(tabs, value='p').classes('w-full') as tab_panels:
        from project import Project
        Project(ui.tab_panel('p'), background_tiles)

        from stageeditor import StageEditor
        stage_editor = StageEditor(ui.tab_panel('s'), background_tiles)

        with ui.tab_panel('a'):
            ui.label('Infos')


if __name__ in {'__main__', '__mp_main__'}:
    from common import run
    run()
