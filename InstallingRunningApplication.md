The easiest way to install osm-bundler is described here. Alternatively you can compose it yourself from several pieces. See CreateDistributionYourself for the details.

# Installation #
  * Install Python
  * Install PIL library for Python from http://www.pythonware.com/products/pil/
  * Download the osm-bundler distribution http://osm-bundler.googlecode.com/files/osm-bundler-full.zip and unpack it.

Linux users may need to take two additional steps:
  * Install libgfortran.so.3: `sudo apt-get install libgfortran3`
  * Specify where the libANN\_char.so library is by typing: `export LD_LIBRARY_PATH="/pathto/osm-bundler/software/bundler/bin"`


# Running #
Normally you would run osm-bundler in the following way:
> python path\_to/RunBundler.py --photo=<text file with a list of photos or a directory with photos>

To see help just run:
> python path\_to/RunBundler.py

# Photo test set #
You could try our photo test set: http://osm-bundler.googlecode.com/files/example_OldTownHall.zip