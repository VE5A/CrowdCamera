import tensorflow as tf
import keras

import cv2
from skimage.io import *
from skimage.transform import resize
import skvideo.io
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import colorsys

import os
from os.path import join
import sys
import random
import time

import matplotlib.pyplot as plt

from keras import backend as K
from keras.models import load_model

module_path = os.path.abspath(os.path.join('crowd_detector'))
if module_path not in sys.path:
    sys.path.append(module_path)

from yad2k.models.keras_yolo import yolo_eval, yolo_head

def prepare_yolo(model_path, class_names):
    yolo_model = load_model(model_path)
    yolo_outputs = yolo_head(yolo_model.output, anchors, len(class_names))
    model_output_channels = yolo_model.layers[-1].output_shape[-1]
    assert model_output_channels == num_anchors * (num_classes + 5), \
        'Mismatch between model and given anchor and class sizes. ' \
        'Specify matching anchors and classes with --anchors_path and ' \
        '--classes_path flags.'
    print('{} model, anchors, and classes loaded.'.format(model_path))

    model_image_size = yolo_model.layers[0].input_shape[1:3]
    is_fixed_size = model_image_size != (None, None)

    # Generate colors for drawing bounding boxes.
    hsv_tuples = [(x / len(class_names), 1., 1.)
                  for x in range(len(class_names))]
    colors = list(map(lambda x: colorsys.hsv_to_rgb(*x), hsv_tuples))
    colors = list(
        map(lambda x: (int(x[0] * 255), int(x[1] * 255), int(x[2] * 255)),
            colors))
    random.seed(10101)  # Fixed seed for consistent colors across runs.
    random.shuffle(colors)  # Shuffle colors to decorrelate adjacent classes.
    random.seed(None)  # Reset seed to default.

    input_image_shape = K.placeholder(shape=(2, ))
    boxes, scores, classes = yolo_eval(
        yolo_outputs,
        input_image_shape,
        score_threshold=args['score_threshold'],
        iou_threshold=args['iou_threshold'],
        max_boxes=50
    )

    model_image_size = yolo_model.layers[0].input_shape[1:3]
    is_fixed_size = model_image_size != (None, None)

    sess = K.get_session()
    
    return {
        'yolo_model': yolo_model,
        'input_image_shape': input_image_shape,
        'boxes': boxes,
        'scores': scores,
        'classes': classes,
        'sess': sess,
        'model_image_size': model_image_size,
        'class_names': class_names,
        'colors': colors
    }

def predict_on_image(img, yolo, person_only=False):
    pil_img = Image.fromarray(img)
    img = cv2.resize(img, tuple(reversed(yolo['model_image_size'])))
    img = np.expand_dims(img, 0).astype('float32') / 255.

    out_boxes, out_scores, out_classes = yolo['sess'].run(
        [yolo['boxes'], yolo['scores'], yolo['classes']],
        feed_dict={
            yolo['yolo_model'].input: img,
            yolo['input_image_shape']: [pil_img.size[1], pil_img.size[0]],
            K.learning_phase(): 0
        })
    print('Found {} boxes'.format(len(out_boxes)))

    font = ImageFont.truetype(
        font='crowd_detector/font/FiraMono-Medium.otf',
        size=np.floor(3e-2 * pil_img.size[1] + 0.5).astype('int32'))
    thickness = (pil_img.size[0] + pil_img.size[1]) // 300

    for i, c in reversed(list(enumerate(out_classes))):
        predicted_class = yolo['class_names'][c]
        if person_only and predicted_class != 'person':
            continue
        
        box = out_boxes[i]
        score = out_scores[i]

        label = '{} {:.2f}'.format(predicted_class, score)

        draw = ImageDraw.Draw(pil_img)
        label_size = draw.textsize(label, font)

        top, left, bottom, right = box
        top = max(0, np.floor(top + 0.5).astype('int32'))
        left = max(0, np.floor(left + 0.5).astype('int32'))
        bottom = min(pil_img.size[1], np.floor(bottom + 0.5).astype('int32'))
        right = min(pil_img.size[0], np.floor(right + 0.5).astype('int32'))
        print(label, (left, top), (right, bottom))

        if top - label_size[1] >= 0:
            text_origin = np.array([left, top - label_size[1]])
        else:
            text_origin = np.array([left, top + 1])

        # My kingdom for a good redistributable image drawing library.
        for i in range(thickness):
            draw.rectangle(
                [left + i, top + i, right - i, bottom - i],
                outline=yolo['colors'][c])
        draw.rectangle(
            [tuple(text_origin), tuple(text_origin + label_size)],
            fill=yolo['colors'][c])
        draw.text(text_origin, label, fill=(0, 0, 0), font=font)
        del draw

    person_count = np.sum([1 if yolo['class_names'][c] == 'person' else 0 for c in out_classes])
    
    return pil_img, person_count

args = dict()
args['model_path'] = 'crowd_detector/models/yolo.h5'
args['anchors_path'] = 'crowd_detector/model_data/yolo_anchors.txt'
args['classes_path'] = 'crowd_detector/model_data/coco_classes.txt'
args['score_threshold'] = .3
args['iou_threshold'] = .5

model_path = os.path.expanduser(args['model_path'])
assert model_path.endswith('.h5'), 'Keras model must be a .h5 file.'
anchors_path = os.path.expanduser(args['anchors_path'])
classes_path = os.path.expanduser(args['classes_path'])

with open(classes_path) as f:
    class_names = f.readlines()
class_names = [c.strip() for c in class_names]

with open(anchors_path) as f:
    anchors = f.readline()
    anchors = [float(x) for x in anchors.split(',')]
    anchors = np.array(anchors).reshape(-1, 2)
    
num_classes = len(class_names)
num_anchors = len(anchors)
