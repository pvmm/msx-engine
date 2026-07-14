import os

from fastapi import FastAPI, Request, Response
from common import add_handlers, run
from tileviewer import TileViewer
from nicegui import app, ui


port = int(os.getenv('PORT', 8080))
reload = bool(os.getenv('NICEGUI_RELOAD', 1))


@app.head('/')
async def root_head():
    return Response(status_code=200)


@ui.page('/')
def main() -> None:
    add_handlers()
    # load local file
    #TileViewer(Image.open(IMAGE_FILE).convert('RGBA'))
    TileViewer()


run(title='TileViwer 0.5.0',
    host='0.0.0.0',
    port=port,
    reload=reload,
)
