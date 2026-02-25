#ifndef PROFILE_H
#define PROFILE_H

#include <stddef.h>

#define PROFILE_MAX_HEADERS 8

typedef struct {
    const char *profile_id;
    const char *schema_version;
    const char *server;
    int port;
    int use_https;
    const char *http_get_uri;
    const char *http_post_uri;
    const char *user_agent;
    const char *headers[PROFILE_MAX_HEADERS];
    size_t header_count;
} profile_config_t;

/* Load profile values from generated profile macros with config.h fallbacks. */
int profile_load(void);

/* Return the currently loaded profile (lazy-loads on first access). */
const profile_config_t *profile_get(void);

const char *profile_get_server(void);
int profile_get_port(void);
int profile_get_use_https(void);
const char *profile_get_http_get_uri(void);
const char *profile_get_http_post_uri(void);
const char *profile_get_user_agent(void);
size_t profile_get_header_count(void);
const char *profile_get_header(size_t index);

#endif /* PROFILE_H */
