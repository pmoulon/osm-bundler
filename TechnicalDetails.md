# Motivation #

This project can considered as a first step towards open source equivalent of Microsoft Photosynth. Microsoft Photosynth desktop application takes a set of overlapping photos and tries to calculate for each photo its relative camera position in 3D space. Also it reconstructs a sparse set of 3D points that represent some points on the photos. Then the photos and the results of 3D reconstruction are uploaded to the Microsoft dedicated server and used in web-based pseudo-3D application.

There is a open source command line predecessor to Microsoft Photosynth called [bundler](http://phototour.cs.washington.edu/bundler/) and developed in the University of Washington. Microsoft licensed it and developed further to the stage which is now known as Microsoft Photosynth.

To run the original bundler software is not an easy task (especially on Windows). What we have developed is a "facade" application (in the sense of facade software design pattern) for the original bundler software.


# Details #

Here are the basic steps in the processing pipeline in our application:

1. Get a set of photos from a user (e.g. as a directory with photos)

2. Prepare photos:
  * scale each photo down if it is too large
  * extract camera model from EXIF tags and check if the camera is in the supplied sqlite    database of cameras
  * extract features from each photo
Arbitrary feature extraction programs can be used, provided that a wrapper class is written for it. Each such wrapper class should be derived from [FeatureExtractor class](http://code.google.com/p/osm-bundler/source/browse/trunk/osm-bundler/osmbundler/features/extractor.py). Two feature extraction classes are provided in our application. They can be found [here](http://code.google.com/p/osm-bundler/source/browse/trunk/osm-bundler/osmbundler/features/) .

3. Perform matching of the extracted image features. A program from the original bundler software is invoked for this task by default. This is done by [BundlerMatching class](http://code.google.com/p/osm-bundler/source/browse/trunk/osm-bundler/osmbundler/matching/bundler.py) . Alternatively another matching program can be utilized, provided that a wrapper class is written for it.

4. Perform so called bundler adjustment.  A program from the original bundler software is invoked for this task in the main manager class.

5. Open the directory with the results of operation. The results are relative 3D positions of cameras and a sparse set of reconstructed 3D points. They can be examined in some 3D viewers and used for further processing.

The processing pipeline is reflected in the small Python script [RunBundler.py](http://code.google.com/p/osm-bundler/source/browse/trunk/osm-bundler/RunBundler.py)

Normally all a user needs to do to start my application is to provide a directory with photos:
python path\_to/RunBundler.py --photo=<text file with a list of photos or a directory with photos>

Other feature extractors can be specified with a special flag.