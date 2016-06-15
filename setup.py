"""
G Container Management
"""
from setuptools import find_packages, setup

dependencies = ['click',                 # command line parsing
                'enum34==1.0.4',          # enum support
                'docker-py==1.1.0',       # docker API
                'urllib3==1.10.3',
                'pycparser==2.10',
                'pyopenssl==0.15.1',      # SSL Support
                'ndg-httpsclient==0.3.3', # SSL Support
                'pyasn1==0.1.7',          # SSL Support
                'iso8601==0.1.10',        # Date and time
               ]

setup(
    name='gcontainer',
    version='1.0',
    url='https://example.com/',
    license='BSD',
    author='Project Secret Unicorn Team',
    author_email='henning@example.com',
    description='G Container Management',
    long_description=__doc__,
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=dependencies,
    entry_points={
        'console_scripts': [
            'gcontainer = gcontainer.cli:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        # 'Development Status :: 5 - Production/Stable',
        # 'Development Status :: 6 - Mature',
        # 'Development Status :: 7 - Inactive',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX',
        'Operating System :: MacOS',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
    ]
)
