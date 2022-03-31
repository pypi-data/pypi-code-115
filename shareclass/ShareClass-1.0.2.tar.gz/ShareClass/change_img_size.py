from PIL import Image
import os


def produceImage(file_in, file_out):
    image = Image.open(file_in)
    if min(image.size) < 500:
        if image.size[0] >= image.size[1]:
            resized_image = image.resize((int(500*image.size[0]/image.size[1]), 500), Image.ANTIALIAS)
        else:
            resized_image = image.resize((500, int(500 * image.size[1] / image.size[0])), Image.ANTIALIAS)
        resized_image.save(file_out)


if __name__ == '__main__':
    pass