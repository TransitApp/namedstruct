import sys

def ord_if_needed(x):
    if isinstance(x, int):
        return x
    else:
        return ord(x)
