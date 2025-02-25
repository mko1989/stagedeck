# Introduction

StageDeck is a versatile stage display application designed for live events and broadcasts. It supports NDI input and web streaming, making it an ideal solution for dynamic stage displays and real-time updates.

## Features

Transparent or opaque window display: Choose between a transparent or solid background to best suit your stage environment.
NDI input support: Integrate live video feeds directly into your display.
Web streaming capability: Stream your display to any device on your network for remote viewing.
Timer functionality: Use countdown or countup timers for time management.
Timer features warning change color, end time change color and blinking. Playing warning time sound, playing end time sound.
Customizable fields and text display: Create and customize fields that can be updated in real-time.
OSC control support: Use OSC messages to dynamically change display content.


## Installation


Option 1: Install from Executable (Recommended)
Download the latest StageDeck Installer.zip
Extract the zip file
Run StageDeck.exe

Option 2: Install from Source
Clone this repository
Install Python 3.9 or later
Install dependencies:
bash
pip install -r requirements.txt
Run the application:
bash
python main.py

For NDI usage NDI runtime is needed. You can grab it quickly from here:
https://github.com/DistroAV/DistroAV/discussions/831

## Usage


Launch StageDeck

Configure display settings in the Settings tab:

Choose monitor
Set background color or transparency
Enable NDI input as background if needed
Configure web streaming
Add and customize fields in the Fields tab that can be dynamically set and changed via OSC.

OSC messages should look like /field/(field-id)/content/(value)

Example: /field/time/content/12:24:56
For best results, create a trigger in Companion on variable change and choose send OSC as an action.
Use the Timer tab for countdown/countup functionality

## Web Streaming

When web streaming is enabled, access the display from any device on your network:

Enable web streaming in the Settings tab
Access http://<computer-ip>:8181 from any web browser
The display will update in real-time with minimal latency

## ScreenShots

![Main window](https://github.com/mko1989/stagedeck/blob/main/screenshots/s1.png)
![Timer](https://github.com/mko1989/stagedeck/blob/main/screenshots/s3.png)
![Setting up a field](https://github.com/mko1989/stagedeck/blob/main/screenshots/s4.png)
![Companion config](https://github.com/mko1989/stagedeck/blob/main/screenshots/s5.png)
![Trigger setup](https://github.com/mko1989/stagedeck/blob/main/screenshots/s6.png)
![Companion variable in a field](https://github.com/mko1989/stagedeck/blob/main/screenshots/s7.png)
![Transparent background](https://github.com/mko1989/stagedeck/blob/main/screenshots/s8.png)
![NDI background](https://github.com/mko1989/stagedeck/blob/main/screenshots/s9.png)

## Development

Main application: main.py

Web server component: web_server.py

PyInstaller spec: companion_viewer.spec
