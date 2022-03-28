import tensorflow
from keras import Model
from keras.layers import LSTM, Dense, Input, GRU, TimeDistributed

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
from kolibri.backend.tensorflow.autoencoder.encoder.seq_encoder import SeqEncoder
from kolibri.backend.tensorflow.autoencoder.decoder.seq_decoder import SeqDecoder
from copy import copy
from kolibri.backend.tensorflow.autoencoder.base_autoencoder import BaseAutoencoder


class SimpleAutoencoder(BaseAutoencoder):


    def __init__(self, hyper_parameters):

        super().__init__(hyper_parameters)

    @classmethod
    def get_default_hyper_parameters(cls):
        return {
#            'layer_multiplyer': 2,
            'encoder':{
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
            'decoder':{
                'hidden': {
                    'units': 40,
                    'activation': 'relu',
                    'type': "dense"
                },
            }
            }




    def build_model_arc(self):
        config_encoder = copy(self.hyper_parameters['encoder'])
        config_decoder = copy(self.hyper_parameters['decoder'])

        self.encoder=SeqEncoder(self.input_dim,config_encoder)
        self.encoder.model().summary()
        # instantiate decoder model

        self.decoder = SeqDecoder(config_decoder, self.input_dim[0])

        # autoencoder = encoder + decoder
        # instantiate autoencoder model
        input=self.encoder.iput_seq
        self.autoencoder = Model(input,
                                 self.decoder(self.encoder(input)),
                                 name='autoencoder')



if __name__ == "__main__":



    corpus = CreditCardFraud()
    train_x=corpus.X

    model = SimpleAutoencoder()
    model.build_model(train_x[:100])



    epochs = 4
    history = None
    model.fit(train_x[0:20000], epochs=epochs)

    model.evaluate(train_x[0:10000])

