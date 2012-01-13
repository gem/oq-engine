"""
Module :mod:`nhe.mfd.base` defines base class for MFD and a base exception
class.
"""
import abc


class MFDError(Exception):
    """
    An error happened during MFD constraint check.
    """


class BaseMFD(object):
    """
    Abstract base class for Magnitude-Frequency Distribution function.
    """
    __metaclass__ = abc.ABCMeta

    #: The list of parameters names that are required by actual
    #: MFD implementation. The property is required to be overridden.
    #: Those and only those attributes that are listed here are allowed
    #: and required as constructor's kwargs. See :meth:`set_parameters`.
    PARAMETERS = abc.abstractproperty()

    def __init__(self, **parameters):
        self.set_parameters(parameters)

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
