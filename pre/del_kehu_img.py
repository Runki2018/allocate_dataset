import os
import cv2
from tqdm import tqdm


def find_800x1024():
    """normal image.shape = (1024,800,3)
        error image.shape = (720,1280,3)
    """
    img_path = '../JPEGImages/'
    # read total file prefix file
    txt_path = './total.txt'
    # save file prefix file respectively for 1024x800 images and the other images
    txt_1024x800 = './total_1024x800.txt'
    txt_other = './other.txt'
    img_1024x800 = []
    img_other = []
    with open(txt_path, 'r') as fd:
        for line in tqdm(fd.readlines()):
            file_prefix = line.strip().strip('\n')
            if file_prefix == '':
                continue
            file_path = img_path + file_prefix + '.jpg'
            img = cv2.imread(file_path)
            h, w, _ = img.shape
            if h == 1024 and w == 800:
                img_1024x800.append(file_prefix+'\n')
            else:
                img_other.append(file_prefix+'\n')
    with open(txt_1024x800, 'w') as fd:
        for line in tqdm(img_1024x800):
            fd.write(line)
    with open(txt_other, 'w') as fd:
        for line in tqdm(img_other):
            fd.write(line)


if __name__ == '__main__':
    find_800x1024()
