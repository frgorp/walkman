'''
A multithreaded processor for mp3 downloading and 
tagging
'''
import os
import urllib2
import eyeD3
from threading import Semaphore

class SongProcessor(object):
	def __init__(self, spoolPath, poolSize = 2):
		assert os.path.isdir(spoolPath) and os.access(spoolPath, os.W_OK)
		self.spool = spoolPath
		self.minions = [Minions(self.spool) for i in xrange(poolSize if poolSize > 0 else 1)]
		self.semaphore = Semaphore(poolSize if poolSize > 0 else 1)

	def downloadSong(self, title, artist, binaryUrl, posterUrl):
		self.semaphore.acquire()
		worker = self.minions.pop()
		result = worker.getSong(WorkParcel(title, artist, binaryUrl, posterUrl))
		self.minions.append(worker)
		self.semaphore.release()
		return result

class Minions(object):
	def __init__(self, spool):
		self.spool = spool

	def getSong(self, work):
		try:
			songName = "%s - %s.mp3" % (work.artist, work.title)
			fileName = "%s/%s" % (self.spool, songName)
			artName  = "%s.jpg" % fileName
			target = urllib2.urlopen(work.downloadUrl)
			mp3 = open(fileName, 'w')
			mp3.write(target.read())
			mp3.close()
			targetArt = urllib2.urlopen(work.posterUrl)
			art = open(artName, 'w')
			art.write(targetArt.read())
			art.close()
			tag = eyeD3.Tag()
			tag.link(fileName)
			tag.setVersion(eyeD3.ID3_V2_3)
			tag.setArtist(work.artist)
			tag.setTitle(work.title)
			tag.addImage(0x08, artName)
			tag.update()
			os.remove(artName)
			return {"file": songName}
		except Exception as e:
			return {"reason": repr(e)}
			
		
class WorkParcel(object):
	def __init__(self, title, artist, downloadUrl, posterUrl):
		self.title = title
		self.artist = artist
		self.downloadUrl = downloadUrl
		self.posterUrl = posterUrl
