# ======================
# -*- coding:utf-8 -*-
# @author:Beall
# @time  :2022/3/2 17:57
# @file  :python添加水印.py
# ======================
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont


def add_text(text, in_img_path, out_img_path):
    try:
        im = Image.open(in_img_path)
        font = ImageFont.truetype('C:/Windows/Fonts/simsun.ttc', 24)
        draw = ImageDraw.Draw(im)
        draw.text((im.size[0] * 0.03, im.size[1] * 0.03), text, fill=(33, 33, 33), font=font)
        im.save(out_img_path)
    except Exception as e:
        print(f'程序错误: {e}')
        pass


def add_logo(water_mark, in_img_path, out_img_path):
    water_mark = Image.open(water_mark)
    image_file = Image.open(in_img_path)
    layer = Image.new('RGBA', image_file.size, (0, 0, 0, 0))
    layer.paste(water_mark, (int(image_file.size[0] * 0.04), int(image_file.size[1] * 0.03)))
    out = Image.composite(layer, image_file, layer)
    out.save(out_img_path)


if __name__ == '__main__':
    pass
