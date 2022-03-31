from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from markdown_it.token import Token


@dataclass
class Attachment:
    """
    A class to hold information about an attachment. With Page attachments in confluence, multiple files
    can share the same name, also with potentially different types, e.g. application/json and application/octet-stream.
    This is modeled by having a dictionary that maps attachment type to a list of file names.
    """
    meaningful_name: str
    files: Dict[str, List[str]]  # key: attachment type, value: list of file names
    destination_file: Path = None
    multiple_copies_warning: bool = False


@dataclass
class AttachmentInfo:
    """
    This class is used to store the information about the attachments, specifically we derive the page id from the
    attachment url string (Path(url).parent.name). As multiple versions of the same file can be attached to a
    confluence page, we keep a dictionary of the "meaningful name" that maps to an attachment
    which holds a list of all file names that are associated to that "attachment".
    """
    page_id: str
    page_name: str
    attachments: Dict[str, Attachment]  # key: meaningful attachment name, value: attachment


def process_tokens(tokens: List[Token], page_name: str) -> AttachmentInfo:
    """
    Process the list of tokens that were generated from the "attachments" section of the input file.
    :param tokens: the list of tokens that holds attachment information
    :param page_name:
    :return: a dictionary of attachment information
    """
    attachments = {}
    page_id = 'unset'
    in_heading = False
    in_attachment_section = False
    for token in tokens:
        if token.type == 'heading_open':
            if in_attachment_section:
                break
            in_heading = True
        elif token.type == 'heading_close':
            in_heading = False
        elif token.type == 'inline':
            if in_heading:
                if token.content == 'Attachments:':
                    in_attachment_section = True
            elif in_attachment_section:
                att_type = att_name = att_url = None
                in_link = False
                soft_break = False
                for child in token.children:
                    if child.type == 'link_open':
                        att_url = child.attrs['href']
                        in_link = True
                        soft_break = False
                    elif child.type == 'link_close':
                        in_link = False
                        soft_break = False
                    elif child.type == 'text':
                        if in_link:
                            if soft_break:
                                att_name += f" {child.content.strip()}"
                            else:
                                att_name = child.content.strip()
                        else:
                            att_type = child.content.strip()
                    elif child.type == 'softbreak':
                        soft_break = True
                    if att_url and att_name and att_type:
                        page_id = Path(att_url).parent.name
                        att_name = att_name.replace(' ', '_')
                        if att_name in attachments:
                            if att_type in attachments[att_name].files:
                                attachments[att_name].files[att_type].append(att_url)
                            else:
                                attachments[att_name].files[att_type] = [att_url]
                        else:
                            attachments[att_name] = Attachment(att_name, {att_type: [att_url]})
                        att_type = att_name = att_url = None
    return AttachmentInfo(page_id, page_name, attachments)
