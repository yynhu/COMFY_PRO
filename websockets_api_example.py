import websocket
import uuid
import json
import requests
import os
import time
from loguru import logger

from comfy_utils import find_file_matching_pattern,generate_task,rename_folder
server_address = "192.168.40.134:8188"
client_id = str(uuid.uuid4())

def queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": client_id}
    response = requests.post(f"http://{server_address}/prompt", json=p)
    return response.json()

def get_image(filename, subfolder, folder_type):
    params = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    response = requests.get(f"http://{server_address}/view", params=params)
    return response.content

def get_history(prompt_id):
    response = requests.get(f"http://{server_address}/history/{prompt_id}")
    return response.json()

def get_images(ws, prompt,save_folder=None):
    prompt_id = queue_prompt(prompt)['prompt_id']
    current_node = ""
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                # if data['node'] is None and data['prompt_id'] == prompt_id:
                #     break # Execution is done
                if data['prompt_id'] == prompt_id:
                    if data['node'] is None:
                        break #Execution is done
                    else:
                        number_str = data['node']
                        current_node = prompt[number_str]['class_type']

        else:
            if current_node == 'SaveImageWebsocket':
            # 将二进制流转换为图片并保存
            #     os.makedirs(prompt_id, exist_ok=True)
                folder_path = os.path.join(save_folder, "处理结果")
                os.makedirs(folder_path, exist_ok=True)
                save_images(folder_path,out[8:])
    # 根据本地历史进行保存
    # history = get_history(prompt_id)[prompt_id]
    # for node_id in history['outputs']:
    #     node_output = history['outputs'][node_id]
    #     # images_output = []
    #     if 'images' in node_output:
    #         for image in node_output['images']:
    #             image_data = get_image(image['filename'], image['subfolder'], image['type'])
    #             # os.makedirs(prompt_id, exist_ok=True)
    #             folder_path = os.path.join(save_folder, "本地历史记录")
    #             os.makedirs(folder_path, exist_ok=True)
    #             save_images(folder_path,image_data,image['filename'])

def interupt_prompt():
    response = requests.post(f"http://{server_address}/interrupt")
    response.raise_for_status()

def clear_comfy_cache(unload_models=True, free_memory=True):
    clear_data = {
        "unload_models": unload_models,
        "free_memory": free_memory
    }
    response = requests.post(f"http://{server_address}/free", json=clear_data)
    response.raise_for_status()  # 检查请求是否成功

def get_node_info_by_class(node_name):
    response = requests.get(f"http://{server_address}/object_info/{node_name}")
    response.raise_for_status()  # 检查请求是否成功
    a=response.json()
    logger.info(a)
    return a
def save_images(dir_,content,filename=None):
    # os.makedirs(dir_, exist_ok=True)
    if filename is None:
        filename = f"{str(uuid.uuid4())}.png"
    with open(os.path.join(dir_, filename), "wb") as f:
        f.write(content)
    logger.success(f"图片已成功保存为: {filename}")


def upload_image(file_path):
    url = f"http://{server_address}/upload/image"
    with open(file_path, 'rb') as file:
        files = {'image': (os.path.basename(file_path), file, 'image/jpeg')}
        # 发送POST请求
        response = requests.post(url, files=files)
        data =response.json()
        result = data["name"]
        logger.success(f"=========图片上传成功:【{result}】")
        return result
# content = open("work_flow/人像抠图.json", "r", encoding="utf-8").read()
# prompt = json.loads(content)
# filename = upload_image(r"C:\Users\Administrator\Desktop\input.jpg")
# prompt["6"]["inputs"]["image"] = filename
# #
# ws = websocket.WebSocket()
# ws.connect("ws://{}/ws?clientId={}".format(server_address, client_id))
# #
# images = get_images(ws, prompt)
# ws.close()
# clear_comfy_cache(free_memory=True)
# print(get_node_info_by_class("AutoDownloadBiRefNetModel"))
def upload_folder(folder):
    images = []
    result = list(find_file_matching_pattern(folder, r".*\.(jpg|jpeg|png|JPG|JPEG|PNG)$"))
    if not result:
        logger.warning(f"没有找到图片:【{folder}】")
        return
    for current_file in result:
        image_name = upload_image(current_file)
        images.append(image_name)
    logger.success(f"=========文件夹上传成功:【{folder}】")
    return images
def single_task_handler(ws,task):
    logger.info(f"开始执行任务：{task}")
    if not os.path.exists(task):
        logger.warning(f"任务文件不存在：{task}")
        return
    images_list = upload_folder(task)
    json_str = open("work_flow/人像抠图.json", "r", encoding="utf-8").read()
    prompt = json.loads(json_str)
    for filename in images_list:
        prompt["6"]["inputs"]["image"] = filename
        get_images(ws, prompt, task)
    rename_folder(task, "-已完成")
# upload_folder(r"C:\Users\Administrator\Desktop\立领3")
# print(generate_task(r"C:\Users\Administrator\Desktop\AI绘图",r"^(?!.*-已完成$).+$"))
def execution_main(folder):
    while True:
        task_list = generate_task(folder, r"^(?!.*-已完成$).+$")
        if not task_list:
            logger.info(f"未检测到任务,5s后重新搜索.....")
            time.sleep(5)
            logger.info(f"任务检测搜索中........>>>>>>>")
            continue
        logger.info(f">>>>>>满足条件的任务列表：{task_list}")
        while task_list:
            ws = websocket.WebSocket()
            ws.connect("ws://{}/ws?clientId={}".format(server_address, client_id))
            task = task_list.pop()
            single_task_handler(ws,task)
            ws.close()


if __name__ == '__main__':
    execution_main(r'\\172.16.1.5\74.ai绘图')
