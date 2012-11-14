import itertools



class UnhandledCommand(RuntimeError):
    """
    A command dispatcher could not locate an appropriate command handler.
    """



class CommandDispatcherMixin(object):
    """
    Dispatch commands to handlers based on their name.

    Command handler names should be of the form C{prefix_commandName},
    where C{prefix} is the value specified by L{prefix}, and must
    accept the parameters as given to L{dispatch}.

    Attempting to mix this in more than once for a single class will cause
    strange behaviour, due to L{prefix} being overwritten.

    @type prefix: C{str}
    @ivar prefix: Command handler prefix, used to locate handler attributes
    """
    prefix = None

    def dispatch(self, commandName, *args):
        """
        Perform actual command dispatch.
        """
        def _getMethodName(command):
            return '%s_%s' % (self.prefix, command)

        def _getMethod(name):
            return getattr(self, _getMethodName(name), None)

        method = _getMethod(commandName)
        if method is not None:
            return method(*args)

        method = _getMethod('unknown')
        if method is None:
            raise UnhandledCommand("No handler for %r could be found" % (_getMethodName(commandName),))
        return method(commandName, *args)



def splitEvery(n, iterable, fillvalue=None):
    """
    Partition a list into sub-lists of length given by C{n}.
    """
    args = [iter(iterable)] * n
    return itertools.izip_longest(fillvalue=fillvalue, *args)
