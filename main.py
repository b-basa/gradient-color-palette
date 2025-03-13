from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog
from typing import List, Tuple
import math
import numpy as np
from PIL import Image, ImageDraw

from config import *


@dataclass
class RGBColor:
    r: int
    b: int
    g: int

    def as_tuple(self):
        return (self.r, self.g, self.b)


@dataclass
class Area:
    x: int
    y: int
    width: int
    height: int


@dataclass
class FillColor:
    color: RGBColor
    area: Area


@dataclass
class GradientColor:
    start_color: RGBColor
    end_color: RGBColor
    area: Area


def main():
    input_png = filedialog.askopenfilename(filetypes=[("PNG Image", ".png")])
    input_palette_colors = get_palette(input_png)

    out_width = 2 * math.ceil((len(input_palette_colors) / OUT_COLOR_PER_COLUMN)) * OUT_COLOR_WIDTH
    out_height = OUT_COLOR_PER_COLUMN * OUT_COLOR_HEIGHT
    with Image.new("RGB", (out_width, out_height)) as img:
        out_img = generate_gradient_palette(img, input_palette_colors)

    out_img.save(OUT_FILE_NAME)


def get_palette(input_file: Path) -> List[RGBColor]:
    colors = []
    with Image.open(input_file) as img:
        img = img.convert("RGB")

        color_amount = img.width / IN_COLOR_WIDTH
        assert color_amount % 1 == 0

        color_amount = int(color_amount)

        for x in range(color_amount):
            pixel = img.getpixel((x * IN_COLOR_WIDTH, 0))
            colors.append(RGBColor(pixel[0], pixel[1], pixel[2]))

    return colors


def get_fill_colors(colors: List[RGBColor]):
    draw_x = 0
    draw_y = 0
    to_draw: List[FillColor] = []
    for i, c in enumerate(colors):
        is_last_in_column = (i + 1) % OUT_COLOR_PER_COLUMN == 0

        fill_area = Area(x=draw_x, y=draw_y, width=OUT_COLOR_WIDTH, height=OUT_COLOR_HEIGHT)
        fill_color = FillColor(color=c, area=fill_area)

        to_draw.append(fill_color)

        draw_y += OUT_COLOR_HEIGHT
        if is_last_in_column:
            draw_x += OUT_COLOR_WIDTH * 2
            draw_y = 0

    return to_draw


def draw_fill_colors(img: Image, colors: List[FillColor]):
    draw = ImageDraw.Draw(img)
    for fc in colors:
        draw.rectangle(
            xy=[
                (fc.area.x, fc.area.y),
                (fc.area.x + fc.area.width - 1, fc.area.y + fc.area.height),
            ],
            fill=fc.color.as_tuple(),
        )
    return img


def get_gradient_colors(colors: List[RGBColor]):
    draw_x = 0
    draw_y = 0
    to_draw: List[GradientColor] = []
    for i in range(len(colors) - 1):
        current_color = colors[i]
        next_color = colors[i + 1]

        is_last_in_column = (i + 1) % OUT_COLOR_PER_COLUMN == 0 or (i + 1) == len(colors)
        if is_last_in_column:
            draw_x += OUT_COLOR_WIDTH * 2
            draw_y = 0
            continue

        gradient_area = Area(
            x=draw_x + OUT_COLOR_WIDTH,
            y=draw_y + OUT_GRADIENT_OFFSET_Y,
            width=OUT_COLOR_WIDTH,
            height=OUT_COLOR_HEIGHT,
        )
        gc = GradientColor(start_color=current_color, end_color=next_color, area=gradient_area)

        to_draw.append(gc)

        draw_y += OUT_COLOR_HEIGHT

    return to_draw


def draw_gradient_colors(img: Image, colors: List[GradientColor]):
    for gc in colors:
        # Gradient matrix
        gradient = np.zeros((gc.area.height, gc.area.width, 3), np.uint8)

        # Fill R, G and B channels with linear gradient between two end colours
        for i in range(3):
            gradient[:, :, i] = np.linspace(
                gc.start_color.as_tuple()[i], gc.end_color.as_tuple()[i], gc.area.width, dtype=np.uint8
            ).reshape(
                (-1, 1)
            )  # Reshape to match the shape of the gradient array

        gradient_img = Image.fromarray(gradient)
        img.paste(gradient_img, (gc.area.x, gc.area.y))
    return img


def get_extra_colors(colors: List[RGBColor]):
    draw_x = 0
    draw_y = 0
    to_draw: List[FillColor] = []
    for i, c in enumerate(colors):
        is_last_in_column = (i + 1) % OUT_COLOR_PER_COLUMN == 0 or (i + 1) == len(colors)
        is_first_in_column = i % OUT_COLOR_PER_COLUMN == 0

        if is_first_in_column or is_last_in_column:
            if is_last_in_column:
                offset = OUT_GRADIENT_OFFSET_Y
            else:
                offset = 0

            fill_area = Area(
                x=draw_x + OUT_COLOR_WIDTH,
                y=draw_y + offset,
                width=OUT_COLOR_WIDTH,
                height=OUT_COLOR_HEIGHT // 2,
            )
            fill_color = FillColor(color=c, area=fill_area)
            to_draw.append(fill_color)

        draw_y += OUT_COLOR_HEIGHT
        if is_last_in_column:
            draw_x += OUT_COLOR_WIDTH * 2
            draw_y = 0

    return to_draw


def generate_gradient_palette(img: Image, colors: List[RGBColor]) -> Image:
    fill_colors = get_fill_colors(colors)
    draw_fill_colors(img, fill_colors)

    gradient_colors = get_gradient_colors(colors)
    draw_gradient_colors(img, gradient_colors)

    extra_colors = get_extra_colors(colors)
    draw_fill_colors(img, extra_colors)

    return img


if __name__ == "__main__":
    main()
