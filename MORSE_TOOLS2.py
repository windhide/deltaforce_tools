import cv2
import numpy as np

MORSE_CODE_DICT = {
    '-----': '0',
    '.----': '1',
    '..---': '2',
    '...--': '3',
    '....-': '4',
    '.....': '5',
    '-....': '6',
    '--...': '7',
    '---..': '8',
    '----.': '9'
}

def decode_morse_from_image(image, method='kmeans'):
    _, binary = cv2.threshold(image, 86, 255, cv2.THRESH_BINARY)
    projection = np.sum(binary, axis=0)
    threshold = 1
    bars = []
    is_bar = False
    start = 0
    for i, val in enumerate(projection):
        if val > threshold:
            if not is_bar:
                is_bar = True
                start = i
        else:
            if is_bar:
                is_bar = False
                end = i
                bars.append((start, end))

    if not bars:
        print("❌ 未识别到任何线段")
        return '', binary

    lengths = [end - start for start, end in bars]
    print("识别到的线段长度：", lengths)

    if method == 'kmeans':
        # sklearn KMeans
        from sklearn.cluster import KMeans
        data = np.array(lengths).reshape(-1, 1)
        kmeans = KMeans(n_clusters=2, n_init='auto').fit(data)
        centers = kmeans.cluster_centers_
        labels = kmeans.labels_
        dot_label = np.argmin(centers)
        symbols = ['.' if label == dot_label else '-' for label in labels]

    elif method == 'simple_cluster':
        # 简易两类聚类
        lengths_np = np.array(lengths)
        mean_len = lengths_np.mean()
        cluster1 = lengths_np[lengths_np <= mean_len]
        cluster2 = lengths_np[lengths_np > mean_len]
        center1 = cluster1.mean() if len(cluster1) > 0 else 0
        center2 = cluster2.mean() if len(cluster2) > 0 else 0
        dot_label = 0 if center1 < center2 else 1
        symbols = []
        for l in lengths_np:
            label = 0 if abs(l - center1) < abs(l - center2) else 1
            symbols.append('.' if label == dot_label else '-')

    elif method == 'threshold':
        # 简单阈值
        min_len = min(lengths)
        max_len = max(lengths)
        threshold_len = (min_len + max_len) / 2
        symbols = ['.' if l < threshold_len else '-' for l in lengths]

    else:
        raise ValueError("method 参数只能是 'kmeans', 'simple_cluster', 'threshold' 之一")

    return ''.join(symbols), binary


def extract_three_groups_and_decode(gray_img, method='kmeans'):
    h, w = gray_img.shape[:2]
    top = 160
    bottom = 200
    group_width = 170
    spacing = 35
    group1_x = 40
    group2_x = group1_x + group_width + spacing
    group3_x = group2_x + group_width + spacing

    roi1 = gray_img[top:bottom, group1_x:group1_x + group_width]
    roi2 = gray_img[top:bottom, group2_x:group2_x + group_width]
    roi3 = gray_img[top:bottom, group3_x:group3_x + group_width]

    code1, bin1 = decode_morse_from_image(roi1, method)
    code2, bin2 = decode_morse_from_image(roi2, method)
    code3, bin3 = decode_morse_from_image(roi3, method)

    num1 = MORSE_CODE_DICT.get(code1, '?')
    num2 = MORSE_CODE_DICT.get(code2, '?')
    num3 = MORSE_CODE_DICT.get(code3, '?')

    show_debug_window(gray_img, [(roi1, bin1, code1, num1),
                                 (roi2, bin2, code2, num2),
                                 (roi3, bin3, code3, num3)])

    return (code1, code2, code3), (num1, num2, num3)


def show_debug_window(gray, group_data):
    pass
    # h, w = gray.shape
    # scale = 0.5
    # resized = cv2.resize(gray, (int(w * scale), int(h * scale)))
    # cv2.imshow("原图（灰度）", resized)
    #
    # for i, (roi, binary, code, digit) in enumerate(group_data):
    #     cv2.imshow(f"区域{i + 1}-原图", roi)
    #     cv2.imshow(f"区域{i + 1}-二值", binary)
    #     print(f"区域{i + 1} 摩斯码: {code} → 数字: {digit}")
    #
    # print("按任意键退出调试窗口...")
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()


if __name__ == "__main__":
    import time
    start_time = time.time()

    img = cv2.imread("QQ20250805-114248.png")
    if img is None:
        print("无法读取图像")
        exit()

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 你可以在这里切换识别方法：
    method = 'simple_cluster'  # 'kmeans' / 'simple_cluster' / 'threshold'

    morse_codes, digits = extract_three_groups_and_decode(gray, method)
    print("\n最终结果：")
    print("摩斯码：", morse_codes)
    print("数字：", digits)

    end_time = time.time()
    print(f"\n执行耗时：{end_time - start_time:.3f} 秒")
