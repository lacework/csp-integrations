import logging.config
console = logging.StreamHandler()

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(levelname)s [%(asctime)s] %(module)s.%(filename)s:%(lineno)s: %(message)s'
        }
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'standard',
            'mode': 'w',
            'filename': 'output.log'
        },
        'default': {
            'level':'INFO',
            'class': 'project_logging.handler.CustomHandler',
            'formatter': 'standard',
        }
    },
    'loggers': {
        '': {
            'handlers': ['default', 'file'],
            'level': 'INFO',
            'propagate': True
        },
        'adal-python': {
            'handlers': ['default', 'file'],
            'level': 'WARN',
            'propagate': True
        },
        'requests': {
            'handlers': ['default', 'file'],
            'level': 'WARN',
            'propagate': True
        }
    }
})
