# coding=utf-8
from __future__ import print_function
import re
import kivy
from kivy.uix.image import Image
from kivy.uix import gridlayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget

kivy.require('1.9.0')

from kivy.clock import Clock
from kivy.properties import BooleanProperty, NumericProperty, StringProperty, ListProperty, ObjectProperty
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.animation import Animation
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.uix.scrollview import ScrollView
from kivy.uix.behaviors import ButtonBehavior

__author__ = 'Daniel'

"""Aquí debería de hacer que el builder cargue estilos.kv,
sin embargo funciona sin colocarlo :S"""

color_1 = (232 / 255.0, 215 / 255.0, 162 / 255.0, 1)
color_texto = (230 / 255.0, 32 / 255.0, 136 / 255.0, 1)

try:
    Builder.load_file("util/widgetsbasicos.kv")
except IOError:
    Builder.load_file("widgetsbasicos.kv")


class Boton(Button):
    pass


class Etiqueta(Label):
    fondo = ListProperty(color_1)
    fondo_pos = ListProperty((0, 0))
    fondo_size = ListProperty((0, 0))

    """def __init__(self, **kwargs):
        super(Etiqueta, self).__init__(**kwargs)
        self.fondo_pos """


class EtiquetaMensaje(Etiqueta):
    RED = 1, 0, 0, 1
    GREEN = 0, 1, 0, 1

    def aceptar(self, mensaje):
        self.color = self.GREEN
        self.text = mensaje

    def rechazar(self, mensaje):
        self.color = self.RED
        self.text = mensaje

    def vaciar(self):
        self.text = ""


class DatosInput(TextInput):
    # [TODO] Modificar método insert_text para que no deje introducir caracteres inválidos o hacer que lo haga la consulta a la base de datos
    pass
    """def on_hint_text(self, instance, value):
        if not isinstance(self.hint_text, unicode):
            caca = self.hint_text.decode("utf-8")
            self.hint_text = caca # Necesario para que el hint_text muestre caracteres unicode
        else:
            super(DatosInput, self).on_hint_text(instance, value)"""


class ExaminarInput(DatosInput):
    """TextInput modificado para verificar si el texto ha sido modificado en un
    periodo de tiempo determinado por tiempo_analisis.

    Cuando el texto es modificado, texto_aceptado permanece en False.
    Cuando el texto no es modificado, texto_aceptado se hace True"""

    # [TODO] ver si puedo hacer que se lanzen eventos por separado cuando el texto sea aceptado o modificado

    texto_aceptado = BooleanProperty(False)
    tiempo_analisis = NumericProperty(2)

    def __init__(self, **kwargs):
        super(ExaminarInput, self).__init__(**kwargs)
        self.clock_analizar = Clock.schedule_once(self.analizar_cambio, self.tiempo_analisis)
        # [TODO] Investigar por qué esto no funciona
        # self.clock_detener_analisis = Clock.unschedule(self.analizar_cambio)

    def clock_detener_analisis(self):
        Clock.unschedule(self.analizar_cambio)

    def on_text(self, *args):
        self.clock_detener_analisis()
        self.texto_aceptado = False
        if self.text:
            self.clock_analizar()

    def analizar_cambio(self, *args):
        if self.text:
            self.texto_aceptado = True

    def on_texto_aceptado(self, *args):
        pass

    def on_tiempo_analisis(self, *args):
        self.clock_analizar = Clock.schedule_once(self.analizar_cambio, self.tiempo_analisis)

    '''def keyboard_on_key_down(self, window, keycode, text, modifiers):
        print window, keycode, text, modifiers, 'keyboard on key down'
        super(ExaminarInput, self).keyboard_on_key_down(window, keycode, text, modifiers)
        
    def keyboard_on_key_up(self, window, keycode):
        print window, keycode, 'keyboard on key up'
        super(ExaminarInput, self).keyboard_on_key_up(window, keycode)
        
    def keyboard_on_textinput(self, window, text):
        print window, text, 'keyboard on text input'
        super(ExaminarInput, self).keyboard_on_textinput(window, text)'''


class GridLayoutAdaptivo(GridLayout):
    def __init__(self, **kwargs):
        super(GridLayoutAdaptivo, self).__init__(**kwargs)
        self.bind(minimum_height=self.setter("height"))


class NotificarInput(GridLayoutAdaptivo):
    tipo = StringProperty('comun')
    caracteres_incorrectos = BooleanProperty(False)
    hay_contenido = StringProperty('')
    texto_aceptado = BooleanProperty(False)

    tiempo_analisis = NumericProperty(1)

    password = BooleanProperty(False)
    use_bubble = BooleanProperty(False)
    allow_copy = BooleanProperty(False)

    checkeo_tiempo = BooleanProperty(True)
    valido = BooleanProperty(False)

    hint_text = StringProperty("")
    longitud_max = NumericProperty(32, allownone=True)
    input_filter = ObjectProperty(None, allownone=True)

    """
    texto_aceptado si es True, el usuario a aceptado 'evaluar' el input.
    valido si es True, el programa (servidor actualmente) reconoce el input del usuario como
    un dato valido."""

    def notificar(self, mensaje, aceptar):
        if aceptar:
            self.ids.etiqueta.aceptar(mensaje)
        else:
            self.ids.etiqueta.rechazar(mensaje)

    def quitar_notificacion(self):
        self.ids.etiqueta.vaciar()

    def on_textinput_text(self):
        if self.checkeo_tiempo:
            self.valido = False
        if self.ids.input.text:
            self.hay_contenido = 'Si'
        else:
            self.hay_contenido = 'No'

        uTexto = self.ids.input.text.decode("utf8")

        if self.tipo == 'username':
            uUsername = uTexto
            if len(uUsername) > 32:
                uUsername = uUsername[0:32]
                self.ids.input.text = uUsername.encode("utf8")
            """if re.match(r'[\w]*$', uUsername):
                self.caracteres_incorrectos = False
                self.quitar_notificacion()
            else:
                self.caracteres_incorrectos = True
                self.notificar("Utiliza solo letras, números y guiones bajos", False)"""
        elif self.longitud_max is not None:
            if len(uTexto) > self.longitud_max:
                self.ids.input.text = uTexto[0:self.longitud_max].encode("utf8")

    def on_textinput_focus(self):
        """Se encarga de mostrar el mensaje de vacío"""
        if not self.ids.input.focus and not self.ids.input.text:  # si pierdo focus y estoy vacio
            self.notificar_vacio()
            return
        if self.ids.input.focus and self.hay_contenido == "No":  # si gano focus y estoy vacio
            self.quitar_notificacion()
            return

    def notificar_vacio(self):
        self.notificar('No puede dejar este campo vacío', False)

    def on_texto_aceptado(self, *args):
        pass


# [TODO] Hacer que la prueba del ExaminarInput funcione


class VistaScroll(ScrollView):
    gspacing = NumericProperty()
    gpadding = NumericProperty()
    color_fondo = ListProperty(color_1)

    def __init__(self, **kwargs):
        super(VistaScroll, self).__init__(**kwargs)
        Clock.schedule_once(self._activar_scroll)

    def _activar_scroll(self, *args):
        """Función creada para activar el scrolling. Es nesesaria porque la ID del layout se inicia
        después del init"""
        self.ids.layout.bind(minimum_height=self.ids.layout.setter("height"))

    def add_cuadro(self, cuadro):
        self.ids.layout.add_widget(cuadro)

    def add_widget(self, widget, index=0):
        try:
            self.ids.layout  # Si no tira error, entonces existe y usamos el metodo sobreescrito
            self.add_cuadro(widget)
        except AttributeError:
            super(VistaScroll, self).add_widget(widget)

    def borrar_cuadros(self):
        self.ids.layout.clear_widgets()

    def remover(self, widget):
        self.ids.layout.remove_widget(widget)

    def scroll_to(self, widget, padding=10, animate=True):
        """Sacado directamente del código fuente de kivy 1.9.1-dev:

        Scrolls the viewport to ensure that the given widget is visible,
        optionally with padding and animation. If animate is True (the
        default), then the default animation parameters will be used.
        Otherwise, it should be a dict containing arguments to pass to
        :class:`~kivy.animation.Animation` constructor.

        .. versionadded:: 1.9.1
        """

        if not self.parent:
            return

        if isinstance(padding, (int, float)):
            padding = (padding, padding)

        pos = self.parent.to_widget(*widget.to_window(*widget.pos))
        cor = self.parent.to_widget(*widget.to_window(widget.right,
                                                      widget.top))

        dx = dy = 0

        if pos[1] < self.y:
            dy = self.y - pos[1] + dp(padding[1])
        elif cor[1] > self.top:
            dy = self.top - cor[1] - dp(padding[1])

        if pos[0] < self.x:
            dx = self.x - pos[0] + dp(padding[0])
        elif cor[0] > self.right:
            dx = self.right - cor[0] - dp(padding[0])

        dsx, dsy = self.convert_distance_to_scroll(dx, dy)
        sxp = min(1, max(0, self.scroll_x - dsx))
        syp = min(1, max(0, self.scroll_y - dsy))

        if animate:
            if animate is True:
                animate = {'d': 0.2, 't': 'out_quad'}
            Animation.stop_all(self, 'scroll_x', 'scroll_y')
            Animation(scroll_x=sxp, scroll_y=syp, **animate).start(self)
        else:
            self.scroll_x = sxp
            self.scroll_y = syp

    def on_gspacing(self, *args):
        self.ids.layout.spacing = self.gspacing

    def on_gpadding(self, *args):
        self.ids.layout.padding = self.gpadding


class EtiquetaPopup(Label):
    pass


class Emergente(Popup):
    def __init__(self, titulo, texto, **kwargs):
        super(Emergente, self).__init__(title=titulo,
                                        content=EtiquetaPopup(text=texto),
                                        size_hint=(None, None),
                                        size=(200, 200),
                                        **kwargs)


class PreguntaEmergente(Popup):
    def __init__(self, titulo, texto, funcion_positiva=None, funcion_negativa=None, **kwargs):
        self.layout = BoxLayout(orientation="vertical")
        self.layout.add_widget(EtiquetaPopup(text=texto,size_hint_y=1))

        boton_si = (Button(text=u"Sí"))
        boton_si.bind(on_press=lambda arg: self.dismiss())
        if funcion_positiva is not None:
            boton_si.bind(on_press=lambda arg :funcion_positiva()) #El lambda quita el argumento extra que agrega el bind

        boton_no = (Button(text="No"))
        boton_no.bind(on_press=lambda arg: self.dismiss())
        if funcion_negativa is not None:
            boton_no.bind(on_press=lambda arg :funcion_negativa())

        botones = BoxLayout(orientation="horizontal", size_hint_y=None, height=50)
        botones.add_widget(boton_si)
        botones.add_widget(boton_no)

        self.layout.add_widget(botones)

        super(PreguntaEmergente, self).__init__(title=titulo,
                                                content=self.layout,
                                                size_hint=(None, None),
                                                size=(200, 200),
                                                **kwargs)


class Espacio(Widget):
    px = NumericProperty(5)


if __name__ == "__main__":
    from kivy.base import runTouchApp
    from kivy.uix.boxlayout import BoxLayout


    def imprimir_respuesta():
        print("aca")


    layout = BoxLayout()
    layout.add_widget(Etiqueta(text="Etiqueta"))
    layout.add_widget(DatosInput())
    boton = Boton(text="Boton")
    boton.bind(on_press=Emergente("Probando", "Esto es una prueba e.e").open)
    layout.add_widget(boton)
    examinar_texto = ExaminarInput()
    examinar_texto.bind(on_texto_aceptado=imprimir_respuesta)
    layout.add_widget(examinar_texto)
    runTouchApp(layout)
