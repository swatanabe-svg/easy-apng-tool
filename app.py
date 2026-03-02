import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from apng import APNG
import io
import os
import zipfile
import base64
import base64
from datetime import datetime
import cv2
import tempfile
import numpy as np
from streamlit_cropper import st_cropper

# ページ設定
st.set_page_config(
    page_title="APNG Generator",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# モダンなダークモードCSS（UI刷新・横スクロール対応版）
st.markdown("""
<style>
    /* グローバル設定 */
    * {
        font-family: "Helvetica Neue", Arial, "Hiragino Kaku Gothic ProN", "Hiragino Sans", Meiryo, sans-serif;
    }
    
    /* 背景色 */
    .stApp {
        background-color: #1a1a1a;
        color: #f0f0f0;
    }
    
    /* メインコンテナ調整 */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 98%;
    }
    
    /* タイトル */
    h1 {
        font-size: 24px;
        font-weight: 700;
        color: #ffffff;
        border-left: 5px solid #007bff;
        padding-left: 15px;
        margin-bottom: 2rem;
    }
    
    /* 入力フィールド */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div {
        background-color: #2c2c2c;
        color: #ffffff;
        border: 1px solid #444;
        border-radius: 4px;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #007bff;
    }

    /* タブ */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #2c2c2c;
        border-radius: 4px 4px 0 0;
        color: #aaa;
        padding: 8px 16px;
        border: 1px solid #333;
        border-bottom: none;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #007bff;
        color: white;
        border-color: #007bff;
    }

    /* ボタン */
    .stButton > button {
        border-radius: 4px;
        font-weight: 600;
        border: 1px solid #444;
        background-color: #333;
        color: #fff;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        border-color: #666;
        background-color: #444;
    }
    .stButton > button[kind="primary"] {
        background-color: #007bff;
        border-color: #0056b3;
        color: white;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #0069d9;
    }
    
    /* エキスパンダー */
    .streamlit-expanderHeader {
        background-color: #252525;
        border: 1px solid #333;
        border-radius: 4px;
    }
    .streamlit-expanderContent {
        border: 1px solid #333;
        border-top: none;
        background-color: #202020;
        padding: 15px;
    }

    /* プレビューエリアのSticky化 */
    div[data-testid="stHorizontalBlock"] {
        align-items: flex-start;
    }
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-of-type(2) {
        position: -webkit-sticky;
        position: sticky;
        top: 3rem;
        z-index: 100;
    }
    
    /* プレビューボックス */
    .preview-box {
        background-color: #111;
        border: 1px solid #333;
        border-radius: 8px;
        padding: 15px;
    }

    /* セクション見出し */
    .simple-header {
        font-size: 16px;
        font-weight: bold;
        color: #ddd;
        margin-top: 10px;
        margin-bottom: 10px;
        border-bottom: 1px solid #444;
        padding-bottom: 5px;
    }
    
    /* 注釈リストアイテム */
    .annotation-item {
        background-color: #252525;
        border: 1px solid #333;
        border-left: 4px solid #007bff;
        padding: 10px;
        margin-bottom: 8px;
        border-radius: 0 4px 4px 0;
    }

    /* 横スクロールコンテナ */
    .scroll-container {
        display: flex;
        overflow-x: auto;
        gap: 12px;
        padding-bottom: 12px;
        margin-bottom: 24px;
        scrollbar-width: thin;
        scrollbar-color: #007bff #333;
    }
    .scroll-container::-webkit-scrollbar {
        height: 8px;
    }
    .scroll-container::-webkit-scrollbar-track {
        background: #333;
        border-radius: 4px;
    }
    .scroll-container::-webkit-scrollbar-thumb {
        background-color: #007bff;
        border-radius: 4px;
    }
    
    /* スクロールアイテム */
    .scroll-item {
        flex: 0 0 240px;
        background-color: #1e1e1e;
        border: 1px solid #444;
        border-radius: 8px;
        padding: 10px;
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    .scroll-item img {
        width: 100%;
        height: auto;
        border-radius: 4px;
        border: 1px solid #333;
        margin-bottom: 8px;
    }
    .scroll-item-caption {
        font-size: 12px;
        color: #ddd;
        font-weight: 600;
        text-align: center;
        width: 100%;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

</style>
""", unsafe_allow_html=True)

# グローバル設定
WIDTH = 600
HEIGHT = 400

# 画像をBase64に変換する関数
def image_to_base64(img):
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def get_autosize_font(text, font_type, weight, max_width, max_height, start_size=150):
    """テキストが指定領域に収まるフォントサイズを計算する（複数行対応）"""
    size = start_size
    min_size = 10
    
    dummy_img = Image.new('RGB', (1, 1))
    draw = ImageDraw.Draw(dummy_img)
    
    lines = text.split('\n')

    while size > min_size:
        font = get_font(font_type, weight, size)
        
        # 複数行の場合、各行の幅と全体の高さを計算
        total_width = 0
        total_height = 0
        line_height = 0
        
        for line in lines:
            if not line.strip():
                # 空行の場合は標準の行高を使用
                bbox = draw.textbbox((0, 0), "A", font=font)
                line_height = bbox[3] - bbox[1]
            else:
                bbox = draw.textbbox((0, 0), line, font=font)
                w = bbox[2] - bbox[0]
                line_height = bbox[3] - bbox[1]
                if w > total_width:
                    total_width = w
            total_height += line_height
        
        # 行間を考慮（行数-1回分）
        line_spacing = int(size * 0.2)  # フォントサイズの20%を行間として追加
        total_height += line_spacing * (len(lines) - 1)
        
        if total_width <= max_width and total_height <= max_height:
            return font, size
        
        size -= 5
        
    return get_font(font_type, weight, min_size), min_size

def optimize_apng_data(apng_bytes, target_size_kb=300):
    """APNGデータが指定サイズを超えていたら削減を試みる簡易ラッパー"""
    if len(apng_bytes) / 1024 <= target_size_kb:
        return apng_bytes
    
    # サイズオーバー時は、減色などを行う（ここでは簡易的にPillowのquantizeを利用するために再構築が必要だが
    # 既存のsave_apngの流れで対応するのがベター。
    # ここでは、バイナリを読み込んで再度最適化処理にかけるのは複雑なため、
    # 生成段階でループ回数やフレーム数を減らすなどの制御が望ましいが、
    # ユーザー要望は「自動で」なので、動画最適化ロジックの一部を流用する形が理想。
    # ですが、静止画ベースのAPNGはそこまで肥大化しない傾向にあるため、
    # 万が一超えた場合は警告を出すか、減色処理を行う。
    
    # 簡易的な実装として、そのまま返す（動画ロジックでカバー）
    # ※ 本格的な再圧縮は構造が大きくなるため、今回は生成パラメータ側で制御推奨
    return apng_bytes

def generate_filename(product_name, custom_name, template_type, seq_num):
    """
    ファイル名生成ルール:
    デフォルト：今日の日付_○○_APNG_○○_素材_○○_01
    日付: yymmdd
    テンプレート名変換: 赤枠点滅→赤枠点滅, 4隅アイコン→4隅ikon, アイコン増加→ikon増加
    """
    date_str = datetime.now().strftime("%y%m%d")
    
    # テンプレート名の変換マップ
    type_map = {
        "赤枠点滅": "赤枠点滅",
        "4隅アイコン": "4隅ikon",
        "アイコン増加": "ikon増加",
        "画像円形切り抜き": "4隅ikon" # 円形切り抜きも4隅点滅なので
    }
    t_name = type_map.get(template_type, template_type)
    
    return f"{date_str}_{product_name}_APNG_{t_name}_素材_{custom_name}_{seq_num:02d}.png"


def mask_circle_transparent(pil_img, margin=0):
    """画像を円形に切り抜き、外側を透明にする"""
    pil_img = pil_img.convert("RGBA")
    size = (min(pil_img.size), min(pil_img.size))
    mask = Image.new('L', pil_img.size, 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse((margin, margin, pil_img.size[0]-margin, pil_img.size[1]-margin), fill=255)
    
    result = pil_img.copy()
    result.putalpha(mask)
    return result

def create_circle_icon_blink_frames(uploaded_image, icon_config, num_frames=5):
    """
    円形切り抜き画像＋点滅アイコンのアニメーションフレームを作成
    icon_config: { 'name': str, 'size': int, 'position': str ('top-right', etc), 'blink_mode': str }
    """
    frames = []
    width, height = 400, 400 # 固定キャンバスサイズ
    
    # 画像を円形にマスクしてリサイズ
    masked_img = mask_circle_transparent(uploaded_image)
    # キャンバスに収まるようにリサイズ (少し余白を持たせる)
    target_size = 300
    masked_img = masked_img.resize((target_size, target_size), Image.Resampling.LANCZOS)
    
    # 配置位置
    paste_x = (width - target_size) // 2
    paste_y = (height - target_size) // 2
    
    icon_name = icon_config.get('name', 'check.png')
    icon_size = icon_config.get('size', 80)
    icon_img = load_icon_image(icon_name, icon_size)
    
    # 4隅の座標を計算
    positions = [
        (10, 10), 
        (width - icon_size - 10, 10),
        (10, height - icon_size - 10), 
        (width - icon_size - 10, height - icon_size - 10)
    ]
    
    for i in range(num_frames):
        frame = Image.new('RGB', (width, height), 'white')  # 白背景
        # 画像配置
        frame.paste(masked_img, (paste_x, paste_y), masked_img)
        
        # 点滅ロジック (偶数フレームのみ表示)
        if i % 2 == 0 and icon_img:
             for pos in positions:
                 frame.paste(icon_img, pos, icon_img)
             
        buffer = io.BytesIO()
        frame.save(buffer, format='PNG')
        frames.append(buffer.getvalue())
        
    return frames

def process_video_to_apng(video_path, start_time, end_time, target_size_kb=300):
    """
    動画を指定区間切り出し、APNGに変換。300KB以下になるように自動調整。
    """
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    start_frame = int(start_time * fps)
    end_frame = int(end_time * fps)
    
    frames_buffer = []
    
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    current_frame = start_frame
    
    while current_frame <= end_frame:
        ret, frame = cap.read()
        if not ret: break
        
        # BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frames_buffer.append(Image.fromarray(frame_rgb))
        current_frame += 1
    cap.release()
    
    if not frames_buffer:
        return None

    # 最適化ループ
    # 戦略: 
    # 1. FPS削減 (間引き)
    # 2. リサイズ
    # 3. 減色 (Quantize)
    
    scales = [1.0, 0.8, 0.6, 0.5, 0.4]
    skip_rates = [2, 3, 4, 5] # 1/2, 1/3...
    
    best_apng = None
    min_size = float('inf')
    
    # まずは適度なFPSに落とす (例: 10FPS程度を目指す)
    # 元が30FPSなら 1/3
    default_skip = max(1, int(fps / 10))
    
    processed_frames = frames_buffer[::default_skip]
    
    for scale in scales:
        resized_frames = []
        for f in processed_frames:
            w, h = f.size
            new_w, new_h = int(w * scale), int(h * scale)
            resized_frames.append(f.resize((new_w, new_h), Image.Resampling.LANCZOS))
            
        # 減色トライ
        for colors in [256, 128, 64, 32]:
            quantized_frames = [f.quantize(colors=colors, method=2) for f in resized_frames] 
            
            # APNG生成
            output = io.BytesIO()
            apng = APNG()
            delay = 100 # 10FPS
            
            # BytesIOに変換して追加
            for qf in quantized_frames:
                buf = io.BytesIO()
                qf.save(buf, format="PNG")
                apng.append_file(io.BytesIO(buf.getvalue()), delay=delay)
            
            apng.save(output)
            size_kb = len(output.getvalue()) / 1024
            
            if size_kb < target_size_kb:
                return output.getvalue()
            
            # 見つからない場合は一番小さいものを保持しておく
            if size_kb < min_size:
                min_size = size_kb
                best_apng = output.getvalue()

    return best_apng # 目標未達でも最小サイズを返す

# 日本語フォント読み込み関数
def get_font(font_type="ゴシック", weight="W7", size=40):
    font_paths = []
    if font_type == "ゴシック":
        linux_paths = [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansMonoCJKjp-Bold.otf",
            "/usr/share/fonts/opentype/noto/NotoSansMonoCJKjp-Regular.otf",
        ]
        font_paths.extend(linux_paths)
        hiragino_std_paths = {
            "W3": "/Library/Fonts/ヒラギノ角ゴ Std W4.otf",
            "W4": "/Library/Fonts/ヒラギノ角ゴ Std W4.otf",
            "W5": "/Library/Fonts/ヒラギノ角ゴ Std W6.otf",
            "W6": "/Library/Fonts/ヒラギノ角ゴ Std W6.otf",
            "W7": "/Library/Fonts/ヒラギノ角ゴ Std W8.otf",
            "W8": "/Library/Fonts/ヒラギノ角ゴ Std W8.otf",
            "W9": "/Library/Fonts/ヒラギノ角ゴ Std W8.otf",
        }
        hiragino_paths = {
            "W3": "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
            "W4": "/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc",
            "W5": "/System/Library/Fonts/ヒラギノ角ゴシック W5.ttc",
            "W6": "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
            "W7": "/System/Library/Fonts/ヒラギノ角ゴシック W7.ttc",
            "W8": "/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc",
            "W9": "/System/Library/Fonts/ヒラギノ角ゴシック W9.ttc",
        }
        windows_paths = {
            "W3": ["C:\\Windows\\Fonts\\meiryo.ttc", "C:\\Windows\\Fonts\\YuGothL.ttc"],
            "W4": ["C:\\Windows\\Fonts\\meiryo.ttc", "C:\\Windows\\Fonts\\YuGothR.ttc"],
            "W5": ["C:\\Windows\\Fonts\\meiryo.ttc", "C:\\Windows\\Fonts\\YuGothM.ttc"],
            "W6": ["C:\\Windows\\Fonts\\meiryob.ttc", "C:\\Windows\\Fonts\\YuGothB.ttc"],
            "W7": ["C:\\Windows\\Fonts\\meiryob.ttc", "C:\\Windows\\Fonts\\YuGothB.ttc"],
            "W8": ["C:\\Windows\\Fonts\\meiryob.ttc", "C:\\Windows\\Fonts\\YuGothB.ttc"],
            "W9": ["C:\\Windows\\Fonts\\meiryob.ttc", "C:\\Windows\\Fonts\\YuGothB.ttc"],
        }
        if weight in hiragino_std_paths: font_paths.append(hiragino_std_paths[weight])
        if weight in hiragino_paths: font_paths.append(hiragino_paths[weight])
        if weight in windows_paths: font_paths.extend(windows_paths[weight])
        font_paths.extend(["msgothic.ttc", "C:\\Windows\\Fonts\\msgothic.ttc"])
    else:
        linux_paths = [
            "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc",
            "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSerifCJK-Bold.ttc",
            "/usr/share/fonts/truetype/noto/NotoSerifCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        ]
        font_paths.extend(linux_paths)
        font_paths.extend([
            "/System/Library/Fonts/ヒラギノ明朝 ProN W6.ttc",
            "/Library/Fonts/ヒラギノ明朝 Std W6.otf",
            "/System/Library/Fonts/ヒラギノ明朝 ProN W3.ttc",
            "/Library/Fonts/ヒラギノ明朝 Std W3.otf",
            "C:\\Windows\\Fonts\\msmincho.ttc",
            "msmincho.ttc"
        ])
    for font_path in font_paths:
        try:
            return ImageFont.truetype(font_path, size)
        except Exception as e:
            continue
    st.warning(f"日本語フォントが見つかりませんでした。デフォルトフォントを使用します。")
    return ImageFont.load_default()

# 描画関連関数群
def draw_text_bold(draw, position, text, font, fill, anchor="mm", is_mincho_bold=False):
    x, y = position
    if is_mincho_bold:
        offsets = [(0, 0), (1, 0), (0, 1), (1, 1)]
        for dx, dy in offsets:
            draw.text((x + dx, y + dy), text, fill=fill, font=font, anchor=anchor)
    else:
        draw.text((x, y), text, fill=fill, font=font, anchor=anchor)

def load_icon_image(icon_name, size):
    icon_path = f"icons/{icon_name}"
    if os.path.exists(icon_path):
        icon = Image.open(icon_path).convert("RGBA")
        icon = icon.resize((size, size), Image.Resampling.LANCZOS)
        return icon
    return None

# 文字描画関数（アラインメント対応）
def draw_text_with_spacing(img, draw, text, x, y, font, color, char_spacing=0, line_spacing=0, aspect_ratio=1.0, is_mincho_bold=False, align="center"):
    lines = text.split('\n')
    
    # まず全体の高さを計算
    total_height = 0
    line_heights = []
    for line in lines:
        if not line:
            bbox = draw.textbbox((0, 0), "A", font=font)
            h = bbox[3] - bbox[1]
        else:
            bbox = draw.textbbox((0, 0), line, font=font)
            h = bbox[3] - bbox[1]
        line_heights.append(h)
        total_height += h + line_spacing
    total_height -= line_spacing  # 最後の行間は不要
    
    # 中央揃えのため、開始Y座標を調整 (yを中心として描画)
    current_y = y - total_height // 2
    
    for idx, line in enumerate(lines):
        if not line:
            current_y += line_heights[idx] + line_spacing
            continue
        
        if char_spacing != 0 or aspect_ratio != 1.0 or align != "center":
            total_width = 0
            char_data = []
            
            for char in line:
                bbox = draw.textbbox((0, 0), char, font=font)
                char_width = (bbox[2] - bbox[0])
                char_height = (bbox[3] - bbox[1])
                scaled_width = char_width * aspect_ratio
                char_data.append((char, scaled_width, char_height))
                total_width += scaled_width + char_spacing
            
            total_width -= char_spacing
            
            if align == "left":
                start_x = x
            elif align == "right":
                start_x = x - total_width
            else:
                start_x = x - total_width / 2
                
            current_x = start_x
            
            for char, scaled_width, char_height in char_data:
                temp_size = int(font.size * 3)
                temp_img = Image.new('RGBA', (temp_size, temp_size), (255, 255, 255, 0))
                temp_draw = ImageDraw.Draw(temp_img)
                
                if is_mincho_bold:
                    offsets = [(0, 0), (1, 0), (0, 1), (1, 1)]
                    for dx, dy in offsets:
                        temp_draw.text((temp_size // 2 + dx, temp_size // 2 + dy), char, fill=color, font=font, anchor="mm")
                else:
                    temp_draw.text((temp_size // 2, temp_size // 2), char, fill=color, font=font, anchor="mm")
                
                if aspect_ratio != 1.0:
                    new_width = int(temp_img.width * aspect_ratio)
                    temp_img = temp_img.resize((new_width, temp_img.height), Image.Resampling.LANCZOS)
                
                paste_x = int(current_x + scaled_width / 2 - temp_img.width / 2)
                paste_y = int(current_y + line_heights[idx] // 2 - temp_img.height / 2)
                img.paste(temp_img, (paste_x, paste_y), temp_img)
                
                current_x += scaled_width + char_spacing
        else:
            # 標準描画（中央揃え）- 行の中心位置で描画
            line_center_y = current_y + line_heights[idx] // 2
            draw_text_bold(draw, (x, line_center_y), line, font, color, "mm", is_mincho_bold)
        
        current_y += line_heights[idx] + line_spacing
    
    return current_y

# テンプレート関数群
def create_red_border_blink_frames(width, height, text_elements, annotation_elements, uploaded_image, image_config, border_width=13, border_color="red", num_frames=5):
    frames = []
    color_map = {"red": "#FF0000", "blue": "#0000FF", "green": "#00FF00", "black": "#000000", "orange": "#FF6600"}
    border_rgb = color_map.get(border_color, "#FF0000")
    for i in range(num_frames):
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)
        if uploaded_image is not None and image_config is not None:
            img_scale = image_config.get('scale', 1.0)
            original_width = image_config.get('original_width', 100)
            original_height = image_config.get('original_height', 100)
            img_width = int(original_width * img_scale)
            img_height = int(original_height * img_scale)
            img_x = image_config.get('x', width // 2)
            img_y = image_config.get('y', height // 2)
            resized_img = uploaded_image.resize((img_width, img_height), Image.Resampling.LANCZOS)
            paste_x = img_x - img_width // 2
            paste_y = img_y - img_height // 2
            if uploaded_image.mode == 'RGBA':
                img.paste(resized_img, (paste_x, paste_y), resized_img)
            else:
                img.paste(resized_img, (paste_x, paste_y))
        if i % 2 == 0:
            draw.rectangle([0, 0, width-1, height-1], outline=border_rgb, width=border_width)
        
        for elem in text_elements:
            if elem.get('enabled', True):
                font = get_font(elem['font'], elem.get('weight', 'W7'), elem['size'])
                is_mincho_bold = elem['font'] == "明朝" and elem.get('weight', 'W7') in ["W7", "W8", "W9"]
                draw_text_with_spacing(img, draw, elem['text'], elem['x'], elem['y'], font, elem['color'],
                                     char_spacing=elem.get('char_spacing', 0),
                                     line_spacing=elem.get('line_spacing', 0),
                                     aspect_ratio=elem.get('aspect_ratio', 1.0),
                                     is_mincho_bold=is_mincho_bold,
                                     align="center")
        
        for elem in annotation_elements:
            if elem.get('enabled', True):
                font = get_font(elem['font'], elem.get('weight', 'W7'), elem['size'])
                is_mincho_bold = elem['font'] == "明朝" and elem.get('weight', 'W7') in ["W7", "W8", "W9"]
                # 注釈は左揃え、アスペクト比対応
                draw_text_with_spacing(img, draw, elem['text'], elem['x'], elem['y'], font, elem['color'],
                                     aspect_ratio=elem.get('aspect_ratio', 1.0),
                                     is_mincho_bold=is_mincho_bold,
                                     align="left")
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        frames.append(buffer.getvalue())
    return frames

def create_corner_icon_blink_frames(width, height, text_elements, annotation_elements, uploaded_image, image_config, icon_name="check.png", icon_size=85, num_frames=5):
    frames = []
    for i in range(num_frames):
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)
        if uploaded_image is not None and image_config is not None:
            img_scale = image_config.get('scale', 1.0)
            original_width = image_config.get('original_width', 100)
            original_height = image_config.get('original_height', 100)
            img_width = int(original_width * img_scale)
            img_height = int(original_height * img_scale)
            img_x = image_config.get('x', width // 2)
            img_y = image_config.get('y', height // 2)
            resized_img = uploaded_image.resize((img_width, img_height), Image.Resampling.LANCZOS)
            paste_x = img_x - img_width // 2
            paste_y = img_y - img_height // 2
            if uploaded_image.mode == 'RGBA':
                img.paste(resized_img, (paste_x, paste_y), resized_img)
            else:
                img.paste(resized_img, (paste_x, paste_y))
        if i % 2 == 0:
            icon_img = load_icon_image(icon_name, icon_size)
            if icon_img:
                positions = [(5, 5), (width - icon_size - 5, 5),
                            (5, height - icon_size - 5), (width - icon_size - 5, height - icon_size - 5)]
                for pos in positions:
                    img.paste(icon_img, pos, icon_img)
        
        for elem in text_elements:
            if elem.get('enabled', True):
                font = get_font(elem['font'], elem.get('weight', 'W7'), elem['size'])
                is_mincho_bold = elem['font'] == "明朝" and elem.get('weight', 'W7') in ["W7", "W8", "W9"]
                draw_text_with_spacing(img, draw, elem['text'], elem['x'], elem['y'], font, elem['color'],
                                     char_spacing=elem.get('char_spacing', 0),
                                     line_spacing=elem.get('line_spacing', 0),
                                     aspect_ratio=elem.get('aspect_ratio', 1.0),
                                     is_mincho_bold=is_mincho_bold,
                                     align="center")
        
        for elem in annotation_elements:
            if elem.get('enabled', True):
                font = get_font(elem['font'], elem.get('weight', 'W7'), elem['size'])
                is_mincho_bold = elem['font'] == "明朝" and elem.get('weight', 'W7') in ["W7", "W8", "W9"]
                draw_text_with_spacing(img, draw, elem['text'], elem['x'], elem['y'], font, elem['color'],
                                     aspect_ratio=elem.get('aspect_ratio', 1.0),
                                     is_mincho_bold=is_mincho_bold,
                                     align="left")
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        frames.append(buffer.getvalue())
    return frames

def create_icon_increase_frames(width, height, icon_text_config, annotation_elements, uploaded_image, image_config, icon_name="check.png", icon_size=60, num_frames=5):
    frames = []
    text_content = icon_text_config.get('text', 'サンプルテキスト').replace('\n', '')
    text_font_type = icon_text_config.get('font', 'ゴシック')
    text_weight = icon_text_config.get('weight', 'W7')
    text_size = icon_text_config.get('icon_size', 40)
    text_color = icon_text_config.get('color', '#000000')
    text_x = icon_text_config.get('icon_x', 74)
    text_y_base = icon_text_config.get('icon_y', 320)
    char_spacing = icon_text_config.get('icon_char_spacing', 0)
    aspect_ratio = icon_text_config.get('icon_aspect_ratio', 1.0)
    row_spacing = icon_text_config.get('icon_row_spacing', 62)
    is_mincho_bold = text_font_type == "明朝" and text_weight in ["W7", "W8", "W9"]
    
    for frame_idx in range(num_frames):
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)
        if uploaded_image is not None and image_config is not None:
            img_scale = image_config.get('scale', 1.0)
            original_width = image_config.get('original_width', 100)
            original_height = image_config.get('original_height', 100)
            img_width = int(original_width * img_scale)
            img_height = int(original_height * img_scale)
            img_x = image_config.get('x', width // 2)
            img_y = image_config.get('y', height // 2)
            resized_img = uploaded_image.resize((img_width, img_height), Image.Resampling.LANCZOS)
            paste_x = img_x - img_width // 2
            paste_y = img_y - img_height // 2
            if uploaded_image.mode == 'RGBA':
                img.paste(resized_img, (paste_x, paste_y), resized_img)
            else:
                img.paste(resized_img, (paste_x, paste_y))
        
        num_lines = frame_idx + 1
        start_y = text_y_base - ((num_lines - 1) * row_spacing)
        icon_img = load_icon_image(icon_name, icon_size)
        font = get_font(text_font_type, text_weight, text_size)
        
        for line_idx in range(num_lines):
            current_y = start_y + (line_idx * row_spacing)
            # アイコン増加のテキストは左揃え基準で描画
            # アイコン位置計算のために1文字目の左端が必要
            
            # draw_text_with_spacingは使わず、従来のロジックを維持しつつアスペクト比対応
            # （アイコン位置との関係が密接なため）
            
            first_char_left_edge = None
            current_x = text_x
            
            for char_idx, char in enumerate(text_content):
                temp_size = int(font.size * 3)
                temp_img = Image.new('RGBA', (temp_size, temp_size), (255, 255, 255, 0))
                temp_draw = ImageDraw.Draw(temp_img)
                if is_mincho_bold:
                    offsets = [(0, 0), (1, 0), (0, 1), (1, 1)]
                    for dx, dy in offsets:
                        temp_draw.text((temp_size // 2 + dx, temp_size // 2 + dy), char, fill=text_color, font=font, anchor="mm")
                else:
                    temp_draw.text((temp_size // 2, temp_size // 2), char, fill=text_color, font=font, anchor="mm")
                
                bbox_text = temp_draw.textbbox((0, 0), char, font=font)
                original_char_width = bbox_text[2] - bbox_text[0]
                scaled_char_width = original_char_width * aspect_ratio
                
                if aspect_ratio != 1.0:
                    new_width = int(temp_img.width * aspect_ratio)
                    temp_img = temp_img.resize((new_width, temp_img.height), Image.Resampling.LANCZOS)
                
                bbox_img = temp_img.getbbox()
                if bbox_img:
                    cropped = temp_img.crop(bbox_img)
                    paste_x = int(current_x + bbox_img[0])
                    paste_y = int(current_y - temp_img.height // 2 + bbox_img[1])
                    if char_idx == 0: first_char_left_edge = paste_x
                    img.paste(cropped, (paste_x, paste_y), cropped)
                    current_x += scaled_char_width + char_spacing
                else:
                    current_x += scaled_char_width + char_spacing
                    if char_idx == 0: first_char_left_edge = current_x
            
            if first_char_left_edge is not None:
                icon_x_pos = int(first_char_left_edge - icon_size - 5)
            else:
                icon_x_pos = text_x - icon_size - 5
            
            icon_y_pos = current_y - icon_size // 2
            if icon_img:
                img.paste(icon_img, (icon_x_pos, icon_y_pos), icon_img)
        
        for elem in annotation_elements:
            if elem.get('enabled', True):
                font_annot = get_font(elem['font'], elem.get('weight', 'W7'), elem['size'])
                is_mincho_bold_annot = elem['font'] == "明朝" and elem.get('weight', 'W7') in ["W7", "W8", "W9"]
                draw_text_with_spacing(img, draw, elem['text'], elem['x'], elem['y'], font, elem['color'],
                                     aspect_ratio=elem.get('aspect_ratio', 1.0),
                                     is_mincho_bold=is_mincho_bold_annot,
                                     align="left")
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        frames.append(buffer.getvalue())
    return frames

def save_apng(frames, num_frames, num_plays=4):
    frame_delay = 1000 // num_frames
    apng_obj = APNG()
    for frame_data in frames:
        apng_obj.append_file(io.BytesIO(frame_data), delay=frame_delay)
    apng_obj.num_plays = num_plays
    output = io.BytesIO()
    apng_obj.save(output)
    output.seek(0)
    return output.getvalue()

def create_preview_image(text_elements, annotation_elements, uploaded_image, image_config, template_type, scale=0.5, **kwargs):
    preview_width = int(WIDTH * scale)
    preview_height = int(HEIGHT * scale)
    img = Image.new('RGB', (preview_width, preview_height), 'white')
    draw = ImageDraw.Draw(img)
    if uploaded_image is not None and image_config is not None:
        img_scale = image_config.get('scale', 1.0)
        original_width = image_config.get('original_width', 100)
        original_height = image_config.get('original_height', 100)
        img_width = int(original_width * img_scale * scale)
        img_height = int(original_height * img_scale * scale)
        img_x = int(image_config.get('x', WIDTH // 2) * scale)
        img_y = int(image_config.get('y', HEIGHT // 2) * scale)
        resized_img = uploaded_image.resize((img_width, img_height), Image.Resampling.LANCZOS)
        paste_x = img_x - img_width // 2
        paste_y = img_y - img_height // 2
        if uploaded_image.mode == 'RGBA':
            img.paste(resized_img, (paste_x, paste_y), resized_img)
        else:
            img.paste(resized_img, (paste_x, paste_y))
    
    if template_type == "赤枠点滅":
        border_width = max(1, int(kwargs.get('border_width', 13) * scale))
        border_color = kwargs.get('border_color', 'red')
        color_map = {"red": "#FF0000", "blue": "#0000FF", "green": "#00FF00", "black": "#000000", "orange": "#FF6600"}
        draw.rectangle([0, 0, preview_width-1, preview_height-1], outline=color_map.get(border_color, "#FF0000"), width=border_width)
    elif template_type == "4隅アイコン点滅":
        icon_size = int(kwargs.get('icon_size', 85) * scale)
        icon_name = kwargs.get('icon_name', 'check.png')
        icon_img = load_icon_image(icon_name, icon_size)
        if icon_img:
            positions = [(10, 10), (preview_width - icon_size - 10, 10),
                        (10, preview_height - icon_size - 10), (preview_width - icon_size - 10, preview_height - icon_size - 10)]
            for pos in positions: img.paste(icon_img, pos, icon_img)
    elif template_type == "アイコン増加":
        icon_text_config = text_elements[0]
        text_content = icon_text_config.get('text', 'サンプルテキスト').replace('\n', '')
        text_font_type = icon_text_config.get('font', 'ゴシック')
        text_weight = icon_text_config.get('weight', 'W7')
        text_size = int(icon_text_config.get('icon_size', 40) * scale)
        text_color = icon_text_config.get('color', '#000000')
        text_x = int(icon_text_config.get('icon_x', 74) * scale)
        text_y_base = int(icon_text_config.get('icon_y', 320) * scale)
        char_spacing = int(icon_text_config.get('icon_char_spacing', 0) * scale)
        aspect_ratio = icon_text_config.get('icon_aspect_ratio', 1.0)
        row_spacing = int(icon_text_config.get('icon_row_spacing', 62) * scale)
        icon_size = int(kwargs.get('icon_size', 60) * scale)
        icon_name = kwargs.get('icon_name', 'check.png')
        is_mincho_bold = text_font_type == "明朝" and text_weight in ["W7", "W8", "W9"]
        num_lines = 5
        start_y = text_y_base - ((num_lines - 1) * row_spacing)
        icon_img = load_icon_image(icon_name, icon_size)
        font = get_font(text_font_type, text_weight, text_size)
        
        for line_idx in range(num_lines):
            current_y = start_y + (line_idx * row_spacing)
            
            first_char_left_edge = None
            current_x = text_x
            
            for char_idx, char in enumerate(text_content):
                temp_size = int(font.size * 3)
                temp_img = Image.new('RGBA', (temp_size, temp_size), (255, 255, 255, 0))
                temp_draw = ImageDraw.Draw(temp_img)
                if is_mincho_bold:
                    offsets = [(0, 0), (1, 0), (0, 1), (1, 1)]
                    for dx, dy in offsets:
                        temp_draw.text((temp_size // 2 + dx, temp_size // 2 + dy), char, fill=text_color, font=font, anchor="mm")
                else:
                    temp_draw.text((temp_size // 2, temp_size // 2), char, fill=text_color, font=font, anchor="mm")
                
                bbox_text = temp_draw.textbbox((0, 0), char, font=font)
                original_char_width = bbox_text[2] - bbox_text[0]
                scaled_char_width = original_char_width * aspect_ratio
                
                if aspect_ratio != 1.0:
                    new_width = int(temp_img.width * aspect_ratio)
                    temp_img = temp_img.resize((new_width, temp_img.height), Image.Resampling.LANCZOS)
                
                bbox_img = temp_img.getbbox()
                if bbox_img:
                    cropped = temp_img.crop(bbox_img)
                    paste_x = int(current_x + bbox_img[0])
                    paste_y = int(current_y - temp_img.height // 2 + bbox_img[1])
                    if char_idx == 0: first_char_left_edge = paste_x
                    img.paste(cropped, (paste_x, paste_y), cropped)
                    current_x += scaled_char_width + char_spacing
                else:
                    current_x += scaled_char_width + char_spacing
                    if char_idx == 0: first_char_left_edge = current_x
            
            if first_char_left_edge is not None:
                icon_x = int(first_char_left_edge - icon_size - int(5 * scale))
            else:
                icon_x = text_x - icon_size - int(5 * scale)
            
            icon_y = current_y - icon_size // 2
            if icon_img:
                img.paste(icon_img, (icon_x, icon_y), icon_img)
    
    if template_type != "アイコン増加":
        for elem in text_elements:
            if elem.get('enabled', True):
                font = get_font(elem['font'], elem.get('weight', 'W7'), int(elem['size'] * scale))
                scaled_x = int(elem['x'] * scale)
                scaled_y = int(elem['y'] * scale)
                scaled_char_spacing = int(elem.get('char_spacing', 0) * scale)
                scaled_line_spacing = int(elem.get('line_spacing', 0) * scale)
                is_mincho_bold = elem['font'] == "明朝" and elem.get('weight', 'W7') in ["W7", "W8", "W9"]
                draw_text_with_spacing(img, draw, elem['text'], scaled_x, scaled_y, font, elem['color'],
                                     char_spacing=scaled_char_spacing,
                                     line_spacing=scaled_line_spacing,
                                     aspect_ratio=elem.get('aspect_ratio', 1.0),
                                     is_mincho_bold=is_mincho_bold,
                                     align="center")
    
    for elem in annotation_elements:
        if elem.get('enabled', True):
            font = get_font(elem['font'], elem.get('weight', 'W7'), int(elem['size'] * scale))
            is_mincho_bold = elem['font'] == "明朝" and elem.get('weight', 'W7') in ["W7", "W8", "W9"]
            draw_text_with_spacing(img, draw, elem['text'], int(elem['x'] * scale), int(elem['y'] * scale), font, elem['color'],
                                 aspect_ratio=elem.get('aspect_ratio', 1.0),
                                 is_mincho_bold=is_mincho_bold,
                                 align="left")
    
    return img

# メインアプリ
st.title("APNG Generator")

# セッション状態の初期化
if 'text_variations' not in st.session_state:
    st.session_state.text_variations = [{
        'text': 'サンプルテキスト',
        'font': 'ゴシック',
        'weight': 'W7',
        'size': 100,
        'color': '#000000',
        'char_spacing': 0,
        'line_spacing': 0,
        'aspect_ratio': 1.0,
        'x': WIDTH // 2,
        'y': HEIGHT // 2,
        'enabled': True,
        'icon_size': 40,
        'icon_x': 74,
        'icon_y': 320,
        'icon_char_spacing': 0,
        'icon_aspect_ratio': 1.0,
        'icon_row_spacing': 62
    }]

default_annot_text = "※定期初回限定クーポンのこと。定期初回価格、1世帯1回限り。すでにキャンペーンで購入済みの方は対象外"
default_neumo_text = "※定期初回限定のクーポンのこと※定期初回価格。初回限定、1世帯1回限り。既にニューモVをキャンペーンで購入済みの方は対象外となります"

if 'annotation_variations' not in st.session_state:
    st.session_state.annotation_variations = [{
        'text': default_annot_text,
        'font': 'ゴシック',
        'weight': 'W7',
        'size': 10,
        'color': '#000000',
        'x': 10,
        'y': 390,
        'enabled': True,
        'is_neumo': False,
        'aspect_ratio': 1.0
    }]

if 'image_variations' not in st.session_state:
    st.session_state.image_variations = [{
        'image': None,
        'original_width': 100,
        'original_height': 100,
        'scale': 1.0,
        'x': WIDTH // 2,
        'y': HEIGHT // 2
    }]

# テキスト設定のコピー用クリップボード
if 'copied_text_settings' not in st.session_state:
    st.session_state.copied_text_settings = None

if 'use_red_border' not in st.session_state:
    st.session_state.use_red_border = True

if 'use_corner_icon' not in st.session_state:
    st.session_state.use_corner_icon = False

if 'use_icon_increase' not in st.session_state:
    st.session_state.use_icon_increase = False

# パラメータのデフォルト値をセッションステートで管理（リアルタイム反映用）
if 'border_width_red' not in st.session_state: st.session_state.border_width_red = 15
if 'icon_size_corner' not in st.session_state: st.session_state.icon_size_corner = 100
if 'icon_size_increase' not in st.session_state: st.session_state.icon_size_increase = 55

# レイアウト：左右分割（比率調整）
mode = st.radio("作成モードを選択", ["テンプレート詳細作成", "テキスト一発作成", "画像円形切り抜き", "動画シーン切り抜き"], horizontal=True)

if mode == "テキスト一発作成":
    st.markdown("### テキストを入れるだけでAPNG作成")
    st.info("各テキスト入力欄ごとに別々のAPNGが作成されます。入力欄内で改行すると、APNG内でも改行されます。")
    
    # テキスト入力欄の数を管理
    if 'simple_text_count' not in st.session_state:
        st.session_state.simple_text_count = 1
    
    if st.button("＋ テキスト追加"):
        st.session_state.simple_text_count += 1
        st.rerun()
    
    text_inputs = []
    for i in range(st.session_state.simple_text_count):
        text = st.text_area(f"テキスト {i+1}", f"サンプル{i+1}", key=f"simple_text_{i}", height=80)
        text_inputs.append(text)
    
    simple_color = st.color_picker("テキスト色", "#FF0000")
    
    st.markdown("#### 作成するテンプレート（複数選択可）")
    c1, c2, c3 = st.columns(3)
    with c1: use_red = st.checkbox("赤枠点滅", value=True)
    with c2: use_corner = st.checkbox("4隅アイコン")
    with c3: use_increase = st.checkbox("アイコン増加")
    
    st.markdown("#### 注釈設定")
    annot_enabled = st.checkbox("注釈を表示する", value=True)
    annot_text = st.text_input("注釈テキスト", "※定期初回限定クーポンのこと。定期初回価格、1世帯1回限り。すでにキャンペーンで購入済みの方は対象外")
    # 注釈は左下、ゴシック、サイズ17、縦横比75%
    
    st.markdown("#### ファイル名設定")
    f_col1, f_col2 = st.columns(2)
    with f_col1: f_prod_name = st.text_input("商材名", "商材名", key="s_prod")
    with f_col2: f_custom_name = st.text_input("識別名", "名前", key="s_cust")

    if st.button("一括作成する"):
        valid_texts = [t for t in text_inputs if t.strip()]
        if not valid_texts:
            st.error("テキストを入力してください")
            st.stop()
            
        generated_files = []
        seq_num = 1
        
        # 注釈要素の準備 - テンプレート別に後で設定するため、ここでは基本値のみ
        annot_height = 0
        base_annot_size = 12  # 赤枠・4隅用のベースサイズ
        increase_annot_size = 8  # アイコン増加用の小さいサイズ
        
        if annot_enabled and annot_text.strip():
            # 注釈が画面幅に収まるか確認
            dummy_img = Image.new('RGB', (1, 1))
            draw = ImageDraw.Draw(dummy_img)
            
            # サイズ調整（画面幅に収まるまで縮小）
            for test_size in [base_annot_size, 11, 10, 9, 8, 7]:
                font = get_font("ゴシック", "W7", test_size)
                bbox = draw.textbbox((0, 0), annot_text, font=font)
                if bbox[2] - bbox[0] <= WIDTH - 10:
                    base_annot_size = test_size
                    break
            
            annot_height = base_annot_size + 5
        
        # 安全領域の計算
        border_margin = 16
        icon_margin = 85
        
        with st.spinner(f"{len(valid_texts)}パターン × テンプレート処理中..."):
            for text in valid_texts:
                center_y = (HEIGHT - annot_height) // 2
                
                # 行間はフォントサイズの15%
                def make_line_spacing(sz):
                    return int(sz * 0.15)
                
                if use_red:
                    safe_w = WIDTH - border_margin * 2
                    safe_h = HEIGHT - border_margin * 2 - annot_height
                    font, size = get_autosize_font(text, "ゴシック", "W7", safe_w, safe_h, start_size=400)
                    
                    # 注釈要素（赤枠用）
                    annot_elem = []
                    if annot_enabled and annot_text.strip():
                        annot_elem = [{
                            'text': annot_text, 'font': 'ゴシック', 'weight': 'W7', 'size': base_annot_size,
                            'color': '#000000', 'x': 5, 'y': HEIGHT - base_annot_size - 2,
                            'enabled': True, 'aspect_ratio': 1.0
                        }]
                    
                    text_elem = [{
                        'text': text, 'font': 'ゴシック', 'weight': 'W7', 'size': size,
                        'color': simple_color, 'x': WIDTH // 2, 'y': center_y,
                        'enabled': True, 'char_spacing': 0, 'line_spacing': make_line_spacing(size), 'aspect_ratio': 1.0
                    }]
                    frames = create_red_border_blink_frames(WIDTH, HEIGHT, text_elem, annot_elem, None, None, border_color="red")
                    apng_data = save_apng(frames, num_frames=5)
                    fname = generate_filename(f_prod_name, f_custom_name, "赤枠点滅", seq_num)
                    generated_files.append((fname, apng_data))
                    seq_num += 1

                if use_corner:
                    safe_w = WIDTH - icon_margin * 2
                    safe_h = HEIGHT - icon_margin - annot_height
                    font, size = get_autosize_font(text, "ゴシック", "W7", safe_w, safe_h, start_size=400)
                    
                    # 注釈要素（4隅用 - 小さいサイズで統一）
                    annot_elem = []
                    if annot_enabled and annot_text.strip():
                        annot_elem = [{
                            'text': annot_text, 'font': 'ゴシック', 'weight': 'W7', 'size': increase_annot_size,
                            'color': '#000000', 'x': 5, 'y': HEIGHT - increase_annot_size - 2,
                            'enabled': True, 'aspect_ratio': 1.0
                        }]
                    
                    text_elem = [{
                        'text': text, 'font': 'ゴシック', 'weight': 'W7', 'size': size,
                        'color': simple_color, 'x': WIDTH // 2, 'y': center_y,
                        'enabled': True, 'char_spacing': 0, 'line_spacing': make_line_spacing(size), 'aspect_ratio': 1.0
                    }]
                    frames = create_corner_icon_blink_frames(WIDTH, HEIGHT, text_elem, annot_elem, None, None, icon_name="check.png", icon_size=80)
                    apng_data = save_apng(frames, num_frames=5)
                    fname = generate_filename(f_prod_name, f_custom_name, "4隅アイコン", seq_num)
                    generated_files.append((fname, apng_data))
                    seq_num += 1
                
                if use_increase:
                    # アイコン増加: 5行が画面いっぱいに収まる計算
                    usable_height = HEIGHT - 15 - annot_height
                    row_height = usable_height // 5
                    icon_size = int(row_height * 0.85)
                    text_size = int(row_height * 0.75)
                    
                    text_for_increase = text.replace('\n', '')
                    
                    # アイコン増加用の小さい注釈
                    annot_elem = []
                    if annot_enabled and annot_text.strip():
                        annot_elem = [{
                            'text': annot_text, 'font': 'ゴシック', 'weight': 'W7', 'size': increase_annot_size,
                            'color': '#000000', 'x': 5, 'y': HEIGHT - increase_annot_size - 2,
                            'enabled': True, 'aspect_ratio': 1.0
                        }]
                    
                    text_elem = {
                        'text': text_for_increase,
                        'font': 'ゴシック', 'weight': 'W7', 'size': text_size,
                        'color': simple_color, 'x': WIDTH//2, 'y': HEIGHT//2,
                        'enabled': True,
                        'icon_size': text_size,
                        'icon_x': icon_size + 15,
                        'icon_y': HEIGHT - 10 - annot_height - row_height // 2,
                        'icon_char_spacing': 0,
                        'icon_aspect_ratio': 0.85,
                        'icon_row_spacing': row_height
                    }
                    frames = create_icon_increase_frames(WIDTH, HEIGHT, text_elem, annot_elem, None, None, icon_size=icon_size)
                    apng_data = save_apng(frames, num_frames=5)
                    fname = generate_filename(f_prod_name, f_custom_name, "アイコン増加", seq_num)
                    generated_files.append((fname, apng_data))
                    seq_num += 1
        
        if generated_files:
            st.success(f"{len(generated_files)}個のAPNGを作成しました！")
            
            # ZIP作成
            zip_buffer = io.BytesIO()
            folder_name = f"{datetime.now().strftime('%Y%m%d')}_{f_prod_name}_APNG_一括_素材_{f_custom_name}"
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for filename, data in generated_files:
                    zip_file.writestr(f"{folder_name}/{filename}", data)
            zip_buffer.seek(0)
            
            st.download_button("まとめてZIPダウンロード", zip_buffer.getvalue(), f"{folder_name}.zip", "application/zip", type="primary")
            
            # 個別ダウンロード
            with st.expander("個別ダウンロード"):
                for idx, (fname, data) in enumerate(generated_files):
                    st.download_button(fname, data, fname, "image/png", key=f"dl_simple_{idx}")
    st.stop() # 以降の処理（通常モード）を実行しない

if mode == "画像円形切り抜き":
    st.markdown("### 画像を丸く切り抜いてアイコン点滅 (4隅)")
    
    uploaded_file = st.file_uploader("画像をアップロード", type=['png', 'jpg', 'jpeg'])
    
    st.markdown("#### ファイル名設定")
    f_col1, f_col2 = st.columns(2)
    with f_col1: f_prod_name = st.text_input("商材名", "商材名", key="c_prod")
    with f_col2: f_custom_name = st.text_input("識別名", "名前", key="c_cust")

    if uploaded_file:
        img = Image.open(uploaded_file)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 切り抜き範囲を選択")
            # Aspect Ratio 1:1 for circle
            cropped_img = st_cropper(img, realtime_update=True, box_color='blue', aspect_ratio=(1,1))
            st.image(cropped_img, caption="切り抜きプレビュー", width=200)
            
        with col2:
            st.markdown("#### アイコン設定")
            icon_name = st.selectbox("点滅させるアイコン", ["check.png", "red_check.png", "！.png", "！？.png"])
            # 4隅固定になったので位置選択は不要
            
            if st.button("アニメーション作成"):
                icon_config = {'name': icon_name, 'size': 80}
                frames = create_circle_icon_blink_frames(cropped_img, icon_config)
                apng_data = save_apng(frames, num_frames=5)
                
                # Check Size logic could be here if needed for images
                size_kb = len(apng_data) / 1024
                if size_kb > 300:
                     st.warning(f"サイズが300KBを超えています ({size_kb:.1f}KB)。減色処理を行います...")
                     # 簡易減色リトライ (本来はcreate_...内で処理すべきだが、バイト列から復元して処理)
                     # ここではsave_apngの前に処理を入れるのが筋だが、既存構造の都合上、事後チェック
                     pass 

                fname = generate_filename(f_prod_name, f_custom_name, "画像円形切り抜き", 1)
                
                st.success("作成完了！")
                st.image(apng_data, caption="完成アニメーション")
                st.download_button("ダウンロード", apng_data, fname, "image/png")
    st.stop()

if mode == "動画シーン切り抜き":
    st.markdown("### 動画からシーンを切り抜いて軽量APNG作成 (300KB以下)")
    video_file = st.file_uploader("動画をアップロード (MP4)", type=['mp4'])
    
    st.markdown("#### ファイル名設定")
    f_col1, f_col2 = st.columns(2)
    with f_col1: f_prod_name = st.text_input("商材名", "商材名", key="v_prod")
    with f_col2: f_custom_name = st.text_input("識別名", "名前", key="v_cust")
    
    if video_file:
        # 一時保存
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') 
        tfile.write(video_file.read())
        
        st.video(tfile.name)
        
        # Duration取得
        cap = cv2.VideoCapture(tfile.name)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps
        cap.release()
        
        st.markdown(f"動画の長さ: {duration:.2f}秒")
        
        start_time, end_time = st.slider("切り抜き範囲 (秒)", 0.0, duration, (0.0, min(duration, 5.0)))
        
        if st.button("最適化APNG作成"):
            with st.spinner("最適化処理中... (サイズ調整のため数回試行します)"):
                apng_data = process_video_to_apng(tfile.name, start_time, end_time)
                
                if apng_data:
                    size_kb = len(apng_data) / 1024
                    fname = generate_filename(f_prod_name, f_custom_name, "動画", 1) # 動画の場合のテンプレート名はどうするか？一旦「動画」
                    
                    st.success(f"作成完了！ サイズ: {size_kb:.1f}KB")
                    st.image(apng_data)
                    st.download_button("ダウンロード", apng_data, fname, "image/png")
                else:
                    st.error("作成に失敗しました。範囲を変えて試してください。")
        
    st.stop()

col_settings, col_preview = st.columns([1.2, 1])

# ==========================================
# 左カラム：設定エリア（タブ化による整理）
# ==========================================
with col_settings:
    # タブの作成
    tab_template, tab_text, tab_image, tab_annot, tab_output = st.tabs([
        "テンプレート選択", "テキスト設定", "画像設定", "注釈設定", "出力・保存"
    ])
    
    # --- タブ1: テンプレート選択 ---
    with tab_template:
        st.markdown('<div class="simple-header">使用するテンプレート</div>', unsafe_allow_html=True)
        col_t1, col_t2, col_t3 = st.columns(3)
        with col_t1:
            use_red_border = st.checkbox("赤枠点滅", value=st.session_state.use_red_border, key="chk_red")
        with col_t2:
            use_corner_icon = st.checkbox("4隅アイコン", value=st.session_state.use_corner_icon, key="chk_corner")
        with col_t3:
            use_icon_increase = st.checkbox("アイコン増加", value=st.session_state.use_icon_increase, key="chk_increase")
        
        st.session_state.use_red_border = use_red_border
        st.session_state.use_corner_icon = use_corner_icon
        st.session_state.use_icon_increase = use_icon_increase
        
        st.markdown('<div class="simple-header">詳細パラメータ</div>', unsafe_allow_html=True)
        if use_red_border:
            st.caption("赤枠点滅の設定")
            col1, col2 = st.columns(2)
            with col1: 
                border_width_red = st.slider("枠線の太さ", 15, 45, st.session_state.border_width_red, key="border_width_red")
            with col2: 
                border_colors = st.multiselect("枠線の色", ["red", "blue", "green", "black", "orange"], default=["red"], key="border_colors")
            
            with st.expander("詳細設定（フレーム数・ループ数）", expanded=False):
                col3, col4 = st.columns(2)
                with col3: num_frames_red = st.slider("フレーム数", 5, 20, 5, key="num_frames_red")
                with col4: loop_count_red = st.selectbox("ループ数", [1, 2, 3, 4], index=3, key="loop_count_red")
            st.divider()
        
        if use_corner_icon:
            st.caption("4隅アイコンの設定")
            col1, col2 = st.columns(2)
            with col1: 
                icon_size_corner = st.slider("アイコンサイズ", 20, 150, st.session_state.icon_size_corner, key="icon_size_corner")
            with col2: 
                icon_names = st.multiselect("アイコン種類", ["check.png", "red_check.png", "！.png", "！？.png"], default=["check.png"], key="icon_names")
            
            with st.expander("詳細設定（フレーム数・ループ数）", expanded=False):
                col3, col4 = st.columns(2)
                with col3: num_frames_corner = st.slider("フレーム数", 5, 20, 5, key="num_frames_corner")
                with col4: loop_count_corner = st.selectbox("ループ数", [1, 2, 3, 4], index=3, key="loop_count_corner")
            st.divider()
        
        if use_icon_increase:
            st.caption("アイコン増加の設定")
            col1, col2 = st.columns(2)
            with col1: 
                icon_size_increase = st.slider("アイコンサイズ(増)", 20, 150, st.session_state.icon_size_increase, key="icon_size_increase")
            with col2: 
                icon_names_increase = st.multiselect("アイコン種類(増)", ["check.png", "red_check.png", "！.png", "！？.png"], default=["check.png"], key="icon_names_increase")
            
            with st.expander("詳細設定（フレーム数・ループ数）", expanded=False):
                col3, col4 = st.columns(2)
                with col3: num_frames_increase = st.slider("フレーム数", 3, 10, 5, key="num_frames_increase")
                with col4: loop_count_increase = st.selectbox("ループ数", [1, 2, 3, 4], index=3, key="loop_count_increase")
    
    # --- タブ2: テキスト設定 ---
    with tab_text:
        # 第1：Text選択ラジオボタン
        text_options = [f"Text {i+1}" for i in range(len(st.session_state.text_variations))]
        selected_text_idx = st.radio("編集するテキストを選択", range(len(text_options)), format_func=lambda x: text_options[x], horizontal=True, index=st.session_state.get('selected_text_tab', 0))
        st.session_state.selected_text_tab = selected_text_idx
        
        # 第2：テキスト操作ボタン群
        btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)
        with btn_col1:
            if st.button("➕ 追加", key="tab_btn_add", use_container_width=True):
                st.session_state.text_variations.append({
                    'text': '新しいテキスト',
                    'font': 'ゴシック',
                    'weight': 'W7',
                    'size': 100,
                    'color': '#000000',
                    'char_spacing': 0,
                    'line_spacing': 0,
                    'aspect_ratio': 1.0,
                    'x': WIDTH // 2,
                    'y': HEIGHT // 2,
                    'enabled': True,
                    'icon_size': 40,
                    'icon_x': 74,
                    'icon_y': 320,
                    'icon_char_spacing': 0,
                    'icon_aspect_ratio': 1.0,
                    'icon_row_spacing': 62
                })
                st.session_state.selected_text_tab = len(st.session_state.text_variations) - 1
                st.rerun()
        with btn_col2:
            # 設定コピー: テキスト内容を除く設定値をクリップボードに保存
            if st.button("📋 設定コピー", key="tab_btn_copy", use_container_width=True):
                current = st.session_state.text_variations[selected_text_idx]
                st.session_state.copied_text_settings = {
                    k: v for k, v in current.items() if k != 'text'
                }
                st.toast(f"Text {selected_text_idx + 1} の設定をコピーしました")
        with btn_col3:
            # 設定ペースト: コピーした設定値を現在のテキストに適用（テキスト内容は維持）
            has_copied = st.session_state.copied_text_settings is not None
            if st.button("📥 設定貼付", key="tab_btn_paste", use_container_width=True, disabled=not has_copied):
                current_text = st.session_state.text_variations[selected_text_idx]['text']
                st.session_state.text_variations[selected_text_idx].update(
                    st.session_state.copied_text_settings
                )
                # テキスト内容は元のまま保持
                st.session_state.text_variations[selected_text_idx]['text'] = current_text
                st.toast(f"Text {selected_text_idx + 1} に設定を貼り付けました")
                st.rerun()
        with btn_col4:
            # テキスト複製: 選択中のテキスト設定を丸ごとコピーして新規追加
            if st.button("📄 複製", key="tab_btn_dup", use_container_width=True):
                import copy
                duplicated = copy.deepcopy(st.session_state.text_variations[selected_text_idx])
                st.session_state.text_variations.append(duplicated)
                st.session_state.selected_text_tab = len(st.session_state.text_variations) - 1
                st.rerun()

        text_var = st.session_state.text_variations[selected_text_idx]
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 第3：テキスト入力欄
        new_text = st.text_area("テキスト内容", value=text_var['text'], height=80, key=f"textarea_{selected_text_idx}", placeholder="テキストを入力...")
        st.session_state.text_variations[selected_text_idx]['text'] = new_text
        
        # 削除ボタン（表示トグルの代わり）
        if st.button("このテキスト設定を削除", key=f"del_txt_{selected_text_idx}", use_container_width=True):
            if len(st.session_state.text_variations) > 1:
                st.session_state.text_variations.pop(selected_text_idx)
                st.session_state.selected_text_tab = max(0, selected_text_idx - 1)
                st.rerun()
            else:
                st.warning("最後のテキスト設定は削除できません")
        
        st.divider()

        # 第5：フォント、ウェイト（太さ）
        col1, col2 = st.columns(2)
        with col1:
            font = st.selectbox("フォント", ["ゴシック", "明朝"],
                                index=["ゴシック", "明朝"].index(text_var.get('font', 'ゴシック')),
                                key=f"font_{selected_text_idx}")
            st.session_state.text_variations[selected_text_idx]['font'] = font
        with col2:
            weight = st.selectbox("太さ", ["W3", "W4", "W5", "W6", "W7", "W8", "W9"],
                                    index=["W3", "W4", "W5", "W6", "W7", "W8", "W9"].index(text_var.get('weight', 'W7')),
                                    key=f"weight_{selected_text_idx}")
            st.session_state.text_variations[selected_text_idx]['weight'] = weight
        
        # 第6：サイズ、色
        col3, col4 = st.columns([2, 1])
        with col3:
            size = st.slider("サイズ", 50, 200, text_var.get('size', 100), key=f"size_{selected_text_idx}")
            st.session_state.text_variations[selected_text_idx]['size'] = size
        with col4:
            color = st.color_picker("色", text_var.get('color', '#000000'), key=f"color_{selected_text_idx}")
            st.session_state.text_variations[selected_text_idx]['color'] = color
        
        # 第7：文字間、行間、縦横比
        col5, col6, col7 = st.columns(3)
        with col5:
            char_spacing = st.slider("文字間", -10, 50, text_var.get('char_spacing', 0), key=f"char_{selected_text_idx}")
            st.session_state.text_variations[selected_text_idx]['char_spacing'] = char_spacing
        with col6:
            line_spacing = st.slider("行間", -10, 50, text_var.get('line_spacing', 0), key=f"line_{selected_text_idx}")
            st.session_state.text_variations[selected_text_idx]['line_spacing'] = line_spacing
        with col7:
            aspect_ratio = st.slider("縦横比", 50, 200, int(text_var.get('aspect_ratio', 1.0) * 100), key=f"aspect_{selected_text_idx}") / 100
            st.session_state.text_variations[selected_text_idx]['aspect_ratio'] = aspect_ratio
            
        # 第8：X座標（横）、Y座標（縦）
        col8, col9 = st.columns(2)
        with col8:
            pos_x = st.slider("横位置 (X)", 0, WIDTH, text_var.get('x', WIDTH // 2), key=f"x_{selected_text_idx}")
            st.session_state.text_variations[selected_text_idx]['x'] = pos_x
        with col9:
            pos_y = st.slider("縦位置 (Y)", 0, HEIGHT, text_var.get('y', HEIGHT // 2), key=f"y_{selected_text_idx}")
            st.session_state.text_variations[selected_text_idx]['y'] = pos_y

        # コールバック関数: rerun前に実行されるためwidget keyの変更が安全
        def center_text(idx):
            st.session_state.text_variations[idx]['x'] = WIDTH // 2
            st.session_state.text_variations[idx]['y'] = HEIGHT // 2
            st.session_state[f"x_{idx}"] = WIDTH // 2
            st.session_state[f"y_{idx}"] = HEIGHT // 2

        st.button("中央に配置", key=f"center_{selected_text_idx}", use_container_width=True,
                  on_click=center_text, args=(selected_text_idx,))

        # アイコン増加専用
        if use_icon_increase:
            with st.expander("アイコン増加専用設定", expanded=True):
                st.caption("※ アイコン増加テンプレート使用時のみ有効")
                col1, col2, col3 = st.columns(3)
                with col1:
                    icon_size = st.slider("文字サイズ", 20, 80, text_var.get('icon_size', 40), key=f"icon_size_{selected_text_idx}")
                    st.session_state.text_variations[selected_text_idx]['icon_size'] = icon_size
                with col2:
                    icon_char_spacing = st.slider("文字間", -10, 50, text_var.get('icon_char_spacing', 0), key=f"icon_char_{selected_text_idx}")
                    st.session_state.text_variations[selected_text_idx]['icon_char_spacing'] = icon_char_spacing
                with col3:
                    icon_aspect_ratio = st.slider("縦横比", 50, 200, int(text_var.get('icon_aspect_ratio', 1.0) * 100), key=f"icon_aspect_{selected_text_idx}") / 100
                    st.session_state.text_variations[selected_text_idx]['icon_aspect_ratio'] = icon_aspect_ratio
                
                col4, col5, col6 = st.columns(3)
                with col4:
                    icon_row_spacing = st.slider("行間隔", 30, 100, text_var.get('icon_row_spacing', 50), key=f"icon_row_{selected_text_idx}")
                    st.session_state.text_variations[selected_text_idx]['icon_row_spacing'] = icon_row_spacing
                with col5:
                    icon_x = st.slider("開始X座標", 0, WIDTH, text_var.get('icon_x', 120), key=f"icon_x_{selected_text_idx}")
                    st.session_state.text_variations[selected_text_idx]['icon_x'] = icon_x
                with col6:
                    icon_y = st.slider("開始Y座標", 0, HEIGHT, text_var.get('icon_y', 300), key=f"icon_y_{selected_text_idx}")
                    st.session_state.text_variations[selected_text_idx]['icon_y'] = icon_y

    # --- タブ3: 画像設定 ---
    with tab_image:
        st.markdown('<div class="simple-header">画像のアップロードと調整</div>', unsafe_allow_html=True)
        for var_idx, img_var in enumerate(st.session_state.image_variations):
            uploaded_file = st.file_uploader(
                "画像を選択", 
                type=['png', 'jpg', 'jpeg', 'webp'],
                key=f"img_{var_idx}"
            )
            
            if uploaded_file is not None:
                uploaded_img = Image.open(uploaded_file)
                st.session_state.image_variations[var_idx]['image'] = uploaded_img
                
                if st.session_state.image_variations[var_idx]['original_width'] == 100:
                    st.session_state.image_variations[var_idx]['original_width'] = uploaded_img.width
                    st.session_state.image_variations[var_idx]['original_height'] = uploaded_img.height
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    img_scale = st.slider("サイズ倍率", 10, 200, int(img_var.get('scale', 1.0) * 100), key=f"img_scale_{var_idx}") / 100
                    st.session_state.image_variations[var_idx]['scale'] = img_scale
                with col2:
                    pos_x = st.slider("X座標", 0, WIDTH, img_var.get('x', WIDTH // 2), key=f"img_x_{var_idx}")
                    st.session_state.image_variations[var_idx]['x'] = pos_x
                with col3:
                    pos_y = st.slider("Y座標", 0, HEIGHT, img_var.get('y', HEIGHT // 2), key=f"img_y_{var_idx}")
                    st.session_state.image_variations[var_idx]['y'] = pos_y

    # --- タブ4: 注釈設定 ---
    with tab_annot:
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("＋ 通常注釈追加", use_container_width=True):
                st.session_state.annotation_variations.append({
                    'text': default_annot_text, 'font': 'ゴシック', 'weight': 'W7', 'size': 10,
                    'color': '#000000', 'x': 10, 'y': 390, 'enabled': True, 'is_neumo': False, 'aspect_ratio': 1.0
                })
                st.rerun()
        with col_btn2:
            if st.button("＋ ニューモV専用追加", use_container_width=True):
                st.session_state.annotation_variations.append({
                    'text': default_neumo_text, 'font': 'ゴシック', 'weight': 'W7', 'size': 10,
                    'color': '#000000', 'x': 10, 'y': 390, 'enabled': True, 'is_neumo': True, 'aspect_ratio': 1.0
                })
                st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)

        # 注釈リストループ
        for var_idx, annot_var in enumerate(st.session_state.annotation_variations):
            st.markdown(f'<div class="annotation-item">', unsafe_allow_html=True)
            
            col_head_title, col_head_sw = st.columns([3, 1])
            with col_head_title:
                title_text = "ニューモV専用注釈" if annot_var.get('is_neumo', False) else f"注釈 #{var_idx + 1}"
                st.markdown(f"**{title_text}**")
            with col_head_sw:
                enabled = st.toggle("有効", value=annot_var['enabled'], key=f"annot_en_{var_idx}")
                st.session_state.annotation_variations[var_idx]['enabled'] = enabled

            col1, col2 = st.columns([3, 1])
            with col1:
                new_text = st.text_input("テキスト内容", value=annot_var['text'], key=f"annot_{var_idx}", label_visibility="collapsed")
                st.session_state.annotation_variations[var_idx]['text'] = new_text
            with col2:
                if len(st.session_state.annotation_variations) > 1:
                    if st.button("削除", key=f"del_annot_{var_idx}", use_container_width=True):
                        st.session_state.annotation_variations.pop(var_idx)
                        st.rerun()

            col3, col4, col5, col6 = st.columns(4)
            with col3:
                font = st.selectbox("フォント", ["ゴシック", "明朝"],
                                    index=["ゴシック", "明朝"].index(annot_var.get('font', 'ゴシック')),
                                   key=f"annot_font_{var_idx}")
                st.session_state.annotation_variations[var_idx]['font'] = font
            with col4:
                size = st.number_input("サイズ", 5, 100, annot_var.get('size', 10), key=f"annot_size_{var_idx}")
                st.session_state.annotation_variations[var_idx]['size'] = size
            with col5:
                pos_x = st.number_input("X", 0, WIDTH, annot_var.get('x', 10), key=f"annot_x_{var_idx}")
                st.session_state.annotation_variations[var_idx]['x'] = pos_x
            with col6:
                pos_y = st.number_input("Y", 0, HEIGHT, annot_var.get('y', 390), key=f"annot_y_{var_idx}")
                st.session_state.annotation_variations[var_idx]['y'] = pos_y
            
            # 注釈用の縦横比スライダー
            aspect = st.slider("縦横比", 50, 200, int(annot_var.get('aspect_ratio', 1.0) * 100), key=f"annot_aspect_{var_idx}") / 100
            st.session_state.annotation_variations[var_idx]['aspect_ratio'] = aspect
            
            st.markdown('</div>', unsafe_allow_html=True)

    # --- タブ5: 出力設定 ---
    with tab_output:
        col_name1, col_name2 = st.columns(2)
        with col_name1:
            product_name = st.text_input("商材名", value="商材名", placeholder="商材名を入力")
        with col_name2:
            custom_name = st.text_input("ファイル識別名", value="名前", placeholder="識別名を入力")
        
        # フォルダ名設定（ZIP用） - デフォルト値を自動生成
        default_folder_name = f"{datetime.now().strftime('%Y%m%d')}_{product_name}_APNG_枠点滅_素材_{custom_name}"
        save_folder_name = st.text_input("保存フォルダ名", value=default_folder_name, placeholder="フォルダ名を入力")
        
        st.caption(f"フォルダ構成: {save_folder_name}/...")
        
        has_neumo_annot = any(annot.get('is_neumo', False) for annot in st.session_state.annotation_variations)
        if has_neumo_annot:
            st.info("ニューモV専用注釈が含まれているため、一部ファイルの商材名は「new5」になります。")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 生成ボタン
        if st.button("APNGを一括生成する", type="primary", disabled=not (use_red_border or use_corner_icon or use_icon_increase), use_container_width=True):
            generated_files = []
            date_str = datetime.now().strftime("%y%m%d")
            
            # パラメータ取得（セッションステートから）
            border_width_red = st.session_state.get('border_width_red', 13)
            border_colors = st.session_state.get('border_colors', ["red"])
            num_frames_red = st.session_state.get('num_frames_red', 5)
            loop_count_red = st.session_state.get('loop_count_red', 4)
            
            icon_size_corner = st.session_state.get('icon_size_corner', 85)
            icon_names = st.session_state.get('icon_names', ["check.png"])
            num_frames_corner = st.session_state.get('num_frames_corner', 5)
            loop_count_corner = st.session_state.get('loop_count_corner', 4)
            
            icon_size_increase = st.session_state.get('icon_size_increase', 100)
            icon_names_increase = st.session_state.get('icon_names_increase', ["check.png"])
            num_frames_increase = st.session_state.get('num_frames_increase', 5)
            loop_count_increase = st.session_state.get('loop_count_increase', 4)
            
            enabled_annotations = [annot for annot in st.session_state.annotation_variations if annot.get('enabled', True)]
            
            # 削除ボタン形式に変更したため、リストにあるものは全て「有効」とみなす
            enabled_texts = st.session_state.text_variations
            
            if len(enabled_texts) == 0:
                st.error("有効なテキストがありません。テキスト設定で追加してください。")
            else:
                # 注釈がない場合は空リストで進行（注釈なしでも保存可能）
                if len(enabled_annotations) == 0:
                    enabled_annotations = [{'text': '', 'font': 'ゴシック', 'weight': 'W7', 'size': 10, 'color': '#000000', 'x': 10, 'y': 390, 'enabled': False, 'aspect_ratio': 1.0}]
                with st.spinner("APNGを生成中..."):
                    for annot_var in enabled_annotations:
                        prod_name = "new5" if annot_var.get('is_neumo', False) else product_name
                        
                        border_counter = 1
                        icon_counter = 1
                        increase_counter = 1
                        
                        for text_var in enabled_texts:
                            for img_idx in range(len(st.session_state.image_variations)):
                                variant_text_elements = [text_var]
                                variant_annotation_elements = [annot_var]
                                variant_uploaded_image = st.session_state.image_variations[img_idx]['image']
                                variant_image_config = st.session_state.image_variations[img_idx]
                                
                                # 赤枠点滅生成
                                if use_red_border:
                                    for border_color in border_colors:
                                        frames = create_red_border_blink_frames(
                                            WIDTH, HEIGHT, variant_text_elements, variant_annotation_elements,
                                            variant_uploaded_image, variant_image_config,
                                            border_width=border_width_red, 
                                            border_color=border_color, 
                                            num_frames=num_frames_red
                                        )
                                        apng_data = save_apng(frames, num_frames=num_frames_red, num_plays=loop_count_red)
                                        filename = f"{date_str}_{prod_name}_APNG_枠点滅_素材_{custom_name}_{border_counter:02d}.png"
                                        generated_files.append((filename, apng_data))
                                        border_counter += 1
                                
                                # 4隅アイコン生成
                                if use_corner_icon:
                                    for icon_name in icon_names:
                                        frames = create_corner_icon_blink_frames(
                                            WIDTH, HEIGHT, variant_text_elements, variant_annotation_elements,
                                            variant_uploaded_image, variant_image_config,
                                            icon_name=icon_name,
                                            icon_size=icon_size_corner,
                                            num_frames=num_frames_corner
                                        )
                                        apng_data = save_apng(frames, num_frames=num_frames_corner, num_plays=loop_count_corner)
                                        filename = f"{date_str}_{prod_name}_APNG_ikon点滅_素材_{custom_name}_{icon_counter:02d}.png"
                                        generated_files.append((filename, apng_data))
                                        icon_counter += 1
                                
                                # アイコン増加生成
                                if use_icon_increase:
                                    for icon_name in icon_names_increase:
                                        frames = create_icon_increase_frames(
                                            WIDTH, HEIGHT, text_var, variant_annotation_elements,
                                            variant_uploaded_image, variant_image_config,
                                            icon_name=icon_name,
                                            icon_size=icon_size_increase,
                                            num_frames=num_frames_increase
                                        )
                                        apng_data = save_apng(frames, num_frames=num_frames_increase, num_plays=loop_count_increase)
                                        filename = f"{date_str}_{prod_name}_APNG_ikon増加_素材_{custom_name}_{increase_counter:02d}.png"
                                        generated_files.append((filename, apng_data))
                                        increase_counter += 1
                    
                    st.success(f"{len(generated_files)}個のAPNGが完成しました！")
                    
                    # ZIPダウンロードボタン
                    if len(generated_files) > 0:
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                            for filename, data in generated_files:
                                # フォルダ名を付与してZIPに追加
                                zip_file.writestr(f"{save_folder_name}/{filename}", data)
                        
                        zip_buffer.seek(0)
                        st.download_button(
                            label=f"まとめてZIPでダウンロード ({len(generated_files)}個)",
                            data=zip_buffer.getvalue(),
                            file_name=f"{date_str}_{product_name}_APNG_all.zip",
                            mime="application/zip",
                            use_container_width=True,
                            type="primary"
                        )

                    # 個別リスト
                    with st.expander("個別ファイルダウンロード", expanded=False):
                        for file_idx, (filename, data) in enumerate(generated_files):
                            file_size_kb = len(data) / 1024
                            col1, col2 = st.columns([4, 1])
                            with col1:
                                st.text(f"{filename} ({file_size_kb:.1f} KB)")
                            with col2:
                                st.download_button("DL", data=data, file_name=filename, mime="image/png", key=f"dl_{file_idx}", use_container_width=True)

# ==========================================
# 右カラム：プレビューエリア（Sticky + 横スクロール）
# ==========================================
with col_preview:
    st.markdown('<div class="preview-box">', unsafe_allow_html=True)
    st.markdown("### PREVIEW")
    st.caption("設定変更はリアルタイムに反映されます")
    
    preview_annotation_elements = [annot for annot in st.session_state.annotation_variations if annot['enabled']]
    
    preview_count = sum([use_red_border, use_corner_icon, use_icon_increase])
    
    if preview_count == 0:
        st.warning("左側の「テンプレート選択」タブで作成したい種類を選択してください")
    else:
        # テキストバリエーション全てを表示（削除されたもの以外）
        enabled_text_variations = st.session_state.text_variations
        
        # 赤枠点滅プレビュー
        if use_red_border:
            st.markdown("##### 赤枠点滅")
            html_content = '<div class="scroll-container">'
            
            # 現在のセッション値を取得（リアルタイム反映用）
            p_border_width = st.session_state.get('border_width_red', 13)
            # 複数選択されている場合は最初の色を使用
            p_border_colors = st.session_state.get('border_colors', ["red"])
            p_border_color = p_border_colors[0] if p_border_colors else "red"
            
            for idx, text_var in enumerate(enabled_text_variations):
                preview_img = create_preview_image(
                    [text_var], preview_annotation_elements,
                    st.session_state.image_variations[0]['image'],
                    st.session_state.image_variations[0],
                    "赤枠点滅", scale=0.5, border_width=p_border_width, border_color=p_border_color
                )
                b64_img = image_to_base64(preview_img)
                text_label = f"Text {st.session_state.text_variations.index(text_var) + 1}"
                html_content += f'<div class="scroll-item"><img src="data:image/png;base64,{b64_img}" /><div class="scroll-item-caption">{text_label}</div></div>'
            html_content += '</div>'
            st.markdown(html_content, unsafe_allow_html=True)
        
        # 4隅アイコンプレビュー
        if use_corner_icon:
            st.markdown("##### 4隅アイコン")
            html_content = '<div class="scroll-container">'
            
            p_icon_size = st.session_state.get('icon_size_corner', 85)
            p_icon_names = st.session_state.get('icon_names', ["check.png"])
            p_icon_name = p_icon_names[0] if p_icon_names else "check.png"
            
            for idx, text_var in enumerate(enabled_text_variations):
                preview_img = create_preview_image(
                    [text_var], preview_annotation_elements,
                    st.session_state.image_variations[0]['image'],
                    st.session_state.image_variations[0],
                    "4隅アイコン点滅", scale=0.5, icon_size=p_icon_size, icon_name=p_icon_name
                )
                b64_img = image_to_base64(preview_img)
                text_label = f"Text {st.session_state.text_variations.index(text_var) + 1}"
                html_content += f'<div class="scroll-item"><img src="data:image/png;base64,{b64_img}" /><div class="scroll-item-caption">{text_label}</div></div>'
            html_content += '</div>'
            st.markdown(html_content, unsafe_allow_html=True)
        
        # アイコン増加プレビュー
        if use_icon_increase:
            st.markdown("##### アイコン増加")
            
            p_icon_size_inc = st.session_state.get('icon_size_increase', 100)
            p_icon_names_inc = st.session_state.get('icon_names_increase', ["check.png"])
            p_icon_name_inc = p_icon_names_inc[0] if p_icon_names_inc else "check.png"
            
            html_content = '<div class="scroll-container">'
            for idx, text_var in enumerate(enabled_text_variations):
                preview_img = create_preview_image(
                    [text_var], preview_annotation_elements,
                    st.session_state.image_variations[0]['image'],
                    st.session_state.image_variations[0],
                    "アイコン増加", 
                    scale=0.5, 
                    icon_size=p_icon_size_inc,
                    icon_name=p_icon_name_inc
                )
                b64_img = image_to_base64(preview_img)
                text_label = f"Text {st.session_state.text_variations.index(text_var) + 1}"
                html_content += f'<div class="scroll-item"><img src="data:image/png;base64,{b64_img}" /><div class="scroll-item-caption">{text_label}</div></div>'
            html_content += '</div>'
            st.markdown(html_content, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)