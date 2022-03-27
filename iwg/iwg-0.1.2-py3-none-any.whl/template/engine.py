import logging
import os
import re
from pathlib import Path
from typing import Union

from .. import parsing
from ..errors import LabelWithoutValue
from . import simple_template_layout
from ..util import update_dict

logger = logging.getLogger(__name__)


def transpile_md(doc_path, defaults: dict=None, markdown_ext: list=None):
    # determine the layout file

    with open(doc_path, encoding="utf-8") as fp:
        metadata, doc_md = parsing.extract_front_matter(fp.read())
        if not metadata:
            metadata = {}
    
    layout = (metadata["layout"]
        if "layout" in metadata
        else "simple")
    
    doc_name = os.path.splitext(os.path.basename(doc_path))[0]
    document = update_dict(defaults, {
        "title": (metadata["title"]
            if "title" in metadata
            else doc_name),
        "content": parsing.markdown_to_html(doc_md, markdown_ext)
    })

    return layout, document


def render(
    document: Union[str, dict],
    out_file: str,
    template_dir: str,
    layout: str,
    doc_name: str="UNTITLED",
    missing_label_ok: bool=False
) -> None:
    """Builds a single document"""

    if isinstance(document, str):
        document = { "content": document }

    tmpl_path = Path(template_dir)
    out_path = Path(out_file)
    
    if layout == "simple":
        template = simple_template_layout
    else:
        layout_file = tmpl_path / "views" / f"{layout}.html"
        with open(layout_file, encoding="utf-8") as fp:
            template = fp.read()

    def labelrepl(matchobj):
        label = matchobj.group(1) 
        if label in document:
            return document[label]
        
        err_msg = (f"Value for '{label}' label is missing."
            f" (in document '{doc_name}')")
        if missing_label_ok:
            logging.warning(err_msg)
            return matchobj.group(0)
        else:
            raise LabelWithoutValue(err_msg)

    label_re = re.compile(r"\{\{\s*(.*?)\s*\}\}")

    logger.debug(f"Processing document {doc_name}...")
    
    result = label_re.sub(labelrepl, template)
    with open(out_path, "w", encoding="utf-8") as fp:
        fp.write(result)
