#!/usr/bin/env python
import httplib
import StringIO
import hashlib
import uuid
import random
import string
import sys
import os
import subprocess
import gzip
import urllib2,urllib
if sys.version_info[1] >= 6:  import json
else: import simplejson as json

_useragent = "Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1"
_referer = "http://grooveshark.com/JSQueue.swf?20110725.01"
_token = None

h = {}
h["country"] = {}
h["country"]["CC1"] = "0"
h["country"]["CC2"] = "0"
h["country"]["CC3"] = "0"
h["country"]["CC4"] = "0"
h["country"]["ID"] = "1"
h["privacy"] = 0
h["session"] = None
h["uuid"] = str.upper(str(uuid.uuid4()))

entrystring = \
"""A Grooveshark song downloader in python
by George Stephanos <gaf.stephanos@gmail.com>
"""

def prepToken(method, secret):
    rnd = (''.join(random.choice(string.hexdigits) for x in range(6))).lower()
    return rnd + hashlib.sha1(method + ":" + _token + secret + rnd).hexdigest()

def getToken():
    global h, _token
    p = {}
    p["parameters"] = {}
    p["parameters"]["secretKey"] = hashlib.md5(h["session"]).hexdigest()
    p["method"] = "getCommunicationToken"
    p["header"] = h
    p["header"]["client"] = "htmlshark"
    p["header"]["clientRevision"] = "20110606"
    conn = httplib.HTTPConnection("grooveshark.com")
    conn.request("POST", "/more.php", json.JSONEncoder().encode(p), {"User-Agent": _useragent, "Referer": _referer, "Content-Type":"", "Accept-Encoding":"gzip", "Cookie":"PHPSESSID=" + h["session"]})
    _token = json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())["result"]

def getSearchResultsEx(query, what="Songs"):
    p = {}
    p["parameters"] = {}
    p["parameters"]["type"] = what
    p["parameters"]["query"] = query
    p["header"] = h
    p["header"]["client"] = "htmlshark"
    p["header"]["clientRevision"] = "20110606"
    p["header"]["token"] = prepToken("getSearchResultsEx", ":backToTheScienceLab:")
    p["method"] = "getSearchResultsEx"
    conn = httplib.HTTPConnection("grooveshark.com")
    conn.request("POST", "/more.php?" + p["method"], json.JSONEncoder().encode(p), 
								 {"User-Agent": _useragent, 
								  "Referer":"http://grooveshark.com/", 
								  "Content-Type":"application/json", 
								  "Accept-Encoding":"gzip", 
								  "Cookie":"PHPSESSID=" + h["session"]})
    j = json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())
    try:
        return j["result"]["result"]["Songs"]
    except:
        return j["result"]["result"]

def artistGetSongsEx(id, isVerified):
    p = {}
    p["parameters"] = {}
    p["parameters"]["artistID"] = id
    p["parameters"]["isVerifiedOrPopular"] = isVerified
    p["header"] = h
    p["header"]["client"] = "htmlshark"
    p["header"]["clientRevision"] = "20110606"
    p["header"]["token"] = prepToken("artistGetSongsEx", ":backToTheScienceLab:")
    p["method"] = "artistGetSongsEx"
    conn = httplib.HTTPConnection("grooveshark.com")
    conn.request("POST", "/more.php?" + p["method"], json.JSONEncoder().encode(p), {"User-Agent": _useragent, "Referer": _referer, "Content-Type":"", "Accept-Encoding":"gzip", "Cookie":"PHPSESSID=" + h["session"]})
    return json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())

def getStreamKeyFromSongIDEx(id):
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
    conn.request("POST", "/more.php?" + p["method"], json.JSONEncoder().encode(p), {"User-Agent": _useragent, "Referer": _referer, "Accept-Encoding":"gzip", "Content-Type":"", "Cookie":"PHPSESSID=" + h["session"]})
    j = json.JSONDecoder().decode(gzip.GzipFile(fileobj=(StringIO.StringIO(conn.getresponse().read()))).read())
    return j

def header_cb(buf):
    global h
    if "PHPSESSID" in buf:
        buf = buf.split(' ')
        h["session"] = buf[1][10:-1]

def init():
    conn = httplib.HTTPConnection("grooveshark.com")
    conn.request("HEAD", "", headers={"User-Agent": _useragent})
    res = conn.getresponse()
    cookie = res.getheader("set-cookie").split(";")
    h["session"] = cookie[0][10:]

def query_artist_title(p_artistName, p_songName):
    
    """Function to Download one specific Song by the Name of p_songName
    by one specific Artist by the name of p_artistName"""
    
    init()
    getToken()
    for result in getSearchResultsEx(p_artistName):
        if result["SongName"].lower() == p_songName.lower():
            stream = getStreamKeyFromSongIDEx(result["SongID"])
            download(stream,result)
            break  
    
    """ If no match for SongName was found in the response to 
        the ArtistName query, query for the SongName instead and 
        fuzzy-match against ArtistName. To avoid a dependency the 
        fuzzy-match Levenshtein library is optional. If it can't be
        found the function will revert to a string comparsion. """
    
    try:
        import Levenshtein
        for result in getSearchResultsEx(p_songName):
            if Levenshtein.ratio(result["ArtistName"].lower().encode('cp437'),p_artistName.lower()) > 0.6:
                stream = getStreamKeyFromSongIDEx(result["SongID"])
                download(stream,result)
                break
    except ImportError:
        for result in getSearchResultsEx(p_songName):
            if result["ArtistName"].lower().encode('cp437')==p_artistName.lower():
                stream = getStreamKeyFromSongIDEx(result["SongID"])
                download(stream,result)
                break

def download(p_stream,p_songInfo):

    """ Function to download a song using a given ip and streamKey
        and save it to its correct location using the information 
        about the song in p_songInfo """
    
    for k,v in p_stream["result"].iteritems():    #Just a dirty hack, forget about this
        p_stream=v
    
    url = "http://"+p_stream['ip']+"/stream.php"
    req = urllib2.Request(url,'streamKey='+p_stream['streamKey'])
    req.add_header('Referer', _referer)
    req.add_header('User-Agent',_useragent)
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

if __name__ == "__main__":
    if len(sys.argv) < 2:
        import gui
        gui.main()
        exit()
    print entrystring
    init()
    getToken()
    m = 0
    s = getSearchResultsEx(sys.argv[1])
    for l in s:
        m += 1
        print str(m) + ': "' + l["SongName"] + '" by "' + l["ArtistName"] + '" (' + l["AlbumName"] + ')'
        if m == 10: break
    songid = raw_input("Enter the Song ID you wish to download or (q) to exit: ")
    if songid == "" or songid == "q": exit()
    songid = eval(songid)
    result=s[songid]
    stream = getStreamKeyFromSongIDEx(result["SongID"])
    download(stream,result)
