# synthesiavid2midi

This utility converts a Synthesia screen capture video into a midi file by working out the key presses.

## Usage

You'll need opencv and its Python bindings installed.

```python main.py [overrides/options in key:value format] output input```

Normally, no options are required but if the transcription is inaccurate or it errors out, you may need to fine tune by using some of the following options.

```showprogress```: Use this to get a visual representation when finetuning. The aim is to have the circles as close to the middle of the key as possible and have the circles represent the correct state of the key (white/black when unpressed, green when pressed).

```nkeys```: Number of white keys shown on the keyboard.

```middlec```: 0-based index of middle C key.

```whitewidth```: Width in pixels of a white key.

```white/blackthreshold```: The threshold for a white/black key to be considered pressed (0-255). For black, you would start at a low value (~20) and increase until all unpressed black keys have white circles. For white, start at a high value (~240) and decrease until all unpressed white keys show black circles.

## Tips

 * Get the highest quality video possible. A 720p video is far more likely to be transcribled accurately than a 480p video.
 * The video should have minimal to no editing and as close to a vanilla screen cap as possible.