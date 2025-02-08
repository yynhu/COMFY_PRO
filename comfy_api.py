#!/usr/bin/env/python
# -*- coding=utf-8 -*-
"""
======================模块功能描述=========================
       @File     : comfy_api.py
       @IDE      : PyCharm
       @Author   : 陈虎
       @Date     : 2025/2/6 11:55
       @Desc     :
=========================================================
"""

import websocket
import uuid
import json
import requests
import os
import time
from loguru import logger
from confs import confg
from comfy_utils import (
    find_file_matching_pattern,
    generate_task,
    rename_folder,
    generate_folder
)

class ImageProcessingClient:
    def __init__(self, server_address="192.168.40.134:8188"):
        self.server_address = server_address
        self.client_id = str(uuid.uuid4())

    def queue_prompt(self, prompt):
        """提交处理请求"""
        data = {"prompt": prompt, "client_id": self.client_id}
        try:
            response = requests.post(f"http://{self.server_address}/prompt", json=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"队列请求失败: {e}")
            return None

    def get_image(self, filename, subfolder, folder_type):
        """获取生成的图片"""
        params = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        try:
            response = requests.get(f"http://{self.server_address}/view", params=params)
            response.raise_for_status()
            return response.content
        except requests.RequestException as e:
            logger.error(f"获取图片失败: {e}")
            return None

    def get_history(self, prompt_id):
        """查询任务历史记录"""
        try:
            response = requests.get(f"http://{self.server_address}/history/{prompt_id}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"查询历史失败: {e}")
            return None

    def interrupt_prompt(self):
        """中断当前任务"""
        try:
            response = requests.post(f"http://{self.server_address}/interrupt")
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"中断任务失败: {e}")

    def clear_cache(self, unload_models=True, free_memory=True):
        """清理服务器缓存"""
        clear_data = {"unload_models": unload_models, "free_memory": free_memory}
        try:
            response = requests.post(f"http://{self.server_address}/free", json=clear_data)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"清理缓存失败: {e}")

    def get_node_info(self, node_name):
        """获取节点信息"""
        try:
            response = requests.get(f"http://{self.server_address}/object_info/{node_name}")
            response.raise_for_status()
            data = response.json()
            logger.info(data)
            return data
        except requests.RequestException as e:
            logger.error(f"获取节点信息失败: {e}")
            return None

    def save_image(self, dir_, content, filename=None):
        """保存图片到指定目录"""
        if filename is None:
            filename = f"{uuid.uuid4()}.png"
        with open(os.path.join(dir_, filename), "wb") as f:
            f.write(content)
        logger.success(f"图片已成功保存: {filename}")

    def upload_image(self, file_path):
        """上传单张图片"""
        url = f"http://{self.server_address}/upload/image"
        try:
            with open(file_path, 'rb') as file:
                files = {'image': (os.path.basename(file_path), file, 'image/jpeg')}
                response = requests.post(url, files=files)
                response.raise_for_status()
                data = response.json()
                logger.success(f"图片上传成功: {data['name']}")
                return data["name"]
        except requests.RequestException as e:
            logger.error(f"上传图片失败: {e}")
            return None

    def upload_folder(self, folder):
        """上传文件夹内所有图片"""
        images = []
        result = list(find_file_matching_pattern(folder, r".*\.(jpg|jpeg|png|JPG|JPEG|PNG)$"))
        if not result:
            logger.warning(f"未找到图片: {folder}")
            return images

        for file in result:
            image_name = self.upload_image(file)
            if image_name:
                images.append(image_name)

        logger.success(f"文件夹上传成功: {folder}")
        return images

    def process_images(self, ws, prompt, save_folder, count):
        """WebSocket 处理图片生成"""
        folder_path = os.path.join(save_folder, "处理结果")
        prompt_id = self.queue_prompt(prompt)['prompt_id']
        current_node = ""

        while True:
            out = ws.recv()
            if isinstance(out, str):
                message = json.loads(out)
                if message['type'] == 'executing':
                    data = message['data']
                    if data['prompt_id'] == prompt_id:
                        if data['node'] is None:
                            break
                        current_node = prompt[data['node']]['class_type']
            else:
                if current_node == 'SaveImageWebsocket':
                    if count == 0:
                        generate_folder(folder_path)
                    self.save_image(folder_path, out[8:])

    def handle_task(self, ws, task, folder):
        """处理单个任务"""
        logger.info(f"开始任务: {task}")
        if not os.path.exists(task):
            logger.warning(f"任务文件不存在: {task}")
            return

        images_list = self.upload_folder(task)
        if not images_list:
            return

        list_ = task.split(folder, 1)[1].strip("\\").split("\\")
        func_name = list_[0]
        json_str = open(f"work_flow/{confg['workflow'][func_name]}", "r", encoding="utf-8").read()
        prompt = json.loads(json_str)

        if len(list_) > 2:
            prompt["2"]["inputs"]["model_name"] = confg["workflow"][list_[-2]]

        count = 0
        for filename in images_list:
            prompt["6"]["inputs"]["image"] = filename
            self.process_images(ws, prompt, task, count)
            count += 1

        rename_folder(task, "-已完成")

    def execute_tasks(self, folder):
        """任务执行主循环"""
        while True:
            task_list = generate_task(folder, r"^(?!.*-已完成$).+$")
            if not task_list:
                logger.info(f"未检测到任务, 5s 后重试...")
                time.sleep(5)
                continue

            logger.info(f"检测到任务: {task_list}")

            while task_list:
                ws = websocket.WebSocket()
                ws.connect(f"ws://{self.server_address}/ws?clientId={self.client_id}")
                task = task_list.pop()
                self.handle_task(ws, task, folder)
                ws.close()


if __name__ == "__main__":
    client = ImageProcessingClient()
    client.execute_tasks(r'\\172.16.1.5\74.ai绘图')

