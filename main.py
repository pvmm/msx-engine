from nicegui import ui
from tile_editor import TileEditor

tiles_changed = False
target_options = ['MSX1', 'MSX2 or above']
target = target_options[0]
available_tiles = 256
scrolling_tiles = available_tiles
palette = False
r18_hardware_scroll = False
megarom = False

frame_rate_options = ['60Hz', '50Hz']
force_frame_rate = False
frame_rate = frame_rate_options[0]

rom_options = ['8K', '16K']
rom_type = rom_options[0]

_105_color_mode = False

fps_options = ['frame rate', 'half the frame rate', 'quarter the frame rate']
fps = 0

scroll_pixels = 8

project_types = ['static screen', 'automatic R2L scrolling', 'free side scrolling']
project_type = project_types[0]
project_changed = True


async def change_project_type(e):
    global project_changed, project_type
    if e.value != project_type and tiles_changed:
        with ui.dialog() as dialog, ui.card():
            ui.label('Changing project type will delete extra tiles. Are you sure?')
            with ui.row():
                ui.button('Yes', on_click=lambda: dialog.submit(True))
                ui.button('No', on_click=lambda: dialog.submit(False))
        result = await dialog
    elif not tiles_changed:
        result = True
    if result:
        global r18_checkbox, scroll_pixels_radio
        project_type = e.value
        if project_type != 'static screen':
            r18_checkbox.enable()
            scroll_pixels_radio.enable()
        else:
            r18_checkbox.disable()
            scroll_pixels_radio.disable()
        ui.notify(f'Project type changed to {project_type}')
    else:
        e.sender.set_value(project_type)


def reserve_second_pattern_table(e):
    global available_tiles, scroll_pixels, r18_hardware_scroll
    global scrolling_tiles_badge 
    print('e',e)
    if e.value:
        available_tiles *= 2
    else:
        available_tiles //= 2
    if not r18_hardware_scroll:
        scrolling_tiles = available_tiles // (8 // scroll_pixels)
    else:
        scrolling_tiles = available_tiles
    ui.notify(f'Amount of tiles available: {scrolling_tiles}')
    scrolling_tiles_badge.set_text(scrolling_tiles)


def set_105_color_mode(e):
    global available_tiles, fps_options, fps
    global fps_badge, second_pattern_checkbox
    if e.value:
        fps += 1
        second_pattern_checkbox.disable()
        available_tiles //= 2
    else:
        fps -= 1
        second_pattern_checkbox.enable()
        available_tiles *= 2
    second_pattern_checkbox.value = e.value
    fps_badge.set_text(fps_options[fps])


def detach_pattern_layers(e):
    global available_tiles, scrolling_tiles, scroll_pixels, r18_hardware_scroll
    global scrolling_tiles_badge 
    if e.value:
        available_tiles *= 3
    else:
        available_tiles //= 3
    if not r18_hardware_scroll:
        scrolling_tiles = available_tiles // (8 // scroll_pixels)
    else:
        scrolling_tiles = available_tiles
    ui.notify(f'Amount of tiles available: {scrolling_tiles}')
    scrolling_tiles_badge.set_text(scrolling_tiles)


def update_fps_badge():
    global fps_options, frame_rate
    global fps_badge
    with ui.row().classes('items-center gap-2 flex-nowrap'):
        ui.label('Frames per second:')
        fps_badge = ui.badge(fps_options[fps], color='magenta')
        if frame_rate != 'automatic':
            ui.label(f'({frame_rate})')


def force_specific_frame_rate(e):
    global target_options, target, frame_rate
    global frame_rate_badge
    if e.value:
        frame_rate_badge.set_text(frame_rate_radio.value)
        frame_rate_radio.enable()
    else:
        frame_rate_radio.disable()
    target = target_options[1 if e.value else 0]
    frame_rate = frame_rate_radio.value
    target_badge.set_text(target)
    frame_rate_badge.visible = e.value
    ui.notify(f'Target platform set to {target}')


def change_frame_rate(e):
    global frame_rate_radio
    frame_rate_badge.visible = True
    frame_rate_badge.set_text(frame_rate_radio.value)


def set_scroll_in_pixels(e):
    global scroll_pixels, scrolling_tiles, available_tiles
    global scrolling_tiles_badge, r18_hardware_scroll_checkbox
    if e.value != scroll_pixels and not r18_hardware_scroll:
        tmp = available_tiles // (8 // e.value)
        if scrolling_tiles != tmp:
            ui.notify(f'Amount of tiles available: {scrolling_tiles}')
        scrolling_tiles = tmp
        scroll_pixels = e.value
    scrolling_tiles_badge.set_text(scrolling_tiles)


def allow_palette_change(e):
    global target_options, target, palette
    palette = e.value
    target = target_options[1 if e.value else 0]
    target_badge.set_text(target)
    ui.notify(f'Target platform set to {target}')


def set_r18(e):
    global target_options, target, r18_hardware_scroll, scrolling_tiles, available_tiles, scroll_pixels
    global scrolling_tiles_badge
    r18_hardware_scroll = e.value
    if e.value:
        scrolling_tiles = available_tiles
    else:
        scrolling_tiles = available_tiles // (8 // scroll_pixels)
    target = target_options[1 if e.value else 0]
    target_badge.set_text(target)
    scrolling_tiles_badge.set_text(scrolling_tiles)
    ui.notify(f'Amount of tiles available: {scrolling_tiles}')
    ui.notify(f'Target platform set to {target}')


def toggle_megarom(e):
    pass


def header(text):
    ui.element('div')
    return ui.label(text)


scrolling_tiles_badge = None
frame_rate_badge = None
frame_rate_radio = None
fps_badge = None
target_badge = None
second_pattern_checkbox = None
r18_checkbox = None
scroll_pixels_radio = None

with ui.tabs() as tabs:
    ui.tab('p', label='Project', icon='rocket_launch')
    ui.tab('t', label='Tileset', icon='apps')
    ui.tab('a', label='About', icon='info')

with ui.tab_panels(tabs, value='p').classes('w-full'):
    with ui.tab_panel('p'):
        toggle = ui.toggle({x:'' for x in project_types}, value=project_type, on_change=lambda e: change_project_type(e))
        with ui.teleport(f'#{toggle.html_id} > button:nth-child(1) .q-btn__content'):
            ui.icon('check_box_outline_blank', size='xl')
        with ui.teleport(f'#{toggle.html_id} > button:nth-child(2) .q-btn__content'):
            ui.icon('trending_flat', size='xl')
        with ui.teleport(f'#{toggle.html_id} > button:nth-child(3) .q-btn__content'):
            ui.icon('swap_horiz', size='xl')
        with ui.row().classes('items-center gap-2 flex-nowrap'):
            ui.label('Project type: ')
            ui.label().bind_text_from(toggle, 'value')

        header('Summary')
        with ui.column().classes('ml-8 gap-1'):
            with ui.row().classes('items-center flex-nowrap'):
                ui.label('Target platform:')
                target_badge = ui.badge(target, color='blue')
            with ui.row().classes('items-center flex-nowrap'):
                ui.label('ROM size:')
                ui.badge('32K', color='green')
            with ui.row().classes('items-center flex-nowrap'):
                ui.label('Page size:')
                ui.badge('16K', color='red')
            with ui.row().classes('items-center flex-nowrap'):
                ui.label('Amount of tiles available:')
                scrolling_tiles_badge = ui.badge(available_tiles, color='orange')
            with ui.row().classes('items-center flex-nowrap'):
                ui.label('Frames per second:')
                fps_badge = ui.badge(fps_options[fps], color='brown')
                frame_rate_badge = ui.badge(frame_rate, color='brown')
                frame_rate_badge.visible = force_frame_rate

        header('Settings')
        with ui.column().classes('ml-8'):
            header('Display engine')
            with ui.column().classes('ml-8'):
                second_pattern_checkbox = ui.checkbox('Reserve second pattern table in VRAM for next frame', on_change=lambda e: reserve_second_pattern_table(e))
                with ui.column().classes('ml-8'):
                    with ui.row().classes('items-center flex-nowrap'):
                        ui.icon('warning', color='warning').classes('text-xl')
                        ui.label('This option may double the required VRAM data transfer when updating tile patterns dinamically.')
                ui.checkbox('105 color mode', on_change=lambda e: set_105_color_mode(e))
                with ui.column().classes('ml-8'):
                    with ui.row().classes('items-center flex-nowrap'):
                        ui.icon('warning', color='warning').classes('text-xl')
                        ui.label('This option reduces color clash but also reduces the game frame rate by half and may cause flicker.')
                ui.checkbox('Detach pattern layers for each third of screen region', on_change=lambda e: detach_pattern_layers(e))
                with ui.column().classes('ml-8'):
                    with ui.row().classes('items-center flex-nowrap'):
                        ui.icon('info', color='black').classes('text-xl')
                        ui.label('Select a distinct pattern table for each screen region if tiles are different in each region.')

                header('MSX2 features')
                with ui.column().classes('ml-8'):
                    ui.checkbox('Allow palette change', on_change=lambda e: allow_palette_change(e))
                    r18_checkbox = ui.checkbox('R#18 hardware scroll', on_change=lambda e: set_r18(e)).disable()
                    with ui.column().classes('ml-8'):
                        with ui.row().classes('items-center flex-nowrap'):
                            ui.icon('info', color='black').classes('text-xl')
                            ui.label('This option will cause visible artifacts on the left and right edges of the screen.')

                    ui.checkbox('Force specific frame rate', on_change=lambda e: force_specific_frame_rate(e))
                    with ui.column().classes('ml-8'):
                        frame_rate_radio = ui.radio(frame_rate_options, value=frame_rate_options[0], on_change=lambda e: change_frame_rate(e)).props('inline').disable()


                header('Amount of pixels to scroll each frame')
                with ui.column().classes('ml-8'):
                    scroll_pixels_radio = ui.radio([1, 2, 4, 8], value=8, on_change=lambda e: set_scroll_in_pixels(e)).props('inline').disable()

            ui.label('Memory layout')
            with ui.column().classes('ml-8'):
                ui.checkbox('ROM bank switching', on_change=lambda e: toggle_megarom(e))
                with ui.column().classes('ml-8'):
                    ui.radio(rom_options, value=rom_options[0], on_change=lambda e: change_frame_rate(e)).props('inline').disable()

    with ui.tab_panel('t'):
        TileEditor(ui.column(), 8)

    with ui.tab_panel('a'):
        ui.label('Infos')


ui.run()

