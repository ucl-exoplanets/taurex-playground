# Scripts

Some useful scripts for taurex.

## Bootstrap Exomol

Downloads exomol cross-sections to a folder of you choice for a given molecule.

Requires

- ``click``

Help:

```bash
Usage: bootstrap_exomol.py [OPTIONS]

Options:
  -m, --molecule [H2O|CH4|NH3|CO2|SO3|SO2|H2CO|PH3]
  -o, --output-dir DIRECTORY
  --help                          Show this message and exit.
```

Example:

```bash
python bootstrap_exomol.py -m H2O -m CH4 --output-dir /path/to/exomol
```