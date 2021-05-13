import json
import os
import xmltodict
import copy


class pointMapping:
    """将截取图中关键点映射回原图"""
    save_dir = './annotations_mapping/'  # 运行程序前记得先删除该目录
    # save_txt = './file_prefix.txt'

    def __init__(self, annotation, xml_dir, img_dir, image_id=0):
        """

        @param annotaion: json 标注文件
        @param xml_dir:  所有原图xml文件所在目录
        @param img_dir:  所有原图所在目录
        """
        super(pointMapping, self).__init__()
        self.xml_dir = xml_dir
        self.img_dir = img_dir
        self.image_id = image_id  # 原图ID,从0开始编码

        self.json_file = json.load(open(annotation, 'r'))  # json标注文件
        self.images_list = self.json_file["images"]
        self.annotations_list = self.json_file["annotations"]
        self.json_file["images"] = []
        self.json_file["annotations"] = []
        self.index = 0  # 当前的截取图image和annotation列表的元素序号

        self.filename = ''  # 截取图图片路径，eg: ./path_prefix/ID_filename_prefix.jpg
        self.filename_prefix = ''  # 文件前缀名, 用于匹配xml和原图: filename_prefix
        self.objectID = ''  # 每个截取图对于一个ID，图片命名方式：ID_filename_prefix.jpg
        self.label = 0  # 手的类别标签
        self.occlusion = 1  # 手的遮挡指标
        self.blur = 0  # 手的模糊指标
        self.wh_target = 0  # 截取图像的目标宽高，其不能大于原图像宽高，其常见取值有224、256等

        self.box_dict = {}  # 原图XML中的bbox
        self.box_xywh = []  # 通过原图XML中的bbox得到的bbox左上角坐标和宽高
        self.size = []  # 原图宽高， w, h

    def xml2json(self):
        xml_file = os.path.join(self.xml_dir, self.filename_prefix + '.xml')
        with open(xml_file, 'r') as fd:
            xml_str = fd.read()
        xml_parse = xmltodict.parse(xml_str)  # xml -> python OrderedDict
        json_str = json.dumps(xml_parse, indent=4)  # xml字符串 转换成 json字符串
        json_dict = json.loads(json_str)  # json字符串 转换成 字典
        return json_dict

    def getObjectIndex(self, json_dict):
        """获取当前截取图属于xml标注中的哪一个object的序号"""
        # 循环查找当前ID的截取图原图是否有ID值更小的截取图，来判断当前ID所对应的XML标注中的object序号
        object_index = 0  # 默认序号为0
        pre_objectID = int(self.objectID) - 1  # 查看原图是否有object_id更小的截取图
        img_name = str(pre_objectID) + '_' + self.filename_prefix + '.jpg'
        path_prefix = self.filename.split(self.objectID)[0]
        img = path_prefix + img_name
        while os.path.exists(img):
            object_index += 1
            pre_objectID -= 1
            img_name = str(pre_objectID) + '_' + self.filename_prefix + '.jpg'
            img = os.path.join(path_prefix, img_name)
        return object_index

    def read_xml(self):
        """读取原图的xml标注，获取原图size、bbox、label等信息"""
        json_dict = self.xml2json()
        width, height = json_dict["annotation"]["size"]["width"], json_dict["annotation"]["size"]["height"]
        self.size = [width, height]
        if type(json_dict["annotation"]["object"]) == dict:
            #  xml中只有一个"object"，即只有一只手的时候为字典
            self.label = json_dict["annotation"]["object"]["name"]  # 手势的类别标签
            self.box_dict = json_dict["annotation"]["object"]["bndbox"]
        else:
            #  xml中有两个"object"，即有两个只手的时候为列表,列表中每一个元素是一个字典
            n_hand = len(json_dict["annotation"]["object"])
            index = self.getObjectIndex(json_dict)
            assert 0 <= index < n_hand, "error: hand index is not in the range of the number of hands!"
            self.label = json_dict["annotation"]["object"][index]["name"]
            self.box_dict = json_dict["annotation"]["object"][index]["bndbox"]

    def get_original_xywh(self):
        """根据原图bbox的左上角坐标和box宽高 计算截取图在原图的左上角坐标和宽高"""
        bbox = self.box_dict
        lx, ly, rx, ry = bbox["xmin"], bbox["ymin"], bbox["xmax"], bbox["ymax"]
        lx, ly, rx, ry = int(lx), int(ly), int(rx), int(ry)
        w, h = rx - lx, ry - ly
        self.box_xywh = []
        self.box_xywh.extend([lx, ly, w, h])
        # lx_square, ly_square, wh  # 截取图对应在原图上的方形区域左上角坐标和边长
        if w > self.wh_target or h > self.wh_target:
            if w > h:
                dy = int((w - h) / 2)
                lx_square, ly_square, wh = lx, ly - dy, w
            else:
                dx = int((h - w) / 2)
                lx_square, ly_square, wh = lx - dx, ly, h
        else:
            dx = int((self.wh_target - w) / 2)
            dy = int((self.wh_target - h) / 2)
            lx_square, ly_square, wh = lx - dx, ly - dy, self.wh_target
        return lx_square, ly_square, wh

    def init_info(self):
        """读入当前截取图标注信息"""
        self.filename = self.images_list[self.index]["file_name"]
        self.filename_prefix = self.filename.split('/')[-1]  # 去除目录部分
        self.objectID, self.filename_prefix = self.filename_prefix.split('_', 1)
        self.filename_prefix = self.filename_prefix.split('.jpg')[0]
        self.wh_target = self.images_list[self.index]["width"]
        self.occlusion = self.images_list[self.index]["occlusion"]
        self.blur = self.images_list[self.index]["blur"]

    def mapping(self):
        # 1、 将截取图根据原图上的bounding box的映射回原图上
        n_object = len(self.images_list)
        while self.index < n_object:
            self.init_info()
            self.read_xml()
            x0, y0, wh0 = self.get_original_xywh()
            scale_ratio = self.wh_target / wh0
            keypoints = self.annotations_list[self.index]["keypoints"]
            new_keypoints = []
            for i in range(0, len(keypoints), 3):
                x_k = keypoints[i] // scale_ratio + x0
                y_k = keypoints[i + 1] // scale_ratio + y0
                c = 1
                new_keypoints.extend([x_k, y_k, c])
            self.save_alone(new_keypoints)
            self.index += 1

    def save_alone(self, keypoints):
        """将映射结果根据原图名，单独保存一个json"""

        if not os.path.exists(self.save_dir):
            os.mkdir(self.save_dir)
        save_file = self.save_dir + self.filename_prefix + '.json'
        if not os.path.exists(save_file):
            # 该原图，没有保存过截取图映射，则新建一个json
            img_name = self.img_dir + self.filename_prefix + '.jpg'
            template = copy.deepcopy(self.json_file)
            image_dict = {"file_name": img_name, "height": self.size[1], "width": self.size[0], "id": self.image_id}
            template["images"] = image_dict
            self.image_id += 1
        else:
            template = json.load(open(save_file, 'r'))  # 追加截取图映射, 不用新建原图信息
        annotation_dict = {"bbox": self.box_xywh, "keypoints": keypoints,
                           "category_id": self.label, "object_id": self.objectID,
                           "occlusion": self.occlusion, "blur": self.blur}
        template["annotations"].append(annotation_dict)
        json.dump(template, open(save_file, 'w'), indent=4)


if __name__ == '__main__':
    ann = './test.json'
    xml_dir = img_dir = './original_data/'
    pm = pointMapping(ann, xml_dir, img_dir)
    pm.mapping()

