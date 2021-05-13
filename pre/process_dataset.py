import copy
import json
import xmltodict
import os
import cv2 as cv
from tqdm import tqdm


class process_dataset:
    """
    1、将XML标注转化成JSON标注
    2、将一张图片中所标注的所有手部实例，单独裁剪成大小为目标宽高的图像。
    3、对于一个图像实例，若其边界框宽高小于目标宽高，则对其进行缩放逐渐逼近目标宽高，获得指定缩放次数张图像。
    """
    image_id = 0  # 保存图像的id, 由于我们将图像中每一只单独保存，因此实例ID = 图像ID
    # last_image_id = -1  # 上一次保存的图像ID
    object_id = 0  # 手部实例的id，一张图像可能有多个手部实例
    wh_target = 256  # 待截取图像的目标宽高，其不能大于图像宽高，其常见取值有224、256等
    display = False  # 显示截取区域的动画, 调试时使用，用于判断边界框位置是否正确

    def __init__(self):
        self.img_path = ""  # 图片路径
        self.img = None  # 图片文件
        self.change_count = 1  # 保存图片的尺度变化次数——生成一个新的文件夹单独保存
        self.box_dict = {}  # xml边界框字典
        self.template = {}  # COCO标注格式的模板
        self.image = {}  # 图片标注
        self.label = 0  # 手势的类别标签，为int型
        self.annotation = {}
        self.root = 'current saving direction'
        self.old_root = 'old_root to record the last self.root'
        self.label_file = 'label.json'  # the label file name for saving json

    @staticmethod
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
        cv.namedWindow("FreiHand")
        cv.imshow('FreiHand', img)
        cv.waitKey(1000)  # 单位ms, 显示 1000 ms 即 1s 后消失
        cv.destroyAllWindows()

    @staticmethod
    def get_w_h_a(lx, ly, rx, ry):
        """ 获取宽、高、面积 """
        width, height = rx - lx, ry - ly
        area = width * height
        print(width, height, area)  # w, h , area
        return width, height, area

    def get_scale_img(self, xml_file, img_path, change_count=1, root=''):
        """
        获取缩放的图片以及相应的手部框位置，并保存json标注文件
        :param xml_file: 图片标注xml文件的路径
        :param img_path: 图片路径
        :param change_count:  保存图片的尺度变化次数——生成一个新的文件夹单独保存
        :param root: direction for saving images and annotations
        :return:
        """
        self.img_path = img_path
        self.change_count = change_count
        self.old_root = self.root
        self.root = root

        with open(xml_file, 'r') as fd:
            xml_str = fd.read()
            # print(xml_str)
        xml_parse = xmltodict.parse(xml_str)  # xml -> python OrderedDict
        json_str = json.dumps(xml_parse, indent=4)  # xml字符串 转换成 json字符串
        json_dict = json.loads(json_str)  # json字符串 转换成 字典
        # print('-'*50)   # 观察 XML标注的内容与格式
        # print(xml_parse)
        # print(json_str)
        # print('-' * 50)

        # 读入图片
        self.img = cv.imread(self.img_path)
        print("original shape = ", self.img.shape)

        # 读入边界框的左上角和右下角两个点的坐标
        if type(json_dict["annotation"]["object"]) == dict:
            #  xml中只有一个"object"，即只有一只手的时候为字典
            self.label = json_dict["annotation"]["object"]["name"]  # 手势的类别标签
            self.box_dict = json_dict["annotation"]["object"]["bndbox"]
            self.handleSingleBox()
        else:
            #  xml中有两个"object"，即有两个只手的时候为列表,列表中每一个元素是一个字典
            n_hand = len(json_dict["annotation"]["object"])
            for i in range(n_hand):
                self.label = json_dict["annotation"]["object"][i]["name"]
                self.box_dict = json_dict["annotation"]["object"][i]["bndbox"]
                self.handleSingleBox()
        self.image_id += 1

    def handleSingleBox(self):
        bbox = self.box_dict
        lx, ly, rx, ry = bbox["xmin"], bbox["ymin"], bbox["xmax"], bbox["ymax"]
        lx, ly, rx, ry = int(lx), int(ly), int(rx), int(ry)
        w, h, _ = self.get_w_h_a(lx, ly, rx, ry)  # 边界框的宽、高、面积

        # 画出边界框，展示当前要截取的区域1s，用于调试，在正式截取时，需要将display标记设为假。
        if self.display:
            self.draw_bbox(self.img, lx, ly, rx, ry)

        # 读取标注文件-
        if self.root != self.old_root:
            """处理第一个图像实例时，先读取标注格式的模板"""
            self.template = json.load(open("../annotation/template.json", 'r'))
            # 获取图片描述和标注的格式
            self.image = self.template["images"][0]
            self.annotation = self.template["annotations"][0]
            # 清空原来的标注信息
            self.template["images"] = []
            self.template["annotations"] = []
        else:
            """处理之后的图片，追加到上一次保存的标注结果"""
            label_file = self.root + self.label_file
            with open(label_file, 'r') as fd:
                self.template = json.load(fd)
            self.image = self.template["images"][-1]
            self.annotation = self.template["annotations"][-1]

        # 保存截取区域的图像和标注
        if w > self.wh_target or h > self.wh_target:
            self.moreThanTarget(w, h, lx, ly, rx, ry)
        else:
            self.lessThanTarget(w, h, lx, ly, rx, ry)
        label_file = self.root + "label.json"
        json.dump(self.template, open(label_file, "w"), indent=4)  # 每次以写打开json文件，会自动清空原文件的内容
        print("length of images = ", len(self.template["images"]))
        print("length of annotations = ", len(self.template["annotations"]))

    def moreThanTarget(self, w, h, lx, ly, rx, ry):
        """当bbox的宽高大于裁剪区的目标宽高时,裁剪一个正方形再缩小成目标宽高"""
        if w > h:
            dy = int((w - h) / 2)
            # 通过bbox坐标计算截取图的左上角和右下角坐标
            x_start, x_end, y_start, y_end = lx, rx, ly - dy, ry + dy
            crop_img = self.img[y_start:y_end, x_start:x_end]  # 从原图中裁剪出来的部分
        else:
            dx = int((h - w) / 2)
            # 通过bbox坐标计算截取图的左上角和右下角坐标
            x_start, x_end, y_start, y_end = lx - dx, rx + dx, ly, ry
            crop_img = self.img[y_start:y_end, x_start:x_end]  # 从原图中裁剪出来的部分

        # 检查和创建相关文件夹
        save_dir = self.root + 'img_0'  # 保存图像的目录 RS = resize
        save_filename = str(self.object_id) + '_' + self.img_path.split('.')[-2].split('/')[-1] \
                        + '.jpg'  # 图像名:最开始的数字为 实例ID，也是annotations列表的下标。
        mksavedir = os.path.join(os.getcwd(), save_dir)
        if not os.path.exists(mksavedir):
            os.mkdir(mksavedir)  # 判断文件夹是否存在，不存在则创建文件夹——用于保存裁剪图片
        save_path = save_dir + "/" + save_filename  # 最终的文件保存路径
        # 保存缩放图
        resize_img = cv.resize(crop_img, (self.wh_target, self.wh_target))
        cv.imwrite(save_path, resize_img)
        # 深拷贝：申请新的内存空间，否则最后添加的所有字典都是一样的，为最后一个元素
        self.image = copy.deepcopy(self.image)
        self.annotation = copy.deepcopy(self.annotation)
        # 添加新的标注信息
        self.image["file_name"] = save_path
        self.image["original_id"] = self.image_id  # 记录原图像ID
        self.image["id"] = self.object_id  # 截取图的图像ID = 实例ID
        self.image["width"] = self.wh_target
        self.image["height"] = self.wh_target
        self.image["label"] = int(self.label)
        self.annotation["category_id"] = int(self.label)
        self.annotation["bbox"] = [0, 0, self.wh_target - 1, self.wh_target - 1]
        self.annotation["id"] = self.object_id  # 手部实例ID
        self.annotation["image_id"] = self.object_id  # 图像ID
        self.annotation["area"] = self.wh_target * self.wh_target
        print("object id = ", self.object_id)
        self.object_id += 1  # 每次处理完一个手部实例，ID自增
        # 通过追加的方式，保存标注信息
        self.template["images"].append(self.image)
        self.template["annotations"].append(self.annotation)

    def lessThanTarget(self, w, h, lx, ly, rx, ry):
        """当bbox的宽高小于裁剪区的目标宽高时"""
        # 计算bbox左上角/右下角与截取图左上角/右下角的x/y方向的偏差
        dx = int((self.wh_target - w) / 2)
        dy = int((self.wh_target - h) / 2)
        # 通过bbox坐标计算截取图的左上角和右下角坐标
        [x_start, x_end, y_start, y_end] = [lx - dx, rx + dx, ly - dy, ry + dy]

        # 由于dx,dy直接去除小数部分，可能最后得到的图不是目标宽高，因此需要修正
        if x_end - x_start == self.wh_target - 1:
            x_end += 1
        if y_end - y_start == self.wh_target - 1:
            y_end += 1

        # 防止越界
        img_h, img_w, _ = self.img.shape  # (h,w,c)   # 原图的高和宽
        if x_start < 0:
            x_start, x_end = 0, self.wh_target
        if y_start < 0:
            y_start, y_end = 0, self.wh_target
        if x_end > img_w:
            x_start, x_end = img_w - self.wh_target, img_w
        if y_end > img_h:
            y_start, y_end = img_h - self.wh_target, img_h

        # print(x_start, x_end, y_start, y_end)
        crop_img = self.img[y_start:y_end, x_start:x_end]
        print("裁剪的图像 shape = ", crop_img.shape)
        # 获取首次截取目标宽高的图像中，手部所在的新bbox = x, y, w, h, 其中w, h 已经获取
        x, y = lx - x_start, ly - y_start

        # 保存多个尺度的放缩图和标注信息
        for i in range(self.change_count):
            Dx = int(i / self.change_count * dx)
            Dy = int(i / self.change_count * dy)
            y_start, y_end, x_start, x_end = Dy, self.wh_target - Dy, Dx, self.wh_target - Dx
            crop_img_i = crop_img[y_start:y_end, x_start:x_end]

            # 检查和创建相关文件夹
            save_dir = self.root + 'img_' + str(i)  # 保存图像的目录 RS = resize
            save_filename = str(self.object_id) + '_' + self.img_path.split('.')[-2].split('/')[-1] \
                            + '.jpg'  # 图像名:最开始的数字为 实例ID，也是annotations列表的下标。
            mksavedir = os.path.join(os.getcwd(), save_dir)
            if not os.path.exists(mksavedir):
                os.mkdir(mksavedir)  # 判断文件夹是否存在，不存在则创建文件夹——用于保存裁剪图片
            save_path = save_dir + "/" + save_filename  # 最终的文件保存路径

            # cv.imwrite(img_save_path, crop_img_i)  #  保存不放缩前的截图
            shape_h, shape_w, _ = crop_img_i.shape
            dw = self.wh_target / shape_w
            dh = self.wh_target / shape_h
            x_new, y_new, w_new, h_new = int(dw * (x - Dx)), int(dh * (y - Dy)), int(dw * w), int(dh * h)
            resize_img = cv.resize(crop_img_i, (self.wh_target, self.wh_target))
            cv.imwrite(save_path, resize_img)  # 保存缩放图

            # 深拷贝：申请新的内存空间，否则最后添加的所有字典都是一样的，为最后一个元素
            self.image = copy.deepcopy(self.image)
            self.annotation = copy.deepcopy(self.annotation)
            # 添加新的标注信息
            self.image["file_name"] = save_path
            self.image["original_id"] = self.image_id  # 记录原图像ID
            self.image["id"] = self.object_id  # 截取图的图像ID = 实例ID
            self.image["width"] = self.wh_target
            self.image["height"] = self.wh_target
            self.image["label"] = int(self.label)
            self.annotation["category_id"] = int(self.label)
            self.annotation["bbox"] = [x_new, y_new, w_new, h_new]
            self.annotation["id"] = self.object_id  # 手部实例ID
            self.annotation["image_id"] = self.object_id  # 图像ID
            self.annotation["area"] = w_new * h_new
            print("object id = ", self.object_id)
            self.object_id += 1  # 每次处理完一个手部实例，ID自增
            self.template["images"].append(self.image)
            self.template["annotations"].append(self.annotation)


if __name__ == "__main__":
    # data_path = "./datafile/3/"  # 存放要处理的ZHhand数据集路径
    # "/home/user/ln_home/data2/ZHhands/training_set/807/"
    img_path = "/home/user/ln_home/data2/ZHhands/JPEGImages/"
    xml_path = "/home/user/ln_home/data2/ZHhands/Annotations/"
    allocate_file_dir = './data/'
    start_index = 19
    person = 7
    tool = process_dataset()
    for index in range(start_index, start_index+person):
        root_dir = allocate_file_dir + str(index) + '/'
        print("root=", root_dir)
        prefix_file = os.listdir(root_dir)[0]  # '*.txt'
        print(prefix_file)
        with open(root_dir + prefix_file, 'r') as fd:
            print("allocate dataset for the person {}".format(index))
            for line in fd.readlines():
                line = line.strip('\n')
                print("file_prefix = ", line)
                xml = xml_path + line + '.xml'
                img = img_path + line + '.jpg'
                tool.get_scale_img(xml_file=xml, img_path=img, change_count=1, root=root_dir)
                print('=' * 60)
