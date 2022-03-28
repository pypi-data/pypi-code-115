import tensorflow
from keras import Model
from keras.layers import LSTM, Dense, Input, GRU, TimeDistributed

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
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

        if len(self.input_dim)>1:
            input=Input(shape=self.input_dim, name='encoder_input')
        else:
            input = Input(shape=(self.input_dim,), name='encoder_input')

        encoded = input

        # Construct encoder layers
        config_encoder=copy(self.hyper_parameters['encoder'])
        nb_units=0
        for unit_name in config_encoder:
            dict_param=config_encoder[unit_name]
            cell_type=dict_param.pop("type")
            dict_param["name"]=unit_name
            nb_units=dict_param["units"]
            if cell_type=="dense":
                encoded = Dense(**dict_param)(encoded)
            elif cell_type in ["lstm", "gru"]:
                training=False
                if 'training' in dict_param:
                    training=dict_param.pop('training')
                lstm = LSTM(**dict_param) if cell_type=="lstm" else GRU(**dict_param)
                encoded=lstm(encoded, training=training)

        # Construct decoder layers
        # The decoded is connected to the encoders, whereas the decoder is not
        config_decoder=copy(self.hyper_parameters['decoder'])

        if len(self.input_dim) > 1:
            decoder_input=encoded#RepeatVector(self.input_dim[0])(encoded)
        else:
            decoder_input = Input(shape=(nb_units,), name='decoder_input')

        decoded=decoder_input
        return_sequences=False
        for unit_name in config_decoder:
            dict_param = config_decoder[unit_name]
            cell_type=dict_param.pop("type")
            dict_param["name"]=unit_name
            if cell_type=="dense":
                decoded=Dense(**dict_param)(decoded)
            elif cell_type in ["lstm", "gru"]:
                training = None
                return_sequences = False if 'return_sequences' not in dict_param else dict_param['return_sequences']

                if 'training' in dict_param:
                    training = dict_param.pop('training')
                lstm = LSTM(**dict_param) if cell_type == "lstm" else GRU(**dict_param)
                decoded = lstm(decoded, training=training)

        if return_sequences:
            decoded = TimeDistributed(tensorflow.keras.layers.Dense(1, name='output'))(decoded)
        else:
            decoded = Dense(self.input_dim[0], name='output')(decoded)

        self.encoder = Model(inputs=input, outputs=encoded)
        self.encoder.summary()
        # instantiate decoder model

        self.decoder = Model(decoder_input, decoded, name='decoder')
        self.decoder.summary()
        # autoencoder = encoder + decoder
        # instantiate autoencoder model
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

