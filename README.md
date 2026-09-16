# 🫥 Vanish AI

> Real-time AI-powered invisibility using human segmentation, background reconstruction, and computer vision.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-red?logo=opencv)
![MediaPipe](https://img.shields.io/badge/MediaPipe-ML-orange) 
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-ff4b4b?logo=streamlit)
![WebRTC](https://img.shields.io/badge/WebRTC-Live%20Video-green)

---

## ✨ Overview

**Vanish AI** is a real-time computer vision application that creates an interactive invisibility effect using a live webcam feed.

The system detects the person in the frame, separates the foreground from the background, reconstructs the background, and combines the results to create a real-time disappearing effect.

The project combines computer vision, AI-based segmentation, background modeling, hand tracking, and real-time video processing in an interactive Streamlit dashboard.

---

## 🚀 Features

- 🫥 **Real-Time Invisibility Effect**
- 🎥 **Live Webcam Processing**
- 🧍 **AI Human Segmentation**
- ✋ **Hand Landmark Tracking**
- 🌄 **Background Modeling & Reconstruction**
- 📊 **Real-Time FPS & System HUD**
- 🖥️ **Interactive Streamlit Dashboard**
- ⚡ **WebRTC-Based Video Streaming**
- 🎨 **Real-Time Visual Effects**

---

## 🧠 How It Works

Webcam
   │
   ▼
WebRTC Video Stream
   │
   ├──────────────┐
   ▼              ▼
Background     Human
Modeling       Segmentation
   │              │
   └──────┬───────┘
          │
          ▼
     Hand Tracking
          │
          ▼
   Ghost / Vanish Engine
          │
          ▼
      HUD Renderer
          │
          ▼
    Final Video Output
