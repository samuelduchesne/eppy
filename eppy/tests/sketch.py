from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from _collections import defaultdict


headers = """component    Node    ZoneSplitter    ZoneInlets    OutdoorNode    ExhaustNode    NotReferenced    ZoneMixer""".split(    )

data = """AirTerminal:SingleDuct:Uncontrolled    Zone Supply Air Node Name    TRUE    FALSE    FALSE    FALSE    FALSE    FALSE
AirTerminal:SingleDuct:Uncontrolled    Zone Supply Air Node Name    FALSE    TRUE    FALSE    FALSE    FALSE    FALSE
ZoneHVAC:AirDistributionUnit    Air Dist Unit Outlet Node Name    FALSE    TRUE    FALSE    FALSE    FALSE    FALSE
AirTerminal:SingleDuct:ConstantVolume:Reheat    Air Inlet Node Name    TRUE    FALSE    FALSE    FALSE    FALSE    FALSE
AirTerminal:SingleDuct:ConstantVolume:Reheat    Air Outlet Node Name    FALSE    TRUE    FALSE    FALSE    FALSE    FALSE
AirTerminal:SingleDuct:VAV:NoReheat    Air Inlet Node Name    TRUE    FALSE    FALSE    FALSE    FALSE    FALSE
AirTerminal:SingleDuct:VAV:NoReheat    Air Outlet Node Name    FALSE    TRUE    FALSE    FALSE    FALSE    FALSE
AirTerminal:SingleDuct:VAV:Reheat:VariableSpeedFan    Air Inlet Node Name    TRUE    FALSE    FALSE    FALSE    FALSE    FALSE
AirTerminal:SingleDuct:VAV:Reheat:VariableSpeedFan    Air Outlet Node Name    FALSE    TRUE    FALSE    FALSE    FALSE    FALSE
AirTerminal:SingleDuct:VAV:HeatAndCool:NoReheat    Air Inlet Node Name    TRUE    FALSE    FALSE    FALSE    FALSE    FALSE
AirTerminal:SingleDuct:VAV:HeatAndCool:NoReheat    Air Outlet Node Name    FALSE    TRUE    FALSE    FALSE    FALSE    FALSE
Fan:ZoneExhaust    Air Inlet Node Name    TRUE    FALSE    FALSE    FALSE    FALSE    FALSE
Fan:ZoneExhaust    Air Outlet Node Name    FALSE    TRUE    FALSE    FALSE    FALSE    FALSE
ZoneHVAC:Dehumidifier:DX    Air Inlet Node Name    TRUE    FALSE    FALSE    FALSE    FALSE    FALSE
ZoneHVAC:Dehumidifier:DX    Air Outlet Node Name    FALSE    TRUE    FALSE    FALSE    FALSE    FALSE
ZoneHVAC:RefrigerationChillerSet    Air Inlet Node Name    TRUE    FALSE    FALSE    FALSE    FALSE    FALSE
ZoneHVAC:RefrigerationChillerSet    Air Outlet Node Name    FALSE    TRUE    FALSE    FALSE    FALSE    FALSE
ZoneHVAC:WaterToAirHeatPump    Air Inlet Node Name    TRUE    FALSE    FALSE    FALSE    FALSE    FALSE
ZoneHVAC:WaterToAirHeatPump    Air Outlet Node Name    FALSE    TRUE    FALSE    FALSE    FALSE    FALSE
ZoneHVAC:FourPipeFanCoil    Air Inlet Node Name    TRUE    FALSE    FALSE    FALSE    FALSE    FALSE
ZoneHVAC:FourPipeFanCoil    Air Outlet Node Name    FALSE    TRUE    FALSE    FALSE    FALSE    FALSE
ZoneHVAC:PackagedTerminalAirConditioner    Air Inlet Node Name    TRUE    FALSE    FALSE    FALSE    FALSE    FALSE
ZoneHVAC:PackagedTerminalAirConditioner    Air Outlet Node Name    FALSE    TRUE    FALSE    FALSE    FALSE    FALSE
ZoneHVAC:PackagedTerminalHeatPump    Air Inlet Node Name    TRUE    FALSE    FALSE    FALSE    FALSE    FALSE
ZoneHVAC:PackagedTerminalHeatPump    Air Outlet Node Name    FALSE    TRUE    FALSE    FALSE    FALSE    FALSE
ZoneHVAC:UnitHeater    Air Inlet Node Name    TRUE    FALSE    FALSE    FALSE    FALSE    FALSE
ZoneHVAC:UnitHeater    Air Outlet Node Name    FALSE    TRUE    FALSE    FALSE    FALSE    FALSE
ZoneHVAC:WindowAirConditioner    Air Inlet Node Name    TRUE    FALSE    FALSE    FALSE    FALSE    FALSE
ZoneHVAC:WindowAirConditioner    Air Outlet Node Name    FALSE    TRUE    FALSE    FALSE    FALSE    FALSE
ZoneHVAC:TerminalUnit:VariableRefrigerantFlow    Terminal Unit Air Inlet Node Name    TRUE    FALSE    FALSE    FALSE    FALSE    FALSE
ZoneHVAC:TerminalUnit:VariableRefrigerantFlow    Terminal Unit Air Outlet Node Name    FALSE    TRUE    FALSE    FALSE    FALSE    FALSE
ZoneHVAC:EvaporativeCoolerUnit    Outdoor Air Inlet Node Name    FALSE    FALSE    TRUE    FALSE    FALSE    FALSE
ZoneHVAC:EvaporativeCoolerUnit    Cooler Outlet Node Name    FALSE    TRUE    FALSE    FALSE    FALSE    FALSE
ZoneHVAC:EvaporativeCoolerUnit    Zone Relief Air Node Name    FALSE    FALSE    FALSE    TRUE    FALSE    FALSE
ZoneHVAC:OutdoorAirUnit    Outdoor Air Node Name    FALSE    FALSE    TRUE    FALSE    FALSE    FALSE
ZoneHVAC:OutdoorAirUnit    AirOutlet Node Name    FALSE    TRUE    FALSE    FALSE    FALSE    FALSE
ZoneHVAC:OutdoorAirUnit    AirInlet Node Name    FALSE    FALSE    FALSE    TRUE    FALSE    FALSE
ZoneHVAC:UnitVentilator    Air Inlet Node Name    FALSE    FALSE    FALSE    TRUE    FALSE    FALSE
ZoneHVAC:UnitVentilator    Air Outlet Node Name    FALSE    TRUE    FALSE    FALSE    FALSE    FALSE
ZoneHVAC:UnitVentilator    Outdoor Air Node Name    FALSE    FALSE    TRUE    FALSE    FALSE    FALSE
ZoneHVAC:IdealLoadsAirSystem    Zone Supply Air Node Name    FALSE    TRUE    FALSE    FALSE    FALSE    FALSE
ZoneHVAC:IdealLoadsAirSystem    Zone Exhaust Air Node Name    FALSE    FALSE    FALSE    TRUE    FALSE    FALSE
WaterHeater:HeatPump:PumpedCondenser    Air Inlet Node Name    FALSE    FALSE    FALSE    TRUE    FALSE    FALSE
WaterHeater:HeatPump:PumpedCondenser    Air Outlet Node Name    FALSE    TRUE    FALSE    FALSE    FALSE    FALSE
WaterHeater:HeatPump:PumpedCondenser    Outdoor Air Node Name    FALSE    FALSE    TRUE    FALSE    FALSE    FALSE
WaterHeater:HeatPump:PumpedCondenser    Tank Use Side Inlet Node Name    FALSE    FALSE    FALSE    FALSE    FALSE    FALSE
WaterHeater:HeatPump:PumpedCondenser    Tank Use Side Outlet Node Name    FALSE    FALSE    FALSE    FALSE    FALSE    FALSE
WaterHeater:HeatPump:WrappedCondenser    Air Inlet Node Name    FALSE    FALSE    FALSE    TRUE    FALSE    FALSE
WaterHeater:HeatPump:WrappedCondenser    Air Outlet Node Name    FALSE    TRUE    FALSE    FALSE    FALSE    FALSE
WaterHeater:HeatPump:WrappedCondenser    Outdoor Air Node Name    FALSE    FALSE    TRUE    FALSE    FALSE    FALSE
ZoneHVAC:VentilatedSlab    Outdoor Air Node Name    FALSE    FALSE    TRUE    FALSE    FALSE    FALSE
AirTerminal:DualDuct:ConstantVolume    Air Outlet Node Name    FALSE    TRUE    FALSE    FALSE    FALSE    FALSE
AirTerminal:DualDuct:ConstantVolume    Hot Air Inlet Node Name    TRUE    FALSE    FALSE    FALSE    FALSE    FALSE
AirTerminal:DualDuct:ConstantVolume    Cold Air Inlet Node Name    TRUE    FALSE    FALSE    FALSE    FALSE    FALSE
AirTerminal:DualDuct:VAV    Air Outlet Node Name    FALSE    TRUE    FALSE    FALSE    FALSE    FALSE
AirTerminal:DualDuct:VAV    Hot Air Inlet Node Name    TRUE    FALSE    FALSE    FALSE    FALSE    FALSE
AirTerminal:DualDuct:VAV    Cold Air Inlet Node Name    TRUE    FALSE    FALSE    FALSE    FALSE    FALSE
AirTerminal:SingleDuct:VAV:Reheat    Air Inlet Node Name    TRUE    FALSE    FALSE    FALSE    FALSE    FALSE
AirTerminal:SingleDuct:VAV:Reheat    Air Outlet Node Name    FALSE    TRUE    FALSE    FALSE    FALSE    FALSE
AirTerminal:SingleDuct:VAV:HeatAndCool:Reheat    Air Inlet Node Name    TRUE    FALSE    FALSE    FALSE    FALSE    FALSE
AirTerminal:SingleDuct:VAV:HeatAndCool:Reheat    Air Outlet Node Name    FALSE    TRUE    FALSE    FALSE    FALSE    FALSE
AirTerminal:SingleDuct:ConstantVolume:FourPipeInduction    Supply Air Inlet Node Name    TRUE    FALSE    FALSE    FALSE    FALSE    FALSE
AirTerminal:SingleDuct:ConstantVolume:FourPipeInduction    Supply Air Inlet Node Name    FALSE    FALSE    FALSE    FALSE    FALSE    TRUE
AirTerminal:SingleDuct:ConstantVolume:FourPipeInduction    Induced Air Inlet Node Name    FALSE    FALSE    FALSE    TRUE    FALSE    FALSE
AirTerminal:SingleDuct:ConstantVolume:FourPipeInduction    Air Outlet Node Name    FALSE    FALSE    FALSE    FALSE    FALSE    TRUE
AirTerminal:SingleDuct:ConstantVolume:FourPipeInduction    Air Outlet Node Name    FALSE    TRUE    FALSE    FALSE    FALSE    FALSE
AirTerminal:DualDuct:VAV:OutdoorAir    Air Outlet Node Name    FALSE    TRUE    FALSE    FALSE    FALSE    FALSE
AirTerminal:DualDuct:VAV:OutdoorAir    Outdoor Air Inlet Node Name    TRUE    FALSE    FALSE    FALSE    FALSE    FALSE
AirTerminal:SingleDuct:SeriesPIU:Reheat    Supply Air Inlet Node Name    TRUE    FALSE    FALSE    FALSE    FALSE    FALSE
AirTerminal:SingleDuct:SeriesPIU:Reheat    Supply Air Inlet Node Name    FALSE    FALSE    FALSE    FALSE    FALSE    TRUE
AirTerminal:SingleDuct:SeriesPIU:Reheat    Secondary Air Inlet Node Name    FALSE    FALSE    FALSE    TRUE    FALSE    FALSE
AirTerminal:SingleDuct:SeriesPIU:Reheat    Outlet Node Name    FALSE    TRUE    FALSE    FALSE    FALSE    FALSE
AirTerminal:SingleDuct:ParallelPIU:Reheat    Supply Air Inlet Node Name    TRUE    FALSE    FALSE    FALSE    FALSE    FALSE
AirTerminal:SingleDuct:ParallelPIU:Reheat    Supply Air Inlet Node Name    FALSE    FALSE    FALSE    FALSE    FALSE    TRUE
AirTerminal:SingleDuct:ParallelPIU:Reheat    Secondary Air Inlet Node Name    FALSE    FALSE    FALSE    TRUE    FALSE    FALSE
AirTerminal:SingleDuct:ParallelPIU:Reheat    Outlet Node Name    FALSE    TRUE    FALSE    FALSE    FALSE    FALSE
AirTerminal:SingleDuct:ParallelPIU:Reheat    Supply Air Inlet Node Name    TRUE    FALSE    FALSE    FALSE    FALSE    FALSE
AirTerminal:SingleDuct:ParallelPIU:Reheat    Supply Air Inlet Node Name    FALSE    FALSE    FALSE    FALSE    FALSE    TRUE
AirTerminal:SingleDuct:ParallelPIU:Reheat    Secondary Air Inlet Node Name    FALSE    FALSE    FALSE    TRUE    FALSE    FALSE
AirTerminal:SingleDuct:ParallelPIU:Reheat    Outlet Node Name    FALSE    TRUE    FALSE    FALSE    FALSE    FALSE
AirTerminal:SingleDuct:ConstantVolume:CooledBeam    Supply Air Inlet Node Name    TRUE    FALSE    FALSE    FALSE    FALSE    FALSE
AirTerminal:SingleDuct:ConstantVolume:CooledBeam    Supply Air Outlet Node Name    FALSE    TRUE    FALSE    FALSE    FALSE    FALSE
AirTerminal:SingleDuct:UserDefined    Primary Air Inlet Node Name    TRUE    FALSE    FALSE    FALSE    FALSE    FALSE
AirTerminal:SingleDuct:UserDefined    Primary Air Outlet Node Name    FALSE    TRUE    FALSE    FALSE    FALSE    FALSE
AirTerminal:SingleDuct:UserDefined    Secondary Air Inlet Node Name    TRUE    FALSE    FALSE    FALSE    FALSE    FALSE
AirTerminal:SingleDuct:UserDefined    Secondary Air Outlet Node Name    FALSE    TRUE    FALSE    FALSE    FALSE    FALSE""".split('\n')

data = [row.split('    ') for row in data]

mydict = defaultdict(dict)
for row in data:
#    print(row)
    for i, item in enumerate(row):
#        nodes = [headers[i] for i, item in enumerate(row) if item == 'TRUE']
        if item == 'TRUE':
            try:
                mydict[row[0].upper()][headers[i]].append(row[1])
            except KeyError:
                mydict[row[0].upper()][headers[i]] = [row[1]]
print(dict(mydict))

