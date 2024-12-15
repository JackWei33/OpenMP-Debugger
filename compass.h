#ifndef COMPASS_H
#define COMPASS_H

#include <string>
#include <utility>
#include <initializer_list>

/**
 * @brief Begins a trace event with a name and optional key-value details.
 *
 * @param name The name of the trace event.
 * @param optional_details Optional key-value pairs providing additional context.
 */
void compass_trace_begin(const std::string& name, 
                         std::initializer_list<std::pair<std::string, std::string>> optional_details = {});

/**
 * @brief Ends a trace event with the given name.
 *
 * @param name The name of the trace event to end.
 */
void compass_trace_end(const std::string& name);

#endif // COMPASS_H