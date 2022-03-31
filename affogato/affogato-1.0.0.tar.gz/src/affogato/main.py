from affogato.loss import CrossEntropy
from affogato.layer import Dropout, Flatten
import numpy as np
from affogato.activation import ReLU, Sigmoid
from affogato.layer import Dense
from affogato.optimizer import SGD

from affogato.model import Model


def main():
    # data = pd.read_csv("c:/files/data.csv")
    # # data = (data-data.mean())/data.std()
    # data["quality"] = data["quality"].div(data["quality"].max())
    # rel_data = data.iloc[0:4897,0:11]
    # rel_data = (rel_data-rel_data.mean())/rel_data.std()
    # rel_data = rel_data.to_numpy()

    # # rel_data = [rel_data[n] / rel_data[n] for n in range(rel_data)]
    # good = [(np.array([rel_data[n]]), np.array([[data["quality"][n]]])) for n in range(len(rel_data))]
    data = [
        (np.array([[0., 1.]]), np.array([[1.]])),
        (np.array([[1., 0]]), np.array([[1.]])),
        (np.array([[1., 1.]]), np.array([[0.]])),
        (np.array([[0., 0.]]), np.array([[0.]])),
        
    ]
    print(data)

    model = Model((1, 2))
    model.add(Dense(8, ReLU())) 
    model.add(Dropout(0.4))
    model.add(Dense(1, Sigmoid()))
    model.compile()
    
    opt = SGD(model.parameters, learning_rate=0.05) 
    loss_history = model.fit(data*60, opt, verbose=True, num_epochs=100)
    model.graph_history()
    
    print()
    print()
    print()
    print(f"{model.predict(data[1][0]):} true:", data[1][1])
    print(f"{model.predict(data[0][0]):} true:", data[0][1])
    print(f"{model.predict(data[2][0]):} true:", data[2][1])
    print(f"{model.predict(data[3][0]):} true:", data[3][1])
    # print(f"{model.predict(np.array([rel_data[1]])):} true:", data["quality"][1])
    # print(f"{model.predict(np.array([rel_data[278]])):} true:", data["quality"][278])
    # print(f"{model.predict(np.array([rel_data[13]])):} true:", data["quality"][13])
    # print(f"{model.predict(np.array([rel_data[17]])):} true:", data["quality"][17])
    


    # for i, layer in enumerate(model.layers):
    #     print(f"{i = }")
    #     print(f"weights = \n{layer.weights.values}")
    #     print(f"bias = \n{layer.bias.values}")
    
    print(f"loss at start = {loss_history[0]}")
    print(f"loss at end = {loss_history[-1]}")

if __name__ == '__main__':    
    main()
