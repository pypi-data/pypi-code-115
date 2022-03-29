from . import WMLDeployment
import argparse
import sys
import pandas as pd
import shutil
import tempfile
import tensorflow as tf
  
class MulticlassIrisTF(WMLDeployment):
    def __init__(self,facts_client,is_cp4d:bool=False):
        super (MulticlassIrisTF,self).__init__(name="Spark Iris TF",
            asset_name="Spark Iris TF",facts_client=facts_client,is_cp4d=is_cp4d)


    def load_data(self, y_name="Species"):
        """Returns the iris dataset as (train_x, train_y), (test_x, test_y)."""

            
        TRAIN_URL = "http://download.tensorflow.org/data/iris_training.csv"
        TEST_URL = "http://download.tensorflow.org/data/iris_test.csv"

        CSV_COLUMN_NAMES = ["SepalLength", "SepalWidth", "PetalLength", "PetalWidth", "Species"]
        SPECIES = ["Setosa", "Versicolor", "Virginica"]
        
        train_path = tf.keras.utils.get_file(TRAIN_URL.split("/")[-1], TRAIN_URL)
        test_path = tf.keras.utils.get_file(TEST_URL.split("/")[-1], TEST_URL)

        train = pd.read_csv(train_path, names=CSV_COLUMN_NAMES, header=0)
        train_x, train_y = train, train.pop(y_name)

        test = pd.read_csv(test_path, names=CSV_COLUMN_NAMES, header=0)
        test_x, test_y = test, test.pop(y_name)

        return (train_x, train_y), (test_x, test_y)

    def train_input_fn(self, features, labels, batch_size):
        """An input function for training"""
        # Convert the inputs to a Dataset.
        dataset = tf.data.Dataset.from_tensor_slices((dict(features), labels))

        # Shuffle, repeat, and batch the examples.
        dataset = dataset.shuffle(1000).repeat().batch(batch_size)

        # Return the dataset.
        return dataset

    def eval_input_fn(self, features, labels, batch_size):
        """An input function for evaluation or prediction"""
        features = dict(features)
        if labels is None:
            # No labels, use only features.
            inputs = features
        else:
            inputs = (features, labels)

        # Convert the inputs to a Dataset.
        dataset = tf.data.Dataset.from_tensor_slices(inputs)

        # Batch the examples
        assert batch_size is not None, "batch_size must not be None"
        dataset = dataset.batch(batch_size)

        # Return the dataset.
        return dataset
    
    
    def train_model(self):
        
        (train_x, train_y), (test_x, test_y) = self.load_data()
        my_feature_columns = []
        for key in train_x.keys():
            my_feature_columns.append(tf.feature_column.numeric_column(key=key))

        # Two hidden layers of 10 nodes each.
        hidden_units = [10, 10]

        # Build 2 hidden layer DNN with 10, 10 units respectively.
        classifier = tf.estimator.DNNClassifier(
            feature_columns=my_feature_columns,
            hidden_units=hidden_units,
            # The model must choose between 3 classes.
            n_classes=3,
        )

        classifier = tf.estimator.DNNClassifier(
        feature_columns=my_feature_columns,
        hidden_units=hidden_units,
        # The model must choose between 3 classes.
        n_classes=3,
        )

        # Train the Model.
        classifier.train(
            input_fn=lambda: self.train_input_fn(train_x, train_y, 100),
            steps=380,
        )


class MulticlassIrisKeras(WMLDeployment):
    def __init__(self,facts_client,is_cp4d:bool=False):
        super (MulticlassIrisKeras,self).__init__(name="Spark Iris Keras",
            asset_name="Spark Iris Keras",facts_client=facts_client,is_cp4d=is_cp4d)

    def train_model(self):
        
        import numpy as np
        from tensorflow import keras
        from tensorflow.keras.datasets import reuters
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import Dense, Dropout, Activation
        from tensorflow.keras.preprocessing.text import Tokenizer


        max_words = 1000
        batch_size = 32
        epochs = 5

        # save np.load
        np_load_old = np.load

        # modify the default parameters of np.load
        np.load = lambda *a,**k: np_load_old(*a, allow_pickle=True)

        print("Loading data...")
        (x_train, y_train), (x_test, y_test) = reuters.load_data(num_words=max_words, test_split=0.2)

        np.load = np_load_old

        print(len(x_train), "train sequences")
        print(len(x_test), "test sequences")

        num_classes = np.max(y_train) + 1
        print(num_classes, "classes")

        print("Vectorizing sequence data...")
        tokenizer = Tokenizer(num_words=max_words)
        x_train = tokenizer.sequences_to_matrix(x_train, mode="binary")
        x_test = tokenizer.sequences_to_matrix(x_test, mode="binary")
        print("x_train shape:", x_train.shape)
        print("x_test shape:", x_test.shape)

        print("Convert class vector to binary class matrix " "(for use with categorical_crossentropy)")
        y_train = keras.utils.to_categorical(y_train, num_classes)
        y_test = keras.utils.to_categorical(y_test, num_classes)
        print("y_train shape:", y_train.shape)
        print("y_test shape:", y_test.shape)

        print("Building model...")
        model = Sequential()
        model.add(Dense(512, input_shape=(max_words,)))
        model.add(Activation("relu"))
        model.add(Dropout(0.5))
        model.add(Dense(num_classes))
        model.add(Activation("softmax"))

        model.compile(loss="categorical_crossentropy", optimizer="adam", metrics=["accuracy"])

        history = model.fit(
        x_train, y_train, batch_size=batch_size, epochs=epochs, verbose=1,validation_data=(x_test, y_test), validation_split=0.1
            )