############################################################################
#
# MODULE:       r.agent.*
# AUTHOR(S):    michael lustenberger inofix.ch
# PURPOSE:      library file for the r.agent.* suite
# COPYRIGHT:    (C) 2011 by the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class DataError(Error):
    """Exception raised for errors in the input.

    Attributes:
        expr -- Context expression in which the error occurred
        msg  -- explanation of the error
    """
    def __init__(self, expr, msg):
        self.expr = expr
        self.msg = msg
        print "DataError: " + expr + " " + msg

class InputError(Error):
    """Exception raised for errors in the input.

    Attributes:
        expr -- input expression in which the error occurred
        msg  -- explanation of the error
    """
    def __init__(self, expr, msg):
        self.expr = expr
        self.msg = msg
        print "InputError: " + expr + " " +msg

def test():
    """Test suite for Error Class"""
    try:
        raise InputError("Error Test Suite", "(no problem with this error)")
    except InputError:
        print "catched! all fine."

