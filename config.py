import logging
import os
from typing import Final
from zoneinfo import ZoneInfo

logging.basicConfig(filename='dev.log', level=logging.INFO)
logger = logging.getLogger(__name__)

with open('.version', 'r', encoding='utf-8') as f:
    version = f.readline().strip()

DATABASE_URL = os.getenv('DATABASE_URL')

VL_TIMEZONE: Final = ZoneInfo("Asia/Vladivostok")
