import json
import os


def strip_suffix():
    """# 将更改标注文件和相应的文件的后缀"""
    old_suffix = "_RS0.jpg"
    new_suffix = ".jpg"
    annotation = './test.json'
    json_file = json.load(open(annotation, 'r'))  # json标注文件
    images_list = json_file["images"]
    for i, img in enumerate(images_list):
        old_file_name = img["file_name"]
        new_file_name = old_file_name.split(old_suffix)[0] + new_suffix
        images_list[i]["file_name"] = new_file_name
        if os.path.exists(old_file_name):
            os.rename(old_file_name, new_file_name)
        print(old_file_name)
        print(" -> ", new_file_name)
        print('-'*50)
    json_file["images"] = images_list
    json.dump(json_file, open(annotation, 'w'), indent=4)


if __name__ == '__main__':
    strip_suffix()
    # fdir = './img_0/'
    # for file in os.listdir(fdir):
    #     print(file)
    #     old_f = fdir + file
    #     file = file.split('.jpg.jpg')[0] + '.jpg'
    #     new_f = fdir + file
    #     if os.path.exists(old_f):
    #         os.rename(old_f, new_f)
