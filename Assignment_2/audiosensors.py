# ------------------- Dependencies -------------------
import sys          # System manipulation
import time         # Used to pause execution in threads as needed
import keyboard     # Register keyboard events (keypresses)
import threading    # Threads for parallel execution
import pyaudio      # Audio streams
import numpy as np  # Matrix/list manipulation
import audioop      # Getting volume from sound data

# GUI dependencies
from PyQt5.QtWidgets import QApplication, QLabel, QWidget
from PyQt5.QtGui import *

#import struct      # Used for converting sound data to integer lists
#import wave        # For recording the sound into playable .wav files from scipy.fftpack import fft

# ------------------- Constants for streams, modify with care! -------------------
CHUNK = 1024*4
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100


# ------------------- Check the input devices -------------------
print("Available audio devices:")
p = pyaudio.PyAudio()
info = p.get_host_api_info_by_index(0)
numdevices = info.get('deviceCount')
for i in range(0, numdevices):
    if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
        print ("Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name'))
p.terminate()


# Code modified from: https://people.csail.mit.edu/hubert/pyaudio/

# Method running on a thread, called once per audio device. This method:
#   - Read and store the audiostream in the buffer
#   - Compute individual mean and variance for each signal (over the last 100 ([buffer_width]) audio signals)
#   - Display the current volume and the individual mean and variance on a label
def log_sound(index, label):

    # --- Global variables ---
    global buffer           # This global buffer consists of several lists one for each audio device
    global buffer_width     # Size of the list available for each audio device (at buffer[index])
    global mean_combined    # Combined mean for the current volumes (computed in mainThread())
    global var_combined     # Combined variance for the current volumes (computed in mainThread())
    #wave_buffer = []       # Store audiosignal here

    # Open audio stream
    stream = p.open(
        format = FORMAT,           # Format of stream data
        channels = CHANNELS,       # Number of input channels
        rate = RATE,               # Frequency of audio
        input = True,              # Stream reads data
        frames_per_buffer = CHUNK, # Number of inout frames for each buffer
        input_device_index = index # Input device
    )

    while True:
        # --- Read, Calculate and Store ---
        # Read a chunk of data from the stream
        data = stream.read(CHUNK)
        # Store the data in buffer for .wav file convertion
        #wave_buffer.append(data)
        # Calculate the volume from the "chunk" of data
        volume = audioop.rms(data, 2)
        # Append the necessary data to the buffer
        buffer[index].append(volume)

        # --- Individual mean / var computation ---
        # Cast np.list into np.array (for .mean() usage)
        buff_array = np.array(buffer[index])
        # Compute mean and var for this array
        mean_indiv = buff_array.mean()
        var_indiv  = np.var(buff_array)

        # --- Check for potential defection ---
        # We consider the microphone defected if:
        #   - its individual mean is low;
        #   - the combined variance is high (which means the environment is not silent);
        #   - and finally, if its individual mean is highly under the combined mean.
        defected = 0
        if (mean_indiv < 500) and (var_combined > 50000) and (mean_indiv + 1000 < mean_combined):
            defected = 1
            print("     " + str(index) + ": m_indiv = " + str(int(mean_indiv*10)/10) + ", mean_combined = " + str(mean_combined))

        # --- Update label background color (depending on microphone defection) ---
        # The idea was to change the labl background color in red when considered defected, but this method is not thread safe and generate segmentation faults. Therefore we will simply add "-----" before the label text
        defected_str = ""
        if defected == 1:
            defected_str = "----"
            #label.setStyleSheet("background-color: red")
        #else:
            #label.setStyleSheet("background-color: white")

        # --- Update label text ---
        # Looks like: "ID: current volume     (mean_indiv=X, var_indiv=Y)  data:[actual data buffer]"
        label.setText(defected_str + str(index) + ": " + str(volume) + "   (mean_indiv=" + str(int(mean_indiv*10)/10) + ", var_indiv=" + str(int(var_indiv*10)/10) + ")") #"  data:" + str(buffer[index]))

        # --- Pause the updates ---
        #time.sleep(0.5)

        # --- Check for quit command ---
        if keyboard.is_pressed('q') or quit_flag:

            print("Closing stream", index)
            stream.stop_stream()
            stream.close()

            # Save the buffer as a .wav file, for testing purposes only
            #print("Storing f"+str(index)+".wav")
            #wf = wave.open("f"+str(index)+".wav", 'wb')
            #wf.setnchannels(CHANNELS)
            #wf.setsampwidth(p.get_sample_size(FORMAT))
            #wf.setframerate(RATE)
            #wf.writeframes(b''.join(wave_buffer))
            #wf.close()
            break



# Close threads when window is closed
def exitMethod():
    global quit_flag
    quit_flag = True



# Main thread method, the code should be implemented here
def mainThread(mean_label, var_label):

    # --- Global variables ---
    global buffer           # This global buffer consists of several lists one for each audio device
    global buffer_width     # Size of the list available for each audio device (at buffer[index])
    global mean_combined    # Combined mean for the current volumes (computed in mainThread())
    global var_combined     # Combined variance for the current volumes (computed in mainThread())

    while True:
        # Check the exit condition and join the threads if it is met
        if keyboard.is_pressed('q') or quit_flag:
            for x in threads:
                x.join()
            p.terminate()
            break

        # Number of devices to consider (code redability variable)
        nb_audio_devices = len(buffer)

        # Ugly check needed for script start (Below try to access buffer[i][-1] when buffer[i] is not initialized)
        for i in range(0, nb_audio_devices):
            if len(buffer[i]) == 0:
                time.sleep(1)

        # --- Pause the updates ---
        #time.sleep(0.5)

        # --- Keep only last buffer values ---
        # For every audio devices: Limit buffers to the buffer_width (only takes last buffer values)
        for i in range(0, nb_audio_devices):
            buffer[i] = buffer[i][-buffer_width:]

        # --------- Combined mean and variance computation ---------
        # Only compute mean and variance for devices 1 and 2 (0 is Microsoft stuff, not a real microphone)
        # We don't want to include it in our calculation in order to not give device 1 more importance than device 2

        # --- Mean computation (could use array.mean() ?) ---
        mean_value = 0
        mean_str = " ("     # Debug purpose
        # For every audio devices (except 0)
        for i in range(1, nb_audio_devices):
            mean_value = mean_value + buffer[i][-1]
            mean_str   = mean_str + str(buffer[i][-1]) + "; "
        # After the sum of all devices volume finish the computation by dividing by the number of terms
        mean_value = mean_value / (nb_audio_devices-1)
        mean_str = mean_str[:-2] + ")"

        # --- Variance computation (np.var(array) ?) ---
        var_value = 0
        for i in range(1, nb_audio_devices):
            # Sum of square distances between each data point to the mean
            var_value = var_value + (buffer[i][-1] - mean_value)**2
        var_value = var_value / (nb_audio_devices-1)

        # Store the combined mean and variance as global variables (must use temporary variable for stability between threads)
        mean_combined = mean_value
        var_combined = var_value

        # --- Labels update ---
        mean_label.setText("Combined Mean: "    + str(int(mean_value*10)/10) + " \n   for data: " + mean_str)
        var_label.setText("Combined Variance: " + str(int(var_value*10)/10))

    print("Execution finished")


######################### MAIN CODE #########################

# --- Init and store global threads and labels ---
threads = []
labels = []
buffer = []
mean_combined = 0
var_combined = 0
buffer_width = 100
quit_flag = False

# --- GUI: Initializing window ---
app = QApplication(sys.argv)
app.aboutToQuit.connect(exitMethod)
window = QWidget()
window.setWindowTitle('Soundwave log')
window.setGeometry(50, 50, 1000, 500)
window.move(500, 500)

# --- Initialize pyaudio ---
p = pyaudio.PyAudio()
info = p.get_host_api_info_by_index(0)
numdevices = info.get('deviceCount')

# --- Run the threads ---
for i in range(0, numdevices):
    # Check if the device takes input
    if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:

        # Initialize labels
        labels.append(QLabel("____________", parent = window))
        labels[-1].move(60, (15 * (i+1)) + (20*i))
        labels[-1].resize(800, 50)
        labels[-1].setFont(QFont('Arial', 10))

        # Append a new buffer to the global list
        buffer.append([])

        # Start threads
        threads.append(threading.Thread(target=log_sound, args=(i, labels[i])))
        threads[i].start()

# --- Init labels for combined data ---
mean = QLabel("Combined mean: IMPLEMENT ME!", parent = window)
mean.move(60, (15 * numdevices + (10 * numdevices)))
mean.resize(300, 80)
mean.setStyleSheet("border: 1px solid black;")
mean.setFont(QFont('Arial', 12))

variance = QLabel("Combined variance: IMPLEMENT ME!", parent = window)
variance.move(60, (15 * numdevices + (15 * (numdevices + 4))))
variance.resize(300, 50)
variance.setStyleSheet("border: 1px solid black;")
variance.setFont(QFont('Arial', 12))

# --- Start the main thread ---
main_thread = threading.Thread(target = mainThread, args=[mean, variance])
main_thread.start()

# --- Show window and run GUI-application loop ---
window.show()
app.exec_()
