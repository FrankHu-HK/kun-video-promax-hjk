# -*- coding: utf-8 -*-

"""

face swap(faceswap_pro)-- / occlusion.

 faceswap.py (v2.7.0 · face swapquality A+B + /format + pose +  + input):

  -- face swapquality(A-F ,"")--

  -- face swapquality(A-F ,"")--

  ✅  Layer A: (det_size 1024 + det_thresh 0.3,/)

  ✅  Layer B: (// + frameocclusion,"")

  ⏳  Layer C: track(frame bbox track + frameframe)

  ⏳  Layer D: (qualityresult)

  ⏳  Layer E: (target/goal)

  ⏳  Layer F: (outputframequality + )

  -- (, A-F ):/5//occlusion --

  v2.2.0 /format:/formatexception auto_format.py ,user

mode:

  --preview-out preview.png    processframe,output || (video)

  mode                      framevideo out.mp4 + bbox.json

:(--resume,interruptdone),(),frameexception,

  parameter(--preset speed/quality/sideface/occlusion),occlusion,

  error(E100+),Debug log(--debug),frame(--frame-timeout).

 SKILL.md stage 1().

dependency: insightface, onnxruntime, opencv-python, numpy

"""

import os

import sys

import json

import time

import argparse

import tempfile

import shutil

import subprocess

import logging

import cv2

import numpy as np



# ============ error( SKILL.md exceptionprocess) ============

ERROR_CODES = {

    "E100": "readfailed(path/file)",

    "E101": "",

    "E102": "modelfile(inswapper_128.onnx / buffalo_l)",

    "E103": "videofileopen(path/encode)",

    "E104": "frameprocessexception(qualitymodelexception)",

    "E105": "failed(qualityexception,suggestion --resume )",

}





def setup_logging(debug):

    level = logging.DEBUG if debug else logging.INFO

    logging.basicConfig(

        level=level,

        format="[%(asctime)s][%(levelname)s] %(message)s",

        datefmt="%H:%M:%S",

    )





def build_source_face(app, photo):

    # path

    tmp_photo = None

    try:

        photo.encode("ascii")

    except UnicodeEncodeError:

        tmp_photo = os.path.join(tempfile.gettempdir(), "user_photo_tmp.jpg")

        shutil.copy(photo, tmp_photo)

        photo = tmp_photo

    img = cv2.imread(photo)

    if img is None:

        raise SystemExit("E100: read: " + photo)

    faces = app.get(img)

    if not faces:

        raise SystemExit("E101: ")

    src = sorted(faces, key=lambda f: f.bbox[2] - f.bbox[0])[-1]

    if tmp_photo and os.path.exists(tmp_photo):

        os.remove(tmp_photo)

    return src





def pick_target(faces, side, w):

    if not faces:

        return None

    if side == "largest":

        return max(faces, key=lambda f: f.bbox[2] - f.bbox[0])

    if side == "right":

        # (1),face swap;

        if len(faces) == 1:

            return faces[0]

        return max(faces, key=lambda f: (f.bbox[0] + f.bbox[2]) / 2)

    # left:;

    if side == "left" and len(faces) == 1:

        return faces[0]

    lefts = [f for f in faces if (f.bbox[0] + f.bbox[2]) / 2 < w * 0.5]

    return max(lefts, key=lambda f: f.bbox[2] - f.bbox[0]) if lefts else None





def yaw_proxy(face):

    """ 5 keypoint:  / .."""

    kps = face.kps

    le, re, nose = kps[0], kps[1], kps[2]

    eye_mid_x = (le[0] + re[0]) / 2.0

    eye_dist = abs(re[0] - le[0]) + 1e-3

    return abs(nose[0] - eye_mid_x) / eye_dist





def enhanced_paste(swapper, frame, target, source_face, mask_scale, feather):

    """,(//)."""

    bgr_fake, M = swapper.get(frame, target, source_face, paste_back=False)

    S = bgr_fake.shape[0]  # 128

    h, w = frame.shape[:2]

    # align(128)

    mask = np.zeros((S, S), np.float32)

    cx, cy = S * 0.5, S * 0.52

    ax, ay = S * 0.46 * mask_scale, S * 0.60 * mask_scale

    cv2.ellipse(mask, (int(cx), int(cy)), (int(ax), int(ay)), 0, 0, 360, 1.0, -1)

    IM = cv2.invertAffineTransform(M)

    fake_w = cv2.warpAffine(bgr_fake, IM, (w, h), borderValue=0.0)

    mask_w = cv2.warpAffine(mask, IM, (w, h), borderValue=0.0)

    # ()

    face_px = max(target.bbox[2] - target.bbox[0], 20)

    sigma = max(face_px * feather, 3)

    mask_w = cv2.GaussianBlur(mask_w, (0, 0), sigmaX=sigma, sigmaY=sigma)

    mask_w = np.clip(mask_w, 0, 1)[:, :, None]

    out = (mask_w * fake_w.astype(np.float32) + (1 - mask_w) * frame.astype(np.float32)).astype(np.uint8)

    return out





def make_app(insight_root, det_size, det_thresh):

    import insightface

    from insightface.app import FaceAnalysis

    app = FaceAnalysis(name="buffalo_l", root=os.path.abspath(insight_root),

                       providers=["CPUExecutionProvider"])

    app.prepare(ctx_id=0, det_size=(det_size, det_size), det_thresh=det_thresh)

    for _k in ["landmark_3d_68", "landmark_2d_106", "genderage"]:

        app.models.pop(_k, None)

    return app





def _load_progress(out_path):

    """readprogress(successprocessframe)."""

    prog = out_path + ".progress"

    if os.path.exists(prog):

        try:

            with open(prog) as f:

                return int(f.read().strip() or 0)

        except Exception:

            return 0

    return 0





def _save_progress(out_path, n):

    prog = out_path + ".progress"

    try:

        with open(prog, "w") as f:

            f.write(str(n))

    except Exception as e:

        logging.warning("progresswritefailed(workflow): %s", e)





# ============ v2.2.0 /formatprocess ============

def safe_open_video(video_path, workdir=None):

    """videoformat, auto_format.py .

    /formatprocess,user.



     (VideoCapture, openpath). mp4(H.264),

    open; workdir/<name>_std.mp4 open.

    """

    if not os.path.exists(video_path):

        raise SystemExit(f"E103: videofiledoes not exist: {video_path}")

    # 1) open

    cap = cv2.VideoCapture(video_path)

    if cap.isOpened():

        ok, frame = cap.read()

        if ok and frame is not None:

            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

            logging.info("  ✅ videoformat,open: %s", video_path)

            return cap, video_path

        cap.release()

    # 2) 

    logging.warning("  ⚠️ videoopen(%s), auto_format.py ", video_path)

    auto_format_script = os.path.join(os.path.dirname(__file__), "auto_format.py")

    if not os.path.exists(auto_format_script):

        raise SystemExit("E103: videoopen auto_format.py does not exist, ffmpeg ")

    out_dir = workdir or os.path.dirname(video_path) or "."

    base = os.path.splitext(os.path.basename(video_path))[0]

    std_path = os.path.join(out_dir, f"{base}_std.mp4")

    r = subprocess.run(

        ["python", auto_format_script, "--input", video_path, "--output", std_path],

        capture_output=True, timeout=1800,

    )

    if r.returncode != 0 or not os.path.exists(std_path):

        logging.error("  auto_format.py failed:\n%s", (r.stderr or b"").decode("utf-8", errors="ignore")[:500])

        raise SystemExit(f"E103: videoopenfailed: {video_path}")

    logging.info("  ✅ success: %s", std_path)

    cap = cv2.VideoCapture(std_path)

    if not cap.isOpened():

        raise SystemExit(f"E103: open: {std_path}")

    return cap, std_path





def safe_open_cap_with_retry(video_path, workdir=None, max_retry=3):

    """retrysafeopen(process/formatexception)."""

    last_err = None

    for attempt in range(max_retry):

        try:

            cap, used_path = safe_open_video(video_path, workdir)

            if cap.isOpened():

                return cap, used_path

        except SystemExit as e:

            last_err = str(e)

        logging.warning("  openvideo %d failed: %s", attempt + 1, last_err)

        if attempt < max_retry - 1:

            import time as _t

            wait = 5 * (2 ** attempt)

            logging.info("   %ds retry...", wait)

            _t.sleep(wait)

    raise SystemExit(f"E103: videoopen(retry {max_retry} ): {video_path}")





def _load_resume_state(path):

    """readstatus(done +  bbox/)."""

    if os.path.exists(path):

        try:

            with open(path, "r", encoding="utf-8") as f:

                d = json.load(f)

            if not isinstance(d, dict):

                return {}

            return d

        except Exception:

            # interruptstatus:,"done"

            logging.warning("statusfile,(generate): %s", path)

            return {}

    return {}





def _save_resume_state(path, state):

    try:

        # :file os.replace,crashstatusfileprogress

        tmp = path + ".tmp"

        with open(tmp, "w", encoding="utf-8") as f:

            json.dump(state, f, ensure_ascii=False)

        os.replace(tmp, path)

    except Exception as e:

        logging.warning("statuswritefailed(workflow): %s", e)





def concat_videos(seg_files, out_path, fps, w, h):

    """video(v2.6.0 ):

    ①  ffmpeg  copy(retry 2 )② failed ffmpeg encode(libx264/aac,exception)

    ③ failed cv2 frame.."""

    seg_files = [s for s in seg_files if os.path.exists(s)]

    if not seg_files:

        return False

    ff = "ffmpeg"

    try:

        import imageio_ffmpeg

        ff = imageio_ffmpeg.get_ffmpeg_exe()

    except Exception:

        pass



    def _write_list():

        list_path = out_path + ".concat.txt"

        with open(list_path, "w", encoding="utf-8") as f:

            for s in seg_files:

                f.write("file '%s'\n" % os.path.abspath(s).replace("\\", "/"))

        return list_path



    # ①  copy,retry 2 (write)

    for attempt in range(2):

        list_path = _write_list()

        try:

            r = subprocess.run([ff, "-y", "-f", "concat", "-safe", "0", "-i", list_path,

                                "-c", "copy", out_path], capture_output=True, timeout=900)

            if r.returncode == 0 and os.path.exists(out_path) and os.path.getsize(out_path) > 0:

                return True

        except Exception as e:

            logging.warning("  ffmpeg  %d failed: %s", attempt + 1, e)

        finally:

            try:

                os.remove(list_path)

            except Exception:

                pass

    # ② encode(,exception/)

    list_path = _write_list()

    try:

        r = subprocess.run([ff, "-y", "-f", "concat", "-safe", "0", "-i", list_path,

                            "-c:v", "libx264", "-c:a", "aac", "-preset", "ultrafast",

                            out_path], capture_output=True, timeout=1200)

        if r.returncode == 0 and os.path.exists(out_path) and os.path.getsize(out_path) > 0:

            logging.info("  ✅ ffmpeg encodesuccess(exception)")

            return True

    except Exception as e:

        logging.warning("  ffmpeg encodefailed: %s", e)

    finally:

        try:

            os.remove(list_path)

        except Exception:

            pass

    # ③  cv2 frame

    vw = cv2.VideoWriter(out_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))

    for s in seg_files:

        c = cv2.VideoCapture(s)

        while True:

            ok, fr = c.read()

            if not ok:

                break

            vw.write(fr)

        c.release()

    vw.release()

    return os.path.exists(out_path)





def render_segment(cap, si, seg_frames, fps, w, h, app, swapper, args, source_face, max_yaw_in, skipped_in):

    """render( si) seg_xxx.mp4(+_trim).loop.

     dict,."""

    seg_dir = args.out + ".segs"

    seg_base = os.path.join(seg_dir, "seg_%03d" % si)

    seg_file = seg_base + ".mp4"

    seg_trim_file = seg_base + "_trim.mp4"

    cap.set(cv2.CAP_PROP_POS_FRAMES, si * seg_frames)

    vw_seg = cv2.VideoWriter(seg_file, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))

    vw_seg_trim = None

    if args.auto_trim_extreme:

        vw_seg_trim = cv2.VideoWriter(seg_trim_file, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))

    seg_bboxes = []

    seg_extreme = 0

    seg_face = 0

    seg_trim_kept = 0

    seg_max_yaw = max_yaw_in

    seg_skipped = skipped_in

    f_in_seg = 0

    while f_in_seg < seg_frames:

        ok, frame = cap.read()

        if not ok:

            break

        t0 = time.time()

        is_extreme = False

        try:

            faces = app.get(frame)

            t = pick_target(faces, args.target_side, w)

            if t is not None:

                y = yaw_proxy(t)

                seg_face += 1

                if y > seg_max_yaw:

                    seg_max_yaw = y

                if y > args.yaw_warn:

                    seg_extreme += 1

                    is_extreme = True

                # occlusion:,edge,/edge

                ms = min(args.mask_scale * (1.0 + 0.15 * y), 1.8)

                fe = min(args.feather + 0.05 * y, 0.2)

                frame = enhanced_paste(swapper, frame, t, source_face, ms, fe)

                seg_bboxes.append([int(v) for v in t.bbox])

            else:

                seg_bboxes.append(None)

            vw_seg.write(frame)

            if vw_seg_trim is not None and not is_extreme:

                vw_seg_trim.write(frame)

                seg_trim_kept += 1

        except Exception as e:

            logging.warning("   %d frame %d processexception,frameskip: %s", si, f_in_seg, e)

            vw_seg.write(frame)

            if vw_seg_trim is not None:

                vw_seg_trim.write(frame)

            seg_bboxes.append(None)

            seg_skipped += 1

        dt = time.time() - t0

        if dt > args.frame_timeout:

            logging.warning("   %d frame %d  %.1fs ", si, f_in_seg, dt)

        f_in_seg += 1

    vw_seg.release()

    if vw_seg_trim is not None:

        vw_seg_trim.release()

    return dict(seg_bboxes=seg_bboxes, seg_extreme=seg_extreme, seg_face=seg_face,

                seg_trim_kept=seg_trim_kept, seg_max_yaw=seg_max_yaw, seg_skipped=seg_skipped)





def _seg_is_valid(seg_file, w, h, fps):

    """filedecode 1 frame."""

    if not os.path.exists(seg_file) or os.path.getsize(seg_file) == 0:

        return False

    c = cv2.VideoCapture(seg_file)

    if not c.isOpened():

        c.release()

        return False

    ok, _ = c.read()

    c.release()

    return ok





def heal_segments(seg_dir, n_segs, src_video, seg_frames, fps, w, h, app, swapper, args, source_face):

    """(v2.7.0 runstable):/,openvideo."""

    healed = 0

    for si in range(n_segs):

        seg_file = os.path.join(seg_dir, "seg_%03d.mp4" % si)

        if _seg_is_valid(seg_file, w, h, fps):

            continue

        logging.warning("  ⚠️  %d /,(E105)", si + 1)

        try:

            cap2 = safe_open_cap_with_retry(

                src_video, workdir=os.path.dirname(os.path.abspath(args.out)) or tempfile.gettempdir())

        except SystemExit as e:

            logging.error("  openvideofailed: %s", e)

            continue

        render_segment(cap2, si, seg_frames, fps, w, h, app, swapper, args, source_face, 0.0, 0)

        cap2.release()

        if _seg_is_valid(seg_file, w, h, fps):

            healed += 1

            logging.info("  ✅  %d success", si + 1)

        else:

            logging.error("  E105:  %d failed, --resume checkvideo", si + 1)

    return healed





def wizard():

    """parameter(v2.6.0 · ):,,document."""

    print("=" * 56)

    print("  kun-video face swapparameter(document,hint/tip)")

    print("=" * 56)



    def ask(q, opts):

        print("\n" + q)

        for i, o in enumerate(opts, 1):

            print("  %d) %s" % (i, o))

        while True:

            try:

                c = int(input("  (input): ").strip())

                if 1 <= c <= len(opts):

                    return c - 1

            except Exception:

                pass

            print("  input 1-%d " % len(opts))



    video = input("\n  videofilepath( video.mp4): ").strip()

    photo = input("  target/goalpath( .jpg): ").strip()

    out = input("  outputfile( pro.mp4): ").strip() or "pro.mp4"

    a = ask("  video?", ["/", "/", "occlusion", "/"])

    preset_map = {0: "quality", 1: "sideface", 2: "occlusion", 3: "auto"}

    preset = preset_map[a]

    cmd = "python scripts/faceswap_pro.py --video %s --photo %s --out %s --preset %s" % (

        video, photo, out, preset)

    if a == 1:

        cmd += " --auto-trim-extreme"

    print("\n✅ generate(copy):")

    print("  " + cmd)

    print("\n  ?copy; faceswap_pro  faceswap.")





def main():

    ap = argparse.ArgumentParser()

    ap.add_argument("--video", required=True)

    ap.add_argument("--photo", required=True)

    ap.add_argument("--out", default="swapped_raw.mp4")

    ap.add_argument("--bbox", default="face_bboxes.json")

    ap.add_argument("--models-dir", default="models")

    ap.add_argument("--insight-root", default=".insightface")

    ap.add_argument("--det-size", default=1024, type=int)

    ap.add_argument("--det-thresh", default=0.3, type=float)

    ap.add_argument("--target-side", default="right", choices=["right", "left", "largest"])

    ap.add_argument("--mask-scale", default=1.15, type=float, help="(,/)")

    ap.add_argument("--feather", default=0.06, type=float, help="(aspect ratio)")

    # mode

    ap.add_argument("--preview-out", default=None, help=",video")

    ap.add_argument("--preview-count", default=6, type=int)

    ap.add_argument("--preview-stride", default=7, type=int, help="frame")

    # parameter

    ap.add_argument("--resume", action="store_true", help=":generate N frame,processframe")

    ap.add_argument("--debug", action="store_true", help=" Debug log")

    ap.add_argument("--frame-timeout", default=30.0, type=float, help="frameprocess(),log")

    ap.add_argument("--max-skip-ratio", default=0.3, type=float, help="skipframe E104(qualityexception)")

    # pose(,hint/tip)

    ap.add_argument("--yaw-warn", default=0.7, type=float, help="( yaw>70° ),frame")

    ap.add_argument("--extreme-ratio-warn", default=0.15, type=float, help="frame,outputsuggestion")

    ap.add_argument("--auto-trim-extreme", action="store_true",

                    help=",generate''(frame),crop")

    ap.add_argument("--preset", default="auto",

                    choices=["auto", "speed", "quality", "sideface", "occlusion"],

                    help="parameter(): speed/quality/sideface/occlusionocclusion")

    ap.add_argument("--segment-secs", default=15, type=int,

                    help="(),,")

    ap.add_argument("--wizard", action="store_true",

                    help="parameter:,,document")

    args = ap.parse_args()



    # mode:loadmodel,exit()

    if args.wizard:

        wizard()

        sys.exit(0)



    setup_logging(args.debug)



    import insightface

    logging.info("[1/3] loadmodel det_size=%d det_thresh=%.2f ...", args.det_size, args.det_thresh)

    try:

        app = make_app(args.insight_root, args.det_size, args.det_thresh)

    except Exception as e:

        raise SystemExit("E102: modelloadfailed: " + str(e))

    try:

        swapper = insightface.model_zoo.get_model(

            os.path.join(args.models_dir, "inswapper_128.onnx"),

            download=False, download_zip=False, providers=["CPUExecutionProvider"])

    except Exception as e:

        raise SystemExit("E102:  inswapper_128.onnx: " + str(e))

    logging.info("[2/3] extracttarget/goalfeature...")

    source_face = build_source_face(app, args.photo)

    logging.info("  target/goal: %s", [int(v) for v in source_face.bbox])



    # v2.7.0 inputprocess(exceptionprocess):target/goal/occlusion,

    try:

        _py = yaw_proxy(source_face)

        if _py > args.yaw_warn:

            logging.warning("=" * 60)

            logging.warning("⚠️ target/goal/occlusion(yaw≈%.2f > %.2f):face swap.", _py, args.yaw_warn)

            logging.warning("   suggestion:①/() ② --preset sideface  --preset occlusion")

            logging.warning("   ?continueparameter;(>85°)model.")

            logging.warning("=" * 60)

    except Exception:

        pass



    cap, used_video = safe_open_cap_with_retry(

        args.video, workdir=os.path.dirname(os.path.abspath(args.out)) or tempfile.gettempdir())

    args.video = used_video  # recordopenvideopath()

    fps = cap.get(cv2.CAP_PROP_FPS)

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))

    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))



    # ============ mode() ============

    if args.preview_out:

        try:

            logging.info("[3/3] : frame(stride=%d)...", args.preview_stride)

            cand = []

            idx = 0

            while True:

                ok, frame = cap.read()

                if not ok:

                    break

                if idx % args.preview_stride == 0:

                    faces = app.get(frame)

                    t = pick_target(faces, args.target_side, w)

                    if t is not None:

                        cand.append((yaw_proxy(t), idx, frame.copy(), t))

                idx += 1

            cap.release()

            cand.sort(key=lambda x: -x[0])

            picks = cand[:args.preview_count]

            picks.sort(key=lambda x: x[1])

            rows = []

            for yaw, fidx, frame, t in picks:

                old = swapper.get(frame.copy(), t, source_face, paste_back=True)

                new = enhanced_paste(swapper, frame.copy(), t, source_face, args.mask_scale, args.feather)

                x1, y1, x2, y2 = [int(v) for v in t.bbox]

                pad = int((x2 - x1) * 0.6)

                cx1, cy1 = max(0, x1 - pad), max(0, y1 - pad)

                cx2, cy2 = min(w, x2 + pad), min(h, y2 + pad)

                def crop(im):

                    c = im[cy1:cy2, cx1:cx2]

                    return cv2.resize(c, (320, 320))

                trip = np.hstack([crop(frame), crop(old), crop(new)])

                cv2.putText(trip, "frame %d yaw=%.2f  [orig | old-swap | NEW-enhanced]" % (fidx, yaw),

                            (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)

                rows.append(trip)

            grid = np.vstack(rows)

            cv2.imwrite(args.preview_out, grid)

            logging.info("PREVIEW DONE -> %s frame: %s", args.preview_out, [p[1] for p in picks])

            return

        except Exception as e:

            logging.error("modefailed: %s", e)

            raise SystemExit("E103: processexception: " + str(e))



    # ============ mode( + frame + occlusion) ============

    logging.info("[3/3] frameface swap( +  + frame)...")

    logging.info("  : %dx%d, %.2ffps, %d frame", w, h, fps, total)



    # -- parameter(,document)--

    PRESETS = {

        "speed":     dict(det_size=512,  mask_scale=1.10, feather=0.05),

        "quality":   dict(det_size=1024, mask_scale=1.25, feather=0.09),

        "sideface":  dict(det_size=1024, mask_scale=1.40, feather=0.11, auto_trim_extreme=True),

        "occlusion": dict(det_size=1024, mask_scale=1.30, feather=0.13),

        "auto":      dict(),

    }

    _DEF = {"det_size": 1024, "mask_scale": 1.15, "feather": 0.06}

    if args.preset in PRESETS and args.preset != "auto":

        for _k, _v in PRESETS[args.preset].items():

            if _k == "auto_trim_extreme":

                if not args.auto_trim_extreme:

                    args.auto_trim_extreme = bool(_v)

                continue

            if getattr(args, _k) == _DEF.get(_k):

                setattr(args, _k, _v)

        logging.info("  apply --preset %s(det_size=%d mask_scale=%.2f feather=%.2f)",

                     args.preset, args.det_size, args.mask_scale, args.feather)



    # --  --

    seg_secs = max(1, int(args.segment_secs))

    seg_frames = max(1, int(round(fps * seg_secs))) if fps and fps > 0 else 1

    n_segs = (total + seg_frames - 1) // seg_frames if total > 0 else 1

    seg_dir = args.out + ".segs"

    os.makedirs(seg_dir, exist_ok=True)

    state_path = args.out + ".resume_state.json"

    state = _load_resume_state(state_path)

    done = set(state.get("done", []))

    if args.resume and done:

        _nxt = min(d for d in range(n_segs) if d not in done)

        logging.info("  :done %d/%d , %d continue", len(done), n_segs, _nxt + 1)



    bboxes_all = []

    skipped = 0

    extreme_frames = 0

    face_frames = 0

    max_yaw = 0.0

    trim_kept = 0

    extreme_segments = []



    for si in range(n_segs):

        seg_base = os.path.join(seg_dir, "seg_%03d" % si)

        seg_file = seg_base + ".mp4"

        # :donefile,,render

        if args.resume and si in done and os.path.exists(seg_file):

            seg_bboxes = state.get("segs", {}).get(str(si), [])

            bboxes_all.extend(seg_bboxes)

            _st = state.get("stats", {}).get(str(si), {})

            extreme_frames += _st.get("extreme", 0)

            face_frames += _st.get("face", 0)

            max_yaw = max(max_yaw, _st.get("max_yaw", 0.0))

            trim_kept += _st.get("trim_kept", 0)

            extreme_segments.append((si, _st.get("start_ts", 0.0), _st.get("end_ts", 0.0), _st.get("ratio", 0.0)))

            logging.info("  [ %d/%d] ✅ done,skip()", si + 1, n_segs)

            continue

        # render(looprender,)

        res = render_segment(cap, si, seg_frames, fps, w, h, app, swapper, args, source_face, max_yaw, skipped)

        seg_bboxes = res["seg_bboxes"]

        seg_extreme = res["seg_extreme"]

        seg_face = res["seg_face"]

        seg_trim_kept = res["seg_trim_kept"]

        max_yaw = max(max_yaw, res["seg_max_yaw"])

        skipped += res["seg_skipped"]

        bboxes_all.extend(seg_bboxes)

        seg_ratio = (seg_extreme / seg_face) if seg_face > 0 else 0.0

        extreme_segments.append((si, si * seg_secs, si * seg_secs + seg_secs, seg_ratio))

        done.add(si)

        state.setdefault("segs", {})[str(si)] = seg_bboxes

        state.setdefault("stats", {})[str(si)] = dict(extreme=seg_extreme, face=seg_face,

                                                       max_yaw=max_yaw, trim_kept=seg_trim_kept,

                                                       start_ts=si * seg_secs, end_ts=si * seg_secs + seg_secs,

                                                       ratio=seg_ratio)

        state["done"] = sorted(done)

        _save_resume_state(state_path, state)

        extreme_frames += seg_extreme

        face_frames += seg_face

        trim_kept += seg_trim_kept

        logging.info("  [ %d/%d] ✅ done(%d %d %.0f%%)", si + 1, n_segs, seg_face, seg_extreme, seg_ratio * 100)



    cap.release()



    # -- v2.7.0 :,/ --

    healed = heal_segments(seg_dir, n_segs, args.video, seg_frames, fps, w, h, app, swapper, args, source_face)

    if healed:

        logging.info("  🛠️  %d exception,continue", healed)



    #  → (ffmpeg ,failed cv2)

    concat_videos([os.path.join(seg_dir, "seg_%03d.mp4" % i) for i in range(n_segs)],

                  args.out, fps, w, h)

    trimmed_path = None

    if args.auto_trim_extreme:

        trimmed_path = os.path.splitext(args.out)[0] + "_trimmed.mp4"

        concat_videos([os.path.join(seg_dir, "seg_%03d_trim.mp4" % i) for i in range(n_segs)

                       if os.path.exists(os.path.join(seg_dir, "seg_%03d_trim.mp4" % i))],

                      trimmed_path, fps, w, h)

    try:

        shutil.rmtree(seg_dir)

        if os.path.exists(state_path):

            os.remove(state_path)

    except Exception:

        pass



    with open(args.bbox, "w") as f:

        json.dump({"w": w, "h": h, "bboxes": bboxes_all}, f)



    # (JSON, + time)

    extreme_ratio = (extreme_frames / face_frames) if face_frames > 0 else 0.0

    if extreme_ratio <= args.extreme_ratio_warn:

        plain = "available:/,."

    elif trimmed_path is not None and trim_kept > 0:

        plain = ":generate(),suggestionversion;quality."

    else:

        plain = ":face swapmodel>70°,suggestion, --auto-trim-extreme ."

    _ext_report = dict(face_frames=face_frames, extreme_frames=extreme_frames,

                       extreme_ratio=round(extreme_ratio, 3), max_yaw=round(max_yaw, 3),

                       trimmed_available=bool(trimmed_path and os.path.exists(trimmed_path)),

                       plain_summary=plain,

                       extreme_segments=[dict(seg=s, start="%.1fs" % st, end="%.1fs" % et, ratio=round(r, 3))

                                         for (s, st, et, r) in extreme_segments if r > args.extreme_ratio_warn])

    try:

        with open(os.path.splitext(args.out)[0] + "_extreme_report.json", "w") as f:

            json.dump(_ext_report, f, ensure_ascii=False, indent=2)

    except Exception:

        pass



    skip_ratio = (skipped / total) if total > 0 else 0.0

    if skip_ratio > args.max_skip_ratio:

        logging.error("E104: skipframe %.1f%%  %.1f%%,checkvideoqualitymodel",

                      skip_ratio * 100, args.max_skip_ratio * 100)



    # ============ pose(,) ============

    extreme_ratio = (extreme_frames / face_frames) if face_frames > 0 else 0.0

    logging.info("pose: frame=%d, frame(>70)=%d (%.1f%%), =%.2f",

                 face_frames, extreme_frames, extreme_ratio * 100, max_yaw)

    if extreme_ratio > args.extreme_ratio_warn:

        logging.warning("=" * 64)

        logging.warning("⚠️ video,'' %.1f%%(70)", extreme_ratio * 100)

        logging.warning("   face swapmodel(inswapper)--,model.")

        logging.warning("   ():")

        logging.warning("   ① ,/face swap()")

        logging.warning("   ②  Photoshop target/goal/video,")

        logging.warning("   ③ quality, matting/;")

        if trimmed_path is not None and trim_kept > 0:

            logging.warning("   ✅ generate'':%s (,)", trimmed_path)

        else:

            logging.warning("   crop? --auto-trim-extreme ")

        logging.warning("   :python scripts/faceswap_pro.py --video <video> --photo <> --preview-out preview.png")

        logging.warning("=" * 64)



    logging.info("DONE -> %s ; bbox -> %s ; skipframe=%d (%.1f%%)",

                  args.out, args.bbox, skipped, skip_ratio * 100)



    # ============ run(/ · v2.6.0) ============

    logging.info("=" * 56)

    logging.info("📋 run(): %s", plain)

    logging.info("   file: %s", args.out)

    if trimmed_path is not None and trim_kept > 0:

        logging.info("   : %s (,)", trimmed_path)

    logging.info("   pose: %s_extreme_report.json( plain_summary)",

                 os.path.splitext(args.out)[0])

    logging.info("=" * 56)





if __name__ == "__main__":

    main()

