import mmap
import os
import re
import shutil

from anytree import Node, PreOrderIter
from markdownify import markdownify as md
from migcon.attachment_info import AttachmentInfo, Attachment, process_tokens
from migcon.drawio_handler import copy_drawio_file, handle_attachment
from migcon.file_dups import find_duplicates
from markdown_it import MarkdownIt
from pathlib import Path
from typing import Dict, Tuple

REMOVE_STRING_A = '<img src="/images/icons/bullet_blue.gif" width="8" height="8" />'
REMOVE_STRING_B = '<img src="images/icons/bullet_blue.gif" width="8" height="8" />'


def get_dest_file_from_node(node: Node) -> Path:
    if node.parent:
        filename = f"{node.filepath.name}.md"
        dest_dir = node.parent.filepath
    else:
        filename = f"{node.name}.md"
        dest_dir = node.filepath
    return Path(dest_dir, filename)


def copy_into_dir_tree(src_dir: Path, structure: Node) -> None:
    """
    Copies the source file into the new directory structure (provided by structure argument)

    :param src_dir: source directory
    :param structure: hierarchy of new directory structure
    """
    for node in PreOrderIter(structure):
        if len(node.children) > 0:
            node.filepath.mkdir(parents=True, exist_ok=True)
        dest = get_dest_file_from_node(node)
        src = Path(src_dir, dest.name)
        shutil.copy(src, dest)


def rewrite_links(structure: Node, replacement_files: Dict[str, str]) -> None:
    """
    Rewrites Markdown links based on the new directory structure created by running the conversion
    :param structure: hierarchy of new directory structure
    :param replacement_files: a dictionary of file name (flat) to file name (relative to new root)
    """
    for node in PreOrderIter(structure):
        target_file = get_dest_file_from_node(node)
        if target_file.is_file():
            _rewrite_links(target_file, replacement_files)


def _rewrite_links(file: Path, replacement_files: Dict[str, str]) -> None:
    """
    Rewrites Markdown links based on the new directory structure created by running the conversion
    :param file: source markdown file
    :param replacement_files: a dictionary of file name (flat) to file name (relative to new root)
    """
    class Fixup:
        def __init__(self):
            self.changed = False

        def fixup(self, match) -> str:
            link_target = match.group(1)
            if link_target in replacement_files:
                self.changed = True
                return f'](/{replacement_files[link_target]})'
            return f']({link_target})'

    with open(file, mode='r+') as input_file:
        data = input_file.read()

    fixup = Fixup()
    flags = re.IGNORECASE | re.DOTALL | re.MULTILINE
    new = re.sub(']\((.*?)\)', fixup.fixup, data, 0, flags)

    if fixup.changed:
        with open(file, mode='w') as output_file:
            output_file.write(new)


def get_attached_files(structure: Node) -> Dict[Path, AttachmentInfo]:
    """
    Returns a dictionary of target file paths to attachment information
    :param structure: root of the content tree
    :return: mapping of target file to attachment information for that file
    """
    attached_files = {}
    for node in PreOrderIter(structure):
        file = get_dest_file_from_node(node)
        if file.is_file():
            page_name = file.stem
            attachment_info = get_attachment_info(file, page_name)
            if attachment_info:
                attached_files[file] = attachment_info
    return attached_files


def get_attachment_info(file: Path, page_name: str) -> AttachmentInfo:
    """
    Process the "Attachments" section of the input file. We are preparing to do the following:
    1. Identify the drawio mx files so, we can create an inflated version of the xml for the drawio directive
    2. Provide meaningful names for attachments in general
    3. Map the page id (used as the attachment directory) to a meaningful name (page name)
    :param file: the source file
    :param page_name: the page name
    :returns: a dictionary that holds the mapping information
    """
    with file.open(mode='r+') as input_file:
        with mmap.mmap(input_file.fileno(), length=0, access=mmap.ACCESS_READ) as mmap_in:
            attachments_offset = mmap_in.rfind(b'<div class="pageSectionHeader">\n\n## Attachments:')
            if attachments_offset >= 0:
                # we have a section header, so we can process the attachments
                # read from there to end of file
                mmap_in.seek(attachments_offset)
                data = mmap_in.read().decode('utf-8')
                # not sure why but the Markdown parser doesn't work properly with the following line, so just remove
                # it. Confluence is pretty standard on this line in exports, so it's relatively safe, even though
                # it's a bit of a hack.
                data = data.replace(REMOVE_STRING_A, '').replace(REMOVE_STRING_B, '')
                md = MarkdownIt("commonmark")
                tokens = md.parse(data)
                # now we have a list of tokens, so we can process them
                return process_tokens(tokens, page_name)


def process_attachments(source: Path, tree: Node) -> Dict[Path, AttachmentInfo]:
    """
    Gathers information on the attachments for each source page. It is common for Confluence to attach multiple
    copies of the same file (different versions perhaps, but often they are identical). This function will
    aggregate all the attachments for each file, and then return a dictionary of the form:
    {
        <file_path>: <AttachmentInfo>
    }
    as well as copying the attachments from the source directory into the target directory tree with meaningful
    names rather than page id and attachment ids.
    :param source: Root directory of the source files
    :param tree: content tree
    :return: dictionary mapping target files to attachment information
    """
    attachment_dir = tree.filepath / 'attachments'
    attachment_dir.mkdir(exist_ok=True)
    attachments = get_attached_files(tree)
    for new_file, attachment_info in attachments.items():
        files_copied = 0
        files_skipped = 0
        page_dir = attachment_dir / attachment_info.page_name
        page_dir.mkdir(exist_ok=True)
        for meaningful_name, attachment in attachment_info.attachments.items():
            copied, skipped = copy_attachment(source, page_dir, attachment, meaningful_name)
            files_copied += copied
            files_skipped += skipped
        # after copying all attachments, ensure that the same number of files appear in the source and target
        # directories
        source_dir = source / next(iter(next(iter(attachment_info.attachments.values())).files.values()))[0]
        source_dir = source_dir.parent
        source_count = len(list(source_dir.glob('*')))
        dest_count = files_copied + files_skipped
        if source_count != dest_count:
            # If you see this warning, there is another case to add to test_content_manager
            print(f'Warning: {files_copied} files were copied to {page_dir}, and {files_skipped} were skipped '
                  f'due to duplication detection or missing file, but there are {source_count} files in the '
                  f'{source_dir}.')
    return attachments


def copy_attachment(source: Path, page_dir: Path, attachment: Attachment, meaningful_name: str) -> Tuple[int, int]:
    """
    Copy the attachment to the attachment directory.
    :param source: the source directory
    :param page_dir: the directory to copy the attachment to
    :param attachment: the attachment_obj that holds the attachments to copy
    :param meaningful_name: the name of the attachment
    :return: Tuple of (# of files copied, # of files skipped)
    """
    files = []
    for attachment_type, file_paths in attachment.files.items():
        # we will ignore attachment type. The cases we've seen with same name for different types are:
        # application/octet-stream and application/json...
        for file_name in file_paths:
            files.append(source / file_name)
    deduped_files = find_duplicates(files)
    is_drawio = '(application/vnd.jgraph.mxfile)' in attachment.files
    idx = 0
    files_copied = 0
    files_skipped = 0
    for source_file, skipped_files in deduped_files.items():
        files_skipped += len(skipped_files)
        dest_file = page_dir / f'{meaningful_name}'
        if idx > 0:
            dest_file = dest_file.parent / f'{dest_file.stem}_{idx}{dest_file.suffix}'
        if dest_file.exists():
            dest_file.unlink()
        if not source_file.exists():
            print(f'Warning: {source_file} does not exist. (Meaningful name: {dest_file})')
            files_skipped += 1
        else:
            files_copied += 1
            if is_drawio:
                dest_file = copy_drawio_file(source_file, dest_file)
            else:
                shutil.copy(source_file, dest_file)
            if attachment.destination_file:
                attachment.multiple_copies_warning = True
            attachment.destination_file = dest_file
            idx += 1
    return files_copied, files_skipped


def nn_min(x: int, y: int) -> int:
    """
    the non-negative minimum of x and y
    """
    if x < 0:
        return y
    if y < 0:
        return x
    if x < y:
        return x
    return y


def remove_trailing_sections(tree: Node):
    """
    Removes the "extra" sections that are part of the export, e.g. Attachments, Comments, Change History
    :param tree: Root of the target directory tree
    """
    for node in PreOrderIter(tree):
        file = get_dest_file_from_node(node)
        with file.open(mode='r+') as input_file:
            with mmap.mmap(input_file.fileno(), length=0, access=mmap.ACCESS_READ) as mmap_in:
                offset = mmap_in.rfind(b'<div class="pageSectionHeader">\n\n## Attachments:')
                offset = nn_min(mmap_in.rfind(b'<div class="pageSectionHeader">\n\n## Comments:'), offset)
                offset = nn_min(mmap_in.rfind(b'## Change History'), offset)
            if offset >= 0:
                os.ftruncate(input_file.fileno(), offset)


def fixup_attachment_references(tree: Node, attachments: Dict[Path, AttachmentInfo], source_root_dir: Path,
                                target_root_dir: Path):
    """
    The export from Confluence results in attachments identified by page_id (directory) and attachment_id (filename).
    Additionally, drawio macros result in an <img> tag with the source drawio deflated and base64 encoded.
    This function replaces the <img> tags with Markdown syntax (e.g. ![](attachment:page_id/attachment_id)),
    using meaningful names for directory and file and using drawio directive when drawio images are encountered.
    :param tree: Content tree
    :param attachments: information about all the source attachments, key: page_name, value: AttachmentInfo
    :param source_root_dir: the root of the source directory tree
    :param target_root_dir: the root directory of the target directory tree
    :return: None
    """
    class Fixup:
        def __init__(self, attachment_info_map: Dict[Path, AttachmentInfo]):
            self.attachment_info_map = attachment_info_map
            self.changed = False
            self.current_file = None

        def prep_file(self, file: Path):
            self.changed = False
            self.current_file = file

        def fixup(self, match):
            self.changed = True
            if match.group(1).startswith('<img src="images/'):
                data = match.group(1).replace('src="images', 'src="/images')
                img_file = match.group(2)
                target_img_file = target_root_dir / img_file
                target_img_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(source_root_dir / img_file, target_img_file)
                return data
            elif match.group(1).find("drawio-diagram-image") != -1:
                data = match.group(2)
                if self.current_file in self.attachment_info_map:
                    attachment_info = self.attachment_info_map[self.current_file]
                else:
                    attachment = Attachment("Unknown", {
                        "(application/vnd.jgraph.mxfile)": [""]
                    })
                    attachment_info = AttachmentInfo("Unknown", self.current_file.stem, {"Unknown": attachment})
                meaningful_name, file_id = handle_attachment(data, attachment_info, source_root_dir, target_root_dir)
                if meaningful_name.endswith('.drawio.xml'):
                    return f'''```{{drawio-image}} {file_id}
```'''
                else:
                    return f'![{meaningful_name}](/{file_id})'
            else:
                # find the attachment_file name in the set of attachments for this page, use the
                # meaningful attachment name for the 'alt text' and the destination file for the
                # path to the image
                img_file = match.group(2)
                attachment_info = self.attachment_info_map[self.current_file]
                for attachment in attachment_info.attachments.values():
                    for files in attachment.files.values():
                        for file in files:
                            if file == img_file:
                                return f'![{attachment.meaningful_name}]' \
                                       f'(/{attachment.destination_file.relative_to(target_root_dir)})'
                # there are a few cases where the conversion to markdown doesn't copy files over.
                # assuming that the source export directory is a peer directory to the markdown root
                # and the markdown source root is a subdirectory of the markdown root, see if we can fish the
                # file out of the original source directory

                if (source_root_dir.parent.parent / source_root_dir.name / img_file).exists():
                    # probably one of the 'download/temp' files; copy it to target directory and
                    # return name of the file
                    img_path = Path(img_file)
                    target_img_file = f"attachments/{self.current_file.stem}/{img_path.name}"
                    shutil.copyfile(source_root_dir.parent.parent / source_root_dir.name / img_file,
                                    target_root_dir / target_img_file)
                    return f'![{img_path.stem}](/{target_img_file})'
                print(f'Warning: Could not find attachment file {img_file} for page {self.current_file}')

    fixup = Fixup(attachments)

    for node in PreOrderIter(tree):
        file = get_dest_file_from_node(node)
        fixup.prep_file(file)
        with file.open(mode='r+') as input_file:
            data = input_file.read()
        flags = re.IGNORECASE | re.DOTALL | re.MULTILINE
        new = re.sub(r'(<img\s*src="(.*?)".*?>)', fixup.fixup, data, 0, flags)
        if fixup.changed:
            with file.open(mode='w') as output_file:
                output_file.write(new)


def fixup_div_tags(tree: Node) -> None:
    """
    Fixup the div tags in the markdown files.
    :param tree: the content root node
    """
    for node in PreOrderIter(tree):
        file = get_dest_file_from_node(node)
        with file.open(mode='r+') as input_file:
            data = input_file.read()
        new = _fixup_divs(data)
        if new != data:
            with file.open(mode='w') as output_file:
                output_file.write(new)

def _fixup_divs(content: str) -> str:
    patterns = [
        r'<div class="content-wrapper">\s*(.*?)\s*</div>',
        r'<div class="content-wrapper">\s*(.*?)\s*</div>',
        r'<div class="table-wrap">\s*(.*?)\s*</div>',
        r'<div class="code panel.*?<div class="CodeContent.*?>\s*(.*?)\s*</div>\s*</div>',
        r'<div>\s*(.*?)\s*</div>',
        r'<div>\s*(.*?)\s*</div>',
        r'<div class="details">\s*(.*?)\s*</div>',
    ]
    flags = re.IGNORECASE | re.DOTALL | re.MULTILINE
    content = fixup_expander(content, flags)
    for pattern in patterns:
        content = re.sub(pattern, r'\1\n', content, 0, flags)
    content = content.replace(u'\xa0', ' ')
    content = fixup_toc_macro(content, flags)
    content = fixup_multi_column(content, flags)
    return content


def fixup_toc_macro(content, flags = re.DOTALL | re.MULTILINE | re.IGNORECASE):
    # since jupyter-book has a toc for each page when rendering html, we can just remove the toc-macro
    toc_macro = r'<div class="toc-macro.*?>.*?</div>'
    content = re.sub(toc_macro, '', content, 0, flags)
    return content


def fixup_expander(content, flags = re.DOTALL | re.MULTILINE | re.IGNORECASE):
    # replace the expander macro with the dropdown directive from sphinx.panels
    expander = r'<div id="expander-content-.*?class="expand-content">\s*(.*?)\s*</div>'
    content = re.sub(expander, r'\1\n```', content, 0, flags)
    expander = r'<div id="expander-control-.*?class="expand-control">\s*<img.*?/>(.*?)\s*</div>'
    content = re.sub(expander, r'```{dropdown} \1', content, 0, flags)
    expander = r'<div id="expander-.*?class="expand-container">(.*?)\s*</div>'
    content = re.sub(expander, r'\1', content, 0, flags)
    return content


def fixup_multi_column(content, flags = re.DOTALL | re.MULTILINE | re.IGNORECASE):
    patterns = [
        r'<div class="innerCell">\s*(.*?)\s*</div>',
        r'<div class="cell normal" data-type="normal">\s*(.*?)\s*</div>',
        r'<div class="columnLayout single" layout="single">\s*(.*?)\s*</div>',
    ]
    for pattern in patterns:
        content = re.sub(pattern, r'\1', content, 0, flags)
    return content

def convert_remaining_html(tree: Node) -> None:
    """
    Fixup the div tags in the markdown files.
    :param tree: the content root node
    """
    for node in PreOrderIter(tree):
        file = get_dest_file_from_node(node)
        with file.open(mode='r+') as input_file:
            data = input_file.read()
        new = _convert_remaining_html(data)
        if new != data:
            with file.open(mode='w') as output_file:
                output_file.write(new)

def _convert_remaining_html(content: str) -> str:
    strip_newline = False
    def _convert_to_md(match):
        converted = md(match.group(1))
        if strip_newline:
            converted = converted.replace('\n', '')
        return converted

    flags = re.IGNORECASE | re.DOTALL | re.MULTILINE

    strip_newline = True
    html_link = r'(<a\s*?href.*?</a>)'
    content = re.sub(html_link, _convert_to_md, content, 0, flags)

    strip_newline = False
    html_table = r'(<table.*?</table>)'
    content = re.sub(html_table, _convert_to_md, content, 0, flags)

    return content
