"""
Funzioni aggiuntive per creare grafiche primitive (ad esempio bitmap)
"""

from __future__ import annotations

from pytamaro.it import Grafica
from pytamaro_extra.primitives import bitmap as original_bitmap


def bitmap(percorso_file: str, pixel_per_unita: int = 1) -> Grafica:
    """
    Carica un'immagine bitmap da file (ad esempio, un file PNG).

    :param percorso_file: percorso al file, incluso il nome del file e l'estensione
    :param pixel_per_unita: quanti pixel corrispondono a un'unità nel nostro dominio
           (ha come valore predefinito 1, che significa che 1 pixel nell'immagine
           corrisponderà esattamente a 1 unità nella grafica risultante)
    :returns: l'immagine caricata come grafica
    """
    return original_bitmap(percorso_file, pixel_per_unita)
