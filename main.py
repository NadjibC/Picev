"""
Simple Google's Material Design Photo Viewer
"""

import glob
import optparse
import os
import sys

import kivy
kivy.require('1.10.1')

from Xlib import display
from kivy import Logger
from kivy.animation import Animation, AnimationTransition
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.carousel import Carousel
from kivy.uix.image import Image
from kivy.uix.scatterlayout import ScatterLayout
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex
from kivymd.app import MDApp
from kivymd.uix.button import MDIconButton
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.imagelist import SmartTileWithLabel as SmartTile
from kivymd.uix.label import MDLabel

__all__ = ('Spacer', 'App', 'app', '__app__', '__version__')
__app__ = 'PICEV'
__version__ = '0.2'

if '-v' in sys.argv or '--version' in sys.argv:
    print(__app__ + " : " + __version__)
    sys.exit()


class Spacer(Widget):
    """
    Spacer Used In bottom Bar
    """
    size_hint = (1, 1)


class App(MDApp):
    """
    Main App Class
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.props = {
            'loading': None,
            'notify': True,
            'tile_toggled': None,
            'tiles': [],
            'transition': AnimationTransition.out_quad,
            'transition_str': 'out_quad',
            'bar_toggled': None,
            'keep_bar_shown': None,
            'cursor_leaved': None
        }

        self.image = None

        self.icon = os.path.split(os.path.realpath(sys.argv[0]))[0] + f'/logo-{__app__.lower()}.png'
        self.title = __app__

        self.loading_screen = Screen(name='loading_screen')

        self.global_screen = Screen()
        self.screen_mgr = ScreenManager()
        self.global_screen.add_widget(self.screen_mgr)

        self.base_view = ScatterLayout()
        self.old_win_size = Window.size
        self.up_popup = MDGridLayout(cols=0, size_hint=(1, None))
        self.up_popup.md_bg_color = self.theme_cls.primary_color
        self.up_popup.pos = (self.up_popup.pos[0], Window.size[1])
        self.up_popup.size = (self.up_popup.size[0], 100)
        self.supported_images = ['*.png', '*.jp*g', '*.bpm', '*.ico', '*.gif', '*.xcf']
        self.current_image = 0
        self.image_list = []
        self.bar_toggled = True
        self.old_size = None
        self.base_image = None
        self.enable_carousel = None
        self.carousel = Carousel(anim_type=self.props['transition_str'])
        self.carousel.bind(current_slide=self.refresh_slide)
        self.file_manager = MDFileManager(ext=['.png', '.jpeg', '.bpm', '.ico', '.gif', '.xcf'])

        Window.bind(on_keyboard=self.on_keyboard)
        # Window.bind(size=self.on_resize)
        Window.bind(on_cursor_leave=lambda dt: self.props.update({'cursor_leaved': True}))
        Window.bind(on_cursor_enter=lambda dt: self.props.update({'cursor_leaved': False}))

        self.anim_duration = 0.2

        self.parser = optparse.OptionParser()
        self.parser.add_option('-i', '--image', help='Show directly specified Image')
        self.parser.add_option('-n', '--carousel', help='Disable Carousel Mode')
        self.parser.add_option('-p', '--preload', help='Switch to simple view then carousel view')
        self.shell_args = self.parser.parse_args()[0]

        self.enable_carousel = self.shell_args.carousel

        if self.enable_carousel:
            self.enable_carousel = int(self.enable_carousel)

        self.view_screen = Screen(name='view_screen')

        self.screen_mgr.add_widget(self.view_screen)
        self.screen_mgr.add_widget(self.loading_screen)

        self.bar_popup = MDGridLayout(rows=1, cols=9)
        self.bar_popup.md_bg_color = self.theme_cls.primary_color
        self.bar_popup.size_hint_y = None
        self.bar_popup.size = (self.bar_popup.size[0], 50)

        open_file = MDIconButton(icon="folder-open", on_release=self.choose_dir)
        self.fullscreen_button = MDIconButton(icon="fullscreen", on_release=self.toggle_fullscreen)
        before_button = MDIconButton(icon="arrow-left", on_release=self.select_before_image)
        after_button = MDIconButton(icon="arrow-right", on_release=self.select_after_image)
        self.carousel_button = MDIconButton(icon="view-carousel", on_release=self.toggle_carousel)
        reset_scale = MDIconButton(icon="lock-reset", on_release=self.reset_scale)
        edit_screen = MDIconButton(icon='draw')

        self.bar_popup.add_widget(Spacer())
        self.bar_popup.add_widget(open_file)
        self.bar_popup.add_widget(self.fullscreen_button)
        self.bar_popup.add_widget(before_button)
        self.bar_popup.add_widget(after_button)
        self.bar_popup.add_widget(self.carousel_button)
        self.bar_popup.add_widget(reset_scale)
        self.bar_popup.add_widget(Spacer())
        self.bar_popup.add_widget(edit_screen)

        self.mini_screen = Screen(name='mini_screen')
        self.mini_screen.add_widget(self.base_view)

        self.view_screen.add_widget(self.mini_screen)
        self.view_screen.add_widget(self.bar_popup)
        self.view_screen.add_widget(self.up_popup)

        if self.enable_carousel:
            self.make_carousel()
        else:
            self.make_simple_view()

        if self.shell_args.image:
            self.set_base_image(self.shell_args.image)

        self.refresh_look()

        clock = Clock.schedule_interval(self.refresh, 0.1)
        del clock

    def get_screen_size(self):
        Display = display.Display().screen()
        width = Display['width_in_pixels']
        height = Display['height_in_pixels']

        return (width, height)

    def on_keyboard(self, window=None, key=None, scancode=None, codepoint=None, modifier=None):
        """
        Special Keyboard Events for __app__

        Args:
            window (_type_, optional): window that called function. Defaults to None.
            key (_type_, optional): Defaults to None.
            scancode (_type_, optional): Defaults to None.
            codepoint (_type_, optional): Defaults to None.
            modifier (_type_, optional): Defaults to None.
        """

        if scancode == 80:
            self.select_before_image()
        elif scancode == 79:
            self.select_after_image()

        del window
        del key
        del scancode
        del codepoint
        del modifier

    def reset_scale(self, caller=None):
        """Reset self.base_view (ScatterLayout) To Default

        Args:
            caller (_type_, optional): caller of the function. Defaults to None.
        """

        self.base_view.scale = 1.0
        self.base_view.rotation = 0
        self.base_view.pos = (0, 0)

        self.make_caption('View Reseted')

        del caller

    def make_caption(self, text, duration=1):
        """Floating Fade-in & Fade-out text

        Args:
            text (_type_): _description_
            duration (int, optional): _description_. Defaults to 1.
        """

        if self.props['notify']:
            caption = MDLabel(text=text,
                              opacity=0,
                              halign='center',
                              font_style='H2')

            caption.color = get_color_from_hex("#FFFFFF")

            animation = Animation(opacity=1, duration=duration)
            animation += Animation(opacity=0, duration=duration)
            animation.on_complete = lambda widget=caption: self.view_screen.remove_widget(widget)

            self.global_screen.add_widget(caption)

            animation.start(caption)
    
    @staticmethod
    def glob(root_dir, pathname):
        pwd = os.getcwd()

        os.chdir(root_dir)

        ls = glob.glob(pathname)
        
        os.chdir(pwd)
		
        return ls

    def get_img_list(self, directory=None):
        """
        Get Image List (ls like)

        Args:
            dir (_type_, optional): _description_. Defaults to None.
        """

        if not directory:
            if os.path.isdir(directory):
                os.chdir(directory)
            directory = '.'

        self.image_list = []

        for supported_image in self.supported_images:
            self.image_list += self.glob(root_dir=directory, pathname=supported_image)

        self.image_list.sort()

        if self.image_list:
            self.props['bar_toggled'] = True
            self.hide_bar()
            if not self.base_image:
                self.base_image = self.image_list[0]

        self.make_tile()

    def set_from_tile(self, tile):
        """
        Function That Select Image and show it to the widget

        Args:
            tile (SmartTile): _description_
        """
        if self.carousel.slides:
            self.carousel.load_slide(self.carousel.slides[self.props['tiles'].index(tile)])

        if self.enable_carousel:
            self.current_image = self.props['tiles'].index(tile)
            self.set_base_image(self.image_list[self.props['tiles'].index(tile)])
        elif not self.enable_carousel:
            self.current_image = self.image_list.index(os.path.split(tile.source)[1])
            self.set_base_image(os.path.split(tile.source)[1])

    def _make_tile(self, dt=None):
        """
        Create Group of SmartTile Classes from self.image_list
        """

        self.up_popup.clear_widgets()
        self.props['tiles'].clear()

        for image in self.image_list:
            self.up_popup.cols += 1
            tile = SmartTile(source=os.path.realpath(image),
                             size_hint=(0.2, 1),
                             on_release=self.set_from_tile)

            tile.text = os.path.split(image)[1].title()
            tile.font_style = 'Caption'  # Must be one of:
            # ['H1', 'H2', 'H3', 'H4', 'H5',
            # 'H6', 'Subtitle1', 'Subtitle2',
            # 'Body1', 'Body2', 'Button',
            # 'Caption', 'Overline', 'Icon']

            self.props['tiles'].append(tile)
            self.up_popup.add_widget(tile)
            
    def make_tile(self):
        Clock.schedule_once(self._make_tile)

    def toggle_carousel(self, caller=None):
        """
        Switch to simple view if the current view is carousel,
        Or switch to carousel if the current view is simple view
        """

        if self.enable_carousel:
            self.switch_to_simple_view()
        else:
            self.switch_to_carousel()

        del caller

    def select_before_image(self, caller=None):
        """
        Switch To Previous Image
        """

        if (self.current_image - 1) > -1:
            if self.enable_carousel:
                if (self.current_image - 1) > len(self.image_list):
                    self.current_image -= 1
                self.image.load_previous()
            else:
                if self.image_list:
                    self.current_image -= 1
                    self.set_base_image(self.image_list[self.current_image])

        del caller

    def select_after_image(self, caller=None):
        """
        Switch To Next Image
        """

        if self.enable_carousel:
            if (self.current_image + 1) < len(self.image_list):
                self.current_image += 1
            self.image.load_next(mode='next')
        else:
            if self.image_list:
                if (self.current_image + 1) < len(self.image_list):
                    self.current_image += 1
                    self.set_base_image(self.image_list[self.current_image])

        del caller

    def toggle_fullscreen(self, caller=None):
        """
        Set the window to fullscreen mode if it is windowed
        Or set the window to windowed mode if it is fullscreen

        Args:
            caller (widget, optional): Nothing. Defaults to None.
        """

        if not Window.fullscreen:
            self.old_size = Window.size
            Window.size = self.get_screen_size()

            Window.fullscreen = True
            Window.borderless = True

            self.fullscreen_button.icon = 'fullscreen-exit'
        elif Window.fullscreen:
            Window.size = self.old_size
            Window.fullscreen = False
            Window.borderless = False

            self.fullscreen_button.icon = 'fullscreen'

        del caller

    def set_base_image(self, path):
        """
        Select Image (Base Function)

        Args:
            path (_type_): _description_
        """
        
        _path = os.path.split(os.path.realpath(path))

        if path in self.image_list:
            self.base_image = path
            if not self.enable_carousel:
                self.image.source = path
                self.pre_carousel()
        else:
            if os.path.isfile(_path[1]):
                os.chdir(_path[0])
                self.image_list = [_path[1]]

                self.make_carousel()

                self.carousel.load_slide(self.carousel.slides[self.current_image])

        if os.path.isdir(path):
            if not path.endswith('/'):
                path = path + '/'

            self.get_img_list(directory=path)
	
            os.chdir(path)

            self.refresh_look()

        else:
            if self.image:
                if os.path.split(path)[1] not in self.image_list:
                    if path not in self.image_list:
                        self.image_list.append(path)
                self.image.source = path

        self.make_tile()

    def refresh_slide(self, carousel, slide):
        """
        Set self.current_image when carousel slide is changed

        Args:
            carousel (Carousel)
            slide (One Of Carousel.slides)
        """

        if slide:
            if not self.props['loading']:
                self.current_image = carousel.slides.index(slide)

    def pause(self):
        """
        Pause Window when it is continued
        """

        print(':: paused ::')

        if not self.props['loading']:
            self.props['loading'] = True

            self.loading_screen.md_bg_color = self.theme_cls.primary_color

            self.screen_mgr.current = 'loading_screen'

    def resume(self):
        """
        Resume Window when it is paused
        """

        if self.props['loading']:
            self.props['loading'] = False

            self.screen_mgr.current = 'view_screen'

    def refresh(self, clock_time=None):
        """
        Popup Management

        Args:
            clock_time (float, optional): Time Passed. Defaults to None.
        """

        del clock_time


        if Window.mouse_pos[1] < self.bar_popup.size[1]:
            self.show_bar()
        elif Window.mouse_pos[1] > self.bar_popup.size[1]:
            self.hide_bar()

        if self.image_list:
            if self.props['keep_bar_shown']:
                self.props['keep_bar_shown'] = False
            
            if not self.props['cursor_leaved']:
                if Window.mouse_pos[1] > (Window.size[1] - self.up_popup.size[1]):
                    self.show_tile()
                elif Window.mouse_pos[1] < (Window.size[1] - self.up_popup.size[1]):
                    self.hide_tile()
            elif self.props['cursor_leaved']:
                self.hide_tile()
        else:
            self.props['keep_bar_shown'] = True
            if not self.props['bar_toggled']:
                self.show_bar()

    def show_bar(self):
        """
        Show The Bottom Bar With Animation
        """


        if not self.props['bar_toggled']:

            animation = Animation(
                pos=(self.bar_popup.pos[0], 0),
                duration=self.anim_duration,
            )
            animation.start(self.bar_popup)

            self.props['bar_toggled'] = True

    def hide_bar(self):
        """
        Hide The Bottom Bar With Animation
        """

        if self.props['bar_toggled']:
            if not self.props['keep_bar_shown']:
                animation = Animation(
                    pos=(self.bar_popup.pos[0], -90),
                    duration=self.anim_duration,
                    transition=self.props['transition']
                )
                animation.start(self.bar_popup)

                self.props['bar_toggled'] = False

    def show_tile(self):
        """
        Show The Tile With Animation
        """

        if not self.props['tile_toggled']:
            animation = Animation(
                pos=(self.up_popup.pos[0], Window.size[1] - self.up_popup.size[1]),
                duration=self.anim_duration,
                transition=self.props['transition']
            )
            animation.start(self.up_popup)

            self.props['tile_toggled'] = True

    def hide_tile(self):
        """
        Hide The Tile With Animation
        """

        if self.props['tile_toggled']:
            animation = Animation(
                pos=(self.up_popup.pos[0], (Window.size[1] + self.up_popup.size[1])),
                duration=self.anim_duration,
                transition=self.props['transition']
            )
            animation.start(self.up_popup)

            self.props['tile_toggled'] = False

    def switch_to_carousel(self):
        """
        Notify before set screen to Carousel View
        """

        if not self.props['loading']:
            self.make_caption('Carousel View (Slow)')

            self.make_carousel()

    def pre_carousel(self):
        """
        Optimize Carousel Widget
        """

        if not self.image_list:
            self.get_img_list()

        for src in self.image_list:
            self.carousel.add_widget(Image(source=src))

        if self.current_image and self.enable_carousel:
            self.carousel.load_slide(self.carousel.slides[self.current_image])

    def make_carousel(self):
        """
        Optimize and set screen to Carousel View
        """

        self.enable_carousel = True

        self.pause()

        self.carousel.clear_widgets()

        Logger.info('View: Mode Changed To Carousel')

        self.base_view.clear_widgets()

        self.pre_carousel()

        self.image = self.carousel

        self.base_view.add_widget(self.image)
        self.carousel_button.icon = 'view-array'

        self.resume()

    def switch_to_simple_view(self):
        """
        Notify before set screen to Simple View
        """

        if not self.props['loading']:
            self.make_caption('Simple View (Fast)')
            self.make_simple_view()

    def make_simple_view(self):
        """
        Optimize and set screen to Simple View
        """

        self.enable_carousel = False
        self.image = Image()
        Logger.info('View: Mode Changed To Simple View')

        if len(self.image_list) <= 1:
            if self.image_list:
                self.set_base_image(self.image_list[self.current_image])
        else:
            self.image.source = self.image_list[self.current_image]

        self.base_view.clear_widgets()

        self.base_view.add_widget(self.image)

        self.carousel_button.icon = 'view-carousel'

    def choose_dir(self, caller=None):
        """Get Group Of Images from Directory (from self.shell_args.image)

        Args:
            caller (_type_, optional): Caller Of Function. Defaults to None.
        """
        if self.shell_args.image:
            if not os.path.isdir(self.shell_args.image):
                directory = os.path.split(self.shell_args.image)[0]
            else:
                directory = self.shell_args.image
        else:
            directory = os.getcwd()

        self.file_manager.select_path = self.select_path
        self.file_manager.exit_manager = self.exit_manager

        self.file_manager.show(directory)

        del caller

    def exit_manager(self, args=None):
        """
        Exit The File Manager

        Args:
            args (NoneType, optional): Nothing. Defaults to None.
        """

        if args:
            self.file_manager.close()

    def select_path(self, path: str):
        """
        Close The File Manager and select path,
        and Open Path from path argument

        Args:
            path (str): Open Path
        """
        self.file_manager.close()
        Clock.schedule_once(lambda dt: self.set_base_image(path))

    def refresh_look(self):
        """
        Refresh The Application View Or Popups
        """

        if self.enable_carousel:
            self.make_carousel()
        elif not self.enable_carousel:
            self.make_simple_view()

        if self.props['tile_toggled']:
            self.show_bar()
        elif not self.props['tile_toggled']:
            self.hide_bar()

    def build(self):
        '''
        Return The Main Screen
        '''

        return self.global_screen

if __name__ == '__main__':
    app = App()
    app.run()
