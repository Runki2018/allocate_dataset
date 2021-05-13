import json
import os

# TODO: 找出category_id != label的原因
# 很奇怪，分配的标注文件中，category_id != label, 而是出现很多为 1的情况。
for i in range(26):
    file = '../annotation/' + str(i) + '.json'
    if not os.path.exists(file):
        continue
    ann = json.load(open(file, 'r'))
    images_list = ann["images"]
    annotations_list = ann["annotations"]
    for k in range(len(images_list)):
        label = images_list[k]["label"]
        annotations_list[k]["category_id"] = label
    ann["annotations"] = annotations_list
    json.dump(ann, open(file, 'w'), indent=4)
