import os
import random
from tqdm import tqdm


def allocate_data(file: str, na: int, nd: int, start_index=0):
    """
    用于生成相应的个人文件夹和txt文件，其包含该人的图片和xml文件前缀。

    :param file: txt file of image of prefix names
    :param na: number of annotator
    :param nd: number of data needed in this allocation
    :param start_index: direction name of personal dataset
    """
    save_path = './data/'
    file_prefix_list = []
    with open(file, 'r') as fd:
        for line in tqdm(fd.readlines()):
            line = line.strip().strip('\n')
            if line == '':
                continue
            file_prefix_list.append(line)
    random.shuffle(file_prefix_list)  # 对文件前缀列表 进行洗牌，打乱顺序
    # print('file list: ', file_prefix_list)
    file_prefix_list1 = []
    for x in tqdm(file_prefix_list):
        if x not in file_prefix_list1:
            file_prefix_list1.append(x)
    nf = len(file_prefix_list)  # number of file_prefix

    # calculate number of data for each person
    n_list = []
    for i in range(na):
        n = nd // na
        n_list.append(n)
    n_list[-1] += nd % na  # the last person has to add the remainder

    allocate_person = []
    for i in range(na):
        data_list = [file_prefix_list1.pop() for i in range(n_list[i])]
        allocate_person.append(data_list)

    # save
    if not os.path.exists(save_path):
        os.mkdir(save_path)
    for i in tqdm(range(start_index, start_index+na)):
        person_dir = save_path + str(i)
        if not os.path.exists(person_dir):
            os.mkdir(person_dir)
        save_file = person_dir + '/' + str(i) + '.txt'
        with open(save_file, 'w') as fd:
            for line in allocate_person[i-start_index]:
                fd.write(line + "\n")
    pending_file = save_path + 'pending.txt'
    with open(pending_file, 'w') as fd:
        for line in file_prefix_list1:
            fd.write(line+'\n')


if __name__ == '__main__':
    file_path = './pending.txt'
    index = 19
    person = 7
    amount = person * 300
    allocate_data(file_path, person, amount, start_index=index)
