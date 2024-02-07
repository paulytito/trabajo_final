# -*- coding: utf-8 -*-
"""yolo5MultiplePolygon.py

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/12uEZqU9A6VqDBetdm24mDDv92MFh2sg6
"""

# @title
import numpy as np
import supervision as sv
from ultralytics import YOLO
import time
import torch
import argparse
import pandas as pd
import cv2

parser = argparse.ArgumentParser(
                    prog='yolov5',
                    description='Este programa detecta y cuenta personas en regiones poligonales',
                    epilog='Texto al final de la ayuda')

parser.add_argument('-i', '--input',required=True)      # option that takes a value
parser.add_argument('-o', '--output',required=True)
parser.add_argument('-fps', '--fps', type=int, default=0, help='Tramas por segundo para salida de vídeo y nombre del archivo del tipo CSV')

args = parser.parse_args()

fps_valor = args.fps

class CountObject():

    def __init__(self,input_video_path,output_video_path) -> None:

        self.model = torch.hub.load('ultralytics/yolov5', 'yolov5x6')
        self.colors = sv.ColorPalette.default()

        self.input_video_path = input_video_path
        self.output_video_path = output_video_path

        self.polygons = [
            np.array([
                [540,  985 ],
                [1620, 985 ],
                [2160, 1920],
                [1620, 2855],
                [540,  2855],
                [0,    1920]
            ], np.int32),
            np.array([
                [0,    1920],
                [540,  985 ],
                [0,    0   ]
            ], np.int32),
            np.array([
                [1620, 985 ],
                [2160, 1920],
                [2160,    0]
            ], np.int32),
            np.array([
                [540,  985 ],
                [0,    0   ],
                [2160, 0   ],
                [1620, 985 ]
            ], np.int32),
            np.array([
                [0,    1920],
                [0,    3840],
                [540,  2855]
            ], np.int32),
            np.array([
                [2160, 1920],
                [1620, 2855],
                [2160, 3840]
            ], np.int32),
            np.array([
                [1620, 2855],
                [540,  2855],
                [0,    3840],
                [2160, 3840]
            ], np.int32)
        ]

        self.video_info = sv.VideoInfo.from_video_path(input_video_path)
        self.zones = [
            sv.PolygonZone(
                polygon=polygon,
                frame_resolution_wh=self.video_info.resolution_wh
            )
            for polygon
            in self.polygons
        ]

        self.zone_annotators = [
            sv.PolygonZoneAnnotator(
                zone=zone,
                color=self.colors.by_idx(index),
                thickness=6,
                text_thickness=8,
                text_scale=4
            )
            for index, zone
            in enumerate(self.zones)
        ]

        self.box_annotators = [
            sv.BoxAnnotator(
                color=self.colors.by_idx(index),
                thickness=4,
                text_thickness=4,
                text_scale=2
                )
            for index
            in range(len(self.polygons))
        ]

        self.time = 0
        self.time_records = [ ]

    def process_video(self):
      cap = cv2.VideoCapture(self.input_video_path)
      frame_rate = fps_valor
      original_fps = int(cap.get(cv2.CAP_PROP_FPS))
      frame_width = int(cap.get(3))
      frame_height = int(cap.get(4))

      if frame_rate == 0:
        frame_rate = original_fps

      out = cv2.VideoWriter(self.output_video_path, cv2.VideoWriter_fourcc(*'mp4v'), frame_rate, (frame_width, frame_height))

      while True:
        ret, frame = cap.read()
        if not ret:
          break

        processed_frame = self.process_frame(frame, self.time)
        out.write(processed_frame)

        self.time +=1
        if frame_rate != original_fps:
            for _ in range (original_fps // frame_rate - 1):
              cap.read()

      cap.release()
      out.release()
      cv2.destroyAllWindows()

      column_names = ['Tiempo'] + ['Poligono {i+1}' for i in range (len(self.polygons))]
      df = pd.DataFrame(self.time_records, columns=column_names)
      df.to_csv('resultadosFPS{fps_valor}.csv', index=False)



    def process_frame(self,frame: np.ndarray, i) -> np.ndarray:
        # detect
        self.time +=1
        results = self.model(frame, size=1280)
        detections = sv.Detections.from_yolov5(results)
        detections = detections[(detections.class_id == 0) & (detections.confidence > 0.5)]

        counts = [0] * len(self.polygons)

        #for zone, zone_annotator, box_annotator in zip(self.zones, self.zone_annotators, self.box_annotators):
            #mask = zone.trigger(detections=detections)
            #detections_filtered = detections[mask]
            #frame = box_annotator.annotate(scene=frame, detections=detections_filtered, skip_label=True)
            #frame = zone_annotator.annotate(scene=frame)
            #counts[index] = len(detections_filtered)

        for index, (zone, zone_annotator, box_annotator) in enumerate (
            zip(self.zones, self.zone_annotators, self.box_annotators)
        ):
          mask = zone.trigger(detections=detections)
          detections_filtered = detections[mask]
          frame = box_annotator.annotate(scene=frame, detections=detections_filtered, skip_label=True)
          frame = zone_annotator.annotate(scene=frame)
          counts[index] = len(detections_filtered)

        self.time_records.append([self.time] + counts)

        return frame

    def process_video(self):

        sv.process_video(source_path=self.input_video_path, target_path=self.output_video_path, callback=self.process_frame)


if __name__ == "__main__":

    obj = CountObject(args.input,args.output)

    start_time = time.time()

    print("Procesando el video original...")
    obj.process_video()

    end_time = time.time()
    elapsed_time = end_time - start_time

    print("Procesamiento completado")
    print(f"Tiempo total de ejecucion: {elapsed_time:.2f} segundos")
