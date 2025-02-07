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

import requests
import json

def interupt_prompt(server_address):
    response = requests.post(f"http://{server_address}/interrupt")
    response.raise_for_status()  # 检查请求是否成功


def get_node_info_by_class(node_class, server_address):
    response = requests.get(f"http://{server_address}/object_info/{node_class}")
    response.raise_for_status()  # 检查请求是否成功
    return response.json()

def clear_comfy_cache(server_address, unload_models=False, free_memory=False):
    clear_data = {
        "unload_models": unload_models,
        "free_memory": free_memory
    }
    response = requests.post(f"http://{server_address}/free", json=clear_data)
    response.raise_for_status()  # 检查请求是否成功
    return response.json()
