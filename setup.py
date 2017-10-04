from setuptools import setup, find_packages


setup(
    name='aiolocals',
    version='0.2.4',
    description='aiolocals is a library for task local state management with '
                'aiohttp integration for tracking request ids.',
    packages=find_packages(),
    include_package_data=True,
    url='https://bitbucket.org/hipchat/aiolocals/',
    zip_safe=False,
)
