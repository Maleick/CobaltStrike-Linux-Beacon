#ifndef TCP_H
#define TCP_H

#include <stddef.h>
#include <stdint.h>
#include "beacon.h"

// Transport interface implementation for TCP
int tcp_transport_init(beacon_state_t *state);
int tcp_transport_send_metadata(beacon_state_t *state, const uint8_t *data, size_t len);
int tcp_transport_receive_tasks(beacon_state_t *state, uint8_t **tasks, size_t *tasks_len);
int tcp_transport_send_output(beacon_state_t *state, const uint8_t *data, size_t len);
void tcp_transport_cleanup(void);

#endif // TCP_H
