import subprocess
import sys
import importlib.util


# ============================================================
# AUTO INSTALL DEPENDENCIES
# ============================================================

REQUIRED = {
    "cv2": "opencv-python",
    "numpy": "numpy",
    "mediapipe": "mediapipe"
}


def _auto_install():

    missing = [
        pkg
        for mod, pkg in REQUIRED.items()
        if importlib.util.find_spec(mod) is None
    ]

    if missing:

        print(
            f"\n[AUTO-INSTALL] Installing: "
            f"{', '.join(missing)}\n"
        )

        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--quiet"
            ] + missing
        )

        print("[AUTO-INSTALL] Done.\n")


_auto_install()


# ============================================================
# IMPORTS
# ============================================================

import cv2
import numpy as np
import time


from app import (
    BackgroundModel,
    SegmentationEngine,
    HandTracker,
    PortalBox,
    HUD
)


# ============================================================
# CONFIG
# ============================================================

BANNER = """
Ghost / Invisibility Mode

  1. Stand still 3s  ->  background captured
  2. Show BOTH hands spread apart  ->  portal appears
  3. Press I  ->  YOU VANISH
  4. Press I again  ->  YOU REAPPEAR

  I = Toggle invisibility
  V = Force visible
  R = Recalibrate
  S = Screenshot
  Q = Quit
"""


WINDOW = "Ghost / Invisibility Mode"


# ============================================================
# DEVICE DETECTION
# ============================================================

def _detect_device():

    try:

        import torch

        if torch.cuda.is_available():

            return (
                "GPU/"
                +
                torch.cuda
                .get_device_name(0)
                .split()[0]
            )

    except ImportError:
        pass

    return "CPU"


# ============================================================
# BACKGROUND CALIBRATION
# ============================================================

def run_calibration(
    cap,
    bg_model,
    w,
    h,
    seconds=3
):

    print(
        f"[CAL] Stand still {seconds}s ..."
    )

    start = time.time()

    while time.time() - start < seconds:

        ret, frame = cap.read()

        if not ret:
            continue

        bg_model.update(
            frame.astype(np.float32)
        )

        rem = int(
            seconds
            -
            (
                time.time()
                -
                start
            )
        ) + 1

        disp = (
            frame * 0.5
        ).astype(np.uint8)

        msg = (
            "STAND STILL  —  "
            "CALIBRATING BACKGROUND"
        )

        tw = cv2.getTextSize(
            msg,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            2
        )[0][0]

        cv2.putText(
            disp,
            msg,
            ((w - tw) // 2, h // 2 - 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 230, 255),
            2,
            cv2.LINE_AA
        )

        tw2 = cv2.getTextSize(
            str(rem),
            cv2.FONT_HERSHEY_SIMPLEX,
            4.0,
            5
        )[0][0]

        cv2.putText(
            disp,
            str(rem),
            ((w - tw2) // 2, h // 2 + 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            4.0,
            (0, 255, 120),
            5,
            cv2.LINE_AA
        )

        cv2.imshow(
            WINDOW,
            disp
        )

        if cv2.waitKey(1) & 0xFF in (
            ord("q"),
            27
        ):
            return False

    print("[CAL] Done\n")

    return True


# ============================================================
# MAIN
# ============================================================

def main():

    print(BANNER)

    dev_str = _detect_device()

    print(
        f"[INFO] Device: {dev_str}"
    )

    # --------------------------------------------
    # Camera index
    # --------------------------------------------

    cam_idx = (
        int(sys.argv[1])
        if len(sys.argv) > 1
        else 0
    )

    cap = None

    # --------------------------------------------
    # Camera backends
    # --------------------------------------------

    if sys.platform == "win32":

        backends = [
            (
                cv2.CAP_DSHOW,
                "DirectShow"
            ),
            (
                cv2.CAP_MSMF,
                "MSMF"
            ),
            (
                cv2.CAP_ANY,
                "Auto"
            )
        ]

    else:

        backends = [
            (
                cv2.CAP_ANY,
                "Auto"
            )
        ]

    probe = None

    # --------------------------------------------
    # Open webcam
    # --------------------------------------------

    for backend, name in backends:

        print(
            f"[CAM] Trying {name} ..."
        )

        _c = cv2.VideoCapture(
            cam_idx + backend
        )

        if _c.isOpened():

            _c.set(
                cv2.CAP_PROP_FRAME_WIDTH,
                1280
            )

            _c.set(
                cv2.CAP_PROP_FRAME_HEIGHT,
                720
            )

            _c.set(
                cv2.CAP_PROP_FPS,
                30
            )

            ret, probe = _c.read()

            if ret and probe is not None:

                cap = _c

                print(
                    f"[CAM] OK with {name}"
                )

                break

            _c.release()

    # --------------------------------------------
    # Camera error
    # --------------------------------------------

    if cap is None:

        print(
            "[ERROR] Could not open webcam."
        )

        print(
            "Close Teams/Zoom/other camera apps first."
        )

        sys.exit(1)

    # --------------------------------------------
    # Resolution
    # --------------------------------------------

    h, w = probe.shape[:2]

    print(
        f"[INFO] Resolution: {w}x{h}"
    )

    print(
        "[INIT] Loading models ..."
    )

    # --------------------------------------------
    # Initialize engines
    # --------------------------------------------

    seg = SegmentationEngine()

    tracker = HandTracker()

    bg_model = BackgroundModel(
        h,
        w,
        n_frames=90
    )

    portal = PortalBox()

    hud = HUD(
        h,
        w,
        dev_str
    )

    print(
        "[INIT] Ready!\n"
    )

    # --------------------------------------------
    # Window
    # --------------------------------------------

    cv2.namedWindow(
        WINDOW,
        cv2.WINDOW_NORMAL
    )

    cv2.resizeWindow(
        WINDOW,
        min(w, 1280),
        min(h, 720)
    )

    # --------------------------------------------
    # Initial calibration
    # --------------------------------------------

    if not run_calibration(
        cap,
        bg_model,
        w,
        h,
        seconds=3
    ):

        cap.release()
        cv2.destroyAllWindows()

        return

    # --------------------------------------------
    # Build background
    # --------------------------------------------

    if bg_model.buf:

        bg_model.bg = (
            np.mean(
                bg_model.buf,
                axis=0
            ).astype(np.float32)
        )

        bg_model.ready = True

    # --------------------------------------------
    # Screenshot counter
    # --------------------------------------------

    sc_idx = 0

    # ========================================================
    # MAIN LOOP
    # ========================================================

    while True:

        ret, frame = cap.read()

        if not ret:

            time.sleep(0.02)

            continue

        # --------------------------------------------
        # FPS
        # --------------------------------------------

        hud.tick()

        # --------------------------------------------
        # AI segmentation
        # --------------------------------------------

        seg_mask = seg.get_mask(
            frame
        )

        # --------------------------------------------
        # Hand tracking
        # --------------------------------------------

        results = tracker.process(
            frame
        )

        info = tracker.get_info(
            results,
            w,
            h
        )

        # --------------------------------------------
        # Portal detection
        # --------------------------------------------

        portal.update(
            info
        )

        # --------------------------------------------
        # Smooth invisibility animation
        # --------------------------------------------

        portal.update_alpha()

        # --------------------------------------------
        # Render
        # --------------------------------------------

        out = portal.render(
            frame,
            seg_mask,
            bg_model.get(),
            info["all_points"]
        )

        out = hud.draw(
            out,
            portal,
            info
        )

        # --------------------------------------------
        # Display
        # --------------------------------------------

        cv2.imshow(
            WINDOW,
            out
        )

        key = cv2.waitKey(1) & 0xFF

        # ====================================================
        # KEYBOARD CONTROLS
        # ====================================================

        # Q / ESC
        if key in (
            ord("q"),
            27
        ):

            break

        # ----------------------------------------------------
        # I = TOGGLE INVISIBILITY
        # ----------------------------------------------------

        elif key == ord("i"):

            portal.toggle_invisibility()

            state = (
                "ON"
                if portal.invisible
                else "OFF"
            )

            print(
                f"[KEY] Invisibility: {state}"
            )

        # ----------------------------------------------------
        # V = FORCE VISIBLE
        # ----------------------------------------------------

        elif key == ord("v"):

            portal.set_visible()

            print(
                "[KEY] Visible mode"
            )

        # ----------------------------------------------------
        # S = SCREENSHOT
        # ----------------------------------------------------

        elif key == ord("s"):

            fn = (
                f"screenshot_"
                f"{sc_idx:04d}.png"
            )

            cv2.imwrite(
                fn,
                out
            )

            print(
                f"[SCREENSHOT] {fn}"
            )

            sc_idx += 1

        # ----------------------------------------------------
        # R = RECALIBRATE
        # ----------------------------------------------------

        elif key == ord("r"):

            print(
                "[KEY] Recalibrating..."
            )

            bg_model.__init__(
                h,
                w
            )

            portal.set_visible()

            portal._alpha = 0.0

            if not run_calibration(
                cap,
                bg_model,
                w,
                h,
                3
            ):

                break

            if bg_model.buf:

                bg_model.bg = (
                    np.mean(
                        bg_model.buf,
                        axis=0
                    ).astype(np.float32)
                )

                bg_model.ready = True

            print(
                "[CAL] Recalibration complete."
            )

    # ========================================================
    # CLEANUP
    # ========================================================

    cap.release()

    cv2.destroyAllWindows()

    print(
        "\n[DONE]"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
