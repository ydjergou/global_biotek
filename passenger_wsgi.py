import sys
import os

# Le bon Python est déjà sélectionné via PassengerPython dans .htaccess
sys.path.insert(0, os.path.dirname(__file__))

from app import app as application
