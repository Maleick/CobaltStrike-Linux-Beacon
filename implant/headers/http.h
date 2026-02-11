#ifndef HTTP_H
#define HTTP_H

#include <stddef.h>
#include <stdint.h>

// HTTP request/response
typedef struct {
    char *data;
    size_t size;
} http_response_t;

// Send HTTP GET request (for initial metadata)
int http_get(const char *uri, const uint8_t *metadata, size_t metadata_len, http_response_t *response);

// Send HTTP POST request (for task output)
int http_post(const char *uri, const uint8_t *data, size_t data_len, const char *session_id, http_response_t *response);

// Free HTTP response
void http_response_free(http_response_t *response);

#endif // HTTP_H
