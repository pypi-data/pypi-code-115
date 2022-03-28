import numpy as np
import tensorflow as tf

from kolibri.backend.tensorflow.embeddings import Embedding
from kolibri.backend.tensorflow.layers import L


class SeqEncoder(tf.keras.Model):
    def __init__(self, input_dim, config_encoder):
        super(SeqEncoder, self).__init__()
        self.input_dim=input_dim
        self.cells=[]
        for unit_name in config_encoder:
            dict_param = config_encoder[unit_name]
            cell_type = dict_param.pop("type")
            dict_param["name"] = unit_name
            if cell_type == "dense":
                self.cells.append(L.Dense(**dict_param))
            elif cell_type in ["lstm", "gru"]:
                self.cells.append(L.LSTM(**dict_param) if cell_type == "lstm" else L.GRU(**dict_param))


    def call(self, x) -> np.ndarray:
        for cell in self.cells:
            x = cell(x)
        return x

    def model(self) -> tf.keras.Model:
        if len(self.input_dim)>1:
            self.iput_seq=L.Input(shape=self.input_dim, name='encoder_input')
        else:
            self.iput_seq = L.Input(shape=(self.input_dim,), name='encoder_input')


        return tf.keras.Model(inputs=self.iput_seq,
                              outputs=self.call(self.iput_seq),
                              name='GRUEncoder')


if __name__ == "__main__":
    pass
