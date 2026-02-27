#ifndef HTTP_H
#define HTTP_H

#include <stddef.h>
#include <stdint.h>
#include "beacon.h"

// HTTP request/response
typedef struct {
    char *data;
    size_t size;
} http_response_t;

// Transport interface implementation for HTTP
int http_transport_init(beacon_state_t *state);
int http_transport_send_metadata(beacon_state_t *state, const uint8_t *data, size_t len);
int http_transport_receive_tasks(beacon_state_t *state, uint8_t **tasks, size_t *tasks_len);
int http_transport_send_output(beacon_state_t *state, const uint8_t *data, size_t len);
void http_transport_cleanup(void);

// Internal HTTP functions
int http_get(const char *uri, const uint8_t *metadata, size_t metadata_len, http_response_t *response);
int http_post(const char *uri, const uint8_t *data, size_t data_len, const char *session_id, http_response_t *response);
void http_response_free(http_response_t *response);

#endif // HTTP_H
