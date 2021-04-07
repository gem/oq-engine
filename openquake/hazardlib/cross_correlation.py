import numpy as np
import numpy.matlib
from scipy import constants
from typing import Type
from abc import ABC, abstractmethod
from openquake.hazardlib.imt import PGA, SA, IMT

class CrossCorrelation(ABC):

    # TODO We need to specify the HORIZONTAL GMM COMPONENT used 

    @abstractmethod
    def get_correlation(self, from_imt: IMT, to_imt: IMT) -> float:
        """
        :param from_imt:
            An intensity measure type
        :param to_imt:
            An intensity measure type
        """
        raise NotImplementedError()


class BakerJayaram2008(CrossCorrelation):
    """
    Implements the correlation model of Baker and Jayaram published in 2008
    on Earthquake Spectra. This model works for GMRotI50.
    """

    def get_correlation(self, from_imt: IMT, to_imt: IMT) -> float:

        from_per = from_imt.period
        to_per = to_imt.period

        t_min = np.min([from_per, to_per])
        t_max = np.max([from_per, to_per])

        c1 = 1 - np.cos(constants.pi/2 -
                        0.366 * np.log(t_max/np.max([t_min, 0.109])))
        c2 = 0.0
        if t_max < 0.2:
            term1 = 1.0 - 1.0/(1.0+np.exp(100.0*t_max-5.0))
            term2 = (t_max-t_min) / (t_max-0.0099)
            c2 = 1 - 0.105 * term1 * term2
        c3 = c1
        if t_max < 0.109:
            c3 = c2
        c4 = c1 + 0.5*(np.sqrt(c3)-c3)*(1+np.cos(constants.pi*t_min/0.109))

        if t_max < 0.109:
            corr = c2
        elif t_min > 0.109:
            corr = c1
        elif t_max < 0.2:
            corr = np.amin([c2, c4])
        else:
            corr = c4

        return corr


def get_correlation_mtx(corr_model: Type[CrossCorrelation], 
        ref_imt: Type[IMT], target_imts: list, num_sites):

    """
    :param corr_model:
        An instance of a correlation models
    :param ref_imt:
        An :class:`openquake.hazardlib.imt.IMT` instance
    :param target_imts:
        A list of the target imts of size M

    :returns:
        A matrix of shape [<number of IMTs>, <number of sites>]
    """
    corr = np.array([corr_model.get_correlation(ref_imt, x)
                     for x in target_imts])
    corr = np.matlib.repmat(np.squeeze(corr), num_sites, 1).T
    return corr
