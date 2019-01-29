# Subs Extract

A simple Python script that uses ffmpeg to extract subtitles and audio from a video.  The purpose is to facilitate creating flash cards from foreign-language TV shows and movies.

It takes as input an .ssa, .ass, .vtt, or .srt subtitle file and corresponding video file, like this:

```
subs_extract.py a_really_cool_show.srt a_really_cool_show.mp4
```

And it then creates a text file and mp3 file for each sentence in the subtitles, putting them in a new directory named after the subtitle file.
