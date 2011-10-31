# This file was automatically generated by SWIG (http://www.swig.org).
# Version 2.0.4
#
# Do not make changes to this file unless you know what you are doing--modify
# the SWIG interface file instead.



from sys import version_info
if version_info >= (2,6,0):
    def swig_import_helper():
        from os.path import dirname
        import imp
        fp = None
        try:
            fp, pathname, description = imp.find_module('_oboe_ext', [dirname(__file__)])
        except ImportError:
            import _oboe_ext
            return _oboe_ext
        if fp is not None:
            try:
                _mod = imp.load_module('_oboe_ext', fp, pathname, description)
            finally:
                fp.close()
            return _mod
    _oboe_ext = swig_import_helper()
    del swig_import_helper
else:
    import _oboe_ext
del version_info
try:
    _swig_property = property
except NameError:
    pass # Python < 2.2 doesn't have 'property'.
def _swig_setattr_nondynamic(self,class_type,name,value,static=1):
    if (name == "thisown"): return self.this.own(value)
    if (name == "this"):
        if type(value).__name__ == 'SwigPyObject':
            self.__dict__[name] = value
            return
    method = class_type.__swig_setmethods__.get(name,None)
    if method: return method(self,value)
    if (not static):
        self.__dict__[name] = value
    else:
        raise AttributeError("You cannot add attributes to %s" % self)

def _swig_setattr(self,class_type,name,value):
    return _swig_setattr_nondynamic(self,class_type,name,value,0)

def _swig_getattr(self,class_type,name):
    if (name == "thisown"): return self.this.own()
    method = class_type.__swig_getmethods__.get(name,None)
    if method: return method(self)
    raise AttributeError(name)

def _swig_repr(self):
    try: strthis = "proxy of " + self.this.__repr__()
    except: strthis = ""
    return "<%s.%s; %s >" % (self.__class__.__module__, self.__class__.__name__, strthis,)

try:
    _object = object
    _newclass = 1
except AttributeError:
    class _object : pass
    _newclass = 0


class Metadata(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, Metadata, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, Metadata, name)
    __repr__ = _swig_repr
    def __init__(self, *args): 
        this = _oboe_ext.new_Metadata(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _oboe_ext.delete_Metadata
    __del__ = lambda self : None;
    __swig_getmethods__["fromString"] = lambda x: _oboe_ext.Metadata_fromString
    if _newclass:fromString = staticmethod(_oboe_ext.Metadata_fromString)
    def createEvent(self): return _oboe_ext.Metadata_createEvent(self)
    __swig_getmethods__["makeRandom"] = lambda x: _oboe_ext.Metadata_makeRandom
    if _newclass:makeRandom = staticmethod(_oboe_ext.Metadata_makeRandom)
    def copy(self): return _oboe_ext.Metadata_copy(self)
    def isValid(self): return _oboe_ext.Metadata_isValid(self)
    def toString(self): return _oboe_ext.Metadata_toString(self)
Metadata_swigregister = _oboe_ext.Metadata_swigregister
Metadata_swigregister(Metadata)

def Metadata_fromString(*args):
  return _oboe_ext.Metadata_fromString(*args)
Metadata_fromString = _oboe_ext.Metadata_fromString

def Metadata_makeRandom():
  return _oboe_ext.Metadata_makeRandom()
Metadata_makeRandom = _oboe_ext.Metadata_makeRandom

class Context(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, Context, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, Context, name)
    __repr__ = _swig_repr
    __swig_getmethods__["get"] = lambda x: _oboe_ext.Context_get
    if _newclass:get = staticmethod(_oboe_ext.Context_get)
    __swig_getmethods__["toString"] = lambda x: _oboe_ext.Context_toString
    if _newclass:toString = staticmethod(_oboe_ext.Context_toString)
    __swig_getmethods__["set"] = lambda x: _oboe_ext.Context_set
    if _newclass:set = staticmethod(_oboe_ext.Context_set)
    __swig_getmethods__["fromString"] = lambda x: _oboe_ext.Context_fromString
    if _newclass:fromString = staticmethod(_oboe_ext.Context_fromString)
    __swig_getmethods__["copy"] = lambda x: _oboe_ext.Context_copy
    if _newclass:copy = staticmethod(_oboe_ext.Context_copy)
    __swig_getmethods__["clear"] = lambda x: _oboe_ext.Context_clear
    if _newclass:clear = staticmethod(_oboe_ext.Context_clear)
    __swig_getmethods__["isValid"] = lambda x: _oboe_ext.Context_isValid
    if _newclass:isValid = staticmethod(_oboe_ext.Context_isValid)
    __swig_getmethods__["init"] = lambda x: _oboe_ext.Context_init
    if _newclass:init = staticmethod(_oboe_ext.Context_init)
    __swig_getmethods__["createEvent"] = lambda x: _oboe_ext.Context_createEvent
    if _newclass:createEvent = staticmethod(_oboe_ext.Context_createEvent)
    __swig_getmethods__["startTrace"] = lambda x: _oboe_ext.Context_startTrace
    if _newclass:startTrace = staticmethod(_oboe_ext.Context_startTrace)
    def __init__(self): 
        this = _oboe_ext.new_Context()
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _oboe_ext.delete_Context
    __del__ = lambda self : None;
Context_swigregister = _oboe_ext.Context_swigregister
Context_swigregister(Context)

def Context_get():
  return _oboe_ext.Context_get()
Context_get = _oboe_ext.Context_get

def Context_toString():
  return _oboe_ext.Context_toString()
Context_toString = _oboe_ext.Context_toString

def Context_set(*args):
  return _oboe_ext.Context_set(*args)
Context_set = _oboe_ext.Context_set

def Context_fromString(*args):
  return _oboe_ext.Context_fromString(*args)
Context_fromString = _oboe_ext.Context_fromString

def Context_copy():
  return _oboe_ext.Context_copy()
Context_copy = _oboe_ext.Context_copy

def Context_clear():
  return _oboe_ext.Context_clear()
Context_clear = _oboe_ext.Context_clear

def Context_isValid():
  return _oboe_ext.Context_isValid()
Context_isValid = _oboe_ext.Context_isValid

def Context_init():
  return _oboe_ext.Context_init()
Context_init = _oboe_ext.Context_init

def Context_createEvent():
  return _oboe_ext.Context_createEvent()
Context_createEvent = _oboe_ext.Context_createEvent

def Context_startTrace():
  return _oboe_ext.Context_startTrace()
Context_startTrace = _oboe_ext.Context_startTrace

class Event(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, Event, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, Event, name)
    def __init__(self, *args, **kwargs): raise AttributeError("No constructor defined")
    __repr__ = _swig_repr
    __swig_destroy__ = _oboe_ext.delete_Event
    __del__ = lambda self : None;
    def addInfo(self, *args): return _oboe_ext.Event_addInfo(self, *args)
    def addEdge(self, *args): return _oboe_ext.Event_addEdge(self, *args)
    def getMetadata(self): return _oboe_ext.Event_getMetadata(self)
    def metadataString(self): return _oboe_ext.Event_metadataString(self)
    __swig_getmethods__["startTrace"] = lambda x: _oboe_ext.Event_startTrace
    if _newclass:startTrace = staticmethod(_oboe_ext.Event_startTrace)
Event_swigregister = _oboe_ext.Event_swigregister
Event_swigregister(Event)

def Event_startTrace(*args):
  return _oboe_ext.Event_startTrace(*args)
Event_startTrace = _oboe_ext.Event_startTrace

class UdpReporter(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, UdpReporter, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, UdpReporter, name)
    __repr__ = _swig_repr
    def __init__(self, *args): 
        this = _oboe_ext.new_UdpReporter(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _oboe_ext.delete_UdpReporter
    __del__ = lambda self : None;
    def sendReport(self, *args): return _oboe_ext.UdpReporter_sendReport(self, *args)
UdpReporter_swigregister = _oboe_ext.UdpReporter_swigregister
UdpReporter_swigregister(UdpReporter)

class FileReporter(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, FileReporter, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, FileReporter, name)
    __repr__ = _swig_repr
    def __init__(self, *args): 
        this = _oboe_ext.new_FileReporter(*args)
        try: self.this.append(this)
        except: self.this = this
    __swig_destroy__ = _oboe_ext.delete_FileReporter
    __del__ = lambda self : None;
    def sendReport(self, *args): return _oboe_ext.FileReporter_sendReport(self, *args)
FileReporter_swigregister = _oboe_ext.FileReporter_swigregister
FileReporter_swigregister(FileReporter)

# This file is compatible with both classic and new-style classes.


