"""

General purpose classes, functions, global variables and imports

"""

### Local

from wonka.utils._type_utils import *
from wonka.utils._text_formatting import *
from wonka.utils._graph_formatting import *

###

from dataclasses import dataclass

import os, sys
import shutil
from pathlib import Path
import webbrowser
import pprint
import re
import copy
import time

from owlready2 import *
import rdflib

import numpy as np
import pandas as pd
from tabulate import tabulate

from pyvis.network import Network
import networkx as nx

# # Dev only
# from icecream import ic, install

# install()  # icecream


"""

Toolbox

"""


def setattrs(_self, **kwargs):
    """set multiple attributes to the first argument at once (passed on as kwargs)"""
    for k, v in kwargs.items():
        setattr(_self, k, v)


# def make_same_size(*args: Sequence, fill_with=None):
#     to_size = len(max(*args, key=lambda l: len(l)))
#     out = copy.deepcopy(args)
#     for seq in out:
#         seq.extend([fill_with] * (to_size - len(seq)))
#     return out


def make_same_size(*args: Sequence, fill_with=None):
    max_len = max(map(len, args))
    return [seq + [fill_with] * (max_len - len(seq)) for seq in args]


"""

DEBUG & LOGGING

"""

import traceback
import logging, colorlog


def generate_method(obj: object, name: str, function: Callable, set_kwargs={}):
    """generate a method and set some of its default kwargs (/!\ lambda function)"""
    setattr(
        obj, name, lambda *args, **kwargs: function(*args, **{**kwargs, **set_kwargs})
    )


class Logger:
    """Custom logger"""

    def __init__(self) -> None:
        self.logs = []
        Logger.setup_logging()
        self.logger = logging.getLogger(__name__)
        for logtype in [
            "debug",
            "info",
            "warning",
            "error",
            "critical",
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL",
        ]:
            generate_method(self, logtype, self.log, set_kwargs=dict(logtype=logtype))

    @staticmethod
    def setup_logging():
        """customise logger display"""
        root = logging.getLogger(__name__)
        root.setLevel(logging.DEBUG)
        format = "%(asctime)s - %(levelname)-8s - %(message)s"
        date_format = "%H:%M:%S"  # '%Y-%m-%d %H:%M:%S'
        if "colorlog" in sys.modules and os.isatty(2):
            cformat = "%(log_color)s" + format
            f = colorlog.ColoredFormatter(
                cformat,
                date_format,
                log_colors={
                    "DEBUG": "blue",
                    "WARNING": "bold_yellow",
                    "INFO": "green",
                    "ERROR": "bold_red",
                    "CRITICAL": "bold_red",
                },
            )
            # Available colors:
            #   black, red, green, yellow, blue, purple, cyan and white
            # Options:
            #   {color}, fg_{color}, bg_{color}, reset                  : foreground/background color; reset
            #   bold, bold_{color}, fg_bold_{color}, bg_bold_{color}    : bold/bright
            #   thin, thin_{color}, fg_thin_{color}                     : thin
        else:
            f = logging.Formatter(format, date_format)
        ch = logging.StreamHandler()
        ch.setFormatter(f)
        root.addHandler(ch)

    def log(
        self,
        msg,
        check=None,
        show_only_once=False,
        logtype="info",
        use_pprint=False,
        *args,
        **kwargs,
    ):
        """conditional logging
        `check` corresponds to an assertion, False triggers the logger
        """
        if not check:
            # allow fancy formatting...
            if isinstance(msg, str):
                disp_msg = [msg]
            else:
                if use_pprint:
                    disp_msg = [pprint.pformat(m) for m in msg]
                else:
                    disp_msg = msg
            # log
            if logtype in ["critical", "CRITICAL", "error", "ERROR"]:
                if check == False:
                    try:
                        raise AssertionError
                    except:
                        # caller = getframeinfo(stack()[2][0])
                        # print('\nFile "%s":%d:\n\n\t%s\n' % (caller.filename, caller.lineno, caller.code_context[0][:-1]))
                        print("\n".join(traceback.format_stack()[:-2]))
                        exit()
                else:
                    print(disp_msg)
                    exit()
                    for dmsg in disp_msg:
                        getattr(self.logger, logtype)(dmsg, *args, **kwargs)
                    exit()
            else:
                if not show_only_once or (show_only_once and not msg in self.logs):
                    for dmsg in disp_msg:
                        getattr(self.logger, logtype)(dmsg, *args, **kwargs)
                    self.logs.append(msg)
        return check

    def debug(self, msg, check=None):
        """Overwritten at initialisation"""

    def info(self, msg, check=None):
        """Overwritten at initialisation"""

    def warning(self, msg, check=None):
        """Overwritten at initialisation"""

    def error(self, msg, check=None):
        """Overwritten at initialisation"""

    def critical(self, msg, check=None):
        """Overwritten at initialisation"""


log = Logger()

### mute TqdmExperimentalWarning (rich's tqdm equivalent being in beta version ATTOW)
import warnings
from tqdm import TqdmExperimentalWarning

warnings.filterwarnings("ignore", category=TqdmExperimentalWarning)
