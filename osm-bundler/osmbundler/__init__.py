import logging
import sys, os, getopt, tempfile, subprocess
import sqlite3

from PIL import Image
from PIL.ExifTags import TAGS

import defaults

import matching
from matching import *

import features
from features import *



distrPath = os.path.dirname( os.path.abspath(sys.argv[0]) )
bundlerExecutable = ''
if sys.platform == "win32": bundlerExecutable = os.path.join(distrPath, "software/bundler/bin/bundler.exe")
else: bundlerExecutable = os.path.join(distrPath, "software/bundler/bin/bundler")

SCALE = 1.0
bundlerListFileName = "list.txt"

camerasDatabase = os.path.join(distrPath, "osmbundler/cameras/cameras.sqlite")
commandLineLongFlags = ["photos=", "maxPhotoDimension=", "featureExtractor="]
exifAttrs = dict(Model=True,Make=True,ExifImageWidth=True,ExifImageHeight=True,FocalLength=True)


class OsmBundler():

    currentDir = ""

    workDir = ""
    
    # value of command line argument --photos=<..>
    photosArg = ""
    
    featureExtractor = None
    
    matchingEngine = None
    
    # sqlite cursor
    dbCursor = None
    
    # list of photos with focal distances for bundler input
    bundlerListFile = None
    
    # list of files with extracted features
    featuresListFile = None
    
    # information about each processed photo is stored in the following dictionary
    # photo file name in self.workDir is used as the key in this dictionary
    photoDict = {}

    def __init__(self):
        for attr in dir(defaults):
            if attr[0]!='_':
                setattr(self, attr, getattr(defaults, attr))
        
        self.parseCommandLineFlags()

        # save current directory (i.e. from where RunBundler.py is called)
        self.currentDir = os.getcwd()
        # create a working directory
        self.workDir = tempfile.mkdtemp(prefix="osm-bundler-")
        logging.info("Working directory created: "+self.workDir)
        
        if not (os.path.isdir(self.photosArg) or os.path.isfile(self.photosArg)):
            raise Exception, "'%s' is neither directory nor a file name" % self.photosArg
        
        # initialize mathing engine based on command line arguments
        self.initMatchingEngine()

        # initialize feature extractor based on command line arguments
        self.initFeatureExtractor()

    def parseCommandLineFlags(self):
        try:
            opts, args = getopt.getopt(sys.argv[1:], "", commandLineLongFlags)
        except getopt.GetoptError:
            self.printHelpExit()

        for opt,val in opts:
            if opt=="--photos":
                self.photosArg = val
            elif opt=="--maxPhotoDimension":
                if val.isdigit() and int(val)>0: self.maxPhotoDimension = int(val)
            elif opt=="--matchingEngine":
                self.matchingEngine = val
            elif opt=="--featureExtractor":
                self.featureExtractor = val
            elif opt=="--help":
                self.printHelpExit()
        
        if self.photosArg=="": self.printHelpExit()

    def preparePhotos(self):
        # open each photo, resize, convert to pgm, copy it to self.workDir and calculate focal distance
        # conversion to pgm is performed by PIL library
        # EXIF reading is performed by PIL library
        
        # open connection to cameras database
        conn = sqlite3.connect(camerasDatabase)
        self.dbCursor = conn.cursor()
        
        # open list of photos with focal distances for bundler input
        self.bundlerListFile = open(os.path.join(self.workDir,bundlerListFileName), "w")
        
        # open list of files with extracted features
        if self.matchingEngine.featureExtractionNeeded:
            self.featuresListFile = open(os.path.join(self.workDir,self.matchingEngine.featuresListFileName), "w")

        if os.path.isdir(self.photosArg):
            # directory with images
            photos=[f for f in os.listdir(self.photosArg) if os.path.isfile(os.path.join(self.photosArg, f)) and os.path.splitext(f)[1].lower()==".jpg"]
            if len(photos)<3: raise Exception, "The directory with images should contain at least 3 .jpg photos"
            for photo in photos:
                photoInfo = dict(dirname=self.photosArg, basename=photo)
                self._preparePhoto(photoInfo)
        elif os.path.isfile(self.photosArg):
            # a file with a list of images
            photosFile = open(self.photosArg)
            # an auxiliary dictionary to eliminate duplicated photos
            _photoDict = {}
            for photo in photosFile:
                photo = photo.rstrip()
                if os.path.isfile(photo):
                    if not photo in _photoDict:
                        _photoDict[photo] = True
                        dirname,basename = os.path.split(photo)
                        photoInfo = dict(dirname=dirname, basename=basename)
                        self._preparePhoto(photoInfo)
            photosFile.close()

        if self.featuresListFile: self.featuresListFile.close()
        self.bundlerListFile.close()
        self.dbCursor.close()


    def _preparePhoto(self, photoInfo):
        photo = photoInfo['basename']
        photoDir = photoInfo['dirname']
        logging.info("\nProcessing photo '%s':" % photo)
        inputFileName = os.path.join(photoDir, photo)
        photo = self._getPhotoCopyName(photo)
        outputFileNameJpg = "%s.jpg" % os.path.join(self.workDir, photo)
        outputFileNamePgm = "%s.pgm" % outputFileNameJpg
        # open photo
        photoHandle = Image.open(inputFileName)
        # get EXIF information as a dictionary
        exif = self._getExif(photoHandle)
        self._calculateFocalDistance(photo, photoInfo, exif)
        
        # resize photo if necessary
        maxDimension = photoHandle.size[0]
        if photoHandle.size[1]>maxDimension: maxDimension = photoHandle.size[1]
        if maxDimension > self.maxPhotoDimension:
            scale = float(self.maxPhotoDimension)/float(maxDimension)
            newWidth = int(scale * photoHandle.size[0])
            newHeight = int(scale * photoHandle.size[1])
            photoHandle = photoHandle.resize((newWidth, newHeight))
            logging.info("\tCopy of the photo has been scaled down to %sx%s" % (newWidth,newHeight))
        
        photoInfo['width'] = photoHandle.size[0]
        photoInfo['height'] = photoHandle.size[1]
        
        photoHandle.save(outputFileNameJpg)
        photoHandle.convert("L").save(outputFileNamePgm)
        
        # put photoInfo to self.photoDict
        self.photoDict[photo] = photoInfo
        
        if self.matchingEngine.featureExtractionNeeded:
            self.extractFeatures(photo)
        os.remove(outputFileNamePgm)


    def _getPhotoCopyName(self, photo):
        # cut off the extension
        photo = photo[:-4]
        # replace spaces in the file name
        photo = photo.replace(' ', '_')
        # find a unique name
        suffix = 1
        while photo in self.photoDict:
            photo = "%s_%s" % (photo, suffix)
            suffix = suffix + 1
        return photo


    def _getExif(self, photoHandle):
        exif = {}
        info = photoHandle._getexif()
        if info:
            for attr, value in info.items():
                decodedAttr = TAGS.get(attr, attr)
                if decodedAttr in exifAttrs: exif[decodedAttr] = value
        if 'FocalLength' in exif: exif['FocalLength'] = float(exif['FocalLength'][0])/float(exif['FocalLength'][1])
        return exif
    
    def _calculateFocalDistance(self, photo, photoInfo, exif):
        hasFocal = False
        if 'Make' in exif and 'Model' in exif:
            # check if have camera entry in the database
            self.dbCursor.execute("select ccd_width from cameras where make=? and model=?", (exif['Make'].strip(),exif['Model'].strip()))
            ccdWidth = self.dbCursor.fetchone()
            if ccdWidth:
                if 'FocalLength' in exif and 'ExifImageWidth' in exif and 'ExifImageHeight' in exif:
                    focalLength = float(exif['FocalLength'])
                    width = float(exif['ExifImageWidth'])
                    height = float(exif['ExifImageHeight'])
                    if focalLength>0 and width>0 and height>0:
                        if width<height: width = height
                        focalPixels = width * (focalLength / ccdWidth[0])
                        hasFocal = True
                        self.bundlerListFile.write("%s.jpg 0 %s\n" % (photo,SCALE*focalPixels))
            else: logging.info("\tEntry for the camera '%s', '%s' does not exist in the camera database" % (exif['Make'], exif['Model']))
        if not hasFocal:
            logging.info("\tCan't estimate focal length in pixels for the photo '%s'" % os.path.join(photoInfo['dirname'],photoInfo['basename']))
            self.bundlerListFile.writelines("%s.jpg\n" % photo)


    def initMatchingEngine(self):
        try:
            matchingEngine = getattr(matching, self.matchingEngine)
            matchingEngineClass = getattr(matchingEngine, matchingEngine.className)
            self.matchingEngine = matchingEngineClass(os.path.join(distrPath, "software"))
        except:
            raise Exception, "Unable initialize matching engine %s" % self.featureExtractor

    def initFeatureExtractor(self):
        try:
            featureExtractor = getattr(features, self.featureExtractor)
            featureExtractorClass = getattr(featureExtractor, featureExtractor.className)
            self.featureExtractor = featureExtractorClass(os.path.join(distrPath, "software"))
        except:
            raise Exception, "Unable initialize feature extractor %s" % self.featureExtractor

    def extractFeatures(self, photo):
        # let self.featureExtractor do its job
        os.chdir(self.workDir)
        self.featureExtractor.extract(photo, self.photoDict[photo])
        self.featuresListFile.write("%s.%s\n" % (photo, self.featureExtractor.fileExtension))
        os.chdir(self.currentDir)
    
    def matchFeatures(self):
        # let self.matchingEngine do its job
        os.chdir(self.workDir)
        self.matchingEngine.match()
        os.chdir(self.currentDir)
    
    def doBundleAdjustment(self):
        # just run Bundler here
        logging.info("\nPerforming bundle adjustment...")
        os.chdir(self.workDir)
        os.mkdir("bundle")
        
        # create options.txt
        optionsFile = open("options.txt", "w")
        optionsFile.writelines(defaults.bundlerOptions)
        optionsFile.close()

        bundlerOutputFile = open("bundle/out", "w")
        subprocess.call([bundlerExecutable, "list.txt", "--options_file", "options.txt"], **dict(stdout=bundlerOutputFile))
        bundlerOutputFile.close()
        os.chdir(self.currentDir)
        logging.info("Finished!")
    
    def printHelpExit(self):
        self.printHelp()
        sys.exit(2)
    
    def openResult(self):
        if sys.platform == "win32": subprocess.call(["explorer", self.workDir])
        else: print "See the results in the '%s' directory" % self.workDir
    
    def printHelp(self):
        helpFile = open(os.path.join(distrPath, "osmbundler/help.txt"), "r")
        print helpFile.read()
        helpFile.close()


# service function: get path of an executable (.exe suffix is added if we are on Windows)
def getExecPath(dir, fileName):
    if sys.platform == "win32": fileName = "%s.exe" % fileName
    return os.path.join(dir, fileName)