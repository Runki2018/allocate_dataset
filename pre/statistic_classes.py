import os
import json
from tqdm import tqdm


def statistic_classes():
    """count the number of each class"""
    nc = 9  # number of classes
    person = 26  # number of annotator
    count_list = [0 for x in range(nc)]
    for i in range(person):
        json_file = './data/' + str(i) + '/label.json'
        ann_json = json.load(open(json_file, 'r'))
        images_list = ann_json["images"]
        for image in tqdm(images_list):
            label = image["label"]
            count_list[label] += 1
    print(count_list)


if __name__ == "__main__":
    statistic_classes()
