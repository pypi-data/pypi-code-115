# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------

"""Utility functions to write the final model and checkpoints during training"""

import logging
import os
import pandas as pd

from azureml.automl.core.shared.constants import MLFlowLiterals, RUN_ID_OUTPUT_PATH
from azureml.automl.dnn.nlp.common.constants import OutputLiterals, SystemSettings
from azureml.automl.dnn.nlp.classification.multilabel.model_wrapper import ModelWrapper
from azureml.core.run import Run
from azureml.train.automl.runtime._azureautomlruncontext import AzureAutoMLRunContext

logger = logging.getLogger(__name__)


def save_model_wrapper(run: Run,
                       model: ModelWrapper,
                       save_mlflow: bool = True) -> str:
    """
    Save a model to outputs directory.

    :param run: The current run.
    :param model: Trained model.
    :param save_mlflow: Whether to save using mlflow.
    :return: The model path.
    """
    os.makedirs(OutputLiterals.OUTPUT_DIR, exist_ok=True)
    model_path = os.path.join(OutputLiterals.OUTPUT_DIR, OutputLiterals.MODEL_FILE_NAME)

    # Save the model
    run_ctx = AzureAutoMLRunContext(run)
    mlflow_options = {MLFlowLiterals.LOADER: SystemSettings.NAMESPACE}
    strs_to_save = {RUN_ID_OUTPUT_PATH: run.id}
    models_to_save = {model_path: model}
    run_ctx.batch_save_artifacts(os.getcwd(),
                                 input_strs=strs_to_save,
                                 model_outputs=models_to_save,
                                 save_as_mlflow=save_mlflow,
                                 mlflow_options=mlflow_options)
    return model_path


def save_metrics(metrics_dict):
    """
    Save a metrics to outputs directory.

    :param metrics_dict: Metrics produced using different thresholds
    :type metrics_dict: dictionary
    """
    os.makedirs(OutputLiterals.OUTPUT_DIR, exist_ok=True)
    metrics_path = os.path.join(OutputLiterals.OUTPUT_DIR, "metrics.csv")

    # Save metrics to csv
    metrics_df = pd.DataFrame(metrics_dict)
    metrics_df.to_csv(metrics_path, index=False)
    logger.info("Metrics saved")


def save_predicted_results(predicted_df: pd.DataFrame, file_name: str):
    """
    Save predicted output

    :param predicted_df: predicted output to save
    :param file_name: location to save
    :return:
    """
    os.makedirs(OutputLiterals.OUTPUT_DIR, exist_ok=True)
    predictions_path = os.path.join(OutputLiterals.OUTPUT_DIR, file_name)
    predicted_df.to_csv(predictions_path, index=False)
    logger.info("Prediction results saved")
