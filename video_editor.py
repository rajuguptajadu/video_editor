import os
import tempfile
from moviepy import VideoFileClip
import streamlit as st

st.set_page_config(page_title="Short Video Converter", page_icon="🎬")

st.title("🎬 Short Video Converter & Vertical Cropper")
st.write(
    "Upload a video, trim it to 30s or 1m, optionally crop to 9:16 vertical,"
    " and export in your preferred format."
)

# 1. File Uploader
uploaded_file = st.file_uploader(
    "Upload your video", type=["mp4", "mov", "avi", "mkv", "webm"]
)

if uploaded_file is not None:
    # Unpack tuple cleanly to get just the file extension string
    _, input_suffix = os.path.splitext(uploaded_file.name)

    with tempfile.NamedTemporaryFile(
        delete=False, suffix=input_suffix
    ) as temp_input:
        temp_input.write(uploaded_file.read())
        temp_input_path = temp_input.name

    try:
        # Load video to get metadata
        clip = VideoFileClip(temp_input_path)
        total_duration = clip.duration
        orig_w, orig_h = clip.size
        clip.close()

        st.video(temp_input_path)
        st.info(
            f"Original Duration: **{total_duration:.2f}s** | Resolution:"
            f" **{orig_w}x{orig_h}**"
        )

        # 2. User Choices
        col1, col2 = st.columns(2)

        with col1:
            duration_choice = st.radio(
                "Select Short Video Duration:",
                options=["30 Seconds", "1 Minute (60 Seconds)"],
            )
            target_duration = 30 if duration_choice == "30 Seconds" else 60

        with col2:
            output_format = st.selectbox(
                "Select Output Video Format:", options=["mp4", "mov", "avi", "webm"]
            )

        # 3. Vertical Cropping Option
        st.subheader("Aspect Ratio & Cropping")
        crop_vertical = st.checkbox(
            "Crop to 9:16 Vertical (Shorts / Reels)", value=True
        )

        x_offset_percent = 50
        if crop_vertical:
            target_w = int(orig_h * (9 / 16))
            target_w = target_w - (target_w % 2)

            if target_w < orig_w:
                x_offset_percent = st.slider(
                    "Horizontal Crop Position (0% = Left, 50% = Center, 100% ="
                    " Right):",
                    min_value=0,
                    max_value=100,
                    value=50,
                )
            else:
                st.info("Video is already vertical or narrower than 9:16.")

        # 4. Start Time Slider
        max_start = max(0.0, total_duration - target_duration)
        start_time = 0.0
        if max_start > 0:
            start_time = st.slider(
                "Select Start Time (in seconds):",
                min_value=0.0,
                max_value=float(max_start),
                value=0.0,
                step=0.5,
            )
        else:
            st.warning(
                "Your video is shorter than or equal to the selected duration. The"
                " full video will be converted."
            )

        # 5. Process Video
        if st.button("Convert Video", type="primary"):
            with st.spinner("Processing & cropping your video... Please wait."):
                output_path = os.path.join(
                    tempfile.gettempdir(), f"short_video.{output_format}"
                )

                video = VideoFileClip(temp_input_path)
                end_time = min(start_time + target_duration, video.duration)
                processed_clip = video.subclipped(start_time, end_time)

                # Apply 9:16 Vertical Crop if selected
                if crop_vertical:
                    w, h = processed_clip.size
                    target_w = int(h * (9 / 16))
                    target_w = target_w - (target_w % 2)

                    if target_w < w:
                        max_x1 = w - target_w
                        x1 = int(max_x1 * (x_offset_percent / 100.0))
                        x2 = x1 + target_w
                        processed_clip = processed_clip.cropped(
                            x1=x1, y1=0, x2=x2, y2=h
                        )

                # Set appropriate codecs based on chosen format
                codec_map = {
                    "mp4": ("libx264", "aac"),
                    "mov": ("libx264", "aac"),
                    "avi": ("mpeg4", "mp3"),
                    "webm": ("libvpx", "libvorbis"),
                }
                v_codec, a_codec = codec_map[output_format]

                processed_clip.write_videofile(
                    output_path,
                    codec=v_codec,
                    audio_codec=a_codec,
                    logger=None,
                )

                processed_clip.close()
                video.close()

            st.success("Conversion complete!")

            if output_format in ["mp4", "webm"]:
                st.video(output_path)

            # 6. Download Button
            with open(output_path, "rb") as file:
                st.download_button(
                    label=f"Download Short Video (.{output_format})",
                    data=file,
                    file_name=f"short_clip.{output_format}",
                    mime=f"video/{output_format}",
                )

    except Exception as e:
        st.error(f"An error occurred while processing the video: {e}")

# Footer Credit
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray; padding: 10px;'>"
    "Design and Develop by <b>R K Gupta</b>"
    "</div>",
    unsafe_allow_html=True,
)
