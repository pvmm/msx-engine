class TileViewer {
    initialize(options) {
        this.canvas = document.getElementById(options.canvasId);
        this.ctx = this.canvas.getContext("2d");
        this.ctx.imageSmoothingEnabled = false;
        this.zoom = options.zoom;
        this.selectedCol = -1;
        this.selectedRow = -1;
        this.image = new Image();
        this.image.onload = () => {
            this.draw();
        };
        this.image.src = options.image;
        this.installEvents();
    }

    setState(state) {
        this.zoom = state.zoom;
        this.selectedCol = state.selectedCol;
        this.selectedRow = state.selectedRow;
    }

    draw() {
        this.canvas.width = this.image.width * this.zoom;
        this.canvas.height = this.image.height * this.zoom;
        this.drawImage();
        this.drawGrid();
        this.drawSelection();
    }

    drawImage() {
        this.ctx.drawImage(
            this.image,
            0,
            0,
            this.canvas.width,
            this.canvas.height
        );
    }

    drawGrid() {
        this.ctx.strokeStyle = "#808080";
        this.ctx.lineWidth = 1;
        this.ctx.beginPath();

        for (let x = 0; x <= this.image.width; x += 8) {
            let xx = x * this.zoom + 0.5;
            this.ctx.moveTo(xx, 0);
            this.ctx.lineTo(xx, this.canvas.height);
        }

        for (let y = 0; y <= this.image.height; y += 8) {
            let yy = y * this.zoom + 0.5;
            this.ctx.moveTo(0, yy);
            this.ctx.lineTo(this.canvas.width, yy);
        }

        this.ctx.stroke();
    }

    drawSelection() {
        if (this.selectedCol < 0)
            return;

        this.ctx.strokeStyle = "#ff0000";
        this.ctx.lineWidth = 2;
        this.ctx.strokeRect(
            this.selectedCol * 8 * this.zoom,
            this.selectedRow * 8 * this.zoom,
            8 * this.zoom,
            8 * this.zoom
        );
    }

    canvasToTile(x, y) {
        return {
            col: Math.floor(x / (8 * this.zoom)),
            row: Math.floor(y / (8 * this.zoom))
        };
    }

    installEvents() {
        this.canvas.addEventListener("click", e => {
            const rect = this.canvas.getBoundingClientRect();
            const tile = this.canvasToTile(
                e.clientX - rect.left,
                e.clientY - rect.top
            );
            emitEvent("tile_clicked", tile);
        });
    }
}

window.tileViewer = new TileViewer();
