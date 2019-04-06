import sublime
import sublime_plugin
import os
import sys
import tempfile
import shutil

# add PIL module
if sublime.platform() == "osx":
	package_file = os.path.normpath(os.path.abspath(__file__))
	package_path = os.path.dirname(package_file)
	lib_path =  os.path.join(package_path, "lib")
	if lib_path not in sys.path:
		sys.path.append(lib_path)
	from PIL import ImageGrab
	from PIL import ImageFile
	from PIL import Image

try:
	from MarkdownEditing.mdeutils import *
except ImportError:
	from mdeutils import *

class InsertImageFromClipboardCommand(MDETextCommand):
	"""docstring for InsertImagerFromClipboardCommand"""
	def load_settings(self):
		settings = sublime.load_settings('Markdown.sublime-settings')
		self.SAVE_METHOD = settings.get("mde.image.save.method")
		print(self.SAVE_METHOD)
		self.SAVE_BASEDIR = settings.get("mde.image.save.basedir")
		print(self.SAVE_BASEDIR)
		# current file dirname
		self.curdir = os.path.dirname(self.view.file_name())


	def run(self, edit):
		print("开始插入图片")
		self.load_settings()

		filepath = InsertImageFromClipboardCommand.save_image()
		if filepath:
			basename,url = self.getLocalUrl(filepath)
			self.view.run_command("insert_snippet", {"contents": "!["+basename+"](" + url + ")"})
		else:
			sublime.status_message("insert_snippet is error")

	@staticmethod
	def save_image():
		# 保存剪切板上的图片内容到临时文件
		m = ImageGrab.grabclipboard()
		if m :
			fd, tempFileName = tempfile.mkstemp(".png")
			try:
				m.save(tempFileName)
			except IOError as e:
				sublime.status_message("save image from clipboard is error")
				raise e
			return tempFileName

	def getLocalUrl(self,filePath):
		# 移动文件路径到制定目录，并且返回插入链接名和url
		if not filePath or not os.path.exists(filePath):
			return
		# filePath, ext
		dirname,ext=os.path.splitext(filePath)
		# 文件名，不含后缀
		basename=os.path.basename(dirname)

		basedir = os.path.expanduser(self.SAVE_BASEDIR) if self.SAVE_METHOD == "absoulte" else os.path.join(self.curdir,self.SAVE_BASEDIR)
		
		basedir = os.path.abspath(basedir)
		# 目标文件夹
		if not os.path.exists(basedir):
			os.makedirs(basedir)
		shutil.move(filePath,basedir)
		# 绝对路径运行
		realpath = basedir if self.SAVE_METHOD=="absoulte" else os.path.relpath(basedir,self.curdir)
		url = os.path.join(os.path.normpath(realpath),basename+""+ext)
		return basename,url
