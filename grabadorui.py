from _ctypes import POINTER
from ctypes import cast
from threading import Thread

import comtypes
import kivy
from kivy.uix.label import Label
from pycaw.pycaw import AudioUtilities, CLSID_MMDeviceEnumerator, IMMDeviceEnumerator, IAudioEndpointVolume
from grabador import Grabador

kivy.require("1.9.0")

from kivy.app import App

from kivy.uix.boxlayout import BoxLayout
from widgetsbasicos import Etiqueta
from widgetsbasicos import DatosInput
from widgetsbasicos import GridLayoutAdaptivo

from kivy.lang import Builder

from pynput.keyboard import Listener

__author__ = "Daniel"


Builder.load_file("grabadorui.kv")

class GrabadorUi(BoxLayout):
    def __init__(self, **kwargs):
        self.volume = None
        self.find_volume_controller()

        self.grabador = Grabador()
        Thread(target=self.grabador.iniciar).start()

        self.key_listener = Listener(on_press=self.listen_volume_keys)
        self.key_listener.start()

        super(GrabadorUi, self).__init__(**kwargs)
        self.ids.inputs.text = self.grabador.p.get_default_input_device_info()["name"]
        self.ids.inputs.values = self.grabador.get_inputs()

        self.ids.outputs.text = self.grabador.p.get_default_output_device_info()["name"]
        self.ids.outputs.values = self.grabador.get_outputs()

    def listen_volume_keys(self, key):
        mute_key = "<173>"
        less_key = "<174>"
        more_key = "<175>"
        if str(key) == mute_key:
            self.volume.SetMute(self.volume.GetMute()^1, None)
        elif str(key) == less_key:
            if self.volume.GetMute():
                self.volume.SetMute(0, None)
            self.volume.VolumeStepDown(None)
        elif str(key) == more_key:
            if self.volume.GetMute():
                self.volume.SetMute(0, None)
            self.volume.VolumeStepUp(None)

    def find_volume_controller(self):
        for device in AudioUtilities.GetAllDevices():
            print(device)
            if device.FriendlyName == "Altavoz/Auricular (Realtek High Definition Audio)":
            #if device.FriendlyName == "CABLE Input (VB-Audio Virtual Cable)":
                deviceEnumerator = comtypes.CoCreateInstance(
                    CLSID_MMDeviceEnumerator,
                    IMMDeviceEnumerator,
                    comtypes.CLSCTX_INPROC_SERVER)
                speakers = deviceEnumerator.GetDevice(
                            device.id)
                devices = speakers
        interface = devices.Activate(
            IAudioEndpointVolume._iid_, comtypes.CLSCTX_ALL, None)
        self.volume = cast(interface, POINTER(IAudioEndpointVolume))

    def search_device(self, name):
        index = 0
        try:
            while True:
                device = self.grabador.p.get_device_info_by_index(index)
                if device["name"] == name:
                    return device["index"]
                index += 1
        except OSError:
            print("esto no debería ocurrir")

    def change_input(self, wid, name):
        device = self.search_device(name)
        self.grabador.cambios["input"] = device

    def change_output(self, wid, name):
        device = self.search_device(name)
        self.grabador.cambios["output"] = device

    def toggle_grabar(self, wid, state):
        if state == "normal":
            self.grabador.guardar = False
        elif state == "down":
            self.grabador.guardar = True

    def change_rate(self, wid, rate):
        if len(rate) > 3 and (int(rate) != 0):
            self.grabador.cambios["rate"] = int(rate)

    def change_channels(self, wid, channels):
        if len(channels) == 1:
            self.grabador.cambios["channels"] = int(channels)

    def change_format(self, wid, format_in_bits):
        if 1 <= len(format_in_bits) <= 2:
            self.grabador.cambios["format_in_bits"] = int(format_in_bits)


class MiClaseApp(App):
    def build(self):
        return GrabadorUi()


if __name__ == "__main__":
    MiClaseApp().run()