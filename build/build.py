#!/usr/bin/env python

import os, md5, subprocess, pickle, sys

hashes = {}
verbose = False

hashFile = ".hashes"

def loadHashes():
	global hashes
	if os.path.isfile(hashFile):
		db = open(hashFile, "rb")
		hashes = pickle.load(db)
		db.close()



def checkpointHashes():
	db = open(hashFile, "wb")
	pickle.dump(hashes, db)
	db.close()


def ensureDirectory(dir):
	if os.path.isdir(dir):
		return
	executeCommand("MKDIR", dir, "mkdir -p " + dir)
	

def prepareDirectories():
	ensureDirectory("generated/bindings")
	ensureDirectory("tmp/bindings")
	ensureDirectory("tmp/generator")
	ensureDirectory("tmp/native")
	ensureDirectory("tmp/objects")
	ensureDirectory("tmp/include")
	ensureDirectory("tmp/tests")


def findFiles(baseDir, ext):
	result = []
	for (root, dirs, files) in os.walk(baseDir):
		for file in files:
			if file.endswith(ext):
				result.append(os.path.join(root, file))
	return result


#
# Scan a list of files and decide if they need [re]-building.
#
# Two things to check:
# 1) target older?
# 2) if so, has source changed?
#
# Otherwise, (no target), just

# *) has source changed?
#
# We compare source files' md5sums against the values we have stored in our
# hash dictionary. The dictionary is immediately updated but this only has any
# persistant effect if a checkpoint happens after a command is run
# successfully. FIXME verify!
#
# Takes a list of touples mapping candidate source files to target filenames
#

def sourceChanged(file, hash):
	if hashes.has_key(file):
		if hashes[file] == hash:
			return False
	return True


def updateHash(file, hash):
	hashes[file] = hash

def debug(args):
	if False:
		print args

def filesNeedBuilding(list):
	changed = []

	for (source, target) in list:
		if not os.path.isfile(source):
			print source + " missing, abort"
			sys.exit()

		f = open(source)
		m = md5.new(f.read())
		f.close()
		hash = m.hexdigest()

		debug("CHECK\t"+str(target)+" from "+source)

		if target:
			debug("TARGET",)
			if not os.path.isfile(target):
				debug("MISSING",)
			elif os.path.getmtime(target) < os.path.getmtime(source):
				debug("OLDER,")
				if not sourceChanged(source, hash):
					debug("SOURCE UNCHANGED")
					continue
			else:
				debug("NEWER, SKIP")
				continue
		else:
			if not sourceChanged(source, hash):
				debug("SOURCE UNCHANGED")
				continue

		debug("BUILD")
		updateHash(source, hash)
		changed.append(source)

	return changed

#
# common use case that source files transform predictably 1:1 into target
# files. Return a list of (source, target) touples
#

def dependsMapSourceFilesToTargetFiles(sourceDir, sourceExt, targetDir, targetExt):
	list = findFiles(sourceDir, sourceExt)
	result = []

	for source in list:
		target = source.replace(sourceDir, targetDir)
		target = target.replace(sourceExt, targetExt)

		pair = (source, target)
		result.append(pair)
	
	return result

#
# single target depnds on many files
#

def dependsListToSingleTarget(list, target):
	result = []

	for source in list:
		pair = (source, target)
		result.append(pair)

	return result

#
# no target, just check origin files for changes; any change will be used to
# trigger action
#

def dependsChangedSourcesOnly(list):
	result = []

	for source in list:
		pair = (source, None)
		result.append(pair)
	
	return result



def executeCommand(short, what, cmd):
	executeCommandInDir(short, what, None, cmd)

def executeCommandInDir(short, what, inDir, cmd):
	if verbose:
		print cmd
	else:
		print short + "\t" + what
	
	status = subprocess.call(cmd, shell=True, cwd=inDir)
	if status != 0:
		sys.exit()

	checkpointHashes()

	


def compileJavaCode(outputDir, classpath, sourcepath, sources):
	cmd = "/opt/sun-jdk-1.5.0.08/bin/javac -source 1.4 -target 1.4"
	cmd += " -d " + outputDir
	if classpath:
		   cmd += " -classpath " + classpath
	if sourcepath:
		cmd += " -sourcepath " + sourcepath
	cmd += " " + " ".join(sources)

	blurb = ""
	for path in sourcepath.split(":"):
		if blurb:
			blurb += ", "
		blurb += path + "*.java"

	executeCommand("JAVAC", blurb, cmd)

def runJavaClass(classname, classpath):
	cmd = "/opt/sun-jdk-1.5.0.08/bin/java"
	cmd += " -classpath " + classpath
	cmd += " -ea " + classname
	if not verbose:
		cmd += " >/dev/null"

	executeCommand("JAVA", classname, cmd)


def compileGeneratorClasses():
	pairs = dependsMapSourceFilesToTargetFiles("src/generator/", ".java", "tmp/generator/", ".class")
	changed = filesNeedBuilding(pairs)
	if not changed:
		return
	compileJavaCode("tmp/generator/", "", "src/generator/", changed)


def generateTranslationAndJniLayers():
	list = findFiles("tmp/generator", ".class")
	list += findFiles("src/defs", ".defs")
	pairs = dependsChangedSourcesOnly(list)

	changed = filesNeedBuilding(pairs)
	if not changed:
		return

	runJavaClass("BindingsGenerator", "tmp/generator/")


def compileBindingsClasses():
	pairs = dependsMapSourceFilesToTargetFiles("src/bindings/", ".java", "tmp/bindings/", ".class")
	pairs += dependsMapSourceFilesToTargetFiles("generated/bindings/", ".java", "tmp/bindings/", ".class")

	changed = filesNeedBuilding(pairs)
	if not changed:
		return

	compileJavaCode("tmp/bindings/", "tmp/bindings/", "src/bindings/:generated/bindings/", changed)


#
# This seems like a lot of effort to copy a file
#

def copyMappingFile():
	source = "mockup/bindings/typeMapping.properties"
	target = "tmp/bindings/typeMapping.properties"
	pairs = [(source, target)]

	changed = filesNeedBuilding(pairs)
	if not changed:
		return

	cmd = "cp " + source + " " + target
	executeCommand("CP", target, cmd)


def makeJarFile():
	jar = "tmp/gtk-4.0.jar"

	list = findFiles("tmp/bindings/", ".class")
	list += findFiles("tmp/bindings/", ".properties")
	pairs = dependsListToSingleTarget(list, jar)

	changed = filesNeedBuilding(pairs)
	if not changed:
		return

	files = [] 
	for file in list:
		files.append(file.replace("tmp/bindings/", ""))

	cmd = "/opt/sun-jdk-1.5.0.08/bin/jar cf "
	cmd += "../../" + jar + " "
	cmd += " ".join(files)

	executeCommandInDir("JAR", jar, "tmp/bindings/", cmd)

#
# main build sequence, with elaborately named methods Carl Rosenberger style
#

def generateBindings():
	prepareDirectories()

	compileGeneratorClasses()
	generateTranslationAndJniLayers()

	compileBindingsClasses()
	copyMappingFile()

	makeJarFile()




#
# prelininary setup
#
if __name__ == '__main__':
	if os.getenv("V"):
		verbose = True

	loadHashes()

	generateBindings()

