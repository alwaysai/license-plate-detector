import time
import edgeiq

"""
Use object detection to detect objects in the frame in realtime. The
types of objects detected can be changed by selecting different models.

To change the computer vision model, follow this guide:
https://dashboard.alwaysai.co/docs/application_development/changing_the_model.html

To change the engine and accelerator, follow this guide:
https://dashboard.alwaysai.co/docs/application_development/changing_the_engine_and_accelerator.html
"""


def main():
    obj_detect = edgeiq.ObjectDetection(
            "alwaysai/vehicle_license_mobilenet_ssd")
    obj_detect.load(engine=edgeiq.Engine.DNN)

    print("Loaded model:\n{}\n".format(obj_detect.model_id))
    print("Engine: {}".format(obj_detect.engine))
    print("Accelerator: {}\n".format(obj_detect.accelerator))
    print("Labels:\n{}\n".format(obj_detect.labels))

    tracker = edgeiq.CentroidTracker(deregister_frames=5)
    fps = edgeiq.FPS()

    try:
        video_paths = edgeiq.list_files(
                            base_path="./video/",
                            valid_exts=".mp4"
                        )
        streamer = edgeiq.Streamer().setup()

        for video_path in video_paths:
            with edgeiq.FileVideoStream(video_path, play_realtime=True)\
                    as video_stream:

                try:
                    # Allow Webcam to warm up
                    time.sleep(2.0)
                    fps.start()

                    # loop detection
                    while video_stream.more():
                        frame = video_stream.read()
                        predictions = []

                        results = obj_detect.detect_objects(
                                                frame,
                                                confidence_level=.5
                                            )

                        # Generate text to display on streamer
                        text = ["Model: {}".format(obj_detect.model_id)]
                        text.append(
                                "Inference time: {:1.3f} s".format(
                                    results.duration
                                    )
                                )
                        text.append("Objects:")

                        # Update tracker results with the new predictions
                        objects = tracker.update(results.predictions)

                        if len(objects) == 0:
                            text.append("no predictions")
                        else:
                            # Create a new prediction list
                            for (object_id, prediction) in objects.items():
                                text.append("{}_{}: {:2.2f}%".format(
                                                    prediction.label,
                                                    object_id,
                                                    prediction.confidence * 100
                                                )
                                            )
                                new_label = '{} {}'.format(
                                                    prediction.label,
                                                    object_id
                                                )
                                prediction.label = '{} {}'.format(
                                                    new_label.split(" ")[0],
                                                    object_id
                                                )
                                predictions.append(prediction)

                        # Mark up the image and update text
                        frame = edgeiq.markup_image(
                                    frame, predictions,
                                    show_labels=True,
                                    show_confidences=False,
                                    colors=obj_detect.colors,
                                    line_thickness=4,
                                    font_size=1,
                                    font_thickness=4
                                )

                        streamer.send_data(frame, text)

                        fps.update()

                        if streamer.check_exit():
                            break
                except edgeiq.NoMoreFrames:
                    continue

    finally:
        fps.stop()
        streamer.close()
        print("elapsed time: {:.2f}".format(fps.get_elapsed_seconds()))
        print("approx. FPS: {:.2f}".format(fps.compute_fps()))

        print("Program Ending")


if __name__ == "__main__":
    main()
