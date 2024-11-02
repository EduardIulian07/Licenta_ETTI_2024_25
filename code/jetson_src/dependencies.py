import sys
import os
import cv2
import sqlite3
import numpy as np
import face_recognition
import mysql.connector
from mysql.connector import errorcode
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QDialog, QFormLayout, QMessageBox
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, Qt