#!/usr/bin/env python3

import sys
import os
import subprocess
import re


def timecode_to_milliseconds(code):
    """ Takes a time code and converts it into an integer of milliseconds.
    """
    elements = code.replace(",", ".").split(":")
    assert(len(elements) < 4)
    
    milliseconds = 0
    if len(elements) >= 1:
        milliseconds += int(float(elements[-1]) * 1000)
    if len(elements) >= 2:
        milliseconds += int(elements[-2]) * 60000
    if len(elements) >= 3:
        milliseconds += int(elements[-3]) * 3600000
    
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


def parse_ass_file(path, padding=0):
    """ Parses an entire .ass file, extracting the dialogue.

        Returns a list of (start, length, dialogue) tuples, one for each
        subtitle found in the file.  A padding of "padding" milliseconds is
        added to the start/end times.
    """
    subtitles = []
    with open(path) as f:
        # First find out the field order of the dialogue.
        found_start = False
        fields = {}
        for line in f:
            if not found_start:
                found_start = line.strip() == "[Events]"
            elif line.strip().startswith("Format:"):
                line = line[7:].strip()
                tmp = line.split(",")
                for i in range(len(tmp)):
                    fields[tmp[i].strip().lower()] = i
                break
        if ("start" not in fields) or ("end" not in fields) or ("text" not in fields):
            raise Exception("'Start', 'End', or 'Text' field not found.")

        # Then parse the dialogue lines.
        start_times = set() # Used to prevent duplicates
        for line in f:
            if line.strip().startswith("Dialogue:"):
                elements = line[9:].strip().split(',', len(fields) - 1)
                start_element = elements[fields["start"]].strip()
                end_element = elements[fields["end"]].strip()
                text_element = elements[-1].strip()

                if (start_element not in start_times) and (text_element != ""):
                    start_times |= set(start_element)
                    start = max(timecode_to_milliseconds(start_element) - padding, 0)
                    end = timecode_to_milliseconds(end_element) + padding
                    length = end - start
                    subtitles += [(
                        milliseconds_to_timecode(start),
                        milliseconds_to_timecode(length),
                        text_element,
                    )]
    subtitles.sort()
    return subtitles


def parse_vtt_file(path, padding=0):
    """ Parses an entire WebVTT/SRT file, extracting the dialogue.

        Returns a list of (start, length, dialogue) tuples, one for each
        subtitle found in the file.  A padding of "padding" milliseconds is
        added to the start/end times.
    """
    subtitles = []
    with open(path) as f:
        start_times = set() # Used to prevent duplicates
        for line in f:
            if "-->" in line:
                # Get the timing.
                times = line.split("-->")
                start = max(timecode_to_milliseconds(times[0].strip()) - padding, 0)
                end = timecode_to_milliseconds(times[1].strip()) + padding
                length = end - start

                # Get the text.
                text = ""
                next_line = f.readline()
                while next_line.strip() != "":
                    text += next_line
                    next_line = f.readline()
                text = text.strip()

                # Process text to get rid of unnecessary tags.
                text = re.sub("</?ruby>", "", text)
                text = re.sub("<rp>.*?</rp>", "", text)
                text = re.sub("<rt>.*?</rt>", "", text)

                # Add to the subtitles list.
                if (start not in start_times) and (text != ""):
                    start_times |= set([start])
                    subtitles += [(
                        milliseconds_to_timecode(start),
                        milliseconds_to_timecode(length),
                        text,
                    )]
    return subtitles


def parse_subtitle_file(filepath, padding=0):
    """ Parses a subtitle file, attempting to automatically determine the
        file format for parsing.
    """
    if filepath.endswith(".ass") or filepath.endswith(".ssa"):
        return parse_ass_file(filepath, padding)
    elif filepath.endswith(".vtt") or filepath.endswith(".srt"):
        return parse_vtt_file(filepath, padding)
    else:
        raise "Unknown subtitle format.  Supported formats are SSA, ASS, VTT, and SRT."


def find_closest_sub(subs_list, timecode, max_diff_milliseconds):
    """ Finds the sub in the given list with the start time closest to timecode.

        Will only return a matching sub if the start time difference is less
        than max_diff_milliseconds.  Otherwise it will return None.
    """
    time_mil = timecode_to_milliseconds(timecode)

    # This certainly isn't the most efficient way to do this, but it's
    # dead-simple and does not appear to be a performance bottleneck at all.
    closest_so_far = -1
    closest_diff = max_diff_milliseconds
    for i in range(len(subs_list)):
        sub_start = timecode_to_milliseconds(subs_list[i][0])
        diff = abs(time_mil - sub_start)
        if diff < closest_diff:
            closest_so_far = i
            closest_diff = diff

    if closest_so_far >= 0:
        return subs_list[closest_so_far]
    else:
        return None


if __name__ == "__main__":
    video_filename = sys.argv[1]
    subs_filename = sys.argv[2]
    second_subs_filename = None
    if len(sys.argv) >= 4:
        second_subs_filename = sys.argv[3]
    dir_name = video_filename.rsplit(".")[0]
    base_name = os.path.basename(dir_name)

    # Parse the subtitle files
    subtitles = parse_subtitle_file(subs_filename, 300)
    second_subs = parse_subtitle_file(second_subs_filename, 300) if second_subs_filename else None

    # Create the directory for the new files if it doesn't already exist.
    try:
        os.mkdir(dir_name)
    except FileExistsError:
        pass
    except Exception as e:
        raise e

    # Set up deck file
    deck_out_filepath = os.path.join(dir_name, "0_deck -- {}.txt".format(base_name))
    deck_file = open(deck_out_filepath, 'w')

    # Process the subtitles
    first_card = True
    for item in subtitles:
        print("\n\n========================================================")
        print("Extracting \"{}\"".format(item[2]))
        print("========================================================")

        # Generate base filename
        base_filename = os.path.join(dir_name, "{} -- {}".format(base_name, item[0].replace(":", "_").replace(".", "-")))

        # Find matching alt sub if any.
        if second_subs:
            alt_sub = find_closest_sub(second_subs, item[0], 1000)
            if alt_sub:
                alt_sub = alt_sub[2]
            else:
                alt_sub = ""

        # Write text file of subtitle
        subtitle_out_filepath = base_filename + ".txt"
        if not os.path.isfile(subtitle_out_filepath):
            with open(subtitle_out_filepath, 'w') as f:
                f.write(item[2])
                if second_subs:
                    f.write("\n\n" + alt_sub)

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

            # Extract video frame
            image_out_filepath = base_filename + ".jpg"
            image_timecode = milliseconds_to_timecode(
                timecode_to_milliseconds(item[0])
                + (timecode_to_milliseconds(item[1]) // 2 )
            )
            subprocess.Popen([
                "ffmpeg",
                "-ss",
                image_timecode,
                "-i",
                video_filename,
                "-vf",
                "scale='min(480,iw)':'min(240,ih)':force_original_aspect_ratio=decrease",
                "-frames:v",
                "1",
                "-q:v",
                "6",
                "-y",
                image_out_filepath,
            ]).wait()

            # Add card to deck file as well.
            if not first_card:
                deck_file.write("\n")
            first_card = False
            deck_file.write(item[2].replace("\t", "    ").replace("\r\n", "</br>").replace("\n", "</br>") + "\t")
            deck_file.write("[sound:{}]".format(os.path.basename(audio_out_filepath_2)) + "\t")
            if second_subs:
                deck_file.write(alt_sub.replace("\t", "    ").replace("\r\n", "</br>").replace("\n", "</br>") + "\t")
            deck_file.write('"<img src=""{}"">"'.format(os.path.basename(image_out_filepath)) + "\t")
            deck_file.write(base_name + "\t")
            deck_file.write("{}".format(item[0].rsplit(".")[0]))

    deck_file.close()

    print("\n\nDone extracting subtitles!")