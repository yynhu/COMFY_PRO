#! /usr/bin/env/python
# -*- coding=utf-8 -*-
"""
======================模块功能描述=========================    
       @File     : utils.py
       @IDE      : PyCharm
       @Author   : 陈虎
       @Date     : 2024/8/17 上午11:28
       @Desc     : 
=========================================================   
"""

import os
import re
import shutil
import time
import winreg
import datetime
import psutil
from PIL import Image
from loguru import logger
expiration_time = None
def get_desktop():
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders')
    return winreg.QueryValueEx(key, "Desktop")[0]


def find_processes_by_name(name_list, close=True):
    if isinstance(name_list, str):
        name_list = [name_list]
    for process in psutil.process_iter(['pid', 'name']):
        if process.info['name'].lower() in map(str.lower, name_list):
            proc = psutil.Process(process.info['pid'])
            logger.success(f"进程 {process.info['name']} (PID: {process.info['pid']}) 已找到。")
            if not close:
                return True
            proc.terminate()

def find_file_matching_pattern(directory, pattern=None, flag=False):
    try:
        with os.scandir(directory) as entries:
            for item in entries:
                # 处理文件且非空的情况
                if item.is_file():
                    try:
                        if os.path.getsize(item.path) > 0:  # 只有在文件非空的情况下才处理
                            if pattern is None or re.match(pattern, item.name):
                                yield item.path
                    except OSError as e:
                        logger.error(f"Error accessing file {item.path}: {e}")
                # 处理目录并递归搜索
                elif flag and item.is_dir():
                    yield from find_file_matching_pattern(item.path, pattern, flag)
    except OSError as e:
        logger.error(f"Error accessing directory {directory}: {e}")
        return set()

def find_file_matching_pattern(directory, pattern=None, flag=False):
    try:
        for item in os.scandir(directory):
            try:
                # 如果是文件且非空，则进行后续处理
                if item.is_file() and os.path.getsize(item.path) > 0:
                    # 如果指定了模式并且文件名匹配该模式，则返回文件路径
                    if pattern and re.match(pattern, item.name):
                        yield item.path
                    # 如果没有指定模式，则直接返回文件路径
                    elif not pattern:
                        yield item.path
                # 如果允许递归搜索子目录且当前条目为目录，则递归调用自身
                elif flag and item.is_dir():
                    yield from find_file_matching_pattern(item.path, pattern, flag)
            except OSError as e:
                # 处理文件被删除或其他操作系统错误
                logger.error(f"Error accessing {item.path}: {e}")
    except OSError as e:
        # 如果目录本身不存在或其他错误，返回空生成器
        logger.error(f"Error accessing directory {directory}: {e}")
        return set()


def find_folder_matching_pattern(directory_path, pattern=None):
    matching_directories = []

    def scan_directory(dir_path):
        try:
            with os.scandir(dir_path) as entries:
                for entry in entries:
                    # 排除回收站文件夹
                    if entry.is_dir() and entry.name != "#recycle" and entry.name != "处理结果":
                        # 匹配文件夹名称
                        if pattern and not re.match(pattern, entry.name):
                            continue
                        images = list(
                            find_file_matching_pattern(entry.path, r".*\.(jpg|jpeg|png|JPG|JPEG|PNG)$"))
                        if images:
                            matching_directories.append(entry.path)
                        # 递归调用以继续遍历子目录
                        scan_directory(entry.path)
        except OSError as e:
            logger.error(f"访问目录时出错: {dir_path}, 错误: {e}")
    scan_directory(directory_path)

    return matching_directories


# 生成文件夹,如果存在时,清空文件夹：
def generate_folder(folder_path, clear=True):
    # folder_path = os.path.join(dir_, name)
    try:
        os.makedirs(folder_path, exist_ok=True)
        if clear:
            shutil.rmtree(folder_path)  # 清空文件夹
            os.makedirs(folder_path)  # 重新创建文件夹
    except FileNotFoundError:
        logger.error(f"路径 {os.path.dirname(folder_path)} 不存在，请检查。")
    except PermissionError:
        logger.error(f"权限不足，无法操作 {folder_path}。")
    except OSError as e:
        logger.error(f"操作失败: {e}")
    # return folder_path


def rename_folder(old_path, new_name, same_folder=True):
    # 检查文件夹是否存在
    if not os.path.exists(old_path):
        logger.warning(f"文件夹 {old_path} 不存在！")
        return
    try:
        # 重命名文件夹
        if same_folder:
            folder_name = os.path.dirname(old_path)
            file_name = os.path.basename(old_path)
            name_ = file_name + new_name
            new_name = os.path.join(folder_name, name_)
        os.rename(old_path, new_name)
        logger.success(f"文件夹已成功从 {old_path} 重命名为 {new_name}")
    except FileNotFoundError:
        logger.error(f"重命名失败: 源文件夹 {old_path} 未找到。")
    except PermissionError:
        logger.error(f"重命名失败: 权限不足，无法重命名 {old_path}。")
    except OSError as e:
        logger.error(f"重命名失败: 操作系统错误 - {e}")
    except Exception as e:
        logger.error(f"重命名失败: 未知错误 - {e}")


def create_path_tuple(tuple_folder):
    result = []
    try:
        with os.scandir(tuple_folder) as entries:
            for entry in entries:
                if not entry.is_dir():
                    continue
                path_first = os.path.join(entry.path, "0")
                path_second = os.path.join(entry.path, "1")
                if os.path.exists(path_first) and os.path.exists(path_second):
                    list_first = list(find_file_matching_pattern(path_first, r".*\.(jpg|jpeg|png|JPG|JPEG|PNG)$"))
                    if len(list_first) != 1:
                        continue
                    list_second = list(find_file_matching_pattern(path_second, r".*\.(jpg|jpeg|png|JPG|JPEG|PNG)$"))
                    if len(list_second) != 1:
                        continue
                    tuple_ = (list_first[0], list_second[0])
                    result.append(tuple_)
        return result
    except Exception as e:
        logger.error(f"创建图组元组失败:{e}")


def get_pt_info(content, reference_width, reference_height):
    original_name = content
    try:
        if os.path.exists(content):
            original_name = os.path.basename(content)
        original_name = original_name.replace(" ", "")
        # 当图片中包含"纯色"时，需要将其排除掉,默认宽度为2
        if "纯色" in original_name:
            logger.info(f"【识别】到纯色图片:{content}")
            return "纯色", 2
        pattern = r'(?:中标|胸标|小标)'
        # 使用 re.sub 函数替换掉匹配的词组
        cleaned_text = re.sub(pattern, '', original_name)
        match_obj = \
            re.search(
                r"(?:\d*\.?\d*\.?\d+-)?(.*?)(\d{1,2}.?\d*)(?:cm)?[x,×,X](\d{1,2}.?\d*)(?:cm)?(?:_ZB)?(?:_?\d*)?(?:_\d+x\d+)?\.(?:jpg|png|psb|psd)$",
                cleaned_text, flags=re.I)
        logger.info(f"原始图片名:{original_name}")
        logger.info(match_obj.groups())
        name = match_obj.group(1)
        logger.info(f"【识别】图片名:{name}")
        value_1 = float(match_obj.group(2))
        value_2 = float(match_obj.group(3))
        if reference_width < reference_height:
            width = min(value_1, value_2)
        else:
            width = max(value_1, value_2)
        logger.info(f"【识别】印花真实宽度:{width}cm")
        return name, width
    except Exception as e:
        logger.info(f"解析失败:{e},图片路径或图片名为：{content}")


def pt_resize(file_path, save_folder):
    try:
        name = os.path.basename(file_path)
        # 图片中是否包含“_ZB”,不包含：False
        flag = True if "_ZB" in name else False
        tmp_ = name.rsplit(".", 1)
        pattern = rf"{tmp_[0]}(?:_ZB)?_\d+_\d+x\d+.{tmp_[1]}"
        result = list(find_file_matching_pattern(save_folder, pattern))
        if result:
            temp_name = os.path.basename(result[0])
            logger.info(f"【图片处理-0】在临时印花文件夹中匹配图片:【{temp_name}】>>>>>>")
            width,height = temp_name.rsplit(".",1)[0].rsplit("_",1)[1].split("x")
            return result[0], flag, float(width), float(height)
        image = Image.open(file_path)
        logger.info(f"【图片处理-1】当前图片尺寸：{image.size}")
        width, height = image.size
        image_bbox = image.getbbox()
        if not image_bbox:
            raise f'该图像中未识别到有效内容，请检查！:{file_path}'
        logger.info(f'【图片处理-2】图像范围:{image_bbox}')
        if width != image_bbox[2] - image_bbox[0] or height != image_bbox[3] - image_bbox[1]:
            image = image.crop(image_bbox)
            width, height = image.size
            image = image.resize((width, height))
        # 对图片进行压缩（宽或高小于1000）
        if width > height and width > 1000:
            height = int(height / width * 1000)
            width = 1000
            image = image.resize((width, height))
        if height > width and height > 1000:
            width = int(width / height * 1000)
            height = 1000
            image = image.resize((width, height))
        # 在修改的图片上加入时间戳:
        random_str = int(time.time() * 1000)
        tmp_.insert(1, f"_{random_str}_{width}x{height}.")
        name = "".join(tmp_)
        result_path = os.path.join(save_folder, name)
        image.save(result_path)
        logger.success(f"【图片处理-3】图片已保存:{result_path}")
        return result_path, flag, float(width), float(height)
    except Exception as e:
        logger.error(f"图片初始化处理失败:{e}")

# 获取模板印花的真实面积：
def remove_psd(folder):
    psd_list = []
    result = find_folder_matching_pattern(folder, r"^输出文件夹-\d+$")
    if not result:
        logger.info("【未找到已查阅的输出文件夹】>>>>>>>")
        return
    for path in result:
        if not os.path.exists(path):
            continue
        list_ = list(find_file_matching_pattern(path, r".*\.psd$", True))
        if not list_:
            continue
        psd_list.extend(list_)
    if not psd_list:
        logger.info("【未找到需要删除的psd文件】>>>>>>>")
        return
    for file_path in psd_list:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.success(f"【删除成功】: {file_path}")
        except Exception as e:
            logger.error(f"删除失败!!!:{file_path},{e}")


def generate_task(folder,pattern):
    tasks = []
    try:
        result_pt = find_folder_matching_pattern(folder, pattern)
        if not result_pt:
            logger.warning("【未找符合条件的文件夹】>>>>>>>")
            return
        for current_pt in result_pt:
            if not os.path.exists(current_pt):
                continue
            # dir_ = os.path.dirname(current_pt)
            # # 检查标记
            # if os.path.exists(os.path.join(dir_, '【标记】.txt')):
            #     continue
            # current_psds = list(find_file_matching_pattern(dir_, r".*\.psd$"))
            # if not current_psds:
            #     continue
            tasks.append(current_pt)
        if tasks:
            tasks.sort(key=lambda x: os.stat(x).st_ctime,reverse=True)
        return tasks
    except Exception as e:
        logger.error(f"生成任务异常:{e}")


def flag_txt(folder, content):
    file_path = os.path.join(folder, '【标记】.txt')
    try:
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(content + '\n')
    except FileNotFoundError as e:
        logger.warning(f"该文件夹已被人为删除：{folder}")


def confirm_time(specific_time):
    try:
        current_time = datetime.datetime.now()
        if current_time <= specific_time:
            return True
        logger.warning(">>>>>>检测当前程序已过有效期，请及时更新!")
    except Exception as e:
        logger.warning(f">>>>>>【确认时效】异常:{e}")


def confirm_userinfo(user_id):
    global expiration_time
    try:
        db = DB()
        result = db.query_sql()
        result_dict = dict(result)
        if user_id not in result_dict:
            logger.warning(f">>>>>>未查询到该用户信息ID:【{user_id}】,请联系管理员！")
            return
        expiration_time = result_dict[user_id]
        if confirm_time(expiration_time):
            return True
    except Exception as e:
        logger.warning(f">>>>>>确认用户信息异常:{e}")

def decrypt_content(content):
    key = "Vd7uQ-5p9dCCNlp6bClBK92ClEiKjp_9s3pF3cUjze0="
    fernet = Fernet(key)
    # with open(file_name, 'rb') as enc_file:
    #     encrypted = enc_file.read()
    decrypted = fernet.decrypt(content)
    decrypted_text = decrypted.decode('utf-8')  # 将字节流转换为文本格式
    return decrypted_text
def decrypt_all():
    result = find_documents(config["mongo"]["tietu_collection"],{"type":'encry_func'})[0]
    key_str =result["keyValue"]
    del result["_id"]
    del result["keyValue"]
    del result["type"]
    js_dict = {x: Fernet(key_str).decrypt(y).decode('utf-8') for x,y in result.items()}
    # logger.info(js_dict)
    return js_dict
if __name__ == '__main__':
    decrypt_all()
    # pt_resize(r"C:\Users\Administrator\Desktop\h中国耀小标2.92X7cm_ZB.png",
    #           r"C:\Users\Administrator\Desktop\贴图程序\PT_TEMP")
    # random_str = f"-已完成{int(time.time() * 1000)}"
    # rename_folder(r"C:\Users\Administrator\Desktop\印花图片", random_str)
    # resutl = create_path_tuple(r"C:\Users\Administrator\Desktop\贴图搜索路径\背面大图\印花-已完成1730871680781\图组")
    # logger.(resutl)
