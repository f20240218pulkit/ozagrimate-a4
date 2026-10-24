"""Tiny diagram helper: emits the same drawing as SVG and high-resolution PNG.

Palette and font follow the team's Container_View.svg.
"""
from PIL import Image, ImageDraw, ImageFont
from xml.sax.saxutils import escape

INK, LINE, BORDER = "#183047", "#486174", "#42647e"
BLUE, GREEN, GREY, BROWN, BOUNDARY = "#d9ebfa", "#e3f0df", "#e9edf1", "#eee8e3", "#f7fafc"
PLANNED = "#fbf5e6"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
OBLIQUE = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf"


class Canvas:
    def __init__(self, width, height):
        self.w, self.h = width, height
        self.svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
                    '<rect width="100%" height="100%" fill="white"/>']
        self.img = Image.new("RGB", (width, height), "white")
        self.d = ImageDraw.Draw(self.img)
        self._fonts = {}

    def font(self, size, weight="normal"):
        key = (size, weight)
        if key not in self._fonts:
            path = {"bold": BOLD, "italic": OBLIQUE}.get(weight, FONT)
            self._fonts[key] = ImageFont.truetype(path, size)
        return self._fonts[key]

    # --- primitives ---------------------------------------------------------------
    def rect(self, x, y, w, h, fill, stroke=BORDER, width=2, dashed=False):
        dash = ' stroke-dasharray="14 9"' if dashed else ""
        self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"{dash}/>')
        self.d.rectangle([x, y, x + w, y + h], fill=fill)
        if dashed:
            self._dashed([(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)], stroke, width)
        else:
            self.d.rectangle([x, y, x + w, y + h], outline=stroke, width=width)

    def text(self, x, y, s, size=19, weight="normal", anchor="middle", fill=INK):
        fw = {"bold": ' font-weight="700"', "italic": ' font-style="italic"'}.get(weight, ' font-weight="400"')
        self.svg.append(f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="DejaVu Sans, sans-serif" '
                        f'font-size="{size}"{fw} fill="{fill}">{escape(s)}</text>')
        f = self.font(size, weight)
        tw = self.d.textlength(s, font=f)
        tx = x - tw / 2 if anchor == "middle" else x - tw if anchor == "end" else x
        self.d.text((tx, y), s, font=f, fill=fill, anchor="ls")
        return tw

    def text_width(self, s, size=19, weight="normal"):
        return self.d.textlength(s, font=self.font(size, weight))

    def _dashed(self, pts, color, width, dash=14, gap=9):
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
            if length == 0:
                continue
            ux, uy, t = (x2 - x1) / length, (y2 - y1) / length, 0
            while t < length:
                e = min(t + dash, length)
                self.d.line([(x1 + ux * t, y1 + uy * t), (x1 + ux * e, y1 + uy * e)], fill=color, width=width)
                t = e + gap

    def arrow(self, pts, color=LINE, width=2, dashed=False, head=True, open_head=False):
        dash = ' stroke-dasharray="14 9"' if dashed else ""
        p = " ".join(f"{x},{y}" for x, y in pts)
        self.svg.append(f'<polyline points="{p}" fill="none" stroke="{color}" stroke-width="{width}"{dash}/>')
        if dashed:
            self._dashed(pts, color, width)
        else:
            self.d.line(pts, fill=color, width=width, joint="curve")
        if head:
            (x1, y1), (x2, y2) = pts[-2], pts[-1]
            length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
            ux, uy = (x2 - x1) / length, (y2 - y1) / length
            s = 16
            a = (x2 - ux * s - uy * s * 0.55, y2 - uy * s + ux * s * 0.55)
            b = (x2 - ux * s + uy * s * 0.55, y2 - uy * s - ux * s * 0.55)
            if open_head:
                self.svg.append(f'<polyline points="{a[0]:.1f},{a[1]:.1f} {x2},{y2} {b[0]:.1f},{b[1]:.1f}" fill="none" stroke="{color}" stroke-width="{width}"/>')
                self.d.line([a, (x2, y2), b], fill=color, width=width)
            else:
                self.svg.append(f'<polygon points="{a[0]:.1f},{a[1]:.1f} {x2},{y2} {b[0]:.1f},{b[1]:.1f}" fill="{color}"/>')
                self.d.polygon([a, (x2, y2), b], fill=color)

    def label(self, x, y, lines, size=17, weight="normal", anchor="middle", bg="white"):
        """Multi-line relationship label with a background so it stays readable over lines."""
        if isinstance(lines, str):
            lines = [lines]
        lh = size + 6
        widths = [self.text_width(s, size, weight) for s in lines]
        w = max(widths) + 14
        h = lh * len(lines) + 6
        left = x - w / 2 if anchor == "middle" else x - 7 if anchor == "start" else x - w + 7
        if bg:
            self.svg.append(f'<rect x="{left:.1f}" y="{y - size - 3:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{bg}"/>')
            self.d.rectangle([left, y - size - 3, left + w, y - size - 3 + h], fill=bg)
        for i, s in enumerate(lines):
            self.text(x, y + i * lh, s, size, weight, anchor)

    # --- C4 element ------------------------------------------------------------------
    def element(self, x, y, w, h, title, tag, desc, fill=BLUE, dashed=False):
        self.rect(x, y, w, h, fill, dashed=dashed)
        cx = x + w / 2
        self.text(cx, y + 38, title, 23, "bold")
        self.text(cx, y + 64, tag, 17)
        for i, line in enumerate(desc):
            self.text(cx, y + 96 + i * 26, line, 19)

    def save(self, base):
        self.svg.append("</svg>")
        with open(base + ".svg", "w") as f:
            f.write("\n".join(self.svg))
        self.img.save(base + ".png", dpi=(200, 200))
