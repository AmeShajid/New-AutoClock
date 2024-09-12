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

# Assign a 5-digit code to each person
person_codes = {
    "Ame Shajid": "12345",  # Example code for Ame Shajid
    # You can add more people and their corresponding codes here
}

# Check if the image directory exists. If not, create it.
if not os.path.exists(image_dir):
    os.makedirs(image_dir)  # Create the directory if it does not exist

# Check if the CSV file exists. If not, create it and write the header row
if not os.path.exists(csv_file):
    with open(csv_file, 'w', newline='') as file:  # Open the CSV file in write mode
        writer = csv.writer(file)  # Create a CSV writer object
        # Write the header row to the CSV file
        writer.writerow(['Date', 'Name', 'Time In', 'Time Out', 'Hours Worked'])

# Initialize `last_recorded_minute` to keep track of the last time a clock-in was recorded
last_recorded_minute = None

def verify_user():
    """Verify the user's name and code."""
    # Ask the user for their name and remove any extra spaces
    user_name = input("Please enter your name: ").strip()
    
    # Check if the name is valid
    if user_name in person_codes:
        # Ask the user for their 5-digit code and remove any extra spaces
        user_code = input("Please enter your 5-digit code: ").strip()
        
        # Check if the code matches the code for the given name
        if user_code == person_codes[user_name]:
            print(f"Code verified for {user_name}")  # Inform the user that the code is correct
            print(f"Welcome, {user_name}.")  # Print the welcome message
            return user_name  # Return the user's name
        else:
            print("Invalid code. Please try again.")  # If the code is incorrect, try again
            return verify_user()  # Retry by calling the function again
    else:
        print("Invalid name. Please try again.")  # If the name is incorrect, try again
        return verify_user()  # Retry by calling the function again

def save_image(frame, name, action):
    """Save an image of the person clocking in or out."""
    # Get the current timestamp and format it as YYYYMMDD_HHMMSS
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    # Create a filename with the name, action (in or out), and timestamp
    filename = f"{name}_{action}_{timestamp}.jpg"
    # Combine directory and filename into a full path
    filepath = os.path.join(image_dir, filename)
    
    # Save the image to the specified filepath
    cv2.imwrite(filepath, frame)

def calculate_hours(start_time, end_time):
    """Calculate the difference in hours and minutes between two times."""
    # Define the format for time strings
    time_format = "%I:%M %p"
    # Convert start and end times from strings to datetime objects
    start = datetime.strptime(start_time, time_format)
    end = datetime.strptime(end_time, time_format)
    # Calculate the time difference between start and end
    delta = end - start

    # Convert the time difference into hours and minutes
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    # Format the time difference as "X hours and Y minutes"
    formatted_time = f"{hours} hours and {minutes} minutes"
    return formatted_time

def process_frame(frame, name):
    """Process the frame to check for clock-in and save image if needed."""
    global last_recorded_minute  # Use the global variable to keep track of the last recorded minute
    
    # Convert the image from BGR (default color format in OpenCV) to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Detect faces in the image
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    # Get the current date and time
    current_time = datetime.now()
    # Round the time to the nearest minute
    current_minute = current_time.replace(second=0, microsecond=0)

    # Format the current time and date
    formatted_time = current_time.strftime('%I:%M %p')  # Format time as 12-hour clock with AM/PM
    formatted_date = current_time.strftime('%Y-%m-%d')  # Format date as YYYY-MM-DD

    # Record the timestamp only if it's a new minute
    if last_recorded_minute != current_minute:
        # Open the CSV file in append mode
        with open(csv_file, 'a', newline='') as file:
            writer = csv.writer(file)
            # Write the row with date, name, clock-in time, and empty clock-out time
            row = [formatted_date, name, formatted_time, '', '']
            writer.writerow(row)  # Write the row to the CSV file
        
        # Save an image of the person who clocked in
        save_image(frame, name, 'in')
        
        # Update the last recorded minute
        last_recorded_minute = current_minute

    return frame  # Return the processed frame

def clock_out(name):
    """Handle clocking out and update the CSV file with the clock-out time."""
    # Initialize video capture for clock-out
    video_capture = cv2.VideoCapture(0)  # Open the video capture from the default camera
    ret, frame = video_capture.read()  # Capture a frame for the clock-out picture
    video_capture.release()  # Release the camera resource

    if ret:  # If a frame was successfully captured
        # Get the current time and format it for the CSV file
        current_time = datetime.now()
        formatted_time = current_time.strftime('%I:%M %p')

        # Save a picture of the person clocking out
        save_image(frame, name, 'out')

        # Open the CSV file and find the last clock-in entry for the user
        rows = []
        with open(csv_file, 'r') as file:
            rows = list(csv.reader(file))  # Read all the rows into a list

        # Iterate through the rows in reverse to find the latest clock-in entry
        for i in range(len(rows) - 1, -1, -1):
            if rows[i][1] == name and rows[i][3] == '':
                # Calculate the hours worked using the calculate_hours function
                clock_in_time = rows[i][2]
                hours_minutes = calculate_hours(clock_in_time, formatted_time)

                # Handle possible formatting issues
                if 'hours and' in hours_minutes:
                    try:
                        hours, minutes = map(int, hours_minutes.replace(' hours and ', ' ').replace(' minutes', '').split())
                        # Update the row with the clock-out time and hours worked
                        rows[i][3] = formatted_time
                        rows[i][4] = f"{hours}h and {minutes}m"

                        # Write the updated rows back to the CSV file
                        with open(csv_file, 'w', newline='') as file:
                            writer = csv.writer(file)
                            writer.writerows(rows)

                        print(f"{name} clocked out at {formatted_time}.")
                        print(f"Hours worked: {hours} hours and {minutes} minutes.")
                        break  # Exit the loop after updating the latest clock-in entry
                    except ValueError:
                        print("Error parsing hours and minutes.")
                else:
                    print("Unexpected format in hours_minutes.")
                break
    else:
        print("Failed to capture clock-out image.")

def main():
    """Main function to handle user input and clock in or clock out."""
    # Verify the user's name and code
    name = verify_user()
    # Ask the user to type 'in' or 'out' and convert input to lowercase
    action = input("Type 'in' to clock in or 'out' to clock out: ").strip().lower()
   
    if action == 'in':  # Check if the user wants to clock in
        # Initialize video capture for clock-in
        video_capture = cv2.VideoCapture(0)  # Open the video capture from the default camera

        while True:  # Start an infinite loop to keep capturing frames
            # Capture a frame from the camera
            ret, frame = video_capture.read()
            if not ret:  # If the frame was not captured successfully
                break  # Exit the loop
            
            time.sleep(3)  # Pause for 3 seconds to avoid capturing black images
            # Process the frame for clock-in
            frame = process_frame(frame, name)
            # Show the frame in a window named 'Video'
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

# Run the function
if __name__ == "__main__":
    main()



