from setuptools import setup

setup(name='USBMaker',
      version='1.0.0',
      packages=['USBMaker'],
      install_requires=['PyQt5'],
      url='https://github.com/gmes/USBMaker',
      license='GPL',
      entry_points={'gui_scripts': ['usbmaker = USBMaker.main']})
