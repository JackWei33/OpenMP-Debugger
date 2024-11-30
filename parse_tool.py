import matplotlib.pyplot as plt
import glob
import os
import re

# Define a class to hold activity intervals
class Activity:
    def __init__(self, start_time, end_time, activity_type, details):
        self.start_time = start_time
        self.end_time = end_time
        self.activity_type = activity_type
        self.details = details

def parse_log_file(filename):
    activities = []
    stack = []
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('Time:'):
            # Start of an event
            time_line = line
            time_match = re.search(r'Time:\s+(\d+)', time_line)
            if time_match:
                time = int(time_match.group(1))
            else:
                i += 1
                continue
            event_line = lines[i+1]
            event_match = re.search(r'Event:\s+(.*)', event_line)
            if event_match:
                event = event_match.group(1)
            else:
                i += 1
                continue
            details = {}
            i += 2
            while i < len(lines) and not lines[i].startswith('--------------------------'):
                detail_line = lines[i]
                detail_match = re.match(r'([\w\s]+):\s+(.*)', detail_line)
                if detail_match:
                    key = detail_match.group(1).strip()
                    value = detail_match.group(2).strip()
                    details[key] = value
                i += 1
            # Now process the event
            if event == 'Implicit Task':
                endpoint = details.get('Endpoint', '')
                if endpoint == 'ompt_scope_begin':
                    # Start of a task
                    stack.append({'activity_type': 'Implicit Task', 'start_time': time, 'details': details})
                elif endpoint == 'ompt_scope_end':
                    # End of a task
                    for j in range(len(stack)-1, -1, -1):
                        if stack[j]['activity_type'] == 'Implicit Task':
                            activity = stack.pop(j)
                            activity['end_time'] = time
                            activities.append(Activity(activity['start_time'], activity['end_time'], activity['activity_type'], activity['details']))
                            break
            elif event == 'Work':
                endpoint = details.get('Endpoint', '')
                if endpoint == 'ompt_scope_begin':
                    # Start of work
                    stack.append({'activity_type': 'Work', 'start_time': time, 'details': details})
                elif endpoint == 'ompt_scope_end':
                    # End of work
                    for j in range(len(stack)-1, -1, -1):
                        if stack[j]['activity_type'] == 'Work':
                            activity = stack.pop(j)
                            activity['end_time'] = time
                            activities.append(Activity(activity['start_time'], activity['end_time'], activity['activity_type'], activity['details']))
                            break
            elif event == 'Mutex Acquire':
                # Start of mutex wait
                stack.append({'activity_type': 'Mutex Wait', 'start_time': time, 'details': details})
            elif event == 'Mutex Acquired':
                # End of mutex wait, start of mutex hold
                for j in range(len(stack)-1, -1, -1):
                    if stack[j]['activity_type'] == 'Mutex Wait':
                        wait_activity = stack.pop(j)
                        wait_activity['end_time'] = time
                        activities.append(Activity(wait_activity['start_time'], wait_activity['end_time'], wait_activity['activity_type'], wait_activity['details']))
                        break
                # Now start of mutex hold
                stack.append({'activity_type': 'Mutex Hold', 'start_time': time, 'details': details})
            elif event == 'Mutex Released':
                # End of mutex hold
                for j in range(len(stack)-1, -1, -1):
                    if stack[j]['activity_type'] == 'Mutex Hold':
                        hold_activity = stack.pop(j)
                        hold_activity['end_time'] = time
                        activities.append(Activity(hold_activity['start_time'], hold_activity['end_time'], hold_activity['activity_type'], hold_activity['details']))
                        break
            # Handle other events similarly
        i += 1
    return activities

def plot_activities(activities_per_thread):
    import matplotlib.patches as mpatches
    fig, ax = plt.subplots()
    y_ticks = []
    y_labels = []
    y_pos = 10
    colors = {'Implicit Task': 'skyblue', 'Work': 'green', 'Mutex Wait': 'orange', 'Mutex Hold': 'red'}
    legend_patches = []
    for activity_type, color in colors.items():
        legend_patches.append(mpatches.Patch(color=color, label=activity_type))
    for thread_id, activities in activities_per_thread.items():
        y_ticks.append(y_pos)
        y_labels.append(f'Thread {thread_id}')
        for activity in activities:
            start = activity.start_time
            duration = activity.end_time - activity.start_time
            ax.broken_barh([(start, duration)], (y_pos - 5, 10), facecolors=colors.get(activity.activity_type, 'grey'))
        y_pos += 15
    ax.set_ylim(5, y_pos)
    ax.set_xlim(0, max([activity.end_time for activities in activities_per_thread.values() for activity in activities]) + 1000)
    ax.set_xlabel('Time (µs)')
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels)
    ax.legend(handles=legend_patches)
    plt.title('Parallel Execution Timeline')
    plt.savefig('timeline.png')

def main():
    log_files = glob.glob('logs/logs_thread_*.txt')
    activities_per_thread = {}
    for log_file in log_files:
        thread_id = os.path.basename(log_file).split('_')[-1].split('.')[0]
        activities = parse_log_file(log_file)
        activities_per_thread[thread_id] = activities
    plot_activities(activities_per_thread)

if __name__ == '__main__':
    main()
