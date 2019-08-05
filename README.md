# Subs Extract

A simple Python script that uses ffmpeg to extract subtitles and audio from a video.  The purpose is to facilitate creating flash cards from foreign-language TV shows and movies.

It takes as input a video file and a corresponding .ssa, .ass, .vtt, or .srt subtitle file, like this:

```
subs_extract.py a_really_cool_show.mp4 a_really_cool_show.srt
```

And it then creates a text file and mp3 file for each sentence in the subtitles, putting them in a new directory named after the video file.  It also creates a deck file that can be imported to Anki, with the following fields per note:

1. The line's subtitle text.
2. The filename of line's audio file, wrapped in an Anki audio tag.
3. The name of the video file the line came from, without the file extension (this basically identifies the movie/episode, assuming your video files are named appropriately).
4. A timestamp, indicating where in the video file the line is.
