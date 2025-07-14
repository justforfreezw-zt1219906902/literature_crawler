from PIL import Image
import numpy as np

def remove_black_border(image_path, output_path):
    # 打开图片
    img = Image.open(image_path)

    # 将图片转换为 NumPy 数组
    img_array = np.array(img)

    # 获取图片的宽度和高度
    height, width, _ = img_array.shape

    # 初始化边界
    top, bottom, left, right = 0, height - 1, 0, width - 1


    # 寻找非黑色像素的边界

    while np.all(img_array[top] == [14, 14 ,14]):

        top += 1
    while np.all(img_array[bottom] == [14, 14 ,14]):
        bottom -= 1
    while np.all(img_array[:, left] == [14, 14 ,14]):
        left += 1
    while np.all(img_array[:, right] == [14, 14 ,14]):
        right -= 1


    # 裁剪图片
    cropped_img = img.crop((left, top, right, bottom))

    # 保存裁剪后的图片
    cropped_img.save(output_path)

# 图片路径
if __name__ == '__main__':
    image_path = './pic/page_screenshot1.jpg'
    output_path = './pic/page_screenshot1-1.jpg'

    # 去除黑边并保存
    remove_black_border(image_path, output_path)