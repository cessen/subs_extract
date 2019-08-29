# Subs Extract

A simple Python script that uses ffmpeg to extract subtitles and audio from a video.  The purpose is to facilitate creating flash cards from foreign-language TV shows and movies.

It takes as input a video file and a corresponding .ssa, .ass, .vtt, or .srt subtitle file, like this:

```
subs_extract.py a_really_cool_show.mp4 a_really_cool_show.srt
```

And it then creates a text file, an mp3 file, and an image thumbnail for each sentence in the subtitles, putting them in a new directory named after the video file.  It also creates a deck file that can be imported into Anki, with the following fields per note:

1. The line's subtitle text.
2. The filename of the line's audio file, wrapped in an Anki audio tag.
3. The filename of the line's image thumbnail.
4. The name of the video file the line came from, without the file extension (this basically identifies the movie/episode, assuming your video files are named appropriately).
5. A timestamp, indicating where in the video file the line is.


## Using a second subtitle file

You can also pass a second subtitle file like so:

```
subs_extract.py a_really_cool_show.mp4 a_really_cool_show.jp.srt a_really_cool_show.en.srt
```

If you do this, Subs Extract will attempt to find a matching subtitle in the second file for every subtitle in the first, and include that as a translation.  It does this based on the start times of the subtitles.  It isn't perfect, and there will usually be a handful of weird matches for each video, but it generally does an okay job.  Also, it sometimes simply won't include a match at all if the timing for a given subtitle is just too different.

The generated deck file will also include the second subtitle like so:

1. The line's subtitle text.
2. The filename of line's audio file, wrapped in an Anki audio tag.
3. **Matching subtitle from second subtitle file.**
4. The filename of the line's image thumbnail.
5. The name of the video file the line came from, without the file extension (this basically identifies the movie/episode, assuming your video files are named appropriately).
6. A timestamp, indicating where in the video file the line is.
