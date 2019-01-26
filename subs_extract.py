#!/usr/bin/env python3

import sys
import os
import subprocess


def timecode_to_milliseconds(code):
    """ Takes a time code and converts it into an integer of milliseconds.
    """
    elements = code.split(":")
    assert(len(elements) == 3)
    milliseconds = int(elements[0]) * 3600000
    milliseconds += int(elements[1]) * 60000
    milliseconds += int(float(elements[2]) * 1000)
    return milliseconds


def milliseconds_to_timecode(milliseconds):
    """ Takes a time in milliseconds and converts it into a time code.
    """
    hours = milliseconds // 3600000
    milliseconds %= 3600000
    minutes = milliseconds // 60000
    milliseconds %= 60000
    seconds = milliseconds // 1000
    milliseconds %= 1000
    return "{}:{:02}:{:02}.{:02}".format(hours, minutes, seconds, milliseconds // 10)


def parse_ass_dialogue_line(line):
    """ Parses a dialogue line from a .ass subtitles files, returning
        the start/end times and the dialogue text as a tuple.
    """
    assert(line.strip().startswith("Dialogue:"))
    elements = line.split(',')
    return (elements[1].strip(), elements[2].strip(), elements[-1].strip())

def parse_ass_file(path, padding=0):
    """ Parses an entire .ass file, extracting the dialogue.

        Returns a list of (start, length, dialogue) tuples, one for each
        subtitle found in the file.  A padding of "padding" milliseconds is
        added to the start/end times.
    """
    start_times = set() # Used to prevent duplicates
    subtitles = []
    with open(path) as f:
        for line in f:
            if line.strip().startswith("Dialogue:"):
                sub = parse_ass_dialogue_line(line)
                if (sub[0] not in start_times) and (sub[2] != ""):
                    start_times |= set(sub[0])
                    start = max(timecode_to_milliseconds(sub[0]) - padding, 0)
                    end = timecode_to_milliseconds(sub[1]) + padding
                    length = end - start
                    subtitles += [(
                        milliseconds_to_timecode(start),
                        milliseconds_to_timecode(length),
                        sub[2],
                    )]
    subtitles.sort()
    return subtitles


if __name__ == "__main__":
    subs_filename = sys.argv[1]
    video_filename = sys.argv[2]
    dir_name = video_filename.rsplit(".")[0]
    base_name = os.path.basename(dir_name)

    # Parse the subtitles file
    subtitles = parse_ass_file(subs_filename, 300)

    # Create the directory for the new files if it doesn't already exist.
    try:
        os.mkdir(dir_name)
    except FileExistsError:
        pass
    except Exception as e:
        raise e

    # Process the subtitles
    for item in subtitles:
        print("\n\n========================================================")
        print("Extracting \"{}\"".format(item[2]))
        print("========================================================")

        # Generate base filename
        base_filename = os.path.join(dir_name, "{} -- {}".format(base_name, item[0].replace(":", "_").replace(".", "-")))

        # Write text file of subtitle
        subtitle_out_filepath = base_filename + ".txt"
        if not os.path.isfile(subtitle_out_filepath):
            with open(subtitle_out_filepath, 'w') as f:
                f.write(item[2])

        # Extract audio of subtitle into mp3 file
        audio_out_filepath_1 = base_filename + ".wav"
        audio_out_filepath_2 = base_filename + ".mp3"
        if (not os.path.isfile(audio_out_filepath_1)) and (not os.path.isfile(audio_out_filepath_2)):
            # Extract just the subtitle audio segment into a temporary wave
            # file.  We do this as a first step so that when we apply the
            # normalization filter it doesn't operate on the seek area around
            # the audio we want, which is slower.
            subprocess.Popen([
                "ffmpeg",
                "-n",
                "-vn",
                "-ss",
                item[0],
                "-i",
                video_filename,
                "-t",
                item[1],
                "-ar",
                "44100",
                "-ac",
                "1",
                audio_out_filepath_1,
            ]).wait()

            # Normalize volume levels and write to mp3 file.
            subprocess.Popen([
                "ffmpeg",
                "-n",
                "-i", audio_out_filepath_1,
                "-aq", "8",
                "-af", "loudnorm",  # Normalize audio according to EBU R128
                audio_out_filepath_2,
            ]).wait()

            # Remove the temp wav file.
            os.remove(audio_out_filepath_1)

    print("\n\nDone extracting subtitles!")