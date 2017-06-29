import sublime
import sublime_plugin
import re
try:
    from MarkdownEditing.mdeutils import *
except ImportError:
    from mdeutils import *

class HightlightPackageControlMsg(sublime_plugin.EventListener):

    def on_new_async(self, view):
        if view.name() == 'Package Control Messages' and view.file_name() == None and view.is_read_only() and ~view_is_markdown(view):
            view.run_command('mde_de_indent')


class MdeDeIndentCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        heading_msg_region = self.view.find(r'Package Control Messages\n=+\n+.+\n-+\n+', 0)
        actual_text_region = sublime.Region(heading_msg_region.b, self.view.size())
        actual_text = self.view.substr(actual_text_region)
        actual_text = re.sub(re.compile(r'^  ', re.MULTILINE), '', actual_text)
        new_view = self.view.window().new_file()
        new_view.run_command('append', {'characters': self.view.substr(heading_msg_region) + actual_text})
        new_view.set_syntax_file('Packages/MarkdownEditing/Markdown.tmLanguage')
        new_view.settings().set(sublime.load_settings('Markdown.sublime_settings').get('color_scheme'))
        new_view.set_scratch(True)
        new_view.set_name('Package Control Messages')
        new_view.set_read_only(True)
        self.view.close()
