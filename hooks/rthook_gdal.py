import os
import sys

base_path = sys._MEIPASS
os.environ['GDAL_DATA'] = os.path.join(base_path, 'gdal', 'data')
os.environ['PROJ_LIB'] = os.path.join(base_path, 'proj')
