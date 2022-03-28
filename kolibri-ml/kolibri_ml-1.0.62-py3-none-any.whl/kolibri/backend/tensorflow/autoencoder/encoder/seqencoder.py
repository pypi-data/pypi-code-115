import numpy as np
import tensorflow as tf

from copy import copy
from kolibri.backend.tensorflow.layers import L


class SeqEncoder(tf.keras.Model):
    def __init__(self):
        super(SeqEncoder, self).__init__()


    @classmethod
    def get_default_hyper_parameters(cls):
        return {
                #            'layer_multiplyer': 2,
                'encoder': {
                    'hidden': {
                        'units': 40,
                        'activation': 'relu',
                        'type': "dense"
                    },
                    'latent': {
                        'units': 10,
                        'activation': 'relu',
                        'type': "dense"
                    },
                },
                'decoder': {
                    'hidden': {
                        'units': 40,
                        'activation': 'relu',
                        'type': "dense"
                    },
                }
            }


    def model(self, config_encoder):

        if len(self.input_dim)>1:
            input=L.Input(shape=self.input_dim, name='encoder_input')
        else:
            input = L.Input(shape=(self.input_dim,), name='encoder_input')

        encoded = input

        for unit_name in config_encoder:
            dict_param=config_encoder[unit_name]
            cell_type=dict_param.pop("type")
            dict_param["name"]=unit_name
            if cell_type=="dense":
                encoded = L.Dense(**dict_param)(encoded)
            elif cell_type in ["lstm", "gru"]:
                training=False
                if 'training' in dict_param:
                    training=dict_param.pop('training')
                lstm = L.LSTM(**dict_param) if cell_type=="lstm" else L.GRU(**dict_param)
                encoded=lstm(encoded, training=training)


        return tf.keras.Model(inputs=input,
                              outputs=encoded,
                              name='SeqEncoder')


if __name__ == "__main__":
    pass
