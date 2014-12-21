import os
import unittest
import math
import numpy
from __main__ import vtk, qt, ctk, slicer

#
# MurineTrial
#
#

comment = '''

Run from bash:

/Applications/Slicer-4.4.0.app/Contents/MacOS/Slicer --additional-module-paths ~/Dropbox/0_work/novartis/muscles/MurineTrial

'''

class MurineTrial:
  def __init__(self, parent):
    parent.title = "Murine Trial"
    parent.categories = ["Wizards"]
    parent.dependencies = []
    parent.contributors = ["Steve Pieper (Isomics)"]
    parent.helpText = """
This is a specialized module for processing Novartis muscle data for volumetrics of murine (mouse and rat) MR scans.
The scans have been segmented according to a specialized protocol.
Several of the methods are specialized to handle the data file paths
that evolved of the course of the project.
    """
    parent.acknowledgementText = """
    This file was developed by Steve Pieper, Isomics, Inc. in collaboration with Novartis and Attila Nagy.
"""
    self.parent = parent

    # Add this test to the SelfTest module's list for discovery when the module
    # is created.  Since this module may be discovered before SelfTests itself,
    # create the list if it doesn't already exist.
    try:
      slicer.selfTests
    except AttributeError:
      slicer.selfTests = {}
    slicer.selfTests['MurineTrial'] = self.runTest

  def runTest(self):
    tester = MurineTrialTest()
    tester.runTest()

#
# qMurineTrialWidget
#

class MurineTrialWidget:
  def __init__(self, parent = None):
    if not parent:
      self.parent = slicer.qMRMLWidget()
      self.parent.setLayout(qt.QVBoxLayout())
      self.parent.setMRMLScene(slicer.mrmlScene)
    else:
      self.parent = parent
    self.layout = self.parent.layout()
    if not parent:
      self.setup()
      self.parent.show()

    self.logic = MurineTrialLogic()

  def setup(self):
    # Instantiate and connect widgets ...

    # reload button
    # (use this during development, but remove it when delivering
    #  your module to users)
    self.reloadButton = qt.QPushButton("Reload")
    self.reloadButton.toolTip = "Reload this module."
    self.reloadButton.name = "MurineTrial Reload"
    self.layout.addWidget(self.reloadButton)
    self.reloadButton.connect('clicked()', self.onReload)

    # reload and test button
    # (use this during development, but remove it when delivering
    #  your module to users)
    self.reloadAndTestButton = qt.QPushButton("Reload and Test")
    self.reloadAndTestButton.toolTip = "Reload this module and then run the self tests."
    self.layout.addWidget(self.reloadAndTestButton)
    self.reloadAndTestButton.connect('clicked()', self.onReloadAndTest)

    # Collapsible button
    measurementsCollapsibleButton = ctk.ctkCollapsibleButton()
    measurementsCollapsibleButton.text = "Materials"
    self.layout.addWidget(measurementsCollapsibleButton)

    # Layout within the measurements collapsible button
    measurementsFormLayout = qt.QFormLayout(measurementsCollapsibleButton)

    # list of measurements in the trial
    self.scrollArea = qt.QScrollArea()
    measurementsFormLayout.addWidget(self.scrollArea)
    self.listWidget = qt.QListWidget()
    self.scrollArea.setWidget(self.listWidget)
    self.scrollArea.setWidgetResizable(True)
    self.listWidget.setProperty('SH_ItemView_ActivateItemOnSingleClick', 1)
    self.listWidget.connect('activated(QModelIndex)', self.onMaterialActivated)
    # populate it
    materialKeys = self.logic.materials.keys()
    materialKeys.sort()
    for materialKey in materialKeys:
      self.listWidget.addItem(materialKey)

    # process all  button
    processAllButton = qt.QPushButton("Process All")
    processAllButton.toolTip = "Loads all subjecs at all timepoints."
    measurementsFormLayout.addWidget(processAllButton)
    processAllButton.connect('clicked(bool)', self.logic.processAll)

    # results area
    self.resultsView = qt.QWebView()
    self.resultsView.minimumSize = qt.QSize(100,100)
    policy = qt.QSizePolicy()
    policy.setHorizontalPolicy(qt.QSizePolicy.Ignored)
    self.resultsView.setSizePolicy(policy)
    self.layout.addWidget(self.resultsView)

    # Add vertical spacer
    self.layout.addStretch(1)

  def updateResults(self):
    html = ''
    html += str(self.currentData)
    html += '<br>'
    html += '<b>Fat Ratio: %s</b>' % str(self.fatRatioMeasurement)
    self.resultsView.setHtml(html)

  def onMaterialActivated(self,modelIndex):
    print('selected row %d' % modelIndex.row())
    material = self.logic.materials[modelIndex.data()]

    slicer.util.loadVolume(material['mrPath'])
    slicer.util.loadVolume(material['segPath'], {'labelmap': True})

    self.resultsView.setHtml("loaded {}".format(material) )

  def onReload(self,moduleName="MurineTrial"):
    """Generic reload method for any scripted module.
    ModuleWizard will subsitute correct default moduleName.
    """
    import imp, sys, os, slicer

    widgetName = moduleName + "Widget"

    # reload the source code
    # - set source file path
    # - load the module to the global space
    filePath = eval('slicer.modules.%s.path' % moduleName.lower())
    p = os.path.dirname(filePath)
    if not sys.path.__contains__(p):
      sys.path.insert(0,p)
    fp = open(filePath, "r")
    globals()[moduleName] = imp.load_module(
        moduleName, fp, filePath, ('.py', 'r', imp.PY_SOURCE))
    fp.close()

    # rebuild the widget
    # - find and hide the existing widget
    # - create a new widget in the existing parent
    parent = slicer.util.findChildren(name='%s Reload' % moduleName)[0].parent()
    for child in parent.children():
      try:
        child.hide()
      except AttributeError:
        pass
    # Remove spacer items
    item = parent.layout().itemAt(0)
    while item:
      parent.layout().removeItem(item)
      item = parent.layout().itemAt(0)

    # delete the old widget instance
    if hasattr(slicer.modules, widgetName):
      w = getattr(slicer.modules, widgetName)
      if hasattr(w, 'cleanup'):
        w.cleanup()

    # create new widget inside existing parent
    widget = eval('globals()["%s"].%s(parent)' % (moduleName, widgetName))
    #widget = eval('reloaded_module.%s(parent)' % widgetName)
    widget.setup()
    setattr(slicer.modules, widgetName, widget)

  def onReloadAndTest(self,moduleName="MurineTrial"):
    try:
      self.onReload()
      evalString = 'globals()["%s"].%sTest()' % (moduleName, moduleName)
      tester = eval(evalString)
      tester.runTest()
    except Exception, e:
      import traceback
      traceback.print_exc()
      qt.QMessageBox.warning(slicer.util.mainWindow(),
          "Reload and Test", 'Exception!\n\n' + str(e) + "\n\nSee Python Console for Stack Trace")


#
# helper class of for measurements
#
class measurements(object):
  """Store a tagged list of samples"""
  def __init__(self):
    self.label = "Unspecified" # a descriptive unique identifier name
    self.subject = "Unspecified" # subject id within trial
    self.property = "Unspecified" # the thing being measured (e.g. muscleVolumeCC or fatRatio)
    self.timepoint = "Unspecified" # code for timepoint (e.g. Baseline, EndOfStudy)
    self.samples = [] # list of samples of this measurement (for test/retest)
    self.labelFiles = [] # labelmap nrrd file path
    self.rawFiles = [] # list of lists of dicom file path

    self.labels = ("Label","Subject","Property","Timepoint","Samples","LabelFiles", "RawFiles")

  def __repr__(self):
    values = (self.label, self.subject, self.property, 
        self.timepoint, self.samples, self.labelFiles, self.rawFiles)
    rep = ""
    for label,value in zip(self.labels,values):
      rep += "%s: %s, " % (label, str(value))
    return rep[:-2]

  def _subjects(self,measurementsList):
    subjects = []
    for m in measurementsList:
      if m.subject not in subjects:
        subjects.append(m.subject)
    return(subjects)

  def _toJSONFile(self,filePath):
    import json
    jsonMeasurement = {}
    for at in dir(self):
      if not at.startswith('_'):
        jsonMeasurement[at] = getattr(self,at)
    fp = open(filePath,"w")
    json.dump(jsonMeasurement, fp)
    fp.close()



#
# MurineTrialLogic
#

class MurineTrialLogic:
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget
  """
  def __init__(self,dataRoot=None,experiment=None):
    self.dataRoot = dataRoot
    self.experiment = experiment

    if not self.dataRoot:
      self.dataRoot = "/Users/pieper/privatedata/novartis/rodents/Data Files"

    print("loading data for experiment %s" % self.experiment)
    self.materials = self.collectMaterials()

  def processAll(self):
    print("TODO: processAll")
    for material in self.materials:
      print("processing %s" % material.label)

  # HACK: duplicated from testing - should be cleaned up really...
  def delayDisplay(self,message,msec=1000):
    """This utility method displays a small dialog and waits.
    This does two things: 1) it lets the event loop catch up
    to the state of the test so that rendering and widget updates
    have all taken place before the test continues and 2) it
    shows the user/developer/tester the state of the test
    so that we'll know when it breaks.
    """
    print(message)
    self.info = qt.QDialog()
    self.infoLayout = qt.QVBoxLayout()
    self.info.setLayout(self.infoLayout)
    self.label = qt.QLabel(message,self.info)
    self.infoLayout.addWidget(self.label)
    qt.QTimer.singleShot(msec, self.info.close)
    self.info.exec_()

  def collectMaterials(self):
    """get the list of available data from the files"""

    species = ('mouse', 'rat')
    subjects = range(1,16)
    times = range(1,5)
    methods = ("Novartis-base", "Slicer-seg", "Slicer-seg-corr", "Slicer-seg-corr-Novartis", "Slicer-seg-corr-2")

    keys = {"species", "subjects", "times", "methods"}
    materials = {}
    for key in keys:
      materials[key] = set()
    
    for specie in species:
      for subject in subjects:
        for time in times:
          for method in methods:
            sampleName = "{}{}time{}".format(specie,subject,time)
            # handle the different naming conventions
            material = {}
            if method == "Novartis-base":
              material['mrPath'] = os.path.join(self.dataRoot,sampleName+".hdr")
              material['segPath'] = os.path.join(self.dataRoot,sampleName+"_seg.hdr")
            else:
              material['mrPath'] = os.path.join(self.dataRoot,method,sampleName+".nrrd")
              material['segPath'] = os.path.join(self.dataRoot,method,sampleName+"-label.nrrd")
            # add an entry to the materials
            if os.path.exists(material['mrPath']) and os.path.exists(material['segPath']):
              materials['species'].add(specie)
              materials['subjects'].add(subject)
              materials['times'].add(time)
              materials['methods'].add(method)
              label = method + '-' + sampleName
              materials[label] = material
    return(materials) 


    tests = ("", "1", "2", "3", "4")

    # TODO: retests
    for test in tests:
      pass

  def endOf2013reretestStatistics(self,targetDirectory):
    """Calculate the label statistics and put them in a csv file in the target"""

    musclesByIndex = {
        1 : "SM",
        2 : "RF",
        3 : "VLI",
        4 : "TFL",
        5 : "SAR",
        6 : "GRA",
        7 : "ST",
        8 : "BFL",
        9 : "BFB",
        10 : "VM",
        11 : "ADD",
    }

    subjects = (
        "0001-01001",
        "0003-30005",
    )

    studyPaths = (
        "0001-01001/progress/0001-01001-Wk24D169-L",
        "0001-01001/round2/0001-01001-Wk24D169-L",
        "0001-01001/round3/0001-01001-Wk24D169-L",

        "0003-30005/progress/0003-30005-EOS-R",
        "0003-30005/round2/0003-30005-EOS-R",
        "0003-30005/round3/0003-30005-EOS-R",
    )

    classmapArchetypeFilePaths = {
        "0001-01001" : "0001-01001/3303_1001_Thigh_Left_Tracked/Followup_Wk24Day169/Edit Muscle and Fat Regions/classmap/Band0/dicom000.dcm",
        "0003-30005" : "0003-30005/3307_30005_Thigh_Right_Tracked/End of Study/Edit Muscle and Fat Regions/classmap/Band0/dicom000.dcm",
    }

    muscleStats = {}
    fatStats = {}

    for studyPath in studyPaths:
      studyRoot = os.path.join(self.dataRoot, studyPath)
      subjectID, testPoint, subjectStudy = studyPath.split('/')
      mrFilePath = os.path.join(studyRoot, subjectStudy + ".nrrd")
      labelFilePath = os.path.join(studyRoot, subjectStudy + "-label.nrrd")

      if testPoint == "progress":
        testPoint = "round1" # for consistency

      mrVolume = slicer.util.loadVolume(mrFilePath, returnNode=True)[1]
      properties = {}
      properties['labelmap'] = True
      labelVolume = slicer.util.loadVolume(labelFilePath, properties, returnNode=True)[1]
      labelArray = slicer.util.array(labelVolume.GetID())

      # load the CRO-provided overall label map
      classmapPath = os.path.join(self.dataRoot, classmapArchetypeFilePaths[subjectID])
      print(classmapPath)
      classmap = slicer.util.loadVolume(classmapPath, returnNode=True)[1]

      # use the same physical mapping for all volumes, since
      # they should all be in the same pixel space
      # but:
      # -- the CRO provided DICOM files have embedded NULL
      #    characters in PixelSpacing so they do not always load correctly
      mrIJKToRAS = vtk.vtkMatrix4x4()
      mrVolume.GetIJKToRASMatrix(mrIJKToRAS)
      classmap.SetIJKToRASMatrix(mrIJKToRAS)

      # make an array that is 1 where there is fat, 0 elsewhere
      classmapArray = slicer.util.array(classmap.GetID())
      if len(classmapArray.shape) > 3 and classmapArray.shape[3] > 1:
        # color image, so IMAT is non-zero green component
        fatArray = classmapArray.transpose()[1].transpose()
        fatArray[fatArray != 0] = 1

      repeatLabel = subjectStudy + "-" + testPoint
      statFilePath = os.path.join(targetDirectory, repeatLabel + "-statistics.csv")

      import LabelStatistics
      statLogic = LabelStatistics.LabelStatisticsLogic(mrVolume, labelVolume)
      statLogic.saveStats(statFilePath)

      for muscleIndex in range(1,12):
        muscleLabelStats = statLogic.labelStats[muscleIndex,"Volume cc"]
        muscleStats[subjectID,testPoint,muscleIndex] = muscleLabelStats
        muscleArray = numpy.array(labelArray,dtype='float32')
        muscleArray[muscleArray != muscleIndex] = 0
        muscleArray[muscleArray == muscleIndex] = 1
        imatArray = muscleArray * fatArray
        fatRatio = imatArray.sum() / muscleArray.sum()
        fatStats[subjectID,testPoint,muscleIndex] = fatRatio



    fp = open(os.path.join(targetDirectory,"summary.csv"), "w")
    fp.write("Subject,Muscle,Volume 1 cc,Volume 2 cc,Volume 3 cc,Ratio 1,Ratio 2,Ratio 3\n");
    for subject in subjects:
      for muscleIndex in range(1,12):
        csvLine = "%s,%s" % (subject,musclesByIndex[muscleIndex])
        for point in range(1,4):
          testPoint = "round%d" % point
          csvLine += ",%s" % str(muscleStats[subjectID,testPoint,muscleIndex])
        for point in range(1,4):
          testPoint = "round%d" % point
          csvLine += ",%s" % str(fatStats[subjectID,testPoint,muscleIndex])
        csvLine += "\n"
        fp.write(csvLine)
    fp.close()



  def loadMeasurementVolumesEndOf2013(self,measurements,sampleIndex=0):
    """Load the volumes corresponding to the given measurement.
    If there is more than one sample, load the sampleIndex'th data.
    """
    import DICOMScalarVolumePlugin
    import DICOMLib

    results = {}
    m = measurements

    # load the original MR scans
    loader = DICOMScalarVolumePlugin.DICOMScalarVolumePluginClass()
    loadable = DICOMLib.DICOMLoadable()
    loadable.name = m.label
    loadable.files = m.rawFiles[sampleIndex]
    results['MR'] = loader.load(loadable)
    results['MR',"files"] = m.rawFiles[sampleIndex]

    # load the CRO-provided overall label map
    results['classmap'] = slicer.util.loadVolume(m.classmapFiles[sampleIndex][0], returnNode=True)[1]
    results['classmap'].SetName(m.label + "-classmap")
    results['classmap',"files"] = m.classmapFiles[sampleIndex]

    # load the semi-automated per-muscle segmentations
    volumesLogic = slicer.modules.volumes.logic()
    labelFile = m.labelFiles[sampleIndex]
    results['muscleLabel'] = volumesLogic.AddArchetypeVolume(
                                  labelFile, m.label+"-label", 1)
    results['muscleLabel',"files"] = labelFile

    for result in ("MR", "classmap", "muscleLabel"):
      if not results[result]:
        print('Could not load %s' % result)
        print(results[result,"files"])
        return


    # use the same physical mapping for all volumes, since
    # they should all be in the same pixel space
    # but:
    # -- the CRO provided DICOM files have embedded NULL
    #    characters in PixelSpacing so they do not always load correctly
    # -- control points are expressed in muscleIJKToRAS coordinates,
    #    but we want to export them with respect to mrIJKToRAS, so
    #    we keep muscleToMR as a 4x4 matrix to map the control points.
    mrIJKToRAS = vtk.vtkMatrix4x4()
    muscleIJKToRAS = vtk.vtkMatrix4x4()
    results['MR'].GetIJKToRASMatrix(mrIJKToRAS)
    results['muscleLabel'].GetIJKToRASMatrix(muscleIJKToRAS)
    results['classmap'].SetIJKToRASMatrix(mrIJKToRAS)
    results['muscleLabel'].SetIJKToRASMatrix(mrIJKToRAS)

    # in the file we have Pmuscle == points in muscle space
    # we want Mmusle2mr == matrix from muscle to mr space
    # thus:
    #  Pmr = Mmuscle2mr * Pmuscle
    mMuscleToMR = vtk.vtkMatrix4x4()
    # so we first map from Pmuscle to IJK, then IJK to MR
    # or:
    #  Pmr = MmrIJKToRAS * MmuscleIJKToRAS-1 * Pmuscle
    muscleIJKToRAS.Invert()
    vtk.vtkMatrix4x4.Multiply4x4(mrIJKToRAS, muscleIJKToRAS, mMuscleToMR)
    results['mMuscleToMR'] = mMuscleToMR

    # select volumes to display
    appLogic = slicer.app.applicationLogic()
    selNode = appLogic.GetSelectionNode()
    selNode.SetReferenceActiveVolumeID(results['MR'].GetID())
    selNode.SetReferenceSecondaryVolumeID(results['classmap'].GetID())
    selNode.SetReferenceActiveLabelVolumeID(results['muscleLabel'].GetID())
    appLogic.PropagateVolumeSelection()

    # set up the composite nodes and slice nodes
    compositeNodes = slicer.util.getNodes('vtkMRMLSliceCompositeNode*')
    for compositeNode in compositeNodes.values():
      compositeNode.SetForegroundOpacity(0.5)
    sliceNodes = slicer.util.getNodes('vtkMRMLSliceNode*')
    for sliceNode in sliceNodes.values():
      sliceNode.SetUseLabelOutline(True)

    layoutManager = slicer.app.layoutManager()
    layoutManager.layout = 3 # the four-up view

    # let the layout take effect and re-render new data
    slicer.app.processEvents()

    layoutManager.resetSliceViews()
    threeDView = layoutManager.threeDWidget(0).threeDView()
    threeDView.lookFromAxis(ctk.ctkAxesWidget.Anterior)
    threeDView.resetFocalPoint()

    renderer = threeDView.renderWindow().GetRenderers().GetItemAsObject(0)
    camera = renderer.GetActiveCamera()
    camera.SetPosition (-125, 1307.15, 211)
    camera.SetFocalPoint (-125, 21, 211)
    camera.SetClippingRange (934.232, 1849.54)
    camera.SetDistance (1286.15)

    # let the layout take effect and re-render new data
    slicer.app.processEvents()

    return results



  def makeModel(self,labelNode,modelName,modelIndex,hierarchyName="Models"):
    """create a model using the command line module
    based on the current editor parameters
    - make a new hierarchy node
    """

    self.delayDisplay("Starting model making",200)
    parameters = {}
    parameters["InputVolume"] = labelNode.GetID()
    # create models for all labels
    parameters["Name"] = modelName
    parameters["Labels"] = modelIndex
    parameters["GenerateAll"] = False
    outHierarchy = slicer.vtkMRMLModelHierarchyNode()
    outHierarchy.SetScene( slicer.mrmlScene )
    outHierarchy.SetName( hierarchyName )
    slicer.mrmlScene.AddNode( outHierarchy )
    parameters["ModelSceneFile"] = outHierarchy

    modelMaker = slicer.modules.modelmaker
    self.CLINode = None
    self.CLINode = slicer.cli.run(modelMaker, self.CLINode, parameters, delete_temporary_files=False)
    waitCount = 0
    while self.CLINode.GetStatusString() != 'Completed' and waitCount < 100:
      self.delayDisplay("Model making in progress (%d)" % waitCount)
      waitCount += 1
    self.delayDisplay("Done",200)

  def calculateFatRatio(self,measurements,currentData):
    """Determine the fat ratio over the segmented muscle volume.
    Estimate this by calculating the per-slice muscle and fat
    volumes only on slices for which the both segmentations exist.
    On those slices, mask the fat volume to so that the only non-zero
    values are in places where the muscle is defined.
    Sum up the fat and muscle volumes from the slices to determine the
    overall ratio estimate, which can be multiplied by the overall
    muscle volume to estimage the overall fat content.
    """

    if not currentData['classmap']:
      print("skipping measurement - no classmap")

    print("\nmeasurements:")
    print(measurements)
    print()
    print(str(currentData))
    classmap = slicer.util.array(currentData['classmap'].GetID())
    musclesArray = slicer.util.array(currentData['muscleLabel'].GetID())
    print(classmap.max())
    print(classmap.shape)
    print(musclesArray.max())
    print(musclesArray.shape)
    slices = musclesArray.shape[0]

    imatArray = numpy.array(classmap)

    if len(imatArray.shape) > 3 and imatArray.shape[3] > 1:
      # color image, so IMAT is non-zero green component
      imatArray = imatArray.transpose()[1].transpose()
      imatArray[imatArray != 0] = 1
      print("imat modified")
      print(imatArray.max())
    else:
      # make a new array as a boolean mask for IMAT
      imatLabel = 5
      imatArray[imatArray != imatLabel] = 0
      imatArray[imatArray == imatLabel] = 1
      print(imatArray.max())

    # make a new array as a boolean mask for the given muscle
    muscleLabel = self.indexByMuscle[measurements.muscle]
    muscleArray = numpy.array(musclesArray)
    muscleArray[muscleArray != muscleLabel] = 0
    muscleArray[muscleArray == muscleLabel] = 1
    print(muscleArray.max())

    fatmapLabel = None
    if measurements.property == "fatRatio":
      volumesLogic = slicer.modules.volumes.logic()
      fatmapLabel = volumesLogic.CloneVolume(currentData['muscleLabel'], 'fatmap-label')
      # make a per-muscle fat map in the label
      fatArray = slicer.util.array(fatmapLabel.GetID())
      fatArray[:] = imatArray * muscleArray
      fatmapLabel.GetImageData().Modified()

    # make models for display
    self.makeModel( currentData['muscleLabel'],
          measurements.muscle, self.indexByMuscle[measurements.muscle])
    if fatmapLabel:
      self.makeModel( fatmapLabel, measurements.muscle + "-IMAT", 1)

    # display the models
    muscleModelNode = slicer.util.getNode(measurements.muscle)
    colorNode = slicer.util.getNode('vtkMRMLColorTableNodeLabels')
    lookupTable = colorNode.GetLookupTable()
    rgb = [0,]*3
    lookupTable.GetColor(self.indexByMuscle[measurements.muscle],rgb)
    displayNode = muscleModelNode.GetDisplayNode()
    displayNode.SetColor(rgb)

    # if the measurement is a fat ratio calculation,
    # then make a lable map to store the per-muscle IMAT
    # and make the model have front face culling (to see inside)
    if measurements.property == "fatRatio":
      # show the muscle inside out
      displayNode.SetFrontfaceCulling(True)
      displayNode.SetBackfaceCulling(False)
      # show the fatmap in white
      fatModelNode = slicer.util.getNode(measurements.muscle + "-IMAT")
      displayNode = fatModelNode.GetDisplayNode()
      displayNode.SetColor(1,1,1)

    # look at the models
    layoutManager = slicer.app.layoutManager()
    layoutManager.resetThreeDViews()

    # calculate the per-slice fat content
    muscleCount = 0
    muscleIMATCount = 0
    for slice in xrange(slices):
      imatSlice = imatArray[slice]
      muscleSlice = muscleArray[slice]
      if imatSlice.max() > 0 and muscleSlice.max() > 0:
        # this is a slice where the muscle is present and the overall
        # labelmap is not missing data
        muscleIMATSlice = imatSlice * muscleSlice
        muscleCount += muscleSlice.sum()
        muscleIMATCount += muscleIMATSlice.sum()
        print("Muscle, imat = (%d, %d)" % (muscleSlice.sum(), muscleIMATSlice.sum()))
      else:
        print("Skipping slice %d" % slice)
    fatRatio = muscleIMATCount / float(muscleCount)

    # calculate the muscle volume if needed
    if len(measurements.samples) == 1 and math.isnan(measurements.samples[0]):
      print('have a nan sample for property %s' % measurements.property )
      if measurements.property == "muscleVolumeCC":
        # if muscle volume not yet calculated, provide it now
        pixelVolumeMM = numpy.array(currentData['muscleLabel'].GetSpacing()).prod()
        pixelVolumeCC = pixelVolumeMM / 10. / 10. / 10.
        nonZeroPixels = muscleArray.sum()
        measurements.samples[0] = nonZeroPixels * pixelVolumeCC
        print ('Volume for %s is %g' % (measurements.label, measurements.samples[0]))


    # make a 'measurements' instance to hold the result
    import copy
    fm = copy.deepcopy(measurements)
    fm.property = "fatRatio"
    fm.label = '%s-%s-%s-%s' % (fm.subject, fm.muscle, fm.property[0], self.timePointCodeMap[fm.timepoint])
    fm.samples = [fatRatio]
    return fm

  def csv(self,measurementsList,filePath):
    fp = open(filePath,"w")
    fp.write("Subject,Property,Muscle,Timepoint,SampleValue,SampleOrder\n")
    for m in measurementsList:
      sampleOrder = 1
      for sample in m.samples:
        values = (m.subject, m.property, m.muscle, m.timepoint, sample, sampleOrder)
        fp.write("\"%s\",\"%s\",\"%s\",\"%s\",%g,%d\n" % values)
        sampleOrder += 1
    fp.close()

class MurineTrialTest(unittest.TestCase):
  """
  This is the test case for your scripted module.
  """

  def delayDisplay(self,message,msec=1000):
    """This utility method displays a small dialog and waits.
    This does two things: 1) it lets the event loop catch up
    to the state of the test so that rendering and widget updates
    have all taken place before the test continues and 2) it
    shows the user/developer/tester the state of the test
    so that we'll know when it breaks.
    """
    print(message)
    self.info = qt.QDialog()
    self.infoLayout = qt.QVBoxLayout()
    self.info.setLayout(self.infoLayout)
    self.label = qt.QLabel(message,self.info)
    self.infoLayout.addWidget(self.label)
    qt.QTimer.singleShot(msec, self.info.close)
    self.info.exec_()

  def setup(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setup()

    self.test_MurineTrial1()

  def test_MurineTrial1(self,galleryDir='/tmp/muscle-gallery'):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests sould exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    import time
    self.delayDisplay("Starting the test")
    if not os.path.exists(galleryDir):
      os.mkdir(galleryDir)
    #
    # load each dataset and print the time taken
    #
    logic = MurineTrialLogic()
    measurementsList = logic.measurementsList
    index = 0
    count = len(measurementsList)
    failedMeasurementsList = []
    fatRatioMeasurementsList = []
    for measurements in measurementsList:
      self.delayDisplay("Loading %s" % measurements.label, 100)
      start = time.time()
      slicer.mrmlScene.Clear(0)
      try:
        currentData = logic.loadMeasurementVolumes(measurements)
        fatRatioMeasurement = logic.calculateFatRatio(measurements, currentData)
        fatRatioMeasurementsList.append(fatRatioMeasurement)
      except Exception, e:
        import traceback
        traceback.print_exc()
        qt.QMessageBox.warning(slicer.util.mainWindow(),
            "Reload and Test", 'Exception!\n\n' + str(e) + "\n\nSee Python Console for Stack Trace")
        failedMeasurementsList.append(measurements)
        print ("Could not load: %s" % measurements.label)
      index += 1
      self.delayDisplay("\n\nLoaded %d of %d: %s\n\n" \
          % (index, count, measurements.label), 100)
      self.delayDisplay("Time: %f" % (time.time() - start), 300)
      start = time.time()

      pixmap = qt.QPixmap.grabWidget(slicer.util.mainWindow())
      pixFile = galleryDir + "/%s.png" % measurements.label
      pixmap.save(pixFile)
      print("Saved to %s" % pixFile)

    # save the csv file of results
    allMeasurements = measurementsList + fatRatioMeasurementsList
    logic.csv(allMeasurements,galleryDir + "/muscles.csv")

    self.delayDisplay('Test passed!')
    os.system('open %s' % galleryDir)
    if len(failedMeasurementsList) > 0:
      print("Some measurements failed!\n")
      print([m.label for m in failedMeasurementsList])
    else:
      print("No failed measurements - nice!")


