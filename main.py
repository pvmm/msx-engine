from nicegui import ui

with ui.tabs() as tabs:
    ui.tab('p', label='Project', icon='rocket_launch')
    ui.tab('t', label='Tileset', icon='apps')
    ui.tab('a', label='About', icon='info')

with ui.tab_panels(tabs, value='p').classes('w-full'):
    with ui.tab_panel('p'):
        options = ['static screen', 'automatic R2L scrolling', 'free side scrolling']
        toggle = ui.toggle({x:'' for x in options}, value='static screen')
        with ui.teleport(f'#{toggle.html_id} > button:nth-child(1) .q-btn__content'):
            ui.icon('check_box_outline_blank', size='xl')
        with ui.teleport(f'#{toggle.html_id} > button:nth-child(2) .q-btn__content'):
            ui.icon('trending_flat', size='xl')
        with ui.teleport(f'#{toggle.html_id} > button:nth-child(3) .q-btn__content'):
            ui.icon('swap_horiz', size='xl')
        with ui.row().classes('items-center gap-2 flex-nowrap'):
            ui.label('Project type: ')
            ui.label().bind_text_from(toggle, 'value')

        ui.label('Summary')
        with ui.column().classes('ml-8 gap-1'):
            with ui.row().classes('items-center gap-2 flex-nowrap'):
                ui.label('Amount of tiles available:')
                ui.badge('256', color='orange')
            with ui.row().classes('items-center gap-2 flex-nowrap'):
                ui.label('ROM size:')
                ui.badge('32K', color='green')
            with ui.row().classes('items-center gap-2 flex-nowrap'):
                ui.label('Page size:')
                ui.badge('16K', color='blue')
            with ui.row().classes('items-center gap-2 flex-nowrap'):
                ui.label('Framerate:')
                ui.badge('60/50Hz', color='red')

        ui.label('Settings')
        with ui.column().classes('ml-8 gap-1'):
            ui.label('Display engine')
            with ui.column().classes('ml-8 gap-1'):
                ui.checkbox('Reserve second pattern table in VRAM', on_change=lambda e: ui.notify(str(e.value)))
                with ui.column().classes('ml-8 gap-1'):
                    with ui.row().classes('items-center gap-2 flex-nowrap'):
                        ui.icon('warning', color='warning').classes('text-xl')
                        ui.label('This option can double the VRAM data transfer when updating tiles.')
                ui.checkbox('105 color mode', on_change=lambda e: ui.notify(str(e.value)))
                with ui.column().classes('ml-8 gap-1'):
                    with ui.row().classes('items-center gap-2 flex-nowrap'):
                        ui.icon('warning', color='warning').classes('text-xl')
                        ui.label('This option reduces the game frame rate by half and may cause flickery.')
                ui.checkbox('Detached pattern layers for each third of screen region', on_change=lambda e: ui.notify(str(e.value)))
                with ui.column().classes('ml-8 gap-1'):
                    with ui.row().classes('items-center gap-2 flex-nowrap'):
                        ui.icon('info', color='black').classes('text-xl')
                        ui.label('Select a different pattern table for each screen region if tiles don\'t repeat.')
                ui.checkbox('Force specific frame rate', on_change=lambda e: ui.notify(str(e.value)))
                with ui.column().classes('ml-8 gap-1'):
                    with ui.row().classes('items-center gap-2 flex-nowrap'):
                        ui.icon('warning', color='warning').classes('text-xl')
                        ui.label('Requires MSX2 or above.')

                ui.element('div').classes('h-8')
                ui.label('Amount of pixels to scroll')
                ui.radio([1, 2, 4, 8], value=8).props('inline')

            ui.label('Memory layout')
            with ui.column().classes('ml-8 gap-1'):
                ui.checkbox('MEGAROM', on_change=lambda e: ui.notify(str(e.value)))

    with ui.tab_panel('a'):
        ui.label('Infos')

ui.run()

