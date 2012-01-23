"""
Module :mod:`nhe.source.rupture` implements :class:`Rupture`.
"""

class Rupture(object):
    """
    Probabilistic rupture object represents a single earthquake rupture
    associated to a probability of occurrence value.

    :param source:
        Seismic source the rupture belongs to. An instance of one of subclasses
        of :class:`nhe.source.base.SeismicSource`.
    :param mag:
        Magnitude of the rupture.
    :param rake:
        Rupture propagation direction in degrees.
    :param hypocenter:
        A :class:`~nhe.common.geo.Point`, rupture's hypocenter.
    :param probability:
        A probability of the rupture to occur within some time span. The value
        should take into account the probabilities of these exact nodal plane,
        magnitude and hypocenter, as well as a probability of occurrence within
        a given time span (obtained from :mod:`temporal occurrence model
        <nhe.common.tom>`).
    """
    def __init__(self, source, mag, rake, hypocenter, probability, surface):
        assert mag > 0
        assert hypocenter.depth > 0
        assert 0 < probability <= 1
        self.source = source
        self.mag = mag
        self.rake = rake
        self.hypocenter = hypocenter
        self.probability = probability
        self.surface = surface


class PointSurface(object):
    def __init__(self, point, strike, dip):
        self.point = point
        self.strike = strike
        self.dip = dip


class EvenlyGriddedSurface(object):
    def __init__(self, top_left, top_right, bottom_right, bottom_left):
        self.top_left = top_left
        self.top_right = top_right
        self.bottom_right = bottom_right
        self.bottom_left = bottom_left

    def get_mesh(self, mesh_spacing):
        mesh = []
        l_line = self.top_left.equally_spaced_points(self.bottom_left,
                                                     mesh_spacing)
        r_line = self.top_right.equally_spaced_points(self.bottom_right,
                                                      mesh_spacing)
        for i, left in enumerate(l_line):
            right = r_line[i]
            mesh.append(left.equally_spaced_points(right, mesh_spacing))

        return mesh
