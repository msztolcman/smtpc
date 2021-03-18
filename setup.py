from setuptools import setup, find_packages

requirements = [
    'structlog',
    'fileperms',
    'toml',
]
extras_requirements = {
    'extended': ['Jinja2'],
}

with open('README.md') as f:
    readme = f.read()

setup(
    name='smtpc',
    version='0.6.0',
    description='',
    long_description=readme,
    long_description_content_type='text/markdown',
    url='https://github.com/msztolcman/smtpc',
    project_urls={
        'GitHub: issues': 'https://github.com/msztolcman/smtpc/issues',
        'GitHub: repo': 'https://github.com/msztolcman/smtpc',
    },
    download_url='https://github.com/msztolcman/smtpc',
    author='Marcin Sztolcman',
    author_email='marcin@urzenia.net',
    license='MIT',
    zip_safe=False,
    include_package_data=True,
    packages=find_packages(),
    python_requires='>=3.7',
    entry_points={
        'console_scripts': [
            'smtpc = smtpc.cli:main',
        ],
    },
    install_requires=requirements,
    extras_require=extras_requirements,
    # see: https://pypi.python.org/pypi?:action=list_classifiers
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Communications :: Email',
        'Topic :: Utilities',
        'Topic :: Software Development',
    ]
)
