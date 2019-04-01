import sublime
import sublime_plugin
import re
import string
import functools
import os

class DecideMdTitle(sublime_plugin.EventListener):
    ''' 决定 设置 Markdown 的文件命名方式
    支持 hexo 的模板
    '''

    def getSublimeTmplMdTitle(self,view):
        # 截取文章开头的部分内容
        cutLength = view.size() if bool(view.size() < 200) else 200
        text = view.substr(sublime.Region(0, cutLength))
        it = re.finditer(r'^title:(.*)$', text, re.M)
        title=None
        # 返回第一匹配命中的
        for m in it:
            title = m.group(1)
            break
        return title

    def on_pre_save_async(self,view):
        if view.file_name() or view.is_loading():
            syntax = view.settings().get('syntax')
            if syntax and 'Markdown' in syntax:
                title = self.getSublimeTmplMdTitle(view)
                # 如果没有title格式，则退出
                if not title:
                    return
                old = view.file_name()
                branch, leaf = os.path.split(old)
                # 获得原始文件名
                oldFileName,suffix=os.path.splitext(leaf)
                if oldFileName != title:
                    new = os.path.join(branch,title+suffix)
                    sublime.status_message("auto rename: " + new)
                    try:
                        if os.path.isfile(new) and not self.is_case_change(old, new):
                            raise OSError("File already exists")

                        os.rename(old, new)

                        if view:
                            view.retarget(new)
                    except OSError as e:
                        sublime.status_message("Unable to rename: " + str(e))
                    except:
                        sublime.status_message("Unable to rename")                   


    def is_case_change(self, old, new):
        if old.lower() != new.lower():
            return False
        if os.stat(old).st_ino != os.stat(new).st_ino:
            return False
        return True

    def on_modified_async(self,view):
    # def on_pre_save_async(self,view):
        if view.file_name() or view.is_loading():
            return

        syntax = view.settings().get('syntax')
        if syntax and 'Markdown' in syntax:
            title = self.getSublimeTmplMdTitle(view)
            if(title):
                view.set_name(title)
                return
            else:
                # print("start MarkdownEdit default Rule")
                # 如果没有找到 重新遵循 MarkdownEdit 中的规则来查找
                text = view.substr(sublime.Region(0, view.size()))
                it = re.finditer(r'^(#{1,6}(?!#))|^(-{3,}|={3,})', text, re.M)
                title = ''
                title_begin = None
                for m in it:
                    if '.front-matter' in view.scope_name(m.start()):
                        continue
                    if re.match(r'^(-{3,}|={3,})$', m.group()):
                        title_end = m.start() - 1
                        title_begin = text.rfind('\n', 0, title_end) + 1
                    else:
                        title_begin = m.end()
                        title_end = re.search('(' + m.group() + ')?(\n|$)', text[title_begin:]).start() + title_begin
                        title_begin = m.start() + 1
                    if 'markup.raw.block.markdown' not in view.scope_name(title_begin).split(' '):
                        break
                if len(title) == 0 and title_begin is not None:
                    title = text[title_begin: title_end]

                title = title.strip()
                if view.file_name() is None and len(title) > 0:
                    view.set_name(title[:55])
