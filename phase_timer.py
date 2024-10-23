import streamlit as st
try:
    import cv2
    print("OpenCV version:", cv2.__version__)
except ImportError:
    st.info("OpenCV is not installed.")
import numpy as np
import pandas as pd
import tempfile

# Function to extract frames from the video
def get_video_frames(video_file):
    cap = cv2.VideoCapture(video_file)
    frames = []
    timestamps = []

    if not cap.isOpened():
        return frames, timestamps  # Return empty lists if the video cannot be opened

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))

    for i in range(frame_count):
        ret, frame = cap.read()
        if ret:
            frames.append(frame)
            timestamps.append(i / fps)  # timestamp in seconds
        else:
            break  # Exit the loop if no frame is read

    cap.release()
    return frames, timestamps

#
# # Function to display the selected frames and timestamps
def display_selected_frames(selected_frames, timestamps):
    st.write("### Selected Frames and Timestamps")
    selected_data = pd.DataFrame({
        'Frame Number': selected_frames,
        'Timestamp (seconds)': [timestamps[i] for i in selected_frames]
    })
    st.dataframe(selected_data)

# Initialize session state to track the current video index
if 'current_video_index' not in st.session_state:
    st.session_state.current_video_index = 0  # Start with the first video

# Video file upload (multiple files)
uploaded_files = st.file_uploader("Upload video files", type=["mp4", "mov", "avi"], accept_multiple_files=True)

if uploaded_files:
    if st.button("Next video"):
        if st.session_state.current_video_index < len(uploaded_files) - 1:
            st.session_state.current_video_index += 1  # Increment to the next video
        else:
            st.warning("No more videos to process.")
    # Get the current file based on session state's video index
    file = uploaded_files[st.session_state.current_video_index]
    st.session_state.frame_index = 0

    # Display the current video file being processed
    st.write(f"### Currently selected video: {file.name}")

    # Create a temporary file to store the uploaded video
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(file.read())
        tmp_file_path = tmp_file.name

    # st.video(tmp_file_path)  # You can display the video using the temp file path
    # Load frames and timestamps from the temporary file
    frames, timestamps = get_video_frames(tmp_file_path)

    # Check if frames were extracted
    if not frames:
        st.error("No frames were extracted from the video. Please check the video file.")
    else:
        # Frame selection index
        if 'frame_index' not in st.session_state:
            st.session_state.frame_index = 0  # Initialize the frame index

        # Frame selection display
        st.write("### Video Player")

        # Slider for frame selection
        st.session_state.frame_index = st.slider(
            "Frame Number", 0, len(frames) - 1, st.session_state.frame_index
        )

        # Display selected frame based on the current frame index
        selected_frame = frames[st.session_state.frame_index]
        # st.image(selected_frame, channels="BGR", caption=f"Frame: {st.session_state.frame_index}")

        # Navigation buttons
        col1, col2 = st.columns(2)

        with col1:
            if st.button("Previous Frame"):
                if st.session_state.frame_index > 0:
                    st.session_state.frame_index -= 1  # Go to the previous frame
                    st.session_state.frame_index = max(st.session_state.frame_index, 0)  # Ensure it doesn't go below 0

        with col2:
            if st.button("Next Frame"):
                if st.session_state.frame_index < len(frames) - 1:
                    st.session_state.frame_index += 1  # Go to the next frame
                    st.session_state.frame_index = min(st.session_state.frame_index,
                                                       len(frames) - 1)  # Ensure it doesn't exceed total frames

        # Display the selected frame based on updated index
        selected_frame = frames[st.session_state.frame_index]
        st.image(selected_frame, channels="BGR", caption=f"Frame: {st.session_state.frame_index}")

        # Select frame button
        if st.button("Select Frame"):
            if 'selected_frames' not in st.session_state:
                st.session_state.selected_frames = []
            st.session_state.selected_frames.append(st.session_state.frame_index)

        # Display selected frames
        if 'selected_frames' in st.session_state:
            display_selected_frames(st.session_state.selected_frames, timestamps)

        # Save button
        # if st.button("Save Selected Frames"):
        #     selected_frames = st.session_state.selected_frames
        #     if selected_frames:
        #         with open("selected_frames.txt", "w") as f:
        #             for frame in selected_frames:
        #                 f.write(f"Frame: {frame}, Timestamp: {timestamps[frame]}\n")
        #         st.success("Selected frames saved to selected_frames.txt")
        #     else:
        #         st.warning("No frames selected to save.")

        if st.button('Average Phase Time'):
            # Sample DataFrame with timestamps (replace this with your actual DataFrame)
            data = {
                'timestamps': [(timestamps[i]) for i in st.session_state.selected_frames if i < len(timestamps)]
            }

            df = pd.DataFrame(data)

            # Group by the pattern 1, 7, 13; 2, 8, 14, and so on
            averages = []

            # Loop over 6 groups: 1, 7, 13; 2, 8, 14; ..., 6, 12, 18
            for i in range(6):
                # Select every 6th element starting from index i
                group = df['timestamps'].iloc[i::6]
                avg = round(group.mean(), 2)  # Calculate the average of the group
                averages.append(float(avg))

            st.info(averages)


else:
    st.write("Please upload at least one video file.")
