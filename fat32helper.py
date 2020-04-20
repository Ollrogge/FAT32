import struct
import sys

def getBytes(fs, pos, numBytes):
	fs.seek(pos)
	_bytes = fs.read(numBytes)
	if numBytes == 0x1:
		formatString = "<B"
	elif numBytes == 0x2:
		formatString = "<H"
	elif numBytes == 0x4:
		formatString = "<I"
	else:
		raise Exception("Not implemented")

	return struct.unpack(formatString, _bytes)[0]

def getString(fs, pos, numBytes):
	fs.seek(pos)
	_bytes = fs.read(numBytes)
	return struct.unpack(str(numBytes)+"s", _bytes)[0].decode()

def bytesPerSector(fs):
	return getBytes(fs, 0xb, 0x2)

def sectorsPerCluster(fs):
	return getBytes(fs, 0xd, 0x1)

def numberOfReservedSectors(fs):
	return getBytes(fs, 0xe, 0x2)

def numberOfFATs(fs):
	return getBytes(fs, 0x10, 0x1)

def sectorsPerFAT(fs):
	return getBytes(fs, 0x24, 0x4)

def rootDirectoryFirstClusterNum(fs):
	return getBytes(fs, 0x2c, 0x4)

def signature(fs):
	return getBytes(fs, 0x1fe, 0x2)

def FATStart(fs):
	return numberOfReservedSectors(fs) * bytesPerSector(fs)

def FATSize(fs):
	return sectorsPerFAT(fs) * bytesPerSector(fs)

def nextClusterNum(fs, num):
	sectorNum = num >> 0x6
	sectorOffset = num & 0x7f
	offset = FATStart(fs) + sectorNum * bytesPerSector(fs) + sectorOffset
	return getBytes(fs, offset, 0x4)

def clusterSize(fs):
	return sectorsPerCluster(fs) * bytesPerSector(fs)

def clusterBegin(fs, num):
	return FATStart(fs) + numberOfFATs(fs) * FATSize(fs) + (num - 2) * clusterSize(fs)

def ppNum(num):
	return "%s (%s)" % (hex(num), num)

def mainInfo(fs):
	print("Bytes per sector:", ppNum(bytesPerSector(fs)))
	print("Sectors per cluster:", ppNum(sectorsPerCluster(fs)))
	print("Reserved sector count:", ppNum(reservedSectorCount(fs)))
	print("Number of FATs:", ppNum(numberOfFATs(fs)))
	print("Fat size:", ppNum(FATSize(fs)))
	print("Start of FAT1:", ppNum(FATStart(fs, 1)))
	print("Start of root directory:", ppNum(rootStart(fs)))
	print("Root dir cluster: ", ppNum(root_dir_cluster(fs)))
	print("Signature:", signature(fs))

def name(fs, offset):
	return getString(fs, offset, 0x8).split()[0]

def isDir(fs, offset):
	return getBytes(fs, offset + 0xb, 0x1) != 0x0

def firstClusterNum(fs, offset):
	return getBytes(fs, offset + 0x1a, 0x2) | (getBytes(fs, offset + 0x14, 0x2) << 0x10)

def fileSize(fs, offset):
	return getBytes(fs, offset + 0x1c, 0x4)

def getDirectory(fs, offset):
	while getBytes(fs, offset, 0x1) != 0x0:
		fileInfo = {}
		fileInfo['name'] = name(fs, offset)
		fileInfo['isDir'] = isDir(fs, offset)
		fileInfo['firstClusterNum'] = firstClusterNum(fs, offset)
		fileInfo['fileSize'] = fileSize(fs, offset)

		offset += 32
		fs.seek(offset)

		yield fileInfo

def getSubDir(fs, fileInfo):
	if fileInfo['firstClusterNum'] == 0 or not fileInfo['isDir']:
		raise Exception("Unable to get subDir")

	return getDirectory(fs, clusterBegin(fs, fileInfo['firstClusterNum']))

def dfs(fs, begin, path, visited):
	if begin in visited:
		return

	visited[begin] = True
	print(path)

	for fileInfo in getDirectory(fs, begin):
		if fileInfo['firstClusterNum'] and fileInfo['isDir']:
			dfs(fs, clusterBegin(fs, fileInfo['firstClusterNum']), path + fileInfo['name'], visited)



#fs = open(sys.argv[1],"rb")
#start = clusterBegin(fs, rootDirectoryFirstClusterNum(fs))
#
#visited = {}
#dfs(fs, start, "", visited)