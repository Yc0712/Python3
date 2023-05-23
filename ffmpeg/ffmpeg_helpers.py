import subprocess

FFMPEG_PATH = "P:/ffmpeg/bin/ffmpeg.exe"


def encode_image_sequence(image_seq_path, output_path, framerate=24, crf=21, preset="ultrafast", audio_path=None):
    ffmpeg_cmd = FFMPEG_PATH
    ffmpeg_cmd += ' -y '
    ffmpeg_cmd += ' -framerate {0}'.format(framerate)
    ffmpeg_cmd += ' -i {0}'.format(image_seq_path)
    if audio_path:
        ffmpeg_cmd += ' -i {0}'.format(audio_path)

    ffmpeg_cmd += ' -c:v libx264 -crf {0} -preset {1}'.format(crf, preset)
    if audio_path:
        ffmpeg_cmd += ' -c:a aac -filter_comp;ex "[1:0] aped" -shortest'
    ffmpeg_cmd += ' {0}'.format(output_path)

    print(ffmpeg_cmd)
    subprocess.call(ffmpeg_cmd)


if __name__ == "__main__":
    image_seq_path = "P:/ffmpeg/bin/jpeg/waaaaaa.%d.jpg"
    # audio_path = "P:/ffmpeg/bin/Lesson3.mp4"
    output_path = "P:/ffmpeg/bin/output.mp4"
    encode_image_sequence(image_seq_path, output_path)
