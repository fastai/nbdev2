# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/02_convert.ipynb (unless otherwise specified).


from __future__ import annotations


__all__ = ['DocExporter', 'export_docs']

# Cell
#nbdev_comment from __future__ import annotations
from .docexp import *
import os,sys

from fastcore.imports import *
from nbconvert.exporters import Exporter
from nbprocess.read import get_config
from importlib import import_module
from fastcore.all import Path,parallel,call_parse,bool_arg,globtastic
import shutil

# Cell
class DocExporter:
    "A notebook exporter which composes preprocessors"

    cfg=default_pp_cfg()
    tpl_path=(Path(__file__).parent/'tpl').resolve()
    tpl_file='nb.md.j2'
    pps=default_pps()

    def __init__(self, files, dest): self.files,self.dest = files,Path(dest)

    def post_process(self):
        idx_f = self.dest/'index.md'
        if idx_f.exists(): shutil.copy(idx_f, idx_f.parent/'README.md')

    @property
    def exporter(self): return doc_exporter(self.pps, self.cfg, tpl_file=self.tpl_file, tpl_path=self.tpl_path)
    def __call__(self, file, dest): return nb2md(file, self.exporter, dest=dest)

# Cell
def _needs_update(fname:Path, dest:str=None):
    "Determines if a markdown file should be updated based on modification time relative to its notebook."
    fname_out = fname.with_suffix('.md')
    if dest: fname_out = Path(dest)/f'{fname_out.name}'
    return not fname_out.exists() or os.path.getmtime(fname) >= os.path.getmtime(fname_out)

def _nb2md(file, docexp=None, dest=None):
    print(f"converting: {file}")
    try: return docexp(file, dest=dest)
    except Exception as e: print(f"{file} failed\n{e}")

# Cell
@call_parse
def export_docs(
    path:str='.', # path or filename
    dest:str=None, # path or filename
    recursive:bool=True, # search subfolders
    symlinks:bool=True, # follow symlinks?
    exporter:str=None, # DocExporter subclass for SSG
    n_workers:int=None, # Number of parallel workers
    pause:int=0, # Pause between parallel launches
    force_all:bool=False, # Force rebuild docs that are up-to-date
    file_glob:str='*.ipynb', # Only include files matching glob
    file_re:str=None, # Only include files matching regex
    folder_re:str=None, # Only enter folders matching regex
    skip_file_glob:str=None, # Skip files matching glob
    skip_file_re:str=None, # Skip files matching regex
    skip_folder_re:str='^[_.]' # Skip folders matching regex
):
    dest = get_config().path("doc_path") if not dest else Path(dest)
    if exporter is None: exporter = get_config().get('exporter', None)
    if exporter is None: exp_cls=DocExporter
    else:
        p,m = exporter.rsplit('.', 1)
        exp_cls = getattr(import_module(p), m)
    if not recursive: skip_folder_re='.'
    files = globtastic(path, symlinks=symlinks, file_glob=file_glob, file_re=file_re,
                       folder_re=folder_re, skip_file_glob=skip_file_glob,
                       skip_file_re=skip_file_re, skip_folder_re=skip_folder_re
                      ).map(Path)

    if str(path).endswith('.ipynb'): force_all,n_workers = True,0
    if not force_all: files = [f for f in files if _needs_update(f, dest)]
    if sys.platform == "win32": n_workers=0
    docexp = exp_cls(files, dest)
    if len(files)==0: print("No notebooks were modified.")
    else: parallel(_nb2md, files, docexp=docexp, n_workers=n_workers, pause=pause, dest=dest)
    docexp.post_process()