from ultralytics import YOLO # Предоставляет YOLO (модель для обнаружения объектов, сегментации).
import cv2 #Работа с изображениями: чтение, декодирование, преобразование цветовых пространств, ресайз, отрисовка боксов.
import numpy as np #Работа с многомерными массивами (изображения в памяти) — основа для OpenCV и YOLO.
import base64 #Кодирование/декодирование данных в формате Base64 (передача изображений в текстовом виде).

from io import BytesIO
from PIL import Image

# --- Глобальные объекты (инициализируются один раз) ---
_yolo_model = None
_calories_db = None

def get_yolo_model():
    global _yolo_model
    if _yolo_model is None:
        _yolo_model = YOLO('yolov8n.pt')
    return _yolo_model

#def get_calories_db():
#    global _calories_db
#    if _calories_db is None:
#        _calories_db = {
#            "apple": 52, "banana": 89, "tomato": 18, "onion": 40,
#            "pizza": 285, "cheese": 402, "sausage": 330,
#            # ... добавьте свои продукты
#        }
#        print("✅ Модель и база данных загружены")
#    return _calories_db


def analyze_image_sync(image_data: str, image_format: str):
    calibration_classes = ["fork", "knife", "spoon", "cell phone", "remote"]  # имена классов из COCO
    # загрузка, YOLO, парсинг
    """
    Синхронно анализирует изображение: загрузка, YOLO, парсинг, расчёт калорий.
    Возвращает словарь с результатами.
    """
    #1. Загружаем изображение


    if image_format == "base64":
        if image_data.startswith("data:image"):
            image_data = image_data.split(",")[1]
        img_bytes = base64.b64decode(image_data)
        np_arr = np.frombuffer(img_bytes, dtype=np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Не удалось декодировать изображение из base64")
    elif image_format == "file":
        img = cv2.imread(image_data)
        if img is None:
            # Вызываем исключение
            raise ValueError(f"Не удалось загрузить файл: {image_data}")
    else:
        # Вызываем исключение
        raise ValueError(f"Неподдерживаемый формат: {image_format}")

    #2. Запускаем YOLO
    model = get_yolo_model()
    results = model(img)

    #3. Парсим результаты
    #cal_db = get_calories_db()
    detected = []
    confidences = {}
    calibration_objects = [] # объекты для калибровки

    for r in results:
        for box in r.boxes: # type: ignore[attr-defined] # Компилятор переживает, что типы будут не совпадать, го это не критично
            # Убрать ошибку не получается, но эна не влияет.
            class_id = int(box.cls[0])
            name = model.names[class_id]
            if name in calibration_classes:
                # Получаем координаты
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                width = x2 - x1
                height = y2 - y1
                area = width * height
                confidence = float(box.conf[0])
                calibration_objects.append({
                    "name": name,
                    "bbox": (x1, y1, x2, y2),
                    "width_px": width,
                    "height_px": height,
                    "area_px": area,
                    "confidence": confidence
                })

            confidence = float(box.conf[0])
            if confidence < 0.3:
                continue

    return {
        "detected_ingredients": detected,
        "calibration_objects" :calibration_objects,
        "confidences": confidences,
        "message_text": f"Найдено {len(detected)} ингредиентов: {', '.join(detected)}"
    }
