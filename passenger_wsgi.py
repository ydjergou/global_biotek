import sys
import os

# Ajoute le répertoire de l'app au path Python
INTERP = "/home/htesbanzny/virtualenv/global-biotek/3.12/bin/python"
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

sys.path.insert(0, os.path.dirname(__file__))

from app import app as application
