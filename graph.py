import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_stacked_bar_chart(parallel_sections_data, section_colors):
    """
    Creates and displays a stacked bar chart using Plotly for each parallel section.

    Parameters:
    - parallel_sections_data: A dictionary where each key is a parallel section name, and each value
                              is a dictionary where each key is a thread name, and each value is another
                              dictionary mapping section names to the time spent in that section.
    """
    num_sections = len(parallel_sections_data)
    subplot_titles = list(parallel_sections_data.keys())

    # Create subplots with a variable number of columns
    fig = make_subplots(rows=1, cols=num_sections, subplot_titles=subplot_titles)

    for pos, (parallel_id, thread_data) in enumerate(parallel_sections_data.items()):
        # Extract thread names and section names
        threads = list(thread_data.keys())
        sections = list(next(iter(thread_data.values())).keys())

        # Prepare data for plotting
        section_times = {section: [] for section in sections}
        for thread in threads:
            for section in sections:
                section_times[section].append(thread_data[thread].get(section, 0))

        # Add a bar for each section
        for section in sections:
            fig.add_trace(go.Bar(
                name=section,
                x=threads,
                y=section_times[section],
                marker_color=section_colors[section],
                hovertemplate=(
                    'Thread: %{x}<br>' +
                    'Section: ' + section + '<br>' +
                    'Time Spent: %{y}<extra></extra>'
                ),
                showlegend=(pos == 0),  # Show legend only for the first subplot
                legendgroup=section  # Group traces by section for synchronized toggling
            ), row=1, col=pos + 1)

    fig.update_layout(
        barmode='stack',
        title='Time Spent by Threads in Different Sections in Parallel Regions',
        xaxis_title='Threads',
        yaxis_title='Time Spent',
        legend_title='Sections'
    )

    # Show the plot
    fig.show()

def main():
    parallel_sections_data = {
        'Parallel Section 1': {
            'Thread 1': {'Working': 5, 'Critical': 3, 'Mutex': 2},
            'Thread 2': {'Working': 4, 'Critical': 6, 'Mutex': 1},
            'Thread 3': {'Working': 7, 'Critical': 2, 'Mutex': 3},
            'Thread 4': {'Working': 6, 'Critical': 5, 'Mutex': 4},
            'Thread 5': {'Working': 8, 'Critical': 4, 'Mutex': 2},
            'Thread 6': {'Working': 3, 'Critical': 7, 'Mutex': 5},
            'Thread 7': {'Working': 5, 'Critical': 3, 'Mutex': 6},
            'Thread 8': {'Working': 2, 'Critical': 4, 'Mutex': 3}
        },
        'Parallel Section 2': {
            'Thread 1': {'Working': 3, 'Critical': 7, 'Mutex': 4},
            'Thread 2': {'Working': 6, 'Critical': 2, 'Mutex': 5},
            'Thread 3': {'Working': 4, 'Critical': 3, 'Mutex': 6},
            'Thread 4': {'Working': 5, 'Critical': 4, 'Mutex': 3},
            'Thread 5': {'Working': 7, 'Critical': 5, 'Mutex': 2},
            'Thread 6': {'Working': 2, 'Critical': 6, 'Mutex': 4},
            'Thread 7': {'Working': 3, 'Critical': 5, 'Mutex': 7},
            'Thread 8': {'Working': 4, 'Critical': 4, 'Mutex': 5}
        },
        'Parallel Section 3': {
            'Thread 1': {'Working': 3, 'Critical': 7, 'Mutex': 4},
            'Thread 2': {'Working': 6, 'Critical': 2, 'Mutex': 5},
            'Thread 3': {'Working': 4, 'Critical': 3, 'Mutex': 6},
            'Thread 4': {'Working': 5, 'Critical': 4, 'Mutex': 3},
            'Thread 5': {'Working': 7, 'Critical': 5, 'Mutex': 2},
            'Thread 6': {'Working': 2, 'Critical': 6, 'Mutex': 4},
            'Thread 7': {'Working': 3, 'Critical': 5, 'Mutex': 7},
            'Thread 8': {'Working': 4, 'Critical': 4, 'Mutex': 5}
        }
    }

    section_colors = {
        'Working': 'rgb(31, 119, 180)',
        'Critical': 'rgb(255, 127, 14)',
        'Mutex': 'rgb(44, 160, 44)'
    }

    create_stacked_bar_chart(parallel_sections_data, section_colors)

if __name__ == "__main__":
    main()
