from setuptools import setup, find_packages


setup(entry_points={'console_scripts': ['tarsync = tarsync.tarsync:main']},
      name="tarsync",
      version='1.0.0',
      options = {},
      description='Syncs application data between systems',
      author='Carl Backstrom',
      packages=find_packages(),
      data_files=[('/etc/tarsync', ['config/config.json'])]
)
