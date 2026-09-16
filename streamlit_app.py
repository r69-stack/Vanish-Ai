import threading
import av
import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase

from app import BackgroundModel, SegmentationEngine, HandTracker, PortalBox, HUD


st.set_page_config(
    page_title="GhostVision AI",
    page_icon="👻",
    layout="wide",
)

st.title("👻 GhostVision AI")
st.caption("Real-time AI invisibility effect using OpenCV + MediaPipe")


class GhostVisionProcessor(VideoProcessorBase):
    def __init__(self):
        self.lock = threading.Lock()

        self.background = None
        self.seg_engine = SegmentationEngine()
        self.hand_tracker = HandTracker()
        self.portal = PortalBox()

        self.h = None
        self.w = None
        self.bg_model = None
        self.hud = None

        self.invisibility_requested = False
        self.recalibrate_requested = False

    def set_invisibility(self, value):
        with self.lock:
            self.invisibility_requested = value

    def toggle_invisibility(self):
        with self.lock:
            self.invisibility_requested = not self.invisibility_requested

    def recalibrate(self):
        with self.lock:
            self.recalibrate_requested = True

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")

        h, w = img.shape[:2]

        if self.bg_model is None or self.h != h or self.w != w:
            self.h, self.w = h, w
            self.bg_model = BackgroundModel(h, w, n_frames=90)
            self.hud = HUD(h, w, "WEB")

        with self.lock:
            if self.recalibrate_requested:
                self.bg_model = BackgroundModel(h, w, n_frames=90)
                self.recalibrate_requested = False

            requested = self.invisibility_requested

        # Background calibration
        frame_f32 = img.astype("float32")
        if not self.bg_model.ready:
            self.bg_model.update(frame_f32)
            self.background = self.bg_model.get()

            cv2_text = "CALIBRATING BACKGROUND..."
            import cv2
            cv2.putText(
                img, cv2_text, (30, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                (0, 230, 255), 2, cv2.LINE_AA
            )

            return av.VideoFrame.from_ndarray(img, format="bgr24")

        self.background = self.bg_model.get()

        # AI processing
        mask = self.seg_engine.get_mask(img)
        results = self.hand_tracker.process(img)
        info = self.hand_tracker.get_info(results, w, h)

        # Portal position / hand visualization
        self.portal.update(info)

        # Streamlit controls override the portal state.
        self.portal.invisible = requested
        self.portal.update_alpha()

        output = self.portal.render(
            img,
            mask,
            self.background,
            info["all_points"],
        )

        self.hud.tick()
        output = self.hud.draw(output, self.portal, info)

        return av.VideoFrame.from_ndarray(output, format="bgr24")


# Sidebar controls
with st.sidebar:
    st.header("Controls")

    if "ghost_state" not in st.session_state:
        st.session_state.ghost_state = False

    if st.button("👻 Toggle Invisibility", use_container_width=True):
        st.session_state.ghost_state = not st.session_state.ghost_state

    if st.button("👤 Visible", use_container_width=True):
        st.session_state.ghost_state = False

    if st.button("🔄 Recalibrate Background", use_container_width=True):
        st.session_state.recalibrate = True
    else:
        st.session_state.recalibrate = False

    st.markdown("---")
    st.info(
        "Allow camera access when your browser asks. "
        "Keep the camera still during background calibration."
    )

ctx = webrtc_streamer(
    key="ghostvision",
    video_processor_factory=GhostVisionProcessor,
    media_stream_constraints={
        "video": True,
        "audio": False,
    },
    async_processing=True,
    rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    },
)

# Send UI commands to the active video processor.
if ctx.video_processor:
    ctx.video_processor.set_invisibility(st.session_state.ghost_state)

    if st.session_state.get("recalibrate", False):
        ctx.video_processor.recalibrate()

st.markdown("---")
st.caption("GhostVision AI • OpenCV + MediaPipe + Streamlit WebRTC")
