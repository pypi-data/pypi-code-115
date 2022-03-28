import tensorflow as tf

from kolibri.backend.tensorflow.layers import L

class SeqDecoder(tf.keras.Model):
    def __init__(self, decoder_params, ipput_size):
        super(SeqDecoder, self).__init__()
        return_sequences=False
        self.cells = []
        for unit_name in decoder_params:
            dict_param = decoder_params[unit_name]
            cell_type = dict_param.pop("type")
            dict_param["name"] = unit_name
            if cell_type == "dense":
                self.cells.append(L.Dense(**dict_param))
            elif cell_type in ["lstm", "gru"]:
                return_sequences = False if 'return_sequences' not in dict_param else dict_param['return_sequences']
                self.cells.append(L.LSTM(**dict_param) if cell_type == "lstm" else L.GRU(**dict_param))

        if return_sequences:
            self.fc = L.TimeDistributed(tf.keras.layers.Dense(1, name='output'))
        else:
            self.fc = tf.keras.layers.Dense(ipput_size, name='output')

    def call(self, enc_output):

        s = self.cells[0](enc_output)
        for cell in self.cells[1:]:
            s=cell(s)

        # Output shape == (batch size, vocab)
        output = self.fc(s)
        return output



if __name__ == "__main__":
    pass
