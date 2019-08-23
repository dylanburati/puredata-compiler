"""
PureData Compiler
=================

This package lets you write PureData patches as Python programs.

  >>> from puredata_compiler import Patch, write_file
  >>> patch = Patch()
  >>> obj, msg = patch.get_creators('obj, msg')
  >>> loadbang = obj('loadbang')
  >>> exclamation = msg('!', loadbang[0])
  >>> obj('print Hello world', exclamation[0])
  >>> write_file('patch.pd', str(patch))
"""

from .api import Patch, write_file


"""
    :""'""'""'""'"";
    *              *
    *    python    *
    *              *
    :######=.......;
      %%
    :#######""'""'""'""'"'"#######;
    *                             *                      
    *                             *
    *   p>>>o.      :d            *
    *   p    o      :d            *
    *   p<<<o.  .d<<<d            *
    *   p,      d    d            *
    *   o.      'd>>>d            *
    *                             *
    *                             *
    :######=......................;

"""