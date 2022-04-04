## Docs export

- Implement [`show_doc`](https://github.com/fastai/nbdev/blob/master/nbs/02_showdoc.ipynb) in markdown/HTML
  - Pluggable parsers for parameter docs
    - docments
    - numpy
- Optionally execute `show_doc` cells
- auto-add `show_doc`
  - support `#default_cls_lvl`
- implement `#collapse_input`, `#collapse_output`, `#hide_output`, `#hide_input`
  - this is already in the mkdocs template
- Back-tick linking
- implement stuff from nbdev export2html, e.g.(?):
  - `remove_widget_state`
- tmp.ipynb tests are flaky

