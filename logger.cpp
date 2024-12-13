// // #include <iostream>
// // #include "spdlog/spdlog.h"
// // #include "spdlog/async.h" //support for async logging.
// // #include "spdlog/sinks/basic_file_sink.h"

// // int main(int, char* [])
// // {
// //     try
// //     {        
// //         auto async_file = spdlog::basic_logger_mt<spdlog::async_factory>("async_file_logger", "logs/async_log.txt");
// //         for (int i = 1; i < 101; ++i)
// //         {
// //             async_file->info("Async message #{}", i);
// //         }
// //         // Under VisualStudio, this must be called before main finishes to workaround a known VS issue
// //         spdlog::drop_all(); 
// //     }
// //     catch (const spdlog::spdlog_ex& ex)
// //     {
// //         std::cout << "Log initialization failed: " << ex.what() << std::endl;
// //     }
// // }

// // simplified_logging_test.cpp

// #include <spdlog/spdlog.h>
// #include <spdlog/async.h> // Support for asynchronous logging
// #include <spdlog/sinks/basic_file_sink.h>
// #include <spdlog/sinks/stdout_color_sinks.h>

// #include <iostream>
// #include <unordered_map>
// #include <memory>
// #include <mutex>
// #include <thread>
// #include <filesystem>
// #include <vector>
// #include <string>
// #include <chrono>

// #include <omp.h>

// // Constants for asynchronous logging
// constexpr size_t ASYNC_QUEUE_SIZE = 1048576; // 1 million items
// constexpr size_t ASYNC_THREAD_COUNT = 2;     // Number of worker threads

// // Global variables for managing per-thread loggers
// std::unordered_map<uint64_t, std::shared_ptr<spdlog::logger>> thread_loggers;
// std::mutex logger_map_mutex;

// // Initialize spdlog with asynchronous support
// void initialize_spdlog()
// {
//     // Initialize the thread pool for asynchronous logging
//     spdlog::init_thread_pool(ASYNC_QUEUE_SIZE, ASYNC_THREAD_COUNT);

//     // Optionally, set a global logger (e.g., console logger)
//     auto console_sink = std::make_shared<spdlog::sinks::stdout_color_sink_mt>();
//     console_sink->set_level(spdlog::level::info);
//     console_sink->set_pattern("%v");

//     auto console_logger = std::make_shared<spdlog::logger>("console", console_sink);
//     console_logger->set_level(spdlog::level::info);
//     spdlog::register_logger(console_logger);
//     spdlog::set_default_logger(console_logger);
// }

// // Shutdown spdlog gracefully
// void shutdown_spdlog()
// {
//     spdlog::shutdown();
// }

// // Function to retrieve or create a logger for a given thread
// std::shared_ptr<spdlog::logger> get_thread_logger(uint64_t thread_id)
// {
//     std::lock_guard<std::mutex> lock(logger_map_mutex);
//     auto it = thread_loggers.find(thread_id);
//     if (it != thread_loggers.end())
//     {
//         return it->second;
//     }
//     else
//     {
//         // Ensure logs directory exists
//         std::filesystem::create_directories("logs");

//         // Create a new asynchronous logger for the thread
//         std::string filename = "logs/log_thread_" + std::to_string(thread_id) + ".txt";
//         auto file_sink = std::make_shared<spdlog::sinks::basic_file_sink_mt>(filename, true);
//         file_sink->set_level(spdlog::level::info);
//         file_sink->set_pattern("%v");

//         auto logger = std::make_shared<spdlog::logger>("logger_thread_" + std::to_string(thread_id), file_sink);
//         logger->set_level(spdlog::level::info);
//         logger->flush_on(spdlog::level::info);

//         // Register the logger with spdlog's registry
//         spdlog::register_logger(logger);
//         thread_loggers[thread_id] = logger;
//         return logger;
//     }
// }

// // Function to log messages from a thread
// void thread_logging_function(int thread_num, int num_messages)
// {
//     // Get the thread ID (unique identifier)
//     uint64_t thread_id = static_cast<uint64_t>(thread_num);

//     // Retrieve or create the logger for this thread
//     auto logger = get_thread_logger(thread_id);

//     // Log multiple messages
//     for (int i = 0; i < num_messages; ++i)
//     {
//         logger->info("Message {} from thread {}", i + 1, thread_num);
//         // Simulate some work
//         std::this_thread::sleep_for(std::chrono::milliseconds(10));
//     }

//     // Optionally, log to the console as well
//     spdlog::default_logger()->info("Thread {} has finished logging.", thread_num);
// }

// int main()
// {
//     // Initialize spdlog
//     initialize_spdlog();

//     std::cout << "Hello World" << std::endl;

//     // Number of threads and messages per thread
//     const int NUM_THREADS = 5;
//     const int MESSAGES_PER_THREAD = 10;

//     // // Create and launch threads
//     // std::vector<std::thread> threads;
//     // for (int i = 1; i <= NUM_THREADS; ++i)
//     // {
//     //     threads.emplace_back(thread_logging_function, i, MESSAGES_PER_THREAD);
//     // }

//     // // Wait for all threads to finish
//     // for (auto &t : threads)
//     // {
//     //     t.join();
//     // }

//     #pragma omp parallel num_threads(5)
//     {
//         thread_logging_function(omp_get_thread_num(), MESSAGES_PER_THREAD);
//     }

//     // Log a final message to the console
//     spdlog::default_logger()->info("All threads have completed logging.");

//     // Shutdown spdlog
//     shutdown_spdlog();

//     std::cout << "Hello World 2" << std::endl;

//     return 0;
// }

#include "quill/Backend.h"
#include "quill/Frontend.h"
#include "quill/LogMacros.h"
#include "quill/Logger.h"
#include "quill/sinks/ConsoleSink.h"
#include <string_view>

int main()
{
  quill::Backend::start();

  quill::Logger* logger = quill::Frontend::create_or_get_logger(
    "root", quill::Frontend::create_or_get_sink<quill::ConsoleSink>("sink_id_1"));

  LOG_INFO(logger, "Hello from {}!", std::string_view{"Quill"});
}
