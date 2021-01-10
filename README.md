# genery
Generic dev utils

**utils**:

- `calcs` - calculations (re-scaling, etc.)
- `cmd` - command line and file operations
- `containers` - operations with container-like classes (lists, dictionaries, etc.)
- `datetimeutils` - delf.
- `textutils` - operations with text (including URLs).

## Usage
Clone this repo or add it to your requirements:

    -e git+https://github.com/deniskolokol/genery.git#egg=genery
In you code:

    from genery import utils
    
    rec = utils.RecordDict(unit=123)
    print(rec.unit)
    >>> 123

See unit-tests for more use cases and examples.

## Unit-tests

    $ python tests.py
