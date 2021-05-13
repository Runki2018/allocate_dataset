import json
from tqdm import tqdm
import os


def set_default(file: str):
    """设置手部关键点遮挡指标的默认值，1-OK和2-手掌两类默认为无遮挡，其余类别设置为遮挡"""
    save_file = file.split(".json")[0] + '_default.json'
    ann = json.load(open(file, 'r'))
    images_list = ann["images"]
    for i in tqdm(range(len(images_list))):
        label = images_list[i]["label"]
        if label != 1 and label != 2:
            images_list[i]["occlusion"] = 1
        else:
            images_list[i]["occlusion"] = 0
    # replace
    ann["images"] = images_list
    # save
    json.dump(ann, open(save_file, 'w'), indent=4)


if __name__ == '__main__':
    file_path = "../annotation/3.json"
    set_default(file_path)

