import os

def yesNoInput (msg):
    while True:
        user_input = raw_input(msg)
        user_input = user_input.lower()
        if user_input == "y" or user_input == "yes" or user_input == "n" or user_input == "no":
            return user_input
        else:
            print "Please enter valid input!"

def filePathInput (msg):
    while True:
        filePath = raw_input(msg)
        if os.path.isfile(filePath):
            return filePath
        else:
            print "File not found! Are you sure path is: \n" + filePath
