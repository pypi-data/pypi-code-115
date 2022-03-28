"""Module create nlp labelling project in labelbox."""
import os
import warnings
from typing import Optional, Union
from pathlib import Path
import json
import pandas as pd
import boto3
import s3fs
from labelbox import Client  # , Dataset,  DataRow,

warnings.filterwarnings("ignore")
# Show All Columns
pd.options.display.max_columns = None

s3 = s3fs.S3FileSystem()


def pull_files_s3(prefix: str, file_type: str, s3_bucket, delimiter='/') -> str:
    """pull_files_s3

    Args:
        prefix (str): S3 folder path name without the bucket part
        file_type (str): type of the data file
        s3_bucket (_type_): S3 bucket
        delimiter (str, optional): Defaults to '/'.

    Yields:
        Iterator[str]: _description_
    """
    prefix = prefix[1:] if prefix.startswith(delimiter) else prefix
    yield from (_.key for _ in s3_bucket.objects.filter(Prefix=prefix) if file_type in _.key)


def create_labeling_project(labelbox_api_key: str,
                            data: Union[str, Path, pd.DataFrame], annotation_col: str, id_col: str,
                            dataset_name: str, project_name: str, project_desc: Optional[str] = '',
                            s3_bucket_name: str = 'test-labelbox-edelman', prefix: Optional[str] = None,
                            temp_data_path: Optional[Union[str, Path]] = None) -> dict:
    """create_labeling_project creates labelling project. dataset and attaches data to project from dxi S3 bucket.

    Args:
        labelbox_api_key (str): your labelbox api_key
        data (Union[str, Path, pd.DataFrame]): data as a dataframe or file path.
        annotation_col (str): the column that we need to annotate in the labelling project.
        id_col (str): the unique identifier column of the dataframe.
        dataset_name (str): name you want to assign to your dataset on labelbox. (json will be added to end)
        project_name (str): name you want to assign to your project on labelbox.
        project_desc (Optional[str]): task description of the project.
        s3_bucket_name (str, optional): S3 bucket that is integrated with labelbox. Defaults to 'test-labelbox-edelman'.
        prefix (Optional[str], optional): folder path to store text files in the S3 bucket. Defaults to None.
        temp_data_path (Optional[Union[str, Path]], optional): file path where text files are stored temporarily. Defaults to None.

    Returns:
        dict: _description_
    """
    # folder to store and sync temporary text files to S3
    if temp_data_path is None:
        temp_data_path = Path(Path.cwd()/'temp_text_file_storage')
        temp_data_path.mkdir(exist_ok=True, parents=True)

    for _, row in data.iterrows():
        with open(temp_data_path/f'{row[id_col]}.txt', 'w') as file:
            file.write(row[annotation_col])

    sync_command = f"aws s3 sync {str(temp_data_path)}  s3://{s3_bucket_name}/{prefix} --quiet --acl public-read"
    os.system(command=sync_command)

    s3_bucket = boto3.resource('s3').Bucket(s3_bucket_name)
    s3_files = list(pull_files_s3(
        prefix=prefix, file_type='txt', s3_bucket=s3_bucket))

    client = Client(api_key=labelbox_api_key)

    dataset_name += ".json"
    # creates an empty dataset
    dataset = client.create_dataset(name=dataset_name)

    # creates an empty project
    project = client.create_project(
        name=project_name,
        description=project_desc)

    # Attach dataset
    project.datasets.connect(dataset)
    my_data_rows = [
        {
            "row_data": f'https://{s3_bucket_name}.s3.amazonaws.com/{file}',
            "external_id": file.split('/')[-1].split('.txt')[0]
        } for file in s3_files
    ]

    s3_file_path = f"{s3_bucket_name}/{dataset_name}"
    with s3.open(s3_file_path, 'w') as file:
        json.dump(my_data_rows, file)

    task = dataset.create_data_rows(my_data_rows)
    task.wait_till_done()
    print(f'sync labelbox {dataset_name} with text files on S3: ', task.status)

    files = temp_data_path.glob('*')
    _ = [file.unlink() for file in files]
    temp_data_path.rmdir()

    return {'created_project': project_name,
            'project_uid': project.uid,
            'attached_datset': dataset_name,
            'dataset_uid': dataset.uid,
            'data_loaded_from': f"s3://{s3_bucket_name}/{prefix}",
            'aws_url_reference_json': f"s3://{s3_file_path}"
            }
