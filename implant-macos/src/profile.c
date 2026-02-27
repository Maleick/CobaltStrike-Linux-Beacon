/* copied from implant/src/profile.c, last synced 2026-02-26 */
#include "profile.h"
#include "config.h"

#include <stddef.h>
#include <string.h>

#if defined(__has_include)
#  if __has_include("../generated/profile_config.h")
#    include "../generated/profile_config.h"
#    define PROFILE_GENERATED_HEADER_PRESENT 1
#  endif
#endif

#ifndef PROFILE_ID
#define PROFILE_ID "legacy-config-default"
#endif

#ifndef PROFILE_SCHEMA_VERSION
#define PROFILE_SCHEMA_VERSION "fallback"
#endif

#ifndef PROFILE_C2_SERVER
#define PROFILE_C2_SERVER C2_SERVER
#endif

#ifndef PROFILE_C2_PORT
#define PROFILE_C2_PORT C2_PORT
#endif

#ifndef PROFILE_C2_USE_HTTPS
#define PROFILE_C2_USE_HTTPS C2_USE_HTTPS
#endif

#ifndef PROFILE_HTTP_GET_URI
#define PROFILE_HTTP_GET_URI HTTP_GET_URI
#endif

#ifndef PROFILE_HTTP_POST_URI
#define PROFILE_HTTP_POST_URI HTTP_POST_URI
#endif

#ifndef PROFILE_USER_AGENT
#define PROFILE_USER_AGENT USER_AGENT
#endif

#ifndef PROFILE_HEADER_0
#define PROFILE_HEADER_0 HTTP_ACCEPT_HEADER
#endif

#ifndef PROFILE_HEADER_1
#define PROFILE_HEADER_1 HTTP_CONNECTION_HEADER
#endif

#ifndef PROFILE_HEADER_2
#define PROFILE_HEADER_2 HTTP_CACHE_CONTROL_HEADER
#endif

static const char *const PROFILE_HEADER_VALUES[] = {
    PROFILE_HEADER_0,
    PROFILE_HEADER_1,
    PROFILE_HEADER_2,
#ifdef PROFILE_HEADER_3
    PROFILE_HEADER_3,
#endif
#ifdef PROFILE_HEADER_4
    PROFILE_HEADER_4,
#endif
#ifdef PROFILE_HEADER_5
    PROFILE_HEADER_5,
#endif
#ifdef PROFILE_HEADER_6
    PROFILE_HEADER_6,
#endif
#ifdef PROFILE_HEADER_7
    PROFILE_HEADER_7,
#endif
};

static profile_config_t g_profile;
static int g_profile_loaded = 0;

static size_t profile_header_value_count(void)
{
    return sizeof(PROFILE_HEADER_VALUES) / sizeof(PROFILE_HEADER_VALUES[0]);
}

int profile_load(void)
{
    size_t i = 0;
    size_t count = profile_header_value_count();

    memset(&g_profile, 0, sizeof(g_profile));

    g_profile.profile_id = PROFILE_ID;
    g_profile.schema_version = PROFILE_SCHEMA_VERSION;
    g_profile.server = PROFILE_C2_SERVER;
    g_profile.port = PROFILE_C2_PORT;
    g_profile.use_https = PROFILE_C2_USE_HTTPS;
    g_profile.http_get_uri = PROFILE_HTTP_GET_URI;
    g_profile.http_post_uri = PROFILE_HTTP_POST_URI;
    g_profile.user_agent = PROFILE_USER_AGENT;
    g_profile.header_count = count > PROFILE_MAX_HEADERS ? PROFILE_MAX_HEADERS : count;

    for (i = 0; i < g_profile.header_count; ++i) {
        g_profile.headers[i] = PROFILE_HEADER_VALUES[i];
    }

    g_profile_loaded = 1;
    return 0;
}

static void ensure_profile_loaded(void)
{
    if (!g_profile_loaded) {
        (void)profile_load();
    }
}

const profile_config_t *profile_get(void)
{
    ensure_profile_loaded();
    return &g_profile;
}

const char *profile_get_id(void)
{
    return profile_get()->profile_id;
}

const char *profile_get_schema_version(void)
{
    return profile_get()->schema_version;
}

const char *profile_get_server(void)
{
    return profile_get()->server;
}

int profile_get_port(void)
{
    return profile_get()->port;
}

int profile_get_use_https(void)
{
    return profile_get()->use_https;
}

const char *profile_get_http_get_uri(void)
{
    return profile_get()->http_get_uri;
}

const char *profile_get_http_post_uri(void)
{
    return profile_get()->http_post_uri;
}

const char *profile_get_user_agent(void)
{
    return profile_get()->user_agent;
}

size_t profile_get_header_count(void)
{
    return profile_get()->header_count;
}

const char *profile_get_header(size_t index)
{
    const profile_config_t *profile = profile_get();

    if (index >= profile->header_count) {
        return NULL;
    }
    return profile->headers[index];
}
