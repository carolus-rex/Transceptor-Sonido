from threading import Thread
from time import sleep, strftime
import numpy as np
import pyaudio

import lame
import wave


__author__ = "Daniel"


class Guardador(Thread):
    def __init__(self, grabador):
        self.archivo_min_duration = 1
        self.grabador = grabador
        self.CHUNK = self.grabador.CHUNK
        self.formatM = pyaudio.paInt16 if 1 < self.grabador.format_in_bits<= 16 else pyaudio.paInt32
        self.channels = self.grabador.channels
        self.rate = self.grabador.rate
        self.archivo = None
        self.crear_nuevo_archivo()
        self.tamaño_chunk_ideal = 8192
        self.ruido_ambiente = 0.00028
        self._silencio = True
        self.archivo_name = None
        super(Guardador, self).__init__()
        self.start()

    def run(self):
        sound_pcm = b""
        sound_chunks = 0
        while True:
            if self.grabador.data_chunks:
                data = self.grabador.data_chunks.pop(0)
                if isinstance(data, bytes):
                    sound_pcm += data
                    sound_chunks += 1
                    if sound_chunks * self.CHUNK >= self.tamaño_chunk_ideal:
                        sound = self.bytes_to_nparray(sound_pcm)
                        rms = self.calcular_rms(sound)
                        #sound =  sound_pcm
                        print(rms)
                        if rms > self.ruido_ambiente:
                            if self._silencio:
                                self._silencio = False
                                #self.crear_nuevo_archivo()
                            self.archivo.writeframes(sound)
                        else:
                            if not self._silencio:
                                print("Grabación Terminada")
                                self._silencio = True
                                self.crear_nuevo_archivo()
                        sound_chunks = 0
                        sound_pcm = b""
                else:
                    for key, value in data.items():
                        if key == "rate":
                            self.rate = value
                        elif key == "channels":
                            self.channels = value
                        elif key == "format_in_bits":
                            self.formatM = value
                    sound_chunks = 0
                    sound_pcm = b""
                    self.crear_nuevo_archivo()
            else:
                sleep((1/self.grabador.rate) * self.grabador.CHUNK)

    def crear_nuevo_archivo(self):
        print("Crear nuevo archivo?")
        try:
            self.archivo.close()
            if self.archivo.getduration() < self.archivo_min_duration:
            #if self.archivo.getnframes()/self.archivo.getframerate() < self.archivo_min_duration:
                self.archivo = lame.open(self.archivo_name, "wb")
                print("No")
            else:
                self.archivo_name = strftime("%y-%m-%d--%H-%M-%S") + ".mp3"
                self.archivo = lame.open(self.archivo_name, "xb")
                #self.archivo = wave.open(self.archivo_name, "wb")
                print("Si " + self.archivo_name)
        except AttributeError:
            self.archivo_name = strftime("%y-%m-%d--%H-%M-%S") + ".mp3"
            self.archivo = lame.open(self.archivo_name, "xb")
            print("Si " + self.archivo_name)
        self.archivo.setframerate(self.rate)
        self.archivo.setsampwidth(self.grabador.p.get_sample_size(self.formatM) * 8)
        #self.archivo.setsampwidth(self.grabador.p.get_sample_size(self.formatM))
        self.archivo.setnchannels(self.channels)

    def bytes_to_nparray(self, data):
        if self.formatM == pyaudio.paInt16:
            nptype = np.int16
        elif self.formatM == pyaudio.paInt32:
            nptype = np.int32
        return np.frombuffer(data, dtype=nptype).reshape((-1, self.channels))

    def calcular_rms(self, sound):
        if self.formatM == pyaudio.paInt8:
            factor_normalizador = 128
        elif self.formatM == pyaudio.paInt16:
            factor_normalizador = 32768
        elif self.formatM == pyaudio.paInt24:
            factor_normalizador = 8388608
            raise NotImplementedError("Numpy no soporta formato de 24 bits/3 bytes")
        elif self.formatM == pyaudio.paInt32:
            factor_normalizador = 2147483648
        return np.sqrt(np.sum((sound / factor_normalizador) ** 2) / len(sound))


class Grabador(object):
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.CHUNK = 1024
        self.format_in_bits = 16
        self.channels = 2
        self.rate = 48000
        self.parlantes = self.p.get_default_input_device_info()["index"]
        self.fuente = self.p.get_default_output_device_info()["index"]
        self.stream = None
        self.crear_stream()
        self.data_chunks = []
        self.guardar = False
        self.cambios = {}
        self.guardador = Guardador(self)

    def get_inputs(self):
        values = []
        index = 0
        try:
            while True:
                device = self.p.get_device_info_by_index(index)
                if device["maxInputChannels"] > 0:
                    values.append(device["name"])
                    print(device["index"])
                index += 1
        except OSError:
            return values

    def get_outputs(self):
        values = []
        index = 0
        try:
            while True:
                device = self.p.get_device_info_by_index(index)
                if device["maxOutputChannels"] > 0:
                    values.append(device["name"])
                    print(device["index"])
                index += 1
        except OSError:
            return values

    def iniciar(self):
        while True:
            sonido = self.stream.read(self.CHUNK)
            if self.format_in_bits not in (16, 24):
                sonido = self.simular_formato(sonido)
            self.stream.write(sonido)
            if self.guardar:
                self.data_chunks.append(sonido)
            if self.cambios:
                tx_cambios = {}
                for key, value in self.cambios.items():
                    if key == "output":
                        self.parlantes = value
                    elif key == "input":
                        self.fuente = value
                    elif key == "rate":
                        self.rate = value
                        tx_cambios[key] = value
                    elif key == "channels":
                        self.channels = value
                        tx_cambios[key] = value
                    elif key == "format_in_bits":
                        self.format_in_bits = value
                        tx_cambios[key] = pyaudio.paInt16 if 1 < value <= 16 else pyaudio.paInt32
                self.cambios.clear()
                self.stream.close()
                self.crear_stream()
                if tx_cambios:
                    self.data_chunks.append(tx_cambios)
            #sleep(self.CHUNK * (1/self.rate))

    def crear_stream(self):
        #self.stream.close()
        if 1 < self.format_in_bits <= 16:
            pyaudio_format = pyaudio.paInt16
        else:
            pyaudio_format = pyaudio.paInt32
        self.stream = self.p.open(rate=self.rate,
                                  channels=self.channels,
                                  format=pyaudio_format,
                                  input=True,
                                  output=True,
                                  input_device_index=self.parlantes,
                                  output_device_index=self.fuente)

    def simular_formato(self, sound):
        if 1 < self.format_in_bits <= 16:
            nptype = np.int16
            factor_normalizador = 32768
        else:
            nptype = np.int32
            factor_normalizador = 2147483648
        factor_escalador = 1 << (self.format_in_bits - 1)
        arr_sound = np.frombuffer(sound, dtype=nptype).reshape((-1, self.channels))
        data = (((((arr_sound / factor_normalizador) * factor_escalador) // 1) / factor_escalador) * factor_normalizador).astype(nptype, copy=False)
        return data.tobytes()


if __name__ == "__main__":
    Grabador().iniciar()
