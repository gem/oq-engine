import abc


class AttenuationRelationship(object):
    __metaclass__ = abc.ABCMeta

    DEFINED_FOR_DISTANCE_RANGE = abc.abstractproperty()
    DEFINED_FOR_TECTONIC_REGION_TYPES = abc.abstractproperty()
    DEFINED_FOR_INTENCITY_MEASURE_TYPES = abc.abstractproperty()
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = abc.abstractproperty()

    REQUIRES_SITE_PARAMETERS = abc.abstractproperty()
    REQUIRES_RUPTURE_PARAMETERS = abc.abstractproperty()
    REQUIRES_DISTANCES = abc.abstractproperty()

    @abc.abstractmethod
    def get_mean_and_stddev(self, context, imt, stddev_type):
        pass

    def get_probabilities_of_exceedance(self, context, imts):
        raise NotImplementedError()

    @classmethod
    def make_context(cls, site, rupture, distances=None):
        context = AttRelContext()

        for param in cls.REQUIRES_SITE_PARAMETERS:
            attr = 'site_%s' % param
            if not hasattr(context, attr):
                raise ValueError('site parameter %r is not defined' % param)
            setattr(context, attr, getattr(site, param))

        for param in cls.REQUIRES_RUPTURE_PARAMETERS:
            attr = 'rupture_%s' % param
            if not hasattr(context, attr):
                raise ValueError('rupture parameter %r is not defined' % param)
            if param == 'mag':
                value = rupture.mag
            elif param == 'trt':
                value = rupture.tectonic_region_type
            elif param in ('strike', 'dip'):
                value = getattr(rupture.surface, 'get_%s' % param)()
            elif param == 'rake':
                value = rupture.rake
            setattr(context, value)

        for param in cls.REQUIRES_DISTANCES:
            attr = 'dist_%s' % param
            if not hasattr(context, attr):
                raise ValueError('distance %r is not defined' % param)
            if distances is not None:
                value = distances[param]
            else:
                if param == 'rrup':
                    value = rupture.surface.get_min_distance(site.location)
                elif param == 'rx':
                    value = rupture.surface.get_rx_distance(site.location)
                elif param == 'rjb':
                    value = rupture.surface.get_joyner_boore_distance(
                        site.location
                    )
                elif param == 'ztor':
                    value = rupture.surface.get_top_edge_depth()
        return context


class _NotSet(object):
    def die(self, *args, **kwargs):
        raise ValueError('parameter is not set')
    __cmp__ = __eq__ = __ne__ = __len__ = die
NOT_SET = _NotSet()


class AttRelContext(object):
    __slots__ = (
        # site parameters
        'site_vs30 site_vs30type site_z1pt0 site_z2pt5 '
        # rupture parameters
        'rup_mag rup_trt rup_strike rup_dip rup_rake '
        # distance parameters
        'dist_rrup dist_rx dist_rjb dist_ztor'
    ).split()

    def __init__(self):
        for param in type(self).__slots__:
            setattr(self, param, NOT_SET)
