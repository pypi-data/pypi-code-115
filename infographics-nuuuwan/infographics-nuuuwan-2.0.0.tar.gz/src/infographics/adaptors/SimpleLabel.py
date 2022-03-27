

class SimpleLabel:
    def __init__(self, get_label_label):
        self.get_label_label = get_label_label

    def get_label(self, palette, id, cxy, rxy):
        label = self.get_label_label(id)
        rx, ry = rxy
        font_size = palette.actual_width * rx / len(label) / 16
        return palette.draw_text(
            label,
            cxy,
            font_size,
        )
