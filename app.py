import os

from tileviewer import TileViewer


port = int(os.getenv("PORT", 7860))


TileViewer()

ui.run(
    host="0.0.0.0",
    port=port,
    title="My NiceGUI App",
)
