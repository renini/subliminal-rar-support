#!/usr/bin/python
'''
    This python script downloads subtitles for packed (.rar) releases using the subliminal module.
    I like to keep my downloads stored in this 'packed' splitted rar form (.rar, .r00, .r01, r02, etc.).

    The script uses rarfile to get the movie/tvshow filename inside the .rar archives.
    Since we need to calculate filehashes for opensubtitles and subdb this only works on 'store' rars
    these are so called 0x30 (m0) compressed archives.
    Code is ugly, but so far this seems to work for me just fine. 
    Hopefully i will find some time to clean the 'code' and release this as a patch for subliminal. Hellup!?

    Enjoy!

    http://github.com/renini/
'''
import os
import io
import struct
import rarfile
import glob
import hashlib
import re
from os.path import expanduser
from subprocess import call
from babelfish import Language
from datetime import timedelta
import enzyme
import logging
import guessit
import subliminal
from subliminal import Movie, Episode, Video

logging.basicConfig(filename='/tmp/subliminal-rar-support.log',level=logging.DEBUG)

# 
# MOVIES = [Movie('man.of.steel.2013.720p.bluray.x264-felony.mkv', 'Man of Steel',
#                 format='BluRay', release_group='felony', resolution='720p', video_codec='h264', audio_codec='DTS',
#                 imdb_id=770828, size=7033732714, year=2013,
#                 hashes={'opensubtitles': '5b8f8f4e41ccb21e', 'thesubdb': 'ad32876133355929d814457537e12dc2'})]
#

# configuration

cachedir = expanduser('~/.subtitles/')                                    # path used for subliminal cache
allowedextensions = ('.avi', '.mp4', '.mov', '.mkv')                      # only process these fileextensions
subproviders = ['addic7ed', 'opensubtitles', 'podnapisi', 'thesubdb']     # subtitle providers to use
languages = {Language('eng'), Language('nld')}                            # languages to search for
videodir = '/storage/downloads/movies'


# functions

def hashOpenSub(name,filesize):
    try:
        longlongformat = 'q'  # long long
        bytesize = struct.calcsize(longlongformat)

        f = name

        #filesize = 11733992852
        hash = filesize

        if filesize < 65536 * 2:
            return "SizeError"

        for x in range(65536/bytesize):
            buffer = f.read(bytesize)
            (l_value,)= struct.unpack(longlongformat, buffer)
            hash += l_value
            hash = hash & 0xFFFFFFFFFFFFFFFF #to remain as 64bit number


        f.seek(max(0,filesize-65536),0)
        for x in range(65536/bytesize):
            buffer = f.read(bytesize)
            (l_value,)= struct.unpack(longlongformat, buffer)
            hash += l_value
            hash = hash & 0xFFFFFFFFFFFFFFFF

        f.close()
        returnedhash =  "%016x" % hash
        return returnedhash

    except Exception as e:
        print e

def hashSubDB(name,filesize):
    try:
        f = name

        hash = f.read(65536)

        f.seek(max(0,filesize-65536),0)
        hash += f.read(65536)

        f.close()
        returnedhash =  hashlib.md5(hash).hexdigest()
        return returnedhash

    except Exception as e:
        print e

# create subtitles cache directory
if not os.path.isdir(cachedir):
    os.makedirs(cachedir)
subliminal.cache_region.configure('dogpile.cache.dbm', arguments={'filename': cachedir + 'cachefile.dbm'})

# check each subdir of videodir
# the expected directory structure is:
# /storage/downloads/movies/Some.Movie.1080p.x264-PYTHON/some.movie.2015.1080p.x264.rar
for dirs in os.walk(videodir).next()[1]:
    #print 'Processing: ' + videodir + '/' + dirs + '/*.rar'
    print 'Processing: ' + videodir + '/' + dirs

    if glob.glob(videodir  + '/' + dirs + '/*.srt'):
        print videodir + '/' + dirs + ' already has a subtitle'
        continue

    # process rarfiles in each videodir
    # NOTE: this will match for all .rar files, so in the case of .rar .r01 .r02, this is oke, 
    # but with part01.rar, part02.rar cases it will try to check them all.
    files = glob.glob(videodir + '/' + dirs + '/*.rar')
    if not files:
        print videodir + '/' + dirs + ' has no rarfiles'
        continue

    for file in files:
        print 'Checking content of rar: ' + file

        try:
            rf = rarfile.RarFile(file)
            for f in rf.infolist():
                #print 'Found the following file: ' + f.filename

                if f.compress_type == 48 and f.filename.endswith(allowedextensions):
                    video = Video.fromguess(dirs  + '/' + f.filename, guessit.guess_file_info(dirs  + '/' + f.filename))
                    print 'Uncompressed store algorithme used (0x30)'
                    print 'Searching subtitles for Filename: ' + f.filename
                    print 'Filesize: ' + str(f.file_size)
                    video.size = f.file_size

                    print video
                    attrs = vars(video)
                    print ', '.join("%s: %s" % item for item in attrs.items())


                    # enzyme
                    try:
                        #global video # nodig voor variable?

                        if f.filename.endswith('.mkv'):
                            with rf.open(f.filename) as openfile:
                                mkv = enzyme.MKV(openfile)

                            if mkv.video_tracks:
                                video_track = mkv.video_tracks[0]

                                if video_track.codec_id == 'V_MPEG4/ISO/AVC':
                                    video.video_codec = 'h268'
                                elif video_track.codec_id == 'V_MPEG4/ISO/SP':
                                    video.video_codec = 'DivX'
                                elif video_track.codec_id == 'V_MPEG4/ISO/ASP':
                                    video.video_codec = 'XviD'

                                print 'Video codec: ' + video.video_codec
                            else:
                                print 'MKV has no video track'

                            if mkv.audio_tracks:
                                audio_track = mkv.audio_tracks[0]

                                if audio_track.codec_id == 'A_AC3':
                                    video.audio_codec = 'AC3'
                                elif audio_track.codec_id == 'A_DTS':
                                    video.audio_codec = 'DTS'
                                elif audio_track.codec_id == 'A_AAC':
                                    video.audio_codec = 'AAC'

                                print 'Audio codec: ' + video.audio_codec
                            else:
                                print 'MKV has no audio track'


                        print video
                        attrs = vars(video)
                        print ', '.join("%s: %s" % item for item in attrs.items())


                    except enzyme.Error:
                        print 'Parsing video metadata with enzyme failed'

                    with rf.open(f.filename) as openfile:
                        #print 'OpenSubtitles hash: ' + hashOpenSub(openfile, f.file_size)
                        #print 'SubDB hash: ' + hashSubDB(openfile, f.file_size)
                        video.hashes['opensubtitles'] = hashOpenSub(openfile, f.file_size)
                        video.hashes['thesubdb'] = hashSubDB(openfile, f.file_size)

                    try:
                        print video
                        attrs = vars(video)
                        print ', '.join("%s: %s" % item for item in attrs.items())

                        # download best subtitles
                        subtitles = subliminal.download_best_subtitles([video], languages, providers=subproviders)

                        # save them to disk, next to the video
                        # save_subtitles(subtitles, single=False, directory=None, encoding=None)
                        subliminal.save_subtitles(subtitles, False, videodir + '/' + dirs + '/' )
                    except Exception as e:
                        print e
                        print "Unable to download subtitle"

        # do not throw an exception if the .rar file is not the first volume
        except:
            pass
