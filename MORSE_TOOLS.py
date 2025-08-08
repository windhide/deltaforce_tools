import cv2
import keyboard
import mss
import numpy as np
import time

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

resolution_config_map = {
    "1080P":{
        "top": 380,
        "bottom": 420,
        "group_width": 140,
        "spacing": 60,
        "group1_x": 530
    },
    "2K":{
        "top":  510,
        "bottom":  570,
        "group_width":  200,
        "spacing":  65,
        "group1_x":  700
    },
    "4K":{
        "top":  780,
        "bottom":  850,
        "group_width":  320,
        "spacing":  70,
        "group1_x":  1050
    }
}

def screenshot_game_and_sendCode(morse_config=None):
    try:
        with mss.mss() as sct:
            monitor = sct.monitors[1]  # 主屏幕
            sct_img = sct.grab(monitor)
            img2 = np.array(sct_img)

            # 转换为灰度图（只保留亮度）
            _gray = cv2.cvtColor(img2, cv2.COLOR_BGRA2GRAY)
            _morse_codes, _digits = extract_three_groups_and_decode(_gray, method="simple_cluster", config=morse_config)

            # 检查 _morse_codes 是否为空，如果为空则打印警告但不直接返回
            if not all(_morse_codes):
                print("⚠️ 警告: 摩斯码识别结果为空或部分为空，可能未识别到有效信息。")

            # 过滤掉无效的数字（例如 '?'）
            valid_digits = [d for d in _digits if d != '?']

            if valid_digits:
                print(f"✅ 准备发送数字: {valid_digits}")
                for digit in valid_digits:
                    try:
                        # 确保只发送有效的数字键
                        if digit.isdigit():
                            keyboard.send(f"num {digit}")
                            time.sleep(0.06)
                        else:
                            print(f"⚠️ 警告: 识别到无效字符 '{digit}'，已跳过发送。")
                    except Exception as e:
                        print(f"❌ 发送按键 '{digit}' 时发生错误: {e}")
                print(f"✅ 成功发送数字: {valid_digits}")
            else:
                print("❌ 未识别到任何有效数字可发送。")

    except Exception as ex:
        print(f"❌ 截图或摩斯码识别过程中发生错误: {ex}")


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
    if len(lengths) > 5:
        print("⚠️ 警告: 识别到的线段数量过多，可能为噪声。")
        return '', binary

    if method == 'kmeans':
        from sklearn.cluster import KMeans
        data = np.array(lengths).reshape(-1, 1)
        # 尝试使用 n_init='auto' 或明确指定 n_init
        kmeans = KMeans(n_clusters=2, n_init=10, random_state=0).fit(data)
        centers = kmeans.cluster_centers_
        labels = kmeans.labels_

        # 确保 dot_label 总是指向较小的中心
        dot_label = np.argmin(centers)
        dash_label = np.argmax(centers)

        # 如果两个中心非常接近，或者只有一个有效的簇，则全部视为点
        if abs(centers[0] - centers[1]) < 5 or len(np.unique(labels)) == 1:
            symbols = ['.' for _ in lengths]  # 全部视为点
        else:
            symbols = ['.' if label == dot_label else '-' for label in labels]

    elif method == 'simple_cluster':
        lengths_np = np.array(lengths)

        # 如果所有长度都相同或非常接近
        if np.std(lengths_np) < 3:  # 使用标准差判断是否为单一长度
            # 进一步判断这个单一长度是短线还是长线
            # 假设短线和长线有一个大致的比例关系，例如长线是短线的2-3倍
            # 我们可以根据所有线段长度的平均值或中位数来动态判断
            median_len = np.median(lengths_np)

            # 设定一个阈值，例如如果单一长度大于中位数的1.5倍，则认为是长线
            # 这个阈值可能需要根据实际情况调整
            # 这里的逻辑是：如果所有线段长度都一样，且这个长度相对较大，就认为是长线
            # 否则认为是短线
            if median_len > 20:  # 假设大于20像素的单一长度更可能是长线
                symbols = ['-' for _ in lengths]
            else:
                symbols = ['.' for _ in lengths]
        else:
            # 否则，进行聚类
            mean_len = lengths_np.mean()
            cluster1 = lengths_np[lengths_np <= mean_len]
            cluster2 = lengths_np[lengths_np > mean_len]

            center1 = cluster1.mean() if len(cluster1) > 0 else 0
            center2 = cluster2.mean() if len(cluster2) > 0 else 0

            # 确保 dot_label 总是指向较小的中心
            dot_label = 0 if center1 < center2 else 1
            symbols = []
            for l in lengths_np:
                label = 0 if abs(l - center1) < abs(l - center2) else 1
                symbols.append('.' if label == dot_label else '-')

    elif method == 'threshold':
        min_len = min(lengths)
        max_len = max(lengths)
        threshold_len = (min_len + max_len) / 2
        symbols = ['.' if l < threshold_len else '-' for l in lengths]

    else:
        raise ValueError("method 参数只能是 'kmeans', 'simple_cluster', 'threshold' 之一")

    return ''.join(symbols), binary


def extract_three_groups_and_decode(gray_img, method='kmeans', config=None):
    if config:
        top = config.get('top', 510)
        bottom = config.get('bottom', 570)
        group_width = config.get('group_width', 200)
        spacing = config.get('spacing', 65)
        group1_x = config.get('group1_x', 700)
    else:
        # 如果没有提供配置，则使用默认值
        top = 380
        bottom = 420
        group_width = 140
        spacing = 60
        group1_x = 530

    print(f"当前配置--- top->{top} bottom->{bottom} group->{group_width} spacing->{spacing} group1-x->{group1_x}")
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

    if config and config.get('debug', False):
        show_debug_window(gray_img, [(roi1, bin1, code1, num1),
                                 (roi2, bin2, code2, num2),
                                 (roi3, bin3, code3, num3)])

    return (code1, code2, code3), (num1, num2, num3)


def show_debug_window(gray, group_data):
    # 检查是否可以使用GUI功能
    can_show_gui = hasattr(cv2, 'imshow')

    if can_show_gui:
        h, w = gray.shape
        scale = 0.5
        resized = cv2.resize(gray, (int(w * scale), int(h * scale)))
        cv2.imshow("原图（灰度）", resized)

        for i, (roi, binary, code, digit) in enumerate(group_data):
            cv2.imshow(f"{i + 1}-original", roi)
            cv2.imshow(f"{i + 1}-debug", binary)

    # 无论如何都打印信息到控制台
    for i, (roi, binary, code, digit) in enumerate(group_data):
        print(f"区域{i + 1} 摩斯码: {code} → 数字: {digit}")

    print("按任意键退出调试窗口...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":

    start_time = time.time()

    img = cv2.imread("screenshot_delta_force_tools_20250805_223823.png")
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
    for number in digits:
        print(number)

    end_time = time.time()
    print(f"\n执行耗时：{end_time - start_time:.3f} 秒")




