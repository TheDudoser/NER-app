import logging
import os

logging.basicConfig(filename='dev.log', level=logging.INFO)
logger = logging.getLogger(__name__)

ANALYSIS_DIR = "analysis"
os.makedirs(ANALYSIS_DIR, exist_ok=True)

DICTIONARIES_DIR = "dictionaries"
os.makedirs(DICTIONARIES_DIR, exist_ok=True)

with open('.version', 'r', encoding='utf-8') as f:
    version = f.readline().strip()
