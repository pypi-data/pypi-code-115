import base64
import filecmp
import shutil
import xml.etree.ElementTree as ETree
import zlib

from migcon.attachment_info import AttachmentInfo
from pathlib import Path
from typing import Tuple
from urllib.parse import unquote
from xml.dom import minidom


def inflate(data: str) -> str:
    """
    reverses the compression used by draw.io

    see: https://drawio-app.com/extracting-the-xml-from-mxfiles/
    see: https://stackoverflow.com/questions/1089662/python-inflate-and-deflate-implementations

    :param data: base64 encoded string
    :return: "plain text" version of the deflated data
    """
    data = base64.b64decode(data)
    decompress = zlib.decompressobj(-zlib.MAX_WBITS)
    inflated = decompress.decompress(data)
    inflated += decompress.flush()
    return unquote(inflated.decode('utf-8'))


def copy_drawio_file(source: Path, target: Path) -> Path:
    tree = ETree.parse(source)
    root = tree.getroot()
    data = root.find('diagram').text
    target_file = Path(f"{str(target)}.drawio.xml")
    write_file_from_data(data, target_file)
    return target_file


def write_file_from_data(data: str, target_file: Path) -> None:
    with target_file.open(mode='w+') as output_file:
        output_file.write(minidom.parseString(inflate(data)).toprettyxml(indent="   "))


def handle_attachment(data: str, attachment_info: AttachmentInfo, source_root: Path,
                      target_root: Path) -> Tuple[str, str]:
    # data is likely coming in as base64 encoded string prefixed with 'data:image/png;base64,'
    # verify that's the case... If it isn't, then I'm uncertain what to do, so print a warning and
    # continue...
    if not data.startswith('data:image/png;base64,'):
        print(f"WARNING: data is not base64 encoded: {data[:100]}")
        return "skip", "skip"
    data = base64.b64decode(data[len('data:image/png;base64,'):])

    # create a temporary file and write inflated data str into it
    temp_file = target_root / "attachments/temporary.png"
    with open(temp_file, 'wb') as output_file:
        output_file.write(data)

    # compare the temp file to the contents of the files in attachments that are 'png'
    for attachment in attachment_info.attachments.values():
        if "(image/png)" in attachment.files:
            for file in attachment.files["(image/png)"]:
                if filecmp.cmp(temp_file, source_root / file):
                    # if the file is the same, we don't need to copy it again
                    temp_file.unlink()
                    # TODO: if we find a match with a png file in the attachments, then try to correlate it back to a
                    #  drawio file
                    #  Unfortunately, exact match on contents is not sufficient. For now, leave this as a manual step
                    return attachment.meaningful_name, file
    # if we get here, the file is not the same as any of the files in the attachments, so we need to copy it
    target_dir = target_root / "attachments" / attachment_info.page_name
    target_dir.mkdir(parents=True, exist_ok=True)
    idx = 0
    while True:
        meaningful_name = f"auto_generated_{idx}.png"
        target_file = target_dir / meaningful_name
        if not target_file.exists():
            shutil.copy(temp_file, target_file)
            temp_file.unlink()
            return meaningful_name, str(target_file.relative_to(target_root))
        idx += 1
