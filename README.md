# PureData Compiler

This package allows you to write patches for [PureData](https://puredata.info) in Python.

## Install

```bash
python -m pip install puredata-compiler  # requires Python >=3.5
```

## Usage

The compiler gives you **creator functions** to compose a patch. These functions
add elements to the patch, using the content and connections you provide.

```python
from puredata_compiler import Patch, write_file


def example():
    """Patch that increments a counter"""
    patch = Patch()
    obj, msg, floatatom, connect = patch.get_creators('obj, msg, floatatom, connect')
 
    bang = msg('bang')
    delay_params = msg('500', new_row=0, new_col=1)
    delay_trig = obj('t b f', delay_params[0])
    delay = obj('delay', delay_trig[0], delay_trig[1])

    start_val = obj('f', (bang[0], delay[0]), x_pos=25, y_pos=125)
    increment = floatatom(new_row=0)
    current_val = obj('+', start_val[0], increment[0])
    # connect is different - it takes an existing element and adds connections,
    # so you can create circular structures
    connect(start_val, (), current_val[0])
    current_val_display = floatatom(current_val[0])

    return patch

if __name__ == "__main__":
    pd_example = example()
    write_file('pd_example.pd', str(pd_example))
```

### Result

![pd_example.pd](https://dylanburati.github.io/assets/puredata-compiler1.png)
