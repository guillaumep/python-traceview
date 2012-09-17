""" Tracelytics instrumentation API for Python.

Copyright (C) 2012 by Tracelytics, Inc.
All rights reserved.
"""
from oboe_ext import Context as SwigContext, Event as SwigEvent, UdpReporter, Metadata
from oboe.rum import rum_header, rum_footer

import logging
import inspect
import random
import sys
import types
import traceback

# defaultdict not implemented before 2.5
from backport import defaultdict

from decorator import decorator

__version__ = '1.2.0'
__all__ = ['config', 'Context', 'UdpReporter', 'Event']

# configuration defaults
config = dict()
config['tracing_mode'] = 'through'      # always, through, never
config['sample_rate'] = 0.3             # out of 1.0
config['reporter_host'] = '127.0.0.1'   # you probably don't want to change the
config['reporter_port'] = 7831          # last two options

config['inst_enabled'] = defaultdict(lambda: True)

SwigContext.init()

_log = logging.getLogger(__name__)
reporter_instance = None

###############################################################################
# Low-level Public API
###############################################################################

class OboeException(Exception):
    pass

def _str_backtrace(backtrace=None):
    if backtrace:
        return "".join(traceback.format_tb(backtrace))
    else:
        return "".join(traceback.format_stack()[:-1])

class Context(object):
    # Basically a wrapper around the swig Metadata

    def __init__(self, md):
        if isinstance(md, basestring):
            self._md = Metadata.fromString(md)
        else:
            self._md = md

    # For interacting with the thread-local Context

    @classmethod
    def get_default(cls):
        """Returns the Context currently stored as the thread-local default."""
        return cls(SwigContext)

    def set_as_default(self):
        """Sets this object as the thread-local default Context."""
        SwigContext.set(self._md)

    @classmethod
    def clear_default(cls):
        """Removes the current thread-local Context."""
        SwigContext.clear()

    # For starting/stopping traces

    @classmethod
    def start_trace(cls, layer, xtr=None):
        """Returns a Context and a start event.

        Takes sampling into account -- may return an (invalid Context, event) pair.
        """

        tracing_mode = config['tracing_mode']
        md = None
        if xtr and tracing_mode in ['always', 'through']:
            # Continuing a trace from another, external, layer
            md = Metadata.fromString(xtr)

        if xtr:
            evt = md.createEvent()
        elif tracing_mode == 'always' and random.random() < config['sample_rate']:
            if not md:
                md = Metadata.makeRandom()
            evt = SwigEvent.startTrace(md)
        else:
            evt = None

        return cls(md), Event(evt, 'entry', layer) if evt else NullEvent()

    def end_trace(self, event): # Reports the last event in a trace
        """Ends this trace, rendering this Context invalid."""
        self.report(event)

    def create_event(self, label, layer):
        """Returns an Event associated with this Context."""
        if self.is_valid():
            return Event(self._md.createEvent(), label, layer)
        else:
            return NullEvent()

    def report(self, event):
        """Report this Event."""
        if self.is_valid() and event.is_valid():
            if self._md == SwigContext:
                _reporter().sendReport(event._evt)
            else:
                _reporter().sendReport(event._evt, self._md)

    def is_valid(self):
        """Returns whether this Context is valid.

        Call this before doing expensive introspection. If this returns False,
        then any event created by this Context will not actually return
        information to Tracelytics.
        """
        return self._md and self._md.isValid()

    def copy(self):
        """Make a clone of this Context."""
        return self.__class__(self._md)

    def __str__(self):
        return self._md.toString()

class Event(object):
    """An Event is a key/value bag that will be reported to the Tracelyzer."""

    def __init__(self, raw_evt, label, layer):
        self._evt = raw_evt
        self._evt.addInfo('Label', label)
        self._evt.addInfo('Layer', layer)

    def add_edge(self, ctx):
        """Connect an additional Context to this Event.

        All Events are created with an edge pointing to the previous Event. This
        creates an additional edge. This pattern is useful for entry/exit pairs
        in a layer.
        """
        if ctx._md == SwigContext:
            self._evt.addEdge(ctx._md.get())
        else:
            self._evt.addEdge(ctx._md)

    def add_edge_str(self, xtr):
        """Adds an edge to this Event, based on a str(Context).

        Useful for continuing a trace, e.g., from an X-Trace header in a service
        call.
        """
        self._evt.addEdgeStr(xtr)

    def add_info(self, key, value):
        """Add a key/value pair to this event."""
        self._evt.addInfo(key, value)

    def add_backtrace(self, backtrace=None):
        """Add a backtrace to this event.

        If backtrace is None, grab the backtrace from the current stack trace.
        """
        self.add_info('Backtrace', _str_backtrace(backtrace))

    def is_valid(self):
        """Returns whether this event will be reported to the Tracelyzer."""
        return True

    def id(self):
        """Returns a string version of this Event.

        Useful for attaching to output service calls (e.g., an X-Trace request
        header).
        """
        return self._evt.metadataString()

class NullEvent(object):
    """Subclass of event that will not be reported to the Tracelyzer.

    All methods here are no-ops. Checking for this class can be done
    (indirectly) by calling is_valid() on an object.
    """

    def __init__(self):
        pass
    def add_edge(self, event):
        pass
    def add_edge_str(self, op_id):
        pass
    def add_info(self, key, value):
        pass
    def add_backtrace(self, backtrace=None):
        pass
    def is_valid(self):
        return False
    def id(self):
        return ''

###############################################################################
# High-level Public API
###############################################################################

try:
    import cStringIO, cProfile, pstats
    found_cprofile = True
except ImportError:
    found_cprofile = False

def _get_profile_info(p):
    """Retursn a sorted set of stats from a cProfile instance."""
    sio = cStringIO.StringIO()
    s = pstats.Stats(p, stream=sio)
    s.sort_stats('time')
    s.print_stats(15)
    stats = sio.getvalue()
    sio.close()
    return stats

def _log_event(evt, keys=None, store_backtrace=True, backtrace=None, edge_str=None):
    if keys is None:
        keys = {}

    for k, v in keys.items():
        evt.add_info(k, v)

    if store_backtrace:
        evt.add_backtrace(backtrace)

    if edge_str:
        evt.add_edge_str(edge_str)

    ctx = Context.get_default()
    ctx.report(evt)

def log(label, layer, keys=None, store_backtrace=True, backtrace=None, edge_str=None):
    """Report a single tracing event.

    :label: 'entry', 'exit', 'info', or 'error'
    :layer: The layer name
    :keys: A optional dictionary of key-value pairs to report.
    :store_backtrace: Whether to report a backtrace. Default: True
    :backtrace: The backtrace to report. Default: this call.
    """
    ctx = Context.get_default()
    if not ctx.is_valid():
        return
    evt = ctx.create_event(label, layer)
    _log_event(evt, keys=keys, store_backtrace=store_backtrace, backtrace=backtrace, edge_str=edge_str)

def start_trace(layer, xtr=None, keys=None, store_backtrace=True, backtrace=None):
    """Start a new trace, or continue one from an external layer.

    :layer: The layer name of the root of the trace.
    :xtr: The X-Trace ID to continue this trace with.
    :keys: An optional dictionary of key-value pairs to report.
    :store_backtrace: Whether to report a backtrace. Default: True
    :backtrace: The backtrace to report. Default: this call.
    """
    ctx, evt = Context.start_trace(layer, xtr=xtr)
    if not ctx.is_valid():
        return
    ctx.set_as_default()
    _log_event(evt, keys=keys, store_backtrace=store_backtrace, backtrace=backtrace)

def end_trace(layer, keys=None):
    """End a trace, reporting a final event.

    This will end a trace locally. If the X-Trace ID returned here is reported
    externally, other processes can continue this trace.

    :layer: The layer name of the final layer.
    :keys: An optional dictionary of key-value pairs to report.
    """
    ctx = Context.get_default()
    if not ctx.is_valid():
        return
    evt = ctx.create_event('exit', layer)
    _log_event(evt, keys=keys, store_backtrace=False)
    ctx_id = last_id()
    Context.clear_default()
    return ctx_id

def log_entry(layer, keys=None, store_backtrace=True, backtrace=None):
    """Report the first event of a new layer.

    :layer: The layer name.
    :keys: An optional dictionary of key-value pairs to report.
    :store_backtrace: Whether to report a backtrace. Default: True
    :backtrace: The backtrace to report. Default: this call.
    """
    ctx = Context.get_default()
    if not ctx.is_valid():
        return
    evt = ctx.create_event('entry', layer)
    _log_event(evt, keys=keys, store_backtrace=store_backtrace, backtrace=backtrace)

def log_error(err_class, err_msg, store_backtrace=True, backtrace=None):
    """Report an error event.

    :err_class: The class of error to report, e.g., the name of the Exception.
    :err_msg: The specific error that occurred.
    :store_backtrace: Whether to report a backtrace. Default: True
    :backtrace: The backtrace to report. Default: this call.
    """
    ctx = Context.get_default()
    if not ctx.is_valid():
        return
    evt = ctx.create_event('error', None)
    keys = {'ErrorClass': err_class,
            'ErrorMsg': err_msg}
    _log_event(evt, keys=keys, store_backtrace=store_backtrace, backtrace=backtrace)

def log_exception(msg=None, store_backtrace=True):
    """Report the last thrown exception as an error

    :msg: An optional message, to override err_msg. Defaults to str(Exception).
    :store_backtrace: Whether to store the Exception backtrace.
    """
    typ, val, tb = sys.exc_info()
    if typ is None:
        raise OboeException('log_exception should only be called from an exception context (e.g., except: block)')
    if msg is None:
        msg = str(val)

    if store_backtrace:
        backtrace = tb
    else:
        backtrace = None

    log_error(typ.__name__, msg, store_backtrace=store_backtrace, backtrace=backtrace)

def log_exit(layer, keys=None, store_backtrace=True, backtrace=None, edge_str=None):
    """Report the last event of the current layer.

    :layer: The layer name.
    :keys: An optional dictionary of key-value pairs to report.
    :store_backtrace: Whether to report a backtrace. Default: True
    :backtrace: The backtrace to report. Default: this call.
    """
    ctx = Context.get_default()
    if not ctx.is_valid():
        return
    evt = ctx.create_event('exit', layer)
    _log_event(evt, keys=keys, store_backtrace=store_backtrace, backtrace=backtrace, edge_str=edge_str)

def last_id():
    """Returns a string representation the last event reported."""
    return str(Context.get_default())

###############################################################################
# Python-specific functions
###############################################################################

def _function_signature(func):
    """Returns a string representation of the function signature of the given func."""
    name = func.__name__
    (args, varargs, keywords, defaults) = inspect.getargspec(func)
    argstrings = []
    if defaults:
        first = len(args)-len(defaults)
        argstrings = args[:first]
        for i in range(first, len(args)):
            d = defaults[i-first]
            if isinstance(d, str):
                d = "'"+d+"'"
            else:
                d = str(d)
            argstrings.append(args[i]+'='+d)
    else:
        argstrings = args
    if varargs:
        argstrings.append('*'+varargs)
    if keywords:
        argstrings.append('**'+keywords)
    return name+'('+', '.join(argstrings)+')'

def trace(layer='Python', xtr_hdr=None, kvs=None):
    """ Decorator to begin a new trace on a block of code.  Takes into account
    oboe.config['tracing_mode'] as well as oboe.config['sample_rate'], so may
    not always start a trace.

    :layer: layer name to report as
    :xtr_hdr: optional, incoming x-trace header if available
    :kvs: optional, dictionary of additional key/value pairs to report
    """
    def _trace_wrapper(func, *f_args, **f_kwargs):
        start_trace(layer, keys=kvs, xtr=xtr_hdr)
        try:
            res = func(*f_args, **f_kwargs)
        except Exception:
            # log exception and re-raise
            log_exception()
            raise
        finally:
            end_trace(layer)

        return res # return output of func(*f_args, **f_kwargs)

    _trace_wrapper._oboe_wrapped = True     # mark our wrapper for protection below

    # instrumentation helper decorator, called to add wrapper at "decorate" time
    def decorate_with_trace(f):
        if getattr(f, '_oboe_wrapped', False):   # has this function already been wrapped?
            return f                             # then pass through
        return decorator(_trace_wrapper, f)      # otherwise wrap function f with wrapper

    return decorate_with_trace

class profile_block(object):
    """A context manager for oboe profiling a block of code with Tracelytics Oboe.

    Reports an error event between entry and exit if an exception is thrown,
    then reraises.

    :profile_name: the profile name to use when reporting.  this should be
        unique to the profiled method.
    :store_backtrace: whether to capture a backtrace or not (False)
    :profile: profile this function with cProfile and report the result
    """
    def __init__(self, profile_name, profile=False, store_backtrace=False):
        self.profile_name = profile_name
        self.use_cprofile = profile
        self.backtrace = store_backtrace
        self.p = None # possible cProfile.Profile() instance

    def __enter__(self):
        if not Context.get_default().is_valid():
            return

        # build entry event
        entry_kvs = { 'Language' : 'python',
                      'ProfileName' : self.profile_name,
                        # XXX We can definitely figure out a way to make these
                        # both available and fast.  For now, this is ok.
                      'File': '',
                      'LineNumber': 0,
                      'Module': '',
                      'FunctionName': '',
                      'Signature': ''}
        log('profile_entry', None, keys=entry_kvs, store_backtrace=self.backtrace)

        # begin profiling
        if self.use_cprofile and found_cprofile:
            self.p = cProfile.Profile()
            self.p.enable(subcalls=True)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not Context.get_default().is_valid():
            return

        # end profiling
        stats = None
        if self.use_cprofile and found_cprofile and self.p:
            stats = _get_profile_info(self.p)

        # exception?
        if exc_type:
            log_exception()

        # build exit event
        exit_kvs = {}
        if self.use_cprofile and stats:
            exit_kvs['ProfileStats'] = stats
        exit_kvs['Language'] = 'python'
        exit_kvs['ProfileName'] = self.profile_name

        log('profile_exit', None, keys=exit_kvs, store_backtrace=self.backtrace)

def profile_function(profile_name, store_args=False, store_return=False, store_backtrace=False,
                     profile=False, callback=None, entry_kvs=None):
    """Wrap a method for tracing and profiling with the Tracelytics Oboe library.

    Reports an error event between entry and exit if an exception is thrown,
    then reraises.

    :profile_name: the profile name to use when reporting.  this should be
        unique to the profiled method.
    :store_return: report the return value of this function
    :store_args: report the arguments to this function
    :store_backtrace: whether to capture a backtrace or not (False)
    :profile: profile this function with cProfile and report the result
    :callback: if set, calls this function after the wrapped function returns,
        which examines the function, arguments, and return value, and may add
        more K/V pairs to the dictionary to be reported
    """

    def before(func, f_args, f_kwargs):
        # get filename, line number, etc, and cache in wrapped function to avoid overhead
        def cache(name, value_func):
            try:
                if not hasattr(func, name):
                    setattr(func, name, value_func())
            except Exception:
                setattr(func, name, None)

        cache('_oboe_file', lambda: inspect.getsourcefile(func))
        cache('_oboe_file', lambda: inspect.getsourcefile(func))
        cache('_oboe_line_number', lambda: inspect.getsourcelines(func)[1])
        cache('_oboe_module', lambda: inspect.getmodule(func).__name__)
        cache('_oboe_signature', lambda: _function_signature(func))

        keys = {'Language': 'python',
                'ProfileName': profile_name,
                'File': getattr(func, '_oboe_file'),
                'LineNumber': getattr(func, '_oboe_line_number'),
                'Module': getattr(func, '_oboe_module'),
                'FunctionName': getattr(func, '__name__'),
                'Signature': getattr(func, '_oboe_signature')}
        return f_args, f_kwargs, keys

    def after(func, f_args, f_kwargs, res):

        return {'Language': 'python',
                'ProfileName': profile_name}

    # Do function passed in here expect to be bound (have im_func/im_class)?

    return log_method(None,
                      store_return=store_return,
                      store_args=store_args,
                      store_backtrace=store_backtrace,
                      before_callback=before,
                      callback=after,
                      profile=profile,
                      entry_kvs=entry_kvs)

def log_method(layer, store_return=False, store_args=False, store_backtrace=False,
               before_callback=None, callback=None, profile=False, entry_kvs=None,
               send_entry_event=True, send_exit_event=True):
    """Wrap a method for tracing with the Tracelytics Oboe library.

    As opposed to profile_function, this decorator gives the method its own layer

    Reports an error event between entry and exit if an exception is thrown,
    then reraises.

    :layer: the layer to use when reporting. If none, this layer will be a
        profile.
    :store_return: report the return value
    :store_args: report the arguments to this function
    :before_callback: if set, calls this function before the wrapped function is
        called. This function can change the args and kwargs, and can return K/V
        pairs to be reported in the entry event.
    :callback: if set, calls this function after the wrapped function returns,
        which examines the function, arguments, and return value, and may add
        more K/V pairs to the dictionary to be reported
    """
    if not entry_kvs:
        entry_kvs = {}

    # run-time event-reporting function, called at each invocation of func(f_args, f_kwargs)
    def _log_method_wrapper(func, *f_args, **f_kwargs):
        if not Context.get_default().is_valid():            # tracing not enabled?
            return func(*f_args, **f_kwargs) # pass through to func right away
        if store_args:
            entry_kvs.update( {'args' : f_args, 'kwargs': f_kwargs} )
        if before_callback:
            before_res = before_callback(func, f_args, f_kwargs)
            if before_res:
                f_args, f_kwargs, extra_entry_kvs = before_res
                entry_kvs.update(extra_entry_kvs)
        if store_backtrace:
            entry_kvs['Backtrace'] = _str_backtrace()
        # is func an instance method?
        if 'im_class' in dir(func):
            entry_kvs['Class'] = func.im_class.__name__

        if send_entry_event:
            # log entry event
            if layer is None:
                log('profile_entry', layer, keys=entry_kvs, store_backtrace=False)
            else:
                log('entry', layer, keys=entry_kvs, store_backtrace=False)

        res = None   # return value of wrapped function
        stats = None # cProfile statistics, if enabled
        try:
            if profile and found_cprofile: # use cProfile?
                p = cProfile.Profile()
                res = p.runcall(func, *f_args, **f_kwargs) # call func via cProfile
                stats = _get_profile_info(p)
            else: # don't use cProfile, call func directly
                res = func(*f_args, **f_kwargs)
        except Exception:
            # log exception and re-raise
            log_exception()
            raise
        finally:
            # prepare data for reporting exit event
            exit_kvs = {}
            edge_str = None

            # call the callback function, if set, and merge its return
            # values with the exit event's reporting data
            if callback and callable(callback):
                cb_ret = callback(func, f_args, f_kwargs, res)
                # callback can optionally return a 2-tuple, where the
                # second parameter is an additional edge to add to
                # the exit event
                if isinstance(cb_ret, tuple) and len(cb_ret) == 2:
                    cb_ret, edge_str = cb_ret
                if cb_ret:
                    exit_kvs.update(cb_ret)

            # (optionally) report return value
            if store_return:
                exit_kvs['ReturnValue'] = str(res)

            # (optionally) report profiler results
            if profile and stats:
                exit_kvs['ProfileStats'] = stats

            if send_exit_event:
                # log exit event
                if layer is None:
                    log('profile_exit', layer, keys=exit_kvs, store_backtrace=False, edge_str=edge_str)
                else:
                    log('exit', layer, keys=exit_kvs, store_backtrace=False, edge_str=edge_str)

        return res # return output of func(*f_args, **f_kwargs)

    _log_method_wrapper._oboe_wrapped = True     # mark our wrapper for protection below

    # instrumentation helper decorator, called to add wrapper at "decorate" time
    def decorate_with_log_method(f):
        if getattr(f, '_oboe_wrapped', False):   # has this function already been wrapped?
            return f                             # then pass through
        if hasattr(f, 'im_func'):                # Is this a bound method of an object
            f = f.im_func                        # then wrap the unbound method
        return decorator(_log_method_wrapper, f) # otherwise wrap function f with wrapper

    # return decorator function with arguments to log_method() baked in
    return decorate_with_log_method

def _reporter():
    global reporter_instance

    if not reporter_instance:
        reporter_instance = UdpReporter(config['reporter_host'], str(config['reporter_port']))

    return reporter_instance

def _Event_addInfo_safe(func):
    def wrapped(*args, **kw):
        try: # call SWIG-generated Event.addInfo (from oboe_ext.py)
            return func(*args, **kw)
        except NotImplementedError: # unrecognized type passed to addInfo SWIG binding
            # args: [self, KeyName, Value]
            if len(args) == 3 and isinstance(args[1], basestring):
                # report this error
                func(args[0], '_Warning', 'Bad type for %s: %s' % (args[1], type(args[2])))
                # last resort: coerce type to string
                if hasattr(args[2], '__str__'):
                    return func(args[0], args[1], str(args[2]))
                elif hasattr(args[2], '__repr__'):
                    return func(args[0], args[1], repr(args[2]))
    return wrapped

###############################################################################
# Backwards compatability
###############################################################################

setattr(SwigEvent, 'addInfo', _Event_addInfo_safe(getattr(SwigEvent, 'addInfo')))

def _old_context_log(cls, layer, label, backtrace=False, **kwargs):
    _log.warn('oboe.Context.log is deprecated. Please use oboe.log (and note signature change).')
    log(label, layer, store_backtrace=backtrace, keys=kwargs)

def _old_context_log_error(cls, exception=None, err_class=None, err_msg=None, backtrace=True):
    _log.warn('oboe.Context.log_error is deprecated. Please use oboe.log_error (and note signature change).')
    if exception:
        err_class = exception.__class__.__name__
        err_msg = str(exception)
    store_backtrace = False
    if backtrace:
        _, _, tb = sys.exc_info()
        store_backtrace = True
    return log_error(err_class, err_msg, store_backtrace=store_backtrace, backtrace=tb)

def _old_context_log_exception(cls, msg=None, exc_info=None, backtrace=True):
    _log.warn('oboe.Context.log_exception is deprecated. Please use oboe.log_exception (and note signature change).')
    typ, val, tb = exc_info or sys.exc_info()
    if msg is None:
        msg = str(val)
    return log_error(typ.__name__, msg, store_backtrace=backtrace, backtrace=tb)

def _old_context_trace(cls, layer='Python', xtr_hdr=None, kvs=None):
    _log.warn('oboe.Context.trace is deprecated. Please use oboe.trace (and note signature change).')
    return trace(layer, xtr_hdr=kvs, kvs=kvs)

def _old_context_profile_function(cls, profile_name, store_args=False, store_return=False, store_backtrace=False,
                             profile=False, callback=None, **entry_kvs):
    _log.warn('oboe.Context.trace is deprecated. Please use oboe.trace (and note signature change).')
    return profile_function(profile_name, store_args=False, store_return=False, store_backtrace=False,
                            profile=False, callback=None, entry_kvs=entry_kvs)

def _old_context_log_method(cls, layer='Python', store_return=False, store_args=False,
                       callback=None, profile=False, **entry_kvs):
    _log.warn('oboe.Context.log_method is deprecated. Please use oboe.log_method (and note signature change).')
    return log_method(layer, store_return=store_return, store_args=store_args,
                      callback=callback, profile=profile, entry_kvs=entry_kvs)

class _old_context_profile_block(profile_block):
    def __init__(self, *args, **kw):
        _log.warn('oboe.Context.profile_block is deprecated. '
                  'Please use oboe.profile_block (and note signature change).')
        super(_old_context_profile_block, self).__init__(*args, **kw)

def _old_context_to_string(cls):
    _log.warn('oboe.Context.toString is deprecated. Please use str(oboe.Context.get_default())')
    return str(Context.get_default())

def _old_context_from_string(cls, md_string):
    _log.warn('oboe.Context.fromString is deprecated.')
    c = Context(md_string)
    c.set_as_default()

def _old_context_is_valid(cls):
    _log.warn('oboe.Context.isValid is deprecated. Please use oboe.Context.get_default().is_valid()')
    return Context.get_default().is_valid()

setattr(Context, 'log',              types.MethodType(_old_context_log, Context))
setattr(Context, 'log_error',        types.MethodType(_old_context_log_error, Context))
setattr(Context, 'log_exception',    types.MethodType(_old_context_log_exception, Context))
setattr(Context, 'log_method',       types.MethodType(_old_context_log_method, Context))
setattr(Context, 'trace',            types.MethodType(_old_context_trace, Context))
setattr(Context, 'profile_function', types.MethodType(_old_context_profile_function, Context))
setattr(Context, 'profile_block',    _old_context_profile_block)
setattr(Context, 'toString',         types.MethodType(_old_context_to_string, Context))
setattr(Context, 'fromString',       types.MethodType(_old_context_from_string, Context))
setattr(Context, 'isValid',          types.MethodType(_old_context_is_valid, Context))
