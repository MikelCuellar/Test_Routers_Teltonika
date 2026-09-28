"""Base de conocimiento de capacidades de hardware por modelo Teltonika Networks."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class HardwareProfile:
    model: str
    family: str                          # RUT_COMPACT, RUT_ADVANCED, RUTX, TRB
    sim_slots: int = 1
    has_dual_sim_switch: bool = False
    ethernet_ports_count: int = 2
    ethernet_port_names: List[str] = field(default_factory=lambda: ["LAN", "WAN"])
    has_wifi: bool = False
    wifi_bands: List[str] = field(default_factory=list) # ["2.4GHz"] o ["2.4GHz", "5GHz"]
    has_gps: bool = False
    has_rs232: bool = False
    has_rs485: bool = False
    has_relay: bool = False
    digital_inputs_count: int = 1
    digital_outputs_count: int = 1
    has_analog_input: bool = False
    has_microsd: bool = False
    has_usb_storage: bool = False


# Catálogo oficial de especificaciones de hardware
CATALOG: Dict[str, HardwareProfile] = {
    # Serie Compacta
    "RUT240": HardwareProfile(
        model="RUT240",
        family="RUT_COMPACT",
        sim_slots=1,
        has_dual_sim_switch=False,
        ethernet_ports_count=2,
        ethernet_port_names=["LAN", "WAN"],
        has_wifi=True,
        wifi_bands=["2.4GHz"],
        has_gps=False,
        digital_inputs_count=1,
        digital_outputs_count=1,
    ),
    "RUT241": HardwareProfile(
        model="RUT241",
        family="RUT_COMPACT",
        sim_slots=1,
        has_dual_sim_switch=False,
        ethernet_ports_count=2,
        ethernet_port_names=["LAN", "WAN"],
        has_wifi=True,
        wifi_bands=["2.4GHz"],
        has_gps=False,
        digital_inputs_count=1,
        digital_outputs_count=1,
    ),
    "RUT200": HardwareProfile(
        model="RUT200",
        family="RUT_COMPACT",
        sim_slots=1,
        has_dual_sim_switch=False,
        ethernet_ports_count=2,
        ethernet_port_names=["LAN", "WAN"],
        has_wifi=True,
        wifi_bands=["2.4GHz"],
        has_gps=False,
        digital_inputs_count=1,
        digital_outputs_count=1,
    ),

    # Serie Industrial Avanzada
    "RUT950": HardwareProfile(
        model="RUT950",
        family="RUT_ADVANCED",
        sim_slots=2,
        has_dual_sim_switch=True,
        ethernet_ports_count=4,
        ethernet_port_names=["LAN1", "LAN2", "LAN3", "WAN"],
        has_wifi=True,
        wifi_bands=["2.4GHz"],
        has_gps=False,
        digital_inputs_count=1,
        digital_outputs_count=1,
    ),
    "RUT951": HardwareProfile(
        model="RUT951",
        family="RUT_ADVANCED",
        sim_slots=2,
        has_dual_sim_switch=True,
        ethernet_ports_count=4,
        ethernet_port_names=["LAN1", "LAN2", "LAN3", "WAN"],
        has_wifi=True,
        wifi_bands=["2.4GHz"],
        has_gps=False,
        digital_inputs_count=1,
        digital_outputs_count=1,
    ),
    "RUT955": HardwareProfile(
        model="RUT955",
        family="RUT_ADVANCED",
        sim_slots=2,
        has_dual_sim_switch=True,
        ethernet_ports_count=4,
        ethernet_port_names=["LAN1", "LAN2", "LAN3", "WAN"],
        has_wifi=True,
        wifi_bands=["2.4GHz"],
        has_gps=True,
        has_rs232=True,
        has_rs485=True,
        has_relay=True,
        digital_inputs_count=2,
        digital_outputs_count=2,
        has_analog_input=True,
        has_microsd=True,
        has_usb_storage=True,
    ),
    "RUT956": HardwareProfile(
        model="RUT956",
        family="RUT_ADVANCED",
        sim_slots=2,
        has_dual_sim_switch=True,
        ethernet_ports_count=4,
        ethernet_port_names=["LAN1", "LAN2", "LAN3", "WAN"],
        has_wifi=True,
        wifi_bands=["2.4GHz"],
        has_gps=True,
        has_rs232=True,
        has_rs485=True,
        has_relay=True,
        digital_inputs_count=2,
        digital_outputs_count=2,
        has_analog_input=True,
        has_microsd=True,
        has_usb_storage=True,
    ),

    # Serie RUTX Gigabit / Alta Velocidad
    "RUTX09": HardwareProfile(
        model="RUTX09",
        family="RUTX",
        sim_slots=2,
        has_dual_sim_switch=True,
        ethernet_ports_count=4,
        ethernet_port_names=["LAN1 (GbE)", "LAN2 (GbE)", "LAN3 (GbE)", "WAN (GbE)"],
        has_wifi=False,
        has_gps=True,
        digital_inputs_count=1,
        digital_outputs_count=1,
        has_usb_storage=True,
    ),
    "RUTX11": HardwareProfile(
        model="RUTX11",
        family="RUTX",
        sim_slots=2,
        has_dual_sim_switch=True,
        ethernet_ports_count=4,
        ethernet_port_names=["LAN1 (GbE)", "LAN2 (GbE)", "LAN3 (GbE)", "WAN (GbE)"],
        has_wifi=True,
        wifi_bands=["2.4GHz", "5GHz"],
        has_gps=True,
        digital_inputs_count=1,
        digital_outputs_count=1,
        has_usb_storage=True,
    ),
    "RUTX50": HardwareProfile(
        model="RUTX50",
        family="RUTX",
        sim_slots=2,
        has_dual_sim_switch=True,
        ethernet_ports_count=5,
        ethernet_port_names=["LAN1 (GbE)", "LAN2 (GbE)", "LAN3 (GbE)", "LAN4 (GbE)", "WAN (GbE)"],
        has_wifi=True,
        wifi_bands=["2.4GHz", "5GHz"],
        has_gps=True,
        digital_inputs_count=1,
        digital_outputs_count=1,
        has_usb_storage=True,
    ),

    # Gateways Industriales TRB
    "TRB140": HardwareProfile(
        model="TRB140",
        family="TRB",
        sim_slots=1,
        ethernet_ports_count=1,
        ethernet_port_names=["LAN (GbE)"],
        has_wifi=False,
        has_gps=False,
        digital_inputs_count=1,
        digital_outputs_count=1,
    ),
    "TRB245": HardwareProfile(
        model="TRB245",
        family="TRB",
        sim_slots=2,
        has_dual_sim_switch=True,
        ethernet_ports_count=1,
        ethernet_port_names=["LAN"],
        has_wifi=False,
        has_gps=True,
        has_rs232=True,
        has_rs485=True,
        digital_inputs_count=2,
        digital_outputs_count=2,
        has_analog_input=True,
    ),
}


def resolve_profile(model_str: str) -> HardwareProfile:
    """Resuelve el perfil de capacidades a partir del nombre del modelo o código de producto."""
    clean = model_str.upper().strip()
    for key, profile in CATALOG.items():
        if key in clean:
            return profile

    # Fallback genérico si no coincide exactamente
    return HardwareProfile(
        model=model_str,
        family="GENERIC_TELTONIKA",
        sim_slots=1,
        ethernet_ports_count=2,
        ethernet_port_names=["LAN", "WAN"],
        has_wifi=True,
        wifi_bands=["2.4GHz"],
        has_gps=False,
    )
