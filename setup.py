#! /usr/bin/env python

import setuptools

with open('README.md', 'rt', encoding='ascii') as f:
    long_description = f.read()

short_description = long_description.split('\n', 1)[0].strip('# ')

with open('requirements.txt', 'rt', encoding='ascii') as f:
    requirements = f.readlines()

setuptools.setup(
        name = 'onsdriver',
        version = '0.1.0',
        description=short_description,
        long_description=long_description,
        long_description_content_type='text/markdown',
        package_dir={'': 'src'},
        packages=setuptools.find_packages(where='src'),
        install_requires=requirements,
        python_requires='>=3.11',
        entry_points={
            'console_scripts': [
                'onsdriver-firsttime=onsdriver.firsttime:main',
                'onsdriver-obsinstall=onsdriver.obsinstall:main',
                'onsdriver-obsplugin=onsdriver.obsplugin:main',
            ],
        },
)
