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