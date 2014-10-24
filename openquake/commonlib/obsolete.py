#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2014, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

############################################################################
#####   this is not used by the engine, only by the GEMScienceTools    #####
############################################################################

from openquake.nrmllib import models as nrml_models
from shapely import wkt
from openquake.hazardlib import scalerel
from openquake.hazardlib.source.rupture import Rupture as HazardlibRupture
from openquake.hazardlib import geo, mfd, pmf, source
from openquake.hazardlib.tom import PoissonTOM


class NrmlHazardlibConverter(object):
    """
    Converter from NRML objects to hazardlib objects. To be instantiated
    with the following parameters:

    :param float investigation_time:
        investigation time parameter
    :param float rupture_mesh_spacing:
        rupture mesh spacing parameter
    :param float width_of_mfd_bin:
        width of mfd bin parameter
    :param area_source_discretization:
        area source discretization parameter
    """
    def __init__(self, investigation_time, rupture_mesh_spacing,
                 width_of_mfd_bin, area_source_discretization):
        self.investigation_time = investigation_time
        self.rupture_mesh_spacing = rupture_mesh_spacing
        self.width_of_mfd_bin = width_of_mfd_bin
        self.area_source_discretization = area_source_discretization
        self.default_tom = PoissonTOM(investigation_time) \
            if investigation_time else None  # None for scenario calculator

    def __call__(self, src):
        """
        Convert a seismic source or rupture object from the NRML representation
        to the HazardLib representation. Inputs can be point, area,
        simple fault, or complex fault sources, or simple or complex fault
        ruptures.

        See :mod:`openquake.nrmllib.models` and
        :mod:`openquake.hazardlib.source`.

        :param src:
            :mod:`openquake.nrmllib.models` seismic source or rupture instance.

        :returns:
            The HazardLib representation of the input source or rupture.
        """
        if isinstance(src, (nrml_models.AreaSource, nrml_models.PointSource,
                            nrml_models.ComplexFaultSource,
                            nrml_models.SimpleFaultSource,
                            nrml_models.CharacteristicSource)):
            return self._nrml_source_to_hazardlib(src)
        elif isinstance(src, (nrml_models.ComplexFaultRuptureModel,
                              nrml_models.SimpleFaultRuptureModel)):
            return self._nrml_rupture_to_hazardlib(src)

    def _nrml_source_to_hazardlib(self, src):
        """
        Convert a NRML source object into the HazardLib representation.
        """
        # The ordering of the switch here matters because:
        #   - AreaSource inherits from PointSource
        #   - ComplexFaultSource inherits from SimpleFaultSource
        try:
            if isinstance(src, nrml_models.AreaSource):
                return self._area_to_hazardlib(src)
            elif isinstance(src, nrml_models.PointSource):
                return self._point_to_hazardlib(src)
            elif isinstance(src, nrml_models.ComplexFaultSource):
                return self._complex_to_hazardlib(src)
            elif isinstance(src, nrml_models.SimpleFaultSource):
                return self._simple_to_hazardlib(src)
            elif isinstance(src, nrml_models.CharacteristicSource):
                return self._characteristic_to_hazardlib(src)
        except:
            etype, err, tb = sys.exc_info()
            msg = ("The following error has occurred with "
                   "source id='%s', name='%s': %s" %
                   (src.id, src.name, err.message))
            raise etype, msg, tb

    def _nrml_rupture_to_hazardlib(self, src):
        """
        Convert a NRML rupture object into the HazardLib representation.

        Parameters and return values are similar to :func:`nrml_to_hazardlib`.
        """
        if isinstance(src, nrml_models.ComplexFaultRuptureModel):
            return self._complex_rupture_to_hazardlib(src)
        elif isinstance(src, nrml_models.SimpleFaultRuptureModel):
            return self._simple_rupture_to_hazardlib(src)

    def _point_to_hazardlib(self, src):
        """Convert a NRML point source to the HazardLib equivalent.

        See :mod:`openquake.nrmllib.models` and
        :mod:`openquake.hazardlib.source`.

        :param src:
            :class:`openquake.nrmllib.models.PointSource` instance.
        :returns:
            The HazardLib representation of the input source.
        """
        shapely_pt = wkt.loads(src.geometry.wkt)

        mf_dist = self._mfd_to_hazardlib(src.mfd)

        # nodal plane distribution:
        npd = pmf.PMF(
            [(x.probability,
              geo.NodalPlane(strike=x.strike, dip=x.dip, rake=x.rake))
             for x in src.nodal_plane_dist]
        )

        # hypocentral depth distribution:
        hd = pmf.PMF([(x.probability, x.depth) for x in src.hypo_depth_dist])

        msr = scalerel.get_available_magnitude_scalerel()[src.mag_scale_rel]()

        point = source.PointSource(
            source_id=src.id,
            name=src.name,
            tectonic_region_type=src.trt,
            mfd=mf_dist,
            rupture_mesh_spacing=self.rupture_mesh_spacing,
            magnitude_scaling_relationship=msr,
            rupture_aspect_ratio=src.rupt_aspect_ratio,
            upper_seismogenic_depth=src.geometry.upper_seismo_depth,
            lower_seismogenic_depth=src.geometry.lower_seismo_depth,
            location=geo.Point(shapely_pt.x, shapely_pt.y),
            nodal_plane_distribution=npd,
            hypocenter_distribution=hd,
            temporal_occurrence_model=self.default_tom,
        )

        return point

    def _area_to_hazardlib(self, src):
        """Convert a NRML area source to the HazardLib equivalent.

        See :mod:`openquake.nrmllib.models` and
        :mod:`openquake.hazardlib.source`.

        :param src:
            :class:`openquake.nrmllib.models.PointSource` instance.
        :returns:
            The HazardLib representation of the input source.
        """
        shapely_polygon = wkt.loads(src.geometry.wkt)
        hazardlib_polygon = geo.Polygon(
            # We ignore the last coordinate in the sequence here, since it is a
            # duplicate of the first. hazardlib will close the loop for us.
            [geo.Point(*x) for x in list(shapely_polygon.exterior.coords)[:-1]]
        )

        mf_dist = self._mfd_to_hazardlib(src.mfd)

        # nodal plane distribution:
        npd = pmf.PMF(
            [(x.probability,
              geo.NodalPlane(strike=x.strike, dip=x.dip, rake=x.rake))
             for x in src.nodal_plane_dist]
        )

        # hypocentral depth distribution:
        hd = pmf.PMF([(x.probability, x.depth) for x in src.hypo_depth_dist])

        msr = scalerel.get_available_magnitude_scalerel()[src.mag_scale_rel]()
        area = source.AreaSource(
            source_id=src.id,
            name=src.name,
            tectonic_region_type=src.trt,
            mfd=mf_dist,
            rupture_mesh_spacing=self.rupture_mesh_spacing,
            magnitude_scaling_relationship=msr,
            rupture_aspect_ratio=src.rupt_aspect_ratio,
            upper_seismogenic_depth=src.geometry.upper_seismo_depth,
            lower_seismogenic_depth=src.geometry.lower_seismo_depth,
            nodal_plane_distribution=npd, hypocenter_distribution=hd,
            polygon=hazardlib_polygon,
            area_discretization=self.area_source_discretization,
            temporal_occurrence_model=self.default_tom,
        )

        return area

    def _simple_to_hazardlib(self, src):
        """Convert a NRML simple fault source to the HazardLib equivalent.

        See :mod:`openquake.nrmllib.models` and
        :mod:`openquake.hazardlib.source`.

        :param src:
            :class:`openquake.nrmllib.models.SimpleFaultRuptureModel` instance.
        :returns:
            The HazardLib representation of the input source.
        """
        shapely_line = wkt.loads(src.geometry.wkt)
        fault_trace = geo.Line([geo.Point(*x) for x in shapely_line.coords])

        mf_dist = self._mfd_to_hazardlib(src.mfd)
        msr = scalerel.get_available_magnitude_scalerel()[src.mag_scale_rel]()

        simple = source.SimpleFaultSource(
            source_id=src.id,
            name=src.name,
            tectonic_region_type=src.trt,
            mfd=mf_dist,
            rupture_mesh_spacing=self.rupture_mesh_spacing,
            magnitude_scaling_relationship=msr,
            rupture_aspect_ratio=src.rupt_aspect_ratio,
            upper_seismogenic_depth=src.geometry.upper_seismo_depth,
            lower_seismogenic_depth=src.geometry.lower_seismo_depth,
            fault_trace=fault_trace,
            dip=src.geometry.dip,
            rake=src.rake,
            temporal_occurrence_model=self.default_tom,
        )

        return simple

    def _complex_to_hazardlib(self, src):
        """Convert a NRML complex fault source to the HazardLib equivalent.

        See :mod:`openquake.nrmllib.models` and
        :mod:`openquake.hazardlib.source`.

        :param src:
            :class:`openquake.nrmllib.models.ComplexFaultRuptureModel` instance
        :returns:
            The HazardLib representation of the input source.
        """
        edges_wkt = []
        edges_wkt.append(src.geometry.top_edge_wkt)
        edges_wkt.extend(src.geometry.int_edges)
        edges_wkt.append(src.geometry.bottom_edge_wkt)

        edges = []

        for edge in edges_wkt:
            shapely_line = wkt.loads(edge)
            line = geo.Line([geo.Point(*x) for x in shapely_line.coords])
            edges.append(line)
        mf_dist = self._mfd_to_hazardlib(src.mfd)
        msr = scalerel.get_available_magnitude_scalerel()[src.mag_scale_rel]()

        cmplx = source.ComplexFaultSource(
            source_id=src.id,
            name=src.name,
            tectonic_region_type=src.trt,
            mfd=mf_dist,
            rupture_mesh_spacing=self.rupture_mesh_spacing,
            magnitude_scaling_relationship=msr,
            rupture_aspect_ratio=src.rupt_aspect_ratio,
            edges=edges,
            rake=src.rake,
            temporal_occurrence_model=self.default_tom,
        )

        return cmplx

    def _characteristic_to_hazardlib(self, src):
        """
        Convert a NRML characteristic fault source to the HazardLib equivalent.

        The surface of a characteristic fault source can be one of the
        following:
            * simple fault
            * complex fault
            * one or more planar surfaces

        See :mod:`openquake.nrmllib.models` and
        :mod:`openquake.hazardlib.source`.

        :param src:
            :class:`openquake.nrmllib.models.CharacteristicSource` instance.
        :returns:
            The HazardLib representation of the input source.
        """
        mf_dist = self._mfd_to_hazardlib(src.mfd)

        if isinstance(src.surface, nrml_models.SimpleFaultGeometry):
            shapely_line = wkt.loads(src.surface.wkt)
            fault_trace = geo.Line(
                [geo.Point(*x) for x in shapely_line.coords])

            surface = geo.SimpleFaultSurface.from_fault_data(
                fault_trace,
                src.surface.upper_seismo_depth,
                src.surface.lower_seismo_depth,
                src.surface.dip,
                self.rupture_mesh_spacing,
            )
        elif isinstance(src.surface, nrml_models.ComplexFaultGeometry):
            edges_wkt = []
            edges_wkt.append(src.surface.top_edge_wkt)
            edges_wkt.extend(src.surface.int_edges)
            edges_wkt.append(src.surface.bottom_edge_wkt)

            edges = []

            for edge in edges_wkt:
                shapely_line = wkt.loads(edge)
                line = geo.Line([geo.Point(*x) for x in shapely_line.coords])
                edges.append(line)

            surface = geo.ComplexFaultSurface.from_fault_data(
                edges, self.rupture_mesh_spacing)
        else:
            # A collection of planar surfaces
            planar_surfaces = []
            for planar_surface in src.surface:
                kwargs = planar_surface.__dict__
                kwargs.update(dict(mesh_spacing=self.rupture_mesh_spacing))

                planar_surfaces.append(geo.PlanarSurface(**kwargs))

            surface = geo.MultiSurface(planar_surfaces)

        char = source.CharacteristicFaultSource(
            source_id=src.id,
            name=src.name,
            tectonic_region_type=src.trt,
            mfd=mf_dist,
            surface=surface,
            rake=src.rake,
            temporal_occurrence_model=self.default_tom,
        )
        return char

    def _simple_rupture_to_hazardlib(self, src):
        """Convert a NRML simple fault source to the HazardLib equivalent.

        See :mod:`openquake.nrmllib.models` and
        :mod:`openquake.hazardlib.source`.

        :param src:
            :class:`openquake.nrmllib.models.PointSource` instance.
        :returns:
            The HazardLib representation of the input rupture.
        """

        shapely_line = wkt.loads(src.geometry.wkt)
        fault_trace = geo.Line([geo.Point(*x) for x in shapely_line.coords])
        geom = src.geometry

        surface = geo.SimpleFaultSurface.from_fault_data(
            fault_trace, geom.upper_seismo_depth, geom.lower_seismo_depth,
            geom.dip, self.rupture_mesh_spacing)

        rupture = HazardlibRupture(
            mag=src.magnitude, rake=src.rake,
            tectonic_region_type=None, hypocenter=geo.Point(*src.hypocenter),
            surface=surface, source_typology=source.SimpleFaultSource)

        return rupture

    def _complex_rupture_to_hazardlib(self, src):
        """Convert a NRML complex fault source to the HazardLib equivalent.

        See :mod:`openquake.nrmllib.models` and
        :mod:`openquake.hazardlib.source`.

        :param src:
            :class:`openquake.nrmllib.models.PointSource` instance.
        :returns:
            The HazardLib representation of the input rupture.
        """

        edges_wkt = []
        edges_wkt.append(src.geometry.top_edge_wkt)
        edges_wkt.extend(src.geometry.int_edges)
        edges_wkt.append(src.geometry.bottom_edge_wkt)

        edges = []

        for edge in edges_wkt:
            shapely_line = wkt.loads(edge)
            line = geo.Line([geo.Point(*x) for x in shapely_line.coords])
            edges.append(line)

        surface = geo.ComplexFaultSurface.from_fault_data(
            edges, self.rupture_mesh_spacing)

        rupture = HazardlibRupture(
            mag=src.magnitude, rake=src.rake,
            tectonic_region_type=None, hypocenter=geo.Point(*src.hypocenter),
            surface=surface, source_typology=source.ComplexFaultSource)

        return rupture

    def _mfd_to_hazardlib(self, src_mfd):
        """Convert a NRML MFD to an HazardLib MFD.

        :param src_mfd:
            :class:`openquake.nrmllib.models.IncrementalMFD` or
            :class:`openquake.nrmllib.models.TGRMFD` instance.
        :returns:
            The HazardLib representation of the MFD. See
            :mod:`openquake.hazardlib.mfd`.
        """
        bin_width = self.width_of_mfd_bin
        if isinstance(src_mfd, nrml_models.TGRMFD):
            assert bin_width is not None
            return mfd.TruncatedGRMFD(
                a_val=src_mfd.a_val, b_val=src_mfd.b_val,
                min_mag=src_mfd.min_mag,
                max_mag=src_mfd.max_mag,
                bin_width=bin_width
            )
        elif isinstance(src_mfd, nrml_models.IncrementalMFD):
            return mfd.EvenlyDiscretizedMFD(
                min_mag=src_mfd.min_mag, bin_width=src_mfd.bin_width,
                occurrence_rates=src_mfd.occur_rates
            )
