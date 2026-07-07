from nicegui import ui, app
from PIL import Image
import base64
from io import BytesIO
from common import run, add_handlers, file_to_base64
from fileloader import FileLoader


class TileViewer:
    zoom: int;
    selected_col = int;
    selected_row = int;
    image: Image;
    image64: str;

    def __init__(self, image: Image | None = None):
        self.zoom = 4
        self.selected_col = -1
        self.selected_row = -1
        self.build_ui()


    def build_ui(self):
        ui.add_head_html('<script src="/static/tileviewer.js"></script>', shared=True)
        with ui.column().classes('w-full h-screen') as parent:
            FileLoader(parent, self.load_image)
            ui.slider(
                min=1,
                max=16,
                value=self.zoom,
                step=1,
                on_change=lambda e: self.set_zoom(int(e.value)),
            )

            with ui.scroll_area().classes('w-full flex-1 border'):
                ui.html(
                    '<canvas id="tile_canvas"></canvas>'
                )

        ui.on("tile_clicked", self.on_tile_clicked)
        #ui.timer(0.1, self.initialize, once=True)


    def load_image(self, image: bytes):
        self.image = Image.open(BytesIO(image))
        buffer = BytesIO()
        self.image.save(buffer, format='PNG')
        self.image64 = file_to_base64(buffer)

        ui.run_javascript(f"""
            window.tileViewer.initialize({{
                canvasId: "tile_canvas",
                image: "{self.image64}",
                zoom: {self.zoom}
            }});
        """)


    def redraw(self):
        ui.run_javascript(f"""
            window.tileViewer.setState({{
                zoom: {self.zoom},
                selectedCol: {self.selected_col},
                selectedRow: {self.selected_row}
            }});
            window.tileViewer.draw();
        """)


    def set_zoom(self, zoom):
        self.zoom = zoom
        self.redraw()


    def on_tile_clicked(self, e):
        self.selected_col = e.args["col"]
        self.selected_row = e.args["row"]
        print(self.selected_col, self.selected_row)
        self.redraw()


@ui.page('/')
def main() -> None:
    add_handlers()
    #TileViewer(Image.open(IMAGE_FILE).convert('RGBA'))
    TileViewer()


if __name__ in {"__main__", "__mp_main__"}:
    from common import run
    run()
