from __future__ import absolute_import
from .namedstruct import *
from .values import *

def generateTests(quiet=False):
    from . import tests
    return tests.generateTests(quiet)

print(__name__)
__import__('pkg_resources').declare_namespace(__name__)
