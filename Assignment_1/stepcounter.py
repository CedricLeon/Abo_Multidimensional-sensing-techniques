import numpy as np
import matplotlib.pyplot as plt

# Simple function to visualize 4 arrays that are given to it
def visualize_data(timestamps, x_arr, y_arr, z_arr, s_arr, thresholds_history):

    # Plotting accelerometer readings
    plt.figure(1)
    plt.plot(timestamps, x_arr, color = "blue" , linewidth = 1.0)
    plt.plot(timestamps, y_arr, color = "red"  , linewidth = 1.0)
    plt.plot(timestamps, z_arr, color = "green", linewidth = 1.0)
    plt.plot(timestamps, s_arr, color = "black", linestyle="--", linewidth = 1.0)
    plt.plot(timestamps, thresholds_history, color = "black", linestyle=":" , linewidth = 1.0)
    plt.show()

    # Magnitude array calculation
    m_arr = []
    for i, x in enumerate(x_arr):
        m_arr.append(magnitude(x_arr[i], y_arr[i], z_arr[i]))

    # Plotting magnitude and steps
    plt.figure(2)
    plt.plot(timestamps, s_arr, color = "black", linewidth = 1.0)
    plt.plot(timestamps, m_arr, color = "red"  , linewidth = 1.0)
    plt.show()

# Function to read the data from the log file and return them into array variables
def read_data(fileName):
    # Get file name
    print("Import data from \"" + str(fileName) + "\"")

    # Open file, get every line and close the file
    with open(str(fileName), "r") as file:
        data = file.readlines()
    print("The file contains " + str(len(data)) + " time steps.")

    # Init empty arrays
    timestamps = []
    x_array = []
    y_array = []
    z_array = []

    # Browse rows and store specific values in arrays
    for i in range(len(data)):
        # Split each row and store result in a tab
        values = data[i].split(",")

        # Pick up and cast each value
        timestamps.append(int(values[0]))
        x_array.append(float(values[1]))
        y_array.append(float(values[2]))
        z_array.append(float(values[3]))

    # Return 4 arrays containing timestamps and the corresponding acceleration for x, y and z axes
    return timestamps, x_array, y_array, z_array

# This function identifies the axis sensible to gravity effect
# On this axis we will see gravity effects: Gravity on earth is around 10 m/s² but, if the phone is head on or head up it can be +10 or -10 so we check both
# This functoin return:
#       - the array which the corresponding axis as been found parallel to gravity
#       - if the phone is head up (headup == 1) or head down (headup == 0)
def identify_gravity(x_arr, y_arr, z_arr):

    # Make averages for each array (on the whole period)
    avg_x = 0
    avg_y = 0
    avg_z = 0
    time_period = len(x_arr)
    for i in range(time_period):
        avg_x = avg_x + x_arr[i]
        avg_y = avg_y + y_arr[i]
        avg_z = avg_z + z_arr[i]
    avg_x = avg_x/time_period
    avg_y = avg_y/time_period
    avg_z = avg_z/time_period

    # Check for the average > or < to 7
    gravity_threshold = 7
    avg = 0
    if avg_x > gravity_threshold or avg_x < -gravity_threshold:
        print("     Selected array: X axis, avg_x: " + str(int(avg_x*100)/100))
        selected_arr = x_arr
        avg = avg_x
    elif avg_y > gravity_threshold or avg_y < -gravity_threshold:
        print("     Selected array: Y axis, avg_y: " + str(int(avg_y*100)/100))
        selected_arr = y_arr
        avg = avg_y
    elif avg_z > gravity_threshold or avg_z < -gravity_threshold:
        print("     Selected array: Z axis, avg_z: " + str(int(avg_z*100)/100))
        selected_arr = z_arr
        avg = avg_z
    else:
        print("     No array was detected as \"gravity sensitive\", taking default: X axis")
        print("     avg_x: " + str(avg_x) + ", avg_y: " + str(avg_y) + " and avg_z: " + str(avg_z))
        selected_arr = x_arr
        avg = avg_x

    # Check if the phone is head up or head down
    head_up = 1
    if avg < 0:
        print("     The phone was detected head down.")
        head_up = 0
    else:
        print("     The phone was detected head up.")

    return selected_arr, head_up

# Function to count steps (Solution N°1: Fixed threshold).
# Should return an array of timestamps from when steps were detected
# Each value in this array should represent the time that step was made.
def count_steps_1(timestamps, x_arr, y_arr, z_arr):
    # --- Identify the axis which is sensible to gravity ---
    selected_arr, head_up = identify_gravity(x_arr, y_arr, z_arr)

    # --- First solution: Fixed threshold ---
    # This solution uses a fixed and pre-determined threshold as well as a minimum time between 2 step detection
    # This feature has been added in order to avoid detecting the same step twice

    # Fixed and default threshold
    threshold = 13
    # Minimum time between 2 steps detection management
    minimum_time_between_steps = 10
    last_step_time = -minimum_time_between_steps
    # Data record variables
    steps_count = 0
    rv = []
    thresholds_history =[0]

    # Browse every timestamp
    for i in range(len(timestamps)-1):
        time = timestamps[i]

        # Check if the threshold has been exceeded (Phone head up or Phone head down)
        if (selected_arr[i] >  threshold > selected_arr[i + 1]) or (selected_arr[i] < -threshold < selected_arr[i + 1]):
            # Check if last step detection was too recent
            if time > last_step_time+minimum_time_between_steps:
                # Update every variable for a step detection
                rv.append(time)
                steps_count += 1
                last_step_time = time

        # Record the threshold every timestep for threshold printing in visualize_data()
        if (head_up == 1):
            thresholds_history.append(threshold)
        elif (head_up == 0):
            thresholds_history.append(-threshold)

    # Print result
    print("     Identified steps: " + str(steps_count) + ", at time: " + str(rv))
    return rv, thresholds_history


# Function to count steps (Solution N°2: Dynamic threshold).
# Should return an array of timestamps from when steps were detected
# Each value in this array should represent the time that step was made.
def count_steps_2(timestamps, x_arr, y_arr, z_arr):
    # --- Identify the axis which is sensible to gravity ---
    selected_arr, head_up = identify_gravity(x_arr, y_arr, z_arr)

    # --- Second solution: Dynamic threshold ---
    # This solution uses a dynamic threshold as well as a minimum time between 2 step detection
    # This feature has been added in order to avoid detecting the same step twice

    # Number of sample inside the time window. The time window goes through [i:i+nb_samples]
    nb_samples = 50
    # Minimum time between 2 steps detection management
    minimum_time_between_steps = 10
    last_step_time = -minimum_time_between_steps
    # Data record variables
    steps_count = 0
    rv = []
    thresholds_history =[0]

    # Browse every timestamp
    for i in range(len(timestamps)-1):
        time = timestamps[i]

        # Refresh threshold every 2*nb_samples
        if (i % nb_samples == 0):
            # Check if new index doesn't go out of bounds
            end_sample   = len(timestamps) if i + nb_samples > len(timestamps) else i + nb_samples

            # Find min and max inside the time window
            min = np.min(selected_arr[i:end_sample])
            max = np.max(selected_arr[i:end_sample])

            # Compute the new threshold
            if (head_up == 1):
                threshold = 0.65*max + 0.35*min
            elif (head_up == 0):
                threshold = 0.35*max + 0.65*min
            print("     [" + str(i) + "; " + str(end_sample) + "] new threshold: " + str(int(threshold*100)/100))

            # Check if the new threshold is viable (in order for example to avoid detecting step when the phone is not in the pocket)
            if (head_up == 1) and (threshold < 11):
                threshold = 100
            elif (head_up == 0) and (threshold > -11):
                threshold = -100
            print("         [" + str(i) + "; " + str(end_sample) + "] new threshold: " + str(int(threshold*100)/100))

        # Record the threshold every timestep for threshold printing in visualize_data()
        thresholds_history.append(threshold)

        # Check if the threshold has been exceeded (Phone head up or Phone head down)
        if (selected_arr[i] >  threshold > selected_arr[i + 1]) or (selected_arr[i] < -threshold < selected_arr[i + 1]):
            # Check if last step detection was too recent
            if time > last_step_time+minimum_time_between_steps:
                # Update every variable for a step detection
                rv.append(time)
                steps_count += 1
                last_step_time = time

    # Print result
    print("     Identified steps: " + str(steps_count) + ", at time: " + str(rv))
    return rv, thresholds_history


# Calculate the magnitude of the given vector
def magnitude(x, y, z):
    return np.linalg.norm((x, y, z))

# Function to convert array of times where steps happened into array to give into graph visualization
# Takes timestamp-array and array of times that step was detected as an input
# Returns an array where each entry is either zero if corresponding timestamp has no step detected or 50000 if the step was detected
def generate_step_array(timestamps, step_time):
    s_arr = []
    ctr = 0

    for i, time in enumerate(timestamps):
        if(ctr < len(step_time) and step_time[ctr] <= time):
            ctr += 1
            s_arr.append(20)
        else:
            s_arr.append(-30)

    while(len(s_arr) < len(timestamps)):
        s_arr.append(0)

    return s_arr

# Check that the sizes of arrays match
def check_data(t,x,y,z):
    if( len(t) != len(x) or len(y) != len(z) or len(x) != len(y) ):
        print("Arrays of incorrect length")
        return False
    print("The amount of data read from accelerometer is " + str(len(t)) + " entries.")
    return True


def main():

    # 3 different datasets:
    #   - Slow_outside (22 real steps)
    #   - Fast_outside (28 real steps)
    #   - Stairs (36 real steps = 32 stairs step + 4 normal steps between the 4 small stairs)
    fileName = "Data/Slow_outside.csv"
    # Slow_outside (22, detected 23 / 20) || Fast_outside (28, 30 / 24 detected (phone goes in and out the pocket)) || Stairs (36 = 32 stairs step + 4 normal steps between the 4 small stairs) (37 / 35 detected)

    # Read data from a measurement file, change the input file name if needed
    timestamps, x_array, y_array, z_array = read_data(fileName)

    # Check that the data does not produce errors
    if(not check_data(timestamps, x_array,y_array,z_array)):
      return

    # Count the steps based on array of measurements from accelerometer
    st, thresholds_history = count_steps_1(timestamps, x_array, y_array, z_array)

    # Print the result
    print("This data contains " + str(len(st)) + " steps according to current algorithm")

    # Convert array of step times into graph-compatible format
    s_array = generate_step_array(timestamps, st)

    # Visualize data and steps
    visualize_data(timestamps, x_array, y_array, z_array, s_array, thresholds_history)

# Call main() function
main()
