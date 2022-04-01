# AUTOGENERATED! DO NOT EDIT! File to edit: ../06_docexp.ipynb.

# %% auto 0
__all__ = ['default_pp_cfg', 'preprocess_cell', 'preprocess', 'preprocess_rm_cell', 'InjectMeta', 'StripAnsi', 'InsertWarning',
           'RmEmptyCode', 'UpdateTags', 'HideInputLines', 'FilterOutput', 'CleanFlags', 'CleanMagics', 'BashIdentify',
           'CleanShowDoc', 'HTMLEscape', 'RmHeaderDash', 'default_pps', 'doc_exporter', 'nb2md']

# %% ../06_docexp.ipynb 3
import re, uuid
from functools import wraps
from fastcore.basics import *
from fastcore.foundation import *
from traitlets.config import Config
from pathlib import Path
from html.parser import HTMLParser

from nbprocess.read import get_config
from nbprocess.processor import *

from nbconvert.preprocessors import ExtractOutputPreprocessor,Preprocessor,TagRemovePreprocessor
from nbconvert import MarkdownExporter
from nbprocess.extract_attachments import ExtractAttachmentsPreprocessor
from nbconvert.writers import FilesWriter

# %% ../06_docexp.ipynb 7
def default_pp_cfg():
    "Default Preprocessor Config for MDX export"
    c = Config()
    c.TagRemovePreprocessor.remove_cell_tags = ("remove_cell", "hide")
    c.TagRemovePreprocessor.remove_all_outputs_tags = ("remove_output", "remove_outputs", "hide_output", "hide_outputs")
    c.TagRemovePreprocessor.remove_input_tags = ('remove_input', 'remove_inputs', "hide_input", "hide_inputs")
    return c

# %% ../06_docexp.ipynb 8
def preprocess_cell(func):
    "Decorator to create a `preprocess_cell` `Preprocessor` for cells"
    @wraps(func, updated=())
    class _C(Preprocessor):
        def preprocess_cell(self, cell, resources, index):
            res = func(cell)
            if res: cell = res
            return cell, resources
    return _C

# %% ../06_docexp.ipynb 9
def preprocess(func):
    "Decorator to create a `preprocess` `Preprocessor` for notebooks"
    @wraps(func, updated=())
    class _C(Preprocessor):
        def preprocess(self, nb, resources):
            res = func(nb)
            if res: nb = res
            nb.cells = list(nb.cells)
            return nb, resources
    return _C

# %% ../06_docexp.ipynb 10
def preprocess_rm_cell(func):
    "Like `preprocess_cell` but remove cells where function returns `True`"
    @preprocess
    def _inner(nb): nb.cells = [cell for cell in nb.cells if not func(cell)]
    return _inner

# %% ../06_docexp.ipynb 11
def _doc_exporter(pps, cfg=None, tpl_file='ob.tpl'):
    cfg = cfg or default_pp_cfg()
    cfg.MarkdownExporter.preprocessors = pps or []
    tmp_dir = Path(__file__).parent/'templates/'
    tpl_file = tmp_dir/f"{tpl_file}"
    if not tpl_file.exists(): raise ValueError(f"{tpl_file} does not exist in {tmp_dir}")
    cfg.MarkdownExporter.template_file = str(tpl_file)
    return MarkdownExporter(config=cfg)

# %% ../06_docexp.ipynb 12
def _run_preprocessor(pps, fname, display=False):
    exp = _doc_exporter(pps)
    result = exp.from_filename(fname)
    if display: print(result[0])
    return result

# %% ../06_docexp.ipynb 18
_re_meta= r'^\s*#(?:cell_meta|meta):\S+\s*[\n\r]'

@preprocess_cell
def InjectMeta(cell):
    "Inject metadata into a cell for further preprocessing with a comment."
    _pattern = r'(^\s*#(?:cell_meta|meta):)(\S+)(\s*[\n\r])'
    if cell.cell_type == 'code' and re.search(_re_meta, cell.source, flags=re.MULTILINE):
        cell_meta = re.findall(_pattern, cell.source, re.MULTILINE)
        d = cell.metadata.get('nbprocess', {})
        for _, m, _ in cell_meta:
            if '=' in m:
                k,v = m.split('=')
                d[k] = v
            else: print(f"Warning cell_meta:{m} does not have '=' will be ignored.")
        cell.metadata['nbprocess'] = d

# %% ../06_docexp.ipynb 26
_re_ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

@preprocess_cell
def StripAnsi(cell):
    "Strip Ansi Characters."
    for o in cell.get('outputs', []):
        if o.get('name') == 'stdout': o['text'] = _re_ansi_escape.sub('', o.text)

# %% ../06_docexp.ipynb 30
@preprocess
def InsertWarning(nb):
    """Insert Autogenerated Warning Into Notebook after the first cell."""
    content = "<!-- WARNING: THIS FILE WAS AUTOGENERATED! DO NOT EDIT! -->"
    mdcell = AttrDict(cell_type='markdown', id=uuid.uuid4().hex[:36], metadata={}, source=content)
    nb.cells.insert(1, mdcell)

# %% ../06_docexp.ipynb 34
def _keepCell(cell): return cell['cell_type'] != 'code' or cell.source.strip()

@preprocess
def RmEmptyCode(nb):
    "Remove empty code cells."
    nb.cells = filter(_keepCell,nb.cells)

# %% ../06_docexp.ipynb 37
@preprocess_cell
def UpdateTags(cell):
    root = cell.metadata.get('nbprocess', {})
    tags = root.get('tags', root.get('tag')) # allow the singular also
    if tags: cell.metadata['tags'] = cell.metadata.get('tags', []) + tags.split(',')

# %% ../06_docexp.ipynb 41
@preprocess_cell
def HideInputLines(cell):
    "Hide lines of code in code cells with the comment `#meta_hide_line` at the end of a line of code."
    tok = '#meta_hide_line'
    if cell.cell_type == 'code' and tok in cell.source:
        cell.source = '\n'.join([c for c in cell.source.splitlines() if not c.strip().endswith(tok)])

# %% ../06_docexp.ipynb 44
@preprocess_cell
def FilterOutput(cell):
    root = cell.metadata.get('nbprocess', {})
    words = root.get('filter_words', root.get('filter_word'))
    # import ipdb; ipdb.set_trace()
    if 'outputs' in cell and words:
        _re = f"^(?!.*({'|'.join(words.split(','))}))"
        for o in cell.outputs:
            if o.name == 'stdout':
                filtered_lines = [l for l in o['text'].splitlines() if re.findall(_re, l)]
                o['text'] = '\n'.join(filtered_lines)

# %% ../06_docexp.ipynb 48
_tst_flags = get_config()['tst_flags'].split('|')

@preprocess_cell
def CleanFlags(cell):
    "A preprocessor to remove Flags"
    if cell.cell_type != 'code': return
    for p in [re.compile(r'^#\s*{0}\s*'.format(f), re.MULTILINE) for f in _tst_flags]:
        cell.source = p.sub('', cell.source).strip()

# %% ../06_docexp.ipynb 50
@preprocess_cell
def CleanMagics(cell):
    "A preprocessor to remove cell magic commands and #cell_meta: comments"
    pattern = re.compile(r'(^\s*(%%|%).+?[\n\r])|({0})'.format(_re_meta), re.MULTILINE)
    if cell.cell_type == 'code': cell.source = pattern.sub('', cell.source).strip()

# %% ../06_docexp.ipynb 54
@preprocess_cell
def BashIdentify(cell):
    "A preprocessor to identify bash commands and mark them appropriately"
    pattern = re.compile('^\s*!', flags=re.MULTILINE)
    if cell.cell_type == 'code' and pattern.search(cell.source):
        cell.metadata.magics_language = 'bash'
        cell.source = pattern.sub('', cell.source).strip()

# %% ../06_docexp.ipynb 58
_re_showdoc = re.compile(r'^ShowDoc', re.MULTILINE)

def _isShowDoc(cell):
    "Return True if cell contains ShowDoc."
    return cell['cell_type'] == 'code' and _re_showdoc.search(cell.source)

@preprocess_cell
def CleanShowDoc(cell):
    "Ensure that ShowDoc output gets cleaned in the associated notebook."
    _re_html = re.compile(r'<HTMLRemove>.*</HTMLRemove>', re.DOTALL)
    if not _isShowDoc(cell): return
    all_outs = [o['data'] for o in cell.outputs if 'data' in o]
    html_outs = [o['text/html'] for o in all_outs if 'text/html' in o]
    if len(html_outs) != 1: return
    cleaned_html = self._re_html.sub('', html_outs[0])
    return AttrDict({'cell_type':'raw', 'id':cell.id, 'metadata':cell.metadata, 'source':cleaned_html})

# %% ../06_docexp.ipynb 61
class _HTMLdf(HTMLParser):
    "HTML Parser that finds a dataframe."
    df,scoped = False,False
    def handle_starttag(self, tag, attrs):
        if tag == 'style' and 'scoped' in dict(attrs): self.scoped=True
    def handle_data(self, data):
        if '.dataframe' in data and self.scoped: self.df=True
    def handle_endtag(self, tag):
        if tag == 'style': self.scoped=False
                
    @classmethod
    def search(cls, x):
        parser = cls()
        parser.feed(x)
        return parser.df

# %% ../06_docexp.ipynb 62
@preprocess_cell
def HTMLEscape(cell):
    "Place HTML in a codeblock and surround it with a <HTMLOutputBlock> component."
    if cell.cell_type !='code': return
    for o in cell.outputs:
        if nested_idx(o, 'data', 'text/html'):
            cell.metadata.html_output = True
            html = o['data']['text/html']
            cell.metadata.html_center = not _HTMLdf.search(html)
            o['data']['text/html'] = '```html\n'+html.strip()+'\n```'

# %% ../06_docexp.ipynb 66
_re_hdr_dash = re.compile(r'^#+\s+.*\s+-\s*$', re.MULTILINE)

@preprocess_rm_cell
def RmHeaderDash(cell):
    "Remove headings that end with a dash -"
    src = cell.source.strip()
    return cell.cell_type == 'markdown' and src.startswith('#') and src.endswith(' -')

# %% ../06_docexp.ipynb 70
def default_pps(c):
    "Default Preprocessors for MDX export"
    return [InjectMeta, CleanMagics, BashIdentify, UpdateTags, InsertWarning, TagRemovePreprocessor,
            CleanFlags, CleanShowDoc, RmEmptyCode, StripAnsi, HideInputLines, RmHeaderDash,
            ExtractAttachmentsPreprocessor, ExtractOutputPreprocessor, HTMLEscape]

# %% ../06_docexp.ipynb 71
def doc_exporter(tpl_file, cfg=None, pps=None):
    "A notebook exporter which composes preprocessors"
    pps = pps or default_pps(cfg)
    return _doc_exporter(pps, cfg, tpl_file=tpl_file)

# %% ../06_docexp.ipynb 72
def nb2md(fname, exp=None, dest=None, cfg=None, pps=None, tpl_file='ob.tpl'):
    "Convert notebook to markdown and export attached/output files"
    if isinstance(dest,Path): dest=dest.name
    file = Path(fname)
    assert file.name.endswith('.ipynb'), f'{fname} is not a notebook.'
    assert file.is_file(), f'file {fname} not found.'
    print(f"converting: {file}")
    exp = doc_exporter(cfg=cfg, pps=pps, tpl_file=tpl_file)
    # https://gitlab.kwant-project.org/solidstate/lectures/-/blob/master/execute.py
    fw = FilesWriter()

    try:
        md = exp.from_filename(fname, resources=dict(unique_key=file.stem, output_files_dir=file.stem))
        if dest: fw.build_directory = dest
        return fw.write(*md, notebook_name=file.stem)
    except Exception as e: print(e)
