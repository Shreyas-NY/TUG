import streamlit as st
import numpy as np
import time
import threading
import wave
import io
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

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
        if beep_count == 1 or beep_count == 6:
            tone = generate_tone(300, sample_rate, special_frequency)
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

    filename_wav = filename + '.wav'

    if 'baseline' in filename:
        with wave.open(filename_wav, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data_pcm.tobytes())
            
                with open(filename_wav, 'rb') as f:
                # Streamlit's download button will now serve the file directly
                    st.download_button(
                        label=f"Download Baseline {seconds}",  # Hidden to user
                        data=f,
                        file_name=f"Baseline_{filename}_{seconds}.wav",
                        mime="audio/wav")    

    else:
        with wave.open(filename_wav, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data_pcm.tobytes())
        
            with open(filename_wav, 'rb') as f:
            # Streamlit's download button will now serve the file directly
                st.download_button(
                    label=f"Download {seconds}",  # Hidden to user
                    data=f,
                    file_name=f"{filename}_{seconds}.wav",
                    mime="audio/wav")


def main():

    st.set_page_config(layout="wide")
    
    with st.chat_message('user'):
        
        st.write("INFORMATION")
        
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
1. Download: Downloads a single WAV file of the concatenated incremental/decremental metronome.''')
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
    filename = st.text_input("Output Filename", placeholder="Example: subject_01", value='TUG_MI',help="Example: subject_01")

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
            # filename += f'{i+1}'
            audio_data, sample_rate = process_file(seconds, list_of_durations[i], filename, enable_subdivisions, subdivisions, numb_subdivisions)
            concatenated_audio = np.concatenate((concatenated_audio, audio_data)) if concatenated_audio.size else audio_data
            final_sample_rate = sample_rate

        write_to_wav_file(concatenated_audio, filename, sample_rate, seconds)
            # write_to_wav_file(audio_data, filename, sample_rate)

        baseline_part = int(duration * final_sample_rate)

        # Slice the concatenated audio to retain only the first part
        baseline_part_audio = concatenated_audio[:baseline_part]

        # Write only the first part to the WAV file
        write_to_wav_file(baseline_part_audio, filename + "_baseline", final_sample_rate, seconds)



    except Exception as e:
        st.info('Please check if all fields are filled correctly.')

        
        
    st.write('#') 

# Establishing a Google Sheets connection

    st.title("TUG Management Portal")
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Fetch existing data
    existing_data = conn.read(worksheet='TUG_SCORE', ttl=1)
    existing_data = existing_data.dropna(how="all")
    
    
    ICD = [
        "Healthy",
        "Impairments",
        "Complaints",
        "Discomfort"]
    
    with st.form(key="TUG_form"):
        subject_name = st.text_input(label="Subject Name")
        ICD = st.selectbox("Condition", options=ICD, index=0)
        age = st.number_input("Age", value=70)
        current_date = st.date_input(label="Date")
        tug_initial = st.number_input("TUG-INITIAL",value=15.00)
        tug_final = st.number_input("TUG-FINAL", value=13.00)
        submit_button = st.form_submit_button(label="Submit TUG Details")
    
    
        if submit_button:
    
            if age == 70:
                st.toast("Age was not altered.")
            if tug_initial == 15.00:
                st.toast("Initial TUG score was not altered.")
            if tug_final == 13.00:
                st.toast("Final TUG score was not altered.")
    
            # Check if all mandatory fields are filled
            if not subject_name:
                st.error("Ensure Subject name is filled.")
                st.stop()
            else:
                # Create a new row of vendor data
                subject_data = pd.DataFrame(
                    [
                        {
                            "SUBJECT'S NAME": subject_name,
                            "SUBJECT'S AGE": age,
                            "ICD": ICD,
                            "DATE": current_date.strftime("%Y-%m-%d"),
                            "TUG-INITIAL": tug_initial,
                            "TUG-FINAL": tug_final,
                            "TUG-DIFFERENCE": tug_initial - tug_final
    
                        }
                    ]
                )
    
                # Add the new vendor data to the existing data
                existing_data = pd.concat([existing_data, subject_data], ignore_index=True)
    
    
                # Update Google Sheets with the new vendor data
                conn.update(worksheet="TUG_SCORE", data=existing_data)
    
                st.toast("Details successfully submitted!")
                st.info("Details successfully submitted!")
    
    
    
    updated_data = st.data_editor(existing_data)
    if st.button('Save Changes'):
        # conn.update(worksheet="TUG_SCORE", data=updated_data)
        updated_data["TUG-DIFFERENCE"] = updated_data['TUG-INITIAL'] - updated_data['TUG-FINAL']
        st.info('Observe the updates below')
        conn.update(worksheet="TUG_SCORE", data=updated_data)
        st.dataframe(updated_data)
        st.info('Changes saved successfully!')
    
    
    if st.button('Generate Plots'):
        # Create plots based on the data
        fig, ax = plt.subplots(1, 2, figsize=(12, 6))
    
        # Example Plot 1: Age Distribution
        sns.lineplot(updated_data['SUBJECT\'S AGE'], ax=ax[0])
        ax[0].set_title("Age Distribution")
        ax[0].set_xlabel("Age")
        ax[0].set_ylabel("Frequency")
    
        # Bar width
        bar_width = 0.35
        subjects = updated_data.index
    
        # Create bars for TUG-INITIAL and TUG-FINAL
        ax[1].bar(subjects, updated_data['TUG-INITIAL'], width=bar_width, label='TUG-INITIAL', color='cyan', align='center')
        ax[1].bar(subjects, updated_data['TUG-FINAL'], width=bar_width, label='TUG-FINAL', color='purple', align='edge')
    
        # Adding labels and title
        ax[1].set_title("TUG Scores Comparison")
        ax[1].set_xlabel("Subjects")
        ax[1].set_ylabel("Scores")
        ax[1].legend()
        ax[1].set_xticklabels(subjects, rotation=45, ha='right')  # Rotate subject names for better readability
    
        st.pyplot(fig)
    
        figg, ax = plt.subplots(1,2,figsize=(12, 6))
        count_greater_equal_2 = (existing_data['TUG-DIFFERENCE'] >= 2).sum()
        count_less_than_2 = (existing_data['TUG-DIFFERENCE'] < 2).sum()
        labels = ['COI', ' ']
        sizes = [count_greater_equal_2, count_less_than_2]
        ax[0].pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=['lightpink', 'purple'])
        ax[0].axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        ax[0].set_title('Proportion of Subjects with TUG Difference ≥ 2')
    
        filtered_data = existing_data[existing_data['TUG-DIFFERENCE'] < 2]
    
        # Count the occurrences of each ICD label for these subjects
        icd_counts = filtered_data['ICD'].value_counts()
        palette = sns.color_palette("pastel", len(icd_counts))
    
        # Plotting
        ax[1].bar(icd_counts.index, icd_counts.values, color=palette)
        ax[1].set_xlabel("ICD Category")
        ax[1].set_ylabel("Frequency")
        ax[1].set_title("Frequency of ICD Labels for Subjects with TUG Difference < 2")
    
        st.pyplot(figg)





if __name__ == "__main__":
    main()
