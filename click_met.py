import streamlit as st
import numpy as np
import time
import threading
import wave
import io

scaled_seconds = []


def generate_tone(duration_ms, sample_rate=44100, frequency=440.0):
    t = np.linspace(0, duration_ms / 1000, int(duration_ms * sample_rate / 1000), endpoint=False)
    tone = np.sin(2 * np.pi * frequency * t)
    return tone


def calculate_durations(output_duration, number_of_trials):
    final_trial_duration = output_duration / 2
    incremental_metronome_value = (output_duration - final_trial_duration) / (number_of_trials - 1)
    
    output_duration_list = [round(output_duration - i * incremental_metronome_value, 2) for i in range(number_of_trials)]
    return output_duration_list


def process_subdivisions(all_pairs, scaling_factor, sample_rate, num_subdivisions, total_samples):
    duration_ms = 100
    frequency_for_subdivisions = 300.0
    tone_for_subdivisions = generate_tone(duration_ms, sample_rate, frequency_for_subdivisions)
    
    audio_data = np.zeros(total_samples)
    
    for pair in all_pairs:
        start_sample_event = int(pair[0] * sample_rate * scaling_factor)
        second_duration = pair[1] - pair[0]
        spacing_samples = int(second_duration * sample_rate * scaling_factor)
        spacing_samples_per_click = spacing_samples // (num_subdivisions + 1)
        
        for i in range(1, num_subdivisions + 1):
            click_start_sample = start_sample_event + i * spacing_samples_per_click
            audio_data[click_start_sample:click_start_sample + len(tone_for_subdivisions)] += tone_for_subdivisions

    return audio_data


def process_file(seconds, duration, filename, enable_subdivisions, subdivisions, numb_subdivisions):
    last_second = seconds[-1]
    input_duration = last_second + 1
    scaling_factor = duration / input_duration
    sample_rate = 44100
    total_samples = int(duration * sample_rate)
    special_frequency = 660.0    
    # tone = generate_tone(100, sample_rate, 440.0)
    
    audio_data = np.zeros(total_samples)
    beep_count = 0

    for timestamp in seconds:
        beep_count += 1
        if beep_count == 3 or beep_count == 5:
            tone = generate_tone(100, sample_rate, special_frequency)
        else:
            tone = generate_tone(100, sample_rate, 440.0)

        start_sample = int(timestamp * sample_rate * scaling_factor)
        audio_data[start_sample:start_sample + len(tone)] += tone
    
    if enable_subdivisions:
        
        all_pairs = sorted([tuple(map(int, second.split(' - '))) for second in subdivisions])
        audio_data += process_subdivisions(all_pairs, scaling_factor, sample_rate, numb_subdivisions, total_samples)
    
    audio_data /= np.max(np.abs(audio_data))
    
    return audio_data, sample_rate


def write_to_wav_file(audio_data, filename, sample_rate, seconds):
    
    audio_data_pcm = (audio_data * 32767).astype(np.int16)

    filename = filename + '.wav'
    
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data_pcm.tobytes())
    
        with open(filename, 'rb') as f:
        # Streamlit's download button will now serve the file directly
            st.download_button(
                label=f"Download {seconds}",  # Hidden to user
                data=f,
                file_name=f"Motor_Imagery_file_{seconds}.wav",
                mime="audio/wav")


def main():

    st.set_page_config(layout="wide")
    
    with st.chat_message('user'):
        
        st.write("HELP")
        st.header('INFORMATION')
        st.markdown('# It is under development')

        
        tab1, tab2 = st.tabs(["NOTES", 'GUIDE ME'])

        with tab1:
            st.write("- **Maintain original duration:** For clicks at **pre-defined seconds**, kindly **do not** alter 'Desired Output Duration' below.")
            st.write('- **Proportionally alter seconds / intervals:** Reducing or increasing the output duration results in computed intervals for metronome clicks.')
            st.write('- **Subdivisions Usage:** Utilize subdivisions to maintain pacing during longer intervals between clicks.')

        with tab2:
            st.markdown('## Sync-TUG App Guide')
            # st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown('### BUTTONS')
            st.write('''
1. Download: Downloads all WAV file of the incremental/decremental metronome.''')
            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown('### SETTINGS')
            st.write('''
1. Subdivisions: Evenly spaced subdivisions between specified timestamps.''')
            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown('### STEPS TO USE')
            st.write('''
- **Enter Time Points**
     - Input the desired seconds **(space-separated)** where metronome clicks should occur.
     - Example: 1 3 7 8 12 13 15''')
            st.write('''
- **Set Output Duration**
     - Specify the total duration of the metronome output in seconds.
     - Example: 10''')
            st.write('''
- **Configure Subdivisions (Optional)**
     1. Enable subdivisions for cues.
     2. Select subdivisions between specified time intervals and adjust the number of subdivisions as needed.''')


    st.write('##')
    st.title("**Welcome to** Sync-TUG")

    seconds = st.text_input("Seconds [space-separated]", placeholder="Example: 1 3 7", help="Example: 1 3 7")
    seconds_for_subdivisions = seconds.split()
    seconds = [float(second) for second in seconds.split()]
    
    number_of_trials = st.number_input("Number of Trials for Motor Imagery", min_value=1, step=1, value=10 ,placeholder="Example: 10", help="Example: 10")
    
    if seconds:
        default_duration = seconds[-1] + 1.00
    else:
        default_duration = 1.0
        
    duration = st.number_input("Desired Output Duration [seconds]", min_value=1.0, step=0.1, value=default_duration, help="Example: 10")
    filename = st.text_input("Output Filename", placeholder="Example: subject_01", value='TUG_MI_Trial_0',help="Example: subject_01")

    enable_subdivisions = st.checkbox("Enable subdivisions")

    subdivisions = None
    numb_subdivisions = None
    
    if enable_subdivisions:

        formatted_seconds = []
        
        for i in range(len(seconds_for_subdivisions) - 1):
            start = seconds_for_subdivisions[i]
            end = seconds_for_subdivisions[i + 1]
            formatted_seconds.append(f"{start} - {end}")
            
        subdivisions = st.multiselect(label="Subdivisions between: ", options=formatted_seconds)
        numb_subdivisions = st.slider("Number of Subdivisions", min_value=0, max_value=8, value=4, step=1)
           
    st.markdown(
    """
    <style>
    .stButton>button {
        width: 200px;  
        height: 40px;
        cursor: pointer;
        }
    .stButton>button:hover{
        background-color: #0861EF;
        color: #FFFFFF;
    }
        
    </style>
    """,
    unsafe_allow_html=True
)

    
    # if st.button("DOWNLOAD"):

    try:
        list_of_durations = calculate_durations(duration, number_of_trials)

        concatenated_audio = np.array([])
        final_sample_rate = None

        for i in range(len(list_of_durations)):
            filename += f'{i+1}'
            audio_data, sample_rate = process_file(seconds, list_of_durations[i], filename, enable_subdivisions, subdivisions, numb_subdivisions)
            concatenated_audio = np.concatenate((concatenated_audio, audio_data)) if concatenated_audio.size else audio_data
            final_sample_rate = sample_rate

        write_to_wav_file(concatenated_audio, filename, sample_rate, seconds)
            # write_to_wav_file(audio_data, filename, sample_rate)


    except Exception as e:
        st.warning('Please check if all fields are filled.')

        
        
    st.write('#') 


if __name__ == "__main__":
    main()
