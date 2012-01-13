"""
Module :mod:`nhe.mfd.base` defines base class for MFD and a base exception
class.
"""
import abc


class MFDError(Exception):
    """
    An error happened during MFD constraint check or modification.
    """


class BaseMFD(object):
    """
    Abstract base class for Magnitude-Frequency Distribution function.
    """
    __metaclass__ = abc.ABCMeta

    #: The list of parameters' names that are required by actual
    #: MFD implementation. The property is required to be overridden.
    #: Those and only those attributes that are listed here are allowed
    #: and required as constructor's kwargs. See :meth:`set_parameters`.
    PARAMETERS = abc.abstractproperty()

    #: The set of modification type names that are supported by an MFD.
    #: Each modification should have a corresponding method named
    #: ``modify_modificationname()`` where the actual modification
    #: logic resides.
    MODIFICATIONS = abc.abstractproperty()

    def __init__(self, **parameters):
        self.set_parameters(parameters)
        self._original_parameters = parameters.copy()

    def set_parameters(self, parameters):
        """
        Assign parameters to object's attributes.

        :param parameters:
            The dictionary of parameters as passed to the constructor.
        :raises MFDError:
            If some actual parameters are missing in :attr:`PARAMETERS`
            or if something from :attr:`PARAMETERS` is missing in actual
            parameters.

        Calls :meth:`check_constraints` once everything is assigned.
        """
        defined = set(parameters)
        required = set(self.PARAMETERS)
        unexpected = defined - required
        missing = required - defined
        if missing:
            raise MFDError('These parameters are required but missing: %s'
                           % ', '.join(sorted(missing)))
        if unexpected:
            raise MFDError('These parameters are unexpected: %s'
                           % ', ' .join(sorted(unexpected)))
        for param_name in self.PARAMETERS:
            setattr(self, param_name, parameters[param_name])
        self.check_constraints()

    def modify(self, modification, parameters):
        """
        Apply a single modification to an MFD parameters.

        Reflects the modification method and calls it passing ``parameters``
        as keyword arguments. See also :attr:`MODIFICATIONS`.

        Modifications can be applied one on top of another. The logic
        of stacking modifications is up to a specific MFD implementation.
        Any number of modifications can be reverted with a single call
        to :meth:`reset`.

        :param modifictaion:
            String name representing the type of modification.
        :param parameters:
            Dictionary of parameters needed for modification.
        :raises MFDError:
            If ``modification`` is missing from :attr:`MODIFICATIONS`.
        """
        if not modification in self.MODIFICATIONS:
            raise MFDError('Modification %s is not supported by %s' %
                           modification, self)
        meth = getattr(self, 'modify_%s' % modification)
        meth(**parameters)

    def reset(self):
        """
        Reset an MFD to its original state after any number of :meth:`modify`s.
        """
        self.set_parameters(self._original_parameters)

    @abc.abstractmethod
    def check_constraints(self):
        """
        Check MFD-specific constraints and raise :exc:`MFDError`
        in case of violation.

        This method must be implemented by subclasses.
        """

    @abc.abstractmethod
    def get_annual_occurrence_rates(self):
        """
        Return an MFD histogram.

        This method must be implemented by subclasses.

        :return:
            The list of tuples, each tuple containing a pair
            ``(magnitude, occurrence_rate)``. Each pair represents
            a single bin of the histogram with ``magnitude`` being
            the center of the bin. Magnitude values are monotonically
            increasing by value of bin width.
        """
