import hashlib
import os
import os.path
import re
import sys
import tempfile
from urllib import parse

import sublime
# 加载第三方的模块
from .mdeutils import MDETextCommand

try:
    from PIL import ImageGrab
except ImportError:
    sublime.message_dialog("please download the appropriate version <https://pypi.org/project/Pillow/2.4.0/#files>")


def getBucket():
    '''
    获得默认的阿里云的 oss bucket 模块
    :param yourAccessKeyId:
    :param yourAccessKeySecret:
    :param yourBucketName:
    :return: 返回默认的 bucket 模块
    '''
    settings = sublime.load_settings('Markdown.sublime-settings')
    othersyslibrary = settings.get("OtherSysLibrary")

    if othersyslibrary:
        for sub in othersyslibrary:
            sub_abs_path = os.path.abspath(sub)
            if os.path.isdir(sub_abs_path) and not sub_abs_path in sys.path:
                sys.path.append(sub_abs_path)
    try:
        import oss2
    except Exception as e:
        sublime.message_dialog("you must install oss2 module")

    # 获得四个重要的元素
    accessKeyId = settings.get("AccessKeyId")
    accessKeySecret = settings.get("AccessKeySecret")
    endPoint = settings.get("EndPoint")
    bucketName = settings.get("BucketName")

    if not accessKeyId:
        print("accessKeyId is none")
        return
    if not accessKeySecret:
        print("AccessKeySecret is none")
        return
    if not endPoint:
        print("EndPoint is none")
        return
    if not bucketName:
        print("bucketName is none")
        return
    # 阿里云主账号AccessKey拥有所有API的访问权限，风险很高。强烈建议您创建并使用RAM账号进行API访问或日常运维，请登录 https://ram.console.aliyun.com 创建RAM账号。
    auth = oss2.Auth(accessKeyId, accessKeySecret)
    # Endpoint以杭州为例，其它Region请按实际情况填写。
    bucket = oss2.Bucket(auth, endPoint, bucketName)
    if not bucket:
        print("bucket name is using first, will create new bucket")
        # 设置存储空间为私有读写权限。
        bucket.create_bucket(oss2.models.BUCKET_ACL_PRIVATE)
    return bucket


def getFileMd5(filename):
    """
    获得文件内容的Hash值
    :param filename:  文件路径
    :return: 该文件内容的hash值
    """
    if not os.path.isfile(filename):
        return
    myhash = hashlib.md5()
    f = open(filename, 'rb')
    while True:
        b = f.read(8096)
        if not b:
            break
        myhash.update(b)
    f.close()
    return myhash.hexdigest()


def upImageToAliOss(filePath, bucket=None):
    '''
    上传一个指定的路径的文件到指定的bucket模块中，设置为只读权限
    :param filePath: 本地文件路径
    :param bucket: bucket对象
    :return: 上传后的url链接
    '''
    absPath = os.path.abspath(filePath)
    fileName = os.path.basename(absPath)
    # 如果文件不存在
    if not os.path.exists(filePath):
        print("file path not exist ", filePath)
        return
    # 上传文件-在文件名前面加上当前时间，防止文件重复
    # nowTime=time.strftime('%Y%m%d%H%M%S',time.localtime(time.time()))
    fileName = getFileMd5(absPath)
    bucket = getBucket()
    if (not bucket):
        sublime.status_message("bucket is None,please check")
        return

    # <yourLocalFile>由本地文件路径加文件名包括后缀组成，例如/users/local/myfile.txt
    callback = bucket.put_object_from_file(fileName, filePath)
    # 设置上传文件的访问权限
    import oss2
    bucket.put_object_acl(fileName, oss2.OBJECT_ACL_PUBLIC_READ)
    # 进行转码
    newFileName = parse.quote_plus(fileName)
    url = "{}://{}.{}/{}".format(bucket._make_url.scheme, bucket.bucket_name, bucket._make_url.netloc, newFileName)
    return url


class ReferenceNewInlineImageFromLocal(MDETextCommand):
    '''上传本地文件到阿里云，并获得插入链接	'''

    def getLocalInsertImagePath(self):
        '''
        获得本地插入图片路径
        return: 本地图片路径
        '''
        # 获得当前编辑窗口对象
        window = self.view.window()
        # 当前的 sheet
        current_sheet = window.active_sheet()
        # 打开对话框选择文件
        window.run_command("prompt_open_file", {"initial_directory": "C:/Users/Public/Pictures"})

        # 查找文件，并且关闭
        file = None
        fileBaseName = None
        window = self.view.window()
        for sheet in window.sheets():
            # 强制切换到当前 sheet 否则，无法获取文件名
            window.focus_sheet(sheet)
            file = window.extract_variables()["file"]
            # 文件路径是否为图片路径
            if bool(re.search('.(gif|jpeg|png|jpg|bmp)$', file)):
                sublime.status_message("find images path %s，close next" % (file))
                # 获得文件基础名
                fileBaseName = window.extract_variables()["file_base_name"]
                window.run_command("close")
                break
            else:
                file = None

        # 激活之前编辑的窗口
        window.focus_sheet(current_sheet)
        return (file, fileBaseName)

    """插入图片"""

    def run(self, edit):
        file, fileBaseName = self.getLocalInsertImagePath()
        if not file:
            print("the insert images is error")
            return
        link = upImageToAliOss(filePath=file)
        if link:
            # self.view.run_command("insert_snippet", {"contents": "![${1:$SELECTION}](${2:" + link + "})"})
            self.view.run_command("insert_snippet", {"contents": "![${2:" + fileBaseName + "}](${1:" + link + "})"})
        else:
            sublime.status_message("insert_snippet is error")


class ReferenceNewInlineImageFromClipboard(MDETextCommand):
    """
    从剪切板中获得图片链接，并且上传到 OSS 中
    """

    def run(self, edit):
        m = ImageGrab.grabclipboard()
        # 如果存在剪切板中存在图片
        if m:
            fd, tempFileName = tempfile.mkstemp(".png")
            try:
                m.save(tempFileName)
            except IOError:
                sublime.message_dialog("the temp file from Clipboard can't save")
                return
            # 上传到 阿里 OSS
            link = upImageToAliOss(filePath=tempFileName)
            if link:
                # self.view.run_command("insert_snippet", {"contents": "![${1:$SELECTION}](${2:" + link + "})"})
                self.view.run_command("insert_snippet", {"contents": "![${1:$SELECTION}](" + link + ")"})
            else:
                sublime.status_message("insert_snippet is error")
