import sys
import numpy as np
import cv2
from matplotlib import pyplot as plt

import random

def mostrar_imagen(arreglo_bidimensional, titulo_de_ventana=None):
    if not titulo_de_ventana:
        titulo_de_ventana = "%dx%d" % arreglo_bidimensional.shape[:2]

    assert isinstance(titulo_de_ventana, str)

    arreglo_bidimensional = arreglo_bidimensional.astype('uint8')
    cv2.imshow(titulo_de_ventana, arreglo_bidimensional)

    while cv2.getWindowProperty(titulo_de_ventana,
                                cv2.WND_PROP_VISIBLE) >= 1:
        if cv2.waitKeyEx(1000) == 27:
            cv2.destroyWindow(titulo_de_ventana)
            break

def guardar_imagen(arreglo_bidimensional, ruta_de_salida="../salida.png"):

    # Pasa encima de cualquier otro formato, xq si
    if not ruta_de_salida.endswith(".png"):
        ruta_de_salida += ".png"

    cv2.imwrite(ruta_de_salida, arreglo_bidimensional)
    return True

# Método para señalar componentes conexas
def colorear_componentes_conexas(componentes_etiquetadas):
    img = np.zeros((componentes_etiquetadas.size, 3), dtype="uint8")
    flat_cc = componentes_etiquetadas.flatten()

    colors = {}
    for label in np.unique(flat_cc):
        r = random.randint(63, 255)
        g = random.randint(63, 255)
        b = random.randint(63, 255)
        colors[label] = [r,g,b]

    for i in range(flat_cc.size):
        if flat_cc[i] > 0:
            img[i] = colors[flat_cc[i]]
    return img.reshape(componentes_etiquetadas.shape[0],
                      componentes_etiquetadas.shape[1],
                      3)

def add_alpha_channel(original, mask):
    b, g, r = cv2.split(original)
    alpha_channel = mask 
    original_alpha = cv2.merge([b, g, r, alpha_channel])
    return original_alpha

def progress_bar(max_value, current_value):
    if current_value == 0:
        sys.stdout.write("Processing...\n")
    bar = "=" * (current_value) + "-" * (max_value - current_value)
    sys.stdout.write('[%s] %d%s\r' % (
        bar, 
        int((current_value/max_value)*100), 
        "%")
        )
    if max_value == current_value:
        sys.stdout.write("\n")
    sys.stdout.flush()
