from setuptools import setup, find_packages

setup(
    name='patheng',
    version='0.3',
    description='Standard Pathway Engineering automation tools',

    author='Kent Coble, Seth Lawlor',
    author_email='coblekent@gmail.com, sethclaw10@gmail.com',
    url='https://bitbucket.org/pathwayengineering/patheng',

    packages=find_packages(),
    install_requires=[
        'pyelasticsearch>=1.4',
        'requests>=2.10'
    ],
    use_2to3=True
)
