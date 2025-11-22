# nodes/preprocess.py
import tensorflow as tf
import numpy as np

IMG_SIZE = (224, 224)  # match your finetuned model input size

def run(inputs: dict):
    image_path = inputs["image_path"]
    # load and preprocess
    img = tf.io.read_file(image_path)
    img = tf.io.decode_image(img, channels=3, expand_animations=False)
    img = tf.image.resize(img, IMG_SIZE)
    img = tf.cast(img, tf.float32)
    img_pre = tf.keras.applications.mobilenet_v3.preprocess_input(img)
    # model expects batched input
    batch = tf.expand_dims(img_pre, axis=0)

    state = dict(inputs)
    state.update({
        "image_path": image_path,
        "image_tensor": batch,
        "orig_shape": tf.shape(img).numpy().tolist()
    })
    return state
