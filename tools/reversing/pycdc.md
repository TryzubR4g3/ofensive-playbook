# pycdc

Python bytecode decompiler used to recover readable Python source from `.pyc` files. Used on: **Aster**.

## Commands Used

### Decompile a Python bytecode file

```bash
./pycdc /output.pyc
```

Used on: **Aster**

recovered obfuscated Python that decoded hex strings into useful hints.

## Notes

- If output still contains obfuscation, copy the recovered source into a `.py` file and execute only after reviewing it.
- For Python 2 bytecode, test with `python2` if the recovered code uses Python 2 syntax.
