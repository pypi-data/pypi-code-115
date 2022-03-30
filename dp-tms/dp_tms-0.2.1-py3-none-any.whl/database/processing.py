"""
    database processing utilities

    methods include
    --------------------
    1. convert_listing_to_document
    2. convert_candidate_to_document
    3. find_structured_data_and_create_file
"""
from typing import List, Dict
from pathlib import Path
import re
from dp_tms.database.storage import (
    check_if_cloud_storage_and_extract_path,
    write_txt_to_s3,
)


def convert_listing_to_document(data: dict) -> str:
    """converts a structured listing json payload in to a txt supported text dump
    Args:
        data (dict): structured json/dict payload
    Returns:
        (str): text dump
    """
    listing_title = re.sub(r"[^a-zA-Z0-9]", " ", data["title"])
    industry = re.sub(r"[^a-zA-Z0-9]", " ", data["industry"])
    experience_lengths = re.sub(r"[^a-zA-Z0-9]", " ", data["experience_lengths"])
    experience_levels = re.sub(r"[^a-zA-Z0-9]", " ", data.get("experience_levels", ""))
    qualification_levels = re.sub(
        r"[^a-zA-Z0-9]", " ", data.get("qualification_levels", "")
    )
    location = re.sub(r"[^a-zA-Z0-9]", " ", data["location"])
    description = re.sub(r"[^a-zA-Z0-9]", " ", data["description"])
    details = ""
    details = re.sub("<[^<]+?>", "", data.get("details", ""))
    details = re.sub(r"[^a-zA-Z0-9]", " ", details)

    if (
        len(
            listing_title
            + industry
            + experience_lengths
            + experience_levels
            + qualification_levels
            + location
            + description
            + details
        )
        == 0
    ):
        return None

    # compile listing document
    text = (
        f"""Title\n{listing_title}\n"""
        f"""Description\n{description}\n"""
        f"""Industry\n{industry}"""
        f"""Experience level\n{experience_levels}\n"""
        f"""Experience length\n{experience_lengths}\n"""
        f"""location\n{location}\n"""
        f"""Qualification\n{qualification_levels}\n"""
        f""""Details\n{details}\n"""
    )

    return text


def convert_candidate_to_document(data: dict) -> str:
    """converts a structured candidate json payload in to a txt supported text dump
    Args:
        data (dict): structured json/dict payload
    Returns:
        (str): text dump
    """
    headline = re.sub(r"[^a-zA-Z0-9]", " ", data["headline"])
    qualification = re.sub(r"[^a-zA-Z0-9]", " ", data["qualification"])
    skills = re.sub(r"[^a-zA-Z0-9]", " ", data["skills"])
    languages = re.sub(r"[^a-zA-Z0-9]", " ", data["languages"])
    experience = re.sub(r"[^a-zA-Z0-9]", " ", data["experience"])
    cover_letter = re.sub(r"[^a-zA-Z0-9]", " ", data["cover_letter"])

    if (
        len(headline + qualification + skills + languages + experience + cover_letter)
        == 0
    ):
        return None

    # convert to CV format in txt
    text = (
        f"""CV\n{headline}\n"""
        f"""Cover Letter\n{cover_letter}\n"""
        f"""Work Experience\n{experience}\n"""
        f"""Qualification\n{qualification}\n"""
        f"""Skills\n{skills}\n"""
        f"""Languages skills\n{languages}\n"""
    )

    return text


def find_structured_data_and_create_file(
    entities: List[Dict[str, str]], base_storage_path: str, created_at: str
) -> List[Dict[str, str]]:
    """
    finds if resume/document path exists,
    else attempts to construct a resume/document document from structured json
    and write a file to storage location.
    Keeps a reference in processed entities.

    Args:
        entities (List[Dict[str, str]]): entity records
        base_storage_path (str): path that file storage paths are based on
        created_at (str): date at which entities are processed and staged

    Returns:
        List[Dict[str, str]]: processed entity records
    """
    entities = entities.copy()
    for i, entity in enumerate(entities):
        # iterate and check
        entity_id = entity.get("entity_id")
        entity_type = entity.get("entity_type")
        properties = entity.get("properties", {})
        resume = properties.get("resume")

        if resume is None:
            if entity_type == "listing":
                # create document
                content = convert_listing_to_document(properties)
            elif entity_type == "candidate":
                content = convert_candidate_to_document(properties)
            else:
                raise Exception(f"entity type not supported: {entity_type}")

            if content is not None:
                storage_path = f"{base_storage_path}/{entity_id}.txt"
                print(f"store at: {storage_path}")

                write_txt_to_s3(storage_path, content)

                bucket, file_path, scheme = check_if_cloud_storage_and_extract_path(
                    storage_path, schemes=["s3"]
                )

                storage_reference = {
                    "file": file_path,
                    "type": "txt",
                    "disk": scheme,
                    "bucket": bucket,
                }

        else:
            # No idea what this is, I'm not sending it in payload
            file_type = resume.get("type")

            if file_type is None:
                file_path = resume["file"]
                file_type = Path(file_path).suffixes
                if len(file_type) > 0:
                    file_type = "".join(file_type)
                else:
                    file_type = None

            storage_reference = {
                "file": resume["file"],
                "type": file_type,
                "disk": resume.get("disk"),
                "bucket": resume.get("bucket"),
            }

            # Why do the above and then replace the variable?
            storage_reference = resume

        entities[i]["properties"]["storage_reference"] = storage_reference
        entities[i]["created_at"] = created_at

    return entities
