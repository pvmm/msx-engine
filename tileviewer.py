from nicegui import ui
from PIL import Image
from io import BytesIO
import base64

IMAGE_FILE = 'image.png'


class TileViewer:

    def __init__(self):
        self.zoom = 4  # each source pixel becomes 4x4 screen pixels

        image = Image.open(IMAGE_FILE).convert('RGBA')

        buffer = BytesIO()
        image.save(buffer, format='PNG')
        self.image_data = base64.b64encode(buffer.getvalue()).decode()

        with ui.column().classes('w-full h-screen'):

            ui.slider(
                min=1,
                max=16,
                value=self.zoom,
                step=1,
                on_change=self.change_zoom,
            ).props('label-always')

            with ui.scroll_area().classes('w-full flex-1 border'):
                ui.html('<canvas id="tile_canvas"></canvas>')

        ui.timer(0.1, self.redraw, once=True)

    def change_zoom(self, e):
        self.zoom = int(e.value)
        self.redraw()

    def redraw(self):

        ui.run_javascript(f"""
const canvas = document.getElementById('tile_canvas');
const ctx = canvas.getContext('2d');

const img = new Image();

img.onload = function() {{

    const zoom = {self.zoom};

    canvas.width = img.width * zoom;
    canvas.height = img.height * zoom;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    ctx.imageSmoothingEnabled = false;

    // Draw enlarged image
    ctx.drawImage(
        img,
        0,
        0,
        canvas.width,
        canvas.height
    );

    // Draw grid
    ctx.strokeStyle = '#888';
    ctx.lineWidth = 1;
    ctx.beginPath();

    // Vertical lines
    for (let x = 0; x <= img.width; x += 8) {{
        const xx = x * zoom + 0.5;
        ctx.moveTo(xx, 0);
        ctx.lineTo(xx, canvas.height);
    }}

    // Horizontal lines
    for (let y = 0; y <= img.height; y += 8) {{
        const yy = y * zoom + 0.5;
        ctx.moveTo(0, yy);
        ctx.lineTo(canvas.width, yy);
    }}

    ctx.stroke();
}};

img.src = 'data:image/png;base64,{self.image_data}';
""")


TileViewer()

ui.run()
