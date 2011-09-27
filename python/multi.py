from functions import *
class Downloader(threading.Thread): 
    queue = Queue.Queue() 
    def __init__(self):
        threading.Thread.__init__(self)
   	self._useragent = "Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1"
    	self._referer = "http://grooveshark.com/JSQueue.swf?20110725.01"
    	self._token = None
	
    def run(self): 
        while True: 
            task = Downloader.queue.get() 
            self.download(task) 
            Downloader.queue.task_done()
    def getStreamKeyFromSongIDEx(self,id):
        p = {}
        p["parameters"] = {}
        p["parameters"]["mobile"] = "false"
        p["parameters"]["prefetch"] = "false"
        p["parameters"]["songIDs"] = id
        p["parameters"]["country"] = h["country"]
        p["header"] = h
        p["header"]["client"] = "jsqueue"
        p["header"]["clientRevision"] = "20110606.04"
        p["header"]["token"] = prepToken("getStreamKeysFromSongIDs", ":bewareOfBearsharktopus:")
        p["method"] = "getStreamKeysFromSongIDs"
        conn = httplib.HTTPConnection("grooveshark.com")
        conn.request("POST", "/more.php?" + p["method"], json.JSONEncoder().encode(p), {"User-Agent": self._useragent, "Referer": self._referer, "Accept-Encoding":"gzip", "Content-Type":"", "Cookie":"PHPSESSID=" + h["session"]})
        j = json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())
        return j
 
    def download(self,p_songInfo):
	
	""" Function to download a song using a given ip and streamKey
        and save it to its correct location using the information 
        about the song in p_songInfo """
        p_stream = self.getStreamKeyFromSongIDEx(p_songInfo["SongID"])
        for k,v in p_stream["result"].iteritems():    #Just a dirty hack, forget about this
            p_stream=v
	httplib.debuglevel=1
        url = "http://"+p_stream['ip']+"/stream.php"
        req = urllib2.Request(url,'streamKey='+p_stream['streamKey'])
        req.add_header('Referer', self._referer)
        req.add_header('User-Agent',self._useragent)
        fd = urllib2.urlopen(req)
	mp3=""
        while 1:
	    data=fd.read(1024)
            if not len(data):
                break
            else:
                mp3+=data
        with open(p_songInfo["ArtistName"]+" - "+p_songInfo["SongName"]+'.mp3','w') as f:
            f.write(mp3)
meine_threads = [Downloader() for i in range(3)] 
for thread in meine_threads: 
    thread.setDaemon(True) 
    thread.start() 