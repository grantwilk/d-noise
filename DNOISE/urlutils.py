"""
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


import urllib.request
import zipfile
import os
import shutil

def downloadBinaries(directory):
    os.chdir(directory)

    if os.path.isdir("OptiXDenoiser"):
        shutil.rmtree("OptiXDenoiser")

    url = "https://www.googleapis.com/drive/v3/files/1xTttPPtDWVeVQBZ5IvgphLMzfMqGwbiZ/?key=AIzaSyAeQC-x72dJTVWT6z_BqMescy4y26GG-aY&alt=media"
    filename = "OptiXDenoiserBinaries.zip"
    urllib.request.urlretrieve(url,filename)

    with zipfile.ZipFile("OptiXDenoiserBinaries.zip", 'r') as zip_ref:
        zip_ref.extractall("")

    os.remove("OptiXDenoiserBinaries.zip")