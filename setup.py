
import os
from setuptools import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()
            
setup(name='namedstruct',
      version='0.1',
      description='namedstruct',
      url='https://github.com/TransitApp/namedstruct',
      author='Transit',
      license="Transit",
      package_dir={ 'namedstruct': '.'},
      install_requires=required,
      zip_safe=False
)
