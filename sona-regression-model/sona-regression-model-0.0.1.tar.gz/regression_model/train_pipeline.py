import numpy as np
from config.core import config
from pipeline import gridsearch
from processing.data_manager import load_dataset, save_pipeline
from processing.features import get_data
from sklearn.model_selection import train_test_split
import joblib


def run_training() -> None:
    """Train the model."""

    # read training data
    dataset = load_dataset(file_name=config.app_config.training_data_file)

    data = get_data(dataset)
    # divide train and test
    X_train, X_test, y_train, y_test = train_test_split(
        data[config.model_config.features],  # predictors
        data[config.model_config.target],
        test_size=config.model_config.test_size,
        # we are setting the random seed here
        # for reproducibility
        random_state=config.model_config.random_state,
    )
    y_train = np.log(y_train)

    # fit model
    gridsearch.fit(X_train, y_train)

    joblib.dump(gridsearch.best_estimator_, r'C:\Users\P2818726\Desktop\Housing_Project_3.23.2022\grid.pkl')

    # persist trained model
    save_pipeline(pipeline_to_persist=gridsearch)


if __name__ == "__main__":
    run_training()
