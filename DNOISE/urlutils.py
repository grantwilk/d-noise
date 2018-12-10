"""
Copyright (C) 2018 Grant Wilk

This file is part of D-NOISE: AI-Acclerated Denoiser.

D-NOISE: AI-Acclerated Denoiser is free software: you can redistribute
it and/or modify it under the terms of the GNU General Public License
as published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

D-NOISE: AI-Acclerated Denoiser is distributed in the hope that it will
be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License along
with D-NOISE: AI-Acclerated Denoiser.  If not, see <https://www.gnu.org/licenses/>.
"""

from urllib import request
from urllib.request import urlopen
import os
import shutil
import threading
import zipfile
from . import fmutils

URL = "https://www.googleapis.com/drive/v3/files/1xTttPPtDWVeVQBZ5IvgphLMzfMqGwbiZ/?key=AIzaSyAeQC-x72dJTVWT6z_BqMescy4y26GG-aY&alt=media"
FILE_NAME = "DNOISE_OptiXBinaries.zip"

SCRIPT_DIR = os.path.dirname(__file__)
CHUNK_SIZE = 1024000 #bytes = 1MB
DOWNLOAD_PERCENT = 0

def downloadbin():
    global SCRIPT_DIR, CHUNK_SIZE, DOWNLOAD_PERCENT, FILE_NAME, URL
    global FILE_SIZE
    def download():
        os.chdir(SCRIPT_DIR)

        if os.path.isdir("OptiXDenoiser"):
            shutil.rmtree("OptiXDenoiser")

        chunkcount = 0
        filesize = int(request.urlopen(URL).info().get('Content-Length'))

        response = urlopen(URL)
        with open(FILE_NAME, 'wb') as f:
            while True:
                chunk = response.read(CHUNK_SIZE)
                if not chunk:
                    break
                f.write(chunk)
                chunkcount += 1
                updateprogress(chunkcount, filesize)

        with zipfile.ZipFile(FILE_NAME, 'r') as zip_ref:
            zip_ref.extractall("")

        os.remove(FILE_NAME)
        fmutils.forceUIUpdate("USER_PREFERENCES")

    t = threading.Thread(target=download)
    t.start()


def updateprogress(chunkcount, filesize):
    global CHUNK_SIZE, DOWNLOAD_PERCENT
    downloadsize = chunkcount * CHUNK_SIZE
    DOWNLOAD_PERCENT = (downloadsize / filesize) * 100
    if DOWNLOAD_PERCENT > 100:
        DOWNLOAD_PERCENT = 100

    fmutils.forceUIUpdate("USER_PREFERENCES")


def getprogress():
    global DOWNLOAD_PERCENT
    return DOWNLOAD_PERCENT