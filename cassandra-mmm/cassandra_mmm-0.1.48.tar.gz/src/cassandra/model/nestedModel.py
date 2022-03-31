from cassandra.model.linear import linear
from cassandra.model.logLinear import logLinear
from cassandra.model.ridge import ridge
from src.cassandra.model.logLog import logLog


def nestedModel(df, X_columns, y_column, model_regression='linear', X_trasformations_columns=[],
                model_regression_log_log='linear', ridge_number=0, metric=['rsq', 'nrmse', 'mape'],
                return_metric=False):
    metrics_values = {}
    name_model = 'Nested Model for ' + y_column

    if model_regression == 'linear':
        if return_metric:
            result, model, metrics_values = linear(df, X_columns, y_column, name_model, metric=metric,
                                                   return_metric=return_metric)
        else:
            result, model = linear(df, X_columns, y_column, name_model, metric=metric, return_metric=return_metric)

    elif model_regression == 'logLinear':
        if return_metric:
            result, model, metrics_values = logLinear(df, X_columns, y_column, name_model, metric=metric,
                                                      return_metric=return_metric)
        else:
            result, model = logLinear(df, X_columns, y_column, name_model, metric=metric, return_metric=return_metric)

    elif model_regression == 'logLog':
        if return_metric:
            result, model, metrics_values = logLog(df, X_trasformations_columns, X_columns, y_column, name_model,
                                                   model_regression=model_regression_log_log, metric=metric,
                                                   return_metric=return_metric)
        else:
            result, model = logLog(df, X_trasformations_columns, X_columns, y_column, name_model,
                                   model_regression=model_regression_log_log, metric=metric,
                                   return_metric=return_metric)

    elif model_regression == 'ridge':
        if return_metric:
            result, model, metrics_values = ridge(df, X_columns, y_column, name_model, ridge_number=ridge_number,
                                                  metric=metric,
                                                  return_metric=return_metric)
        else:
            result, model = ridge(df, X_columns, y_column, name_model, ridge_number=ridge_number, metric=metric,
                                  return_metric=return_metric)

    if metrics_values:
        return result, model, metrics_values
    else:
        return result, model


def mainNestedModel(sub_df, sub_X_columns, sub_y_column, X_columns, y_column, sub_model_regression='linear',
                    sub_X_trasformations_columns=[],
                    sub_model_regression_log_log='linear', sub_ridge_number=0, sub_metric=['rsq', 'nrmse', 'mape'],
                    return_sub_metric=False, model_regression='linear',
                    X_trasformations_columns=[], model_regression_log_log='linear', ridge_number=0,
                    metric=['rsq', 'nrmse', 'mape'], return_metric=False):
    metrics_values = {}
    if return_sub_metric == True:
        sub_result, sub_model, sub_metric_values = nestedModel(sub_df, sub_X_columns, sub_y_column,
                                                               sub_model_regression, sub_X_trasformations_columns,
                                                               sub_model_regression_log_log, sub_ridge_number,
                                                               sub_metric, return_sub_metric)
    else:
        sub_result, sub_model = nestedModel(sub_df, sub_X_columns, sub_y_column, sub_model_regression,
                                            sub_X_trasformations_columns,
                                            sub_model_regression_log_log, sub_ridge_number, sub_metric)

    df = sub_result

    df[sub_y_column] = sub_result['prediction']

    name_model = model_regression + ' for ' + y_column

    if model_regression == 'linear':
        if return_metric:
            result, model, metrics_values = linear(df, X_columns, y_column, name_model, metric=metric,
                                                   return_metric=return_metric)
        else:
            result, model = linear(df, X_columns, y_column, name_model, metric=metric, return_metric=return_metric)

    elif model_regression == 'logLinear':
        if return_metric:
            result, model, metrics_values = logLinear(df, X_columns, y_column, name_model, metric=metric,
                                                      return_metric=return_metric)
        else:
            result, model = logLinear(df, X_columns, y_column, name_model, metric=metric, return_metric=return_metric)

    elif model_regression == 'logLog':
        if return_metric:
            result, model, metrics_values = logLog(df, X_trasformations_columns, X_columns, y_column, name_model,
                                                   model_regression=model_regression_log_log, metric=metric,
                                                   return_metric=return_metric)
        else:
            result, model = logLog(df, X_trasformations_columns, X_columns, y_column, name_model,
                                   model_regression=model_regression_log_log, metric=metric,
                                   return_metric=return_metric)

    elif model_regression == 'ridge':
        if return_metric:
            result, model, metrics_values = ridge(df, X_columns, y_column, name_model, ridge_number=ridge_number,
                                                  metric=metric, return_metric=return_metric)
        else:
            result, model = ridge(df, X_columns, y_column, name_model, ridge_number=ridge_number, metric=metric,

                                  return_metric=return_metric)

    if metrics_values:
        return result, model, metrics_values, sub_result, sub_model, sub_metric_values
    else:
        return result, model, sub_result, sub_model
