# from datetime import datetime
from PIL import ImageGrab

import sublime
import sublime_plugin
from .mdeutils import view_is_markdown


class HaveImageFromClipboardListenerCommand(sublime_plugin.ViewEventListener):
    def on_activated_async(self):
        sublime.status_message("focus on view")
        if view_is_markdown(self.view):
            m = ImageGrab.grabclipboard()
            # if the clipboard have image, than setting the setting of clipboard.image to True
            self.view.settings().set("clipboard.image", False) if not m else self.view.settings().set("clipboard.image",
                                                                                                      True)
