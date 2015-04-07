# Introduction #
Instead of downloading ready to use Bundler distribution, you can compose it yourself from several pieces.

# Details #

  * Install Python
  * Install PIL library from http://www.pythonware.com/products/pil/
  * Download Python scripts from http://osm-bundler.googlecode.com/files/osm-bundler.zip and unpack them. _osm-bundler_ will be the top level directory in the distribution.
  * Create _software_ directory in the _osm-bundler_ directory

Install Bundler:
  * Create _bundler_ directory in the _osm-bundler/software_ directory.
  * Download the latest Bundler binaries from http://phototour.cs.washington.edu/bundler/
  * Unpack _bin_ directory from the Bundler distribution to the _osm-bundler/software/bundler_ directory

Install VLFeat library:
  * Create _vlfeat/bin_ directory in the _osm-bundler/software_ directory.
  * Download the latest VLFeat library binaries from http://www.vlfeat.org/download.html
  * Unpack _vlfeat/bin/w32_ and _vlfeat/bin/glx_ directories from the VLFeat distribution to the _osm-bundler/software/vlfeat/bin_ directory

Optionally you can install SIFT demo distribution developed by David Lowe:
  * Create _sift-lowe_ directory in the _osm-bundler/software_ directory.
  * Download SIFT demo distribution from http://people.cs.ubc.ca/~lowe/keypoints/
  * Unpack _sift_ and _siftWin32.exe_ files from the SIFT demo distribution to the _osm-bundler/software/sift-lowe_