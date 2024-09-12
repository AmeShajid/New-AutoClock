import cv2  # Import OpenCV for working with video and images
import face_recognition  # Import face_recognition to recognize faces in images
import csv  # Import csv to read and write CSV files
import os  # Import os to handle file and directory operations
import time  # Import time to pause the program if needed
from datetime import datetime  # Import datetime to get the current date and time

# Define the path to the CSV file where clock-in/clock-out data will be stored
csv_file = '/Users/ameshajid/Documents/VisualStudioCode/Small Projects/AutoClock/AutoClock_data.csv'
# Define the path to the directory where images will be saved
image_dir = '/Users/ameshajid/Documents/VisualStudioCode/Small Projects/AutoClock/Images'

# Check if the image directory exists. If not, create it.
if not os.path.exists(image_dir):
    os.makedirs(image_dir)  # Create the directory if it does not exist

# Check if the CSV file exists. If not, create it and write the header row
if not os.path.exists(csv_file):
    with open(csv_file, 'w', newline='') as file:  # Open the CSV file in write mode
        writer = csv.writer(file)  # Create a CSV writer object
        # Write the header row to the CSV file
        writer.writerow(['Date', 'Name', 'Time In', 'Time Out', 'Hours Worked'])

# Prompt the user to enter their name
name = input("Please enter your name: ")

# Initialize a variable to keep track of the last recorded minute
last_recorded_minute = None

def save_image(frame, name, action):
    """Save an image of the person clocking in or out."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')  # Get the current timestamp and format it
    filename = f"{name}_{timestamp}.jpg"  # Create a filename with the name and timestamp
    filepath = os.path.join(image_dir, filename)  # Combine directory and filename into a full path
    
    # Save the image to the specified filepath
    cv2.imwrite(filepath, frame)

def process_frame(frame):
    """Process the frame to check for clock-in and save image if needed."""
    global last_recorded_minute  # Use the global variable to keep track of the last recorded minute
    
    # Convert the image from BGR (default color format in OpenCV) to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Detect faces in the image
    face_locations = face_recognition.face_locations(rgb_frame)  # Find faces in the image
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)  # Get face encodings

    # Get the current date and time
    current_time = datetime.now()  # Get the current date and time
    # Round the time to the nearest minute
    current_minute = current_time.replace(second=0, microsecond=0)  # Remove seconds and microseconds

    # Format the current time and date
    formatted_time = current_time.strftime('%I:%M %p')  # Format time as 12-hour clock with AM/PM
    formatted_date = current_time.strftime('%Y-%m-%d')  # Format date as YYYY-MM-DD

    # Record the timestamp only if it's a new minute
    if last_recorded_minute != current_minute:  # Check if the current minute is different from the last recorded minute
        with open(csv_file, 'a', newline='') as file:  # Open the CSV file in append mode
            writer = csv.writer(file)  # Create a CSV writer object
            # Write the row with date, name, clock-in time, and empty clock-out time
            row = [formatted_date, name, formatted_time, '', '']
            writer.writerow(row)  # Write the row to the CSV file
        
        # Save an image of the person who clocked in
        save_image(frame, name, 'in')
        
        # Update the last recorded minute
        last_recorded_minute = current_minute

    return frame  # Return the processed frame

def calculate_hours(start_time_str, end_time_str):
    """Calculate the difference in hours and minutes between two time strings."""
    format_str = '%I:%M %p'  # Define the time format
    start_time = datetime.strptime(start_time_str, format_str)  # Convert start time string to datetime object
    end_time = datetime.strptime(end_time_str, format_str)  # Convert end time string to datetime object
    time_diff = end_time - start_time  # Calculate the time difference
    hours, remainder = divmod(time_diff.seconds, 3600)  # Get hours and the remainder in seconds
    minutes, _ = divmod(remainder, 60)  # Get minutes from the remainder
    return hours, minutes  # Return hours and minutes

def right_align_hours(hours_worked, max_length):
    """Right-align the hours worked value with spaces."""
    return hours_worked.rjust(max_length)  # Right-align the string to the specified length

def clock_out(name):
    """Handle clocking out and update the CSV file with the clock-out time."""
    # Read the current data from the CSV file
    rows = []  # Initialize an empty list to store rows
    with open(csv_file, 'r', newline='') as file:  # Open the CSV file in read mode
        reader = csv.reader(file)  # Create a CSV reader object
        for row in reader:  # Iterate through each row in the CSV file
            rows.append(row)  # Add each row to the list
    
    # Update the clock-out time for the specific name
    updated = False  # Initialize a flag to check if an update was made
    with open(csv_file, 'w', newline='') as file:  # Open the CSV file in write mode
        writer = csv.writer(file)  # Create a CSV writer object
        for row in rows:  # Iterate through each row in the list
            if row[1] == name and row[3] == '':  # Check if the row matches the name and clock-out time is empty
                row[3] = datetime.now().strftime('%I:%M %p')  # Update the clock-out time with the current time
                hours, minutes = calculate_hours(row[2], row[3])  # Calculate hours worked
                hours_worked = f"{hours}h {minutes}m"  # Format hours worked
                row[4] = right_align_hours(hours_worked, 10)  # Right-align the hours worked
                updated = True  # Set the flag to True indicating an update was made
            writer.writerow(row)  # Write the updated row to the CSV file
    
    if updated:  # Check if an update was made
        # Initialize video capture to take a picture of the person clocking out
        video_capture = cv2.VideoCapture(0)  # Open the video capture from the default camera
        time.sleep(2)  # Pause for 2 seconds to allow the camera to adjust
        ret, frame = video_capture.read()  # Read a frame from the video capture
        if ret:  # Check if the frame was successfully captured
            # Save the image of the person who clocked out
            save_image(frame, name, 'out')
        video_capture.release()  # Release the camera resource
        cv2.destroyAllWindows()  # Close any OpenCV windows
    else:
        # Print a message if no clock-in record was found for the given name
        print("No clock-in record found for", name)

def main():
    """Main function to handle user input and clock in or clock out."""
    # Ask the user if they want to clock in or clock out
    action = input("Type 'in' to clock in or 'out' to clock out: ").strip().lower()  # Get user input and convert to lowercase
   
    if action == 'in':  # Check if the user wants to clock in
        # Initialize video capture for clock-in
        video_capture = cv2.VideoCapture(0)  # Open the video capture from the default camera

        while True:  # Start an infinite loop
            # Capture a frame-by-frame from the camera
            ret, frame = video_capture.read()  # Read a frame from the video capture
            if not ret:  # If the frame was not captured successfully
                break  # Exit the loop
            
            time.sleep(3)  # Pause for 3 seconds to avoid capturing black images
            frame = process_frame(frame)  # Process the frame for clock-in
            cv2.imshow('Video', frame)  # Show the frame in a window named 'Video'
            if cv2.waitKey(1) & 0xFF == ord('q'):  # Check if the 'q' key was pressed
                break  # Exit the loop

        video_capture.release()  # Release the camera resource
        cv2.destroyAllWindows()  # Close any OpenCV windows
    
    elif action == 'out':  # Check if the user wants to clock out
        clock_out(name)  # Call the function to handle clock-out
    
    else:  # If the input is not 'in' or 'out'
        # Print a message if the input is not valid
        print("Invalid action. Please type 'in' or 'out'.")

#run the function woohoo we are done
if __name__ == "__main__":
    main()

