import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Establishing a Google Sheets connection

st.title("TUG Management Portal")
spreadsheet = st.secrets["connections_gsheets"]["spreadsheet"]
st.success(spreadsheet)
conn = st.connection("gsheets", spreadsheet=spreadsheet, type=GSheetsConnection)

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
