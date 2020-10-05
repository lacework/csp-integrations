from __future__ import print_function
from builtins import input
import os

def yesNoInput (msg):
    while True:
        user_input = input(msg)
        user_input = user_input.lower()
        if user_input == "y" or user_input == "yes" or user_input == "n" or user_input == "no":
            return user_input
        else:
            print("Please enter valid input!")

def filePathInput (msg):
    while True:
        filePath = input(msg)
        if os.path.isfile(filePath):
            return filePath
        else:
            print("File not found! Are you sure path is: \n" + filePath)
