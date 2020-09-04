
import os
from setuptools import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()
            
setup(name='namedstruct',
      version='0.1',
      description='Compressor for sharing system map layers to the bpin format',
      url='https://github.com/TransitApp/pyTransitTools',
      author='Transit',
      license="Transit",
      packages=['namedstruct'],
      package_dir={ 'namedstruct': '.'},
      install_requires=required,
      zip_safe=False
)   
