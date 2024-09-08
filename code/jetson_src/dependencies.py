import sys
import cv2
import sqlite3
import numpy as np
import face_recognition
import mysql.connector
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QLineEdit, QComboBox, QMainWindow)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer