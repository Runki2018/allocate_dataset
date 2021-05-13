import json
from tqdm import tqdm


def get_relative_keypoints(kp, w, h):
    """根据图像宽高将关键点映射到0~1，的到相对坐标；且会去除置信度"""
    keypoints_relative = []
    for i in range(0, len(kp), 3):
        xy = kp[i] / w, kp[i+1] / h  # [x, y]
        keypoints_relative.extend(xy)
    return keypoints_relative


def get_txt(json_file: str):
    """将train.json 和 test.json读取为
    label x1 y1 x2 y2 ... x21, y21
    """
    ann = json.load(open(json_file, 'r'))
    images_list = ann["images"]
    annotation_list = ann["annotations"]
    w, h = images_list[0]['width'], images_list[0]['height']
    save_file = json_file.split('.json')[0] + '_images.txt'
    with open(save_file, 'w') as f:
        for image in tqdm(images_list):
            file_name = image["file_name"]
            f.write(file_name + '\n')
    save_file = json_file.split('.json')[0] + '_annotations.txt'
    print(save_file)
    with open(save_file, 'w') as f:
        for annotation in tqdm(annotation_list):
            label = annotation["category_id"]
            keypoints = annotation["keypoints"]
            keypoints_relative = get_relative_keypoints(keypoints, w, h)
            line = str(label)
            for x in keypoints_relative:
                line += ' ' + str(x)
            f.write(line + '\n')


if __name__ == '__main__':
    # file = '../annotation/alone_class_checked/combine_sample/total_checked_samples.json'
    file = '../../keypoints_gt_classification/combine_sample/test.json'
    # file = '../post/revise_totalSamples2.json'
    get_txt(file)

