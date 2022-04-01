# AUTOGENERATED! DO NOT EDIT! File to edit: ../07_convert.ipynb.

# %% ../07_convert.ipynb 1
from __future__ import annotations
from nbprocess.mdx import *
import os,sys

from nbconvert.exporters import Exporter
from fastcore.all import Path,parallel,call_parse,bool_arg,globtastic

# %% auto 0
__all__ = ['nbprocess_docs']

# %% ../07_convert.ipynb 4
def _needs_update(fname:Path, dest:str=None):
    "Determines if a markdown file should be updated based on modification time relative to its notebook."
    fname_out = fname.with_suffix('.md')
    if dest: fname_out = Path(dest)/f'{fname_out.name}'
    return not fname_out.exists() or os.path.getmtime(fname) >= os.path.getmtime(fname_out)


@call_parse
def nbprocess_docs(
    path:str='.', # path or filename
    dest:str='build', # path or filename
    recursive:bool=True, # search subfolders
    symlinks:bool=True, # follow symlinks?
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
    if not recursive: skip_folder_re='.'
    files = globtastic(path, symlinks=symlinks, file_glob=file_glob, file_re=file_re,
                       folder_re=folder_re, skip_file_glob=skip_file_glob,
                       skip_file_re=skip_file_re, skip_folder_re=skip_folder_re
                      ).map(Path)
    
    if len(files)==1: force_all,n_workers = True,0
    if not force_all:
        files = [f for f in files if _needs_update(f, dest)]
    if len(files)==0: print("No notebooks were modified.")
    else:
        if sys.platform == "win32": n_workers = 0
        passed = parallel(nb2md, files, n_workers=n_workers, pause=pause, dest=dest)
        if not all(passed):
            msg = "Conversion failed on the following:\n"
            print(msg + '\n'.join([f.name for p,f in zip(passed,files) if not p]))
        
