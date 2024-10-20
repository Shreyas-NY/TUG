import streamlit as st
import numpy as np
import time
import threading
import wave
import winsound
import sounddevice as sd

scaled_seconds = []


def play_metronome(seconds, duration):
    
    global scaled_seconds
    last_second = seconds[-1]
    input_duration = last_second + 1
    scaling_factor = duration / input_duration
    scaled_seconds = [second * scaling_factor for second in seconds]
    def play_beep(start_time):
        winsound.Beep(440, 100)
        # print(f"Metronome ticked at time {time.time() - start_time:.2f} seconds")

    def play_metronome_ticks(scaled_seconds):
        for second in scaled_seconds:
            delay = second
            if delay > 0:
                start_time = time.time()
                threading.Timer(delay, play_beep, args=[start_time]).start()

    play_metronome_ticks(scaled_seconds)



def play_metronome_with_subdivisions(seconds, duration, filename, enable_subdivisions, subdivisions, numb_subdivisions):
    audio_data, sample_rate = process_file(seconds, duration, filename, enable_subdivisions, subdivisions, numb_subdivisions)
    sd.play(audio_data, sample_rate)
    sd.wait()


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
    tone = generate_tone(100, sample_rate, 440.0)
    
    audio_data = np.zeros(total_samples)
    
    for timestamp in seconds:
        start_sample = int(timestamp * sample_rate * scaling_factor)
        audio_data[start_sample:start_sample + len(tone)] += tone
    
    if enable_subdivisions:
        
        all_pairs = sorted([tuple(map(int, second.split(' - '))) for second in subdivisions])
        audio_data += process_subdivisions(all_pairs, scaling_factor, sample_rate, numb_subdivisions, total_samples)
    
    audio_data /= np.max(np.abs(audio_data))
    
    return audio_data, sample_rate


def write_to_wav_file(audio_data, filename, sample_rate):
    
    audio_data_pcm = (audio_data * 32767).astype(np.int16)

    filename = filename + '.wav'
    
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data_pcm.tobytes())
    
    st.success('Success! Please check your directory :)')


def main():

    st.set_page_config(layout="wide")

    # st.sidebar.markdown("[Link to Streamlit](https://www.streamlit.io/)")

    
    with st.chat_message('user'):
        
        st.write("HELP")
        st.header('INFORMATION')
        st.markdown('#### Developed at the BIO-FEEDBACK LAB, at Ramaiah Memorial Hospital.')

        
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
1. Preview: Plays a preview of the metronome based on the specified parameters.
2. Download: Downloads a WAV file of the baseline metronome.
3. Generate: Downloads all WAV file of the incremental/decremental metronome.''')
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

            st.write('''
- **Preview Metronome**

     1. Click the "Preview" button to listen to a preview of the baseline-metronome based on the entered settings.
     2. Adjust settings as necessary.''')

            st.write('''
 - **Download Metronome Audio**

     - Click "Download Baseline" to download the previewed WAV file.
     Ensure a valid filename is entered.
      - Click "Generate All" to download the incremental/decremental metronome.''')


    st.write('##')
    st.title("**Welcome to** Sync-TUG")
    # st.toast(':question: Kindly **scroll up** to find the **Help** section.')


    seconds = st.text_input("Seconds [space-separated]", placeholder="Example: 1 3 7", help="Example: 1 3 7")
    seconds_for_subdivisions = seconds.split()
    seconds = [int(second) for second in seconds.split()]
    
    number_of_trials = st.number_input("Number of Trials for Motor Imagery", min_value=1, step=1, value=10 ,placeholder="Example: 10", help="Example: 10")
    
    if seconds:
        default_duration = seconds[-1] + 1.00
    else:
        default_duration = 1.0
        
    duration = st.number_input("Desired Output Duration [seconds]", min_value=1.0, step=0.1, value=default_duration, help="Example: 10")
    filename = st.text_input("Output Filename", placeholder="Example: subject_01", value='TUG_MI_Trial_0',help="Example: subject_01")

    # Checkbox to enable subdivisions
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


    
    if st.button("Preview"):
        try:
            if enable_subdivisions:
                with st.spinner(text='Playing'):
                    play_metronome_with_subdivisions(seconds, duration, filename, enable_subdivisions, subdivisions, numb_subdivisions)
                    st.toast('**Completed** :white_check_mark:')

            else:
                with st.spinner(text='Playing'):
                    play_metronome(seconds, duration)
                    time.sleep(seconds[-1] + 1)

                    st.toast('**Completed** :white_check_mark:')
        except Exception as e:
            st.warning(e)
            st.warning('The fields above are required.')
    
        
    if st.button("Download Baseline"):
        try:
            if not filename:
                st.warning('Please enter a filename.')
                quit()

            try:
                audio_data, sample_rate = process_file(seconds, duration, filename, enable_subdivisions, subdivisions, numb_subdivisions)
                write_to_wav_file(audio_data, filename, sample_rate)

            except Exception as e:
                st.warning(e)
        except Exception as e:
                st.warning(e)
        
  
    if st.button("Generate All"):

        try:
            list_of_durations = calculate_durations(duration, number_of_trials)

            for i in range(len(list_of_durations)):
                filename = 'Trial_' + f'{i+1}'
                audio_data, sample_rate = process_file(seconds, list_of_durations[i], filename, enable_subdivisions, subdivisions, numb_subdivisions)
                write_to_wav_file(audio_data, filename, sample_rate)

        except Exception as e:
            st.warning(e)

        
        
    st.write('#') 


if __name__ == "__main__":
    main()