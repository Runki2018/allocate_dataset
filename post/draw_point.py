import cv2 as cv
import os
import json


def draw_bbox(img, lx, ly, rx, ry):
    """
        画出边界框的位置

    :param img: cv读入的图片
    :param lx: 左上角点的 x 坐标值
    :param ly: 左上角点的 y 坐标值
    :param rx: 右下角点的 x 坐标值
    :param ry: 右下角点的 y 坐标值
    """
    leftTop = (lx, ly)  # 左上角的点坐标 (x,y)
    rightBottom = (rx, ry)  # 右下角的点坐标= (x+w,y+h)
    point_color = (0, 0, 255)  # BGR
    thickness = 1
    lineType = 8
    cv.rectangle(img, leftTop, rightBottom, point_color, thickness, lineType)


def draw_point(img, keypoints):
    points_list = []
    for i in range(0, len(keypoints), 3):
        point = int(keypoints[i]), int(keypoints[i + 1])  # (xi, yi)
        points_list.append(point)
    color_list = [(255, 0, 0), (0, 255, 255), (255, 0, 255), (255, 140, 0), (0, 0, 255), (0, 255, 0)]  # RGB
    for i, (r, g, b) in enumerate(color_list):
        color_list[i] = (b, g, r)  # BGR
    point_size = 1
    thickness = 4  # 可以为 0 、4、8
    for i in range(0, 21):
        if i == 0:
            cv.circle(img, points_list[i], point_size, color_list[i], thickness)
        else:
            index = (i - 1) // 4 + 1
            cv.circle(img, points_list[i], point_size, color_list[index], thickness)


if __name__ == '__main__':
    # 用于可视化关键点和bbox, 看从截取图映射会原图的参数是否正确
    # ann_dir = './annotations_mapping/'  # 运行程序前记得先删除该目录
    # window_name = "ZHHand"
    # cv.namedWindow(window_name, cv.WINDOW_FREERATIO)
    # for file in os.listdir(ann_dir):
    #     extended_name = file.split('.')[-1]
    #     if not extended_name == 'json':
    #         continue
    #     file = ann_dir + file
    #     json_dict = json.load(open(file, 'r'))
    #     annotations_list = json_dict["annotations"]
    #     img_file = json_dict["images"]["file_name"]
    #     img = cv.imread(img_file)
    #     for annotation in annotations_list:
    #         keypoints = annotation["keypoints"]
    #         x, y, w, h = annotation["bbox"]
    #         draw_bbox(img, x, y, x + w, y + h)
    #         draw_point(img, keypoints)
    #     cv.imshow(window_name, img)
    #     cv.waitKey(1000)  # 单位ms, 显示 1000 ms 即 1s 后消失
    # cv.destroyAllWindows()

    # 单一图片测试：
    ann_dir = './annotations_mapping/'  # 运行程序前记得先删除该目录
    file = ann_dir + "hand_det_before_840_init.json"
    window_name = "ZHHand"
    cv.namedWindow(window_name, cv.WINDOW_FREERATIO)
    json_dict = json.load(open(file, 'r'))
    annotations_list = json_dict["annotations"]
    img_file = json_dict["images"]["file_name"]
    img = cv.imread(img_file)
    for annotation in annotations_list:
        keypoints = annotation["keypoints"]
        x, y, w, h = annotation["bbox"]
        draw_bbox(img, x, y, x + w, y + h)
        draw_point(img, keypoints)
    cv.imshow(window_name, img)
    cv.waitKey(0)  # 单位ms, 显示 1000 ms 即 1s 后消失
    cv.destroyAllWindows()
