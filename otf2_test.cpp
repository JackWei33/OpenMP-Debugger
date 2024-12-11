// #include <iostream>
// #include <omp.h>
// #include <cstdlib>
// #include <cstring>
// #include <otf2/otf2.h>

// // Error checking macro for simplicity
// #define CHECK_OTF2(call) \
//     do { \
//         OTF2_ErrorCode _err = call; \
//         if (_err != OTF2_SUCCESS) { \
//             std::cerr << "OTF2 Error: " << OTF2_Error_GetName(_err) \
//                       << " (" << OTF2_Error_GetDescription(_err) << ")" << std::endl; \
//             std::exit(EXIT_FAILURE); \
//         } \
//     } while (0)

// int main(int argc, char** argv)
// {
//     // Basic setup
//     const char* trace_directory = "otf2_trace";
//     const char* trace_name = "example_trace";

//     // Create an OTF2 archive
//     OTF2_Archive* archive = OTF2_Archive_Open(
//         trace_directory,        // Archive directory
//         trace_name,             // Archive name
//         OTF2_FILEMODE_WRITE,    // Mode
//         1024 * 1024,            // Chunk size events
//         4 * 1024 * 1024,        // Chunk size defs
//         OTF2_SUBSTRATE_POSIX,   // Substrate
//         OTF2_COMPRESSION_NONE); // Compression

//     if (!archive) {
//         std::cerr << "Failed to create OTF2 archive." << std::endl;
//         return EXIT_FAILURE;
//     }

//     // Set the number of locations. For simplicity, we use one location.
//     CHECK_OTF2(OTF2_Archive_SetSerialCollectiveCallbacks(archive));
//     OTF2_GlobalDefWriter* global_def_writer = OTF2_Archive_GetGlobalDefWriter(archive);

//     // Time information (just placeholders; OTF2 requires stable timer resolution info)
//     CHECK_OTF2(OTF2_Archive_SetMachineName(archive, "example_machine"));
//     CHECK_OTF2(OTF2_Archive_SetDescription(archive, "Example OTF2 trace of an OpenMP parallel region."));
//     CHECK_OTF2(OTF2_Archive_OpenDefFiles(archive));

//     // Define a single location (representing a single thread for simplicity)
//     OTF2_LocationRef location_id = 0x0000000000000001ULL;
//     uint64_t global_num_locations = 1;

//     // Global definitions
//     CHECK_OTF2(OTF2_GlobalDefWriter_WriteString(global_def_writer, 0, "ExampleMachine"));
//     CHECK_OTF2(OTF2_GlobalDefWriter_WriteString(global_def_writer, 1, "OpenMPParallelRegion"));
//     CHECK_OTF2(OTF2_GlobalDefWriter_WriteString(global_def_writer, 2, "main"));
//     CHECK_OTF2(OTF2_GlobalDefWriter_WriteString(global_def_writer, 3, "OMP Region"));

//     // System tree node
//     OTF2_SystemTreeNodeRef system_tree_node = 0;
//     CHECK_OTF2(OTF2_GlobalDefWriter_WriteSystemTreeNode(
//         global_def_writer, system_tree_node, 0, 0, OTF2_SYSTEM_TREE_DOMAIN_MACHINE));

//     // Location group (e.g., representing a process)
//     OTF2_LocationGroupRef location_group = 0;
//     CHECK_OTF2(OTF2_GlobalDefWriter_WriteLocationGroup(
//         global_def_writer, location_group, 1, 0, system_tree_node, OTF2_LOCATION_GROUP_TYPE_PROCESS));

//     // // Location definition
//     // CHECK_OTF2(OTF2_GlobalDefWriter_WriteLocation(
//     //     global_def_writer, location_id, 2, location_group, OTF2_LOCATION_TYPE_CPU_THREAD, 0, OTF2_LOCATION_GROUP_TYPE_UNKNOWN));

//     // Region definition: let's define a region for our OpenMP parallel section
//     OTF2_RegionRef region_id = 0;
//     CHECK_OTF2(OTF2_GlobalDefWriter_WriteRegion(
//         global_def_writer,
//         region_id,
//         3,          // name string ref ("OMP Region")
//         2,          // canonical name string ref ("main")
//         0, 0,       // no file info in this simple example
//         OTF2_REGION_ROLE_PARALLEL,
//         OTF2_PARADIGM_OPENMP,
//         OTF2_REGION_FLAG_NONE,
//         0,          // no source code info
//         0));

//     // Close definitions
//     CHECK_OTF2(OTF2_Archive_CloseDefFiles(archive));

//     // Open event writer for our single location
//     CHECK_OTF2(OTF2_Archive_OpenEvtFiles(archive));
//     OTF2_EvtWriter* evt_writer = OTF2_Archive_GetEvtWriter(archive, location_id);

//     // Get a stable start timestamp
//     // In a real scenario, you'd use OTF2_Archive_GetTraceId or OTF2_ClockProperties, 
//     // but we’ll just start from zero here for simplicity.
//     uint64_t start_time = 0;

//     // Emit a measurement start event
//     CHECK_OTF2(OTF2_EvtWriter_MeasurementOnOff(evt_writer, NULL, start_time, OTF2_MEASUREMENT_ON));

//     // An example OpenMP parallel region
//     // We will instrument entering and leaving the region.
//     uint64_t timestamp = start_time + 10;
//     CHECK_OTF2(OTF2_EvtWriter_Enter(evt_writer, NULL, timestamp, region_id));

// #pragma omp parallel
//     {
//         // Some parallel work. For demonstration, just do a simple loop.
//         int tid = omp_get_thread_num();
//         // Note: For a real application, each thread should have its own location 
//         // and its own evt_writer. Here we just show the concept, ignoring that 
//         // multiple threads writing to one evt_writer isn't best practice.
// #pragma omp for
//         for (int i = 0; i < 100; ++i) {
//             // Simulate work
//         }
//     }

//     timestamp += 100; // Just simulating time passing
//     CHECK_OTF2(OTF2_EvtWriter_Leave(evt_writer, NULL, timestamp, region_id));

//     // Emit a measurement off event
//     CHECK_OTF2(OTF2_EvtWriter_MeasurementOnOff(evt_writer, NULL, timestamp + 10, OTF2_MEASUREMENT_OFF));

//     // Close event files and archive
//     CHECK_OTF2(OTF2_Archive_CloseEvtFiles(archive));
//     CHECK_OTF2(OTF2_Archive_Close(archive));

//     std::cout << "OTF2 trace written to " << trace_directory << "/" << trace_name << ".\n";
//     return 0;
// }
