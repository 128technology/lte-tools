"""Load providers in this directory."""

import os
import pkgutil
import importlib

providers = []

# iterate over all python modules in "providers" and add module to list
for _, name, _ in pkgutil.iter_modules([os.path.dirname(__file__)]):
    module = importlib.import_module(__name__ + '.' + name)
    providers.append(module)
