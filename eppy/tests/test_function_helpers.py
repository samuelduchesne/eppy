from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import eppy.function_helpers as fh
from eppy.bunch_subclass import register_epbunch_function


class TestRegisterFunction:
    """Testing function registering"""

    def test_register_function_area(self, building):
        """Add a function that uses other default epbunch functions"""

        @register_epbunch_function(
            "twice_area",
            keys=[
                "BuildingSurface:Detailed",
                "Wall:Detailed",
                "RoofCeiling:Detailed",
                "Floor:Detailed",
                "FenestrationSurface:Detailed",
                "Shading:Site:Detailed",
                "Shading:Building:Detailed",
                "Shading:Zone:Detailed",
            ],
        )
        @property
        def twice_area(abunch):
            """simply return twice the area"""
            return abunch.area * 2

        surf = building.idfobjects["BuildingSurface:Detailed".upper()][0]
        assert surf.twice_area == surf.area * 2

    def test_register_function_conditioned_area(self, building):
        """Add a new custom function that does not come default with eppy"""

        @register_epbunch_function("conditioned_area", keys=["Zone"])
        @property
        def conditioned_area(abunch):
            zone = abunch
            area = 0
            for surface in zone.zonesurfaces:
                if surface.tilt == 180.0:
                    is_part_of = zone.Part_of_Total_Floor_Area.upper() != "NO"
                    multiplier = float(zone.Multiplier if zone.Multiplier != "" else 1)

                    area += surface.area * multiplier * is_part_of
            return area

        zone = building.idfobjects["Zone".upper()][0]
        assert dir(zone)
        assert zone.conditioned_area
