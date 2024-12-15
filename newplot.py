import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.animation import FuncAnimation
import matplotlib

matplotlib.use('TkAgg')

csv_path = 'led_data.csv'

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10), sharex=True)


def dynamic_plot(i):
    try:
        data = pd.read_csv(csv_path)

        required_columns = ['Time', '670nm', '850nm', '950nm', '1300nm']
        for col in required_columns:
            if col not in data.columns:
                print(f"Error: Missing column '{col}' in CSV file.")
                return

        x = data['Time']
        silicon_data = data['670nm'] + data['850nm'] + data['950nm']
        inga_data = data['1300nm']

        ax1.clear()
        ax2.clear()

        ax1.plot(x, silicon_data, label='Silicon (670nm, 850nm, 950nm)', color='blue', linewidth=1)
        ax1.legend(loc='upper left')
        ax1.set_ylabel('Silicon Signal (mV)')
        ax1.set_title('Dynamic Plot for the photo diode')

        ax2.plot(x, inga_data, label='InGaAs (1300nm)', color='green', linewidth=1)
        ax2.legend(loc='upper left')
        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('InGaAs Signal (mV)')

        plt.tight_layout()

    except pd.errors.EmptyDataError:
        print("Error: The CSV file is empty. Waiting for data...")
    except FileNotFoundError:
        print(f"Error: File '{csv_path}' not found. Please check the file path.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


ani = FuncAnimation(fig, dynamic_plot, interval=1000, cache_frame_data=False)

plt.show()
