import copy
import logging

class CustomHandler(logging.StreamHandler):
    def __init__(self, stream=None):
        logging.StreamHandler.__init__(self, stream)

    def emit(self, record):
        newRecord = copy.copy(record)
        newRecord.exc_info = None
        super(CustomHandler,self).emit(newRecord)
