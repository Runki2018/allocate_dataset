import json
import os
import random
from tqdm import tqdm
from datetime import datetime

# 初始化样本信息
nc = 9  # number of classes
classes = ['0-其他', '1-OK', '2-手掌', '3-向上', '4-向下', '5-向右', '6-向左', '7-比心', '8-嘘']
person = 26  # number of annotator
# 定义各个目录：
label_dir = '../annotation/'  # 各人的标注文件所在目录
alone_class = 'alone_class/'  # 每个类别的样本按序号单独存储为一个标注文件
alone_class_checked = 'alone_class_checked/'  # 修改过关键点的各类标注文件所在目录

image1class_list = [[] for _ in range(nc)]  # 为每一类图片创建一个空列表,记录相应的 "images" 信息
annotation1class_list = [[] for _ in range(nc)]  # 为每一类图片创建一个空列表,记录相应的 "annotations" 信息


def split_sample():
    """按类别分离样本, 并生成相应的9个json文件"""
    vacancy = 0  # 未完成的标注的人数
    count_all_list = [0 for i in range(nc)]  # 记录每一类样本的总数
    count_list = [0 for i in range(nc)] # 记录每一类样本无标记模糊的总数
    # 分离样本、统计各类样本数
    for i in range(person):
        json_file = label_dir + str(i) + '.json'
        if not os.path.exists(json_file):
            print('json_file not exist !: {}'.format(json_file))
            vacancy += 1
            continue
        ann_json = json.load(open(json_file, 'r'))
        images_list = ann_json["images"]
        annotation_list = ann_json["annotations"]
        for index, image in enumerate(images_list):
            label = image["label"]  # 0~8
            blur = image["blur"]  # 0/1
            count_all_list[label] += 1
            if blur == 0:
                count_list[label] += 1
                image1class_list[label].append(image)
                annotation1class_list[label].append(annotation_list[index])

    print('-' * 50)
    print("完成的人数：{} /{}".format(person-vacancy, person))
    print("已获取的样本总数： {} /{}".format(sum(count_list), sum(count_all_list)))
    print('-' * 50)
    # 保存各类样本的标注文件
    for i in range(nc):
        print("类别 {0}\t的数量为 {1}/{2},  {3:.4}% ".
              format(classes[i], count_list[i], count_all_list[i], count_list[i]/count_all_list[i]*100))
        template_file = label_dir + 'template.json'  # 模板标注文件
        template = json.load(open(template_file, 'r'))
        template["images"] = image1class_list[i]
        template["annotations"] = annotation1class_list[i]
        # 保存日期和类别：
        time = str(datetime.now()).split('-')  # ['2021', '03', '16 15:56:45.784162']
        time[2] = time[2].split(' ')[0]  # ['2021', '03', '16']
        template['info']["year"] = time[0]
        template['info']["date_created"] = time[0] + '/' + time[1] + '/' + time[2]
        template['info']['description'] = 'ZHhand: ' + classes[i]
        # save
        save_dir = label_dir + alone_class
        save_file = save_dir + str(i) + '.json'
        if not os.path.exists(save_dir):
            os.mkdir(save_dir)
        json.dump(template, open(save_file, 'w'), indent=4)


def pick_checked():
    """ 进一步细分，挑选出修改过关键点的图片"""
    print("-" * 50)
    print("pick_checked()")
    print("-" * 50)
    sum_checked = 0
    for i in range(nc):
        images_list = image1class_list[i]
        annotation_list = annotation1class_list[i]
        new_list = [[], []]  # [images, annotations]
        for index in range(len(images_list)):
            check_state = images_list[index]["CheckState"]
            if check_state == "Checked":
                sum_checked += 1
                new_list[0].append(images_list[index])
                new_list[1].append(annotation_list[index])

        print("类别 {}\t的数量为 {} ".format(classes[i], len(new_list[0])))
        # save
        json_file = label_dir + alone_class + str(i) + ".json"
        ann = json.load(open(json_file, 'r'))
        ann["images"] = new_list[0]
        ann["annotations"] = new_list[1]
        save_dir = label_dir + alone_class_checked
        if not os.path.exists(save_dir):
            os.mkdir(save_dir)
        save_file = save_dir + str(i) + ".json"
        json.dump(ann, open(save_file, "w"), indent=4)
    print("number of checked sample = {}".format(sum_checked))


def combine_sample(annotation_dir: str):
    """将样本集合并"""
    images_list = []
    annotations_list = []
    for file_name in tqdm(os.listdir(annotation_dir)):
        if file_name.split('.')[-1] != 'json':
            continue
        file = annotation_dir + file_name
        ann = json.load(open(file, 'r'))
        images_list.extend(ann["images"])
        annotations_list.extend(ann["annotations"])

    template_file = label_dir + 'template.json'  # 模板标注文件
    template = json.load(open(template_file, 'r'))
    template["images"] = images_list
    template["annotations"] = annotations_list
    # 保存日期和类别：
    time = str(datetime.now()).split('-')  # ['2021', '03', '16 15:56:45.784162']
    time[2] = time[2].split(' ')[0]  # ['2021', '03', '16']
    template['info']["year"] = time[0]
    template['info']["date_created"] = time[0] + '/' + time[1] + '/' + time[2]
    template['info']['description'] = 'ZHhand'
    # save
    save_dir = annotation_dir + "combine_sample/"
    save_file = save_dir + "total_checked_samples.json"
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)
    json.dump(template, open(save_file, 'w'), indent=4)
    return save_file, save_dir


def get2set(json_file: str, ratio: float, save_dir: str):
    """获取训练集和测试集,:
    json_file: str -> 将被划分为两部分的原数据集标注文件
    ratio: float -> 训练集的占比 0~1
    save_dir: str -> 保存标注文件的目录
    """
    ann = json.load(open(json_file, 'r'))
    images_list = ann["images"]
    annotations_list = ann["annotations"]
    train = [[], []]  # images, annotations
    test = [[], []]
    index_list = [i for i in range(len(images_list))]  # 0~len(images)
    random.shuffle(index_list)  # 打乱序号，随机分配训练和测试数据集
    nt = int(len(images_list) * ratio)  # number of train dataset
    for i, index in tqdm(enumerate(index_list)):
        if i < nt:
            train[0].append(images_list[index])
            train[1].append(annotations_list[index])
        else:
            test[0].append(images_list[index])
            test[1].append(annotations_list[index])

    print("train sample:{}".format(len(train[0])))
    print("test sample:{}".format(len(test[0])))
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)
    ann["images"] = train[0]
    ann["annotations"] = train[1]
    save_file = os.path.join(save_dir, "../../keypoints_gt_classification/combine_sample/train.json")
    json.dump(ann, open(save_file, "w"), indent=4)

    ann["images"] = test[0]
    ann["annotations"] = test[1]
    save_file = os.path.join(save_dir, "../../keypoints_gt_classification/combine_sample/test.json")
    json.dump(ann, open(save_file, "w"), indent=4)


if __name__ == '__main__':
    # 处理从各人手里拿到的标注文件
    # split_sample()  # 将26人的标注文件合并，然后根据手势类别分成9个标注文件
    # pick_checked()  # 将修改过关键点的样本挑选出来， 同样生成9个标注文件
    # ann_dir = label_dir + alone_class_checked
    # file, save_dir = combine_sample(ann_dir)  # 将9个标注文件合并成一个

    file = "./revise_totalSamples2.json"
    save_dir = "./"
    # 处理完标注文件后，将最终的标注分成测试集和训练集
    get2set(file, 0.8, save_dir)  # 将标注文件按照比例分成训练集和测试集。


